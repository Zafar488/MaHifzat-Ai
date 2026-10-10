"""Explicitly fictional judge-demo patient observations."""
SCENARIOS = {
    "Routine ANC": {"age":26,"systolic_bp":118,"diastolic_bp":76,"heart_rate":74,"temperature_celsius":37.0,
                    "blood_sugar_mmol_l":5.2,"gestational_age_weeks":28.0,"contacts":[12,20,26]},
    "Maternal emergency": {"age":34,"systolic_bp":180,"diastolic_bp":120,"heart_rate":110,"temperature_celsius":38.4,
                    "blood_sugar_mmol_l":9.8,"gestational_age_weeks":34.0,"symptoms":["Severe headache","Blurred vision"],"contacts":[12,20,26,30]},
    "Fetal concern": {"age":30,"systolic_bp":120,"diastolic_bp":80,"heart_rate":82,"temperature_celsius":37.0,
                    "blood_sugar_mmol_l":5.4,"gestational_age_weeks":36.0,"ctg":True,"contacts":[12,20,26,30,34]},
    "Missed checkups": {"age":28,"systolic_bp":118,"diastolic_bp":76,"heart_rate":74,"temperature_celsius":37.0,
                    "blood_sugar_mmol_l":5.2,"gestational_age_weeks":32.0,"contacts":[12,20],"missed":2,"transport":True,"phone":False},
    "Incomplete vitals + danger sign": {"age":25,"gestational_age_weeks":30.0,"symptoms":["Convulsions"],"contacts":[12,20,26]},
}
