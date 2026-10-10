"""Verify two bilingual reports on the running app with clearly synthetic, public test inputs."""
import argparse
import json
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ui.api_client import APIClient
from backend.services.bilingual_reports import report_html

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--live-providers',action='store_true',help='Use consented synthetic measurements and public Peshawar coordinates with configured Groq/OSM/road providers')
    args=parser.parse_args()
    anon=APIClient();health=anon.request('GET','/health');assert health['demo_mode'] is False
    username='report-check-'+uuid.uuid4().hex[:8]
    anon.request('POST','/auth/signup',json={'username':username,'password':'Local-Verification-2026!','full_name':'Bilingual report software verification'})
    token=anon.request('POST','/auth/login',data={'username':username,'password':'Local-Verification-2026!'})['access_token']
    client=APIClient(token)
    patient=client.request('POST','/patients',json={'name':'Synthetic report verification case','age':30,'gestational_age_weeks':28})
    ctg=json.loads((ROOT/'exports/data_test_pack/inputs/ctg_normal.json').read_text(encoding='utf-8'))
    payload={'patient_id':patient['patient_id'],'vitals':{'age':30,'gestational_age_weeks':28,'systolic_bp':120,'diastolic_bp':80,
      'heart_rate':80,'temperature_celsius':37,'blood_sugar_mmol_l':6},'ctg_features':ctg,'ctg_source':'uci_measured','provenance':'patient_reported',
      'location':{'latitude':34.01,'longitude':71.53,'source':'manual','share_for_discovery':args.live_providers,'share_for_routing':args.live_providers},
      'allow_llm_processing':args.live_providers,'encounter':{'storage_consent':True,'notification_consent':False,'dating_source':'ultrasound',
        'previous_pregnancies':2,'previous_births':1,'movements_started':True,'movements_reduced':False,'preferred_language':'ur','run_research_models':True,
        'measurement_taken_at':'2026-10-10T12:00:00+05:00','glucose_test_type':'random',
        'gestation_labs':{'bmi':25,'skin_thickness_mm':20,'insulin_mu_ml':100,'diabetes_pedigree_function':.3},
        'appointment_research':{'scholarship':False,'hypertension':False,'diabetes':False,'alcoholism':False,'handicap_code':0,'sms_received':False}},
      'followup':{'gestational_age_weeks':28,'completed_contact_weeks':[12,20,26],'next_appointment_date':'2026-10-17','booking_date':'2026-10-10','last_completed_checkup_date':'2026-09-26','reminder_actually_sent':False}}
    result=client.request('POST','/care/assess',json=payload)['result']
    assert not result['errors'] and len({e['agent'] for e in result['audit_trail']})==9
    assert all(r['status']=='research_prediction' for r in result['research_results'].values()),result['research_results']
    ai=result['clinician_result']['ai_assistance']
    if args.live_providers:assert ai['status']=='generated',ai
    reports=result['reporting_result']['reports']
    assert set(reports)=={'care','referral'}
    destination=ROOT/'exports/bilingual_reports';destination.mkdir(parents=True,exist_ok=True)
    for kind,report in reports.items():
        assert set(report['languages'])=={'en','ur'}
        if args.live_providers:assert report['llm_generated'] is True
        (destination/(kind+'-report.html')).write_text(report_html(report),encoding='utf-8')
        for lang in ('en','ur'):
            (destination/(kind+'-report-'+lang+'.txt')).write_text(report['languages'][lang]['text'],encoding='utf-8')
    saved=client.request('GET','/agents/cases/'+result['case_id'])
    assert saved['result']['reporting_result']['reports']==reports
    facs=result['referral_result'].get('ranked_facilities',[])
    proof={'tested_at':datetime.now(timezone.utc).isoformat(),'account':username,'case_id':result['case_id'],
       'test_inputs':'Synthetic software inputs and selected measured dataset CTG row; public Peshawar coordinates, not actual user GPS',
       'case_saved':True,'nine_agents':True,'two_reports':True,'report_languages':['English','Urdu script'],
       'groq_status':ai['status'],'research_models':{name:r['status'] for name,r in result['research_results'].items()},
       'maternal_model':result['clinical_risk_result']['maternal_risk']['status'],'fetal_model':result['fetal_result']['status'],
       'hospital_count':len(facs),'road_routes':sum(f.get('distance_kind')=='road' for f in facs),
       'coverage_limited':result['referral_result'].get('coverage_limited'),'coverage_radius_km':result['referral_result'].get('coverage_radius_km'),
       'sample_report_dir':str(destination)}
    (ROOT/'docs/bilingual-report-verification.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
    print(json.dumps(proof,indent=2))
if __name__=='__main__':main()
