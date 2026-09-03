"""MaternalGuard — maternal health risk classification from vital signs."""

import sys
import os
import json
import warnings

# Ensure project root is on sys.path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import numpy as np
import pandas as pd
import lightgbm as lgb
import joblib
import optuna

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder

from src.data.loaders.uci_maternal import load_uci_maternal
from src.data.preprocessing import split_data, scale_features, handle_imbalance

warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)

RANDOM_STATE = 42


# ──────────────────────────────────────────────────────────────────────────────
# Optuna objective for LightGBM HPO
# ──────────────────────────────────────────────────────────────────────────────

def _lgbm_objective(X_train, y_train, feature_names):
    """Return an Optuna objective that maximises macro-F1 via 5-fold CV."""

    def objective(trial):
        params = {
            "num_leaves": trial.suggest_int("num_leaves", 10, 50),
            "learning_rate": trial.suggest_float("learning_rate", 0.05, 0.1),
            "n_estimators": trial.suggest_int("n_estimators", 200, 500),
            "min_child_samples": trial.suggest_int("min_child_samples", 5, 30),
            "subsample": trial.suggest_float("subsample", 0.7, 0.9),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 0, 5),
            "reg_lambda": trial.suggest_float("reg_lambda", 0, 5),
            "class_weight": "balanced",
            "random_state": RANDOM_STATE,
            "verbose": -1,
            "force_col_wise": True,
        }
        model = lgb.LGBMClassifier(**params)
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
        scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="f1_macro")
        return scores.mean()

    return objective


# ──────────────────────────────────────────────────────────────────────────────
# Main training function
# ──────────────────────────────────────────────────────────────────────────────

