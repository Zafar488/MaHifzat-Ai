"""Compatibility adapter for the canonical safety service. No separate prescription rules."""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from backend.services.safety import SafetyService

class TriageLevel(Enum):
    GREEN = "LOW_RISK"
    ORANGE = "URGENT"
    RED = "HIGH_RISK_EMERGENCY"
    UNKNOWN = "INSUFFICIENT_DATA"

@dataclass
class PatientVitals:
    systolic_bp: float | None = None
    diastolic_bp: float | None = None
    heart_rate: float | None = None
    temperature_celsius: float | None = None
    respiratory_rate: float | None = None
    gestational_age_weeks: float | None = None
    fetal_movement_present: bool | None = None
    vaginal_bleeding: str | None = None
    headache_severity: str | None = None
    visual_disturbance: bool | None = None
    epigastric_pain: bool | None = None
    vaginal_discharge_foul: bool | None = None
    convulsions: bool | None = None
    consciousness_level: str | None = None

@dataclass
class TriageResult:
    triage_level: TriageLevel
    triggered_rules: list = field(default_factory=list)
    clinical_rationale: list = field(default_factory=list)
    recommended_actions: list = field(default_factory=list)
    override_ml_scores: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ClinicalSafetyEngine:
    def evaluate(self, vitals):
        values = asdict(vitals)
        values["vaginal_bleeding"] = {"heavy":"severe","spotting":"mild"}.get(values["vaginal_bleeding"],values["vaginal_bleeding"])
        values["consciousness_level"] = {"verbal":"drowsy","pain":"unconscious","unresponsive":"unconscious"}.get(values["consciousness_level"],values["consciousness_level"])
        result = SafetyService().check_who_red_flags(values)
        return TriageResult(TriageLevel(result["triage_level"]),result["triggered_rules"],result["clinical_rationale"],result["recommended_actions"],result["override_ml_scores"],result["timestamp"])
    def to_dict(self, result):
        return {**asdict(result),"triage_level":result.triage_level.value}

def run_unit_tests():
    engine = ClinicalSafetyEngine()
    assert engine.evaluate(PatientVitals()).triage_level == TriageLevel.UNKNOWN
    assert engine.evaluate(PatientVitals(systolic_bp=180)).triage_level == TriageLevel.RED
    assert engine.evaluate(PatientVitals(vaginal_bleeding="heavy")).triage_level == TriageLevel.RED
    assert engine.evaluate(PatientVitals(temperature_celsius=39,vaginal_discharge_foul=True)).triage_level == TriageLevel.RED
    print("Canonical safety compatibility checks passed")
if __name__ == "__main__": run_unit_tests()
