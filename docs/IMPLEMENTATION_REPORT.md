# Project review and implementation evidence — 2026-10-10

## Real application update

The default app now uses `scripts/start_app.py`, has patient signup/sign-in and does not seed fictional cases/facilities. All five complete pipelines execute in the model workbench; clinical care uses the maternal/fetal tasks plus deterministic rules. Patient-owned self-assessment runs all nine nodes. Groq's actual configured model produced a structured explanation after explicit de-identified-data authorization. Browser GPS controls, real OSM hospital discovery and openrouteservice road routing are integrated. Live public-coordinate checks returned eight mapped hospitals and road estimates. Public Overpass errors trigger one bounded official map request with explicitly limited 2 km coverage. Capability tags/bed acceptance remain unverified until a local service confirms them.

WhatsApp/SMS composers and call dialer links are user initiated. App-open reminders and persisted follow-up tasks operate without a messaging API. Automatic delivery is not claimed and mobile charges may apply. The separate isolated demo launcher remains optional test tooling only. Operation: `REAL_APP_GUIDE.md`. Provider evidence: `live_provider_verification.json`.

## Scope and choices
Reviewed the application, API/auth/access control, workflow nodes, training scripts, schemas, loaders, data files, saved artifacts and available project presentation material. The initial working tree already contained extensive edits and a deleted React frontend. Existing patient databases and dataset files were preserved. Source inventory/hashes are in `project_inventory.json`; generated environments, caches, secrets and Git internals are excluded.

The four proposed workflows were appropriate to the project's purpose and are now implemented through Streamlit → scoped FastAPI → persistent SQLite. Deterministic safety rules precede ML. Capability-based referral needs verified data, rather than a nearest-hospital guess. ANC priority uses observable operational rules, rather than applying a general appointment dataset to pregnant patients.

## Main fixes
- Replaced the legacy direct-model UI with backend-backed case persistence and all nine audited nodes.
- Kept missing measurements unknown; corrected Celsius/legacy Fahrenheit handling and rejected malformed CTG event units/booleans/nonfinite values.
- Loaded complete preprocessing/model bundles, not bare estimators missing their original scaler.
- Combined fetal escalation with overall emergency status while retaining separate maternal triage.
- Implemented service filtering, stale-data handling, consent-based road routing, honest distance fallback and no fabricated ETA.
- Added clinician handover, case retrieval, review/referral and scoped ANC tasks with recorded outcomes.
- Prevented duplicate case/task effects and conflicting reuse of case observations.
- Enforced demo isolation, disabled unconfigured external messaging and honored the LLM feature flag.
- Replaced duplicate legacy danger rules with the canonical service and removed medication instructions.
- Repaired contract export after the pre-existing frontend deletion.
- Repaired old proxy-model training entry points and stopped silent synthetic download fallback.

## Data and models
Maternal dataset: 1,014 rows but only 416 identical-feature groups; 598 repeated feature rows and 35 groups with conflicting risk labels. CTG: 2,126 rows, 2,111 groups, 15 repeated feature rows and two conflicting-label groups. These limits matter for evaluation.

Retrained complete pipelines with training-only grouped CV comparing RandomForest, ExtraTrees and LightGBM. Both selected LightGBM. Identical feature groups do not cross into the holdout. Scores were independently reproduced from the saved artifact and saved indices:

| Model | Macro-F1 | Accuracy | Risk-label recall |
|---|---:|---:|---|
| MaternalGuard | 0.6871 | 0.7119 | high 0.8182; mid 0.4200 |
| FetalWatch | 0.9247 | 0.9624 | pathological 0.9688 (31/32); suspect 0.8286 |

Maternal performance did not materially improve from the previous grouped baseline (~0.6881). Further blind retraining on the same holdout would not establish correctness. Model probabilities are not calibrated guarantees. The holdout was reused in project development; a prospective district dataset remains necessary.

All five legacy estimators were smoke-tested. The old CareReach preprocessor failed on the current scikit-learn runtime. New complete research-only CareReach and GestationInsight pipelines resolve runtime compatibility while retaining explicit proxy-data limitations. Preterm-birth inference remains disabled because CTG status is not an observed preterm outcome. Its original CTG CLASS task is now rebuilt and executable for all ten pattern classes in the model workbench (macro-F1 0.8504). OncoTrace data is unrelated to these maternal workflows. Dataset origins without an acquisition manifest cannot be certified from row counts.

All 15 local PhysioNet records were decoded; feature extraction yielded finite values. Those exploratory raw-signal features are not clinically demonstrated to match UCI device-summary definitions and are not served as equivalent inputs.

## What verification establishes
Final verification: **64 backend tests passed, zero failures**. API readiness and Streamlit health returned HTTP 200. Detailed software evidence is in `software_verification.json`.

Backend tests cover validation, safety priority, model preprocessing, degraded models, auth/scoping, persistence, idempotency, referral capabilities/routing consent, data freshness, ANC actions and all nine nodes. `demo_verification.json` documents actual HTTP runs of five synthetic scenarios including review/referral and task completion. Browser testing demonstrates the UI connects to and saves backend results.

These are software and internal dataset checks. They do not prove clinical diagnostic accuracy, real hospital availability, actual messaging delivery or actual field GPS reliability.

## Remaining dependencies
Supply the target district and verified directory. Configure openrouteservice for consent-based real road ETA. Select a messaging provider to connect the existing drafts/task queue to real delivery. Preterm/ANC/gestational models require labelled relevant outcomes, not proxy labels. Production needs a persistent deployment, explicit secrets, HTTPS and local clinical validation.

Use the updated README, PRESENTATION.md and demo guide for judging. Existing PDF/PPTX and old exploratory notebooks may contain outdated claims or evaluation methods; they were preserved as source material and are not the current implementation evidence.
