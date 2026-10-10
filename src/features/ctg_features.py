"""Feature engineering for CTG-based fetal health prediction.

Extracts the UCI CTG 21-feature schema from raw 4 Hz CTU-UHB FHR+UC signals
so that models trained on UCI CTG data can also be applied to CTU-UHB recordings.

Feature names match the UCI Cardiotocography dataset columns exactly:
    LB, AC, FM, UC, DL, DS, DP, ASTV, MSTV, ALTV, MLTV,
    Width, Min, Max, Nmax, Nzeros, Mode, Mean, Median, Variance, Tendency
"""

from __future__ import annotations

import os
import warnings
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
import wfdb
from scipy.signal import find_peaks

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

UCI_FEATURE_NAMES: list[str] = [
    "LB", "AC", "FM", "UC", "DL", "DS", "DP",
    "ASTV", "MSTV", "ALTV", "MLTV",
    "Width", "Min", "Max", "Nmax", "Nzeros",
    "Mode", "Mean", "Median", "Variance", "Tendency",
]

# ---------------------------------------------------------------------------
# Helper – baseline detection
# ---------------------------------------------------------------------------


def _detect_baseline(fhr: np.ndarray, fs: int) -> float:
    """Estimate the FHR baseline in bpm.

    The baseline is computed iteratively:
      1. Start with the median of all valid FHR values.
      2. Remove values that are >25 bpm above or >35 bpm below the current
         estimate (these are likely accelerations / decelerations).
      3. Re-compute median until convergence.

    Parameters
    ----------
    fhr : np.ndarray
        1-D FHR signal (bpm).  Invalid samples must already be set to 0 or NaN.
    fs : int
        Sampling frequency in Hz.

    Returns
    -------
    float
        Estimated baseline FHR in bpm.  Returns NaN when no valid data exists.
    """
    valid = fhr[(fhr > 0) & np.isfinite(fhr)]
    if len(valid) == 0:
        return float("nan")

    baseline = float(np.median(valid))
    for _ in range(10):
        mask = (valid > baseline - 35) & (valid < baseline + 25)
        subset = valid[mask]
        if len(subset) == 0:
            break
        new_baseline = float(np.median(subset))
        if abs(new_baseline - baseline) < 0.5:
            baseline = new_baseline
            break
        baseline = new_baseline

    return round(baseline, 1)


# ---------------------------------------------------------------------------
# Helper – acceleration detection
# ---------------------------------------------------------------------------


def _detect_accelerations(
    fhr: np.ndarray, baseline: float, fs: int
) -> list[Tuple[int, int]]:
    """Detect accelerations in the FHR signal.

    An acceleration is defined as the FHR rising ≥15 bpm above the baseline
    for at least 15 seconds.

    Parameters
    ----------
    fhr : np.ndarray
        1-D FHR signal (bpm).
    baseline : float
        Estimated FHR baseline.
    fs : int
        Sampling frequency.

    Returns
    -------
    list of (start_sample, end_sample)
        Index pairs marking each detected acceleration.
    """
    if np.isnan(baseline) or len(fhr) == 0:
        return []

    threshold = baseline + 15
    min_samples = 15 * fs  # 15 seconds

    above = np.zeros(len(fhr), dtype=bool)
    valid_mask = (fhr > 0) & np.isfinite(fhr)
    above[valid_mask] = fhr[valid_mask] >= threshold

    events: list[Tuple[int, int]] = []
    in_event = False
    start = 0
    for i, val in enumerate(above):
        if val and not in_event:
            start = i
            in_event = True
        elif not val and in_event:
            if i - start >= min_samples:
                events.append((start, i))
            in_event = False
    # Handle event that extends to end of signal
    if in_event and len(fhr) - start >= min_samples:
        events.append((start, len(fhr)))

    return events


# ---------------------------------------------------------------------------
# Helper – deceleration detection
# ---------------------------------------------------------------------------


