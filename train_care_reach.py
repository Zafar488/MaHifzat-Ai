"""
CareReach — ANC Missed Visit Risk Classifier
Enterprise-grade ML pipeline for predicting appointment no-shows.
"""
import sys
import os
import warnings
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.preprocessing import RobustScaler, LabelEncoder, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    roc_auc_score,
    f1_score,
    precision_recall_curve,
    average_precision_score,
    confusion_matrix,
)
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from imblearn.combine import SMOTETomek
from imblearn.over_sampling import SMOTE
import xgboost as xgb
import lightgbm as lgb
import optuna
import joblib
import shap

sys.path.insert(0, "g:/hackthon")
warnings.filterwarnings("ignore")
optuna.logging.set_verbosity(optuna.logging.WARNING)

# ── Constants ────────────────────────────────────────────────────────────────
RANDOM_STATE: int = 42
DATA_PATH: str = "g:/hackthon/data/carereach_prepared.parquet"
ARTIFACT_DIR: Path = Path("g:/hackthon/artifacts/carereach")
TARGET_COL: str = "target"

DROP_COLS: List[str] = [
    "PatientId",
    "AppointmentID",
    "ScheduledDay",
    "AppointmentDay",
    "Neighbourhood",
    "No-show",
]

NUMERIC_FEATURES: List[str] = [
    "Age",
    "Scholarship",
    "Hipertension",
    "Diabetes",
    "Alcoholism",
    "Handcap",
    "SMS_received",
    "booking_delta_days",
    "appointment_dow",
    "sms_x_delta",
    "comorbidity_count",
]

CATEGORICAL_FEATURES: List[str] = ["Gender", "age_group"]


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_data(path: str) -> pd.DataFrame:
    """Load parquet dataset and print shape."""
    print(f"[1/9] Loading data from {path} ...")
    df = pd.read_parquet(path)
    print(f"       Loaded {df.shape[0]:,} rows × {df.shape[1]} columns")
    return df


def handle_nulls(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with null target; fill age_group nulls with mode."""
    print("[2/9] Handling nulls ...")
    before = len(df)
    df = df.dropna(subset=[TARGET_COL])
    after_target = len(df)
    if before != after_target:
        print(f"       Dropped {before - after_target} rows with null target")

    # age_group: convert Categorical → str, fill NaN with mode
    df["age_group"] = df["age_group"].astype(str).replace("nan", np.nan)
    mode_val = df["age_group"].mode()[0]
    null_count = df["age_group"].isna().sum()
    if null_count > 0:
        df["age_group"] = df["age_group"].fillna(mode_val)
        print(f"       Filled {null_count} age_group nulls with mode '{mode_val}'")

    # Gender: fill if any nulls
    if df["Gender"].isna().any():
        df["Gender"] = df["Gender"].fillna(df["Gender"].mode()[0])

    print(f"       Final shape: {df.shape[0]:,} rows")
    return df


def select_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Select numeric + categorical features; drop IDs and raw dates."""
    print("[3/9] Selecting features ...")
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES].copy()
    y = df[TARGET_COL].copy()

    # Ensure categorical columns are strings for OneHotEncoder
    for col in CATEGORICAL_FEATURES:
        X[col] = X[col].astype(str)

    print(f"       Numeric features:    {len(NUMERIC_FEATURES)}")
    print(f"       Categorical features: {len(CATEGORICAL_FEATURES)}")
    print(f"       Total features:       {X.shape[1]}")
    return X, y


def build_preprocessor() -> ColumnTransformer:
    """Build leak-safe ColumnTransformer with RobustScaler + OneHotEncoder."""
    numeric_transformer = RobustScaler()
    categorical_transformer = OneHotEncoder(
        drop="first", sparse_output=False, handle_unknown="ignore"
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, NUMERIC_FEATURES),
            (
                "cat",
                categorical_transformer,
                CATEGORICAL_FEATURES,
            ),
        ]
    )
    return preprocessor


