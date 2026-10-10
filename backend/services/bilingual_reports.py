"""Two bilingual, source-grounded case reports; optional AI prose cannot replace recorded facts."""
from datetime import datetime, timezone
from html import escape
from backend.services.reporting import recommended_care_actions
from backend.services.referral_planner import effective_urgency

TERMS = {
    "unknown":"نامعلوم", "available":"دستیاب", "unavailable":"دستیاب نہیں",
    "location_required":"مقام درکار", "no_matching_facility":"مطابق ہسپتال دستیاب نہیں",
    "unverified_candidate_requires_confirmation":"غیر مصدقہ امیدوار؛ تصدیق درکار",
    "candidate_requires_confirmation":"امیدوار؛ قبول کرنے کی تصدیق درکار",
    "reported_service_tags_then_straight_line":"نقشے کی خدمات کی معلومات، پھر سیدھا فضائی فاصلہ",
    "road_eta":"سڑک سے اندازاً سفر کا وقت", "straight_line_distance":"سیدھا فضائی فاصلہ",
    "not_assessed":"جانچ نہیں ہوئی", "research_prediction":"صرف تحقیقی ماڈل کا نتیجہ",
    "experimental":"تجرباتی نتیجہ", "not recorded":"درج نہیں", "none":"نہیں",
    "routine":"معمول کی پیروی", "urgent":"فوری طبی توجہ", "emergency":"ہنگامی", "low risk":"کم خطرے کی ماڈل کیٹیگری",
    "mid risk":"درمیانی خطرے کی ماڈل کیٹیگری", "high risk":"زیادہ خطرے کی ماڈل کیٹیگری",
    "normal":"نارمل ماڈل کیٹیگری", "suspect":"تشویش کی ماڈل کیٹیگری", "pathological":"غیر معمولی ماڈل کیٹیگری",
    "LOW_RISK":"دی گئی معلومات میں مقررہ خطرے کی علامت متحرک نہیں ہوئی", "URGENT":"فوری طبی معائنہ درکار",
    "HIGH_RISK_EMERGENCY":"ہنگامی خطرے کی علامات", "INSUFFICIENT_DATA":"معلومات ناکافی",
    "reminder":"یاددہانی", "call":"فون پر رابطہ", "home_visit":"ہیلتھ ورکر کا گھر پر دورہ",
    "emergency_assessment":"فوری ہنگامی معائنہ", "schedule_contact":"اگلا معائنہ طے کریں",
    "straight_line":"سیدھا فضائی فاصلہ؛ سڑک کا فاصلہ نہیں", "road":"سڑک کا فاصلہ", "gps":"جی پی ایس",
    "manual":"دستی درج کردہ", "measured":"ناپی گئی معلومات", "patient_reported":"مریضہ کی بتائی ہوئی معلومات",
    "fasting":"خالی پیٹ", "random":"کسی بھی وقت", "clinical_test":"طبی ٹیسٹ", "clinician":"معالج کی تصدیق",
    "ultrasound":"الٹراساؤنڈ", "other":"دیگر", "alert":"ہوش میں", "drowsy":"غنودگی", "unconscious":"بے ہوش",
    "mild":"ہلکی", "moderate":"درمیانی", "severe":"شدید", "immediate":"فوری", "high":"زیادہ", "medium":"درمیانی",
    "app":"ایپ", "sms":"ایس ایم ایس", "whatsapp":"واٹس ایپ", "health_worker_visit":"ہیلتھ ورکر کا دورہ",
    "severe_hypertension":"بہت زیادہ بلڈ پریشر", "convulsions":"دورے", "vaginal_bleeding":"اندام نہانی سے خون",
    "pre_eclampsia_danger_signs":"پری ایکلیمپسیا سے متعلق خطرے کی علامات", "reduced_fetal_movement":"بچے کی حرکت میں کمی",
    "altered_consciousness":"ہوش میں تبدیلی", "fever_with_foul_discharge":"بخار اور بدبودار اخراج", "hypotension":"کم بلڈ پریشر",
    "Severe headache":"شدید سر درد", "Blurred vision":"دھندلا نظر آنا", "Vaginal bleeding":"اندام نہانی سے خون",
    "Convulsions":"دورے", "Reduced fetal movement":"بچے کی حرکت میں کمی", "Severe abdominal pain":"پیٹ کا شدید درد",
    "Hypertension":"ہائی بلڈ پریشر", "Diabetes":"ذیابیطس", "Heart disease":"دل کی بیماری", "Anaemia":"خون کی کمی",
    "Previous pre-eclampsia":"پہلے پری ایکلیمپسیا", "Previous bleeding":"پہلے خون بہنا", "Previous caesarean":"پہلے سیزیرین",
    "Previous preterm birth":"پہلے وقت سے پہلے پیدائش", "Previous stillbirth":"پہلے مردہ بچے کی پیدائش",
}
OBSERVATIONS=[
 ("age","Age","عمر","years"),("gestational_age_weeks","Pregnancy age","حمل کی عمر","weeks"),
 ("systolic_bp","Systolic BP","اوپری بلڈ پریشر","mmHg"),("diastolic_bp","Diastolic BP","نچلا بلڈ پریشر","mmHg"),
 ("heart_rate","Heart rate","دل کی دھڑکن","bpm"),("temperature_celsius","Temperature","درجہ حرارت","°C"),
 ("blood_sugar_mmol_l","Blood glucose","بلڈ شوگر","mmol/L"),("respiratory_rate","Breathing rate","سانس کی رفتار","/min"),
 ("vaginal_bleeding","Vaginal bleeding","اندام نہانی سے خون",""),("headache_severity","Headache severity","سر درد کی شدت",""),
 ("visual_disturbance","Vision disturbance","نظر میں خرابی",""),("epigastric_pain","Upper abdominal pain","پیٹ کے اوپری حصے میں درد",""),
 ("convulsions","Convulsions","دورے",""),("vaginal_discharge_foul","Foul-smelling discharge","بدبودار اخراج",""),
 ("consciousness_level","Consciousness","ہوش کی حالت",""),("fetal_movement_present","Fetal movement flag","بچے کی حرکت کی حفاظتی علامت",""),
]


