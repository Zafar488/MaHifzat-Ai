# 🤱 MaaHifazat AI — Maternal & Fetal Health Platform

> **AI-powered maternal health monitoring for rural Pakistan** — combining multi-agent orchestration, ML risk prediction, smart referrals, and a real-time clinical dashboard to reduce preventable maternal and neonatal mortality.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [ML Models](#-ml-models)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [API Reference](#-api-reference)
- [Running Tests](#-running-tests)
- [Screenshots](#-screenshots)

---

## 🌍 Overview

MaaHifazat AI ("Mother's Protection" in Urdu) is a full-stack clinical decision support platform built for frontline healthcare workers in low-resource settings. The system:

- **Predicts** fetal distress, maternal risk, and preterm birth using trained ML models
- **Orchestrates** a multi-agent LangGraph pipeline to automate patient intake, risk classification, referrals, and clinician review
- **Communicates** alerts via multi-channel messaging (SMS, voice, in-app)
- **Visualises** all data through a modern React + TypeScript dashboard

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🧠 **Multi-Agent Orchestration** | LangGraph-powered pipeline with 9 specialised nodes (intake, risk, referral, communication, review, reporting…) |
| 📊 **Risk Prediction** | 4 ML models covering fetal monitoring, maternal risk, preterm birth, and care outreach |
| 🚑 **Smart Referrals** | Automated facility matching via OpenStreetMap / Overpass API with routing |
| 🔔 **Real-time Alerts** | Priority-based alerting with multi-channel delivery |
| 📈 **Clinical Dashboard** | React 19 + Recharts dashboard with patient lists, analytics, and audit trail |
| 🔐 **JWT Authentication** | Secure role-based access for clinicians and administrators |
| 📋 **Audit Logging** | Full audit trail for all clinical actions |

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     Frontend (React + Vite)               │
│  Dashboard · Patients · Referrals · Alerts · Analytics    │
└─────────────────────────┬────────────────────────────────┘
                          │  REST API (FastAPI)
┌─────────────────────────▼────────────────────────────────┐
│                    Backend (FastAPI)                       │
│  /api/patients  /api/risks  /api/referrals  /api/agents   │
└────────┬──────────────────────────┬───────────────────────┘
         │                          │
┌────────▼────────┐       ┌─────────▼──────────────────────┐
│   ML Model      │       │   Agent Orchestrator (LangGraph)│
│   Registry      │       │                                 │
│ • FetalWatch    │       │  patient_intake → clinical_risk │
│ • MaternalGuard │       │  → fetal_monitoring → referral  │
│ • PretermGuard  │       │  → communication → review       │
│ • CareReach     │       │  → anc_followup → reporting     │
│ • GestationI.   │       └────────────────────────────────-┘
└─────────────────┘
         │
┌────────▼────────┐
│  SQLite / Data  │
│  (async SQLAlch)│
└─────────────────┘
```

---

## 🤖 ML Models

| Model | Task | Dataset | Key Metrics |
|---|---|---|---|
| **FetalWatch** | Fetal distress classification (NSP: Normal / Suspect / Pathological) | CTG-UHB + UCI CTG | XGBoost / LightGBM ensemble |
| **MaternalGuard** | Maternal risk level prediction (Low / Mid / High) | UCI Maternal Health | Gradient Boosted Trees |
| **PretermGuard** | Preterm birth risk prediction | PhysioNet CTG-UHB | Random Forest + SHAP |
| **CareReach** | Care outreach prioritisation | Synthetic + UCI | LightGBM |
| **GestationInsight** | Gestational outcome classification | Combined datasets | Optuna-tuned XGBoost |

All models are trained with **Optuna** hyperparameter search, **SHAP** explainability, and calibrated probability outputs. Trained artifacts are stored in `artifacts/`.

---

## 🛠 Tech Stack

### Backend
| Layer | Technology |
|---|---|
| API Framework | FastAPI 0.110+ |
| Agent Orchestration | LangGraph 0.2+ / LangChain Core |
| LLM Provider | Groq (`openai/gpt-oss-120b`) |
| Database | SQLite via SQLAlchemy (async) + aiosqlite |
| Auth | JWT (python-jose + passlib/bcrypt) |
| ML | scikit-learn, XGBoost, LightGBM, imbalanced-learn, Optuna, SHAP |

### Frontend
| Layer | Technology |
|---|---|
| Framework | React 19 + TypeScript |
| Build Tool | Vite 8 |
| Styling | Tailwind CSS v4 |
| Data Fetching | TanStack Query v5 + Axios |
| Charts | Recharts 3 |
| Forms | React Hook Form + Zod |
| Routing | React Router v7 |

---

## 📁 Project Structure

```
MaHifzat-agent/
├── backend/                  # FastAPI application
│   ├── agents/               # LangGraph agent orchestration
│   │   ├── orchestrator.py   # Main graph definition
│   │   └── nodes/            # 9 agent nodes (intake, risk, referral…)
│   ├── api/                  # REST API layer
│   │   ├── main.py           # FastAPI app factory + lifespan
│   │   ├── auth.py           # JWT authentication endpoints
│   │   └── routes/           # patients, risks, referrals, alerts, audit…
│   ├── db/                   # SQLAlchemy models & engine
│   ├── schemas/              # Pydantic request/response schemas
│   ├── services/             # Business logic & model inference
│   └── config.py             # Pydantic-settings configuration
│
├── frontend/                 # React + Vite dashboard
│   └── src/
│       ├── pages/            # Dashboard, Patients, Referrals, Alerts…
│       ├── components/       # Reusable UI + layout components
│       ├── hooks/            # Custom React hooks
│       ├── services/         # API client layer
│       └── types/            # TypeScript type definitions
│
├── src/                      # ML training codebase
│   ├── data/                 # Data loaders + preprocessing
│   ├── features/             # Feature engineering
│   ├── models/               # Model definitions (FetalWatch, MaternalGuard…)
│   └── evaluation/           # Metrics & calibration utilities
│
├── data/                     # Raw datasets (git-ignored for large files)
│   └── ctu-uhb-ctgdb/        # PhysioNet CTG waveforms
│
├── artifacts/                # Trained model .joblib files (git-ignored)
├── notebooks/                # EDA + pipeline demo notebooks
├── scripts/                  # Data download + training helper scripts
│
├── train_care_reach.py       # CareReach model training script
├── train_gestation_insight.py# GestationInsight training script
├── app.py                    # Standalone demo app (Gradio/Streamlit)
├── safety_rules.py           # Clinical safety guardrails
├── requirements.txt          # ML/data dependencies
├── requirements-backend.txt  # Backend API dependencies
└── run_app.bat               # One-click Windows startup script
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [Groq API key](https://console.groq.com)

### 1. Clone the repository

```bash
git clone https://github.com/Zafar488/MaHifzat-agent.git
cd MaHifzat-agent
```

### 2. Set up environment variables

```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 3. Install backend dependencies

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements-backend.txt
pip install -r requirements.txt
```

### 4. Start the backend

```bash
uvicorn backend.api.main:app --reload --port 8000
```

API docs available at: **http://localhost:8000/api/docs**

### 5. Install and start the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at: **http://localhost:5173**

### 6. (Optional) Train the ML models

```bash
python train_care_reach.py
python train_gestation_insight.py
```

Or use the one-click Windows script:

```batch
run_app.bat
```

---

## 🔑 Environment Variables

Copy `.env.example` to `.env` and fill in:

| Variable | Description | Required |
|---|---|---|
| `GROQ_API_KEY` | Groq LLM API key ([get one here](https://console.groq.com)) | ✅ Yes |

All other settings (database URL, JWT secret, model paths, etc.) are configured via `backend/config.py` and can be overridden through environment variables.

> ⚠️ **Never commit `.env` to git.** It is already listed in `.gitignore`.

---

## 📡 API Reference

Full interactive docs available at `/api/docs` (Swagger UI) and `/api/redoc` when the backend is running.

### Key Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Register a new clinician account |
| `POST` | `/api/auth/login` | Authenticate and receive JWT token |
| `GET` | `/api/patients` | List all patients |
| `POST` | `/api/patients` | Register a new patient |
| `GET` | `/api/patients/{id}` | Get patient profile |
| `POST` | `/api/risks/assess` | Run full ML risk assessment |
| `GET` | `/api/referrals` | List referrals |
| `POST` | `/api/agents/run` | Trigger the full agent pipeline |
| `GET` | `/api/alerts` | Fetch active clinical alerts |
| `GET` | `/api/analytics/dashboard` | Dashboard summary statistics |
| `GET` | `/api/audit` | Audit trail |
| `GET` | `/api/health` | Backend + model health check |

---

## 🧪 Running Tests

```bash
# Backend tests
pytest backend/tests/ -v

# With coverage
pytest backend/tests/ --cov=backend --cov-report=term-missing
```

---

## 📸 Screenshots

| Main Dashboard | Agent Pipeline | Risk Assessment |
|:---:|:---:|:---:|
| ![Dashboard](01_main_page.png) | ![Agents](02_agent_page.png) | ![Form](03_form_filled.png) |

| Results — Top | Results — Full |
|:---:|:---:|
| ![Results Top](04_results_top.png) | ![Results Full](05_results_full.png) |

---

## 👥 Team

Built at **[Hackathon 2026]** — MaaHifazat AI team.

---

## 📄 License

This project is licensed under the MIT License.
