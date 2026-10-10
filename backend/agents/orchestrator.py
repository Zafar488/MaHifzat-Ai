"""Safety-first LangGraph routing; durable execution is handled by case API."""
from datetime import datetime, timezone
from langgraph.graph import StateGraph, END
from backend.schemas.state import AgentState
from backend.schemas.clinical import ClinicalInput, normalize_symptoms
from backend.agents.nodes import patient_intake, clinical_risk, fetal_monitoring, anc_followup, smart_referral, communication, clinician_review, data_quality, reporting

NODES = {name: fn for name, fn in locals().copy().items() if name in ("patient_intake", "clinical_risk", "fetal_monitoring", "anc_followup", "smart_referral", "communication", "clinician_review", "data_quality", "reporting")}


def guarded(name):
    async def invoke(state):
        try:
            return await NODES[name](state)
        except Exception:
            # Do not persist exception strings containing clinical input or credentials.
            return {"errors": [{"agent": name, "error": "node_failed"}], "current_step": name + "_failed", "audit_trail": [{"agent": name, "action": "node_failed", "timestamp": datetime.now(timezone.utc).isoformat()}]}
    return invoke


def route_after_clinical_risk(state):
    return END if state.get("errors") else "patient_intake"


def route_after_intake(state):
    if state.get("errors"):
        return END
    return "data_quality"


def route_after_data_quality(state):
    if state.get("errors"):
        return END
    return "fetal_monitoring"


def route_after_fetal(state):
    return END if state.get("errors") else "anc_followup"


graph = StateGraph(AgentState)
for name in NODES:
    graph.add_node(name, guarded(name))
# Danger-sign triage is performed even when intake is incomplete.
graph.set_entry_point("clinical_risk")
graph.add_conditional_edges("clinical_risk", route_after_clinical_risk, {END: END, "patient_intake": "patient_intake"})
graph.add_conditional_edges("patient_intake", route_after_intake, {END: END, "data_quality": "data_quality"})
graph.add_conditional_edges("data_quality", route_after_data_quality, {END: END, "fetal_monitoring": "fetal_monitoring", "anc_followup": "anc_followup"})
graph.add_conditional_edges("fetal_monitoring", route_after_fetal, {END: END, "anc_followup": "anc_followup"})
for source, target in [("anc_followup", "smart_referral"), ("smart_referral", "clinician_review"), ("clinician_review", "communication"), ("communication", "reporting")]:
    graph.add_conditional_edges(source, lambda state, target=target: END if state.get("errors") else target, {END: END, target: target})
graph.add_edge("reporting", END)
workflow = graph.compile()


async def run_workflow(initial_state):
    # Reject malformed inputs before graph execution; no false completed status.
    ClinicalInput.model_validate(initial_state.get("vitals") or {})
    normalize_symptoms(initial_state.get("symptoms"))
    from backend.schemas.assessment import AssessmentInput
    from backend.schemas.care import FollowupContext, PatientLocation
    AssessmentInput.ctg_numeric(initial_state.get("ctg_data"))
    AssessmentInput.ctg_contract(initial_state.get("ctg_data"))
    FollowupContext.model_validate(initial_state.get("followup") or {})
    from backend.schemas.encounter import EncounterContext
    EncounterContext.model_validate(initial_state.get("encounter") or {})
    if initial_state.get("location"):
        PatientLocation.model_validate(initial_state["location"])
    from backend.schemas.encounter import merge_movement_observation
    initial_state={**initial_state,"vitals":merge_movement_observation(initial_state.get("vitals") or {},initial_state.get("encounter") or {})}
    result = await workflow.ainvoke(initial_state)
    maternal = (result.get("clinical_risk_result") or {}).get("maternal_risk", {})
    fetal = result.get("fetal_result") or {}
    incomplete = not result.get("intake_complete") or maternal.get("status") in ("unavailable", "insufficient_data", "error") or fetal.get("status") in ("unavailable", "insufficient_data", "error")
    result["status"] = "failed" if result.get("errors") else "incomplete" if incomplete else "pending_review"
    return result


async def run_single_node(node_name, state):
    if node_name not in NODES:
        raise ValueError("Unknown node")
    ClinicalInput.model_validate(state.get("vitals") or {})
    return await guarded(node_name)(state)
