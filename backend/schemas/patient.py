"""Patient-related Pydantic schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class VitalsInput(BaseModel):
    systolic_bp: Optional[float] = Field(None, ge=60, le=250)
    diastolic_bp: Optional[float] = Field(None, ge=30, le=150)
    heart_rate: Optional[float] = Field(None, ge=30, le=200)
    temperature_celsius: Optional[float] = Field(None, ge=34, le=42)
    respiratory_rate: Optional[float] = Field(None, ge=8, le=60)
    blood_sugar: Optional[float] = Field(None, ge=20, le=600)
    gestational_age_weeks: Optional[float] = Field(None, ge=0, le=45)
    fetal_movement_present: Optional[bool] = None


class SymptomEntry(BaseModel):
    name: str
    severity: str = "mild"  # mild, moderate, severe
    duration_hours: Optional[float] = None


class PatientCreate(BaseModel):
    name: str
    age: int = Field(ge=10, le=60)
    gender: Gender = Gender.FEMALE
    phone: Optional[str] = None
    location: Optional[str] = None
    gestational_age_weeks: Optional[float] = None
    parity: Optional[int] = None
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
