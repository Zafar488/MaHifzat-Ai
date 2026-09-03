"""Generate notebooks/02_pipeline_demo.ipynb programmatically via nbformat."""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import nbformat as nbf

nb = nbf.v4.new_notebook()
nb.metadata = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    },
    "language_info": {"name": "python", "version": "3.10"},
}

cells = []


def md(source: str) -> None:
    cells.append(nbf.v4.new_markdown_cell(source.strip()))


def code(source: str) -> None:
    cells.append(nbf.v4.new_code_cell(source.strip()))


# ── Cell 1 — Title ────────────────────────────────────────────────────────────
md("""
# 🏥 End-to-End Pipeline Demo — FetalWatch & MaternalGuard

This notebook runs the complete pipeline for both models:

1. Load datasets (UCI CTG + UCI Maternal Health Risk)
2. Preprocess (split → scale → balance)
3. Train FetalWatch (LightGBM / RF / XGBoost) — `n_trials=5` for demo speed
4. Train MaternalGuard (LightGBM / LogisticRegression) — `n_trials=5`
5. Evaluate both pipelines (confusion matrix, ROC, SHAP, feature importance)
6. Compare all models in a summary table
""")

# ── Cell 2 — Setup ────────────────────────────────────────────────────────────
code("""
import sys, os, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.getcwd(), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

warnings.filterwarnings("ignore")
sns.set_style("whitegrid")
%matplotlib inline

PLOTS_DIR = os.path.join(os.getcwd(), "plots")
os.makedirs(PLOTS_DIR, exist_ok=True)
print(f"Project root : {PROJECT_ROOT}")
print(f"Plots saved to: {PLOTS_DIR}")
""")

# ── Cell 3 — Load Data (markdown) ─────────────────────────────────────────────
md("""
## 1 · Load Data

Load the UCI Cardiotocography (CTG) dataset for FetalWatch and the UCI Maternal
Health Risk dataset for MaternalGuard using the project's data loaders.
""")

# ── Cell 4 — Load Data (code) ─────────────────────────────────────────────────
code("""
from src.data.loaders.uci_ctg import load_uci_ctg
from src.data.loaders.uci_maternal import load_uci_maternal

DATA_DIR = os.path.join(PROJECT_ROOT, "data")

X_ctg, y_ctg = load_uci_ctg(data_dir=DATA_DIR)
X_mat, y_mat = load_uci_maternal(data_dir=DATA_DIR)

print("=== UCI CTG (FetalWatch) ===")
print(f"  Samples : {X_ctg.shape[0]}")
print(f"  Features: {X_ctg.shape[1]}")
print(f"  Classes : {sorted(y_ctg.unique())}")
print(f"  Distribution:\\n{y_ctg.value_counts().to_string()}")
print()
print("=== UCI Maternal Health Risk (MaternalGuard) ===")
print(f"  Samples : {X_mat.shape[0]}")
print(f"  Features: {X_mat.shape[1]}")
print(f"  Classes : {sorted(y_mat.unique())}")
print(f"  Distribution:\\n{y_mat.value_counts().to_string()}")
""")

# ── Cell 5 — Preprocess (markdown) ────────────────────────────────────────────
md("""
## 2 · Preprocess

Apply the standardised preprocessing pipeline:
stratified split (70/15/15) → RobustScaler → SMOTE oversampling.
""")

