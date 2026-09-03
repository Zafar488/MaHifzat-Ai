"""Integration tests for the ModelRegistry inference service."""
import pytest
from backend.services.inference import ModelRegistry, CTG_FEATURES
from backend.services.safety import SafetyService


# ---------------------------------------------------------------------------
# ModelRegistry tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_model_registry_loads():
    """Verify ModelRegistry().load_all() succeeds and health_check returns all models as loaded."""
    registry = ModelRegistry()
    registry.load_all()
    health = registry.health_check()

    # All 5 models should be present
    assert isinstance(health, dict)
    assert "fetalwatch" in health
    assert "maternalguard" in health
    assert "pretermguard" in health
    assert "carereach" in health
    assert "gestationinsight" in health

    # All should be loaded (True)
    for model_name, loaded in health.items():
        assert loaded is True, f"Model {model_name} failed to load"


@pytest.mark.asyncio
async def test_predict_maternal_risk():
    """Call predict_maternal_risk with sample vitals, verify returns dict with risk_level and confidence."""
    registry = ModelRegistry()
    registry.load_all()

    vitals = {
        "Age": 30,
        "SystolicBP": 120,
        "DiastolicBP": 80,
        "BS": 7.0,
        "BodyTemp": 98.6,
        "HeartRate": 76,
    }

    result = registry.predict_maternal_risk(vitals)

    assert isinstance(result, dict)
    assert "risk_level" in result
    assert "confidence" in result
    assert result["model_available"] is True
    assert isinstance(result["confidence"], float)
    assert 0.0 <= result["confidence"] <= 1.0


@pytest.mark.asyncio
async def test_predict_fetal_health():
    """Call predict_fetal_health with 21 zeros (dummy CTG), verify returns dict with fetal_status."""
    registry = ModelRegistry()
    registry.load_all()

    # Build dummy CTG features (all zeros)
    ctg_features = {feature: 0.0 for feature in CTG_FEATURES}

    result = registry.predict_fetal_health(ctg_features)

    assert isinstance(result, dict)
    assert "fetal_status" in result
    assert result["model_available"] is True
    assert isinstance(result["confidence"], float)


@pytest.mark.asyncio
async def test_safety_check():
    """Call SafetyService().check_who_red_flags with dangerous vitals, verify RED/emergency."""
    safety = SafetyService()

    vitals_dict = {
        "systolic_bp": 170,
        "diastolic_bp": 110,
        "heart_rate": 95,
        "temperature_celsius": 37.0,
        "respiratory_rate": 18,
        "gestational_age_weeks": 32,
        "fetal_movement_present": True,
        "vaginal_bleeding": "none",
        "headache_severity": "none",
        "visual_disturbance": False,
        "epigastric_pain": False,
        "vaginal_discharge_foul": False,
        "convulsions": False,
        "consciousness_level": "alert",
    }

    result = safety.check_who_red_flags(vitals_dict)

    assert isinstance(result, dict)
    assert "triage_level" in result
    # SBP 170 >= 160 triggers severe_hypertension → RED
    assert result["triage_level"] == "HIGH_RISK_EMERGENCY"
    assert "severe_hypertension" in result["triggered_rules"]
    assert result["override_ml_scores"] is True
