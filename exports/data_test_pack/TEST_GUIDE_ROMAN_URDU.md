# MaaHifazat: tamam data aur test inputs

Yeh local testing ka pack hai. `data/` mein original prepared datasets aur 15 raw signal records hain. `artifacts/` mein current pipelines aur purane estimators alag folders mein preserve hain. Current app `artifacts/serving` aur `artifacts/research` pipelines use karti hai. Original app databases aur API credentials is training/test archive ka hissa nahi hain.

## Dashboard mein test karein

1. http://localhost:8501 par apna account banayein/sign in karein.
2. New assessment mein neeche ke observations aur follow-up inputs enter karein. Har row ek alag software-test case hai; real patient data nahi. Unknown measurements blank chhorein.
3. Fetal case ke liye `inputs/ctg_pathological.json` ya `inputs/ctg_suspect.json` ka poora JSON Optional measured CTG JSON field mein paste karein.
4. Run all nine agents and save case click karein. Expected rule urgency aur follow-up action neeche hain.
5. Model evidence mein model select karein aur `models/<name>_features.json` ka JSON paste karein. Run model prediction ka result `<name>_expected.json` se compare karein.

| Test | Age | Weeks | BP mmHg | HR bpm | Temp C | Glucose mmol/L | Symptoms | Expected action |
|---|---:|---:|---|---:|---:|---:|---|---|
| Routine ANC | 26 | 28.0 | 118/76 | 74 | 37.0 | 5.2 | None | reminder |
| Maternal emergency | 34 | 34.0 | 180/120 | 110 | 38.4 | 9.8 | Severe headache, Blurred vision | emergency_assessment |
| Fetal concern | 30 | 36.0 | 120/80 | 82 | 37.0 | 5.4 | None | emergency_assessment |
| Missed checkups | 28 | 32.0 | 118/76 | 74 | 37.0 | 5.2 | None | home_visit |
| Incomplete vitals + danger sign | 25 | 30.0 | blank/blank | blank | blank | blank | Convulsions | emergency_assessment |
| Urgent BP | 30 | 28.0 | 145/95 | 74 | 37.0 | 5.2 | None | call |
| Fetal suspect | 30 | 36.0 | 120/80 | 82 | 37.0 | 5.4 | None | call |

Routine ANC: completed contacts 12,20,26. Maternal emergency: 12,20,26,30. Fetal cases: 12,20,26,30,34. Missed checkups: completed 12,20; missed visits 2; transport barrier Yes; phone access No. Incomplete danger case: completed 12,20,26. Urgent BP: completed 12,20,26.

Routine test ka MaternalGuard output mid risk aa sakta hai: rule LOW_RISK aur model category alag cheezein hain. Synthetic scenario se medical accuracy prove nahi hoti. Full holdout scores `reports/model_audit.json` mein hain.

## Location aur live services

Public Peshawar test coordinates: latitude 34.01, longitude 71.53. Overview mein Manual location save karein, OpenStreetMap aur road-provider consents select karke Find nearby hospitals click karein. Actual GPS capture ke liye Use current location ya Start live location click karein aur browser permission dein; Stop tracking band karta hai. Yeh pack user ki real GPS location contain nahi karta.
Assessment par Groq consent enable karne se configured provider explanation banata hai. API keys `.env` mein rehti hain. Overpass fail ho to 2 km bounded-map fallback clearly limited coverage dikhata hai. Hospital services/bed acceptance ki tasdeeq map data se nahi hoti.

## API aur reproducible tests

Staff POST `/api/agents/run` use karein; patient POST `/api/care/assess`. Scenario JSON ke `payload.patient_id` mein apni registered profile ID rakhein. Har new case ke liye `case_id` omit karein ya unique ID dein. Test inputs default mein external processing consent nahi dete; live services sirf explicit UI consent par activate karein.

```powershell
.venv\Scripts\python.exe -m pytest backend/tests -q -p no:cacheprovider
.venv\Scripts\python.exe scripts/audit_models.py
.venv\Scripts\python.exe scripts/verify_real_app.py --live-providers
.venv\Scripts\python.exe scripts/export_test_pack.py
```

Live verification command ek labelled local software-verification account/profile/case create karta hai. De-identified synthetic observations aur public coordinates configured providers ko bhejta hai. Automatic SMS/WhatsApp/call delivery is command se test nahi hoti; buttons composer/dialer kholte hain.

## Model target ki had

MaternalGuard RiskLevel aur FetalWatch NSP par chalte hain. Repaired PretermGuard CLASS ke 10 CTG patterns predict karta hai; preterm birth outcomes nahi. CareReach general no-show proxy aur GestationInsight Pima-derived proxy hai. In teen research outputs ko obstetric urgency/diagnosis ke liye use nahi kiya jata. OncoTrace dataset preserved hai, maternity workflow mein use nahi hota.
