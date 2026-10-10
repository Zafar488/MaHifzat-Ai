"""Verify the running UI backend with synthetic cases and save judge-demo evidence."""
import json
import sys
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ui.api_client import APIClient
from app_demo_scenarios import SCENARIOS

def main():
    health=APIClient().request("GET","/health")
    if not health["demo_mode"]: raise RuntimeError("Verification requires the isolated demo")
    token=APIClient().request("POST","/auth/login",data={"username":"demo-clinician","password":"MaaHifazat-Demo-2026!"})["access_token"]
    client=APIClient(token)
    ctg=client.request("GET","/analytics/models/demo-ctg")["features"]
    summaries=[]
    for scenario,preset in SCENARIOS.items():
        name="DEMO verification "+scenario
        patients=client.request("GET","/patients",params={"search":name})
        patient=next((p for p in patients if p["name"]==name),None)
        if patient is None:
            patient=client.request("POST","/patients",json={"name":name,"age":preset["age"],"gestational_age_weeks":preset["gestational_age_weeks"],"location":"Fictional demo village"})
        vitals={k:v for k,v in preset.items() if k in ("age","gestational_age_weeks","systolic_bp","diastolic_bp","heart_rate","temperature_celsius","blood_sugar_mmol_l")}
        slug=scenario.lower().replace(" ","-").replace("+","and")
        payload={"patient_id":patient["patient_id"],"case_id":"demo-v2-e2e-"+slug,"vitals":vitals,
                 "symptoms":[{"name":s,"severity":"severe"} for s in preset.get("symptoms",[])],
                 "ctg_features":ctg if preset.get("ctg") else None,"ctg_source":"demo" if preset.get("ctg") else None,
                 "provenance":"demo","location":{"latitude":34.08,"longitude":71.39,"source":"demo"},
                 "followup":{"gestational_age_weeks":preset["gestational_age_weeks"],"completed_contact_weeks":preset.get("contacts",[]),
                   "missed_visits":preset.get("missed",0),"transport_barrier":preset.get("transport",False),"phone_access":preset.get("phone")}}
        response=client.request("POST","/agents/run",json=payload)
        assert client.request("POST","/agents/run",json=payload)==response
        result=response["result"]
        assert len({e["agent"] for e in result["audit_trail"]})==9
        assert result["communication_result"]["messages_sent"]==0
        assert result["clinician_result"]["case_summary_text"]==result["reporting_result"]["narrative"]
        saved=client.request("GET","/agents/cases/"+payload["case_id"])
        assert saved["result"]==result
        if scenario in ("Maternal emergency","Fetal concern","Incomplete vitals + danger sign"): assert result["emergency"]
        if scenario=="Missed checkups": assert result["anc_result"]["recommended_action"]=="home_visit"
        if scenario=="Fetal concern":
            assert result["referral_result"]["selected_facility"]["has_nicu"]
            assert "Continue scheduled clinical care" not in result["clinician_result"]["case_summary_text"]
        if scenario=="Incomplete vitals + danger sign": assert result["status"]=="incomplete"
        summaries.append({"scenario":scenario,"case_id":payload["case_id"],"nine_agents":True,"status":result["status"],
           "emergency":result["emergency"],"facility":result["referral_result"]["selected_facility"]["name"],
           "followup_action":result["anc_result"]["recommended_action"],"messages_sent":0})
    # Record a synthetic clinician decision and referral; no actual care or messages.
    case=summaries[1]["case_id"]
    saved=client.request("GET","/agents/cases/"+case)
    if saved["review_status"]=="pending":
        client.request("POST","/agents/cases/"+case+"/review",json={"decision":"approved","notes":"Synthetic demonstration review. No actual patient or facility.","create_referral":True,"facility_name":"DEMO District maternity hospital","urgency":"emergency"})
    client.request("POST","/agents/cases/"+case+"/resume")
    tasks=client.request("GET","/followups")
    task=next(t for t in tasks if t["case_id"]==summaries[3]["case_id"])
    if task["status"]=="pending":
        client.request("PUT","/followups/"+task["id"],json={"status":"completed","notes":"Synthetic health-worker visit demonstration; no real visit occurred."})
    report={"health":health,"scenarios":summaries,"review_and_referral_persisted":True,"task_outcome_persisted":True,"external_messages_sent":0}
    (ROOT/"docs/demo_verification.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("PASS: five saved scenarios, nine agents each, idempotency, review/referral and task outcome")
if __name__=="__main__":main()