def _detect_decelerations(
    fhr: np.ndarray, baseline: float, fs: int
) -> Tuple[list[dict], list[dict], list[dict]]:
    """Detect decelerations in the FHR signal.

    A deceleration is defined as the FHR dropping ≥15 bpm below the baseline
    for at least 15 seconds.

    Classifications
    ---------------
    - Light deceleration (DL): drop of 15–30 bpm below baseline.
    - Severe deceleration (DS): drop of >30 bpm below baseline.
    - Prolonged deceleration (DP): any deceleration lasting >60 seconds.

    Parameters
    ----------
    fhr : np.ndarray
        1-D FHR signal.
    baseline : float
        Estimated baseline FHR.
    fs : int
        Sampling frequency.

    Returns
    -------
    light, severe, prolonged : lists of dicts
        Each dict has keys ``start``, ``end``, ``depth`` (max drop in bpm).
    """
    if np.isnan(baseline) or len(fhr) == 0:
        return [], [], []

    min_drop = 15
    min_samples = 15 * fs

    valid_fhr = fhr.copy()
    valid_fhr[(valid_fhr <= 0) | ~np.isfinite(valid_fhr)] = np.nan

    drop = baseline - valid_fhr  # positive when FHR is below baseline

    decel_events: list[dict] = []
    in_event = False
    start = 0
    max_drop = 0.0

    for i in range(len(drop)):
        d = drop[i]
        if np.isnan(d):
            # treat gaps as ending event
            if in_event:
                if i - start >= min_samples and max_drop >= min_drop:
                    decel_events.append({
                        "start": start,
                        "end": i,
                        "depth": max_drop,
                    })
                in_event = False
                max_drop = 0.0
            continue

        if d >= min_drop:
            if not in_event:
                start = i
                in_event = True
                max_drop = d
            else:
                max_drop = max(max_drop, d)
        else:
            if in_event:
                if i - start >= min_samples and max_drop >= min_drop:
                    decel_events.append({
                        "start": start,
                        "end": i,
                        "depth": max_drop,
                    })
                in_event = False
                max_drop = 0.0

    # Close any open event
    if in_event and len(drop) - start >= min_samples and max_drop >= min_drop:
        decel_events.append({"start": start, "end": len(drop), "depth": max_drop})

    light = [e for e in decel_events if 15 <= e["depth"] <= 30]
    severe = [e for e in decel_events if e["depth"] > 30]
    prolonged = [e for e in decel_events if (e["end"] - e["start"]) > 60 * fs]

    return light, severe, prolonged


# ---------------------------------------------------------------------------
# Helper – short-term variability
# ---------------------------------------------------------------------------


