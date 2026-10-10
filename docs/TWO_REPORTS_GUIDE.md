# Chaar sections aur do Urdu/English reports

App: http://localhost:8501

New assessment mein aik patient case ke chaar sections hain:

1. Patient and pregnancy details: patient ID, name/contact, weeks + days, expected delivery date, dating source, previous pregnancies/births, complications, medical history, preferred language, location aur consent.
2. Mother's assessment: aik martaba measured BP, glucose mmol/L, temperature Celsius, heart rate aur breathing rate. Measurement date/time Pakistan timezone mein, glucose test type, structured Yes/No/Unknown safety signs, notes aur available labs bhi record hote hain.
3. Baby's assessment: movements shuru hui hain ya nahi, usual pattern mein kami/tabdeeli, concern ka time aur clinician notes. CTG available = Yes par JSON, approved single-record CSV ya advanced measured 21-feature entry use karein. Template download button form ke upar hai. CTG photo/PDF se automatic numeric extraction connected nahi; project ke available five models tabular hain.
4. Appointments and follow-up: booking date, clinician appointment, last completed checkup, completed ANC contacts, missed visits, transport/phone barriers, actual previous reminder status aur notification channel.

Unknown ko No/normal nahi banaya jata. Extra free-text notes structured danger signs ka automatic replacement nahi. Reduced movements ka structured field safety engine se connected hai. Movements abhi kabhi mehsoos hi nahi hui hon, is ko established movement pattern ki kami assume nahi kiya jata.

## Assessment aur reports

Patient consent obtained to store this case select karein. Location sirf current/live GPS permission se ya manually confirmed coordinates se lein; discovery/routing ke consents alag hain. Phir Run Assessment · save case and generate two reports click karein.

- Report 1: Mother and baby care — observed measurements, safety flags, maternal/fetal results, missing information, history, care-seeking steps, avoiding delays aur follow-up.
- Report 2: Location and hospital referral — case ki recorded position, selected/alternative candidates, coordinates, meter/km distance, road ya straight-line type, available road ETA, required services, reported/verified/unknown service status aur confirmation requirements.

Har report mein English aur native Urdu script tabs hain. HTML aur text downloads mein dono zabanain shamil hain. HTML ko browser mein khol kar print bhi kar sakte hain. Reports case ke sath backend mein save hoti hain aur Saved cases se dobara milti hain. Purane cases mein recorded facts se bilingual display banta hai; missing historical fields invent nahi hote.

Groq consent select karne par prediction aur referral ke BAAD Groq dono reports ki English/Urdu explanation aur Roman Urdu family summary banata hai. Naam, phone, patient/case IDs, exact coordinates aur free-text notes Groq ko nahi bheje jate. Typed measurements/history context aur available model outputs authorized external processing mein jate hain. API unavailable/invalid output par recorded-fact reports milti hain; un ko falsely LLM-generated label nahi diya jata.

## Paanch models, nau workflow agents

MaternalGuard required measured inputs par; FetalWatch compatible measured CTG par chalta hai. Available research models ke checkbox se baqi teen components bhi isi case mein run ho sakte hain:

- PretermGuard: poore CTG inputs par 10 CTG pattern classes; observed premature birth predictor nahi.
- GestationInsight: optional complete laboratory/history inputs; derived features backend banata hai. Dataset-specific pedigree score guess na karein. Pima-derived proxy pregnancy complication ka validated outcome nahi.
- CareReach: booking/appointment dates aur explicitly known appointment research variables par. SMS_received ke liye actual SMS status chahiye; WhatsApp ya generic reminder ko SMS assume nahi kiya jata. Booking delay aur last-visit duration alag hain.

Missing research inputs par not assessed result milega. Yeh teen outputs urgency, follow-up action ya hospital selection ko override nahi karte. Naye clinical care aur delivery/treatment ka final decision qualified clinician ka rehta hai.

## Fresh verification

88 automated tests pass, zero failures/errors. Test coverage mein case resume/idempotency, patient access control, reduced-movement mapping, strict single-patient CTG CSV, wrong units/duplicate headers/missing values rejection, bilingual reports, Urdu script validation, report HTML escaping aur research boundaries shamil hain.

Running-app live check: nine agents, actual five model components, saved two bilingual reports, Groq generated explanations, five actual hospital candidates aur five road routes verified. Is run mein Overpass fail hua aur 2 km bounded-map fallback use hui. Yeh complete regional hospital coverage nahi. Services/bed availability/receiving acceptance ki phone par tasdeeq zaroori hai.

Sample reports synthetic software-test observations aur public Peshawar coordinates par bani hain; kisi real patient ka diagnosis nahi. Actual device GPS capture aur automatic SMS/WhatsApp/call delivery is verification mein exercise nahi hui.

Commands:

```powershell
.venv\Scripts\python.exe -m pytest backend/tests -q -p no:cacheprovider
.venv\Scripts\python.exe scripts/verify_bilingual_reports.py --live-providers
```

Live verification command clearly labelled local verification account/case banata hai aur consented synthetic inputs/public coordinates configured providers ko bhejta hai.
