"""Real app flows, external-consent boundaries and all five model contracts."""
import json
import httpx
import pytest
from backend.config import settings
from backend.integrations.osm_discovery import OSMDiscoveryClient,_CACHE
from backend.services.ai_assistant import explain_case
from backend.services.model_workbench import catalog,predict
from backend.services.hospital_search import discover_hospitals
from backend.tests.conftest import login_as
from backend.tests.test_api import VITALS
from ui.contact_actions import contact_links

@pytest.mark.asyncio
async def test_patient_self_care_runs_nine_nodes_with_ownership(async_client,patient_id):
    headers=await login_as(async_client,"patient")
    own=await async_client.post("/api/patients",json={"name":"Synthetic personal profile","age":30},headers=headers)
    assert own.status_code==201
    response=await async_client.post("/api/care/assess",json={"patient_id":own.json()["patient_id"],"vitals":VITALS,"provenance":"patient_reported"},headers=headers)
    assert response.status_code==200,response.text
    result=response.json()["result"]
    assert len({e["agent"] for e in result["audit_trail"]})==9
    assert result["clinician_result"]["ai_assistance"]["status"]=="not_requested"
    denied=await async_client.post("/api/care/assess",json={"patient_id":patient_id,"vitals":VITALS},headers=headers)
    assert denied.status_code==404
    assert (await async_client.post("/api/agents/run",json={"patient_id":own.json()["patient_id"],"vitals":VITALS},headers=headers)).status_code==403

@pytest.mark.asyncio
async def test_osm_consent_and_actual_map_tags(monkeypatch):
    _CACHE.clear()
    calls=[]
    async def post(self,url,**kwargs):
        calls.append(kwargs)
        return httpx.Response(200,request=httpx.Request("POST",url),json={"elements":[
          {"type":"node","id":123,"lat":34.011,"lon":71.531,"tags":{"name":"Synthetic map fixture","amenity":"hospital","emergency":"yes","healthcare:speciality":"gynaecology;neonatology"}},
          {"type":"way","id":456,"center":{"lat":34.02,"lon":71.54},"tags":{"name":"Second fixture"}},
          {"type":"node","id":789,"lat":999,"lon":71.54,"tags":{}}
        ]})
    monkeypatch.setattr(httpx.AsyncClient,"post",post)
    point={"latitude":34.01,"longitude":71.53}
    denied=await OSMDiscoveryClient().search(point)
    assert denied["status"]=="consent_required" and not calls
    result=await OSMDiscoveryClient().search({**point,"share_for_discovery":True})
    assert result["status"]=="ok" and len(result["facilities"])==2
    first=result["facilities"][0]
    assert first["reported_services"]=={"has_emergency":True,"has_maternity":True,"has_nicu":None}
    assert first["capabilities_verified"] is False and first["availability"]=="unknown"
    assert first["distance_m"]>0 and first["source_url"].endswith("/node/123")
    assert "around:25000,34.01,71.53" in calls[0]["data"]["data"]
    assert (await OSMDiscoveryClient().search({**point,"share_for_discovery":True}))["cached"]
    assert len(calls)==1

@pytest.mark.asyncio
async def test_osm_failure_has_no_fictional_fallback(monkeypatch):
    _CACHE.clear()
    async def post(*args,**kwargs):raise httpx.ReadTimeout("Synthetic timeout")
    monkeypatch.setattr(httpx.AsyncClient,"post",post)
    monkeypatch.setattr(httpx.AsyncClient,"get",post)
    result=await OSMDiscoveryClient().search({"latitude":34.01,"longitude":71.53,"share_for_discovery":True})
    assert result["status"]=="provider_unavailable" and result["facilities"]==[]

@pytest.mark.asyncio
async def test_discovery_routes_do_not_mutate_shared_cache(monkeypatch):
    row={"facility_id":"fixture","latitude":34.02,"longitude":71.54,"distance_km":1,"distance_m":1000,"distance_kind":"straight_line"}
    from backend.integrations.routing_client import RoutingClient
    async def search(*args,**kwargs):return {"facilities":[row],"status":"ok"}
    async def route(*args,**kwargs):return {"distance_km":2,"distance_kind":"road","travel_time_minutes":5}
    monkeypatch.setattr(OSMDiscoveryClient,"search",search)
    monkeypatch.setattr(RoutingClient,"get_route",route)
    result=await discover_hospitals({"latitude":34.01,"longitude":71.53,"share_for_discovery":True,"share_for_routing":True})
    assert result["facilities"][0]["distance_kind"]=="road"
    assert row["distance_kind"]=="straight_line" and row["distance_km"]==1

def ai_state():
    return {"patient_id":"PRIVATE-ID","case_id":"PRIVATE-CASE","phone":"PRIVATE-PHONE","name":"PRIVATE-NAME",
        "location":{"latitude":34.123456,"longitude":71.987654},"allow_llm_processing":True,
        "vitals":{"age":30},"symptoms":[{"name":"PRIVATE-NAME PRIVATE-PHONE PRIVATE-ID 03001234567","severity":"mild"}],"missing_fields":["systolic_bp"],
        "clinical_risk_result":{"who_red_flags":{"is_emergency":False,"triage_level":"INSUFFICIENT_DATA"},
           "maternal_risk":{"risk_level":"unknown"}}}

