"""Durable workflow execution, idempotent retries and clinician decisions."""
from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.auth import require_role, get_current_user
from backend.api.access import accessible_patient
from backend.api.deps import get_db, get_model_registry, get_safety_service
from backend.agents.orchestrator import run_workflow, run_single_node, NODES
from backend.schemas.auth import UserRole
from backend.schemas.assessment import WorkflowRequest, AssessmentInput
from backend.schemas.clinical import ClinicalInput
from backend.services.cases import reserve_case, persist_assessment, assess, normalized_input
from backend.db.models import CaseRecord, AgentStateRecord, AuditLog, ClinicalRecord, Referral
from backend.config import settings

router = APIRouter(prefix="/agents", tags=["agents"])
clinical_roles = require_role(UserRole.CLINICIAN, UserRole.ADMIN)


@router.get("/status")
async def nodes(user=Depends(clinical_roles)):
    return [{"name": name, "description": fn.__doc__ or name.replace("_", " ")} for name, fn in NODES.items()]


@router.post("/run")
async def run_full_workflow(request: WorkflowRequest, db: AsyncSession = Depends(get_db), user=Depends(require_role(UserRole.LHW, UserRole.CLINICIAN, UserRole.ADMIN)), registry=Depends(get_model_registry), safety=Depends(get_safety_service)):
    patient = await accessible_patient(db, user, request.patient_id)
    existing = await db.get(CaseRecord, request.case_id) if request.case_id else None
    # A case-only request resumes from stored observations; never invents measurements.
    if existing and request.model_fields_set <= {"patient_id", "case_id", "language", "channel"}:
        if existing.patient_id != request.patient_id:
            raise HTTPException(409, "Case belongs to another patient")
        case = existing
    else:
        case, _ = await reserve_case(db, request, user)
    if case.state_data.get("workflow_result"):
        result = case.state_data["workflow_result"]
        return JSONResponse(status_code=500 if result["status"] == "failed" else 200, content={"status": result["status"], "result": result})
    # Atomic claim prevents duplicate runs across processes/workers.
    claimed = await db.execute(update(CaseRecord).where(CaseRecord.id == case.id, CaseRecord.status != "workflow_running", CaseRecord.state_data["workflow_result"].as_string().is_(None)).values(status="workflow_running"))
    if claimed.rowcount != 1:
        raise HTTPException(409, "Workflow is already running")
    intake = case.state_data["input"]
    state = {"patient_id": case.patient_id, "case_id": case.id, "vitals": intake["vitals"], "symptoms": intake["symptoms"], "ctg_data": intake["ctg_features"], "language": request.language, "channel": "app", "audit_trail": [], "errors": [], "messages": []}
    state.update(location=intake.get("location"), followup=intake.get("followup", {}),
                 encounter=intake.get("encounter", {}), patient_context={"name":patient.name,"phone":patient.phone},
                 provenance=intake["provenance"], allow_llm_processing=intake.get("allow_llm_processing",False), demographics={"age": patient.age, "gestational_age_weeks": patient.gestational_age_weeks})
    try:
        result = await run_workflow(state)
    except Exception:
        result = {**state, "status": "failed", "errors": [{"agent": "workflow", "error": "workflow_failed"}]}
    response = case.state_data.get("assessment") or assess(intake, case.id, registry, safety)
    # Fetal concerns are separate from maternal danger-sign triage.
    if (result.get("fetal_result") or {}).get("escalate"):
        response = {**response, "fetal_concern": True}
    if not case.state_data.get("assessment"):
        await persist_assessment(db, case, response, user)
    from backend.api.routes.followups import save_task
    await save_task(db, case, result.get("anc_result"))
    case.status = result["status"]
    case.state_data = {**case.state_data, "assessment": response, "workflow_result": result}
    db.add(AgentStateRecord(case_id=case.id, thread_id=case.id, state_data=result, current_step=result.get("current_step", "failed"), is_complete=False))
    for event in result.get("audit_trail", []):
        db.add(AuditLog(case_id=case.id, agent_name=event["agent"], action=event["action"], output_summary={"status": result["status"]}))
    # Commit failed states too; rollback on a persistence failure.
    await db.commit()
    return JSONResponse(status_code=500 if result["status"] == "failed" else 200, content={"status": result["status"], "result": result})


class ReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["approved", "rejected"]
    notes: str = Field(min_length=1, max_length=2000)
    create_referral: bool = False
    facility_name: str | None = Field(None, min_length=1, max_length=200)
    urgency: Literal["routine", "urgent", "emergency"] = "urgent"


