"""Loader for PhysioNet CTU-UHB Intrapartum CTG Database."""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import wfdb


DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "ctu-uhb-ctgdb"


def load_physionet_records(
    data_dir: str | Path = DEFAULT_DATA_DIR,
) -> List[Dict[str, Any]]:
    """Load all CTU-UHB CTG recordings from a local directory.

    Each ``.dat`` / ``.hea`` pair is read with :func:`wfdb.rdrecord`.
    Corrupt or missing records are skipped with a warning rather than
    raising an exception, so downstream code always receives a clean list.

    Parameters
    ----------
    data_dir : str or Path, default repo data/ctu-uhb-ctgdb dir
        Directory containing the WFDB ``.dat`` and ``.hea`` files.

    Returns
    -------
    records : list[dict]
        One dict per successfully loaded record with the following keys:

        ``record_name``
            Base name of the record (e.g. ``"1001"``).
        ``fhr_signal``
            Foetal-heart-rate signal as a 1-D :class:`numpy.ndarray`.
        ``uc_signal``
            Uterine-contraction signal as a 1-D :class:`numpy.ndarray`.
        ``fs``
            Sampling frequency in Hz (always ``4`` for this database).
        ``metadata``
            A dict containing record header metadata (``record_name``,
            ``n_sig``, ``fs``, ``sig_len``, ``comments``, …).
    """
    data_dir = Path(data_dir)
    if not data_dir.exists():
        raise FileNotFoundError(
            f"CTU-UHB CTG database directory not found at: {data_dir}"
        )

    # Discover unique record names from .hea files (one per record)
    hea_files = sorted(data_dir.glob("*.hea"))
    records: List[Dict[str, Any]] = []

    for hea_path in hea_files:
        record_name = hea_path.stem  # e.g. "1001"

        try:
            record = wfdb.rdrecord(
                str(data_dir / record_name),
                channels=None,  # all channels
                sampfrom=0,
            )
        except Exception as exc:  # noqa: BLE001
            warnings.warn(
                f"Skipping record '{record_name}': failed to read "
                f"({type(exc).__name__}: {exc})",
                stacklevel=2,
            )
            continue

        # Validate basic expectations: at least 2 signals (FHR + UC)
        if record.p_signal is None or record.p_signal.shape[1] < 2:
            warnings.warn(
                f"Skipping record '{record_name}': expected at least 2 "
                f"signals, got {0 if record.p_signal is None else record.p_signal.shape[1]}",
                stacklevel=2,
            )
            continue

        fhr_signal: np.ndarray = record.p_signal[:, 0].copy()
        uc_signal: np.ndarray = record.p_signal[:, 1].copy()

        metadata: Dict[str, Any] = {
            "record_name": record.record_name,
            "n_sig": record.n_sig,
            "fs": record.fs,
            "sig_len": record.sig_len,
            "comments": record.comments,
            "sig_name": record.sig_name,
        }

        records.append(
            {
                "record_name": record_name,
                "fhr_signal": fhr_signal,
                "uc_signal": uc_signal,
                "fs": int(record.fs) if record.fs else 4,
                "metadata": metadata,
            }
        )

    return records
