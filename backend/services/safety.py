"""
Safety service — thin adapter over the existing ClinicalSafetyEngine.
"""

import sys
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from safety_rules import (
    ClinicalSafetyEngine,
    PatientVitals,
    TriageResult,
    TriageLevel,
)


class SafetyService:
    """Adapter wrapping the WHO Clinical Safety Rule Engine."""

    def __init__(self) -> None:
        self.engine = ClinicalSafetyEngine()

    def check_who_red_flags(self, vitals_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run WHO danger-sign assessment.

        Parameters
        ----------
        vitals_dict : dict
            Vital-sign and symptom inputs matching ``PatientVitals`` fields:
            systolic_bp, diastolic_bp, heart_rate, temperature_celsius,
            respiratory_rate, gestational_age_weeks, fetal_movement_present,
            vaginal_bleeding, headache_severity, visual_disturbance,
            epigastric_pain, vaginal_discharge_foul, convulsions,
            consciousness_level.

        Returns
        -------
        dict
            triage_level, triggered_rules, clinical_rationale,
            recommended_actions, override_ml_scores, timestamp.
        """
        patient_vitals = PatientVitals(
            systolic_bp=vitals_dict.get("systolic_bp"),
            diastolic_bp=vitals_dict.get("diastolic_bp"),
            heart_rate=vitals_dict.get("heart_rate"),
            temperature_celsius=vitals_dict.get("temperature_celsius"),
            respiratory_rate=vitals_dict.get("respiratory_rate"),
            gestational_age_weeks=vitals_dict.get("gestational_age_weeks"),
            fetal_movement_present=vitals_dict.get("fetal_movement_present"),
            vaginal_bleeding=vitals_dict.get("vaginal_bleeding"),
            headache_severity=vitals_dict.get("headache_severity"),
            visual_disturbance=vitals_dict.get("visual_disturbance"),
            epigastric_pain=vitals_dict.get("epigastric_pain"),
            vaginal_discharge_foul=vitals_dict.get("vaginal_discharge_foul"),
            convulsions=vitals_dict.get("convulsions"),
            consciousness_level=vitals_dict.get("consciousness_level"),
        )

        result: TriageResult = self.engine.evaluate(patient_vitals)
        return self.engine.to_dict(result)

    def is_emergency(self, vitals_dict: Dict[str, Any]) -> bool:
        """Quick check if vitals indicate an emergency (RED triage)."""
        result = self.check_who_red_flags(vitals_dict)
        return result.get("triage_level") == "HIGH_RISK_EMERGENCY"


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_safety_service: "SafetyService | None" = None


def get_safety_service() -> SafetyService:
    """Return a process-wide SafetyService singleton."""
    global _safety_service
    if _safety_service is None:
        _safety_service = SafetyService()
    return _safety_service