TERMS.update({key:ur for key,en,ur,unit in OBSERVATIONS})
TERMS.update({"CTG pattern CLASS (not preterm birth)":"CTG پیٹرن CLASS؛ وقت سے پہلے پیدائش کا نتیجہ نہیں",
    "Pima-derived research label":"Pima ڈیٹاسیٹ کی تحقیقی کیٹیگری", "General appointment no-show label":"عام ملاقات میں غیر حاضری کی کیٹیگری"})

def value_text(value, lang):
    if value is None or value=="":return "Not recorded / unknown" if lang=="en" else "درج نہیں / نامعلوم"
    if isinstance(value,bool):return ("Yes" if value else "No") if lang=="en" else ("ہاں" if value else "نہیں")
    if isinstance(value,list):return ", ".join(value_text(v,lang) for v in value) if value else ("None recorded" if lang=="en" else "کچھ درج نہیں")
    text=str(value)
    return TERMS.get(text,text) if lang=="ur" else text


def care_steps(urgency,safety,lang):
    if lang=="en":
        return recommended_care_actions(urgency,safety)+[
            "Share this report and the original measurements with a qualified maternity clinician.",
            "Arrange appropriate transport and a companion with the health worker; confirm the receiving service.",
            "Record any new or worsening symptoms and seek clinical help. Do not use these experimental model labels to prescribe treatment or decide a delivery plan."]
    first={"emergency":"فوراً ہنگامی زچگی کے معائنے کے لیے رابطہ کریں۔ معمول کی ملاقات، ماڈل کے نتیجے یا سافٹ ویئر کی منظوری کا انتظار نہ کریں۔",
           "urgent":"جلد مستند زچگی کے معالج سے معائنہ کروائیں۔",
           "routine":"مقررہ طبی معائنے جاری رکھیں اور نئی علامات پر طبی مدد لیں۔"}[urgency]
    if safety.get("triage_level")=="INSUFFICIENT_DATA" and urgency=="routine":
        first="جو پیمائشیں درج نہیں وہ حاصل کریں؛ کسی بھی تشویش پر طبی معائنہ کروائیں۔"
    return [first,"یہ رپورٹ اور اصل پیمائشیں مستند زچگی کے معالج کو دیں۔",
            "ہیلتھ ورکر کے ساتھ مناسب سواری اور ساتھ جانے والے فرد کا بندوبست کریں؛ متعلقہ ہسپتال سے تصدیق کریں۔",
            "نئی یا بڑھتی علامات درج کریں اور طبی مدد لیں۔ تجرباتی ماڈل کی کیٹیگری سے دوا یا پیدائش کا منصوبہ طے نہ کریں۔"]


