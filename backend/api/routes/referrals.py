"""Referral management routes."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user
from backend.api.deps import get_db
from backend.db.repositories import ReferralRepo
from backend.schemas.auth import TokenPayload

router = APIRouter(prefix="/referrals", tags=["referrals"])


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class ReferralCreate(BaseModel):
    patient_id: str
    case_id: Optional[str] = None
    facility_name: Optional[str] = None
    facility_type: Optional[str] = None
    facility_lat: Optional[float] = None
    facility_lon: Optional[float] = None
    distance_km: Optional[float] = None
    travel_time_min: Optional[float] = None
    urgency_level: str = "routine"  # routine, urgent, emergency


class ReferralStatusUpdate(BaseModel):
    status: str  # pending, accepted, in_transit, completed, cancelled


def _referral_to_dict(r) -> dict:
    return {
        "id": r.id,
        "patient_id": r.patient_id,
        "case_id": r.case_id,
        "facility_name": r.facility_name,
        "facility_type": r.facility_type,
        "facility_lat": r.facility_lat,
        "facility_lon": r.facility_lon,
        "distance_km": r.distance_km,
        "travel_time_min": r.travel_time_min,
        "urgency_level": r.urgency_level,
        "status": r.status,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_referral(
    payload: ReferralCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Create a new referral manually."""
    repo = ReferralRepo(db)
    referral = await repo.create(payload.model_dump())
    return _referral_to_dict(referral)


@router.get("")
async def list_referrals(
    urgency: Optional[str] = Query(None, description="Filter by urgency level"),
    referral_status: Optional[str] = Query(None, alias="status", description="Filter by status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """List referrals with optional filters and pagination."""
    from sqlalchemy import select, desc
    from backend.db.models import Referral

    query = select(Referral)
    if urgency:
        query = query.where(Referral.urgency_level == urgency)
    if referral_status:
        query = query.where(Referral.status == referral_status)
    query = query.order_by(desc(Referral.created_at)).limit(limit).offset(skip)

    result = await db.execute(query)
    referrals = list(result.scalars().all())
    return [_referral_to_dict(r) for r in referrals]


@router.get("/{referral_id}")
async def get_referral(
    referral_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Get a referral by ID."""
    repo = ReferralRepo(db)
    referral = await repo.get_by_id(referral_id)
    if referral is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found")
    return _referral_to_dict(referral)


@router.put("/{referral_id}/status")
async def update_referral_status(
    referral_id: str,
    payload: ReferralStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Update the status of a referral."""
    repo = ReferralRepo(db)
    referral = await repo.get_by_id(referral_id)
    if referral is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found")
    await repo.update_status(referral_id, payload.status)
    updated = await repo.get_by_id(referral_id)
    return _referral_to_dict(updated)