# ── Cell 6 — Preprocess CTG ───────────────────────────────────────────────────
code("""
from src.data.preprocessing import preprocess_pipeline, split_data, scale_features, handle_imbalance
from sklearn.preprocessing import LabelEncoder

# ── FetalWatch (CTG) preprocessing ─────────────────────────────────────────────
prep_ctg = preprocess_pipeline(
    X_ctg, y_ctg,
    scale=True, balance="smote",
    test_size=0.15, val_size=0.15,
    random_state=42, scale_method="robust",
)
X_train_ctg, X_val_ctg, X_test_ctg = prep_ctg["X_train"], prep_ctg["X_val"], prep_ctg["X_test"]
y_train_ctg, y_val_ctg, y_test_ctg = prep_ctg["y_train"], prep_ctg["y_val"], prep_ctg["y_test"]

print("[CTG] Split sizes:")
print(f"  Train: {len(X_train_ctg)}  |  Val: {len(X_val_ctg)}  |  Test: {len(X_test_ctg)}")
print(f"  Train class distribution (after SMOTE):\\n{y_train_ctg.value_counts().to_string()}")

# ── MaternalGuard preprocessing ────────────────────────────────────────────────
le_mat = LabelEncoder()
y_mat_enc = pd.Series(le_mat.fit_transform(y_mat), name=y_mat.name)
label_map_mat = dict(zip(le_mat.classes_, le_mat.transform(le_mat.classes_)))
print(f"\\n[Maternal] Label mapping: {label_map_mat}")

X_train_m, X_val_m, X_test_m, y_train_m, y_val_m, y_test_m = split_data(
    X_mat, y_mat_enc, test_size=0.15, val_size=0.15, random_state=42,
)
X_train_m, X_val_m, X_test_m, scaler_m = scale_features(
    X_train_m, X_val_m, X_test_m, method="robust",
)
X_train_m, y_train_m = handle_imbalance(X_train_m, y_train_m, method="smote", random_state=42)

print(f"\\n[Maternal] Split sizes:")
print(f"  Train: {len(X_train_m)}  |  Val: {len(X_val_m)}  |  Test: {len(X_test_m)}")
""")

# ── Cell 7 — Train FetalWatch (markdown) ──────────────────────────────────────
md("""
## 3 · Train FetalWatch

Run the FetalWatch pipeline (LightGBM + Random Forest + XGBoost) with
`n_trials=5` Optuna trials for fast demo execution.
""")

# ── Cell 8 — Train FetalWatch (code) ──────────────────────────────────────────
code("""
from src.models.fetal_watch import train_fetal_watch

fetal_results = train_fetal_watch(data_dir=DATA_DIR, n_trials=5)
print("\\nFetalWatch pipeline complete.")
print(f"Best model: {max(fetal_results, key=lambda k: fetal_results[k]['macro_f1'])}")
""")

# ── Cell 9 — Train MaternalGuard (markdown) ───────────────────────────────────
md("""
## 4 · Train MaternalGuard

Run the MaternalGuard pipeline (LightGBM + Logistic Regression) with
`n_trials=5` for demo speed.
""")

# ── Cell 10 — Train MaternalGuard (code) ──────────────────────────────────────
code("""
from src.models.maternal_guard import train_maternal_guard

maternal_results = train_maternal_guard(data_dir=DATA_DIR, n_trials=5)
print("\\nMaternalGuard pipeline complete.")
print(f"Best model: {maternal_results['best_model']}  |  Macro-F1: {maternal_results['best_macro_f1']:.4f}")
""")

# ── Cell 11 — Evaluate FetalWatch (markdown) ──────────────────────────────────
md("""
## 5 · Evaluate FetalWatch

Generate confusion matrix, ROC curves, feature-importance chart, and SHAP
summary for the best FetalWatch model.
""")

