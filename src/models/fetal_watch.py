"""Supported training entrypoint; preprocessing and group CV are in scripts.run_models."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

def train_fetal_watch(data_dir=None, n_trials=20):
    from scripts.run_models import train_model
    _, manifest = train_model("fetalwatch", Path(data_dir) if data_dir else ROOT / "data")
    return manifest

if __name__ == "__main__":
    train_fetal_watch()
