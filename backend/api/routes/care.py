"""Patient self-assessment uses the same nine-node workflow with ownership enforced."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from backend.api.auth import get_current_user
from backend.api.deps import get_db,get_model_registry,get_safety_service
from backend.api.routes.agents import run_full_workflow
from backend.db.models import PatientAccess
from backend.schemas.auth import UserRole
from backend.schemas.assessment import WorkflowRequest

router=APIRouter(prefix="/care",tags=["personal care"])

@router.post("/assess")
async def self_assess(request:WorkflowRequest,db=Depends(get_db),user=Depends(get_current_user),
                      registry=Depends(get_model_registry),safety=Depends(get_safety_service)):
    if user.role!=UserRole.PATIENT:
        raise HTTPException(403,"Patient account required; staff use the clinical workflow.")
    owned=await db.scalar(select(PatientAccess.patient_id).where(PatientAccess.patient_id==request.patient_id,
              PatientAccess.user_id==user.sub,PatientAccess.is_owner.is_(True)))
    if not owned: raise HTTPException(404,"Personal patient profile not found")
    if request.provenance=="demo": raise HTTPException(422,"Personal assessments must use actual reported or measured observations")
    return await run_full_workflow(request,db,user,registry,safety)
