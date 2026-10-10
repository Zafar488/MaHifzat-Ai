"""Durable app alerts, scoped acknowledgment and honest messaging."""
from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.auth import get_current_user, require_role
from backend.api.access import patient_scope, accessible_patient
from backend.api.deps import get_db
from backend.db.models import Alert, Patient, CaseRecord, AuditLog
from backend.schemas.auth import UserRole
from backend.integrations.messaging_client import MessagingClient

router = APIRouter(prefix="/alerts", tags=["alerts"])


def serialize(a):
    return {"alert_id": a.id, "patient_id": a.patient_id, "case_id": a.case_id, "type": a.kind, "message": a.message, "channel": a.channel, "status": a.provider_status, "message_id": a.message_id, "created_at": a.created_at, "acknowledged": a.acknowledged_at is not None, "acknowledged_at": a.acknowledged_at}


async def checked(db, user, alert_id):
    alert = await db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(404, "Alert not found")
    await accessible_patient(db, user, alert.patient_id)
    return alert


@router.get("")
async def list_alerts(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500), db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    rows = await db.scalars(select(Alert).where(Alert.patient_id.in_(select(Patient.id).where(patient_scope(user)))).order_by(Alert.created_at.desc()).offset(skip).limit(limit))
    return [serialize(a) for a in rows]


@router.get("/{alert_id}/status")
@router.get("/{alert_id}")
async def detail(alert_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return serialize(await checked(db, user, alert_id))


@router.post("/{alert_id}/acknowledge")
async def acknowledge(alert_id: str, db: AsyncSession = Depends(get_db), user=Depends(require_role(UserRole.ADMIN, UserRole.CLINICIAN, UserRole.LHW))):
    alert = await checked(db, user, alert_id)
    if alert.acknowledged_at is None:
        alert.acknowledged_at, alert.acknowledged_by = datetime.utcnow(), user.sub
        db.add(AuditLog(case_id=alert.case_id, agent_name="alerts", action="alert_acknowledged", input_summary={"actor_id": user.sub}, output_summary={"alert_id": alert.id}))
    return serialize(alert)


class SendAlertRequest(BaseModel):
    patient_id: str
    case_id: str
    message: str = Field(min_length=1, max_length=1000)
    channel: Literal["sms", "whatsapp"] = "sms"


@router.post("/send", status_code=201)
async def send(request: SendAlertRequest, db: AsyncSession = Depends(get_db), user=Depends(require_role(UserRole.ADMIN, UserRole.CLINICIAN))):
    patient = await accessible_patient(db, user, request.patient_id)
    case = await db.get(CaseRecord, request.case_id)
    if case is None or case.patient_id != patient.id:
        raise HTTPException(404, "Case not found")
    if case.review_status != "approved":
        raise HTTPException(409, "Case approval required")
    if not patient.phone:
        raise HTTPException(422, "No verified recipient phone")
    client = MessagingClient()
    result = await (client.send_sms(patient.phone, request.message) if request.channel == "sms" else client.send_whatsapp(patient.phone, request.message))
    if result["status"] == "unavailable":
        raise HTTPException(503, "Messaging provider unavailable; no message sent")
    alert = Alert(patient_id=patient.id, case_id=case.id, message=request.message, channel=request.channel, kind="simulated_message", provider_status=result["status"], message_id=result["message_id"])
    db.add(alert)
    await db.flush()
    db.add(AuditLog(case_id=case.id, agent_name="alerts", action="message_simulated", input_summary={"actor_id": user.sub}, output_summary={"alert_id": alert.id, "status": "simulated"}))
    return serialize(alert)
