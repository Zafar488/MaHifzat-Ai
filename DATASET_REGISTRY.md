# DATASET_REGISTRY.md

## Dataset A — UCI Cardiotocography (CTG) Data Set

| Field | Value |
|---|---|
| **Source** | UCI Machine Learning Repository |
| **URL** | https://archive.ics.uci.edu/dataset/193/cardiotocography |
| **Records** | 2,126 fetal cardiotocograms |
| **Features** | 21 numeric FHR/UC diagnostic features (baseline heart rate, accelerations, fetal movements, uterine contractions, short/long-term variability, histogram features) |
| **Target** | `fetal_health` / `NSP` — 3-class (Normal / Suspect / Pathological); also 10-class morphologic pattern |
| **License** | CC BY 4.0 |
| **Origin** | Portugal (SisPorto system) |

### Class Distribution

| Class | Count |
|---|---|
| Normal | ~1,655 |
| Suspect | ~295 |
| Pathological | ~176 |

### Download

```python
from ucimlrepo import fetch_ucirepo
ctg = fetch_ucirepo(id=193)
```

---

## Dataset B — UCI Maternal Health Risk Data Set

| Field | Value |
|---|---|
| **Source** | UCI Machine Learning Repository |
| **URL** | https://archive.ics.uci.edu/dataset/863/maternal+health+risk |
| **Records** | 1,013 |
| **Features** | 6 — Age, Systolic BP, Diastolic BP, Blood Sugar, Body Temperature, Heart Rate |
| **Target** | `RiskLevel` — 3-class (low / mid / high risk) |
| **License** | CC BY 4.0 |
| **Origin** | Rural Bangladesh (IoT-based system) |

### Download

```python
from ucimlrepo import fetch_ucirepo
maternal = fetch_ucirepo(id=863)
```

---

## Dataset C — PhysioNet CTU-UHB Intrapartum Cardiotocography Database

| Field | Value |
|---|---|
| **Source** | PhysioNet (CTU Prague + University Hospital Brno) |
| **URL** | https://physionet.org/content/ctu-uhb-ctgdb/1.0.0/ |
| **Records** | 552 CTG recordings (selected from 9,164) |
| **Features** | Raw FHR + UC signals at 4 Hz, up to 90 min per recording |
| **Target/Outcome** | Umbilical arterial blood pH (objective ground truth) |
| **License** | Free for non-commercial use (cite source publication) |
| **Origin** | Czech Republic, 2010–2012 |

### Download

```python
import wfdb
wfdb.dl_database('ctu-uhb-ctgdb', 'data/ctu-uhb-ctgdb')
```

---

## Dataset D — Comprehensive Maternal Health Risk from IoT-enabled MCPS (Verification Result)

| Field | Value |
|---|---|
| **Source** | BMC Medical Informatics and Decision Making (2026), Hossain et al. |
| **Data Repository** | **Mendeley Data** — https://data.mendeley.com/datasets/ckhgtgdg4f/1 |
| **NOT on PhysioNet** | Contrary to initial lead |
| **Records** | ~6,058 |
| **Features** | 8 — Age, Body Temperature, Heart Rate, Systolic BP, Diastolic BP, BMI, HbA1c, + risk label |
| **Target** | Risk level classification |
| **Origin** | Bangladesh (expanded successor of UCI Maternal Health Risk dataset, same research group) |
| **Status** | Published, available on Mendeley Data; CC BY license likely |

> **Note:** Treat as optional enrichment for the MaternalGuard model.

---

## Why Not Merge

These four datasets are **not merged into a single table** because:

1. **Different pipeline stages** — Datasets A & C feed the **FetalWatch** model (fetal health from CTG signals), while Datasets B & D feed the **MaternalGuard** model (maternal risk from vital signs). They occupy separate branches of the pipeline.
2. **Different populations** — Data originates from Portugal, Czech Republic, and Bangladesh. Merging would confound population-level biases and make evaluation unreliable.
3. **Incompatible schemas** — CTG signal features (A/C) share no columns with maternal vital signs (B/D). Even B and D differ in feature count (6 vs 8) and sample size. A unified schema would require heavy imputation and alignment with no clear benefit.

Each dataset is loaded independently by its own loader in `src/data/loaders/`.

---

## What Is Still Missing

- **No Pakistan / Khyber Pakhtunkhwa (KP)–specific data exists yet** in any public repository for either fetal or maternal health. This project currently relies on proxy populations (Portugal, Czech Republic, Bangladesh).
- Future work should seek local clinical partnerships to collect region-specific data, which would significantly improve model generalizability for the target deployment context.
