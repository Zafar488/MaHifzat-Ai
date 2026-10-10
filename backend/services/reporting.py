"""Deterministic handover preserves measurements, provenance and missing data."""
import json
from backend.schemas.clinical import ClinicalInput

def recommended_care_actions(urgency, safety):
    if urgency == "emergency" and not safety.get("is_emergency"):
        return ["Seek immediate emergency maternity assessment for the fetal concern. Do not wait for a routine appointment or software review."]
    if urgency == "urgent" and safety.get("triage_level") != "URGENT":
        return ["Arrange prompt maternity clinician assessment for the identified concern."]
    return safety.get("recommended_actions", [])

def build_handover(state):
    v = ClinicalInput.model_validate(state.get("vitals") or {})
    clinical = state.get("clinical_risk_result") or {}
    safety = clinical.get("who_red_flags") or {}
    maternal = clinical.get("maternal_risk") or {}
    fetal = state.get("fetal_result") or {}
    anc = state.get("anc_result") or {}
    referral = state.get("referral_result") or {}
    facility = referral.get("selected_facility") or {}
    missing = list(v.missing_vitals())
    if v.age is None: missing.append("age")
    if v.blood_sugar_mmol_l is None: missing.append("blood_sugar_mmol_l")
    observations = []
    for key, label, unit in [("age", "Age", "years"), ("gestational_age_weeks", "Gestation", "weeks"),
          ("systolic_bp", "Systolic BP", "mmHg"), ("diastolic_bp", "Diastolic BP", "mmHg"),
          ("heart_rate", "Heart rate", "bpm"), ("temperature_celsius", "Temperature", "C"),
          ("blood_sugar_mmol_l", "Blood glucose", "mmol/L")]:
        value = getattr(v, key)
        observations.append(f"{label}: {value:g} {unit}" if value is not None else f"{label}: not recorded")
    symptoms = state.get("symptoms") or []
    symptoms_text = "; ".join(f"{s['name']} ({s.get('severity', 'unspecified')})" if isinstance(s, dict) else str(s) for s in symptoms) or "No symptoms reported"
    urgency = referral.get("urgency_level", "emergency" if state.get("emergency") else "routine")
    lines = [f"MaaHifazat clinical handover | Case: {state.get('case_id', 'unsaved')}",
        f"Patient ID: {state.get('patient_id', 'unknown')} | Provenance: {state.get('provenance', 'unspecified')}",
        f"Attention: {urgency.upper()} | Maternal rule triage: {safety.get('triage_level', 'not assessed')}",
        "Observations: " + "; ".join(observations), "Reported symptoms: " + symptoms_text,
        "Danger signs: " + (", ".join(safety.get("triggered_rules", [])) or "None of the configured rules triggered"),
        f"Experimental maternal model: {maternal.get('risk_level', 'unknown')} ({maternal.get('status', 'not assessed')})",
        f"Experimental fetal model: {fetal.get('fetal_status', 'not_assessed')} ({fetal.get('status', 'no measured CTG')})",
        "Missing measurements: " + (", ".join(missing) or "None of the required maternal measurements"),
        f"Referral candidate: {facility.get('name', 'none')} | {referral.get('status', 'not planned')}"]
    if facility:
        lines.append(f"Distance: {facility.get('distance_km')} km ({facility.get('distance_kind')}); road ETA: {facility.get('travel_time_minutes') if facility.get('travel_time_minutes') is not None else 'unavailable'} minutes")
        lines.append("Facility services/acceptance must be confirmed. " + ("SIMULATED FACILITY." if facility.get("simulated") else "Directory source: " + facility.get("source", "unknown")))
    if facility and not facility.get("capabilities_verified", False):
        lines.append("Service verification: unconfirmed map tags only; maternity/emergency/NICU and acceptance require direct confirmation.")
    lines.extend([f"ANC: {anc.get('priority', 'unknown')} priority; action: {anc.get('recommended_action', 'schedule contact')}; next appointment: {anc.get('next_appointment_date') or 'clinician to schedule'}",
        "Next actions: " + " ".join(recommended_care_actions(urgency, safety)),
        "Review: pending qualified clinician review. Emergency assessment must not wait for software review.",
        "Model evidence: probabilities are uncalibrated; CTG-pattern, no-show and Pima-derived proxy results do not determine clinical care."])
    return {"case_summary_text": "\n".join(lines), "status": "pending_review",
            "requires_immediate_attention": urgency == "emergency", "risk_indicators": safety.get("triggered_rules", []),
            "decision": None, "reviewer": None, "llm_generated": False}
