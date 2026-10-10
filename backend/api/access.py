"""Server-side object permissions: admin or explicit owner/assignment."""
from fastapi import HTTPException
from sqlalchemy import select
from backend.db.models import Patient, PatientAccess
from backend.schemas.auth import UserRole


def patient_scope(user):
    if user.role == UserRole.ADMIN:
        return True
    return Patient.id.in_(select(PatientAccess.patient_id).where(PatientAccess.user_id == user.sub))


async def accessible_patient(db, user, patient_id):
    patient = await db.scalar(select(Patient).where(Patient.id == patient_id, patient_scope(user)))
    if patient is None:
        # Conceal existence of inaccessible records.
        raise HTTPException(404, "Patient not found")
    return patient


def staff_only(user):
    if user.role not in (UserRole.ADMIN, UserRole.CLINICIAN, UserRole.LHW):
        raise HTTPException(403, "Staff role required")
