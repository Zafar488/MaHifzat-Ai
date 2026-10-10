# Project ke fresh test results

Test report UTC: 2026-10-10T11:02:52.976765+00:00

Project local machine par test kiya gaya. Backend ke 74 tests pass hue; 0 failures, 0 errors, 0 skipped. Is ke ilawa 7 actual assessment workflows pass hue, har case mein tamam 9 agents audit huay. Chaar invalid payloads reject huay.

## Tamam local datasets

| File | Rows | Columns |
|---|---:|---:|
| carereach_prepared.parquet | 110,527 | 20 |
| gestation_prepared.parquet | 768 | 17 |
| oncotrace_prepared.parquet | 569 | 39 |
| uci_ctg.parquet | 2,126 | 23 |
| uci_maternal.parquet | 1,014 | 7 |

Total prepared rows: **115,004**. Is ke ilawa **15 raw CTG recordings** aur un ki `.hea` headers shamil hain. Original files preserve hain. API keys aur account/patient databases archive mein shamil nahi.

## Paanch models

| Model | Asal target | Internal macro F1 |
|---|---|---:|
| maternalguard | RiskLevel | 0.6871 |
| fetalwatch | NSP | 0.9247 |
| pretermguard | CLASS | 0.8504 |
| gestationinsight | target | 0.7423 |
| carereach | target | 0.5627 |

Yeh saved internal splits ke scores hain. Fresh audit mein in ko dobara reproduce kiya; external medical validation abhi established nahi. MaternalGuard ke mid-risk recall ka score 0.42 hai, is liye har prediction ko sahi kehna durust nahi. Duplicate feature groups train aur test ke darmiyan share nahi hote. CTG test examples correctly classified holdout rows se sirf functional branch testing ke liye select huay; woh naya unbiased accuracy test nahi.

Purana preserved CareReach artifact current environment mein load fail hota hai. App ka current complete CareReach pipeline load aur prediction dono karta hai. PretermGuard ab 10 CTG pattern classes predict karta hai; premature delivery ka observed target is data mein nahi. CareReach aur GestationInsight proxy research models hain.

## Workflow ke actual results

| Case | Rule urgency | Emergency | Follow-up | Agents |
|---|---|---|---|---:|
| Routine ANC | LOW_RISK | False | reminder | 9 |
| Maternal emergency | HIGH_RISK_EMERGENCY | True | emergency_assessment | 9 |
| Fetal concern | LOW_RISK | True | emergency_assessment | 9 |
| Missed checkups | LOW_RISK | False | home_visit | 9 |
| Incomplete vitals + danger sign | HIGH_RISK_EMERGENCY | True | emergency_assessment | 9 |
| Urgent BP | URGENT | False | call | 9 |
| Fetal suspect | LOW_RISK | False | call | 9 |

Rule urgency aur model risk category alag outputs hain. Misal ke taur par Routine ANC test mein rule LOW_RISK aur maternal model mid risk raha. Missing measurements ko normal assume nahi kiya gaya; convulsions wale incomplete case mein emergency action bana.

## Running app aur real providers

- Signup/login, paanch model predictions, nine-agent assessment aur case persistence ka live API flow successful raha.
- Groq ne de-identified synthetic inputs par response generate kiya.
- OpenStreetMap se 8 actual hospital candidates mile. Overpass fail hone par bounded-map fallback use hua; coverage sirf 2 km thi.
- FastAPI health/readiness aur Streamlit health ne HTTP 200 diya. App demo mode band tha.
- Unit/integration suite ne consent, routing units/timeouts, patient access boundaries aur messaging composer behavior check kiya.

Hospital ki services, beds aur acceptance map data se verify nahi hoti. Actual device GPS capture is run mein test nahi hua; public Peshawar coordinates use huay. SMS/WhatsApp/call delivery send nahi ki gayi; current buttons composer/dialer kholte hain. Load, deployment aur independent security audit is report ka hissa nahi.

## Data ke findings

- Maternal file: 598 duplicate feature rows aur 35 conflicting-label groups. CTG: 15 duplicate feature rows aur 2 conflicting-label groups.
- CareReach prepared data mein 3,547 missing cells; Gestation prepared data mein 11. Data ko is export mein silently replace/impute nahi kiya.
- Dataset registry mein maternal local row count 1,014 correct kiya. Is turn mein retraining ya application behavior change nahi kiya.

## Data aur test inputs ka istemal

ZIP extract karein aur `TEST_GUIDE_ROMAN_URDU.md` kholein. Us mein dashboard ke liye measurements, units, follow-up history, complete CTG JSON aur expected actions diye hain. `models/` mein har model ke features, API request aur actual expected prediction hai.

Detailed evidence: `latest-test-results.xml`, `model_audit.json`, `real_app_verification.json`, `latest_project_test_report.json` aur pack ka `workflow_checks.json`. `PACKAGE_MANIFEST.json` har included file ka SHA-256 aur size deta hai. Archive ke CRC aur tamam manifest hashes verify huay.