@router.post("/cases/{case_id}/review")
async def review(case_id: str, request: ReviewRequest, db: AsyncSession = Depends(get_db), user=Depends(clinical_roles)):
    case = await db.get(CaseRecord, case_id)
    if case is None:
        raise HTTPException(404, "Case not found")
    await accessible_patient(db, user, case.patient_id)
    if case.status in ("failed", "workflow_running", "running"):
        raise HTTPException(409, "Case requires safe recovery before review")
    if case.review_status != "pending":
        raise HTTPException(409, "Case already reviewed")
    if request.create_referral and (request.decision != "approved" or not request.facility_name):
        raise HTTPException(422, "Referral requires approval and a manually verified facility")
    result = await db.execute(update(CaseRecord).where(CaseRecord.id == case_id, CaseRecord.review_status == "pending").values(review_status=request.decision, reviewed_by=user.sub, reviewed_at=datetime.utcnow(), review_notes=request.notes, status=request.decision))
    if result.rowcount != 1:
        raise HTTPException(409, "Case already reviewed")
    records = await db.scalars(select(ClinicalRecord).where(ClinicalRecord.case_id == case_id))
    for record in records:
        record.clinician_decision, record.clinician_notes = request.decision, request.notes
    referral_id = None
    if request.create_referral:
        referral = Referral(patient_id=case.patient_id, case_id=case_id, facility_name=request.facility_name, urgency_level=request.urgency)
        db.add(referral)
        await db.flush()
        referral_id = referral.id
    db.add(AuditLog(case_id=case_id, agent_name="clinician_review", action=request.decision, input_summary={"actor_id": user.sub}, output_summary={"referral_id": referral_id}))
    await db.flush()
    return {"case_id": case_id, "review_status": request.decision, "reviewed_by": user.sub, "referral_id": referral_id}


@router.post("/cases/{case_id}/resume")
async def resume(case_id: str, db: AsyncSession = Depends(get_db), user=Depends(clinical_roles)):
    case = await db.get(CaseRecord, case_id)
    if case is None:
        raise HTTPException(404, "Case not found")
    await accessible_patient(db, user, case.patient_id)
    if case.review_status != "approved":
        raise HTTPException(409, "Only approved cases can resume")
    # No automatic external effects; reviewed state becomes a durable completed record.
    case.status = "completed"
    state = {**case.state_data.get("workflow_result", {}), "status": "completed", "clinician_result": {**(case.state_data.get("workflow_result", {}).get("clinician_result") or {}), "status": "approved", "reviewer": case.reviewed_by, "reviewed_at": case.reviewed_at.isoformat()}, "communication_result": {**(case.state_data.get("workflow_result", {}).get("communication_result") or {}), "status": "not_sent", "messages_sent": 0}}
    case.state_data = {**case.state_data, "workflow_result": state}
    if not await db.scalar(select(AgentStateRecord.id).where(AgentStateRecord.case_id == case_id, AgentStateRecord.is_complete.is_(True))):
        db.add(AgentStateRecord(case_id=case_id, thread_id=case_id, state_data=state, current_step="review_complete", is_complete=True))
        db.add(AuditLog(case_id=case_id, agent_name="workflow", action="reviewed_case_completed", input_summary={"actor_id": user.sub}))
    return {"status": "completed", "result": state}


class NodeInvokeRequest(BaseModel):
    state: dict = Field(default_factory=dict)


@router.post("/{node_name}/invoke")
async def invoke(node_name: str, request: NodeInvokeRequest, db: AsyncSession = Depends(get_db), user=Depends(require_role(UserRole.ADMIN))):
    if not settings.DEMO_MODE:
        raise HTTPException(403, "Individual node invocation requires explicit development demo mode")
    if node_name not in NODES:
        raise HTTPException(404, "Node not found")
    await accessible_patient(db, user, request.state.get("patient_id", ""))
    try:
        ClinicalInput.model_validate(request.state.get("vitals") or {})
    except ValueError:
        raise HTTPException(422, "Invalid clinical input")
    result = await run_single_node(node_name, request.state)
    return {"node": node_name, "status": "failed" if result.get("errors") else "simulated", "result": result}

@router.get("/cases/{case_id}")
async def saved_case(case_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    case = await db.get(CaseRecord, case_id)
    if case is None:
        raise HTTPException(404, "Case not found")
    await accessible_patient(db, user, case.patient_id)
    return {"case_id": case.id, "status": case.status, "review_status": case.review_status,
            "result": case.state_data.get("workflow_result", {}),
            "reviewed_by": case.reviewed_by, "reviewed_at": case.reviewed_at, "review_notes": case.review_notes}