# ── Cell 12 — Evaluate FetalWatch (code) ──────────────────────────────────────
code("""
import joblib
from src.evaluation.metrics import (
    plot_confusion_matrix,
    plot_roc_curves,
    plot_feature_importance,
    plot_calibration_curves,
    generate_classification_report,
    generate_shap_summary,
    compare_models,
)

# Reload the best FetalWatch model and the preprocessed test split
fw_model = joblib.load(os.path.join(PROJECT_ROOT, "artifacts", "fetalwatch", "best_model.joblib"))

# Re-run preprocessing to get aligned test labels (deterministic with random_state=42)
prep_fw = preprocess_pipeline(
    X_ctg, y_ctg, scale=True, balance="smote",
    test_size=0.15, val_size=0.15, random_state=42, scale_method="robust",
)
X_test_fw, y_test_fw = prep_fw["X_test"], prep_fw["y_test"]
y_pred_fw = fw_model.predict(X_test_fw)
y_proba_fw = fw_model.predict_proba(X_test_fw)
fw_labels = sorted(y_ctg.unique())

# ── Confusion matrix ──────────────────────────────────────────────────────────
plot_confusion_matrix(
    y_test_fw, y_pred_fw, labels=fw_labels,
    title="FetalWatch — Confusion Matrix",
    save_path=os.path.join(PLOTS_DIR, "fw_confusion_matrix.png"),
)

# ── ROC curves ─────────────────────────────────────────────────────────────────
plot_roc_curves(
    y_test_fw, y_proba_fw, labels=fw_labels,
    title="FetalWatch — ROC Curves (OVR)",
    save_path=os.path.join(PLOTS_DIR, "fw_roc_curves.png"),
)

# ── Feature importance ─────────────────────────────────────────────────────────
plot_feature_importance(
    fw_model, feature_names=list(X_ctg.columns), top_n=15,
    title="FetalWatch — Feature Importance",
    save_path=os.path.join(PLOTS_DIR, "fw_feature_importance.png"),
)

# ── Calibration curves ─────────────────────────────────────────────────────────
plot_calibration_curves(
    y_test_fw, y_proba_fw, labels=fw_labels,
    title="FetalWatch — Calibration Curves",
    save_path=os.path.join(PLOTS_DIR, "fw_calibration.png"),
)

# ── Classification report ──────────────────────────────────────────────────────
fw_report = generate_classification_report(
    y_test_fw, y_pred_fw, labels=fw_labels, model_name="FetalWatch",
)
print(fw_report["classification_report"])
print(f"Macro-F1   : {fw_report['macro_f1']:.4f}")
print(f"Weighted-F1: {fw_report['weighted_f1']:.4f}")

# ── SHAP summary ───────────────────────────────────────────────────────────────
generate_shap_summary(
    fw_model, X_test_fw, feature_names=list(X_ctg.columns),
    save_path=os.path.join(PLOTS_DIR, "fw_shap_summary.png"),
)
print("\\nAll FetalWatch evaluation plots saved to:", PLOTS_DIR)
""")

# ── Cell 13 — Evaluate MaternalGuard (markdown) ───────────────────────────────
md("""
## 6 · Evaluate MaternalGuard

Same evaluation suite for the best MaternalGuard model.
""")

# ── Cell 14 — Evaluate MaternalGuard (code) ───────────────────────────────────
code("""
# Reload best MaternalGuard model + label encoder
mg_model = joblib.load(os.path.join(PROJECT_ROOT, "artifacts", "maternalguard", "best_model.joblib"))
mg_le    = joblib.load(os.path.join(PROJECT_ROOT, "artifacts", "maternalguard", "label_encoder.joblib"))
mg_labels = list(mg_le.classes_)

# Re-run preprocessing for aligned test split
X_tr_m2, X_val_m2, X_test_m2, y_tr_m2, y_val_m2, y_test_m2 = split_data(
    X_mat, pd.Series(mg_le.transform(y_mat), name=y_mat.name),
    test_size=0.15, val_size=0.15, random_state=42,
)
X_tr_m2, X_val_m2, X_test_m2, _ = scale_features(X_tr_m2, X_val_m2, X_test_m2, method="robust")

y_pred_mg = mg_model.predict(X_test_m2)
y_proba_mg = mg_model.predict_proba(X_test_m2)

# ── Confusion matrix ──────────────────────────────────────────────────────────
plot_confusion_matrix(
    y_test_m2, y_pred_mg, labels=mg_labels,
    title="MaternalGuard — Confusion Matrix",
    save_path=os.path.join(PLOTS_DIR, "mg_confusion_matrix.png"),
)

# ── ROC curves ─────────────────────────────────────────────────────────────────
plot_roc_curves(
    y_test_m2, y_proba_mg, labels=mg_labels,
    title="MaternalGuard — ROC Curves (OVR)",
    save_path=os.path.join(PLOTS_DIR, "mg_roc_curves.png"),
)

# ── Feature importance ─────────────────────────────────────────────────────────
plot_feature_importance(
    mg_model, feature_names=list(X_mat.columns), top_n=10,
    title="MaternalGuard — Feature Importance",
    save_path=os.path.join(PLOTS_DIR, "mg_feature_importance.png"),
)

# ── Calibration curves ─────────────────────────────────────────────────────────
plot_calibration_curves(
    y_test_m2, y_proba_mg, labels=mg_labels,
    title="MaternalGuard — Calibration Curves",
    save_path=os.path.join(PLOTS_DIR, "mg_calibration.png"),
)

# ── Classification report ──────────────────────────────────────────────────────
mg_report = generate_classification_report(
    y_test_m2, y_pred_mg, labels=mg_labels, model_name="MaternalGuard",
)
print(mg_report["classification_report"])
print(f"Macro-F1   : {mg_report['macro_f1']:.4f}")
print(f"Weighted-F1: {mg_report['weighted_f1']:.4f}")

# ── SHAP summary ───────────────────────────────────────────────────────────────
generate_shap_summary(
    mg_model, X_test_m2, feature_names=list(X_mat.columns),
    save_path=os.path.join(PLOTS_DIR, "mg_shap_summary.png"),
)
print("\\nAll MaternalGuard evaluation plots saved to:", PLOTS_DIR)
""")

