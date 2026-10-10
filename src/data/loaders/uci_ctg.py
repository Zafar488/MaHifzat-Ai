"""Loader for UCI Cardiotocography (CTG) Data Set (id=193)."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import pandas as pd

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data"

# NSP label mapping: 1=Normal, 2=Suspect, 3=Pathological
NSP_LABEL_MAP: dict[int, str] = {1: "Normal", 2: "Suspect", 3: "Pathological"}


def load_uci_ctg(
    data_dir: str | Path = DEFAULT_DATA_DIR,
) -> Tuple[pd.DataFrame, pd.Series]:
    """Load the UCI Cardiotocography dataset from a local Parquet file.

    Parameters
    ----------
    data_dir : str or Path, default repo data dir
        Directory that contains ``uci_ctg.parquet``.

    Returns
    -------
    X : pd.DataFrame
        Feature matrix (21 columns) with the ``NSP`` and ``CLASS`` columns
        removed.
    y : pd.Series
        Target labels mapped to human-readable strings
        (``'Normal'``, ``'Suspect'``, ``'Pathological'``).

    Raises
    ------
    FileNotFoundError
        If the Parquet file does not exist at the expected path.
    """
    parquet_path = Path(data_dir) / "uci_ctg.parquet"
    if not parquet_path.exists():
        raise FileNotFoundError(
            f"UCI CTG parquet file not found at: {parquet_path}"
        )

    df = pd.read_parquet(parquet_path)

    # Separate features and target
    feature_cols = [c for c in df.columns if c not in ("NSP", "CLASS")]
    X: pd.DataFrame = df[feature_cols].copy()
    y: pd.Series = df["NSP"].map(NSP_LABEL_MAP).copy()
    y.name = "NSP"

    return X, y
