"""Dataset-specific loader modules."""

from src.data.loaders.physionet_ctg import load_physionet_records
from src.data.loaders.uci_ctg import load_uci_ctg
from src.data.loaders.uci_maternal import load_uci_maternal

__all__ = [
    "load_uci_ctg",
    "load_uci_maternal",
    "load_physionet_records",
]
