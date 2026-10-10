"""Real audit events only; filters and counts applied in SQL before pagination."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.auth import require_role
from backend.api.deps import get_db
from backend.db.models import AuditLog, CaseRecord
from backend.schemas.auth import UserRole

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs")
async def logs(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=500), agent_name: str | None = None, patient_id: str | None = None, date_from: datetime | None = None, date_to: datetime | None = None, db: AsyncSession = Depends(get_db), user=Depends(require_role(UserRole.ADMIN))):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(422, "Date range is reversed")
    query = select(AuditLog)
    if agent_name:
        query = query.where(AuditLog.agent_name == agent_name)
    if patient_id:
        query = query.where(AuditLog.case_id.in_(select(CaseRecord.id).where(CaseRecord.patient_id == patient_id)))
    if date_from:
        query = query.where(AuditLog.timestamp >= date_from.replace(tzinfo=None))
    if date_to:
        query = query.where(AuditLog.timestamp <= date_to.replace(tzinfo=None))
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    rows = await db.scalars(query.order_by(AuditLog.timestamp.desc(), AuditLog.id).offset(skip).limit(limit))
    return {"total": total, "skip": skip, "limit": limit, "logs": [{"id": r.id, "agent_name": r.agent_name, "action": r.action, "case_id": r.case_id, "timestamp": r.timestamp, "details": r.action.replace("_", " "), "severity": "error" if r.error else "info"} for r in rows]}