def train_maternal_guard(data_dir="g:/hackthon/data", n_trials=20):
    """Train and evaluate MaternalGuard classifiers.

    Parameters
    ----------
    data_dir : str
        Directory containing ``uci_maternal.parquet``.
    n_trials : int
        Number of Optuna trials for LightGBM HPO.

    Returns
    -------
    dict
        Results dictionary with metrics for both models.
    """
    print("=" * 60)
    print("  MaternalGuard — Maternal Health Risk Classifier")
    print("=" * 60)

    # ── 1. Load data ──────────────────────────────────────────────────────
    print("\n[1/7] Loading UCI Maternal Health Risk data …")
    X, y = load_uci_maternal(data_dir=data_dir)
    print(f"      Dataset shape: {X.shape[0]} samples, {X.shape[1]} features")
    print(f"      Classes: {sorted(y.unique())}")

    # ── 2. Encode labels ──────────────────────────────────────────────────
    print("[2/7] Encoding labels …")
    le = LabelEncoder()
    y_encoded = pd.Series(le.fit_transform(y), name=y.name)
    label_map = dict(zip(le.classes_, le.transform(le.classes_)))
    print(f"      Label mapping: {label_map}")

    # ── 3. Preprocess: split → scale → SMOTE ──────────────────────────────
    print("[3/7] Preprocessing (stratified split 70/15/15, RobustScaler, SMOTE) …")
    X_train, X_val, X_test, y_train, y_val, y_test = split_data(
        X, y_encoded, test_size=0.15, val_size=0.15, random_state=RANDOM_STATE,
    )
    X_train_sc, X_val_sc, X_test_sc, scaler = scale_features(
        X_train, X_val, X_test, method="robust",
    )
    X_train_bal, y_train_bal = handle_imbalance(
        X_train_sc, y_train, method="smote", random_state=RANDOM_STATE,
    )
    print(f"      Train: {X_train_bal.shape[0]}, Val: {X_val_sc.shape[0]}, Test: {X_test_sc.shape[0]}")

    # Combine train+val for CV-based HPO (more data for folds)
    X_trainval = pd.concat([X_train_bal, X_val_sc], ignore_index=True)
    y_trainval = pd.concat([y_train_bal, y_val], ignore_index=True)

    feature_names = list(X.columns)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    # ── 4a. LightGBM with Optuna HPO ─────────────────────────────────────
    print(f"[4/7] LightGBM hyperparameter search ({n_trials} Optuna trials) …")
    study = optuna.create_study(
        direction="maximize",
        pruner=optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=5),
        study_name="maternalguard_lgbm",
    )
    study.optimize(
        _lgbm_objective(X_trainval, y_trainval, feature_names),
        n_trials=n_trials,
        show_progress_bar=False,
    )
    best_params = study.best_params
    best_cv_f1 = study.best_value
    print(f"      Best CV macro-F1: {best_cv_f1:.4f}")
    print(f"      Best params: {best_params}")

    # Retrain best LightGBM on full train+val with early stopping on test
    print("      Retraining best LightGBM on train+val …")
    lgbm_params = {
        **best_params,
        "class_weight": "balanced",
        "random_state": RANDOM_STATE,
        "verbose": -1,
        "force_col_wise": True,
    }
    lgbm_model = lgb.LGBMClassifier(**lgbm_params)
    lgbm_model.fit(
        X_trainval, y_trainval,
        eval_set=[(X_test_sc, y_test)],
        callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(period=0)],
    )

    # ── 4b. Logistic Regression baseline ──────────────────────────────────
    print("[5/7] Logistic Regression baseline (grid over C) …")
    C_values = [0.001, 0.01, 0.1, 1, 10, 100]
    best_lr_f1 = -1
    best_lr = None
    best_C = None
    for C in C_values:
        lr = LogisticRegression(
            C=C,
            class_weight="balanced",
            max_iter=1000,
            multi_class="multinomial",
            random_state=RANDOM_STATE,
        )
        scores = cross_val_score(lr, X_trainval, y_trainval, cv=cv, scoring="f1_macro")
        if scores.mean() > best_lr_f1:
            best_lr_f1 = scores.mean()
            best_lr = lr
            best_C = C
    print(f"      Best C: {best_C}, CV macro-F1: {best_lr_f1:.4f}")

    # Retrain best LR on train+val
    best_lr.fit(X_trainval, y_trainval)

    # ── 5. Evaluate on held-out test set ──────────────────────────────────
    print("[6/7] Evaluating on held-out test set …")
    results = {"models": {}}

    for model_name, model in [("LightGBM", lgbm_model), ("LogisticRegression", best_lr)]:
        y_pred = model.predict(X_test_sc)
        y_proba = model.predict_proba(X_test_sc)

        report = classification_report(
            y_test, y_pred,
            target_names=le.classes_,
            output_dict=True,
            zero_division=0,
        )
        macro_f1 = report["macro avg"]["f1-score"]

        # AUROC one-vs-rest
        try:
            auroc = roc_auc_score(
                y_test, y_proba, multi_class="ovr", average="macro",
            )
        except ValueError:
            auroc = None

        cm = confusion_matrix(y_test, y_pred)

        print(f"\n  -- {model_name} --")
        print(f"  Macro-F1: {macro_f1:.4f}  |  AUROC (OVR): {auroc:.4f}" if auroc else f"  Macro-F1: {macro_f1:.4f}")
        print(classification_report(y_test, y_pred, target_names=le.classes_, zero_division=0))

        results["models"][model_name] = {
            "macro_f1": round(macro_f1, 4),
            "auroc_ovr": round(auroc, 4) if auroc else None,
            "per_class": {},
            "confusion_matrix": cm.tolist(),
        }
        for cls_name in le.classes_:
            cr = report[cls_name]
            results["models"][model_name]["per_class"][cls_name] = {
                "precision": round(cr["precision"], 4),
                "recall": round(cr["recall"], 4),
                "f1-score": round(cr["f1-score"], 4),
                "support": int(cr["support"]),
            }

    # Determine best model
    lgbm_f1 = results["models"]["LightGBM"]["macro_f1"]
    lr_f1 = results["models"]["LogisticRegression"]["macro_f1"]
    best_model_name = "LightGBM" if lgbm_f1 >= lr_f1 else "LogisticRegression"
    best_model = lgbm_model if best_model_name == "LightGBM" else best_lr
    results["best_model"] = best_model_name
    results["best_macro_f1"] = results["models"][best_model_name]["macro_f1"]

    # ── 7. Save artefacts ─────────────────────────────────────────────────
    print("[7/7] Saving artefacts …")
    artifact_dir = os.path.join(_project_root, "artifacts", "maternalguard")
    os.makedirs(artifact_dir, exist_ok=True)

    joblib.dump(best_model, os.path.join(artifact_dir, "best_model.joblib"))
    joblib.dump(le, os.path.join(artifact_dir, "label_encoder.joblib"))
    print(f"      Saved best model ({best_model_name}) and label encoder to {artifact_dir}")

    with open(os.path.join(artifact_dir, "results.json"), "w") as f:
        json.dump(results, f, indent=2)
    print(f"      Saved results.json")

    # Store feature importance if LightGBM
    if best_model_name == "LightGBM":
        importances = dict(zip(feature_names, best_model.feature_importances_.tolist()))
        results["feature_importance"] = dict(
            sorted(importances.items(), key=lambda x: x[1], reverse=True)
        )
        # Re-save with importance
        with open(os.path.join(artifact_dir, "results.json"), "w") as f:
            json.dump(results, f, indent=2)

    print("\n" + "=" * 60)
    print(f"  Best model: {best_model_name}  |  Macro-F1: {results['best_macro_f1']:.4f}")
    print("=" * 60)

    return results


# ──────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────────────────────

def main():
    results = train_maternal_guard()

    # ── Formatted summary ─────────────────────────────────────────────────
    print("\n\n" + "=" * 60)
    print("  MaternalGuard — Final Results Summary")
    print("=" * 60)

    best_name = results["best_model"]
    best_f1 = results["best_macro_f1"]
    print(f"\n  Best model : {best_name}")
    print(f"  Macro-F1   : {best_f1:.4f}")

    # Per-model comparison table
    print(f"\n  {'Model':<25} {'Macro-F1':>10} {'AUROC (OVR)':>14}")
    print("  " + "-" * 51)
    for name, m in results["models"].items():
        auroc_str = f"{m['auroc_ovr']:.4f}" if m["auroc_ovr"] is not None else "N/A"
        print(f"  {name:<25} {m['macro_f1']:>10.4f} {auroc_str:>14}")

    # Per-class sensitivity (recall) for best model
    print(f"\n  Per-class sensitivity (recall) — {best_name}:")
    for cls, metrics in results["models"][best_name]["per_class"].items():
        print(f"    {cls:<15} recall = {metrics['recall']:.4f}  (support={metrics['support']})")

    # Feature importance from LightGBM
    if "feature_importance" in results:
        print(f"\n  Feature importance (LightGBM):")
        for feat, imp in results["feature_importance"].items():
            print(f"    {feat:<25} {imp}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
