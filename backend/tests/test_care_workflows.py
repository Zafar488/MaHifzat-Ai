"""Regression scenarios for all four care workflows and integration failures."""
import json
from datetime import date, datetime, timezone, timedelta
import httpx
import pytest
from pydantic import ValidationError
from backend.config import settings
from backend.schemas.assessment import WorkflowRequest
from backend.schemas.clinical import ClinicalInput
from backend.services.followup import plan_followup
from backend.services.referral_planner import plan_referral
from backend.integrations.facility_locator import haversine_km, FacilityLocatorClient
from backend.integrations.routing_client import RoutingClient
from backend.tests.conftest import login_as
from backend.tests.test_api import VITALS

def test_canonical_temperature_never_guesses_units():
    with pytest.raises(ValidationError):
        ClinicalInput.model_validate({"temperature_celsius": 98.6})
    assert ClinicalInput.model_validate({"BodyTemp":98.6}).temperature_celsius == pytest.approx(37)

def test_anc_operational_actions_and_schedule():
    today = date(2026,10,10)
    routine = plan_followup({"gestational_age_weeks":28,"completed_contact_weeks":[12,20,26]}, today=today)
    assert routine["recommended_action"] == "reminder"
    assert routine["next_appointment_date"] == "2026-10-24"
    assert routine["next_reminder_date"] == "2026-10-23"
    call = plan_followup({"next_appointment_date":"2026-10-05"},today=today)
    assert call["recommended_action"] == "call" and call["overdue_days"] == 5
    visit = plan_followup({"missed_visits":2,"transport_barrier":True},today=today)
    assert visit["recommended_action"] == "home_visit" and visit["priority"] == "high"
    assert visit["missed_risk_score"] is None
    assert plan_followup({},today=today)["recommended_action"] == "schedule_contact"
    assert plan_followup({},urgency="emergency",today=today)["recommended_action"] == "emergency_assessment"

def test_invalid_followup_and_ctg_rejected():
    with pytest.raises(ValidationError):
        WorkflowRequest(patient_id="synthetic", followup={"gestational_age_weeks":20,"completed_contact_weeks":[26]})
    with pytest.raises(ValidationError):
        WorkflowRequest(patient_id="synthetic", ctg_features={"AC":True})
    with pytest.raises(ValidationError):
        WorkflowRequest(patient_id="synthetic", location={"latitude":100,"longitude":71})
    with pytest.raises(ValidationError):
        WorkflowRequest(patient_id="synthetic", ctg_features={"AC":12})

def test_distance_known_reference():
    assert haversine_km((0,0),(0,0)) == 0
    assert haversine_km((0,0),(0,1)) == pytest.approx(111.195,abs=.01)

@pytest.mark.asyncio
async def test_capabilities_before_proximity(monkeypatch):
    monkeypatch.setattr(settings,"DEMO_MODE",True)
    result = await plan_referral({"latitude":34.08,"longitude":71.39,"source":"demo"}, "emergency",
                                 {"fetal_status":"pathological"},demo=True)
    assert result["selected_facility"]["facility_id"] == "demo-newborn"
    assert len(result["excluded_facilities"]) == 2
    assert result["selected_facility"]["travel_time_minutes"] is None
    assert result["status"] == "simulated_candidate"
    assert result["selected_facility"]["directions_url"] is None

@pytest.mark.asyncio
async def test_facility_directory_validation_stale_and_availability(tmp_path,monkeypatch):
    now = datetime.now(timezone.utc)
    base = {"facility_id":"good","name":"Synthetic capable facility","latitude":34.1,"longitude":71.4,
            "has_emergency":True,"has_maternity":True,"source":"Synthetic test directory",
            "verified_at":now.date().isoformat(),"availability":"unavailable","availability_checked_at":now.isoformat()}
    stale = {**base,"facility_id":"stale","verified_at":(now.date()-timedelta(days=400)).isoformat()}
    path = tmp_path/"facilities.json"
    path.write_text(json.dumps({"facilities":[base,stale]}))
    monkeypatch.setattr(settings,"FACILITY_DIRECTORY_PATH",path)
    locator = FacilityLocatorClient()
    assert len(await locator.find_nearby_facilities(34.08,71.39)) == 1
    result = await plan_referral({"latitude":34.08,"longitude":71.39}, "emergency")
    assert result["status"] == "no_matching_facility"
    base["availability_checked_at"] = (now-timedelta(days=2)).isoformat()
    path.write_text(json.dumps({"facilities":[base]}))
    result = await plan_referral({"latitude":34.08,"longitude":71.39}, "emergency")
    assert result["selected_facility"]["availability"] == "unknown"
    assert result["selected_facility"]["requires_availability_confirmation"]
    path.write_text("{broken")
    assert await FacilityLocatorClient().find_nearby_facilities(34.08,71.39) == []

