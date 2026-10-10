"""Patient access is scoped by explicit ownership/assignment on every operation."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.auth import get_current_user, require_role
from backend.api.access import patient_scope, accessible_patient
from backend.api.deps import get_db
from backend.db.models import Patient, PatientAccess, User, ClinicalRecord, AuditLog
from backend.schemas.auth import UserRole
from backend.schemas.patient import PatientCreate, PatientProfile

router = APIRouter(prefix="/patients", tags=["patients"])


def profile(p):
    return {**{key: getattr(p, key) for key in PatientCreate.model_fields}, "patient_id": p.id, "created_at": p.created_at, "updated_at": p.updated_at}


@router.post("", response_model=PatientProfile, status_code=201)
async def create_patient(payload: PatientCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    if user.role == UserRole.PATIENT:
        if await db.scalar(select(PatientAccess.patient_id).where(PatientAccess.user_id == user.sub, PatientAccess.is_owner.is_(True))):
            raise HTTPException(409, "A patient account may register one personal profile")
    patient = Patient(**payload.model_dump())
    db.add(patient)
    await db.flush()
    db.add(PatientAccess(patient_id=patient.id, user_id=user.sub, is_owner=user.role == UserRole.PATIENT))
    db.add(AuditLog(agent_name="patients", action="patient_registered", input_summary={"actor_id": user.sub}, output_summary={"patient_id": patient.id}))
    return profile(patient)


@router.get("", response_model=list[PatientProfile])
async def list_patients(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), search: str = Query("", max_length=100), db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    query = select(Patient).where(patient_scope(user), Patient.is_active.is_(True))
    if search:
        query = query.where(Patient.name.ilike("%" + search.replace("%", "\\%").replace("_", "\\_") + "%", escape="\\"))
    rows = await db.scalars(query.order_by(Patient.created_at.desc(), Patient.id).offset(skip).limit(limit))
    return [profile(p) for p in rows]


@router.get("/{patient_id}", response_model=PatientProfile)
async def get_patient(patient_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return profile(await accessible_patient(db, user, patient_id))


@router.put("/{patient_id}", response_model=PatientProfile)
async def update_patient(patient_id: str, payload: PatientCreate, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    patient = await accessible_patient(db, user, patient_id)
    for key, value in payload.model_dump().items():
        setattr(patient, key, value)
    db.add(AuditLog(agent_name="patients", action="patient_updated", input_summary={"actor_id": user.sub}, output_summary={"patient_id": patient_id}))
    await db.flush()
    return profile(patient)


@router.get("/{patient_id}/assessments")
async def history(patient_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    await accessible_patient(db, user, patient_id)
    rows = await db.scalars(select(ClinicalRecord).where(ClinicalRecord.patient_id == patient_id).order_by(ClinicalRecord.created_at.desc()))
    return [{"case_id": r.case_id, "maternal_risk_level": r.maternal_risk_level, "triage_level": r.triage_level, "is_emergency": r.is_emergency, "created_at": r.created_at} for r in rows]


class Assignment(BaseModel):
    user_id: str
    is_owner: bool = False


@router.post("/{patient_id}/assign", status_code=201)
async def assign(patient_id: str, payload: Assignment, db: AsyncSession = Depends(get_db), actor=Depends(require_role(UserRole.ADMIN))):
    await accessible_patient(db, actor, patient_id)
    target = await db.get(User, payload.user_id)
    if target is None or not target.is_active:
        raise HTTPException(404, "User not found")
    if payload.is_owner != (target.role == "patient"):
        raise HTTPException(422, "Patient roles require ownership; staff roles require assignment")
    if payload.is_owner:
        owner = await db.scalar(select(PatientAccess).where(PatientAccess.user_id == target.id, PatientAccess.is_owner.is_(True)))
        if owner and owner.patient_id != patient_id:
            raise HTTPException(409, "Patient account already owns a different profile")
    entry = await db.get(PatientAccess, (patient_id, target.id))
    if entry is None:
        db.add(PatientAccess(patient_id=patient_id, user_id=target.id, is_owner=payload.is_owner))
    db.add(AuditLog(agent_name="patients", action="patient_assigned", input_summary={"actor_id": actor.sub}, output_summary={"patient_id": patient_id, "user_id": target.id}))
    return {"patient_id": patient_id, "user_id": target.id}


@router.delete("/{patient_id}/assign/{user_id}")
async def unassign(patient_id: str, user_id: str, db: AsyncSession = Depends(get_db), actor=Depends(require_role(UserRole.ADMIN))):
    await accessible_patient(db, actor, patient_id)
    entry = await db.get(PatientAccess, (patient_id, user_id))
    if entry:
        await db.delete(entry)
        db.add(AuditLog(agent_name="patients", action="patient_unassigned", input_summary={"actor_id": actor.sub}, output_summary={"patient_id": patient_id, "user_id": user_id}))
    return {"removed": entry is not None}
