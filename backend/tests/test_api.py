"""API, contract, authorization and durable workflow regression coverage."""
import uuid
from datetime import datetime, timedelta
import pytest
from sqlalchemy import select, func
from backend.tests.conftest import login_as, TestSessionLocal
from backend.db.models import ClinicalRecord, CaseRecord, AgentStateRecord, AuditLog, Referral, User, Alert
from backend.config import settings

VITALS = {"Age": 30, "SystolicBP": 120, "DiastolicBP": 80, "BS": 7.0, "BodyTemp": 98.6, "HeartRate": 76}


@pytest.mark.asyncio
async def test_health_and_readiness(async_client):
    health = (await async_client.get("/api/health")).json()
    assert health["status"] == "ok"
    assert health["clinical_models"]["maternalguard"] is True
    assert health["research_workbench_models"]["carereach"] is False
    assert health["research_workbench_models"]["gestationinsight"] is False
    r = await async_client.get("/api/ready")
    assert r.status_code == 200, r.text
    ready = r.json()
    assert ready["clinical_models"]["maternalguard"] is True
    assert ready["research_workbench_models"]["carereach"] is False
    assert ready["research_workbench_models"]["gestationinsight"] is False
    assert ready["supported_models_ready"] is True



@pytest.mark.asyncio
async def test_login_and_logout(async_client):
    header = await login_as(async_client, "admin")
    assert (await async_client.get("/api/auth/me", headers=header)).json()["role"] == "admin"
    assert (await async_client.post("/api/auth/logout", headers=header)).status_code == 200
    assert (await async_client.get("/api/auth/me", headers=header)).status_code == 401
    assert (await async_client.post("/api/auth/login", data={"username": "admin", "password": "admin"})).status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["admin", "clinician", "lhw"])
async def test_public_privilege_signup_denied(async_client, role):
    r = await async_client.post("/api/auth/signup", json={"username": "new-user", "password": "Synthetic-test-pass!", "full_name": "Synthetic", "role": role})
    assert r.status_code == 422
    assert (await async_client.post("/api/auth/login", data={"username": "new-user", "password": "Synthetic-test-pass!"})).status_code == 401


@pytest.mark.asyncio
async def test_signup_default_patient_persistent(async_client):
    r = await async_client.post("/api/auth/signup", json={"username": "new-patient", "password": "Synthetic-test-pass!", "full_name": "Synthetic"})
    assert r.status_code == 201
    header = await login_as(async_client, "new-patient")
    assert (await async_client.get("/api/auth/me", headers=header)).json()["role"] == "patient"
    async with TestSessionLocal() as db:
        assert (await db.get(User, r.json()["user_id"])).role == "patient"


@pytest.mark.asyncio
async def test_disabled_or_role_changed_user_token_denied(async_client, auth_headers):
    clinician = await login_as(async_client, "clinician")
    r = await async_client.put("/api/auth/users/test-clinician", json={"role": "lhw", "is_active": False}, headers=auth_headers)
    assert r.status_code == 200
    assert (await async_client.get("/api/auth/me", headers=clinician)).status_code == 401


@pytest.mark.asyncio
async def test_patient_boundaries_every_route(async_client, auth_headers, patient_id):
    patient = await login_as(async_client, "patient")
    clinician = await login_as(async_client, "clinician")
    case = (await async_client.post("/api/risks/assess", json={"patient_id": patient_id, "vitals": {**VITALS, "SystolicBP": 180, "DiastolicBP": 120}}, headers=auth_headers)).json()["case_id"]
    referral = (await async_client.post("/api/referrals", json={"patient_id": patient_id, "facility_name": "Synthetic facility"}, headers=auth_headers)).json()["id"]
    alert = (await async_client.get("/api/alerts", headers=auth_headers)).json()[0]["alert_id"]
    for header in (patient, clinician):
        assert (await async_client.get("/api/patients", headers=header)).json() == []
        assert (await async_client.get(f"/api/patients/{patient_id}", headers=header)).status_code == 404
        assert (await async_client.put(f"/api/patients/{patient_id}", json={"name": "Other", "age": 30}, headers=header)).status_code == 404
        assert (await async_client.get(f"/api/patients/{patient_id}/assessments", headers=header)).status_code == 404
        assert (await async_client.post("/api/risks/assess", json={"patient_id": patient_id, "vitals": VITALS}, headers=header)).status_code == 404
        assert (await async_client.get(f"/api/risks/{case}", headers=header)).status_code == 404
        assert (await async_client.get("/api/referrals", headers=header)).json() == []
        assert (await async_client.get(f"/api/referrals/{referral}", headers=header)).status_code == 404
        assert (await async_client.get("/api/alerts", headers=header)).json() == []
        assert (await async_client.get(f"/api/alerts/{alert}", headers=header)).status_code == 404
        assert (await async_client.get("/api/audit/logs", headers=header)).status_code == 403
        assert (await async_client.get("/api/analytics/dashboard", headers=header)).json()["total_patients"] == 0
    assert (await async_client.post("/api/agents/run", json={"patient_id": patient_id, "case_id": case}, headers=patient)).status_code == 403
    assert (await async_client.post("/api/agents/run", json={"patient_id": patient_id, "case_id": case}, headers=clinician)).status_code == 404
    assigned = await async_client.post(f"/api/patients/{patient_id}/assign", json={"user_id": "test-clinician"}, headers=auth_headers)
    assert assigned.status_code == 201
    assert (await async_client.get(f"/api/patients/{patient_id}", headers=clinician)).status_code == 200