def _compute_stv(fhr: np.ndarray, fs: int) -> Tuple[np.ndarray, float, float]:
    """Compute short-term variability (STV) of the FHR signal.

    STV is computed as the mean absolute difference between consecutive
    valid FHR samples within non-overlapping 1-minute windows.

    Parameters
    ----------
    fhr : np.ndarray
        1-D FHR signal (bpm).
    fs : int
        Sampling frequency.

    Returns
    -------
    stv_per_window : np.ndarray
        STV value for each 1-minute window.
    mean_stv : float
        Mean STV across all windows (MSTV).
    astv_pct : float
        Percentage of windows where STV < 1 bpm (ASTV).
    """
    window_size = 60 * fs  # 1 minute in samples
    n_windows = max(1, len(fhr) // window_size)

    stv_values: list[float] = []
    for w in range(n_windows):
        start = w * window_size
        end = start + window_size
        segment = fhr[start:end]
        valid = segment[(segment > 0) & np.isfinite(segment)]
        if len(valid) < 2:
            continue
        diffs = np.abs(np.diff(valid))
        stv_values.append(float(np.mean(diffs)))

    if len(stv_values) == 0:
        return np.array([]), 0.0, 0.0

    stv_arr = np.array(stv_values)
    mean_stv = float(np.mean(stv_arr))
    astv_pct = float(np.sum(stv_arr < 1.0) / len(stv_arr) * 100.0)

    return stv_arr, round(mean_stv, 2), round(astv_pct, 2)


# ---------------------------------------------------------------------------
# Helper – long-term variability
# ---------------------------------------------------------------------------


def _compute_ltv(fhr: np.ndarray, fs: int) -> Tuple[np.ndarray, float, float]:
    """Compute long-term variability (LTV) of the FHR signal.

    LTV is the amplitude (max − min) of valid FHR values within each
    non-overlapping 1-minute window.

    Parameters
    ----------
    fhr : np.ndarray
        1-D FHR signal (bpm).
    fs : int
        Sampling frequency.

    Returns
    -------
    ltv_per_window : np.ndarray
        LTV value for each 1-minute window.
    mean_ltv : float
        Mean LTV across all windows (MLTV).
    altv_pct : float
        Percentage of windows where LTV is outside the normal range
        (defined as 10–30 bpm), reported as ALTV.
    """
    window_size = 60 * fs
    n_windows = max(1, len(fhr) // window_size)

    ltv_values: list[float] = []
    for w in range(n_windows):
        start = w * window_size
        end = start + window_size
        segment = fhr[start:end]
        valid = segment[(segment > 0) & np.isfinite(segment)]
        if len(valid) < 2:
            continue
        amplitude = float(np.max(valid) - np.min(valid))
        ltv_values.append(amplitude)

    if len(ltv_values) == 0:
        return np.array([]), 0.0, 0.0

    ltv_arr = np.array(ltv_values)
    mean_ltv = float(np.mean(ltv_arr))
    # Abnormal = outside normal 10–30 bpm range
    abnormal = np.sum((ltv_arr < 10) | (ltv_arr > 30))
    altv_pct = float(abnormal / len(ltv_arr) * 100.0)

    return ltv_arr, round(mean_ltv, 2), round(altv_pct, 2)


# ---------------------------------------------------------------------------
# Helper – histogram features
# ---------------------------------------------------------------------------


def _compute_histogram_features(fhr: np.ndarray) -> dict[str, float]:
    """Compute histogram-based features from valid FHR values.

    FHR values are binned into 1-bpm-wide bins covering the full integer
    range of observed values.

    Parameters
    ----------
    fhr : np.ndarray
        1-D FHR signal (bpm).

    Returns
    -------
    dict
        Keys: Width, Min, Max, Nmax, Nzeros, Mode, Mean, Median,
        Variance, Tendency.
    """
    valid = fhr[(fhr > 0) & np.isfinite(fhr)]
    if len(valid) == 0:
        return {
            "Width": 0, "Min": 0, "Max": 0, "Nmax": 0, "Nzeros": 0,
            "Mode": 0, "Mean": 0, "Median": 0, "Variance": 0, "Tendency": 0,
        }

    fhr_int = np.round(valid).astype(int)
    fhr_min = int(np.min(fhr_int))
    fhr_max = int(np.max(fhr_int))
    width = fhr_max - fhr_min

    bins = np.arange(fhr_min, fhr_max + 2)  # +2 to include max bin edge
    hist, bin_edges = np.histogram(fhr_int, bins=bins)

    # Nmax: number of peaks in the histogram (local maxima)
    if len(hist) >= 3:
        peaks_idx, _ = find_peaks(hist.astype(float), height=0)
        nmax = len(peaks_idx) if len(peaks_idx) > 0 else 1
    else:
        nmax = 1 if len(hist) > 0 else 0

    nzeros = int(np.sum(hist == 0))

    # Mode: the bin centre with the highest count
    bin_centres = (bin_edges[:-1] + bin_edges[1:]) / 2.0
    mode_val = float(bin_centres[np.argmax(hist)]) if len(hist) > 0 else 0.0

    mean_val = float(np.mean(valid))
    median_val = float(np.median(valid))
    variance_val = float(np.var(valid))

    # Tendency: skewness indicator
    #   1  = positively skewed (mean > median)
    #   0  = symmetric
    #  -1  = negatively skewed (mean < median)
    diff = mean_val - median_val
    if abs(diff) < 1.0:
        tendency = 0
    elif diff > 0:
        tendency = 1
    else:
        tendency = -1

    return {
        "Width": int(width),
        "Min": int(fhr_min),
        "Max": int(fhr_max),
        "Nmax": int(nmax),
        "Nzeros": int(nzeros),
        "Mode": int(round(mode_val)),
        "Mean": int(round(mean_val)),
        "Median": int(round(median_val)),
        "Variance": int(round(variance_val)),
        "Tendency": int(tendency),
    }


# ---------------------------------------------------------------------------
# Helper – fetal movement proxy
# ---------------------------------------------------------------------------


def _detect_fetal_movements(fhr: np.ndarray, fs: int) -> int:
    """Estimate fetal movements as rapid short-duration FHR changes.

    A fetal movement proxy is counted when the FHR changes by ≥10 bpm
    within a 2-second window, following the convention used in CTG analysis.

    Parameters
    ----------
    fhr : np.ndarray
        1-D FHR signal.
    fs : int
        Sampling frequency.

    Returns
    -------
    int
        Estimated number of fetal movement events.
    """
    valid = fhr.copy()
    valid[(valid <= 0) | ~np.isfinite(valid)] = np.nan

    # Use a 2-second sliding window step
    step = 2 * fs
    if step < 2 or len(valid) < step:
        return 0

    count = 0
    prev_median = np.nanmedian(valid[:step]) if not np.all(np.isnan(valid[:step])) else np.nan

    idx = step
    while idx + step <= len(valid):
        window = valid[idx: idx + step]
        if np.all(np.isnan(window)):
            idx += step
            continue
        cur_median = np.nanmedian(window)
        if not np.isnan(prev_median) and not np.isnan(cur_median):
            if abs(cur_median - prev_median) >= 10:
                count += 1
        prev_median = cur_median
        idx += step

    return count


# ---------------------------------------------------------------------------
# Helper – uterine contraction detection
# ---------------------------------------------------------------------------


def _detect_contraction(uc: np.ndarray, fs: int) -> int:
    """Detect uterine contractions as peaks in the UC (tocometer) signal.

    Parameters
    ----------
    uc : np.ndarray
        1-D uterine contraction signal.
    fs : int
        Sampling frequency.

    Returns
    -------
    int
        Number of detected contraction peaks.
    """
    valid = uc[np.isfinite(uc)]
    if len(valid) == 0:
        return 0

    # Minimum distance between contractions: ~2 minutes
    min_distance = 2 * 60 * fs
    # Prominence threshold: at least 10 units above surroundings
    prominence_thresh = max(10, float(np.std(valid)) * 0.5)

    peaks, properties = find_peaks(
        uc,
        distance=max(min_distance, 1),
        prominence=prominence_thresh,
        height=float(np.median(valid)) + 5,
    )

    return len(peaks)


# ---------------------------------------------------------------------------
# Main feature extraction from signals
# ---------------------------------------------------------------------------


def extract_features_from_signal(
    fhr_signal: np.ndarray,
    uc_signal: np.ndarray,
    fs: int = 4,
) -> pd.Series:
    """Extract 21 UCI-CTG-compatible features from raw FHR and UC signals.

    Parameters
    ----------
    fhr_signal : np.ndarray
        1-D fetal heart-rate signal in bpm.  Invalid values should be 0.
    uc_signal : np.ndarray
        1-D uterine contraction signal in arbitrary units.
    fs : int, optional
        Sampling frequency in Hz (default 4).

    Returns
    -------
    pd.Series
        Series indexed by the 21 UCI CTG feature names.

    Raises
    ------
    ValueError
        If fewer than 50 % of FHR samples are valid (non-zero, finite).
    """
    fhr = np.asarray(fhr_signal, dtype=float).ravel()
    uc = np.asarray(uc_signal, dtype=float).ravel()

    # Quality check: >50 % valid
    valid_mask = (fhr > 0) & np.isfinite(fhr)
    valid_pct = valid_mask.sum() / len(fhr) if len(fhr) > 0 else 0.0
    if valid_pct < 0.50:
        raise ValueError(
            f"Record quality too low: only {valid_pct:.1%} of FHR values are valid."
        )

    duration_min = len(fhr) / fs / 60.0  # recording duration in minutes
    if duration_min <= 0:
        raise ValueError("Recording duration is zero.")

    # --- Baseline ---
    baseline = _detect_baseline(fhr, fs)

    # --- Accelerations ---
    accels = _detect_accelerations(fhr, baseline, fs)
    ac_count = len(accels)

    # --- Decelerations ---
    light_decel, severe_decel, prolonged_decel = _detect_decelerations(
        fhr, baseline, fs
    )
    dl_count = len(light_decel)
    ds_count = len(severe_decel)
    dp_count = len(prolonged_decel)

    # --- Fetal movements (proxy) ---
    fm_count = _detect_fetal_movements(fhr, fs)

    # --- Uterine contractions ---
    uc_count = _detect_contraction(uc, fs)

    # --- Short-term variability ---
    _, mstv, astv = _compute_stv(fhr, fs)

    # --- Long-term variability ---
    _, mltv, altv = _compute_ltv(fhr, fs)

    # --- Histogram features ---
    hist_feats = _compute_histogram_features(fhr)

    # UCI CTG event features are counts per second, not counts per minute.
    duration_sec = duration_min * 60.0
    features = {
        "LB": baseline,
        "AC": round(ac_count / duration_sec, 6) if duration_sec > 0 else 0.0,
        "FM": round(fm_count / duration_sec, 6) if duration_sec > 0 else 0.0,
        "UC": round(uc_count / duration_sec, 6) if duration_sec > 0 else 0.0,
        "DL": round(dl_count / duration_sec, 6) if duration_sec > 0 else 0.0,
        "DS": round(ds_count / duration_sec, 6) if duration_sec > 0 else 0.0,
        "DP": round(dp_count / duration_sec, 6) if duration_sec > 0 else 0.0,
        "ASTV": astv,
        "MSTV": mstv,
        "ALTV": altv,
        "MLTV": mltv,
    }
    features.update(hist_feats)

    return pd.Series(features, name=None)[UCI_FEATURE_NAMES]


# ---------------------------------------------------------------------------
# Batch extraction
# ---------------------------------------------------------------------------


def extract_features_batch(
    records_dir: str | os.PathLike,
    output_path: Optional[str | os.PathLike] = None,
) -> pd.DataFrame:
    """Load all WFDB records from *records_dir* and extract CTG features.

    Parameters
    ----------
    records_dir : path-like
        Directory containing WFDB ``.dat`` / ``.hea`` file pairs
        (e.g. the CTU-UHB CTG database subset).
    output_path : path-like, optional
        If provided, the resulting DataFrame is saved as a Parquet file.

    Returns
    -------
    pd.DataFrame
        One row per recording, columns are the 21 UCI CTG feature names
        plus a ``record_name`` index column.
    """
    records_dir = Path(records_dir)
    hea_files = sorted(records_dir.glob("*.hea"))

    if len(hea_files) == 0:
        warnings.warn(f"No .hea files found in {records_dir}")
        return pd.DataFrame(columns=["record_name"] + UCI_FEATURE_NAMES)

    rows: list[dict] = []
    skipped: list[str] = []

    for hea_path in hea_files:
        record_name = hea_path.stem
        try:
            record = wfdb.rdrecord(str(records_dir / record_name))
        except Exception as exc:  # noqa: BLE001
            warnings.warn(f"Failed to read record {record_name}: {exc}")
            skipped.append(record_name)
            continue

        # Identify FHR and UC channels
        sig_names = [s.upper() for s in record.sig_name]
        try:
            fhr_idx = sig_names.index("FHR")
            uc_idx = sig_names.index("UC")
        except ValueError:
            warnings.warn(
                f"Record {record_name} missing FHR/UC channels "
                f"(found {record.sig_name}). Skipping."
            )
            skipped.append(record_name)
            continue

        fhr_signal = record.p_signal[:, fhr_idx]
        uc_signal = record.p_signal[:, uc_idx]
        fs = record.fs or 4

        try:
            features = extract_features_from_signal(fhr_signal, uc_signal, fs)
        except ValueError as exc:
            warnings.warn(f"Record {record_name} skipped: {exc}")
            skipped.append(record_name)
            continue

        row = features.to_dict()
        row["record_name"] = record_name
        rows.append(row)

    if len(rows) == 0:
        warnings.warn("No valid records processed.")
        return pd.DataFrame(columns=["record_name"] + UCI_FEATURE_NAMES)

    df = pd.DataFrame(rows, columns=["record_name"] + UCI_FEATURE_NAMES)

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_path, index=False)
        print(f"Saved {len(df)} records to {output_path}")

    if skipped:
        print(f"Skipped {len(skipped)} record(s): {', '.join(skipped)}")

    return df


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    _records_dir = Path(__file__).resolve().parents[2] / "data" / "ctu-uhb-ctgdb"
    _output_dir = Path(__file__).resolve().parents[2] / "artifacts"

    print(f"Reading WFDB records from: {_records_dir}")
    print("-" * 60)

    result_df = extract_features_batch(
        records_dir=_records_dir,
        output_path=_output_dir / "ctu_uhb_features.parquet",
    )

    print("-" * 60)
    print(f"Extracted features for {len(result_df)} recording(s).\n")
    if len(result_df) > 0:
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", 200)
        print(result_df.to_string(index=False))
