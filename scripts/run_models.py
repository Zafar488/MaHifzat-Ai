"""Run all model training pipelines and collect metrics.

Callable as a CLI script *or* importable as ``run_all_models()`` from the
Streamlit app.  Data / artifact paths are resolved relative to the project
root so no hard-coded absolute paths are needed.
"""

import sys
import os
import json
import io
from pathlib import Path
from typing import Any, Dict, Optional

# ── Resolve project root (works for both CLI and import) ────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = str(BASE_DIR / "data")
ARTIFACTS_DIR = str(BASE_DIR / "artifacts")

# Ensure project root is on sys.path for imports
_root = str(BASE_DIR)
if _root not in sys.path:
    sys.path.insert(0, _root)

# Fix Windows console encoding for Unicode output
os.environ["PYTHONIOENCODING"] = "utf-8"
if hasattr(sys.stdout, "buffer") and sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer") and sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


# ═══════════════════════════════════════════════════════════════════════════════
# Callable training function — used by both CLI and Streamlit
# ═══════════════════════════════════════════════════════════════════════════════

def run_all_models(
    data_dir: Optional[str] = None,
    n_trials: int = 10,
    *,
    train_fetalwatch: bool = True,
    train_maternalguard: bool = True,
    train_carereach: bool = False,
    train_gestation: bool = False,
    verbose: bool = True,
) -> Dict[str, Any]:
    """Run training pipelines and return results dict.

    Parameters
    ----------
    data_dir : path to the ``data/`` directory (defaults to ``BASE_DIR / "data"``).
    n_trials : Optuna trials for FetalWatch / MaternalGuard (default 10).
    train_fetalwatch / train_maternalguard / train_carereach / train_gestation :
        Toggle individual training jobs on or off.
    verbose : print progress to stdout.

    Returns
    -------
    dict with keys ``fetalwatch``, ``maternalguard``, ``carereach``,
    ``gestation_insight``, ``artifacts_ok``.
    """

    import warnings
    import optuna

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    warnings.filterwarnings("ignore")

    data_dir = data_dir or DATA_DIR
    results: Dict[str, Any] = {}

    def _log(msg: str):
        if verbose:
            print(msg)

    # ── FetalWatch ────────────────────────────────────────────────────────
    if train_fetalwatch:
        from src.models.fetal_watch import train_fetal_watch

        _log("\n" + "=" * 60)
        _log("FETALWATCH MODEL TRAINING")
        _log("=" * 60)
        fw_results = train_fetal_watch(data_dir=data_dir, n_trials=n_trials)
        results["fetalwatch"] = fw_results

        best_fw = max(fw_results, key=lambda k: fw_results[k]["macro_f1"])
        _log(f"\nBest model     : {best_fw}")
        _log(f"Macro F1       : {fw_results[best_fw]['macro_f1']:.4f}")

    # ── MaternalGuard ─────────────────────────────────────────────────────
    if train_maternalguard:
        from src.models.maternal_guard import train_maternal_guard

        _log("\n" + "=" * 60)
        _log("MATERNALGUARD MODEL TRAINING")
        _log("=" * 60)
        mg_results = train_maternal_guard(data_dir=data_dir, n_trials=n_trials)
        results["maternalguard"] = mg_results

        _log(f"\nBest model     : {mg_results['best_model']}")
        _log(f"Macro F1       : {mg_results['best_macro_f1']:.4f}")

    # ── CareReach ─────────────────────────────────────────────────────────
    if train_carereach:
        _log("\n" + "=" * 60)
        _log("CAREREACH MODEL TRAINING")
        _log("=" * 60)
        # CareReach has its own standalone training script
        import subprocess
        proc = subprocess.run(
            [sys.executable, str(BASE_DIR / "train_care_reach.py")],
            capture_output=True, text=True, cwd=str(BASE_DIR),
        )
        results["carereach"] = {
            "stdout": proc.stdout[-2000:] if proc.stdout else "",
            "returncode": proc.returncode,
        }
        _log(proc.stdout[-500:] if proc.stdout else "(no output)")

    # ── GestationInsight ──────────────────────────────────────────────────
    if train_gestation:
        _log("\n" + "=" * 60)
        _log("GESTATIONINSIGHT MODEL TRAINING")
        _log("=" * 60)
        import subprocess
        proc = subprocess.run(
            [sys.executable, str(BASE_DIR / "train_gestation_insight.py")],
            capture_output=True, text=True, cwd=str(BASE_DIR),
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        results["gestation_insight"] = {
            "stdout": proc.stdout[-2000:] if proc.stdout else "",
            "returncode": proc.returncode,
        }
        _log(proc.stdout[-500:] if proc.stdout else "(no output)")

    # ── Verify artifacts ──────────────────────────────────────────────────
    artifact_paths = [
        BASE_DIR / "artifacts" / "fetalwatch" / "best_model.joblib",
        BASE_DIR / "artifacts" / "fetalwatch" / "results.json",
        BASE_DIR / "artifacts" / "maternalguard" / "best_model.joblib",
        BASE_DIR / "artifacts" / "maternalguard" / "results.json",
        BASE_DIR / "artifacts" / "carereach" / "best_model.joblib",
        BASE_DIR / "artifacts" / "carereach" / "metadata.json",
        BASE_DIR / "artifacts" / "gestationinsight" / "best_model.joblib",
        BASE_DIR / "artifacts" / "gestationinsight" / "metadata.json",
        BASE_DIR / "artifacts" / "pretermguard" / "best_model.joblib",
        BASE_DIR / "artifacts" / "pretermguard" / "results.json",
    ]
    artifact_status = {}
    for p in artifact_paths:
        artifact_status[str(p.relative_to(BASE_DIR))] = p.exists()
    results["artifacts"] = artifact_status
    results["artifacts_ok"] = all(
        v for k, v in artifact_status.items()
        if "fetalwatch" in k or "maternalguard" in k or "pretermguard" in k
    )

    _log("\n" + "=" * 60)
    _log("ARTIFACT VERIFICATION")
    _log("=" * 60)
    for path_str, exists in artifact_status.items():
        tag = "OK" if exists else "MISSING"
        _log(f"  [{tag}] {path_str}")

    _log("\n" + "=" * 60)
    _log("ALL DONE")
    _log("=" * 60)

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# CLI entry-point
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    run_all_models(n_trials=10)
"""Run both FetalWatch and MaternalGuard training pipelines and collect metrics."""

import sys
import os
import json
import io

# Fix Windows console encoding for Unicode output
os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, 'g:/hackthon')

