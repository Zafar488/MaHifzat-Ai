"""Run EDA on all 3 datasets and save plots as PNG."""
import os
import sys
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = str(ROOT / 'data')
NOTEBOOK_DIR = str(ROOT / 'notebooks')
os.makedirs(NOTEBOOK_DIR, exist_ok=True)

plt.style.use('seaborn-v0_8-whitegrid')

# ═══════════════════════════════════════════════════════════
# DATASET A: UCI Cardiotocography
# ═══════════════════════════════════════════════════════════
print("=" * 60)
print("DATASET A: UCI Cardiotocography")
print("=" * 60)
df_ctg = pd.read_parquet(os.path.join(DATA_DIR, 'uci_ctg.parquet'))
print(f"Shape: {df_ctg.shape}")
print(f"Columns: {list(df_ctg.columns)}")
print(f"\nDtypes:\n{df_ctg.dtypes}")
print(f"\nDescribe:\n{df_ctg.describe().round(3)}")

# Missing values
missing_a = df_ctg.isnull().sum()
print(f"\nMissing values:\n{missing_a}")
print(f"Total missing: {missing_a.sum()}")

# NSP class distribution bar chart
nsp_labels = {1: 'Normal', 2: 'Suspect', 3: 'Pathologic'}
nsp_counts = df_ctg['NSP'].value_counts().sort_index()
nsp_counts.index = nsp_counts.index.map(nsp_labels.get)

fig, ax = plt.subplots(figsize=(8, 5))
bars = nsp_counts.plot(kind='bar', ax=ax, color=['#2ecc71', '#f39c12', '#e74c3c'], edgecolor='black')
ax.set_title('Dataset A: NSP Class Distribution', fontsize=14, fontweight='bold')
ax.set_xlabel('Fetal State (NSP)')
ax.set_ylabel('Count')
for bar, count in zip(bars.patches, nsp_counts.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10,
            f'{count} ({count/len(df_ctg)*100:.1f}%)', ha='center', fontsize=10)
plt.tight_layout()
plt.savefig(os.path.join(NOTEBOOK_DIR, 'ctg_nsp_distribution.png'), dpi=150, bbox_inches='tight')
plt.close()
print("\nSaved: ctg_nsp_distribution.png")

# Correlation heatmap
features_only = df_ctg.drop(columns=['CLASS', 'NSP'])
fig, ax = plt.subplots(figsize=(14, 10))
corr = features_only.corr()
sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', center=0,
            square=True, linewidths=0.5, ax=ax, cbar_kws={'shrink': 0.8})
ax.set_title('Dataset A: Feature Correlation Heatmap', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(NOTEBOOK_DIR, 'ctg_correlation_heatmap.png'), dpi=150, bbox_inches='tight')
plt.close()
print("Saved: ctg_correlation_heatmap.png")

# ═══════════════════════════════════════════════════════════
# DATASET B: UCI Maternal Health Risk
# ═══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("DATASET B: UCI Maternal Health Risk")
print("=" * 60)
df_mat = pd.read_parquet(os.path.join(DATA_DIR, 'uci_maternal.parquet'))
print(f"Shape: {df_mat.shape}")
print(f"Columns: {list(df_mat.columns)}")
print(f"\nDtypes:\n{df_mat.dtypes}")
print(f"\nDescribe:\n{df_mat.describe().round(3)}")

# Missing values
missing_b = df_mat.isnull().sum()
print(f"\nMissing values:\n{missing_b}")
print(f"Total missing: {missing_b.sum()}")

# Risk distribution bar chart
risk_order = ['low risk', 'mid risk', 'high risk']
risk_counts = df_mat['RiskLevel'].value_counts().reindex(risk_order)

fig, ax = plt.subplots(figsize=(8, 5))
bars = risk_counts.plot(kind='bar', ax=ax, color=['#2ecc71', '#f39c12', '#e74c3c'], edgecolor='black')
ax.set_title('Dataset B: Risk Level Distribution', fontsize=14, fontweight='bold')
ax.set_xlabel('Risk Level')
ax.set_ylabel('Count')
for bar, count in zip(bars.patches, risk_counts.values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5,
            f'{count} ({count/len(df_mat)*100:.1f}%)', ha='center', fontsize=10)
