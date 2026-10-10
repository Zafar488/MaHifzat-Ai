"""Clinical contract v1: glucose mmol/L, temperature Celsius.
UCI legacy BS/BodyTemp mean mmol/L/Fahrenheit. Generic values require units.
"""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator


class Symptom(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=100)
    severity: Literal["mild", "moderate", "severe"] = "mild"
    duration_hours: float | None = Field(None, ge=0, le=8760)


class ClinicalInput(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    age: float | None = Field(None, ge=10, le=100)
    systolic_bp: float | None = Field(None, ge=40, le=300)
    diastolic_bp: float | None = Field(None, ge=20, le=200)
    heart_rate: float | None = Field(None, ge=20, le=250)
    temperature_celsius: float | None = Field(None, ge=30, le=45)
    blood_sugar_mmol_l: float | None = Field(None, ge=0.5, le=55)
    respiratory_rate: float | None = Field(None, ge=4, le=80)
    gestational_age_weeks: float | None = Field(None, ge=0, le=45)
    fetal_movement_present: StrictBool | None = None
    vaginal_bleeding: Literal["none", "mild", "moderate", "severe"] | None = None
    headache_severity: Literal["none", "mild", "moderate", "severe"] | None = None
    visual_disturbance: StrictBool | None = None
    epigastric_pain: StrictBool | None = None
    vaginal_discharge_foul: StrictBool | None = None
    convulsions: StrictBool | None = None
    consciousness_level: Literal["alert", "drowsy", "unconscious"] | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize(cls, value):
        if isinstance(value, cls):
            return value
        data = dict(value)
        def assign(key, incoming):
            if key in data and data[key] is not None and abs(float(data[key]) - float(incoming)) > 1e-8:
                raise ValueError(f"Conflicting values for {key}")
            data[key] = incoming
        for legacy, canonical in {"Age": "age", "SystolicBP": "systolic_bp", "DiastolicBP": "diastolic_bp", "HeartRate": "heart_rate", "BS": "blood_sugar_mmol_l"}.items():
            if legacy in data:
                incoming = data.pop(legacy)
                if isinstance(incoming, bool):
                    raise ValueError("Vitals must be numeric")
                if incoming is not None:
                    assign(canonical, incoming)
        if "BodyTemp" in data:
            incoming = data.pop("BodyTemp")
            if isinstance(incoming, bool):
                raise ValueError("Temperature must be numeric")
            if incoming is not None:
                if "temperature_celsius" in data and data["temperature_celsius"] is not None:
                    if abs(float(data["temperature_celsius"]) - float(incoming)) < 1e-4 and float(data["temperature_celsius"]) > 45:
                        data.pop("temperature_celsius")
                assign("temperature_celsius", (float(incoming) - 32) * 5 / 9)
        for raw, unit_key, canonical, units in [
            ("blood_sugar", "blood_sugar_unit", "blood_sugar_mmol_l", {"mmol/L": lambda x: x, "mg/dL": lambda x: x / 18.0182}),
            ("temperature", "temperature_unit", "temperature_celsius", {"C": lambda x: x, "F": lambda x: (x - 32) * 5 / 9}),
        ]:
            if raw in data:
                unit = data.pop(unit_key, None)
                if unit not in units:
                    raise ValueError(f"{raw} requires an explicit valid {unit_key}")
                incoming = data.pop(raw)
                if isinstance(incoming, bool):
                    raise ValueError(f"{raw} must be numeric")
                assign(canonical, units[unit](float(incoming)))
        numeric = {"age", "systolic_bp", "diastolic_bp", "heart_rate", "temperature_celsius", "blood_sugar_mmol_l", "respiratory_rate", "gestational_age_weeks"}
        if any(isinstance(data.get(key), bool) for key in numeric):
            raise ValueError("Vitals must be numbers, not booleans")
        if data.get("systolic_bp") is not None and data.get("diastolic_bp") is not None:
            if float(data["diastolic_bp"]) >= float(data["systolic_bp"]):
                raise ValueError("Diastolic BP must be lower than systolic BP")
        return data

    def maternal_features(self):
        return dict(zip(["Age", "SystolicBP", "DiastolicBP", "BS", "BodyTemp", "HeartRate"], [self.age, self.systolic_bp, self.diastolic_bp, self.blood_sugar_mmol_l, None if self.temperature_celsius is None else self.temperature_celsius * 9 / 5 + 32, self.heart_rate]))

    def missing_vitals(self):
        return [name for name in ("systolic_bp", "diastolic_bp", "heart_rate", "temperature_celsius") if getattr(self, name) is None]


def normalize_symptoms(symptoms):
    return [Symptom(name=s) if isinstance(s, str) else Symptom.model_validate(s) for s in (symptoms or [])]
