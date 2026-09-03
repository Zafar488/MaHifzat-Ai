"""Audit log routes — admin-only access to system audit trail."""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user, require_role
from backend.api.deps import get_db
from backend.db.repositories import AuditRepo
from backend.schemas.auth import TokenPayload, UserRole

router = APIRouter(prefix="/audit", tags=["audit"])


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
    current_user: TokenPayload = Depends(require_role(UserRole.ADMIN)),
):
    """
    List audit logs with optional filtering and pagination.
    Requires admin role.
    """
    repo = AuditRepo(db)

    try:
        # Fetch a broad recent window then filter in Python
        # (Full SQL filtering can be added when needed)
        logs = await repo.get_recent(limit=limit + skip)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit logs: {str(exc)}",
        )

    # Apply optional filters
    if agent_name:
        logs = [log for log in logs if log.agent_name == agent_name]

    if patient_id:
        # AuditLog has case_id; also check if model has patient_id attr
        logs = [
            log for log in logs
            if (getattr(log, "patient_id", None) == patient_id or log.case_id == patient_id)
        ]

    if date_from:
        logs = [log for log in logs if log.timestamp >= date_from]

    if date_to:
        logs = [log for log in logs if log.timestamp <= date_to]

    # Apply pagination after filtering
    paginated = logs[skip: skip + limit]

    return {
        "total": len(logs),
        "skip": skip,
        "limit": limit,
        "logs": [
            {
                "id": log.id,
                "agent_name": log.agent_name,
                "action": log.action,
                "case_id": log.case_id,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                **{
                    k: getattr(log, k, None)
                    for k in ("patient_id", "details", "severity")
                    if hasattr(log, k)
                },
            }
            for log in paginated
        ],
    }
