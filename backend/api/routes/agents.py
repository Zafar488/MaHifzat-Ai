"""Agent orchestration routes — run full workflow or individual nodes."""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.api.auth import get_current_user, require_role
from backend.agents.orchestrator import run_single_node, run_workflow
from backend.schemas.auth import TokenPayload, UserRole

router = APIRouter(prefix="/agents", tags=["agents"])

# ---------------------------------------------------------------------------
# Node metadata (static descriptions for the /status endpoint)
# ---------------------------------------------------------------------------

_NODE_DESCRIPTIONS: Dict[str, str] = {
    "patient_intake": "Validate and normalize incoming patient data",
    "data_quality": "Run data quality checks (missing values, outliers)",
    "clinical_risk": "MaternalGuard + GestationInsight risk prediction",
    "fetal_monitoring": "FetalWatch + PretermGuard CTG analysis",
    "anc_followup": "CareReach ANC missed-visit risk scoring",
    "smart_referral": "Rank nearby facilities and generate referral",
    "communication": "Send SMS / WhatsApp alerts and reminders",
    "clinician_review": "Summarise case for clinician decision",
    "reporting": "Generate structured clinical report",
}


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class WorkflowRequest(BaseModel):
    """Initial state payload for running the full workflow."""
    patient_id: str = Field(..., description="Patient identifier")
    case_id: str = Field(..., description="Case / encounter identifier")
    language: str = Field("ur", description="Preferred language (en, ur, ps, sk)")
    channel: str = Field("app", description="Communication channel")
    vitals: Dict[str, Any] = Field(default_factory=dict)
    symptoms: List[Any] = Field(default_factory=list)
    demographics: Dict[str, Any] = Field(default_factory=dict)
    ctg_data: Dict[str, Any] | None = None


class NodeInvokeRequest(BaseModel):
    """State dict to pass to a single agent node."""
    state: Dict[str, Any] = Field(default_factory=dict)


class NodeInfo(BaseModel):
    name: str
    description: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/run")
async def run_full_workflow(
    request: WorkflowRequest,
    current_user: TokenPayload = Depends(require_role(UserRole.CLINICIAN, UserRole.ADMIN)),
):
    """
    Run the full multi-agent orchestration workflow.
    Requires clinician or admin role.
    """
    initial_state = request.model_dump()
    try:
        result = await run_workflow(initial_state)
        return {"status": "completed", "result": _safe_serialize(result)}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(exc)}",
        )


@router.get("/status", response_model=List[NodeInfo])
async def list_agent_nodes(
    current_user: TokenPayload = Depends(get_current_user),
):
    """Return a list of all agent nodes and their descriptions."""
    return [NodeInfo(name=name, description=desc) for name, desc in _NODE_DESCRIPTIONS.items()]


@router.post("/{node_name}/invoke")
async def invoke_single_node(
    node_name: str,
    request: NodeInvokeRequest,
    current_user: TokenPayload = Depends(require_role(UserRole.CLINICIAN, UserRole.ADMIN)),
):
    """
    Run a single agent node by name (useful for testing/debugging).
    Requires clinician or admin role.
    """
    if node_name not in _NODE_DESCRIPTIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown node '{node_name}'. Available: {list(_NODE_DESCRIPTIONS.keys())}",
        )
    try:
        result = await run_single_node(node_name, request.state)
        return {"node": node_name, "status": "completed", "result": _safe_serialize(result)}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Node '{node_name}' execution failed: {str(exc)}",
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_serialize(obj: Any) -> Any:
    """Convert LangGraph state dict to JSON-safe format (strip non-serializable keys)."""
    if isinstance(obj, dict):
        return {k: _safe_serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_safe_serialize(item) for item in obj]
    # Fall back to str for non-serializable types
    try:
        import json
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        return str(obj)