# ── Cell 15 — Model Comparison (markdown) ─────────────────────────────────────
md("""
## 7 · Model Comparison

Compare all trained models across both pipelines in a single summary table.
""")

# ── Cell 16 — Model Comparison (code) ─────────────────────────────────────────
code("""
# Build unified comparison dict
all_results = {}

# FetalWatch models
for model_name, m in fetal_results.items():
    all_results[f"FetalWatch / {model_name}"] = {
        "macro_f1": m["macro_f1"],
        "auroc": m.get("auroc_ovr_macro"),
        "per_class": m.get("per_class", {}),
    }

# MaternalGuard models
for model_name, m in maternal_results.get("models", {}).items():
    all_results[f"MaternalGuard / {model_name}"] = {
        "macro_f1": m["macro_f1"],
        "auroc": m.get("auroc_ovr"),
        "per_class": m.get("per_class", {}),
    }

comparison_df = compare_models(
    all_results,
    save_path=os.path.join(PLOTS_DIR, "model_comparison.csv"),
)
comparison_df
""")

# ── Cell 17 — Summary (markdown) ──────────────────────────────────────────────
md("""
## 8 · Summary & Next Steps

### Key Findings
- **FetalWatch** (UCI CTG — 3-class fetal health): LightGBM with Optuna HPO
  typically achieves the best macro-F1, outperforming the Random Forest
  baseline and XGBoost.
- **MaternalGuard** (UCI Maternal — 3-class risk level): LightGBM generally
  outperforms Logistic Regression, especially on the minority classes.

### Observations
- Class imbalance (especially for "Pathological" and "high risk") remains a
  challenge; SMOTE helps but more data or alternative sampling strategies
  (ADASYN, class-weighted loss tuning) could improve minority-class recall.
- SHAP analysis highlights which CTG features and maternal vital signs drive
  predictions — useful for clinical interpretability.

### Next Steps
1. **PreTermGuard** — integrate the PhysioNet CTU-UHB dataset for preterm
   birth prediction.
2. **Ensemble** — combine FetalWatch + MaternalGuard predictions for a
   holistic risk dashboard.
3. **Deployment** — wrap models in a FastAPI service with a Streamlit UI.
4. **External validation** — test on held-out clinical data to assess
   generalisation.
""")

# ── Assemble notebook ─────────────────────────────────────────────────────────
nb.cells = cells

out_path = os.path.join(os.path.dirname(__file__), "..", "notebooks", "02_pipeline_demo.ipynb")
with open(out_path, "w", encoding="utf-8") as fh:
    nbf.write(nb, fh)

print(f"Notebook written to: {out_path}")
