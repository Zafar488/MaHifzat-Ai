"""Measured location and explicit follow-up observations shared by UI and API."""
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

class PatientLocation(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    source: Literal["gps", "manual", "demo"] = "manual"
    accuracy_m: float | None = Field(None, ge=0)
    captured_at: datetime | None = None
    share_for_routing: StrictBool = False
    share_for_discovery: StrictBool = False

class FollowupContext(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    gestational_age_weeks: float | None = Field(None, ge=0, le=45)
    completed_contact_weeks: list[int] = Field(default_factory=list, max_length=8)
    next_appointment_date: date | None = None
    missed_visits: int = Field(0, ge=0, le=50)
    transport_barrier: StrictBool = False
    phone_access: StrictBool | None = None
    booking_date: date | None = None
    last_completed_checkup_date: date | None = None
    reminder_actually_sent: StrictBool | None = None
    preferred_notification_channel: Literal["app", "sms", "whatsapp", "call", "health_worker_visit"] = "app"

    @model_validator(mode="after")
    def contacts(self):
        if self.booking_date and self.next_appointment_date and self.booking_date > self.next_appointment_date:
            raise ValueError("Booking date cannot follow appointment date")
        if len(set(self.completed_contact_weeks)) != len(self.completed_contact_weeks):
            raise ValueError("Duplicate contact milestones")
        if set(self.completed_contact_weeks) - {12, 20, 26, 30, 34, 36, 38, 40}:
            raise ValueError("Unknown ANC contact milestone")
        if self.gestational_age_weeks is not None and any(w > self.gestational_age_weeks for w in self.completed_contact_weeks):
            raise ValueError("Future contact cannot be marked completed")
        return self

class Facility(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    facility_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    type: str = "hospital"
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    has_emergency: StrictBool = False
    has_maternity: StrictBool = False
    has_nicu: StrictBool = False
    phone: str | None = None
    source: str = Field(min_length=1)
    verified_at: date | None = None
    availability: Literal["unknown", "available", "unavailable"] = "unknown"
    availability_checked_at: datetime | None = None
    simulated: StrictBool = False