def valid_ai(urgency="routine"):
    return {"urgency":urgency,"explanation_roman_urdu":"Blood pressure record karein aur maternity team se rabta karein.",
      "clinician_context":"Missing measured blood pressure; review is needed.",
      "followup_questions":["Aapka measured blood pressure kya hai?"],"facts_used":["Blood pressure missing"],
      "care_explanation_english":"Collect missing blood pressure and arrange clinician review.",
      "care_explanation_urdu":"بلڈ پریشر درج کریں اور معالج سے رابطہ کریں۔",
      "referral_explanation_english":"No selected hospital; record location and confirm services.",
      "referral_explanation_urdu":"ہسپتال منتخب نہیں؛ مقام درج کریں اور خدمات کی تصدیق کریں۔"}

@pytest.mark.asyncio
async def test_groq_consent_and_minimum_payload(monkeypatch):
    monkeypatch.setattr(settings,"ENABLE_LLM",True)
    monkeypatch.setattr(settings,"GROQ_API_KEY","synthetic-key")
    calls=[]
    async def post(self,url,**kwargs):
        calls.append(kwargs["json"])
        return httpx.Response(200,request=httpx.Request("POST",url),json={"choices":[{"message":{"content":json.dumps(valid_ai())}}]})
    monkeypatch.setattr(httpx.AsyncClient,"post",post)
    denied=await explain_case({**ai_state(),"allow_llm_processing":False})
    assert denied["status"]=="not_requested" and not calls
    result=await explain_case(ai_state())
    assert result["llm_generated"] is True
    payload=json.dumps(calls[0]["messages"])
    assert not any(value in payload for value in ("PRIVATE-ID","PRIVATE-CASE","PRIVATE-PHONE","PRIVATE-NAME","34.123456","71.987654","03001234567"))
    assert calls[0]["response_format"]=={"type":"json_object"}

@pytest.mark.asyncio
@pytest.mark.parametrize("content",[json.dumps(valid_ai("emergency")),"broken-json"])
async def test_groq_invalid_output_falls_back_without_changing_care(monkeypatch,content):
    monkeypatch.setattr(settings,"ENABLE_LLM",True)
    monkeypatch.setattr(settings,"GROQ_API_KEY","synthetic-key")
    async def post(self,url,**kwargs):
        return httpx.Response(200,request=httpx.Request("POST",url),json={"choices":[{"message":{"content":content}}]})
    monkeypatch.setattr(httpx.AsyncClient,"post",post)
    result=await explain_case(ai_state())
    assert result["status"]=="provider_failed" and result["llm_generated"] is False and result["urgency"]=="routine"

def test_five_models_execute_actual_contracts():
    from backend.services.inference import ModelRegistry
    ModelRegistry().load_all()
    entries=catalog()
    assert len(entries)==5 and all(e["executable"] for e in entries)
    for entry in entries:
        result=predict(entry["name"],entry["example"])
        assert result["status"] in ("experimental","research_prediction")
        assert result["probabilities"] and abs(sum(result["probabilities"].values())-1)<1e-6
    preterm=next(e for e in entries if e["name"]=="pretermguard")
    assert preterm["target"]=="CLASS" and preterm["care_decision_use"] is False

def test_free_contact_actions_are_explicit_composers():
    links=contact_links("0300 1234567","Care checkup & appointment")
    assert links["whatsapp"].startswith("https://wa.me/923001234567?text=")
    assert "%26" in links["sms"] and links["call"]=="tel:03001234567"
    assert contact_links("javascript:alert(1)","message") is None

@pytest.mark.asyncio
async def test_real_bounded_map_fallback_reports_partial_coverage(monkeypatch):
    _CACHE.clear()
    calls=[]
    async def post(*args,**kwargs):raise httpx.ReadTimeout("Synthetic provider timeout")
    async def get(self,url,**kwargs):
        calls.append(kwargs)
        return httpx.Response(200,request=httpx.Request("GET",url),json={"elements":[
            {"type":"node","id":1,"lat":34.01,"lon":71.53},
            {"type":"node","id":2,"lat":34.011,"lon":71.531},
            {"type":"way","id":3,"nodes":[1,2],"tags":{"amenity":"hospital","name":"Synthetic map geometry"}},
            {"type":"node","id":4,"lat":34.01,"lon":71.54,"tags":{"amenity":"school"}}]})
    monkeypatch.setattr(httpx.AsyncClient,"post",post)
    monkeypatch.setattr(httpx.AsyncClient,"get",get)
    result=await OSMDiscoveryClient().search({"latitude":34.01,"longitude":71.53,"share_for_discovery":True},25)
    assert result["status"]=="ok" and len(result["facilities"])==1
    assert result["coverage_limited"] and result["coverage_radius_km"]==2
    assert result["provider"]=="osm_bounded_map" and len(calls)==1
    assert result["facilities"][0]["source_url"].endswith("/way/3")
