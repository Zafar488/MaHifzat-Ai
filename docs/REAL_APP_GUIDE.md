# MaaHifazat — real app chalane ka tareeqa

Pehle `run_app.bat` chalayein. Browser mein http://localhost:8501 kholein aur **Create account** se apna patient account banayein. Password kam az kam 12 characters ka ho. Sign in ke baad **Overview** mein location aur nearby hospitals hain.

## Location aur hospitals

**Use current location** ek martaba GPS leta hai. **Start live location** browser ki ijazat ke baad location changes leta hai; **Stop tracking** usay band karta hai. Browser/phone permission aur localhost ya HTTPS zaroori hain. GPS na mile to **Manual location** mein coordinates record karein.

OpenStreetMap coordinate-sharing checkbox select karein. Road distance ke liye openrouteservice consent bhi select karein. **Find nearby hospitals** par asal map records, distance aur available road ETA aati hai. Chhota distance meters mein, bara kilometers mein dikhaya jata hai. Maps link user click par directions kholta hai.

Overpass unavailable ho to official OSM map fallback nearest 2 km tak limited hai. Screen par partial coverage saaf likhi hoti hai; isay poore 25/100 km ki search na samjhein. Radius ke tamam results ke liye Overpass provider ya apni verified facility directory chahiye. Map mein hospital hona maternity/emergency/NICU service ya available bed ki tasdeeq nahi. Unknown ko available nahi dikhaya jata. Restricted facilities bhi direct acceptance confirmation chahti hain.

## Assessment aur nine agents

**New assessment** mein apni patient profile register/select karein. Asal measured vitals, units aur symptoms dein; unknown measurements khali chhorein. CTG ke 21 measured device features hon to JSON dein. Bana kar CTG features enter na karein. Follow-up appointment, completed contacts aur transport barriers record karein.

Groq explanation chahiye to de-identified-data consent select karein. **Run all nine agents and save case** patient intake, data quality, maternal risk, fetal monitoring, ANC follow-up, smart referral, clinician handover, communication aur reporting ke nine nodes chalata hai. Har node ka audit saved hai. Groq fail ho to recorded assessment aur deterministic urgency phir bhi rehti hai.

**Saved cases** mein results aur clinician handover download karein. Clinician/admin assigned cases review aur referrals track kar sakte hain. Emergency advice software review ka intezar nahi karti.

## Paanch models

**Model evidence** mein tamam paanch complete pipelines ki prediction chala sakte hain. MaternalGuard aur FetalWatch actual maternal/CTG labels par assessment mein lage hain. PretermGuard ka repaired output 10 CTG pattern classes hai; data mein observed preterm birth nahi. CareReach general appointment labels par hai aur GestationInsight Pima-derived proxy labels par. In teen targets ko obstetric clinical accuracy kehna durust nahi. Real outcomes milne par in targets ke liye naye validated models train karna mumkin hai.

## Free communication options

**Follow-up tasks** mein reminder aur staff task queue saved rehti hai. App khuli ho to due reminders refresh hote hain. Phone number ho aur aap contact-app sharing select karein to WhatsApp prepared message, SMS composer aur call dialer khol sakte hain. App khud sent/delivered status claim nahi karti.

Composer/dialer integration ke liye paid API nahi chahiye. WhatsApp ko internet chahiye; SMS/call ki mobile-network cost ho sakti hai. Band app se automatic SMS, WhatsApp ya calls ke liye provider/account, recipient consent aur delivery callbacks chahiye. Tamam channels ka universal free automatic provider available hone ka dawa nahi hai.

## Aapki taraf se mazeed kya chahiye

Maujooda Groq aur openrouteservice keys live test mein chal gayi hain. Keys chat mein na bhejein. Verified hospital maternity/emergency/NICU services, phone, coordinates, source aur verification date wali directory mile to referral aur behtar hoga. Live bed/acceptance information ke liye hospital ki confirmed feed chahiye. Automated messaging chahiye to provider account batayein; tab actual delivery integration banegi.

Staff admin banane ke liye `.venv\Scripts\python.exe scripts/create_admin.py` chalayein. Password private prompt mein enter hota hai. Admin **Team accounts** se clinician/LHW accounts aur patient assignments kar sakta hai. Har patient sirf apna record dekhta hai.

Provider evidence: `docs/live_provider_verification.json`. Model/data audit: `docs/model_audit.json`. Local verification ne synthetic non-identifying observations aur public Peshawar coordinates use kiye; user ki actual GPS location collect nahi ki.