@pytest.mark.asyncio
async def test_route_consent_timeout_and_valid_units(monkeypatch):
    monkeypatch.setattr(settings,"OPENROUTESERVICE_API_KEY","synthetic-key")
    calls = []
    async def post(self,url,**kwargs):
        calls.append(kwargs["json"])
        return httpx.Response(200,request=httpx.Request("POST",url),json={"features":[{"properties":{"summary":{"distance":12500,"duration":1800}},
                  "geometry":{"coordinates":[[71.39,34.08],[71.55,34.01]]}}]})
    monkeypatch.setattr(httpx.AsyncClient,"post",post)
    client = RoutingClient()
    assert (await client.get_route((34.08,71.39),(34.01,71.55)))["travel_time_minutes"] is None
    assert calls == []
    route = await client.get_route((34.08,71.39),(34.01,71.55),consent=True)
    assert route["distance_km"] == 12.5 and route["travel_time_minutes"] == 30
    assert calls[0]["coordinates"] == [[71.39,34.08],[71.55,34.01]]
    async def timeout(*args,**kwargs):
        raise httpx.ReadTimeout("Synthetic timeout")
    monkeypatch.setattr(httpx.AsyncClient,"post",timeout)
    route = await client.get_route((34.08,71.39),(34.01,71.55),consent=True)
    assert route["status"] == "provider_failed" and route["travel_time_minutes"] is None

@pytest.mark.asyncio
async def test_nine_agents_handover_persistence_and_task_scoping(async_client,auth_headers,patient_id,monkeypatch):
    monkeypatch.setattr(settings,"DEMO_MODE",True)
    payload = {"patient_id":patient_id,"case_id":"care-demo","vitals":{**VITALS,"SystolicBP":180,"DiastolicBP":120},
               "provenance":"demo","location":{"latitude":34.08,"longitude":71.39,"source":"demo"},
               "followup":{"gestational_age_weeks":34,"completed_contact_weeks":[12,20],"missed_visits":2}}
    response = await async_client.post("/api/agents/run",json=payload,headers=auth_headers)
    assert response.status_code == 200,response.text
    result = response.json()["result"]
    assert len({e["agent"] for e in result["audit_trail"]}) == 9
    assert result["referral_result"]["selected_facility"]["has_emergency"]
    text = result["clinician_result"]["case_summary_text"]
    assert "Systolic BP: 180 mmHg" in text and "Temperature: 37 C" in text and "SIMULATED FACILITY" in text
    assert result["communication_result"]["messages_sent"] == 0
    assert (await async_client.post("/api/agents/run",json=payload,headers=auth_headers)).json() == response.json()
    tasks = (await async_client.get("/api/followups",headers=auth_headers)).json()
    assert len(tasks) == 1 and tasks[0]["action"] == "emergency_assessment"
    saved = (await async_client.get("/api/agents/cases/care-demo",headers=auth_headers)).json()
    assert saved["result"]["reporting_result"]["narrative"] == text
    stranger = await login_as(async_client,"patient")
    assert (await async_client.get("/api/followups",headers=stranger)).json() == []
    assert (await async_client.get("/api/agents/cases/care-demo",headers=stranger)).status_code == 404
    assert (await async_client.post("/api/facilities/search",json={"patient_id":patient_id,"location":payload["location"],"demo":True},headers=stranger)).status_code == 404
    conflict={**payload,"location":{"latitude":34.2,"longitude":71.6,"source":"demo"}}
    assert (await async_client.post("/api/agents/run",json=conflict,headers=auth_headers)).status_code == 409
    review={"decision":"approved","notes":"Synthetic clinician review"}
    assert (await async_client.post("/api/agents/cases/care-demo/review",json=review,headers=auth_headers)).status_code == 200
    resumed=await async_client.post("/api/agents/cases/care-demo/resume",headers=auth_headers)
    assert resumed.status_code == 200
    assert resumed.json()["result"]["clinician_result"]["case_summary_text"] == text
    assert resumed.json()["result"]["reporting_result"]["narrative"] == text
    assert resumed.json()["result"]["communication_result"]["messages_sent"] == 0
    task_id=tasks[0]["id"]
    changed = await async_client.put("/api/followups/"+task_id,json={"status":"completed","notes":"Synthetic worker follow-up"},headers=auth_headers)
    assert changed.status_code == 200
    assert (await async_client.put("/api/followups/"+task_id,json={"status":"completed","notes":"Duplicate"},headers=auth_headers)).status_code == 409

@pytest.mark.asyncio
async def test_fetal_pathological_escalates_assessment_and_alert(async_client,auth_headers,patient_id,monkeypatch):
    from backend.services.inference import ModelRegistry, CTG_FEATURES
    registry = ModelRegistry()
    monkeypatch.setattr(registry,"predict_fetal_health", lambda f: {"fetal_status":"pathological","status":"experimental","model_available":True,"probabilities":{},"confidence":None})
    features = dict(zip(CTG_FEATURES,registry._models["fetalwatch"]["known_input"]))
    response = await async_client.post("/api/risks/assess",json={"patient_id":patient_id,"vitals":VITALS,"ctg_features":features,"ctg_source":"uci_measured"},headers=auth_headers)
    assert response.status_code == 200,response.text
    assert response.json()["is_emergency"] is True and response.json()["urgency_level"] == "emergency"
    assert response.json()["safety_triage"]["is_emergency"] is False
    assert len((await async_client.get("/api/alerts",headers=auth_headers)).json()) == 1

@pytest.mark.asyncio
async def test_demo_location_cannot_enter_measured_case(async_client,auth_headers,patient_id):
    response = await async_client.post("/api/agents/run",json={"patient_id":patient_id,"vitals":VITALS,
               "location":{"latitude":34.08,"longitude":71.39,"source":"demo"}},headers=auth_headers)
    assert response.status_code == 422