import warnings
import optuna

# Suppress noisy logs
optuna.logging.set_verbosity(optuna.logging.WARNING)
warnings.filterwarnings("ignore")

# ═══════════════════════════════════════════════════════════════════════════
# Run FetalWatch
# ═══════════════════════════════════════════════════════════════════════════
from src.models.fetal_watch import train_fetal_watch

print("=" * 60)
print("FETALWATCH MODEL TRAINING")
print("=" * 60)
fw_results = train_fetal_watch(data_dir='g:/hackthon/data', n_trials=10)

# ═══════════════════════════════════════════════════════════════════════════
# Run MaternalGuard
# ═══════════════════════════════════════════════════════════════════════════
from src.models.maternal_guard import train_maternal_guard

print("\n" + "=" * 60)
print("MATERNALGUARD MODEL TRAINING")
print("=" * 60)
mg_results = train_maternal_guard(data_dir='g:/hackthon/data', n_trials=10)

# ═══════════════════════════════════════════════════════════════════════════
# Print comprehensive results
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("FINAL METRICS SUMMARY")
print("=" * 60)

# ── FetalWatch Summary ──────────────────────────────────────────────────────
print("\n--- FETALWATCH ---")
best_fw = max(fw_results, key=lambda k: fw_results[k]['macro_f1'])
print(f"Training completed : YES")
print(f"Best model         : {best_fw}")
print(f"Macro F1-score     : {fw_results[best_fw]['macro_f1']:.4f}")
auroc_fw = fw_results[best_fw].get('auroc_ovr_macro')
print(f"AUROC (OVR macro)  : {auroc_fw:.4f}" if auroc_fw else "AUROC (OVR macro)  : N/A")

print("\nPer-class metrics (all models):")
for model_name, metrics in fw_results.items():
    print(f"\n  [{model_name}]")
    print(f"    Macro-F1: {metrics['macro_f1']:.4f}")
    auroc = metrics.get('auroc_ovr_macro')
    print(f"    AUROC   : {auroc:.4f}" if auroc else "    AUROC   : N/A")
    for cls, cls_metrics in metrics.get('per_class', {}).items():
        print(f"    {cls:<15}  Precision={cls_metrics['precision']:.4f}  Recall={cls_metrics['recall']:.4f}  F1={cls_metrics['f1-score']:.4f}")

# ── MaternalGuard Summary ───────────────────────────────────────────────────
print("\n--- MATERNALGUARD ---")
best_mg = mg_results['best_model']
print(f"Training completed : YES")
print(f"Best model         : {best_mg}")
print(f"Macro F1-score     : {mg_results['best_macro_f1']:.4f}")

print("\nPer-class metrics (all models):")
for model_name, metrics in mg_results.get('models', {}).items():
    print(f"\n  [{model_name}]")
    print(f"    Macro-F1: {metrics['macro_f1']:.4f}")
    auroc = metrics.get('auroc_ovr')
    print(f"    AUROC   : {auroc:.4f}" if auroc else "    AUROC   : N/A")
    for cls, cls_metrics in metrics.get('per_class', {}).items():
        print(f"    {cls:<15}  Precision={cls_metrics['precision']:.4f}  Recall={cls_metrics['recall']:.4f}  F1={cls_metrics['f1-score']:.4f}  Support={cls_metrics.get('support', 'N/A')}")

# ── Verify Artifacts ────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("ARTIFACT VERIFICATION")
print("=" * 60)
artifacts = [
    'g:/hackthon/artifacts/fetalwatch/best_model.joblib',
    'g:/hackthon/artifacts/fetalwatch/results.json',
    'g:/hackthon/artifacts/maternalguard/best_model.joblib',
    'g:/hackthon/artifacts/maternalguard/results.json',
]
for path in artifacts:
    exists = os.path.exists(path)
    status = "OK" if exists else "MISSING"
    print(f"  [{status}] {path}")

print("\n" + "=" * 60)
print("ALL DONE")
print("=" * 60)