@pytest.mark.asyncio
@pytest.mark.parametrize("vitals", [
    {**VITALS, "SystolicBP": 180, "DiastolicBP": 120},
    {"age": 30, "systolic_bp": 180, "diastolic_bp": 120, "heart_rate": 76, "blood_sugar_mmol_l": 7, "temperature_celsius": 37},
])
async def test_emergency_formats(async_client, auth_headers, patient_id, vitals):
    r = await async_client.post("/api/risks/assess", json={"patient_id": patient_id, "vitals": vitals}, headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.json()["is_emergency"] is True
    assert r.json()["safety_triage"]["triage_level"] == "HIGH_RISK_EMERGENCY"
    assert r.json()["maternal_risk"]["confidence"] is None


@pytest.mark.asyncio
@pytest.mark.parametrize("payload,emergency", [
    ({"vitals": {}}, False),
    ({"vitals": {"systolic_bp": 180}}, True),
    ({"vitals": {}, "symptoms": [{"name": "convulsions", "severity": "severe"}]}, True),
    ({"vitals": VITALS, "symptoms": ["Severe headache"]}, True),
])
async def test_missing_and_symptoms(async_client, auth_headers, patient_id, payload, emergency):
    r = await async_client.post("/api/risks/assess", json={"patient_id": patient_id, **payload}, headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.json()["is_emergency"] is emergency
    if not payload["vitals"]:
        assert r.json()["status"] == "incomplete"
        assert "normal" not in " ".join(r.json()["safety_triage"]["clinical_rationale"]).lower() or r.json()["is_emergency"]


@pytest.mark.asyncio
@pytest.mark.parametrize("vitals", [{"SystolicBP": "invalid"}, {"systolic_bp": True}, {"systolic_bp": 999}, {"blood_sugar": 100}, {"temperature": 37, "temperature_unit": "Kelvin"}, {"systolic_bp": 120, "SystolicBP": 180}])
async def test_invalid_inputs_never_persist(async_client, auth_headers, patient_id, vitals):
    r = await async_client.post("/api/risks/assess", json={"patient_id": patient_id, "vitals": vitals}, headers=auth_headers)
    assert r.status_code == 422
    async with TestSessionLocal() as db:
        assert await db.scalar(select(func.count()).select_from(CaseRecord)) == 0


@pytest.mark.asyncio
async def test_missing_patient_and_invalid_referral(async_client, auth_headers):
    assert (await async_client.post("/api/risks/assess", json={"patient_id": "absent", "vitals": VITALS}, headers=auth_headers)).status_code == 404
    assert (await async_client.post("/api/referrals", json={"patient_id": "absent", "facility_name": "Synthetic", "urgency_level": "nonsense"}, headers=auth_headers)).status_code == 422
    assert (await async_client.post("/api/referrals", json={"patient_id": "absent", "facility_name": "Synthetic"}, headers=auth_headers)).status_code == 404


@pytest.mark.asyncio
async def test_persistence_idempotency_review_and_resume(async_client, auth_headers, patient_id):
    case_id = str(uuid.uuid4())
    payload = {"patient_id": patient_id, "case_id": case_id, "vitals": VITALS}
    first = await async_client.post("/api/risks/assess", json=payload, headers=auth_headers)
    assert first.status_code == 200, first.text
    assert (await async_client.post("/api/risks/assess", json=payload, headers=auth_headers)).json() == first.json()
    assert (await async_client.post("/api/risks/assess", json={**payload, "vitals": {**VITALS, "HeartRate": 90}}, headers=auth_headers)).status_code == 409
    run_payload = {"patient_id": patient_id, "case_id": case_id}
    run = await async_client.post("/api/agents/run", json=run_payload, headers=auth_headers)
    assert run.status_code == 200, run.text
    assert run.json()["status"] == "pending_review"
    assert run.json()["result"]["communication_result"]["status"] == "not_sent"
    assert (await async_client.post("/api/agents/run", json=run_payload, headers=auth_headers)).json() == run.json()
    async with TestSessionLocal() as db:
        assert await db.scalar(select(func.count()).select_from(ClinicalRecord)) == 1
        assert await db.scalar(select(func.count()).select_from(AgentStateRecord)) == 1
        assert await db.scalar(select(func.count()).select_from(Referral)) == 0
        assert await db.scalar(select(func.count()).select_from(AuditLog)) > 3
    assert (await async_client.post(f"/api/agents/cases/{case_id}/resume", headers=auth_headers)).status_code == 409
    decision = {"decision": "approved", "notes": "Synthetic review", "create_referral": True, "facility_name": "Synthetic verified facility", "urgency": "urgent"}
    reviewed = await async_client.post(f"/api/agents/cases/{case_id}/review", json=decision, headers=auth_headers)
    assert reviewed.status_code == 200, reviewed.text
    assert (await async_client.post(f"/api/agents/cases/{case_id}/review", json=decision, headers=auth_headers)).status_code == 409
    assert (await async_client.post(f"/api/agents/cases/{case_id}/resume", headers=auth_headers)).json()["status"] == "completed"
    saved = (await async_client.get(f"/api/risks/{case_id}", headers=auth_headers)).json()
    assert saved["reviewed_by"] == "test-admin" and saved["reviewed_at"]
    referral_id = reviewed.json()["referral_id"]
    assert (await async_client.put(f"/api/referrals/{referral_id}/status", json={"status": "nonsense"}, headers=auth_headers)).status_code == 422
    assert (await async_client.put(f"/api/referrals/{referral_id}/status", json={"status": "completed"}, headers=auth_headers)).status_code == 409
    for status in ("accepted", "in_transit", "completed"):
        assert (await async_client.put(f"/api/referrals/{referral_id}/status", json={"status": status}, headers=auth_headers)).status_code == 200


@pytest.mark.asyncio
async def test_failed_graph_persisted_truthfully(async_client, auth_headers, patient_id, monkeypatch):
    from backend.agents.orchestrator import NODES
    async def failing(state):
        raise RuntimeError("Synthetic failure")
    monkeypatch.setitem(NODES, "data_quality", failing)
    payload = {"patient_id": patient_id, "case_id": "failure-case", "vitals": VITALS}
    r = await async_client.post("/api/agents/run", json=payload, headers=auth_headers)
    assert r.status_code == 500, r.text
    assert r.json()["status"] == "failed"
    async with TestSessionLocal() as db:
        case = await db.get(CaseRecord, "failure-case")
        assert case.status == "failed"
        assert (await db.scalar(select(AgentStateRecord))).is_complete is False
    assert (await async_client.post("/api/agents/run", json=payload, headers=auth_headers)).status_code == 500


@pytest.mark.asyncio
async def test_analytics_and_audit_filters(async_client, auth_headers, patient_id):
    async with TestSessionLocal() as db:
        for label in ["high risk", "mid risk", "low risk", None]:
            db.add(ClinicalRecord(patient_id=patient_id, maternal_risk_level=label))
        db.add(AuditLog(agent_name="synthetic", action="older", timestamp=datetime(2020, 1, 1)))
        db.add(AuditLog(agent_name="synthetic", action="newer", timestamp=datetime(2026, 10, 9)))
        await db.commit()
    dashboard = (await async_client.get("/api/analytics/dashboard", headers=auth_headers)).json()
    assert dashboard["risk_distribution"] == {"high": 1, "medium": 1, "low": 1, "unknown": 1}
    assert dashboard["total_assessments"] == 4 and dashboard["recent_cases"] == 4
    logs = (await async_client.get("/api/audit/logs", params={"agent_name": "synthetic", "date_from": "2026-01-01", "limit": 1}, headers=auth_headers)).json()
    assert logs["total"] == 1 and logs["logs"][0]["action"] == "newer"


@pytest.mark.asyncio
async def test_empty_audit_truthful(async_client, auth_headers):
    r = await async_client.get("/api/audit/logs", headers=auth_headers)
    assert r.json()["logs"] == []


@pytest.mark.asyncio
async def test_alerts_acknowledge_and_no_live_message(async_client, auth_headers, patient_id, monkeypatch):
    r = await async_client.post("/api/risks/assess", json={"patient_id": patient_id, "case_id": "alert-case", "vitals": {"systolic_bp": 180}}, headers=auth_headers)
    assert r.status_code == 200
    alerts = (await async_client.get("/api/alerts", headers=auth_headers)).json()
    assert len(alerts) == 1 and alerts[0]["status"] == "not_sent"
    r = await async_client.post(f"/api/alerts/{alerts[0]['alert_id']}/acknowledge", headers=auth_headers)
    assert r.json()["acknowledged"] is True
    from backend.integrations.messaging_client import MessagingClient
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    assert (await MessagingClient().send_sms("synthetic", "synthetic"))["status"] == "unavailable"
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    result = await MessagingClient().send_whatsapp("synthetic", "synthetic")
    assert result["status"] == "simulated" and result["sent_at"] is None


@pytest.mark.asyncio
async def test_preferences_persist(async_client, auth_headers):
    preferences = {"language": "ur", "email_notifications": False, "sms_notifications": False}
    assert (await async_client.put("/api/auth/preferences", json=preferences, headers=auth_headers)).status_code == 200
    assert (await async_client.get("/api/auth/preferences", headers=auth_headers)).json() == preferences


@pytest.mark.asyncio
async def test_login_rate_limit(async_client):
    for _ in range(10):
        assert (await async_client.post("/api/auth/login", data={"username": "missing", "password": "bad"})).status_code == 401
    assert (await async_client.post("/api/auth/login", data={"username": "missing", "password": "bad"})).status_code == 429
