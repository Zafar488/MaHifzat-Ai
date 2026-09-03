"""Referral and facility schemas."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class FacilityInfo(BaseModel):
    facility_id: str
    name: str
    type: str  # hospital, clinic, health_center
    latitude: float
    longitude: float
    distance_km: Optional[float] = None
    travel_time_minutes: Optional[float] = None
    has_emergency: bool = False
    has_maternity: bool = False
    has_nicu: bool = False
    current_load: Optional[str] = None  # low, medium, high


class ReferralResult(BaseModel):
    referral_case_id: str
    ranked_facilities: List[FacilityInfo] = []
    selected_facility: Optional[FacilityInfo] = None
    estimated_travel_time_min: Optional[float] = None
    urgency_level: str = "routine"  # routine, urgent, emergency
    created_at: datetime = Field(default_factory=datetime.now)
