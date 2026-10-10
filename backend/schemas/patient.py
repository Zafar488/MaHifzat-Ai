"""Patient-related Pydantic schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


from backend.schemas.clinical import ClinicalInput as VitalsInput, Symptom as SymptomEntry


class PatientCreate(BaseModel):
    name: str
    age: int = Field(ge=10, le=60)
    gender: Gender = Gender.FEMALE
    phone: Optional[str] = None
    location: Optional[str] = None
    gestational_age_weeks: Optional[float] = Field(None, ge=0, le=45)
    parity: Optional[int] = Field(None, ge=0, le=30)
    language: str = "ur"
    channel: str = "app"


class PatientProfile(PatientCreate):
    patient_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class PatientScreening(BaseModel):
    patient_id: str
    vitals: VitalsInput
    symptoms: List[SymptomEntry] = []
    ctg_features: Optional[dict] = None
    notes: Optional[str] = None
    created_offline_at: Optional[datetime] = None  # Offline sync support
    client_generated_id: Optional[str] = None       # Offline sync support
