"""One case, four intake sections; measurements are entered once with explicit units."""
import json
import uuid
from datetime import datetime, time
import streamlit as st
from backend.schemas.assessment import WorkflowRequest
from backend.services.ctg_import import ctg_template_csv, parse_ctg_csv, parse_ctg_json, complete_ctg
from backend.services.inference import CTG_FEATURES

UNKNOWN=["Unknown","Yes","No"]
BOOL={"Unknown":None,"Yes":True,"No":False}


def render_assessment_form(patient,preset,key,demo,gps,staff):
    st.download_button("Download approved CTG CSV template",ctg_template_csv(),"ctg-measured-template.csv","text/csv")
    st.caption("CTG requires 21 measured device/export features. Event rates AC/FM/UC/DL/DS/DP are events per second; ASTV/ALTV are percentages. Image/PDF uploads do not extract these features.")
    with st.form("assessment_"+key):
        st.subheader("1 · Patient and pregnancy details")
        st.caption("Patient ID: "+(patient["patient_id"] if patient else "Generated when this case is saved"))
        cols=st.columns(3)
        name=cols[0].text_input("Patient name",value=patient["name"] if patient else "DEMO "+key if demo else st.session_state["user"]["full_name"])
        age=cols[1].number_input("Age (years)",min_value=10,max_value=60,value=patient["age"] if patient else preset.get("age"))
        phone=cols[2].text_input("Contact phone (optional)",value=(patient.get("phone") or "") if patient else "")
        previous_weeks=preset.get("gestational_age_weeks",patient.get("gestational_age_weeks") if patient else None)
        cols=st.columns(3)
        weeks=cols[0].number_input("Pregnancy completed weeks",min_value=0,max_value=45,value=int(previous_weeks) if previous_weeks is not None else None)
        days=cols[1].number_input("Additional pregnancy days",min_value=0,max_value=6,value=round((previous_weeks-int(previous_weeks))*7) if previous_weeks is not None else 0)
        edd=cols[2].date_input("Expected delivery date (optional)",value=None)
        cols=st.columns(3)
        lmp=cols[0].date_input("Last menstrual period (LMP) date (optional)",value=None)
        plurality=cols[1].selectbox("Pregnancy plurality",["Singleton","Twins","Multiple","Unknown"],index=0)
        dating=cols[2].selectbox("Pregnancy dating source",["unknown","clinician","ultrasound","other"],format_func=lambda s:{"unknown":"Unknown","clinician":"Clinician-confirmed","ultrasound":"Ultrasound","other":"Other"}[s])
        
        # Trimester and Visible Date Conflict Resolution
        if weeks is not None:
            tri_name = "1st Trimester (Weeks 1–12)" if weeks <= 12 else "2nd Trimester (Weeks 13–26)" if weeks <= 26 else "3rd Trimester (Weeks 27+)"
            st.info(f"📅 Derived Trimester: **{tri_name}** ({weeks}w {days}d)")
        if lmp is not None and weeks is not None:
            from datetime import date as d_cls
            days_diff = (d_cls.today() - lmp).days
            if days_diff > 0:
                lmp_weeks = days_diff // 7
                if abs(lmp_weeks - weeks) >= 2:
                    st.warning(f"⚠️ Dating Conflict: LMP calculates {lmp_weeks} weeks, but entered age is {weeks} weeks. Clinical dating source ({dating}) will be recorded to visibly reconcile this.")

        cols=st.columns(3)
        previous_pregnancies=cols[0].number_input("Previous pregnancies (excluding current)",min_value=0,max_value=30,value=None)
        previous_births=cols[1].number_input("Previous births",min_value=0,max_value=30,value=patient.get("parity") if patient else None)
        language=cols[2].selectbox("Preferred language",["ur","en","ps"],format_func=lambda v:{"ur":"Urdu","en":"English","ps":"Pashto"}[v])
        complications=st.multiselect("Previous pregnancy complications",["Previous pre-eclampsia","Previous bleeding","Previous caesarean","Previous preterm birth","Previous stillbirth"])
        conditions=st.multiselect("Existing medical conditions",["Hypertension","Diabetes","Heart disease","Anaemia"])
        history_notes=st.text_area("Other history / conditions (original notes)",max_chars=2000)
        st.caption("Use current/live GPS above, or enter manually confirmed coordinates below. These coordinates belong to this patient case.")
        cols=st.columns(3)
        known_location=cols[0].checkbox("Location is known",value=bool(demo or gps or preset.get("latitude") is not None))
        default_lat = float(preset.get("latitude", gps["latitude"] if gps else 34.015000))
        default_lon = float(preset.get("longitude", gps["longitude"] if gps else 71.525000))
        latitude=cols[1].number_input("Latitude",min_value=-90.0,max_value=90.0,value=default_lat if (demo or gps or preset.get("latitude") is not None) else None,format="%.6f",key=key+"_latitude")
        longitude=cols[2].number_input("Longitude",min_value=-180.0,max_value=180.0,value=default_lon if (demo or gps or preset.get("longitude") is not None) else None,format="%.6f",key=key+"_longitude")
        discover=st.checkbox("Allow coordinate sharing with OpenStreetMap to find actual hospitals",value=bool(preset.get("discover", True)),disabled=bool(demo))
        routing=st.checkbox("I consent to sharing these coordinates with the road-routing provider",value=bool(preset.get("routing", True)),disabled=bool(demo))
        storing=st.checkbox("Patient consent obtained to store this case",value=bool(preset.get("storing", False)))
        notifications=st.checkbox("Patient consent obtained for notifications",value=bool(preset.get("notifications", True)))

        st.subheader("2 · Mother's assessment")
        gestation=None if weeks is None else weeks+days/7
        values={"age":age,"gestational_age_weeks":gestation}
        cols=st.columns(3)
        specs=[("systolic_bp","Systolic BP (mmHg)",40.0,300.0),("diastolic_bp","Diastolic BP (mmHg)",20.0,200.0),
               ("heart_rate","Heart rate (bpm)",20.0,250.0),("temperature_celsius","Temperature (C)",30.0,45.0),
               ("blood_sugar_mmol_l","Blood glucose (mmol/L)",0.5,55.0),("respiratory_rate","Breathing rate (breaths/min)",4.0,80.0)]
        for i,(field,label,lo,hi) in enumerate(specs):
            values[field]=cols[i%3].number_input(label,min_value=lo,max_value=hi,value=float(preset[field]) if field in preset else None,step=.1,format="%.1f")
        with st.expander("Alternate unit inputs (°F thermometer / mg/dL glucometer)", expanded=False):
            st.caption("Standard inputs are Celsius (°C) and mmol/L. If measured with °F or mg/dL, enter here to convert automatically:")
            conv_cols = st.columns(2)
            f_temp = conv_cols[0].number_input("Measured Body Temp (°F)", min_value=86.0, max_value=113.0, value=float(preset["BodyTemp"]) if "BodyTemp" in preset else None, step=0.1, format="%.1f")
            mg_bs = conv_cols[1].number_input("Measured Blood Sugar (mg/dL)", min_value=10.0, max_value=1000.0, value=float(preset["BS_mg"]) if "BS_mg" in preset else None, step=1.0, format="%.1f")
            if f_temp is not None and values.get("temperature_celsius") is None:
                values["temperature_celsius"] = round((f_temp - 32) * 5 / 9, 1)
            if mg_bs is not None and values.get("blood_sugar_mmol_l") is None:
                values["blood_sugar_mmol_l"] = round(mg_bs / 18.0182, 1)
        cols=st.columns(3)
        measured_date=cols[0].date_input("Measurement date (optional)",value=None)
        measured_time=cols[1].time_input("Measurement time (Pakistan local)",value=time(12,0))
        glucose_type=cols[2].selectbox("Blood sugar test type",["unknown","fasting","random","clinical_test"],format_func=lambda v:v.replace('_',' ').title())
        cols=st.columns(3)
        values["vaginal_bleeding"]=cols[0].selectbox("Vaginal bleeding",[None,"none","mild","moderate","severe"],format_func=lambda v:"Unknown" if v is None else v.title())
        values["headache_severity"]=cols[1].selectbox("Headache severity",[None,"none","mild","moderate","severe"],format_func=lambda v:"Unknown" if v is None else v.title())
        values["consciousness_level"]=cols[2].selectbox("Consciousness level",[None,"alert","drowsy","unconscious"],format_func=lambda v:"Unknown" if v is None else v.title())
        for i,(field,label) in enumerate([("visual_disturbance","Vision disturbance"),("epigastric_pain","Upper abdominal pain"),("convulsions","Convulsions"),("vaginal_discharge_foul","Foul-smelling vaginal discharge")]):
            values[field]=BOOL[cols[i%3].selectbox(label,UNKNOWN)]
        symptoms=st.multiselect("Other structured reported symptoms",["Severe headache","Blurred vision","Vaginal bleeding","Convulsions","Reduced fetal movement","Severe abdominal pain"],default=preset.get("symptoms",[]))
        additional_symptoms=st.text_area("Additional symptom notes (not automatically converted to danger signs)",max_chars=2000)
        additional_tests=st.text_area("Other clinical test results and units (optional)",max_chars=2000)
        with st.expander("Optional additional measurements for GestationInsight research"):
            st.caption("Not mandatory. A dataset-specific family-history score must not be guessed. These records do not make a validated pregnancy-complication model.")
            hw_cols = st.columns(2)
            h_cm = hw_cols[0].number_input("Patient height (cm, optional)", min_value=100.0, max_value=250.0, value=None)
            w_kg = hw_cols[1].number_input("Patient weight (kg, optional)", min_value=30.0, max_value=250.0, value=None)
            calc_bmi = round(w_kg / ((h_cm / 100) ** 2), 1) if (h_cm and w_kg) else None
            if calc_bmi:
                st.caption(f"Calculated BMI: {calc_bmi} kg/m²")
            labs={}
            cols=st.columns(2)
            for i,(field,label,hi) in enumerate([("bmi","BMI (kg/m²)",100.0),("skin_thickness_mm","Skinfold thickness (mm)",100.0),("insulin_mu_ml","Insulin (µU/mL)",3000.0),("diabetes_pedigree_function","Dataset-specific diabetes pedigree score",5.0)]):
                labs[field]=cols[i%2].number_input(label,min_value=.01,max_value=hi,value=calc_bmi if field=="bmi" and calc_bmi else None)

        st.subheader("3 · Baby's assessment")
        cols=st.columns(2)
        started=BOOL[cols[0].selectbox("Has the mother started feeling movements?",UNKNOWN)]
        reduced=BOOL[cols[1].selectbox("Are movements less/different than usual?",UNKNOWN,index=1 if "Reduced fetal movement" in preset.get("symptoms",[]) else 0)]
        if reduced is True:
            values["fetal_movement_present"]=False
        elif started is True and reduced is False:
            values["fetal_movement_present"]=True
        elif started is False and (weeks or 0)>=24:
            values["fetal_movement_present"]=False
        else:
            values["fetal_movement_present"]=None
        cols=st.columns(2)
        concern_date=cols[0].date_input("Movement concern date (optional)",value=None)
        concern_time=cols[1].time_input("Movement concern time (Pakistan local)",value=time(12,0))
        fetal_notes=st.text_area("Baby / movement clinician notes",max_chars=2000)
        ctg_available=st.selectbox("CTG available?",UNKNOWN,index=1 if preset.get("ctg") else 0)
        if ctg_available in ("No","Unknown"):
            st.info("Fetal CTG assessment not performed. Movement safety information is still assessed.")
        ctg_method=st.radio("CTG input method",["JSON","CSV upload","Advanced measured features"],horizontal=True)
        ctg_text=st.text_area("Optional measured CTG JSON (21 features)",value=st.session_state.get("demo_ctg_json","") if preset.get("ctg") else "",height=100)
        ctg_upload=st.file_uploader("Upload approved single-record CTG CSV",type=["csv"])
        with st.expander("Advanced measured CTG feature entry"):
            st.caption("Supply only measured compatible device/export values. Leave unknown values blank.")
            entered={}
            cols=st.columns(3)
            for i,feature in enumerate(CTG_FEATURES):entered[feature]=cols[i%3].number_input(feature,value=None,format="%.6f",key="ctg_"+feature+key)
        st.caption("CTG available = No/Unknown: no fetal CTG prediction. Existing movement safety information is still assessed.")

        st.subheader("4 · Appointments and follow-up")
        contacts=st.multiselect("Completed ANC contact milestones (weeks)",[12,20,26,30,34,36,38,40],default=preset.get("contacts",[]))
        cols=st.columns(3)
        booked=cols[0].date_input("Appointment booking date (optional)",value=None)
        appointment=cols[1].date_input("Clinician's next appointment (optional)",value=None)
        last_visit=cols[2].date_input("Last completed checkup date (optional)",value=None)
        cols=st.columns(3)
        missed=cols[0].number_input("Reported missed visits",min_value=0,max_value=50,value=preset.get("missed",0))
        transport=cols[1].checkbox("Transport barrier",value=preset.get("transport",False))
        phone_access=BOOL[cols[2].selectbox("Phone access",UNKNOWN,index=2 if preset.get("phone") is False else 0)]
        cols=st.columns(2)
        sent=BOOL[cols[0].selectbox("Was a reminder actually sent previously?",UNKNOWN)]
        channel=cols[1].selectbox("Preferred notification channel",["app","sms","whatsapp","call","health_worker_visit"])
        with st.expander("Optional appointment research variables"):
            st.caption("Unknown remains unknown. These variables only support the general no-show research model.")
            care_research={}
            cols=st.columns(2)
            for i,(field,label) in enumerate([("sms_received","Was an SMS reminder actually received?"),("scholarship","Financial scholarship/support"),("hypertension","Recorded hypertension"),("diabetes","Recorded diabetes"),("alcoholism","Recorded alcoholism")]):
                care_research[field]=BOOL[cols[i%2].selectbox(label,UNKNOWN)]
            care_research["handicap_code"]=st.number_input("Dataset-specific handicap code (0-4, if known)",min_value=0,max_value=4,value=None)
        run_research=st.checkbox("Run available research models after assessment (never determine care)",value=bool(preset.get("run_research", True)))
        allow_ai=st.checkbox("Allow de-identified observations and symptoms to be processed by Groq for Urdu and English reports",value=bool(preset.get("allow_ai", True)))
        st.caption("Reports always preserve recorded facts. Groq explanation follows predictions; qualified clinician review remains required.")
        submitted=st.form_submit_button("Run Assessment · save case and generate two reports",width="stretch")
    if not submitted:return None
    if not storing:raise ValueError("Obtain patient consent to store the case before saving")
    if age is None or not name.strip():raise ValueError("Record the patient's name and age")
    if weeks is None and days:raise ValueError("Record completed pregnancy weeks before additional days")
    ctg=None
    if ctg_available=="Yes":
        if ctg_method=="CSV upload":
            if ctg_upload is None:raise ValueError("Upload the measured CTG CSV")
            ctg=parse_ctg_csv(ctg_upload.getvalue())
        elif ctg_method=="Advanced measured features":ctg=complete_ctg({k:v for k,v in entered.items() if v is not None})
        else:ctg=parse_ctg_json(ctg_text)
    elif ctg_text.strip() or ctg_upload is not None or any(v is not None for v in entered.values()):
        raise ValueError("CTG data was supplied: select CTG available = Yes to assess it")
    location={"latitude":latitude,"longitude":longitude,"source":"demo" if demo else gps.get("source","gps") if gps and latitude==gps["latitude"] and longitude==gps["longitude"] else "manual","share_for_routing":routing,"share_for_discovery":discover} if known_location else None
    if location and location["source"]=="gps":location.update(accuracy_m=gps.get("accuracy_m"),captured_at=gps.get("captured_at"))
    from zoneinfo import ZoneInfo
    stamp=lambda d,t:datetime.combine(d,t,tzinfo=ZoneInfo("Asia/Karachi")).isoformat() if d else None
    payload={"patient_id":patient["patient_id"] if patient else "new","case_id":str(uuid.uuid4()),
      "vitals":{k:v for k,v in values.items() if v is not None},"symptoms":[{"name":s,"severity":"severe"} for s in symptoms],
      "ctg_features":ctg,"ctg_source":"demo" if demo and ctg is not None else "uci_measured" if ctg is not None else None,
      "provenance":"demo" if demo else "measured" if staff else "patient_reported","location":location,
      "language":language,"allow_llm_processing":allow_ai,
      "encounter":{"expected_delivery_date":edd.isoformat() if edd else None,"dating_source":dating,
         "previous_pregnancies":previous_pregnancies,"previous_births":previous_births,"previous_complications":complications,
         "medical_conditions":conditions,"history_notes":history_notes,"measurement_taken_at":stamp(measured_date,measured_time),
         "glucose_test_type":glucose_type,"additional_test_results":additional_tests,"additional_symptoms":additional_symptoms,
         "movements_started":started,"movements_reduced":reduced,"movement_concern_noticed_at":stamp(concern_date,concern_time),
         "fetal_notes":fetal_notes,"preferred_language":language,"storage_consent":storing,"notification_consent":notifications,
         "gestation_labs":labs,"run_research_models":run_research,"appointment_research":care_research},
      "followup":{"gestational_age_weeks":gestation,"completed_contact_weeks":contacts,"missed_visits":missed,
         "transport_barrier":transport,"phone_access":phone_access,"next_appointment_date":appointment.isoformat() if appointment else None,
         "booking_date":booked.isoformat() if booked else None,"last_completed_checkup_date":last_visit.isoformat() if last_visit else None,
         "reminder_actually_sent":sent,"preferred_notification_channel":channel}}
    WorkflowRequest.model_validate(payload)
    return {"payload":payload,"profile":{"name":name.strip(),"age":age,"gestational_age_weeks":gestation,"phone":phone.strip() or None,"parity":previous_births,"language":language}}
