from pathlib import Path
import pandas as pd
from ucimlrepo import fetch_ucirepo

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Dataset A: UCI Cardiotocography (id=193) ──
print("=" * 60)
print("DATASET A: UCI Cardiotocography (id=193)")
print("=" * 60)
ctg = fetch_ucirepo(id=193)
df_a = ctg.data.features.copy()
df_a['CLASS'] = ctg.data.targets['CLASS'].values
df_a['NSP'] = ctg.data.targets['NSP'].values
print(f"Shape: {df_a.shape}")
print(f"Columns ({len(df_a.columns)}): {list(df_a.columns)}")
print(f"\nDtypes:\n{df_a.dtypes}")
print(f"\nFirst 5 rows:\n{df_a.head()}")
print(f"\nNSP class distribution (1=Normal, 2=Suspect, 3=Pathologic):")
print(df_a['NSP'].value_counts().sort_index())
print(f"\nCLASS distribution (10 classes):")
print(df_a['CLASS'].value_counts().sort_index())
ctg_path = DATA_DIR / "uci_ctg.parquet"
df_a.to_parquet(ctg_path, index=False)
print(f"\nSaved to {ctg_path} ({len(df_a)} records)")

# ── Dataset B: UCI Maternal Health Risk (id=863) ──
print("\n" + "=" * 60)
print("DATASET B: UCI Maternal Health Risk (id=863)")
print("=" * 60)
maternal = fetch_ucirepo(id=863)
df_b = maternal.data.features.copy()
df_b['RiskLevel'] = maternal.data.targets['RiskLevel'].values
print(f"Shape: {df_b.shape}")
print(f"Columns ({len(df_b.columns)}): {list(df_b.columns)}")
print(f"\nDtypes:\n{df_b.dtypes}")
print(f"\nFirst 5 rows:\n{df_b.head()}")
print(f"\nRiskLevel class distribution:\n{df_b['RiskLevel'].value_counts().sort_index()}")
maternal_path = DATA_DIR / "uci_maternal.parquet"
df_b.to_parquet(maternal_path, index=False)
print(f"\nSaved to {maternal_path} ({len(df_b)} records)")

print("\n[OK] Both UCI datasets downloaded successfully!")
