"""Typed API request shared by risk and workflow entrypoints."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator, model_validator
from backend.schemas.clinical import ClinicalInput, Symptom, normalize_symptoms
from backend.schemas.care import PatientLocation, FollowupContext
from backend.schemas.encounter import EncounterContext


class AssessmentInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    patient_id: str = Field(min_length=1, max_length=100)
    case_id: str | None = Field(None, min_length=1, max_length=100)
    vitals: ClinicalInput = Field(default_factory=ClinicalInput)
    symptoms: list[Symptom] = Field(default_factory=list)
    ctg_features: dict[str, float] | None = None
    ctg_source: Literal["uci_measured", "demo"] | None = None
    clinical_features: dict[str, float] | None = None
    anc_features: dict | None = None
    provenance: Literal["measured", "patient_reported", "demo"] = "patient_reported"
    location: PatientLocation | None = None
    followup: FollowupContext = Field(default_factory=FollowupContext)
    allow_llm_processing: StrictBool = False
    encounter: EncounterContext = Field(default_factory=EncounterContext)

    @model_validator(mode="after")
    def movement_safety(self):
        from backend.schemas.encounter import merge_movement_observation
        if self.encounter.movements_reduced is True:
            self.vitals=ClinicalInput.model_validate(merge_movement_observation(self.vitals.model_dump(),self.encounter.model_dump()))
        return self

    @field_validator("symptoms", mode="before")
    @classmethod
    def symptoms_normalized(cls, value):
        return normalize_symptoms(value)

    @field_validator("ctg_features", mode="before")
    @classmethod
    def ctg_numeric(cls, value):
        if value is not None:
            if not isinstance(value, dict) or any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in value.values()):
                raise ValueError("CTG values must be numeric measurements")
        return value

    @field_validator("ctg_features")
    @classmethod
    def ctg_contract(cls, value):
        if value is not None:
            import math
            from backend.services.inference import CTG_FEATURES
            if set(value) - set(CTG_FEATURES):
                raise ValueError("Unknown CTG feature")
            if not all(math.isfinite(v) for v in value.values()):
                raise ValueError("CTG features must be finite")
            for name, v in value.items():
                if name in ("AC", "FM", "UC", "DL", "DS", "DP") and not 0 <= v <= 1:
                    raise ValueError("CTG event rates must be events per second in [0,1]")
                if name in ("ASTV", "ALTV") and not 0 <= v <= 100:
                    raise ValueError("CTG percentages must be in [0,100]")
                if name == "Tendency" and v not in (-1, 0, 1):
                    raise ValueError("Invalid histogram tendency")
                if name != "Tendency" and v < 0:
                    raise ValueError("CTG measurements cannot be negative")
        return value


class WorkflowRequest(AssessmentInput):
    ctg_data: dict[str, float] | None = None
    language: Literal["en", "ur", "ps", "sk"] = "en"
    channel: Literal["app", "web", "offline"] = "app"
    demographics: dict = Field(default_factory=dict)

    @field_validator("ctg_data", mode="before")
    @classmethod
    def numeric_ctg_data(cls, value):
        return AssessmentInput.ctg_numeric(value)

    @field_validator("ctg_data")
    @classmethod
    def valid_ctg_data(cls, value):
        return AssessmentInput.ctg_contract(value)