def stratified_split(
    X: pd.DataFrame, y: pd.Series
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """70/15/15 stratified split."""
    print("[4/9] Stratified split 70/15/15 ...")
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, random_state=RANDOM_STATE, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, random_state=RANDOM_STATE, stratify=y_temp
    )
    print(
        f"       Train: {len(X_train):,}  Val: {len(X_val):,}  Test: {len(X_test):,}"
    )
    return X_train, X_val, X_test, y_train, y_val, y_test


def apply_smote_tomek(
    X_train: pd.DataFrame, y_train: pd.Series
) -> Tuple[pd.DataFrame, pd.Series]:
    """Apply SMOTE-Tomek to training set only."""
    print("[5/9] Applying SMOTE-Tomek on training set ...")
    smote_tomek = SMOTETomek(random_state=RANDOM_STATE)
    X_res, y_res = smote_tomek.fit_resample(X_train, y_train)
    print(
        f"       Resampled: {len(X_res):,} rows "
        f"(class 0: {(y_res == 0).sum():,}, class 1: {(y_res == 1).sum():,})"
    )
    return X_res, y_res


# ── Model Training ───────────────────────────────────────────────────────────

def train_logistic_regression(
    X_train: np.ndarray, y_train: np.ndarray
) -> LogisticRegression:
    """Train ElasticNet logistic regression baseline."""
    print("[6/9] Training LogisticRegression (ElasticNet baseline) ...")
    model = LogisticRegression(
        penalty="elasticnet",
        l1_ratio=0.5,
        C=1.0,
        class_weight="balanced",
        max_iter=1000,
        solver="saga",
        random_state=RANDOM_STATE,
    )
    t0 = time.time()
    model.fit(X_train, y_train)
    print(f"       Done in {time.time() - t0:.1f}s")
    return model


def train_xgboost(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    n_trials: int = 20,
) -> xgb.XGBClassifier:
    """Train XGBoost with Optuna HPO."""
    print(f"[7/9] Training XGBoost with Optuna ({n_trials} trials) ...")
    spw = float((y_train == 0).sum()) / max((y_train == 1).sum(), 1)

    def objective(trial: optuna.Trial) -> float:
        params = {
            "max_depth": trial.suggest_int("max_depth", 3, 8),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "n_estimators": trial.suggest_int("n_estimators", 100, 500, step=50),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "scale_pos_weight": spw,
            "eval_metric": "auc",
            "random_state": RANDOM_STATE,
            "use_label_encoder": False,
            "verbosity": 0,
        }
        model = xgb.XGBClassifier(**params)
        model.fit(
            X_train,
            y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )
        preds = model.predict_proba(X_val)[:, 1]
        return roc_auc_score(y_val, preds)

    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE),
    )
    t0 = time.time()
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    elapsed = time.time() - t0
    print(
        f"       Best XGB AUROC (val): {study.best_value:.4f} "
        f"in {elapsed:.1f}s ({n_trials} trials)"
    )

    best_params = study.best_params
    best_params.update(
        {"scale_pos_weight": spw, "eval_metric": "auc",
         "random_state": RANDOM_STATE, "use_label_encoder": False, "verbosity": 0}
    )
    best_model = xgb.XGBClassifier(**best_params)
    best_model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)
    return best_model


