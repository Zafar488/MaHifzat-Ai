import pytest
from backend.agents.orchestrator import run_workflow, NODES
from backend.services.inference import ModelRegistry, CTG_FEATURES

def state(vitals=None):
    return {"patient_id": "synthetic", "case_id": "synthetic-case", "vitals": vitals or {}, "symptoms": [], "audit_trail": [], "errors": [], "messages": []}


@pytest.mark.asyncio
async def test_missing_intake_still_triaged():
    s = state({"systolic_bp": 180})
    s["symptoms"] = [{"name": "convulsions", "severity": "severe"}]
    result = await run_workflow(s)
    assert result["emergency"] is True
    assert result["status"] == "incomplete"
    assert result["clinical_risk_result"]["who_red_flags"]["triggered_rules"]
    assert result["communication_result"]["status"] == "not_sent"


@pytest.mark.asyncio
async def test_top_level_ctg_runs_fetal_node():
    r = ModelRegistry()
    r.load_all()
    s = state({"age": 30, "systolic_bp": 120, "diastolic_bp": 80, "blood_sugar_mmol_l": 7, "temperature_celsius": 37, "heart_rate": 76})
    s["ctg_data"] = dict(zip(CTG_FEATURES, r._models["fetalwatch"]["known_input"]))
    result = await run_workflow(s)
    assert result["fetal_result"]["fetal_model_available"] is True
    assert "fetal_monitoring" in [e["agent"] for e in result["audit_trail"]]


@pytest.mark.asyncio
async def test_suspect_escalates_without_preterm_claim(monkeypatch):
    r = ModelRegistry()
    monkeypatch.setattr(r, "predict_fetal_health", lambda values: {"fetal_status": "suspect", "status": "experimental", "model_available": True, "probabilities": {}, "confidence": None})
    s = state({"systolic_bp": 120})
    s["ctg_data"] = {"LB": 130}
    result = await run_workflow(s)
    assert result["fetal_result"]["escalate"] is True
    assert result["referral_result"]["urgency_level"] == "urgent"
    assert result["fetal_result"]["preterm_risk"] == "disabled"


@pytest.mark.asyncio
async def test_node_error_stops_downstream(monkeypatch):
    async def fail(s):
        raise RuntimeError("Synthetic")
    monkeypatch.setitem(NODES, "data_quality", fail)
    result = await run_workflow(state({"systolic_bp": 120}))
    assert result["status"] == "failed"
    assert result.get("reporting_result") is None


@pytest.mark.asyncio
async def test_malformed_input_rejected():
    with pytest.raises(ValueError):
        await run_workflow(state({"systolic_bp": "bad"}))

@pytest.mark.asyncio
async def test_model_execution_error_stops_workflow(monkeypatch):
    r=ModelRegistry()
    monkeypatch.setattr(r,"predict_maternal_risk",lambda _:{"risk_level":"unknown","status":"error","model_available":False,"probabilities":{},"confidence":None})
    result=await run_workflow(state({"age":30,"systolic_bp":120,"diastolic_bp":80,"blood_sugar_mmol_l":7,"temperature_celsius":37,"heart_rate":76}))
    assert result["status"]=="failed"
    assert result.get("reporting_result") is None


@pytest.mark.asyncio
async def test_fetal_emergency_handover_does_not_offer_routine_care(monkeypatch):
    r=ModelRegistry()
    monkeypatch.setattr(r,"predict_fetal_health",lambda _:{"fetal_status":"pathological","status":"experimental","model_available":True,"probabilities":{},"confidence":None})
    s=state({"age":30,"systolic_bp":120,"diastolic_bp":80,"blood_sugar_mmol_l":5.4,"temperature_celsius":37,"heart_rate":82})
    s["ctg_data"]={"LB":125}
    result=await run_workflow(s)
    summary=result["clinician_result"]["case_summary_text"]
    assert "Seek immediate emergency maternity assessment for the fetal concern" in summary
    assert "Continue scheduled clinical care" not in summary
