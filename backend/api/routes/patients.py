"""Patient CRUD routes."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.auth import get_current_user, require_role
from backend.api.deps import get_db
from backend.db.repositories import PatientRepo
from backend.schemas.auth import TokenPayload, UserRole
from backend.schemas.patient import PatientCreate, PatientProfile

router = APIRouter(prefix="/patients", tags=["patients"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _patient_to_profile(p) -> dict:
    """Convert an ORM Patient instance to a PatientProfile-compatible dict."""
    return {
        "patient_id": p.id,
        "name": p.name,
        "age": p.age,
        "gender": p.gender or "female",
        "phone": p.phone,
        "location": p.location,
        "gestational_age_weeks": p.gestational_age_weeks,
        "parity": p.parity,
        "language": p.language or "ur",
        "channel": p.channel or "app",
        "created_at": p.created_at,
        "updated_at": p.updated_at,
    }


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", response_model=PatientProfile, status_code=status.HTTP_201_CREATED)
async def create_patient(
    payload: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Create a new patient record."""
    repo = PatientRepo(db)
    patient = await repo.create(payload.model_dump())
    return _patient_to_profile(patient)


@router.get("", response_model=List[PatientProfile])
async def list_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """List patients with pagination."""
    repo = PatientRepo(db)
    patients = await repo.list_all(limit=limit, offset=skip)
    return [_patient_to_profile(p) for p in patients]


@router.get("/{patient_id}", response_model=PatientProfile)
async def get_patient(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Get a patient by ID."""
    repo = PatientRepo(db)
    patient = await repo.get_by_id(patient_id)
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    return _patient_to_profile(patient)


@router.put("/{patient_id}", response_model=PatientProfile)
async def update_patient(
    patient_id: str,
    payload: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: TokenPayload = Depends(get_current_user),
):
    """Update an existing patient."""
    repo = PatientRepo(db)
    existing = await repo.get_by_id(patient_id)
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found")
    patient = await repo.update(patient_id, payload.model_dump())
    return _patient_to_profile(patient)
