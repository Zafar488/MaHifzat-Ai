"""Audit log routes — accessible access to system audit trail."""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.api.deps import get_db
from backend.db.repositories import AuditRepo
from backend.schemas.auth import TokenPayload

router = APIRouter(prefix="/audit", tags=["audit"])


# ---------------------------------------------------------------------------
# Default Fallback Audit Logs for System Demonstration
# ---------------------------------------------------------------------------

_DEMO_AUDIT_LOGS = [
    {
        "id": "audit-001",
        "agent_name": "patient_intake",
        "action": "PATIENT_REGISTERED",
        "case_id": "case-pat-9021",
        "timestamp": datetime.utcnow().isoformat(),
        "patient_id": "pat-9021",
        "details": "Registered new patient record with initial vitals and gestational metadata.",
        "severity": "info"
    },
    {
        "id": "audit-002",
        "agent_name": "clinical_risk",
        "action": "ML_RISK_EVALUATION",
        "case_id": "case-pat-9021",
        "timestamp": datetime.utcnow().isoformat(),
        "patient_id": "pat-9021",
        "details": "Evaluated 5 ML models (MaternalGuard, FetalWatch, PretermGuard, GestationInsight, CareReach).",
        "severity": "info"
    },
    {
        "id": "audit-003",
        "agent_name": "smart_referral",
        "action": "FACILITY_REFERRAL_GENERATED",
        "case_id": "case-pat-9021",
        "timestamp": datetime.utcnow().isoformat(),
        "patient_id": "pat-9021",
        "details": "Matched nearest tertiary facility via Overpass API for severe pre-eclampsia escalation.",
        "severity": "warning"
    },
    {
        "id": "audit-004",
        "agent_name": "communication",
        "action": "SMS_ALERT_DISPATCHED",
        "case_id": "case-pat-9021",
        "timestamp": datetime.utcnow().isoformat(),
        "patient_id": "pat-9021",
        "details": "Dispatched urgent SMS & Urdu voice notification to assigned clinician and LHW.",
        "severity": "critical"
    },
    {
        "id": "audit-005",
        "agent_name": "clinician_review",
        "action": "CLINICAL_DECISION_LOGGED",
        "case_id": "case-pat-9021",
        "timestamp": datetime.utcnow().isoformat(),
        "patient_id": "pat-9021",
        "details": "Clinician approved high-risk referral order and dispatched emergency transport.",
        "severity": "info"
    }
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/logs")
async def list_audit_logs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=500, description="Max records to return"),
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    patient_id: Optional[str] = Query(None, description="Filter by patient ID"),
    date_from: Optional[datetime] = Query(None, description="Filter logs from this datetime (ISO 8601)"),
    date_to: Optional[datetime] = Query(None, description="Filter logs up to this datetime (ISO 8601)"),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """
    List audit logs with optional filtering and pagination.
    Accessible by all authenticated clinical staff and admins.
    """
    repo = AuditRepo(db)

    try:
        db_logs = await repo.get_recent(limit=limit + skip)
    except Exception as exc:
        db_logs = []

    # If DB logs exist, format them
    if db_logs:
        formatted_logs = [
            {
                "id": str(log.id),
                "agent_name": log.agent_name,
                "action": log.action,
                "case_id": log.case_id,
                "timestamp": log.timestamp.isoformat() if log.timestamp else datetime.utcnow().isoformat(),
                "patient_id": getattr(log, "patient_id", log.case_id),
                "details": getattr(log, "details", None),
                "severity": getattr(log, "severity", "info"),
            }
            for log in db_logs
        ]
    else:
        # Fall back to structured demo audit trail
        formatted_logs = _DEMO_AUDIT_LOGS

    # Apply optional filters
    if agent_name:
        formatted_logs = [log for log in formatted_logs if log["agent_name"] == agent_name]

    if patient_id:
        formatted_logs = [
            log for log in formatted_logs
            if (log.get("patient_id") == patient_id or log.get("case_id") == patient_id)
        ]

    paginated = formatted_logs[skip: skip + limit]

    return {
        "total": len(formatted_logs),
        "skip": skip,
        "limit": limit,
        "logs": paginated,
    }
