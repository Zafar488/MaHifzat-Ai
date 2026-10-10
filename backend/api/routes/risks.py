"""Clinical assessment with danger-sign triage, scoped access and idempotency."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.auth import get_current_user
from backend.api.access import accessible_patient
from backend.api.deps import get_db, get_model_registry, get_safety_service
from backend.db.models import CaseRecord
from backend.schemas.assessment import AssessmentInput
from backend.services.cases import reserve_case, persist_assessment, assess

router = APIRouter(prefix="/risks", tags=["risks"])
RiskAssessmentRequest = AssessmentInput


@router.post("/assess")
async def assess_risk(request: AssessmentInput, db: AsyncSession = Depends(get_db), user=Depends(get_current_user), registry=Depends(get_model_registry), safety=Depends(get_safety_service)):
    await accessible_patient(db, user, request.patient_id)
    case, new = await reserve_case(db, request, user)
    if not new and case.state_data.get("assessment"):
        return case.state_data["assessment"]
    response = assess(case.state_data["input"], case.id, registry, safety)
    case.status = response["status"]
    case.state_data = {**case.state_data, "assessment": response}
    await persist_assessment(db, case, response, user)
    from backend.api.routes.followups import save_task
    await save_task(db, case, response["anc_followup"])
    return response


@router.get("/{case_id}")
async def get_risk_assessment(case_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    case = await db.get(CaseRecord, case_id)
    if case is None:
        raise HTTPException(404, "Assessment not found")
    await accessible_patient(db, user, case.patient_id)
    return {**case.state_data.get("assessment", {}), "case_id": case.id, "patient_id": case.patient_id,
            "vitals": case.state_data["input"]["vitals"], "symptoms": case.state_data["input"]["symptoms"],
            "ctg_features": case.state_data["input"]["ctg_features"], "ctg_source": case.state_data["input"]["ctg_source"],
            "provenance": case.state_data["input"]["provenance"], "status": case.status,
            "review_status": case.review_status, "reviewed_by": case.reviewed_by, "reviewed_at": case.reviewed_at}
