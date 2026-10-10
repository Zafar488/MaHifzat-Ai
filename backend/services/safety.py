"""Conservative screening; references in docs/CLINICAL_REFERENCES.md.
Rules require clinical review. Provides escalation advice, never prescriptions.
"""
from datetime import datetime, timezone
from backend.schemas.clinical import ClinicalInput, normalize_symptoms

RULE_VERSION = "2026-10-09.1"


class SafetyService:
    def check_who_red_flags(self, vitals_dict, symptoms=None):
        v = ClinicalInput.model_validate(vitals_dict)
        signs = v.model_dump()
        for symptom in normalize_symptoms(symptoms):
            name = symptom.name.lower().replace("_", " ").strip()
            if name in ("convulsions", "seizure", "seizures"):
                signs["convulsions"] = True
            elif name in ("bleeding", "vaginal bleeding"):
                signs["vaginal_bleeding"] = symptom.severity
            elif name in ("severe headache", "headache"):
                signs["headache_severity"] = "severe" if name == "severe headache" else symptom.severity
            elif name in ("visual changes", "blurred vision", "visual disturbance"):
                signs["visual_disturbance"] = True
            elif name in ("reduced fetal movement", "absent fetal movement"):
                signs["fetal_movement_present"] = False
            elif name in ("epigastric pain", "severe abdominal pain"):
                signs["epigastric_pain"] = True
        rules = []
        if (v.systolic_bp is not None and v.systolic_bp >= 160) or (v.diastolic_bp is not None and v.diastolic_bp >= 110):
            rules.append("severe_hypertension")
        if signs["convulsions"]:
            rules.append("convulsions")
        if signs["vaginal_bleeding"] not in (None, "none"):
            rules.append("vaginal_bleeding")
        if signs["headache_severity"] == "severe" or signs["visual_disturbance"] or signs["epigastric_pain"]:
            rules.append("pre_eclampsia_danger_signs")
        if signs["fetal_movement_present"] is False:
            rules.append("reduced_fetal_movement")
        if signs["consciousness_level"] in ("drowsy", "unconscious"):
            rules.append("altered_consciousness")
        if v.temperature_celsius is not None and v.temperature_celsius >= 38 and signs["vaginal_discharge_foul"]:
            rules.append("fever_with_foul_discharge")
        if v.systolic_bp is not None and v.systolic_bp < 90:
            rules.append("hypotension")
        missing = v.missing_vitals()
        emergency = bool(rules)
        urgent = not emergency and ((v.systolic_bp is not None and v.systolic_bp >= 140) or (v.diastolic_bp is not None and v.diastolic_bp >= 90) or (v.temperature_celsius is not None and v.temperature_celsius >= 38) or (v.heart_rate is not None and v.heart_rate >= 120))
        if emergency:
            triage, rationale, actions = "HIGH_RISK_EMERGENCY", ["Danger signs detected: " + ", ".join(rules)], ["Seek immediate assessment by an emergency maternity service. Do not wait for a model prediction or software review."]
        elif urgent:
            triage, rationale, actions = "URGENT", ["Available measurements require prompt clinical assessment."], ["Contact a qualified maternity clinician promptly."]
        elif missing:
            triage, rationale, actions = "INSUFFICIENT_DATA", ["Missing vitals; clinical status cannot be assessed."], ["Collect missing measurements and seek clinical assessment for any concern."]
        else:
            triage, rationale, actions = "LOW_RISK", ["No configured danger-sign rule triggered in the supplied data; this does not exclude illness."], ["Continue scheduled clinical care and seek help for new symptoms."]
        return {"triage_level": triage, "triggered_rules": rules, "clinical_rationale": rationale, "recommended_actions": actions, "override_ml_scores": emergency, "is_emergency": emergency, "missing_fields": missing, "rule_version": RULE_VERSION, "clinical_review_status": "pending", "timestamp": datetime.now(timezone.utc).isoformat()}

    def is_emergency(self, vitals_dict, symptoms=None):
        return self.check_who_red_flags(vitals_dict, symptoms)["is_emergency"]


_safety_service = SafetyService()


def get_safety_service():
    return _safety_service
