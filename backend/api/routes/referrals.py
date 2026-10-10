"""Scoped referrals with verified parent existence and explicit transitions."""
from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.auth import get_current_user, require_role
from backend.api.access import accessible_patient, patient_scope
from backend.api.deps import get_db
from backend.schemas.auth import UserRole
from backend.db.models import Referral, Patient, CaseRecord, AuditLog

router = APIRouter(prefix="/referrals", tags=["referrals"])
Urgency = Literal["routine", "urgent", "emergency"]
ReferralStatus = Literal["pending", "accepted", "in_transit", "completed", "cancelled"]
TRANSITIONS = {"pending": {"accepted", "cancelled"}, "accepted": {"in_transit", "completed", "cancelled"}, "in_transit": {"completed", "cancelled"}, "completed": set(), "cancelled": set()}


class ReferralCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    patient_id: str
    case_id: str | None = None
    facility_name: str = Field(min_length=1, max_length=200)
    facility_type: str | None = None
    facility_lat: float | None = Field(None, ge=-90, le=90)
    facility_lon: float | None = Field(None, ge=-180, le=180)
    distance_km: float | None = Field(None, ge=0)
    travel_time_min: float | None = Field(None, ge=0)
    urgency_level: Urgency = "routine"


class ReferralStatusUpdate(BaseModel):
    status: ReferralStatus


def serialize(r):
    return {col.name: getattr(r, col.name) for col in r.__table__.columns}


@router.post("", status_code=201)
async def create(payload: ReferralCreate, db: AsyncSession = Depends(get_db), user=Depends(require_role(UserRole.CLINICIAN, UserRole.ADMIN))):
    await accessible_patient(db, user, payload.patient_id)
    if payload.case_id:
        case = await db.get(CaseRecord, payload.case_id)
        if case is None or case.patient_id != payload.patient_id:
            raise HTTPException(404, "Case not found")
        if case.review_status != "approved":
            raise HTTPException(409, "Case must be approved before referral creation")
    referral = Referral(**payload.model_dump())
    db.add(referral)
    await db.flush()
    db.add(AuditLog(case_id=payload.case_id, agent_name="referrals", action="referral_created", input_summary={"actor_id": user.sub}, output_summary={"referral_id": referral.id}))
    return serialize(referral)


@router.get("")
async def list_referrals(urgency: Urgency | None = None, referral_status: ReferralStatus | None = Query(None, alias="status"), skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    query = select(Referral).where(Referral.patient_id.in_(select(Patient.id).where(patient_scope(user))))
    if urgency:
        query = query.where(Referral.urgency_level == urgency)
    if referral_status:
        query = query.where(Referral.status == referral_status)
    rows = await db.scalars(query.order_by(Referral.created_at.desc()).offset(skip).limit(limit))
    return [serialize(r) for r in rows]


async def checked(db, user, referral_id):
    r = await db.get(Referral, referral_id)
    if r is None:
        raise HTTPException(404, "Referral not found")
    await accessible_patient(db, user, r.patient_id)
    return r


@router.get("/{referral_id}")
async def detail(referral_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return serialize(await checked(db, user, referral_id))


@router.put("/{referral_id}/status")
async def transition(referral_id: str, payload: ReferralStatusUpdate, db: AsyncSession = Depends(get_db), user=Depends(require_role(UserRole.CLINICIAN, UserRole.ADMIN, UserRole.LHW))):
    r = await checked(db, user, referral_id)
    if payload.status != r.status and payload.status not in TRANSITIONS.get(r.status, set()):
        raise HTTPException(409, "Referral transition is not allowed")
    if r.status != payload.status:
        r.status = payload.status
        if r.status == "completed":
            r.completed_at = datetime.utcnow()
        db.add(AuditLog(case_id=r.case_id, agent_name="referrals", action="referral_status_changed", input_summary={"actor_id": user.sub}, output_summary={"referral_id": r.id, "status": r.status}))
    await db.flush()
    return serialize(r)