plt.tight_layout()
plt.savefig(os.path.join(NOTEBOOK_DIR, 'maternal_risk_distribution.png'), dpi=150, bbox_inches='tight')
plt.close()
print("\nSaved: maternal_risk_distribution.png")

# Pairplot
g = sns.pairplot(df_mat, hue='RiskLevel',
                 hue_order=['low risk', 'mid risk', 'high risk'],
                 palette={'low risk': '#2ecc71', 'mid risk': '#f39c12', 'high risk': '#e74c3c'},
                 plot_kws={'alpha': 0.5, 's': 20}, diag_kws={'alpha': 0.7})
g.figure.suptitle('Dataset B: Feature Pairplot by Risk Level', y=1.02, fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(NOTEBOOK_DIR, 'maternal_pairplot.png'), dpi=150, bbox_inches='tight')
plt.close()
print("Saved: maternal_pairplot.png")

# ═══════════════════════════════════════════════════════════
# DATASET C: PhysioNet CTU-UHB
# ═══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("DATASET C: PhysioNet CTU-UHB CTG")
print("=" * 60)

try:
    import wfdb
    CTU_DIR = os.path.join(DATA_DIR, 'ctu-uhb-ctgdb')
    hea_files = sorted([f.replace('.hea', '') for f in os.listdir(CTU_DIR) if f.endswith('.hea')])
    print(f"Recordings available: {len(hea_files)}")
    print(f"Record names: {hea_files}")

    # Read all metadata
    records_meta = []
    for rec_name in hea_files:
        rec = wfdb.rdrecord(os.path.join(CTU_DIR, rec_name))
        records_meta.append({
            'record': rec_name,
            'n_signals': rec.n_sig,
            'fs_hz': rec.fs,
            'sig_len': rec.sig_len,
            'duration_min': round(rec.sig_len / rec.fs / 60, 1),
            'signals': ', '.join(rec.sig_name),
            'units': ', '.join(rec.units)
        })

    df_meta = pd.DataFrame(records_meta)
    print(f"\nMetadata summary:\n{df_meta[['fs_hz', 'sig_len', 'duration_min']].describe().round(2)}")
    print(f"\nAll records:\n{df_meta.to_string(index=False)}")

    # Plot FHR signal for first recording
    sample_rec_name = hea_files[0]
    rec = wfdb.rdrecord(os.path.join(CTU_DIR, sample_rec_name))

    fig, axes = plt.subplots(rec.n_sig, 1, figsize=(14, 3 * rec.n_sig), sharex=True)
    if rec.n_sig == 1:
        axes = [axes]

    time_sec = np.arange(rec.sig_len) / rec.fs
    colors = ['#2980b9', '#e74c3c', '#27ae60']

    for i, (ax, sig_name, unit) in enumerate(zip(axes, rec.sig_name, rec.units)):
        color = colors[i % len(colors)]
        ax.plot(time_sec, rec.p_signal[:, i], linewidth=0.5, color=color)
        ax.set_ylabel(f'{sig_name} ({unit})')
        ax.set_title(f'{sig_name}', fontweight='bold')
        ax.grid(True, alpha=0.3)

    axes[-1].set_xlabel('Time (seconds)')
    fig.suptitle(f'Dataset C: Record {sample_rec_name} - Signals over Time', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(NOTEBOOK_DIR, 'physionet_sample_signal.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print(f"\nSaved: physionet_sample_signal.png")

except Exception as e:
    print(f"PhysioNet EDA error: {e}")

# ═══════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("| Dataset | Records | Features | Target | Classes |")
print("|---------|---------|----------|--------|---------|")
print(f"| A: UCI CTG | {len(df_ctg)} | 21 | NSP | 3 (Normal/Suspect/Pathologic) |")
print(f"| B: UCI Maternal | {len(df_mat)} | 6 | RiskLevel | 3 (low/mid/high risk) |")
print(f"| C: PhysioNet CTU-UHB | 552 (15 downloaded) | 2 signals | - | Raw waveform |")
print(f"\nPlots saved in: {NOTEBOOK_DIR}")
for f in sorted(os.listdir(NOTEBOOK_DIR)):
    if f.endswith('.png'):
        print(f"  - {f}")
print("\n[OK] EDA complete!")