def train_lightgbm(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_val: np.ndarray,
    y_val: np.ndarray,
    n_trials: int = 20,
) -> lgb.LGBMClassifier:
    """Train LightGBM with Optuna HPO."""
    print(f"[8/9] Training LightGBM with Optuna ({n_trials} trials) ...")

    def objective(trial: optuna.Trial) -> float:
        params = {
            "num_leaves": trial.suggest_int("num_leaves", 20, 100),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "n_estimators": trial.suggest_int("n_estimators", 100, 500, step=50),
            "min_child_samples": trial.suggest_int("min_child_samples", 10, 50),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "is_unbalance": True,
            "random_state": RANDOM_STATE,
            "verbose": -1,
        }
        model = lgb.LGBMClassifier(**params)
        model.fit(
            X_train,
            y_train,
            eval_set=[(X_val, y_val)],
            eval_metric="auc",
        )
        preds = model.predict_proba(X_val)[:, 1]
        return roc_auc_score(y_val, preds)

    study = optuna.create_study(
        direction="maximize",
        sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE),
    )
    t0 = time.time()
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    elapsed = time.time() - t0
    print(
        f"       Best LGB AUROC (val): {study.best_value:.4f} "
        f"in {elapsed:.1f}s ({n_trials} trials)"
    )

    best_params = study.best_params
    best_params.update(
        {"is_unbalance": True, "random_state": RANDOM_STATE, "verbose": -1}
    )
    best_model = lgb.LGBMClassifier(**best_params)
    best_model.fit(
        X_train, y_train, eval_set=[(X_val, y_val)], eval_metric="auc"
    )
    return best_model


# ── Evaluation ───────────────────────────────────────────────────────────────

def evaluate_model(
    model: Any,
    X_test: np.ndarray,
    y_test: np.ndarray,
    label: str,
) -> Dict[str, float]:
    """Evaluate model on test set: Macro-F1, AUROC, PR-AUC."""
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    macro_f1 = f1_score(y_test, y_pred, average="macro")
    auroc = roc_auc_score(y_test, y_prob)
    pr_auc = average_precision_score(y_test, y_prob)

    print(f"\n       ── {label} ──")
    print(f"       Macro-F1:  {macro_f1:.4f}")
    print(f"       AUROC:     {auroc:.4f}")
    print(f"       PR-AUC:    {pr_auc:.4f}")
    print(classification_report(y_test, y_pred, target_names=["Showed", "Missed"]))

    return {"macro_f1": macro_f1, "auroc": auroc, "pr_auc": pr_auc}


def save_artifacts(
    best_model: Any,
    preprocessor: ColumnTransformer,
    metrics: Dict[str, Any],
    feature_list: List[str],
    model_name: str,
    y: pd.Series,
) -> None:
    """Save best model, preprocessor, and metadata."""
    print("[9/9] Saving artifacts ...")
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(best_model, ARTIFACT_DIR / "best_model.joblib")
    joblib.dump(preprocessor, ARTIFACT_DIR / "preprocessor.joblib")

    metadata = {
        "training_date": datetime.now().isoformat(),
        "metrics": metrics,
        "feature_list": feature_list,
        "model_name": model_name,
        "version": "1.0.0",
        "class_distribution": {
            "class_0": int((y == 0).sum()),
            "class_1": int((y == 1).sum()),
        },
    }
    with open(ARTIFACT_DIR / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"       Saved to {ARTIFACT_DIR}/")
    print(f"       ├── best_model.joblib")
    print(f"       ├── preprocessor.joblib")
    print(f"       └── metadata.json")


def save_shap_plot(model: Any, X_test: np.ndarray, feature_names: List[str]) -> None:
    """Compute SHAP values and save summary plot."""
    print("       Generating SHAP summary plot ...")
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        if hasattr(model, "feature_importances_"):
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_test)
            # For binary classification, TreeExplainer may return a list
            if isinstance(shap_values, list):
                shap_values = shap_values[1]
        else:
            explainer = shap.Explainer(model, X_test)
            shap_values = explainer(X_test)

        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        plt.figure(figsize=(12, 8))
        shap.summary_plot(
            shap_values,
            X_test,
            feature_names=feature_names,
            show=False,
            plot_size=None,
        )
        plt.tight_layout()
        plt.savefig(ARTIFACT_DIR / "shap_summary.png", dpi=150, bbox_inches="tight")
        plt.close()
        print(f"       Saved SHAP plot → {ARTIFACT_DIR / 'shap_summary.png'}")
    except Exception as e:
        print(f"       SHAP plot generation failed: {e}")


