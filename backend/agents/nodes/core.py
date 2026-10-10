"""Auditable workflow nodes using shared clinical, referral and follow-up services."""
from datetime import datetime, timezone
from backend.schemas.clinical import ClinicalInput, normalize_symptoms
from backend.services.inference import get_model_registry
from backend.services.safety import SafetyService
from backend.services.followup import plan_followup
from backend.services.referral_planner import plan_referral, effective_urgency
from backend.services.reporting import build_handover

def output(node, **updates):
    return {**updates, "current_step": node + "_complete", "audit_trail": [{"agent": node, "action": node + "_evaluated", "timestamp": datetime.now(timezone.utc).isoformat()}]}

def urgency(state):
    clinical = state.get("clinical_risk_result") or {}
    return effective_urgency(clinical.get("who_red_flags") or {}, clinical.get("maternal_risk"), state.get("fetal_result"))

async def patient_intake(state):
    v = ClinicalInput.model_validate(state.get("vitals") or {})
    missing = v.missing_vitals()
    return output("patient_intake", vitals=v.model_dump(exclude_none=True), symptoms=[s.model_dump() for s in normalize_symptoms(state.get("symptoms"))], intake_complete=not missing, missing_fields=missing, followup_questions=["Please provide measured " + key.replace("_", " ") for key in missing])

async def clinical_risk(state):
    vitals = dict(state.get("vitals") or {})
    if vitals.get("age") is None and (state.get("demographics") or {}).get("age"):
        vitals["age"] = state["demographics"]["age"]
    safety = SafetyService().check_who_red_flags(vitals, state.get("symptoms"))
    maternal = get_model_registry().predict_maternal_risk(vitals)
    if safety["is_emergency"]:
        maternal["safety_override"] = True
        maternal["safety_override_reason"] = "who_red_flags_emergency"
    result = {"maternal_risk": maternal, "gestational_risk": get_model_registry().predict_gestational_complication({}), "who_red_flags": safety, "is_emergency": safety["is_emergency"], "risk_summary": "; ".join(safety["clinical_rationale"]), "llm_generated": False}
    if maternal["status"] == "error":
        return output("clinical_risk", clinical_risk_result=result, emergency=safety["is_emergency"], errors=[{"agent": "clinical_risk", "error": "model_inference_failed"}])
    return output("clinical_risk", clinical_risk_result=result, emergency=safety["is_emergency"])

async def data_quality(state):
    v = ClinicalInput.model_validate(state.get("vitals") or {})
    return output("data_quality", data_quality_result={"missing_fields": v.missing_vitals(), "status": "insufficient_data" if v.missing_vitals() else "validated_input"})

async def fetal_monitoring(state):
    features = state.get("ctg_data")
    if features is None:
        return output("fetal_monitoring", fetal_result={"fetal_status": "not_assessed", "status": "not_assessed", "reason": "No measured CTG features", "escalate": False})
    prediction = get_model_registry().predict_fetal_health(features)
    status = prediction["fetal_status"].lower()
    updates = {"fetal_result": {**prediction, "fetal_confidence": None, "fetal_model_available": prediction["model_available"], "preterm_risk": "disabled", "escalate": status in ("suspect", "suspicious", "pathological")}}
    if status == "pathological":
        updates["emergency"] = True
    if prediction["status"] == "error":
        updates["errors"] = [{"agent": "fetal_monitoring", "error": "model_inference_failed"}]
    return output("fetal_monitoring", **updates)

async def anc_followup(state):
    return output("anc_followup", anc_result=plan_followup(state.get("followup"), state.get("vitals"), urgency(state)))

async def smart_referral(state):
    return output("smart_referral", referral_result=await plan_referral(state.get("location"), urgency(state),
                    state.get("fetal_result"), demo=state.get("provenance") == "demo"))

async def clinician_review(state):
    from backend.services.ai_assistant import explain_case
    from backend.services.case_research import research_for_case
    research=research_for_case(state)
    state={**state,"research_results":research}
    summary=build_handover(state)
    summary["ai_assistance"]=await explain_case(state)
    return output("clinician_review", clinician_result=summary, research_results=research)

async def communication(state):
    anc = state.get("anc_result") or {}
    action = anc.get("recommended_action", "schedule_contact")
    draft = f"Please contact your maternity care team. Follow-up action: {action.replace('_', ' ')}. Appointment: {anc.get('next_appointment_date') or 'please arrange with your clinician'}."
    if state.get("emergency"):
        draft = "Danger signs detected. Seek immediate emergency maternity assessment. Do not wait for a reminder or software review."
    return output("communication", communication_result={"status": "not_sent", "messages_sent": 0, "all_delivered": False,
                  "draft_message": draft, "recommended_channel": "health_worker_visit" if action == "home_visit" else "call" if action == "call" else "app",
                  "reason": "Draft prepared; no external message sent. Reviewed explicit action and provider required."})

async def reporting(state):
    summary = (state.get("clinician_result") or build_handover(state))["case_summary_text"]
    from backend.services.bilingual_reports import build_two_reports
    return output("reporting", reporting_result={"reports":build_two_reports(state), "narrative": summary, "clinical_validation": "not established", "review_status": "pending", "llm_generated": False})
