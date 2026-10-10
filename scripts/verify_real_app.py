"""Create a labelled local verification account; optional live calls use public/synthetic inputs only."""
import argparse
import json
import sys
import uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ui.api_client import APIClient

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--live-providers",action="store_true",help="Use public coordinates and synthetic de-identified inputs with configured providers")
    args=parser.parse_args()
    anonymous=APIClient()
    health=anonymous.request("GET","/health")
    assert health["demo_mode"] is False
    username="verification-"+uuid.uuid4().hex[:10]
    password="Local-Verification-2026!"
    anonymous.request("POST","/auth/signup",json={"username":username,"password":password,"full_name":"Software verification account"})
    token=anonymous.request("POST","/auth/login",data={"username":username,"password":password})["access_token"]
    client=APIClient(token)
    user=client.request("GET","/auth/me")
    assert user["role"]=="patient"
    patient=client.request("POST","/patients",json={"name":"Software verification observations","age":30,"gestational_age_weeks":28,"location":"Public Peshawar test point; not user GPS"})
    models=client.request("GET","/models/catalog")["models"]
    executions={}
    for model in models:
        result=client.request("POST","/models/predict",json={"model":model["name"],"features":model["example"]})
        assert result.get("probabilities") and abs(sum(result["probabilities"].values())-1)<1e-6
        executions[model["name"]]=result["status"]
    location={"latitude":34.01,"longitude":71.53,"source":"manual","share_for_discovery":args.live_providers,"share_for_routing":args.live_providers}
    response=client.request("POST","/care/assess",json={"patient_id":patient["patient_id"],"vitals":{"age":30,"gestational_age_weeks":28,"systolic_bp":120,"diastolic_bp":80,"heart_rate":80,"temperature_celsius":37,"blood_sugar_mmol_l":6},"provenance":"patient_reported","location":location,"allow_llm_processing":args.live_providers,"followup":{"gestational_age_weeks":28,"completed_contact_weeks":[12,20],"missed_visits":3,"transport_barrier":True,"phone_access":False}})
    result=response["result"]
    assert len({event["agent"] for event in result["audit_trail"]})==9
    assert not result.get("errors"),result.get("errors")
    assert result["anc_result"]["recommended_action"]=="home_visit"
    saved=client.request("GET","/agents/cases/"+result["case_id"])
    assert saved["result"]==result
    assert client.request("GET","/followups")
    hospitals=client.request("POST","/facilities/nearby",json={"location":location,"radius_km":25}) if args.live_providers else None
    proof={"account":username,"test_inputs":"Synthetic software-verification observations; public test point, no actual user GPS","demo_mode":False,"models":executions,"case_id":result["case_id"],"nine_agents":True,"case_saved":True,"followup_action":result["anc_result"]["recommended_action"],"groq_status":result["clinician_result"]["ai_assistance"]["status"],"referral_status":result["referral_result"]["status"],"hospital_search":{k:hospitals.get(k) for k in ("status","provider","coverage_limited","coverage_radius_km")} if hospitals else None,"hospital_count":len(hospitals["facilities"]) if hospitals else None}
    (ROOT/"docs/real_app_verification.json").write_text(json.dumps(proof,indent=2),encoding="utf-8")
    print(json.dumps(proof,indent=2))
if __name__=="__main__":main()
