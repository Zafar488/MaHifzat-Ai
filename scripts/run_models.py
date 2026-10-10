"""Reproducible experimental training. Importing this module never trains.
Train-fold preprocessing; duplicate-feature groups never cross partitions.
Model selection uses training CV only. Test data is evaluated exactly once.
"""
from pathlib import Path
import argparse
import hashlib
import json
import platform
import sys
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from lightgbm import LGBMClassifier
from sklearn.model_selection import GroupShuffleSplit, StratifiedGroupKFold, GridSearchCV
from sklearn.metrics import f1_score, classification_report

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.services.inference import MATERNAL_FEATURES, CTG_FEATURES

SEED = 20261009


def train_model(name, data_dir=ROOT / "data", output_dir=ROOT / "artifacts" / "serving"):
    maternal = name == "maternalguard"
    path = Path(data_dir) / ("uci_maternal.parquet" if maternal else "uci_ctg.parquet")
    df = pd.read_parquet(path)
    features = MATERNAL_FEATURES if maternal else CTG_FEATURES
    target = "RiskLevel" if maternal else "NSP"
    x = df[features].astype(float)
    y = df[target].astype(str) if maternal else df[target].map({1: "normal", 2: "suspect", 3: "pathological"})
    if y.isna().any() or not np.isfinite(x.to_numpy()).all():
        raise ValueError("Invalid dataset; no silent dropping or target substitution")
    # Feature-identical rows (including conflicting labels) stay in one group.
    groups = pd.util.hash_pandas_object(x, index=False).astype(str)
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=SEED)
    train, test = next(splitter.split(x, y, groups))
    if set(groups.iloc[train]) & set(groups.iloc[test]):
        raise AssertionError("Group leakage")
    pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("estimator", RandomForestClassifier(n_estimators=100, random_state=SEED, class_weight="balanced", n_jobs=1)),
    ])
    cv = StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=SEED)
    grid = [
        {"estimator": [RandomForestClassifier(n_estimators=300, random_state=SEED, class_weight="balanced", n_jobs=1)],
         "estimator__max_depth": [6, None], "estimator__min_samples_leaf": [1, 3]},
        {"estimator": [ExtraTreesClassifier(n_estimators=300, random_state=SEED, class_weight="balanced", n_jobs=1)],
         "estimator__max_depth": [6, None], "estimator__min_samples_leaf": [1, 3]},
        {"estimator": [LGBMClassifier(n_estimators=200, random_state=SEED, class_weight="balanced", verbosity=-1, n_jobs=1)],
         "estimator__num_leaves": [10, 20], "estimator__min_child_samples": [10, 20]},
    ]
    search = GridSearchCV(pipeline, grid, cv=cv, scoring="f1_macro", n_jobs=1, refit=True)
    search.fit(x.iloc[train], y.iloc[train], groups=groups.iloc[train])
    winner = search.best_estimator_
    prediction = winner.predict(x.iloc[test])
    known = x.iloc[test[0]].tolist()
    known_frame = pd.DataFrame([known], columns=features)
    units = {"Age": "years", "SystolicBP": "mmHg", "DiastolicBP": "mmHg", "BS": "mmol/L", "BodyTemp": "F", "HeartRate": "beats/min"} if maternal else {f: ("events/second" if f in ("AC", "FM", "UC", "DL", "DS", "DP") else "UCI193 definition") for f in features}
    bundle = {
        "schema_version": 1, "model_version": "experimental-v2-20261010",
        "pipeline": winner, "features": features, "units": units,
        "label_map": {str(c): str(c) for c in winner.classes_},
        "sklearn_version": sklearn.__version__, "python_version": platform.python_version(),
        "calibration": "uncalibrated class probabilities; not clinical confidence",
        "intended_use": "UCI maternal risk category research" if maternal else "UCI NSP fetal-state classification research; not preterm prediction",
        "feature_ranges": {f: [float(x.iloc[train][f].min()), float(x.iloc[train][f].max())] for f in features},
        "known_input": known, "known_prediction": str(winner.predict(known_frame)[0]),
        "known_probabilities": winner.predict_proba(known_frame)[0].tolist(),
    }
    folder = Path(output_dir) / name
    folder.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, folder / "pipeline-v1.joblib")
    manifest = {
        "dataset": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "source": "https://archive.ics.uci.edu/dataset/" + ("863/maternal+health+risk" if maternal else "193/cardiotocography"),
        "rows": len(df), "unique_feature_groups": groups.nunique(), "target": target,
        "seed": SEED, "train_indices": train.tolist(), "test_indices": test.tolist(),
        "train_test_group_overlap": 0, "split_strategy": "feature-group holdout and stratified group training CV",
        "patient_identifiers": "absent; cannot establish patient-level independence",
        "cv_macro_f1": float(search.best_score_), "best_params": {k: str(v) if k == "estimator" else v for k, v in search.best_params_.items()},
        "selected_algorithm": type(winner.named_steps["estimator"]).__name__,
        "candidate_selection": "RandomForest, ExtraTrees and LightGBM selected by training group CV only; historical test reused for internal comparison",
        "final_test_macro_f1": float(f1_score(y.iloc[test], prediction, average="macro")),
        "test_report": classification_report(y.iloc[test], prediction, output_dict=True),
        "clinical_validation": "not established; internal experimental evaluation only",
        "historical_metrics": "legacy metrics not reproduced or used for model selection",
        "sklearn_version": sklearn.__version__, "units": units,
    }
    (folder / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(name, "rows=", len(df), "groups=", groups.nunique(), "test macro-F1=", round(manifest["final_test_macro_f1"], 4))
    return bundle, manifest


def run_all_models(
    n_trials: int = 5,
    train_fetalwatch: bool = True,
    train_maternalguard: bool = True,
    train_carereach: bool = False,
    train_gestation: bool = False,
    verbose: bool = False,
):
    results = {}
    if train_fetalwatch:
        try:
            train_model("fetalwatch")
            results["fetalwatch"] = json.loads((ROOT / "artifacts/serving/fetalwatch/manifest.json").read_text())
        except Exception as exc:
            results["fetalwatch"] = {"error": str(exc)}

    if train_maternalguard:
        try:
            train_model("maternalguard")
            results["maternalguard"] = json.loads((ROOT / "artifacts/serving/maternalguard/manifest.json").read_text())
        except Exception as exc:
            results["maternalguard"] = {"error": str(exc)}

    if train_carereach or train_gestation:
        results["proxy_training"] = {"status": "disabled", "reason": "Proxy outcome data cannot establish ANC or gestational predictions; standalone research scripts remain archived."}

    results["artifacts"] = {
        "FetalWatch Serving": (ROOT / "artifacts" / "serving" / "fetalwatch" / "pipeline-v1.joblib").exists(),
        "MaternalGuard Serving": (ROOT / "artifacts" / "serving" / "maternalguard" / "pipeline-v1.joblib").exists(),
        "FetalWatch Model": (ROOT / "artifacts" / "fetalwatch" / "best_model.joblib").exists(),
        "MaternalGuard Model": (ROOT / "artifacts" / "maternalguard" / "best_model.joblib").exists(),
        "CareReach Model": (ROOT / "artifacts" / "carereach" / "best_model.joblib").exists(),
        "GestationInsight Model": (ROOT / "artifacts" / "gestationinsight" / "best_model.joblib").exists(),
    }
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", choices=["maternalguard", "fetalwatch", "all"], default="all")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "artifacts" / "serving")
    args = parser.parse_args()
    for name in (["maternalguard", "fetalwatch"] if args.model == "all" else [args.model]):
        train_model(name, args.data_dir, args.output_dir)


if __name__ == "__main__":
    main()
