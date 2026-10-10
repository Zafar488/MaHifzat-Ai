# Judge demo guide

Start `run_app.bat` or `.venv\Scripts\python.exe scripts/start_demo.py`. Keep the launcher running. UI: http://localhost:8501; API: http://127.0.0.1:8000/api/docs.

Login: `demo-clinician` / `MaaHifazat-Demo-2026!`. Synthetic data lives in `data/demo-app.db`; the original database is preserved. Admin and LHW demo accounts are also available.

1. Open New assessment. Enable 'Use a synthetic judge-demo scenario' and choose Maternal emergency. Run all nine agents. Show the red escalation, symptom flags, capable facility, labelled straight-line distance and doctor summary.
2. Choose Fetal concern. Load the held-out fetal example. Its selection is disclosed. Run and show CTG concern with a newborn-care candidate. Do not call the single selected case an accuracy test.
3. Choose Missed checkups. Run and show the home-visit recommendation, reason and persisted task. Open Follow-up tasks and record a synthetic completion note.
4. Choose Incomplete vitals + danger sign. Missing measurements remain missing; convulsions still trigger escalation. There is no fabricated ML prediction.
5. Open Saved cases. Download handover, record clinician review and create a manually confirmed synthetic referral. Demonstrate stored outcomes and the audit trail.
6. Open Model evidence. Show reproduced holdout scores and disabled-model reasons.

All demo patient observations and facilities are fictional except the labelled dataset feature example. No messages, real visits or hospital acceptance occur. Road ETA is unavailable in demo mode. Manual coordinates demonstrate location without obtaining the user's actual location. GPS requires the user's browser permission; if denied or unsupported, manual entry remains available.

Run `scripts/verify_demo.py` while the demo is running for API evidence of five scenarios, nine nodes per scenario, retry idempotency, persisted review/referral and task completion. It uses synthetic names and case IDs and records evidence in `docs/demo_verification.json`.

If login fails after a restart, sign out and sign in. If port 8000 or 8501 is occupied, stop the earlier demo launcher before starting another instance. This prototype requires supplied local data and artifacts; training is not needed to present it.
