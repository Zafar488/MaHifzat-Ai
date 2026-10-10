"""
WHO Clinical Safety Rule Engine — MaaHifazat AI
Deterministic expert system implementing WHO Maternal Emergency Triage guidelines.
Reference: WHO (2017) Managing Complications in Pregnancy and Childbirth (MCPC)
           ISBN: 9789241546669
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import json
from datetime import datetime


# ---------------------------------------------------------------------------
# Enum: TriageLevel
# ---------------------------------------------------------------------------

class TriageLevel(Enum):
    """WHO Emergency Triage classification levels."""

    GREEN = "LOW_RISK"            # Routine care
    YELLOW = "MODERATE_RISK"      # Requires attention within 1 hour
    ORANGE = "HIGH_RISK"          # Urgent, requires attention within 15 min
    RED = "HIGH_RISK_EMERGENCY"   # Immediate life-threatening, requires instant intervention


# ---------------------------------------------------------------------------
# Dataclass: PatientVitals
# ---------------------------------------------------------------------------

@dataclass
class PatientVitals:
    """Container for all patient vital-sign and symptom inputs."""

    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None
    heart_rate: Optional[float] = None
    temperature_celsius: Optional[float] = None
    respiratory_rate: Optional[float] = None
    gestational_age_weeks: Optional[float] = None
    fetal_movement_present: Optional[bool] = None
    vaginal_bleeding: Optional[str] = None          # 'none', 'spotting', 'moderate', 'heavy'
    headache_severity: Optional[str] = None          # 'none', 'mild', 'severe'
    visual_disturbance: Optional[bool] = None
    epigastric_pain: Optional[bool] = None
    vaginal_discharge_foul: Optional[bool] = None
    convulsions: Optional[bool] = None
    consciousness_level: Optional[str] = None        # 'alert', 'verbal', 'pain', 'unresponsive'


# ---------------------------------------------------------------------------
# Dataclass: TriageResult
# ---------------------------------------------------------------------------

@dataclass
class TriageResult:
    """Output of the triage evaluation including all triggered rules and actions."""

    triage_level: TriageLevel
    triggered_rules: List[str] = field(default_factory=list)
    clinical_rationale: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    override_ml_scores: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ---------------------------------------------------------------------------
# Class: ClinicalSafetyEngine
# ---------------------------------------------------------------------------

class ClinicalSafetyEngine:
    """
    WHO-based Maternal Emergency Triage Rule Engine.

    Evaluates patient vitals against WHO danger-sign criteria.
    If **any** red flag evaluates True the engine sets
    ``override_ml_scores = True`` and assigns ``TriageLevel.RED``,
    overriding all ML-based risk scores.
    """

    # Convenience type alias for rule return values
    _RuleResult = Optional[Tuple[str, str, str]]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(self, vitals: PatientVitals) -> TriageResult:
        """
        Run all triage rules in priority order and return a *TriageResult*.

        Evaluation order:
        1. RED-flag rules  (immediate life-threatening)
        2. ORANGE rules    (urgent)
        3. YELLOW rules    (requires attention)
        4. GREEN           (default — routine care)
        """
        result = TriageResult(triage_level=TriageLevel.GREEN)

        # ---- RED rules ------------------------------------------------
        red_rules: List = [
            self._check_severe_hypertension,
            self._check_hemorrhage,
            self._check_imminent_eclampsia,
            self._check_eclampsia,
            self._check_sepsis,
            self._check_reduced_fetal_movement,
            self._check_unconsciousness,
        ]
        for rule_fn in red_rules:
            triggered = rule_fn(vitals)
            if triggered is not None:
                name, rationale, action = triggered
                result.triggered_rules.append(name)
                result.clinical_rationale.append(rationale)
                result.recommended_actions.append(action)

        if result.triggered_rules:
            result.triage_level = TriageLevel.RED
            result.override_ml_scores = True
            return result

        # ---- ORANGE rules ---------------------------------------------
        orange_rules: List = [
            self._check_moderate_hypertension,
            self._check_moderate_bleeding,
            self._check_tachycardia,
            self._check_high_fever,
        ]
        for rule_fn in orange_rules:
            triggered = rule_fn(vitals)
            if triggered is not None:
                name, rationale, action = triggered
                result.triggered_rules.append(name)
                result.clinical_rationale.append(rationale)
                result.recommended_actions.append(action)

        if result.triggered_rules:
            result.triage_level = TriageLevel.ORANGE
            return result

        # ---- YELLOW rules ---------------------------------------------
        yellow_rules: List = [
            self._check_mild_hypertension,
            self._check_mild_symptoms,
        ]
        for rule_fn in yellow_rules:
            triggered = rule_fn(vitals)
            if triggered is not None:
                name, rationale, action = triggered
                result.triggered_rules.append(name)
                result.clinical_rationale.append(rationale)
                result.recommended_actions.append(action)

        if result.triggered_rules:
            result.triage_level = TriageLevel.YELLOW
            return result

        # ---- GREEN (default) ------------------------------------------
        result.clinical_rationale.append(
            "No danger signs detected. Patient vitals are within normal limits."
        )
        result.recommended_actions.append(
            "Continue routine antenatal care and monitoring."
        )
        return result

    # ------------------------------------------------------------------
    # RED FLAG RULES (Immediate Level-1 Escalation)
    # ------------------------------------------------------------------

    def _check_severe_hypertension(self, vitals: PatientVitals) -> _RuleResult:
        """SBP >= 160 OR DBP >= 110 mmHg — hypertensive crisis."""
        sbp = vitals.systolic_bp
        dbp = vitals.diastolic_bp
        if sbp is None and dbp is None:
            return None
        if (sbp is not None and sbp >= 160) or (dbp is not None and dbp >= 110):
            return (
                "severe_hypertension",
                (
                    f"Severe hypertension detected (SBP={sbp}, DBP={dbp} mmHg). "
                    "Risk of stroke, placental abruption, and organ failure."
                ),
                (
                    "Administer IV labetalol or hydralazine immediately. "
                    "Start magnesium sulfate for seizure prophylaxis. "
                    "Prepare for possible emergency delivery."
                ),
            )
        return None

    def _check_hemorrhage(self, vitals: PatientVitals) -> _RuleResult:
        """Heavy vaginal bleeding — potential placental abruption or previa."""
        if vitals.vaginal_bleeding is None:
            return None
        if vitals.vaginal_bleeding.lower() == "heavy":
            return (
                "hemorrhage",
                (
                    "Heavy vaginal bleeding detected. "
                    "High risk of hypovolemic shock and fetal distress."
                ),
                (
                    "Establish two large-bore IV lines. "
                    "Begin fluid resuscitation with crystalloids. "
                    "Cross-match blood and prepare for emergency cesarean section."
                ),
            )
        return None

    def _check_imminent_eclampsia(self, vitals: PatientVitals) -> _RuleResult:
        """Severe headache WITH visual disturbance OR epigastric pain."""
        if vitals.headache_severity is None:
            return None
        if vitals.headache_severity.lower() != "severe":
            return None
        visual = vitals.visual_disturbance is True
        epigastric = vitals.epigastric_pain is True
        if visual or epigastric:
            accompanying = []
            if visual:
                accompanying.append("visual disturbance")
            if epigastric:
                accompanying.append("epigastric pain")
            return (
                "imminent_eclampsia",
                (
                    f"Severe headache with {' and '.join(accompanying)}. "
                    "Classic pre-eclamptic toxemia signs indicating imminent eclampsia."
                ),
                (
                    "Administer IV magnesium sulfate loading dose (4 g over 15 min). "
                    "Control blood pressure with IV antihypertensives. "
                    "Prepare for urgent delivery once stabilized."
                ),
            )
        return None

    def _check_eclampsia(self, vitals: PatientVitals) -> _RuleResult:
        """Active convulsions — eclamptic seizure."""
        if vitals.convulsions is None:
            return None
        if vitals.convulsions:
            return (
                "eclampsia",
                (
                    "Active convulsions detected — eclamptic seizure in progress. "
                    "Immediate life-threatening emergency for mother and fetus."
                ),
                (
                    "Protect airway and administer IV magnesium sulfate (4 g bolus). "
                    "Provide supplemental oxygen. "
                    "Prepare for emergency cesarean section once seizures are controlled."
                ),
            )
        return None

    def _check_sepsis(self, vitals: PatientVitals) -> _RuleResult:
        """Temperature >= 38.5 °C WITH foul-smelling vaginal discharge."""
        if vitals.temperature_celsius is None or vitals.vaginal_discharge_foul is None:
            return None
        if vitals.temperature_celsius >= 38.5 and vitals.vaginal_discharge_foul:
            return (
                "sepsis",
                (
                    f"High fever ({vitals.temperature_celsius} °C) with foul-smelling "
                    "vaginal discharge — strong indicators of maternal sepsis."
                ),
                (
                    "Obtain blood cultures and start broad-spectrum IV antibiotics immediately. "
                    "Monitor for signs of septic shock. "
                    "Escalate to obstetric emergency team."
                ),
            )
        return None

    def _check_reduced_fetal_movement(self, vitals: PatientVitals) -> _RuleResult:
        """Absent fetal movement after 28 weeks gestation."""
        if vitals.gestational_age_weeks is None or vitals.fetal_movement_present is None:
            return None
        if vitals.gestational_age_weeks >= 28 and not vitals.fetal_movement_present:
            return (
                "reduced_fetal_movement",
                (
                    f"Absent fetal movement at {vitals.gestational_age_weeks} weeks gestation. "
                    "Possible fetal compromise or intrauterine fetal demise."
                ),
                (
                    "Perform immediate cardiotocography (CTG) monitoring. "
                    "Arrange urgent obstetric ultrasound assessment. "
                    "Consider emergency delivery if fetal distress confirmed."
                ),
            )
        return None

    def _check_unconsciousness(self, vitals: PatientVitals) -> _RuleResult:
        """Consciousness level 'pain' or 'unresponsive' on AVPU scale."""
        if vitals.consciousness_level is None:
            return None
        level = vitals.consciousness_level.lower()
        if level in ("pain", "unresponsive"):
            return (
                "unconsciousness",
                (
                    f"Reduced consciousness (AVPU: {vitals.consciousness_level}). "
                    "Potential cerebral event, severe metabolic derangement, or shock."
                ),
                (
                    "Secure airway and provide supplemental oxygen. "
                    "Establish IV access and check bedside blood glucose. "
                    "Call emergency obstetric and anaesthesia teams immediately."
                ),
            )
        return None

    # ------------------------------------------------------------------
    # ORANGE RULES (Urgent — attention within 15 minutes)
    # ------------------------------------------------------------------

    def _check_moderate_hypertension(self, vitals: PatientVitals) -> _RuleResult:
        """SBP 140–159 OR DBP 90–109 mmHg."""
        sbp = vitals.systolic_bp
        dbp = vitals.diastolic_bp
        if sbp is None and dbp is None:
            return None
        sbp_flag = sbp is not None and 140 <= sbp <= 159
        dbp_flag = dbp is not None and 90 <= dbp <= 109
        if sbp_flag or dbp_flag:
            return (
                "moderate_hypertension",
                (
                    f"Moderate hypertension detected (SBP={sbp}, DBP={dbp} mmHg). "
                    "Risk of progression to severe pre-eclampsia."
                ),
                (
                    "Monitor blood pressure every 15 minutes. "
                    "Obtain urine protein and blood work. "
                    "Consider oral antihypertensive therapy (methyldopa or nifedipine)."
                ),
            )
        return None

    def _check_moderate_bleeding(self, vitals: PatientVitals) -> _RuleResult:
        """Moderate vaginal bleeding."""
        if vitals.vaginal_bleeding is None:
            return None
        if vitals.vaginal_bleeding.lower() == "moderate":
            return (
                "moderate_bleeding",
                (
                    "Moderate vaginal bleeding detected. "
                    "Requires urgent assessment for placental complications."
                ),
                (
                    "Establish IV access and begin fluid monitoring. "
                    "Perform bedside ultrasound to assess placental position. "
                    "Monitor maternal hemodynamics and fetal heart rate continuously."
                ),
            )
        return None

    def _check_tachycardia(self, vitals: PatientVitals) -> _RuleResult:
        """Heart rate > 120 bpm."""
        if vitals.heart_rate is None:
            return None
        if vitals.heart_rate > 120:
            return (
                "tachycardia",
                (
                    f"Maternal tachycardia ({vitals.heart_rate} bpm). "
                    "May indicate hemorrhage, infection, dehydration, or cardiac compromise."
                ),
                (
                    "Assess for underlying cause (bleeding, fever, pain). "
                    "Establish IV access and administer IV fluids. "
                    "Obtain ECG and continuous cardiac monitoring."
                ),
            )
        return None

    def _check_high_fever(self, vitals: PatientVitals) -> _RuleResult:
        """Temperature >= 38 °C without foul discharge (fever without sepsis indicators)."""
        if vitals.temperature_celsius is None:
            return None
        if vitals.temperature_celsius >= 38.0:
            # Sepsis rule (RED) already checked; this catches isolated fever
            foul = vitals.vaginal_discharge_foul is True
            if foul and vitals.temperature_celsius >= 38.5:
                # Would have been caught by sepsis RED rule already
                return None
            return (
                "high_fever",
                (
                    f"Elevated temperature ({vitals.temperature_celsius} °C). "
                    "Possible infection requiring urgent evaluation."
                ),
                (
                    "Obtain urine analysis and blood cultures if indicated. "
                    "Administer paracetamol and monitor temperature closely. "
                    "Assess for urinary tract or respiratory infection."
                ),
            )
        return None

    # ------------------------------------------------------------------
    # YELLOW RULES (Requires attention within 1 hour)
    # ------------------------------------------------------------------

    def _check_mild_hypertension(self, vitals: PatientVitals) -> _RuleResult:
        """SBP 130–139 OR DBP 81–89 (pre-hypertension range)."""
        sbp = vitals.systolic_bp
        dbp = vitals.diastolic_bp
        if sbp is None and dbp is None:
            return None
        sbp_flag = sbp is not None and 130 <= sbp <= 139
        dbp_flag = dbp is not None and 81 <= dbp <= 89
        if sbp_flag or dbp_flag:
            return (
                "mild_hypertension",
                (
                    f"Mildly elevated blood pressure (SBP={sbp}, DBP={dbp} mmHg). "
                    "Pre-hypertensive range — requires monitoring for progression."
                ),
                (
                    "Re-check blood pressure in 30 minutes. "
                    "Advise rest and left lateral positioning. "
                    "Schedule follow-up blood pressure monitoring."
                ),
            )
        return None

    def _check_mild_symptoms(self, vitals: PatientVitals) -> _RuleResult:
        """Mild headache OR spotting."""
        mild_headache = (
            vitals.headache_severity is not None
            and vitals.headache_severity.lower() == "mild"
        )
        spotting = (
            vitals.vaginal_bleeding is not None
            and vitals.vaginal_bleeding.lower() == "spotting"
        )
        if not mild_headache and not spotting:
            return None
        symptoms = []
        if mild_headache:
            symptoms.append("mild headache")
        if spotting:
            symptoms.append("vaginal spotting")
        return (
            "mild_symptoms",
            (
                f"Minor symptoms reported: {' and '.join(symptoms)}. "
                "Not immediately dangerous but warrants clinical attention."
            ),
            (
                "Document symptoms and monitor for progression. "
                "Provide reassurance and analgesia if needed. "
                "Advise patient to report worsening symptoms immediately."
            ),
        )

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self, result: TriageResult) -> Dict:
        """Serialize a *TriageResult* to a JSON-compatible dictionary."""
        return {
            "triage_level": result.triage_level.value,
            "triggered_rules": result.triggered_rules,
            "clinical_rationale": result.clinical_rationale,
            "recommended_actions": result.recommended_actions,
            "override_ml_scores": result.override_ml_scores,
            "timestamp": result.timestamp,
        }


# ---------------------------------------------------------------------------
# Unit Tests
# ---------------------------------------------------------------------------

def run_unit_tests() -> None:
    """Comprehensive unit tests for ClinicalSafetyEngine."""
    engine = ClinicalSafetyEngine()

    # Test 1: Severe hypertension
    vitals = PatientVitals(systolic_bp=170, diastolic_bp=95)
    result = engine.evaluate(vitals)
    assert result.triage_level == TriageLevel.RED
    assert result.override_ml_scores is True
    assert "severe_hypertension" in result.triggered_rules

    # Test 2: Normal vitals
    vitals = PatientVitals(
        systolic_bp=120,
        diastolic_bp=80,
        temperature_celsius=37.0,
        heart_rate=75,
        vaginal_bleeding="none",
        fetal_movement_present=True,
        gestational_age_weeks=32,
    )
    result = engine.evaluate(vitals)
    assert result.triage_level == TriageLevel.GREEN
    assert result.override_ml_scores is False

    # Test 3: Imminent eclampsia
    vitals = PatientVitals(headache_severity="severe", visual_disturbance=True)
    result = engine.evaluate(vitals)
    assert result.triage_level == TriageLevel.RED

    # Test 4: Sepsis signs
    vitals = PatientVitals(temperature_celsius=39.0, vaginal_discharge_foul=True)
    result = engine.evaluate(vitals)
    assert result.triage_level == TriageLevel.RED

    # Test 5: Reduced fetal movement after 28 weeks
    vitals = PatientVitals(gestational_age_weeks=32, fetal_movement_present=False)
    result = engine.evaluate(vitals)
    assert result.triage_level == TriageLevel.RED

    # Test 6: Moderate hypertension (ORANGE)
    vitals = PatientVitals(systolic_bp=150, diastolic_bp=95)
    result = engine.evaluate(vitals)
    assert result.triage_level == TriageLevel.ORANGE

    # Test 7: Heavy bleeding
    vitals = PatientVitals(vaginal_bleeding="heavy")
    result = engine.evaluate(vitals)
    assert result.triage_level == TriageLevel.RED

    # Test 8: Convulsions (eclampsia)
    vitals = PatientVitals(convulsions=True)
    result = engine.evaluate(vitals)
    assert result.triage_level == TriageLevel.RED

    # Test 9: Multiple flags — highest priority wins
    vitals = PatientVitals(systolic_bp=170, vaginal_bleeding="heavy", convulsions=True)
    result = engine.evaluate(vitals)
    assert result.triage_level == TriageLevel.RED
    assert len(result.triggered_rules) >= 2  # Multiple rules triggered

    # Test 10: Partial/missing data — engine should not crash
    vitals = PatientVitals()  # All None
    result = engine.evaluate(vitals)
    assert result.triage_level == TriageLevel.GREEN  # No data = no flags

    print("All 10 unit tests PASSED!")


if __name__ == "__main__":
    run_unit_tests()
