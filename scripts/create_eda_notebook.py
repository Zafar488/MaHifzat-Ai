"""Generate EDA notebook using nbformat."""
import nbformat as nbf

nb = nbf.v4.new_notebook()
nb.metadata = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3"
    }
}

cells = []

# ── Title cell ──
cells.append(nbf.v4.new_markdown_cell("""# Exploratory Data Analysis (EDA) - All 3 Datasets
This notebook performs EDA on:
- **Dataset A**: UCI Cardiotocography (CTG) — 2,126 records, 21 features, NSP 3-class
- **Dataset B**: UCI Maternal Health Risk — 1,014 records, 6 features, RiskLevel 3-class
- **Dataset C**: PhysioNet CTU-UHB CTG — subset of recordings with FHR/UC signals
"""))

# ── Imports ──
cells.append(nbf.v4.new_code_cell("""import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette('Set2')

DATA_DIR = 'g:/hackthon/data'
NOTEBOOK_DIR = 'g:/hackthon/notebooks'
os.makedirs(NOTEBOOK_DIR, exist_ok=True)
print("Setup complete.")
"""))

# ── Dataset A ──
cells.append(nbf.v4.new_markdown_cell("## Dataset A: UCI Cardiotocography (CTG)\n21 CTG features + CLASS (10-class) + NSP (3-class target)"))

cells.append(nbf.v4.new_code_cell("""df_ctg = pd.read_parquet(os.path.join(DATA_DIR, 'uci_ctg.parquet'))
print(f"Shape: {df_ctg.shape}")
print(f"\\nColumns: {list(df_ctg.columns)}")
print(f"\\nDtypes:\\n{df_ctg.dtypes}")
print(f"\\nDescribe:\\n{df_ctg.describe().round(3)}")
"""))

cells.append(nbf.v4.new_code_cell("""# Missing values check
missing = df_ctg.isnull().sum()
print(f"Missing values per column:\\n{missing}")
print(f"\\nTotal missing: {missing.sum()}")
"""))

cells.append(nbf.v4.new_code_cell("""# NSP class distribution bar chart
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
plt.show()
print("Saved: ctg_nsp_distribution.png")
"""))

cells.append(nbf.v4.new_code_cell("""# Correlation heatmap
features_only = df_ctg.drop(columns=['CLASS', 'NSP'])
fig, ax = plt.subplots(figsize=(14, 10))
corr = features_only.corr()
sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm', center=0,
            square=True, linewidths=0.5, ax=ax, cbar_kws={'shrink': 0.8})
ax.set_title('Dataset A: Feature Correlation Heatmap', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(NOTEBOOK_DIR, 'ctg_correlation_heatmap.png'), dpi=150, bbox_inches='tight')
plt.show()
print("Saved: ctg_correlation_heatmap.png")
"""))

# ── Dataset B ──
cells.append(nbf.v4.new_markdown_cell("## Dataset B: UCI Maternal Health Risk\n6 features + RiskLevel (3-class target: low/mid/high risk)"))

cells.append(nbf.v4.new_code_cell("""df_mat = pd.read_parquet(os.path.join(DATA_DIR, 'uci_maternal.parquet'))
print(f"Shape: {df_mat.shape}")
print(f"\\nColumns: {list(df_mat.columns)}")
print(f"\\nDtypes:\\n{df_mat.dtypes}")
print(f"\\nDescribe:\\n{df_mat.describe().round(3)}")
"""))

cells.append(nbf.v4.new_code_cell("""# Missing values check
missing_b = df_mat.isnull().sum()
print(f"Missing values per column:\\n{missing_b}")
print(f"\\nTotal missing: {missing_b.sum()}")
"""))

cells.append(nbf.v4.new_code_cell("""# RiskLevel class distribution bar chart
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
plt.show()
print("Saved: maternal_risk_distribution.png")
"""))

cells.append(nbf.v4.new_code_cell("""# Pairplot of features by risk level
sns.pairplot(df_mat, hue='RiskLevel', hue_order=['low risk', 'mid risk', 'high risk'],
             palette={'low risk': '#2ecc71', 'mid risk': '#f39c12', 'high risk': '#e74c3c'},
             plot_kws={'alpha': 0.5, 's': 20}, diag_kws={'alpha': 0.7})
plt.suptitle('Dataset B: Feature Pairplot by Risk Level', y=1.02, fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(NOTEBOOK_DIR, 'maternal_pairplot.png'), dpi=150, bbox_inches='tight')
plt.show()
print("Saved: maternal_pairplot.png")
"""))

