"""Case-specific history; unknown observations never become model defaults."""
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

class GestationLabs(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    skin_thickness_mm: float | None = Field(None, strict=True, gt=0, le=100)
    insulin_mu_ml: float | None = Field(None, strict=True, gt=0, le=3000)
    bmi: float | None = Field(None, strict=True, gt=0, le=100)
    diabetes_pedigree_function: float | None = Field(None, strict=True, gt=0, le=5)

class AppointmentResearch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scholarship: StrictBool | None = None
    sms_received: StrictBool | None = None
    hypertension: StrictBool | None = None
    diabetes: StrictBool | None = None
    alcoholism: StrictBool | None = None
    handicap_code: int | None = Field(None, strict=True, ge=0, le=4)

class EncounterContext(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    expected_delivery_date: date | None = None
    dating_source: Literal["clinician", "ultrasound", "other", "unknown"] = "unknown"
    previous_pregnancies: int | None = Field(None, strict=True, ge=0, le=30)
    previous_births: int | None = Field(None, strict=True, ge=0, le=30)
    previous_complications: list[str] = Field(default_factory=list, max_length=20)
    medical_conditions: list[str] = Field(default_factory=list, max_length=20)
    history_notes: str = Field("", max_length=2000)
    measurement_taken_at: datetime | None = None
    glucose_test_type: Literal["fasting", "random", "clinical_test", "unknown"] = "unknown"
    additional_test_results: str = Field("", max_length=2000)
    additional_symptoms: str = Field("", max_length=2000)
    movements_started: StrictBool | None = None
    movements_reduced: StrictBool | None = None
    movement_concern_noticed_at: datetime | None = None
    fetal_notes: str = Field("", max_length=2000)
    preferred_language: Literal["en", "ur", "ps"] = "ur"
    storage_consent: StrictBool | None = None
    notification_consent: StrictBool = False
    gestation_labs: GestationLabs = Field(default_factory=GestationLabs)
    run_research_models: StrictBool = False
    appointment_research: AppointmentResearch = Field(default_factory=AppointmentResearch)

    @model_validator(mode="after")
    def consistent_history(self):
        if self.storage_consent is False:
            raise ValueError("Consent to store this case is required before saving")
        if self.previous_births is not None and self.previous_pregnancies is not None and self.previous_births > self.previous_pregnancies:
            raise ValueError("Previous births cannot exceed previous pregnancies")
        if self.movements_started is False and self.movements_reduced is True:
            raise ValueError("Movement reduction cannot be marked when movements have never been felt")
        return self


def merge_movement_observation(vitals,encounter):
    # Not having started feeling movements is different from a reduction in an established pattern.
    if encounter.get("movements_reduced") is True:
        if vitals.get("fetal_movement_present") is True:
            raise ValueError("Reduced movement conflicts with an explicitly reassuring movement flag")
        return {**vitals,"fetal_movement_present":False}
    return vitals