# ── Main Pipeline ────────────────────────────────────────────────────────────

def main() -> None:
    """Run full CareReach ML pipeline."""
    print("=" * 70)
    print("  CareReach — ANC Missed Visit Risk Classifier")
    print("=" * 70)
    t_start = time.time()

    # 1. Load
    df = load_data(DATA_PATH)

    # 2. Handle nulls
    df = handle_nulls(df)

    # 3. Feature selection
    X, y = select_features(df)

    # 4. Stratified split
    X_train, X_val, X_test, y_train, y_val, y_test = stratified_split(X, y)

    # 6. Build preprocessor — fit on training data, transform all splits
    preprocessor = build_preprocessor()
    X_train_proc = preprocessor.fit_transform(X_train)
    X_val_proc = preprocessor.transform(X_val)
    X_test_proc = preprocessor.transform(X_test)

    # Get feature names after preprocessing
    cat_encoder = preprocessor.named_transformers_["cat"]
    cat_features_out = cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES).tolist()
    all_feature_names = NUMERIC_FEATURES + cat_features_out

    # 5. SMOTE-Tomek on preprocessed training data
    X_train_res, y_train_res = apply_smote_tomek(
        pd.DataFrame(X_train_proc, columns=all_feature_names), y_train
    )
    X_train_res = X_train_res.values if hasattr(X_train_res, 'values') else X_train_res
    X_val_np = X_val_proc
    X_test_np = X_test_proc

    # 7. Train models
    # Logistic Regression
    lr_model = train_logistic_regression(X_train_res, y_train_res)

    # XGBoost
    xgb_model = train_xgboost(X_train_res, y_train_res, X_val_np, y_val)

    # LightGBM
    lgb_model = train_lightgbm(X_train_res, y_train_res, X_val_np, y_val)

    # 8. Evaluate on test set
    print("\n" + "=" * 70)
    print("  TEST SET EVALUATION")
    print("=" * 70)

    results: Dict[str, Dict[str, float]] = {}
    results["LogisticRegression"] = evaluate_model(
        lr_model, X_test_np, y_test, "LogisticRegression"
    )
    results["XGBoost"] = evaluate_model(
        xgb_model, X_test_np, y_test, "XGBoost"
    )
    results["LightGBM"] = evaluate_model(
        lgb_model, X_test_np, y_test, "LightGBM"
    )

    # Comparison table
    print("\n" + "=" * 70)
    print("  MODEL COMPARISON")
    print("=" * 70)
    print(f"{'Model':<25} {'Macro-F1':>10} {'AUROC':>10} {'PR-AUC':>10}")
    print("-" * 55)
    for name, m in results.items():
        print(
            f"{name:<25} {m['macro_f1']:>10.4f} "
            f"{m['auroc']:>10.4f} {m['pr_auc']:>10.4f}"
        )

    # Select best model by Macro-F1
    best_name = max(results, key=lambda k: results[k]["macro_f1"])
    best_model_map = {
        "LogisticRegression": lr_model,
        "XGBoost": xgb_model,
        "LightGBM": lgb_model,
    }
    best_model = best_model_map[best_name]
    print(f"\n  ★ Best model: {best_name} "
          f"(Macro-F1={results[best_name]['macro_f1']:.4f})")

    # 9. SHAP
    save_shap_plot(best_model, X_test_np, all_feature_names)

    # 10. Save artifacts
    save_artifacts(
        best_model=best_model,
        preprocessor=preprocessor,
        metrics=results,
        feature_list=all_feature_names,
        model_name=best_name,
        y=y,
    )

    elapsed_total = time.time() - t_start
    print(f"\n  Total pipeline time: {elapsed_total:.1f}s")
    print("=" * 70)


if __name__ == "__main__":
    main()
