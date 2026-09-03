"""Shared preprocessing functions for all datasets."""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional, Tuple, Union

import numpy as np
import pandas as pd
from imblearn.over_sampling import ADASYN, SMOTE
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import (
    MinMaxScaler,
    RobustScaler,
    StandardScaler,
)

# ──────────────────────────────────────────────────────────────────────────────
# Stratified train / val / test split
# ──────────────────────────────────────────────────────────────────────────────


def split_data(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.15,
    val_size: float = 0.15,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """Perform stratified train / validation / test splits.

    The function carries out two sequential stratified splits:

    1. Full data → (train+val) vs test  (`test_size`)
    2. (train+val) → train vs val        (`val_size / (1 - test_size)`)

    Parameters
    ----------
    X : pd.DataFrame
        Feature matrix.
    y : pd.Series
        Target labels.
    test_size : float, default 0.15
        Fraction of the full dataset reserved for testing.
    val_size : float, default 0.15
        Fraction of the full dataset reserved for validation.
    random_state : int, default 42
        Seed for reproducibility.

    Returns
    -------
    X_train, X_val, X_test, y_train, y_val, y_test
        Six objects representing the three splits.
    """
    # First split: separate test set
    X_trainval, X_test, y_trainval, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    # Second split: separate validation set from the remaining data
    # Adjust val_size relative to the trainval portion
    adjusted_val_size = val_size / (1.0 - test_size)
    X_train, X_val, y_train, y_val = train_test_split(
        X_trainval,
        y_trainval,
        test_size=adjusted_val_size,
        random_state=random_state,
        stratify=y_trainval,
    )

    return X_train, X_val, X_test, y_train, y_val, y_test


# ──────────────────────────────────────────────────────────────────────────────
# Feature scaling
# ──────────────────────────────────────────────────────────────────────────────

ScalerType = Union[RobustScaler, StandardScaler, MinMaxScaler]


def scale_features(
    X_train: pd.DataFrame,
    X_val: Optional[pd.DataFrame] = None,
    X_test: Optional[pd.DataFrame] = None,
    method: Literal["robust", "standard", "minmax"] = "robust",
) -> Tuple[pd.DataFrame, Optional[pd.DataFrame], Optional[pd.DataFrame], ScalerType]:
    """Fit a scaler on the training set and transform all provided splits.

    Parameters
    ----------
    X_train : pd.DataFrame
        Training feature matrix (used to *fit* the scaler).
    X_val : pd.DataFrame, optional
        Validation feature matrix.
    X_test : pd.DataFrame, optional
        Test feature matrix.
    method : {'robust', 'standard', 'minmax'}, default 'robust'
        Scaling strategy:
        - ``'robust'``   → :class:`~sklearn.preprocessing.RobustScaler`
        - ``'standard'`` → :class:`~sklearn.preprocessing.StandardScaler`
        - ``'minmax'``   → :class:`~sklearn.preprocessing.MinMaxScaler`

    Returns
    -------
    X_train_scaled, X_val_scaled, X_test_scaled, scaler
        Scaled DataFrames (with original column names and index preserved)
        and the fitted scaler instance.
    """
    scaler_map: Dict[str, type] = {
        "robust": RobustScaler,
        "standard": StandardScaler,
        "minmax": MinMaxScaler,
    }
    if method not in scaler_map:
        raise ValueError(
            f"Unknown scaling method '{method}'. "
            f"Choose from: {list(scaler_map)}"
        )

    scaler = scaler_map[method]()
    scaler.fit(X_train)

    def _transform(df: pd.DataFrame) -> pd.DataFrame:
        arr = scaler.transform(df)
        return pd.DataFrame(arr, columns=df.columns, index=df.index)

    X_train_scaled = _transform(X_train)
    X_val_scaled = _transform(X_val) if X_val is not None else None
    X_test_scaled = _transform(X_test) if X_test is not None else None

    return X_train_scaled, X_val_scaled, X_test_scaled, scaler


# ──────────────────────────────────────────────────────────────────────────────
# Class-imbalance handling
# ──────────────────────────────────────────────────────────────────────────────


def handle_imbalance(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    method: Literal["smote", "adasyn", "none"] = "smote",
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.Series]:
    """Resample the training set to address class imbalance.

    Parameters
    ----------
    X_train : pd.DataFrame
        Training feature matrix.
    y_train : pd.Series
        Training labels.
    method : {'smote', 'adasyn', 'none'}, default 'smote'
        Oversampling strategy:
        - ``'smote'``  → SMOTE
        - ``'adasyn'`` → ADASYN
        - ``'none'``   → no resampling (returns inputs unchanged)
    random_state : int, default 42
        Seed for reproducibility.

    Returns
    -------
    X_resampled : pd.DataFrame
        Resampled feature matrix.
    y_resampled : pd.Series
        Resampled labels.
    """
    if method == "none":
        return X_train.copy(), y_train.copy()

    sampler_map: Dict[str, Any] = {
        "smote": SMOTE(random_state=random_state),
        "adasyn": ADASYN(random_state=random_state),
    }

    if method not in sampler_map:
        raise ValueError(
            f"Unknown imbalance method '{method}'. "
            f"Choose from: {list(sampler_map) + ['none']}"
        )

    sampler = sampler_map[method]
    X_res, y_res = sampler.fit_resample(X_train, y_train)

    # Restore pandas types
    X_resampled = pd.DataFrame(X_res, columns=X_train.columns)
    y_resampled = pd.Series(y_res, name=y_train.name)

    return X_resampled, y_resampled


# ──────────────────────────────────────────────────────────────────────────────
# Convenience pipeline
# ──────────────────────────────────────────────────────────────────────────────


def preprocess_pipeline(
    X: pd.DataFrame,
    y: pd.Series,
    scale: bool = True,
    balance: Literal["smote", "adasyn", "none"] = "smote",
    test_size: float = 0.15,
    val_size: float = 0.15,
    random_state: int = 42,
    scale_method: Literal["robust", "standard", "minmax"] = "robust",
) -> Dict[str, Any]:
    """Chain split → scale → balance into a single convenience call.

    Parameters
    ----------
    X : pd.DataFrame
        Full feature matrix.
    y : pd.Series
        Full target labels.
    scale : bool, default True
        Whether to apply feature scaling.
    balance : {'smote', 'adasyn', 'none'}, default 'smote'
        Class-imbalance handling strategy applied to the training split.
    test_size : float, default 0.15
        Fraction of the full dataset reserved for testing.
    val_size : float, default 0.15
        Fraction of the full dataset reserved for validation.
    random_state : int, default 42
        Seed for reproducibility.
    scale_method : {'robust', 'standard', 'minmax'}, default 'robust'
        Scaling strategy (only used when ``scale=True``).

    Returns
    -------
    result : dict
        Dictionary with the following keys:

        - ``X_train``, ``X_val``, ``X_test``
        - ``y_train``, ``y_val``, ``y_test``
        - ``scaler`` (fitted scaler or ``None``)
    """
    # Step 1 – Split
    X_train, X_val, X_test, y_train, y_val, y_test = split_data(
        X, y, test_size=test_size, val_size=val_size, random_state=random_state
    )

    # Step 2 – Scale
    scaler: Optional[ScalerType] = None
    if scale:
        X_train, X_val, X_test, scaler = scale_features(
            X_train, X_val, X_test, method=scale_method
        )

    # Step 3 – Balance (training set only)
    X_train, y_train = handle_imbalance(
        X_train, y_train, method=balance, random_state=random_state
    )

    return {
        "X_train": X_train,
        "X_val": X_val,
        "X_test": X_test,
        "y_train": y_train,
        "y_val": y_val,
        "y_test": y_test,
        "scaler": scaler,
    }
