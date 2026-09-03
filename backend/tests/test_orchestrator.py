"""Integration tests for the LangGraph orchestrator workflow."""
import pytest
from backend.agents.orchestrator import run_workflow


# ---------------------------------------------------------------------------
# Helper: build a base state dict
# ---------------------------------------------------------------------------

def _make_state(
    *,
    systolic_bp: float = 120.0,
    diastolic_bp: float = 80.0,
    heart_rate: float = 76.0,
    temperature_celsius: float = 37.0,
    gestational_age_weeks: float = 32.0,
    intake_complete: bool = True,
    extra_vitals: dict | None = None,
) -> dict:
    """Build a minimal AgentState dict for orchestrator tests."""
    vitals = {
        "systolic_bp": systolic_bp,
        "diastolic_bp": diastolic_bp,
        "heart_rate": heart_rate,
        "temperature_celsius": temperature_celsius,
        "gestational_age_weeks": gestational_age_weeks,
    }
    if extra_vitals:
        vitals.update(extra_vitals)

    return {
        "patient_id": "test-patient-001",
        "case_id": "test-case-001",
        "language": "en",
        "channel": "app",
        "vitals": vitals,
        "symptoms": [],
        "demographics": {"age": 30, "phone": "+923000000000"},
        "intake_complete": intake_complete,
        "emergency": False,
        "audit_trail": [],
        "errors": [],
        "messages": [],
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_normal_workflow():
    """Run workflow with complete intake data and normal vitals.

    Verifies:
    - clinical_risk_result is populated
    - no emergency
    - flow completes through to reporting
    """
    state = _make_state()

    result = await run_workflow(state)

    # Intake should be complete
    assert result.get("intake_complete") is True

    # Clinical risk should have been assessed
    assert result.get("clinical_risk_result") is not None
    assert isinstance(result["clinical_risk_result"], dict)

    # No emergency with normal vitals
    assert result.get("emergency") is False

    # Reporting should have been generated (normal flow goes through reporting)
    assert result.get("reporting_result") is not None

    # Audit trail should have entries from multiple nodes
    audit = result.get("audit_trail", [])
    assert len(audit) >= 3, f"Expected ≥3 audit entries, got {len(audit)}"


@pytest.mark.asyncio
async def test_emergency_workflow():
    """Run workflow with dangerous vitals (SBP=180, DBP=120).

    Verifies:
    - emergency=True is set
    - smart_referral was triggered (referral_result populated)
    """
    state = _make_state(systolic_bp=180.0, diastolic_bp=120.0)

    result = await run_workflow(state)

    # Emergency should be flagged
    assert result.get("emergency") is True

    # Clinical risk should detect emergency
    clinical = result.get("clinical_risk_result")
    assert clinical is not None
    assert clinical.get("is_emergency") is True

    # Smart referral should have been triggered
    referral = result.get("referral_result")
    assert referral is not None
    assert referral.get("urgency_level") == "emergency"

    # Communication should have been sent
    comm = result.get("communication_result")
    assert comm is not None
    assert comm.get("is_emergency_alert") is True


@pytest.mark.asyncio
async def test_incomplete_intake():
    """Run workflow with intake_complete=False (missing required vitals).

    Verifies:
    - Workflow stops early (END after patient_intake)
    - clinical_risk_result is NOT populated
    """
    state = _make_state(intake_complete=False)
    # Also remove required fields so patient_intake re-evaluates and finds them missing
    state["vitals"] = {"systolic_bp": 120.0}  # missing diastolic_bp, heart_rate, etc.

    result = await run_workflow(state)

    # Intake should remain incomplete
    assert result.get("intake_complete") is False

    # Clinical risk should NOT have been reached
    assert result.get("clinical_risk_result") is None

    # Reporting should NOT have been reached
    assert result.get("reporting_result") is None