# ── Dataset C ──
cells.append(nbf.v4.new_markdown_cell("""## Dataset C: PhysioNet CTU-UHB CTG Database
Cardiotocography recordings with Fetal Heart Rate (FHR) and Uterine Contraction (UC) signals.
Note: Only a subset of recordings was downloaded for initial EDA due to large dataset size (552 total recordings).
"""))

cells.append(nbf.v4.new_code_cell("""import wfdb

CTU_DIR = os.path.join(DATA_DIR, 'ctu-uhb-ctgdb')

# List downloaded records
if os.path.exists(CTU_DIR):
    hea_files = [f.replace('.hea', '') for f in os.listdir(CTU_DIR) if f.endswith('.hea')]
    print(f"Number of recordings available: {len(hea_files)}")
    print(f"Record names: {sorted(hea_files)}")
else:
    print("CTU-UHB directory not found. Run download_physionet.py first.")
    hea_files = []
"""))

cells.append(nbf.v4.new_code_cell("""# Read and display metadata for all downloaded records
if hea_files:
    records_meta = []
    for rec_name in sorted(hea_files):
        try:
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
        except Exception as e:
            print(f"Error reading {rec_name}: {e}")
    
    df_meta = pd.DataFrame(records_meta)
    print(f"Recordings loaded: {len(df_meta)}")
    print(f"\\nMetadata summary:\\n{df_meta[['fs_hz', 'sig_len', 'duration_min']].describe().round(2)}")
    print(f"\\nAll records:\\n{df_meta.to_string(index=False)}")
else:
    print("No records available.")
"""))

cells.append(nbf.v4.new_code_cell("""# Plot FHR signal for first recording
if hea_files:
    sample_rec_name = sorted(hea_files)[0]
    rec = wfdb.rdrecord(os.path.join(CTU_DIR, sample_rec_name))
    
    fig, axes = plt.subplots(rec.n_sig, 1, figsize=(14, 3 * rec.n_sig), sharex=True)
    if rec.n_sig == 1:
        axes = [axes]
    
    time_sec = np.arange(rec.sig_len) / rec.fs
    
    for i, (ax, sig_name, unit) in enumerate(zip(axes, rec.sig_name, rec.units)):
        ax.plot(time_sec, rec.p_signal[:, i], linewidth=0.5, color='steelblue')
        ax.set_ylabel(f'{sig_name} ({unit})')
        ax.set_title(f'{sig_name}', fontweight='bold')
        ax.grid(True, alpha=0.3)
    
    axes[-1].set_xlabel('Time (seconds)')
    fig.suptitle(f'Dataset C: Record {sample_rec_name} - Signals over Time', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(NOTEBOOK_DIR, 'physionet_sample_signal.png'), dpi=150, bbox_inches='tight')
    plt.show()
    print(f"Saved: physionet_sample_signal.png")
else:
    print("No records to plot.")
"""))

cells.append(nbf.v4.new_markdown_cell("""## Summary
| Dataset | Records | Features | Target | Classes |
|---------|---------|----------|--------|---------|
| A: UCI CTG | 2,126 | 21 | NSP | 3 (Normal/Suspect/Pathologic) |
| B: UCI Maternal | 1,014 | 6 | RiskLevel | 3 (low/mid/high risk) |
| C: PhysioNet CTU-UHB | 552 (subset downloaded) | 2 signals | - | Raw waveform data |

### Key observations:
- **Dataset A**: Imbalanced classes (Normal dominates at ~78%). 21 CTG-derived features available.
- **Dataset B**: Relatively balanced classes. 6 clinical features (Age, BP, BS, Temp, HR).
- **Dataset C**: Raw FHR + UC signals at 4 Hz sampling. Suitable for signal processing and feature extraction.
"""))

nb.cells = cells

# Write notebook
nb_path = 'g:/hackthon/notebooks/01_eda_exploration.ipynb'
with open(nb_path, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
print(f"Notebook saved to {nb_path}")
