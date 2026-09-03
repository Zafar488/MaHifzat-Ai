"""Model evaluation metrics and reporting.

Provides reusable functions for generating confusion matrices, ROC curves,
feature-importance charts, calibration plots, SHAP summaries, classification
reports, and model-comparison tables.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Sequence, Union

import matplotlib

matplotlib.use("Agg")  # safe headless default
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
    auc,
)

# Consistent clean style
sns.set_style("whitegrid")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _save_and_close(fig: plt.Figure, save_path: Optional[str]) -> None:
    """Save figure to *save_path* (if given) and close it to free memory."""
    if save_path is not None:
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 1. Confusion matrix
# ---------------------------------------------------------------------------

def plot_confusion_matrix(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    labels: Sequence[str],
    title: str = "",
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot a normalised confusion-matrix heatmap with counts and percentages.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground-truth labels.
    y_pred : array-like of shape (n_samples,)
        Predicted labels.
    labels : sequence of str
        Display names for each class (must match unique values in *y_true*).
    title : str, optional
        Plot title.
    save_path : str, optional
        If provided, save the figure to this path.

    Returns
    -------
    fig : matplotlib.figure.Figure
        The generated figure (already closed if *save_path* was given).
    """
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    cm_norm = cm.astype("float") / cm.sum(axis=1, keepdims=True)
    cm_norm = np.nan_to_num(cm_norm)

    fig, ax = plt.subplots(figsize=(7, 6))
    sns.heatmap(
        cm_norm,
        annot=True,
        fmt=".2%",
        cmap="Blues",
        xticklabels=labels,
        yticklabels=labels,
        vmin=0,
        vmax=1,
        ax=ax,
        cbar_kws={"label": "Recall %"},
    )
    # Overlay raw counts
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(
                j + 0.5,
                i + 0.78,
                f"(n={cm[i, j]})",
                ha="center",
                va="center",
                fontsize=8,
                color="grey",
            )

    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title(title or "Confusion Matrix (Normalised)")
    fig.tight_layout()
    _save_and_close(fig, save_path)
    return fig


# ---------------------------------------------------------------------------
# 2. ROC curves (one-vs-rest)
# ---------------------------------------------------------------------------