def build_two_reports(state):
    clinical=state.get("clinical_risk_result") or {}
    safety=clinical.get("who_red_flags") or {}
    maternal=clinical.get("maternal_risk") or {}
    fetal=state.get("fetal_result") or {}
    anc=state.get("anc_result") or {}
    referral=state.get("referral_result") or {}
    encounter=state.get("encounter") or {}
    followup=state.get("followup") or {}
    vitals=state.get("vitals") or {}
    identity=state.get("patient_context") or {}
    urgency=effective_urgency(safety,maternal,fetal)
    ai=(state.get("clinician_result") or {}).get("ai_assistance") or {}
    generated=datetime.now(timezone.utc).isoformat()
    reports={}
    for kind in ("care","referral"):
        report={"kind":kind,"case_id":state.get("case_id"),"generated_at":generated,"urgency":urgency,
                "review_status":"pending","llm_generated":False,"languages":{}}
        for lang in ("en","ur"):
            is_en=lang=="en"
            sections=[]
            def section(en,ur,lines):sections.append({"heading":en if is_en else ur,"lines":lines})
            def field(en,ur,val,unit=""):
                if not is_en:unit={"years":"سال","weeks":"ہفتے","min":"منٹ"}.get(unit,unit)
                return (en if is_en else ur)+": "+value_text(val,lang)+(f" {unit}" if val is not None and unit else "")
            section("Patient and case","مریضہ اور کیس",[
                field("Case ID","کیس نمبر",state.get("case_id")),field("Patient ID","مریضہ نمبر",state.get("patient_id")),
                field("Name","نام",identity.get("name")),field("Contact","رابطہ",identity.get("phone")),
                field("Urgency","توجہ کی ترجیح",urgency),field("Provenance","معلومات کا ذریعہ",state.get("provenance")),
                field("Generated UTC","رپورٹ کا وقت UTC",generated)])
            if kind=="care":
                section("Mother's measured observations and safety","ماں کی پیمائشیں اور حفاظتی علامات",[
                    field(en,ur,vitals.get(key),unit) for key,en,ur,unit in OBSERVATIONS]+[
                    field("Measured at","پیمائش کا وقت",encounter.get("measurement_taken_at")),
                    field("Glucose test type","شوگر ٹیسٹ کی قسم",encounter.get("glucose_test_type")),
                    field("Rule triage","حفاظتی قواعد کا نتیجہ",safety.get("triage_level")),
                    field("Triggered danger signs","خطرے کی متحرک علامات",safety.get("triggered_rules",[])),
                    field("Missing measurements","نامکمل پیمائشیں",state.get("missing_fields") or safety.get("missing_fields",[])),
                    field("Reported symptoms","بتائی ہوئی علامات",[value_text(s.get("name"),lang)+" ("+value_text(s.get("severity"),lang)+")" for s in state.get("symptoms",[])])])
                section("Pregnancy history and available tests","حمل کی سابقہ معلومات اور دستیاب ٹیسٹ",[
                    field("Expected delivery date","متوقع تاریخ پیدائش",encounter.get("expected_delivery_date")),
                    field("Dating source","حمل کی تاریخ کا ذریعہ",encounter.get("dating_source")),
                    field("Previous pregnancies","پچھلے حمل",encounter.get("previous_pregnancies")),
                    field("Previous births","پچھلی پیدائشیں",encounter.get("previous_births")),
                    field("Previous complications","پچھلی پیچیدگیاں",encounter.get("previous_complications",[])),
                    field("Existing conditions","موجودہ بیماریاں",encounter.get("medical_conditions",[])),
                    field("History notes (original text)","سابقہ معلومات کے نوٹس (اصل متن)",encounter.get("history_notes")),
                    field("Additional symptoms (original text; not structured triage)","اضافی علامات (اصل متن؛ خودکار حفاظتی فیصلہ نہیں)",encounter.get("additional_symptoms")),
                    field("Other tests (original text)","دیگر ٹیسٹ (اصل متن)",encounter.get("additional_test_results")),
                    *[field(en,ur,(encounter.get("gestation_labs") or {}).get(key),unit) for key,en,ur,unit in [
                        ("bmi","BMI","باڈی ماس انڈیکس","kg/m²"),("skin_thickness_mm","Skinfold thickness","جلد کی موٹائی","mm"),
                        ("insulin_mu_ml","Insulin","انسولین","µU/mL"),("diabetes_pedigree_function","Dataset-specific family-history score","ڈیٹاسیٹ کا مخصوص خاندانی اسکور","")]]])
                section("Baby and prediction evidence","بچے کی جانچ اور ماڈل کے نتائج",[
                    field("Movements started","کیا حرکت محسوس ہونا شروع ہوئی",encounter.get("movements_started")),
                    field("Movements less/different than usual","کیا حرکت معمول سے کم یا مختلف ہے",encounter.get("movements_reduced")),
                    field("Concern first noticed","تشویش پہلی بار کب ہوئی",encounter.get("movement_concern_noticed_at")),
                    field("Fetal notes (original text)","بچے کے نوٹس (اصل متن)",encounter.get("fetal_notes")),
                    field("Maternal model category","ماں کے ماڈل کی کیٹیگری",maternal.get("risk_level")),
                    field("Maternal model version","ماں کے ماڈل کا ورژن",maternal.get("model_version")),
                    field("Fetal CTG category","بچے کے CTG ماڈل کی کیٹیگری",fetal.get("fetal_status","not_assessed")),
                    field("Fetal model version","بچے کے ماڈل کا ورژن",fetal.get("model_version")),
                    field("Maternal class probabilities (uncalibrated)","ماں کی کیٹیگری کے امکانات (طبی اعتبار ثابت نہیں)",[f"{value_text(k,lang)}: {v:.4f}" for k,v in (maternal.get("probabilities") or {}).items()]),
                    field("Fetal class probabilities (uncalibrated)","بچے کی کیٹیگری کے امکانات (طبی اعتبار ثابت نہیں)",[f"{value_text(k,lang)}: {v:.4f}" for k,v in (fetal.get("probabilities") or {}).items()]),
                    "No measured CTG: fetal CTG assessment not performed." if is_en and not state.get("ctg_data") else "ناپی ہوئی CTG معلومات نہیں: بچے کی CTG جانچ نہیں ہوئی۔" if not is_en and not state.get("ctg_data") else ("Compatible measured CTG features were assessed." if is_en else "مطابقت رکھنے والی ناپی ہوئی CTG معلومات کا جائزہ لیا گیا۔"),
                    "Experimental labels are not diagnoses or calibrated confidence. No local clinical validation established." if is_en else "تجرباتی کیٹیگری تشخیص یا ثابت شدہ اعتماد نہیں۔ مقامی طبی توثیق ابھی قائم نہیں ہوئی۔"])
                research=state.get("research_results") or {}
                research_lines=[]
                for model,target in (("pretermguard","CTG pattern CLASS (not preterm birth)"),("gestationinsight","Pima-derived research label"),("carereach","General appointment no-show label")):
                    output=research.get(model) or {}
                    research_lines.extend([field("Model","ماڈل",model),field("Research target","تحقیقی ہدف",target),
                        field("Status","حالت",output.get("status","not_assessed")),field("Dataset label","ڈیٹاسیٹ کی کیٹیگری",output.get("label")),
                        field("Version","ورژن",output.get("model_version")),
                        field("Research probabilities (uncalibrated)","تحقیقی امکانات (طبی اعتبار ثابت نہیں)",[f"{k}: {v:.4f}" for k,v in (output.get("probabilities") or {}).items()]),
                        field("Research note (source text)","تحقیقی وضاحت (اصل متن)",(output.get("reason") or output.get("feature_notes")) if is_en else ("ضروری ناپی ہوئی معلومات پوری نہیں یا تحقیقی جانچ منتخب نہیں کی گئی؛ کوئی قدر فرض نہیں کی گئی۔" if output.get("status")=="not_assessed" else "صرف ڈیٹاسیٹ کی تحقیقی کیٹیگری؛ حمل کا ثابت شدہ طبی نتیجہ نہیں۔"))])
                if research_lines:
                    section("Optional research evidence — does not determine care","اختیاری تحقیقی شواہد — علاج کا فیصلہ نہیں",research_lines+[
                        "These targets are not validated pregnancy outcomes; they do not change urgency, follow-up or destination." if is_en else "یہ اہداف حمل کے توثیق شدہ نتائج نہیں؛ ان سے خطرے، اگلے معائنے یا ہسپتال کا فیصلہ تبدیل نہیں ہوتا۔"])
                section("Next actions and prevention of delay","اگلے اقدامات اور تاخیر سے بچاؤ",care_steps(urgency,safety,lang))
                section("Appointments and follow-up","ملاقاتیں اور اگلا معائنہ",[
                    field("Priority","ترجیح",anc.get("priority")),field("Action","اقدام",anc.get("recommended_action")),
                    field("Appointment booked on","ملاقات کی بکنگ کی تاریخ",followup.get("booking_date")),
                    field("Last completed checkup","آخری مکمل معائنے کی تاریخ",followup.get("last_completed_checkup_date")),
                    field("Next appointment","اگلی ملاقات",anc.get("next_appointment_date")),
                    field("Estimated pregnancy age at appointment","ملاقات پر حمل کی اندازاً عمر",anc.get("next_appointment_gestational_age_weeks"),"weeks"),
                    field("Next reminder","اگلی یاددہانی",anc.get("next_reminder_date")),
                    field("Completed contact weeks","مکمل معائنوں کے ہفتے",followup.get("completed_contact_weeks",[])),
                    field("Missed visits","چھوٹے ہوئے معائنے",followup.get("missed_visits")),
                    field("Transport barrier","سواری میں رکاوٹ",followup.get("transport_barrier")),field("Phone access","فون کی دستیابی",followup.get("phone_access")),
                    field("Reminder previously sent","کیا پہلے یاددہانی بھیجی گئی",followup.get("reminder_actually_sent")),
                    field("Preferred channel","پسندیدہ رابطہ",followup.get("preferred_notification_channel")),
                    field("Notification consent","اطلاع کی اجازت",encounter.get("notification_consent")),
                    "A task/draft is not proof of a sent message or completed visit." if is_en else "ٹاسک یا مسودہ پیغام بھیجے جانے یا دورہ مکمل ہونے کا ثبوت نہیں۔"])
            else:
                point=state.get("location") or {}
                section("Current recorded position","موجودہ درج کردہ مقام",[
                    field("Latitude","عرض البلد",point.get("latitude")),field("Longitude","طول البلد",point.get("longitude")),
                    field("Location source","مقام کا ذریعہ",point.get("source")),field("Captured at","مقام درج ہونے کا وقت",point.get("captured_at")),
                    field("GPS accuracy","جی پی ایس کی درستگی",point.get("accuracy_m"),"m"),
                    field("Discovery consent","ہسپتال تلاش کرنے کی اجازت",point.get("share_for_discovery")),
                    field("Road-routing consent","سڑک کا فاصلہ معلوم کرنے کی اجازت",point.get("share_for_routing"))])
                required=referral.get("capabilities_needed") or {}
                service_names={"has_maternity":("Maternity","زچگی"),"has_emergency":("Emergency","ہنگامی خدمات"),"has_nicu":("Newborn/NICU","نومولود / NICU")}
                section("Required services and ranking","مطلوبہ خدمات اور ہسپتال کا انتخاب",[
                    field("Services needed","درکار خدمات",[service_names[k][0 if is_en else 1] for k in service_names if required.get(k)]),
                    field("Referral status","ریفرل کی حالت",referral.get("status")),
                    field("Ranking basis","ترتیب کی بنیاد",referral.get("ranking_basis")),
                    field("Search coverage","تلاش کا دائرہ",referral.get("coverage_radius_km"),"km"),
                    field("Limited search coverage","تلاش کا محدود دائرہ",referral.get("coverage_limited",False)),
                    "Verified required services are matched before travel distance. Map-tag candidates require direct confirmation." if is_en else "تصدیق شدہ مطلوبہ خدمات کو فاصلے پر ترجیح دی جاتی ہے۔ نقشے کے امیدوار ہسپتال سے براہ راست تصدیق درکار ہے۔"])
                selected=referral.get("selected_facility") or {}
                facilities=referral.get("ranked_facilities") or []
                if not facilities:
                    section("No hospital candidate available","ہسپتال کا امیدوار دستیاب نہیں",[
                        "Contact maternity/emergency services manually. Emergency assessment must not wait for GPS, an API or this report." if is_en else "زچگی یا ہنگامی خدمات سے خود رابطہ کریں۔ ہنگامی معائنہ جی پی ایس، API یا اس رپورٹ کا انتظار نہ کرے۔"])
                for fac in facilities:
                    distance=fac.get("distance_km")
                    distance_label=(f"{distance*1000:.0f} m" if distance<1 else f"{distance:.2f} km") if isinstance(distance,(int,float)) else None
                    lines=[field("Hospital","ہسپتال",fac.get("name")),field("Latitude","عرض البلد",fac.get("latitude")),
                        field("Longitude","طول البلد",fac.get("longitude")),field("Distance","فاصلہ",distance_label),
                        field("Distance type","فاصلے کی قسم",fac.get("distance_kind")),field("Estimated road travel time","سڑک سے سفر کا اندازاً وقت",fac.get("travel_time_minutes"),"min"),
                        field("Phone","فون",fac.get("phone")),field("Directory source","ریکارڈ کا ذریعہ",fac.get("source")),
                        field("Services verified","خدمات کی تصدیق",fac.get("capabilities_verified",False)),
                        field("Verified on","تصدیق کی تاریخ",fac.get("verified_at")),field("Availability","دستیابی",fac.get("availability")),
                        field("Availability checked","دستیابی کی تصدیق کا وقت",fac.get("availability_checked_at"))]
                    for key,(en,ur) in service_names.items():
                        verified=bool(fac.get("capabilities_verified"))
                        val=fac.get(key) if verified else (fac.get("reported_services") or {}).get(key)
                        lines.append(field(en+(" (verified)" if verified else " (map-reported, unverified)"),ur+(" (تصدیق شدہ)" if verified else " (نقشے کی غیر مصدقہ معلومات)"),val))
                    lines += [field("Directions URL","راستے کا لنک",fac.get("directions_url")),
                        "Confirm required services, beds, access and acceptance by phone. A candidate is not an accepted referral." if is_en else "فون پر مطلوبہ خدمات، بستر، رسائی اور مریضہ کو قبول کرنے کی تصدیق کریں۔ امیدوار ہسپتال کا مطلب منظور شدہ ریفرل نہیں۔"]
                    is_selected=fac.get("facility_id")==selected.get("facility_id")
                    section("Suggested hospital candidate" if is_selected else "Alternative hospital candidate","تجویز کردہ امیدوار ہسپتال" if is_selected else "متبادل امیدوار ہسپتال",lines)
                section("Transfer handover","منتقلی کے وقت معلومات",care_steps(urgency,safety,lang)+[
                    "Share Report 1 with the receiving clinician. Road ETA is an estimate; straight-line distance does not describe the road route." if is_en else "پہلی رپورٹ متعلقہ معالج کو دیں۔ سفر کا وقت اندازہ ہے؛ سیدھا فضائی فاصلہ سڑک کا راستہ نہیں بتاتا۔"])
            ai_key=("care" if kind=="care" else "referral")+"_explanation_"+("english" if is_en else "urdu")
            ai_text=ai.get(ai_key) if ai.get("llm_generated") else None
            if ai_text:
                section("Groq explanation — clinician review required","Groq کی وضاحت — معالج کا جائزہ ضروری",[ai_text])
                report["llm_generated"]=True
            section("Clinical review","معالج کا جائزہ",[
                "Pending qualified clinician review. This report cannot guarantee safety of mother or baby and does not prescribe treatment." if is_en else "مستند معالج کے جائزے کا انتظار ہے۔ یہ رپورٹ ماں یا بچے کی سلامتی کی ضمانت یا علاج کا نسخہ نہیں۔",
                "Emergency care must not wait for the language model or software approval." if is_en else "ہنگامی علاج زبان کے ماڈل یا سافٹ ویئر کی منظوری کا انتظار نہ کرے۔"])
            title=("Report 1: Mother and baby care" if kind=="care" else "Report 2: Location and hospital referral") if is_en else ("رپورٹ ۱: ماں اور بچے کی دیکھ بھال" if kind=="care" else "رپورٹ ۲: مقام اور ہسپتال ریفرل")
            report["languages"][lang]={"title":title,"sections":sections,"text":title+"\n\n"+"\n\n".join(s["heading"]+"\n"+"\n".join(s["lines"]) for s in sections)}
        reports[kind]=report
    return reports


def report_html(report):
    articles=[]
    for lang in ("en","ur"):
        item=report["languages"][lang]
        body="".join("<section><h2>"+escape(s["heading"])+"</h2><ul>"+"".join("<li>"+escape(line)+"</li>" for line in s["lines"])+"</ul></section>" for s in item["sections"])
        articles.append(f'<article lang="{lang}" dir="'+('rtl' if lang=='ur' else 'ltr')+'"><h1>'+escape(item['title'])+'</h1>'+body+'</article>')
    return '<!doctype html><html><head><meta charset="utf-8"><title>MaaHifazat report</title><style>body{max-width:960px;margin:24px auto;padding:20px;font:17px/1.8 Arial,sans-serif;color:#123b37}article{margin-bottom:48px}section{break-inside:avoid}li{white-space:pre-wrap;overflow-wrap:anywhere}h2{font-size:20px}@media print{article+article{break-before:page}}</style></head><body>'+''.join(articles)+'</body></html>'
