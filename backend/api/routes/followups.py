"""Persistent follow-up task queue. Completing a task records work, not delivery."""
from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from backend.api.deps import get_db
from backend.api.auth import get_current_user, require_role
from backend.api.access import patient_scope, accessible_patient
from backend.db.models import FollowupTask, Patient, CaseRecord, AuditLog
from backend.schemas.auth import UserRole

router = APIRouter(prefix="/followups", tags=["followups"])
def serialize(task):
    return {col.name: getattr(task, col.name) for col in task.__table__.columns}

@router.get("")
async def queue(status: Literal["pending", "completed", "cancelled"] | None = None, db=Depends(get_db), user=Depends(get_current_user)):
    query = select(FollowupTask).where(FollowupTask.patient_id.in_(select(Patient.id).where(patient_scope(user))))
    if status: query = query.where(FollowupTask.status == status)
    tasks = await db.scalars(query.order_by(FollowupTask.due_date, FollowupTask.created_at).limit(500))
    return [serialize(task) for task in tasks]

class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["completed", "cancelled"]
    notes: str = Field(min_length=1, max_length=2000)

@router.put("/{task_id}")
async def resolve(task_id: str, request: TaskUpdate, db=Depends(get_db), user=Depends(require_role(UserRole.LHW, UserRole.CLINICIAN, UserRole.ADMIN))):
    task = await db.get(FollowupTask, task_id)
    if task is None: raise HTTPException(404, "Task not found")
    await accessible_patient(db, user, task.patient_id)
    if task.status != "pending": raise HTTPException(409, "Task already resolved")
    task.status, task.notes, task.completed_by, task.completed_at = request.status, request.notes, user.sub, datetime.utcnow()
    db.add(AuditLog(case_id=task.case_id, agent_name="anc_followup", action="task_" + request.status,
                   input_summary={"actor_id": user.sub}, output_summary={"task_id": task.id}))
    return serialize(task)

async def save_task(db, case, plan):
    if not plan: return
    existing = await db.scalar(select(FollowupTask.id).where(FollowupTask.case_id == case.id))
    if existing: return
    db.add(FollowupTask(case_id=case.id, patient_id=case.patient_id, action=plan["recommended_action"],
           priority=plan["priority"], due_date=plan["task_due_date"], details=plan))