def plot_roc_curves(
    y_true: np.ndarray,
    y_score: np.ndarray,
    labels: Sequence[str],
    title: str = "",
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Plot one-vs-rest ROC curves for a multiclass classifier.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground-truth labels (raw class values, not one-hot).
    y_score : ndarray of shape (n_samples, n_classes)
        Predicted probability matrix (columns aligned with *labels*).
    labels : sequence of str
        Class names; ``labels[i]`` corresponds to column *i* of *y_score*.
    title : str, optional
        Plot title.
    save_path : str, optional
        If provided, save the figure to this path.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    from sklearn.preprocessing import label_binarize

    y_bin = label_binarize(y_true, classes=list(labels))
    n_classes = len(labels)

    fig, ax = plt.subplots(figsize=(7, 6))

    tprs, aucs_list = [], []
    mean_fpr = np.linspace(0, 1, 100)

    for i, cls in enumerate(labels):
        fpr, tpr, _ = roc_curve(y_bin[:, i], y_score[:, i])
        roc_auc = auc(fpr, tpr)
        aucs_list.append(roc_auc)
        interp_tpr = np.interp(mean_fpr, fpr, tpr)
        interp_tpr[0] = 0.0
        tprs.append(interp_tpr)
        ax.plot(fpr, tpr, lw=2, label=f"{cls} (AUC={roc_auc:.3f})")

    # Macro-average
    mean_tpr = np.mean(tprs, axis=0)
    mean_tpr[-1] = 1.0
    macro_auc = np.mean(aucs_list)
    ax.plot(
        mean_fpr,
        mean_tpr,
        lw=2,
        linestyle="--",
        color="grey",
        label=f"Macro avg (AUC={macro_auc:.3f})",
    )
    ax.plot([0, 1], [0, 1], "k--", lw=1, alpha=0.4)
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title(title or "ROC Curves (One-vs-Rest)")
    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    _save_and_close(fig, save_path)
    return fig


# ---------------------------------------------------------------------------
# 3. Feature importance
# ---------------------------------------------------------------------------

def plot_feature_importance(
    model: Any,
    feature_names: Sequence[str],
    top_n: int = 15,
    title: str = "",
    save_path: Optional[str] = None,
) -> plt.Figure:
    """Bar chart of the *top_n* most important features.

    Works with any model that exposes a ``feature_importances_`` attribute
    (LightGBM, XGBoost, Random Forest, etc.).

    Parameters
    ----------
    model : fitted estimator
        Must have ``feature_importances_``.
    feature_names : sequence of str
        Feature names aligned with the model's input columns.
    top_n : int, default 15
        Number of top features to display.
    title : str, optional
        Plot title.
    save_path : str, optional
        If provided, save the figure to this path.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    importances = np.asarray(model.feature_importances_)
    idx = np.argsort(importances)[::-1][:top_n]
    names = [feature_names[i] for i in idx]
    vals = importances[idx]

    fig, ax = plt.subplots(figsize=(8, max(4, top_n * 0.35)))
    ax.barh(range(len(names)), vals[::-1], align="center", color="steelblue")
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names[::-1])
    ax.set_xlabel("Feature Importance")
    ax.set_title(title or f"Top {top_n} Feature Importances")
    fig.tight_layout()
    _save_and_close(fig, save_path)
    return fig


# ---------------------------------------------------------------------------
# 4. Calibration curves
# ---------------------------------------------------------------------------

def plot_calibration_curves(
    y_true: np.ndarray,
    y_proba: np.ndarray,
    labels: Sequence[str],
    title: str = "",
    save_path: Optional[str] = None,
    n_bins: int = 10,
) -> plt.Figure:
    """Plot calibration (reliability) curves for each class.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground-truth labels.
    y_proba : ndarray of shape (n_samples, n_classes)
        Predicted probability matrix.
    labels : sequence of str
        Class names aligned with columns of *y_proba*.
    title : str, optional
        Plot title.
    save_path : str, optional
        If provided, save the figure to this path.
    n_bins : int, default 10
        Number of bins used by ``calibration_curve``.

    Returns
    -------
    fig : matplotlib.figure.Figure
    """
    from sklearn.preprocessing import label_binarize

    y_bin = label_binarize(y_true, classes=list(labels))
    fig, ax = plt.subplots(figsize=(7, 6))

    for i, cls in enumerate(labels):
        prob_true, prob_pred = calibration_curve(
            y_bin[:, i], y_proba[:, i], n_bins=n_bins, strategy="uniform"
        )
        ax.plot(prob_pred, prob_true, marker="o", lw=2, label=cls)

    ax.plot([0, 1], [0, 1], "k--", lw=1, label="Perfectly calibrated")
    ax.set_xlabel("Mean Predicted Probability")
    ax.set_ylabel("Fraction of Positives")
    ax.set_title(title or "Calibration Curves")
    ax.legend(loc="lower right", fontsize=9)
    fig.tight_layout()
    _save_and_close(fig, save_path)
    return fig


# ---------------------------------------------------------------------------
# 5. Classification report
# ---------------------------------------------------------------------------

def generate_classification_report(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    labels: Sequence[str],
    model_name: str = "",
) -> Dict[str, Any]:
    """Generate a structured classification report.

    Parameters
    ----------
    y_true : array-like
        Ground-truth labels.
    y_pred : array-like
        Predicted labels.
    labels : sequence of str
        Class label names.
    model_name : str, optional
        Human-readable model identifier included in the output dict.

    Returns
    -------
    report_dict : dict
        Keys: ``model_name``, ``classification_report`` (str),
        ``macro_f1``, ``weighted_f1``, ``per_class`` (dict of dicts).
    """
    report = classification_report(
        y_true, y_pred, labels=list(labels), output_dict=True, zero_division=0
    )
    report_str = classification_report(
        y_true, y_pred, labels=list(labels), zero_division=0
    )

    per_class: Dict[str, Dict[str, float]] = {}
    for cls in labels:
        cls_key = str(cls)
        if cls_key in report:
            per_class[cls_key] = {
                "precision": float(report[cls_key]["precision"]),
                "recall": float(report[cls_key]["recall"]),
                "f1-score": float(report[cls_key]["f1-score"]),
                "support": int(report[cls_key]["support"]),
            }

    return {
        "model_name": model_name,
        "classification_report": report_str,
        "macro_f1": float(report["macro avg"]["f1-score"]),
        "weighted_f1": float(report["weighted avg"]["f1-score"]),
        "per_class": per_class,
    }


# ---------------------------------------------------------------------------
# 6. SHAP summary
# ---------------------------------------------------------------------------

def generate_shap_summary(
    model: Any,
    X: Union[np.ndarray, pd.DataFrame],
    feature_names: Sequence[str],
    save_path: Optional[str] = None,
    max_samples: int = 200,
) -> None:
    """Generate a SHAP beeswarm summary plot for a tree-based model.

    Uses ``shap.TreeExplainer``.  For large datasets a random subsample of
    *max_samples* rows is used to keep computation tractable.

    Parameters
    ----------
    model : fitted tree-based estimator
        Must be compatible with ``shap.TreeExplainer``.
    X : ndarray or DataFrame
        Feature matrix used to compute SHAP values.
    feature_names : sequence of str
        Feature names for axis labels.
    save_path : str, optional
        If provided, save the plot to this path.
    max_samples : int, default 200
        Maximum number of rows sampled for SHAP computation.
    """
    import shap

    if isinstance(X, pd.DataFrame):
        X_arr = X.values
    else:
        X_arr = np.asarray(X)

    # Sub-sample for speed
    if X_arr.shape[0] > max_samples:
        rng = np.random.RandomState(42)
        idx = rng.choice(X_arr.shape[0], max_samples, replace=False)
        X_arr = X_arr[idx]

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X_arr)

    # shap_values may be a list (one per class) for multiclass TreeExplainer
    # Use the first class or the array itself for binary
    if isinstance(shap_values, list):
        # Take the SHAP values for the predicted-dominant class (index 0)
        sv = shap_values[0]
    else:
        sv = shap_values

    fig, ax = plt.subplots(figsize=(9, 7))
    plt.sca(ax)
    shap.summary_plot(sv, feature_names=list(feature_names), show=False)
    fig = plt.gcf()
    fig.tight_layout()
    _save_and_close(fig, save_path)


# ---------------------------------------------------------------------------
# 7. Compare models
# ---------------------------------------------------------------------------

def compare_models(
    results_dict: Dict[str, Dict[str, Any]],
    save_path: Optional[str] = None,
) -> pd.DataFrame:
    """Print a formatted comparison table and optionally save as CSV.

    Parameters
    ----------
    results_dict : dict
        ``{model_name: {macro_f1, auroc, per_class_metrics, ...}}``.

        Recognised keys per model entry (all optional — missing keys are
        shown as ``N/A``):

        - ``macro_f1``      — float
        - ``auroc`` or ``auroc_ovr_macro`` or ``auroc_ovr`` — float
        - ``weighted_f1``   — float
        - ``per_class``     — dict of per-class dicts
    save_path : str, optional
        If provided, save the comparison table as a CSV file.

    Returns
    -------
    df : pd.DataFrame
        The comparison table.
    """
    rows = []
    for name, m in results_dict.items():
        auroc = m.get("auroc") or m.get("auroc_ovr_macro") or m.get("auroc_ovr")
        row = {
            "Model": name,
            "Macro-F1": m.get("macro_f1"),
            "Weighted-F1": m.get("weighted_f1"),
            "AUROC (OVR)": auroc,
        }
        # Per-class recall
        per_class = m.get("per_class", {})
        for cls, cls_m in per_class.items():
            row[f"Recall_{cls}"] = cls_m.get("recall")
        rows.append(row)

    df = pd.DataFrame(rows)

    # Pretty-print
    print("\n" + "=" * 70)
    print("  MODEL COMPARISON")
    print("=" * 70)
    print(df.to_string(index=False, float_format="%.4f", na_rep="N/A"))
    print("=" * 70 + "\n")

    if save_path is not None:
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
        df.to_csv(save_path, index=False, float_format="%.4f")
        print(f"  [Saved] Comparison table -> {save_path}")

    return df
