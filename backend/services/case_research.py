"""Optional three-model research execution. Outputs cannot change care, referral or urgency."""
from datetime import date
from backend.services.model_workbench import predict


def research_for_case(state):
    ctx=state.get("encounter") or {}
    skipped=lambda reason:{"status":"not_assessed","reason":reason,"care_decision_use":False}
    results={name:skipped("Optional research execution not requested") for name in ("pretermguard","gestationinsight","carereach")}
    if not ctx.get("run_research_models"):return results
    vitals=state.get("vitals") or {}
    def run(name,features):
        try:results[name]=predict(name,features)
        except (ValueError,OSError,AttributeError,KeyError):results[name]={"status":"unavailable","care_decision_use":False,"reason":"Research model inference unavailable; clinical care outputs remain unchanged"}
    ctg=state.get("ctg_data")
    if ctg and len(ctg)==21:run("pretermguard",ctg)
    else:results["pretermguard"]=skipped("All 21 compatible measured CTG features are required; target is CTG pattern, not preterm birth")
    labs=ctx.get("gestation_labs") or {}
    if all(labs.get(k) is not None for k in ("skin_thickness_mm","insulin_mu_ml","bmi","diabetes_pedigree_function")) and ctx.get("previous_pregnancies") is not None and all(vitals.get(k) is not None for k in ("age","blood_sugar_mmol_l","diastolic_bp")):
        glucose=vitals["blood_sugar_mmol_l"]*18.0182
        age=vitals["age"];pregnancies=ctx["previous_pregnancies"]+1;dbp=vitals["diastolic_bp"]
        features={"Pregnancies":pregnancies,"Glucose":glucose,"BloodPressure":dbp,"SkinThickness":labs["skin_thickness_mm"],
            "Insulin":labs["insulin_mu_ml"],"BMI":labs["bmi"],"DiabetesPedigreeFunction":labs["diabetes_pedigree_function"],"Age":age,
            "MAP":(2*dbp+dbp+40)/3,"SBP_estimated":dbp+40,"glucose_tolerance_idx":glucose/140,
            "age_parity_interaction":age*pregnancies,"insulin_glucose_ratio":glucose/labs["insulin_mu_ml"]}
        run("gestationinsight",features)
        results["gestationinsight"]["feature_notes"]="Training-defined SBP estimate is DBP+40, not measured BP. Glucose converted to mg/dL. Previous pregnancies + current pregnancy used. Pima proxy is not a pregnancy outcome."
    else:results["gestationinsight"]=skipped("Required measured laboratory/history inputs missing; no family-history score or laboratory value is invented")
    fup=state.get("followup") or {};care=ctx.get("appointment_research") or {}
    if all(care.get(k) is not None for k in ("scholarship","hypertension","diabetes","alcoholism","handicap_code","sms_received")) and all(fup.get(k) is not None for k in ("booking_date","next_appointment_date")) and vitals.get("age") is not None:
        parse=lambda d:date.fromisoformat(d) if isinstance(d,str) else d
        appointment=parse(fup['next_appointment_date']);booked=parse(fup['booking_date']);delta=(appointment-booked).days
        age=vitals['age'];group=next(label for upper,label in ((18,'adolescent'),(25,'young_adult'),(35,'adult'),(45,'middle_age'),(60,'senior'),(100,'elderly')) if age<=upper)
        sms=int(care['sms_received']);hypertension=int(care['hypertension']);diabetes=int(care['diabetes']);alcohol=int(care['alcoholism'])
        run("carereach",{"Age":age,"Scholarship":int(care['scholarship']),"Hipertension":hypertension,"Diabetes":diabetes,"Alcoholism":alcohol,
            "Handcap":care['handicap_code'],"SMS_received":sms,"booking_delta_days":delta,"appointment_dow":appointment.weekday(),
            "sms_x_delta":sms*delta,"comorbidity_count":hypertension+diabetes+alcohol,"Gender":"F","age_group":group})
        results['carereach']['feature_notes']="Booking delay is booking-to-appointment days, not days since the last visit. General appointment dataset proxy; not ANC clinical risk."
    else:results['carereach']=skipped("Appointment history or explicit research variables missing; unknown conditions are not assumed absent")
    return results
