"""Loader for UCI Maternal Health Risk Data Set (id=863)."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd


def load_uci_maternal(
    data_dir: str | Path = "g:/hackthon/data",
) -> Tuple[pd.DataFrame, pd.Series]:
    """Load the UCI Maternal Health Risk dataset from a local Parquet file.

    Parameters
    ----------
    data_dir : str or Path, default ``"g:/hackthon/data"``
        Directory that contains ``uci_maternal.parquet``.

    Returns
    -------
    X : pd.DataFrame
        Feature matrix (all columns except ``RiskLevel``).
    y : pd.Series
        Risk-level labels (``'low risk'``, ``'mid risk'``, ``'high risk'``).

    Raises
    ------
    FileNotFoundError
        If the Parquet file does not exist at the expected path.
    """
    parquet_path = Path(data_dir) / "uci_maternal.parquet"
    if not parquet_path.exists():
        raise FileNotFoundError(
            f"UCI Maternal parquet file not found at: {parquet_path}"
        )

    df = pd.read_parquet(parquet_path)

    # Separate features and target
    feature_cols = [c for c in df.columns if c != "RiskLevel"]
    X: pd.DataFrame = df[feature_cols].copy()
    y: pd.Series = df["RiskLevel"].copy()
    y.name = "RiskLevel"

    return X, y
