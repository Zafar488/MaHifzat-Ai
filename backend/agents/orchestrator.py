"""LangGraph orchestrator — central StateGraph wiring all 9 agent nodes."""

from langgraph.graph import StateGraph, END

from backend.schemas.state import AgentState
from backend.agents.nodes import (
    patient_intake,
    clinical_risk,
    fetal_monitoring,
    anc_followup,
    smart_referral,
    communication,
    clinician_review,
    data_quality,
    reporting,
)

# ---------------------------------------------------------------------------
# Conditional routing functions
# ---------------------------------------------------------------------------

def route_after_intake(state: dict) -> str:
    """Route after patient_intake: END if incomplete, else data_quality."""
    if not state.get("intake_complete", False):
        return END
    return "data_quality"


def route_after_data_quality(state: dict) -> str:
    """After data_quality, move to clinical_risk (sequential parallel-branch)."""
    return "clinical_risk"


def route_after_clinical_risk(state: dict) -> str:
    """Emergency → smart_referral; CTG present → fetal_monitoring; else anc."""
    if state.get("emergency", False):
        return "smart_referral"
    vitals = state.get("vitals") or {}
    if isinstance(vitals, dict) and vitals.get("ctg_data") is not None:
        return "fetal_monitoring"
    return "anc_followup"


def route_after_fetal(state: dict) -> str:
    """Emergency (pathological CTG) → smart_referral; else anc_followup."""
    if state.get("emergency", False):
        return "smart_referral"
    return "anc_followup"


def route_after_clinician(state: dict) -> str:
    """Normal → reporting; emergency → END (skip reporting for speed)."""
    if state.get("emergency", False):
        return END
    return "reporting"


# ---------------------------------------------------------------------------
# Build the StateGraph
# ---------------------------------------------------------------------------

graph = StateGraph(AgentState)

# Add all 9 nodes
graph.add_node("patient_intake", patient_intake)
graph.add_node("data_quality", data_quality)
graph.add_node("clinical_risk", clinical_risk)
graph.add_node("fetal_monitoring", fetal_monitoring)
graph.add_node("anc_followup", anc_followup)
graph.add_node("smart_referral", smart_referral)
graph.add_node("communication", communication)
graph.add_node("clinician_review", clinician_review)
graph.add_node("reporting", reporting)

# Entry point
graph.set_entry_point("patient_intake")

# --- Conditional edges ---

graph.add_conditional_edges(
    "patient_intake",
    route_after_intake,
    {END: END, "data_quality": "data_quality"},
)

graph.add_conditional_edges(
    "data_quality",
    route_after_data_quality,
    {"clinical_risk": "clinical_risk"},
)

graph.add_conditional_edges(
    "clinical_risk",
    route_after_clinical_risk,
    {
        "smart_referral": "smart_referral",
        "fetal_monitoring": "fetal_monitoring",
        "anc_followup": "anc_followup",
    },
)

graph.add_conditional_edges(
    "fetal_monitoring",
    route_after_fetal,
    {"smart_referral": "smart_referral", "anc_followup": "anc_followup"},
)

graph.add_conditional_edges(
    "anc_followup",
    lambda _state: "smart_referral",
    {"smart_referral": "smart_referral"},
)

graph.add_conditional_edges(
    "smart_referral",
    lambda _state: "communication",
    {"communication": "communication"},
)

graph.add_conditional_edges(
    "communication",
    lambda _state: "clinician_review",
    {"clinician_review": "clinician_review"},
)

graph.add_conditional_edges(
    "clinician_review",
    route_after_clinician,
    {END: END, "reporting": "reporting"},
)

graph.add_edge("reporting", END)

# ---------------------------------------------------------------------------
# Compile
# ---------------------------------------------------------------------------

workflow = graph.compile()

# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

async def run_workflow(initial_state: dict) -> dict:
    """Run the full orchestration workflow with given initial state."""
    result = await workflow.ainvoke(initial_state)
    return result


async def run_single_node(node_name: str, state: dict) -> dict:
    """Run a single agent node by name for testing purposes."""
    node_map = {
        "patient_intake": patient_intake,
        "data_quality": data_quality,
        "clinical_risk": clinical_risk,
        "fetal_monitoring": fetal_monitoring,
        "anc_followup": anc_followup,
        "smart_referral": smart_referral,
        "communication": communication,
        "clinician_review": clinician_review,
        "reporting": reporting,
    }
    fn = node_map.get(node_name)
    if fn is None:
        raise ValueError(f"Unknown node: {node_name!r}. Available: {list(node_map)}")
    return await fn(state)
