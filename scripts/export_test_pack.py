"""Export source data/models and verified, ready-to-enter test inputs; no credentials or app DBs."""
import asyncio
import hashlib
import json
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import pandas as pd
from pydantic import ValidationError
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app_demo_scenarios import SCENARIOS
from backend.services.inference import ModelRegistry,CTG_FEATURES
from backend.services.model_workbench import catalog,predict
from backend.schemas.assessment import WorkflowRequest
from backend.agents.orchestrator import run_workflow
OUT=ROOT/'exports'/'data_test_pack'
OUT.mkdir(parents=True,exist_ok=True)
WRITTEN=[]
def write(relative,value):
    path=OUT/relative
    path.parent.mkdir(parents=True,exist_ok=True)
    text=json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False) if not isinstance(value,str) else value
    path.write_text(text,encoding='utf-8')
    WRITTEN.append((path,relative))
    return path

def ctg_examples(registry):
    frame=pd.read_parquet(ROOT/'data/uci_ctg.parquet')
    manifest=json.loads((ROOT/'artifacts/serving/fetalwatch/manifest.json').read_text(encoding='utf-8'))
    test=frame.iloc[manifest['test_indices']]
    features=test[CTG_FEATURES].astype(float)
    labels=registry._models['fetalwatch']['pipeline'].predict(features)
    examples={}
    for actual,label in ((1,'normal'),(2,'suspect'),(3,'pathological')):
        positions=[i for i,(y,p) in enumerate(zip(test.NSP,labels)) if int(y)==actual and str(p)==label]
        if not positions:raise RuntimeError('No usable held-out '+label+' example')
        row=features.iloc[positions[0]].to_dict()
        examples[label]=row
        write('inputs/ctg_'+label+'.json',row)
        write('inputs/ctg_'+label+'_source.json',{'dataset':'uci_ctg.parquet','source_row_index':int(test.index[positions[0]]),
            'ground_truth_NSP':actual,'ground_truth_label':label,'model_prediction':registry.predict_fetal_health(row),
            'selection':'Correctly classified saved holdout row, selected for functional testing only; not a new accuracy evaluation.'})
    return examples

async def scenarios(examples):
    presets=deepcopy(SCENARIOS)
    presets['Urgent BP']={**presets['Routine ANC'],'age':30,'systolic_bp':145,'diastolic_bp':95}
    presets['Fetal suspect']={**presets['Fetal concern'],'ctg_label':'suspect'}
    expected={
        'Routine ANC':('LOW_RISK',False,'reminder','pending_review'),
        'Maternal emergency':('HIGH_RISK_EMERGENCY',True,'emergency_assessment','pending_review'),
        'Fetal concern':('LOW_RISK',True,'emergency_assessment','pending_review'),
        'Missed checkups':('LOW_RISK',False,'home_visit','pending_review'),
        'Incomplete vitals + danger sign':('HIGH_RISK_EMERGENCY',True,'emergency_assessment','incomplete'),
        'Urgent BP':('URGENT',False,'call','pending_review'),
        'Fetal suspect':('LOW_RISK',False,'call','pending_review')}
    cases=[]
    checks=[]
    for name,preset in presets.items():
        slug=name.lower().replace(' + ','_').replace(' ','_')
        vitals={k:preset[k] for k in ('age','systolic_bp','diastolic_bp','heart_rate','temperature_celsius','blood_sugar_mmol_l','gestational_age_weeks') if k in preset}
        ctg=examples[preset.get('ctg_label','pathological')] if preset.get('ctg') else None
        payload={'patient_id':'REPLACE_WITH_YOUR_OWN_PATIENT_ID','vitals':vitals,
            'symptoms':[{'name':s,'severity':'severe'} for s in preset.get('symptoms',[])],
            'ctg_features':ctg,'ctg_source':'uci_measured' if ctg else None,'provenance':'patient_reported',
            'location':{'latitude':34.01,'longitude':71.53,'source':'manual','share_for_discovery':False,'share_for_routing':False},
            'allow_llm_processing':False,'followup':{'gestational_age_weeks':preset['gestational_age_weeks'],
                'completed_contact_weeks':preset.get('contacts',[]),'missed_visits':preset.get('missed',0),
                'transport_barrier':preset.get('transport',False),'phone_access':preset.get('phone')}}
        WorkflowRequest.model_validate(payload)
        state={'patient_id':'software-verification','case_id':'pack-'+slug,'vitals':vitals,'symptoms':payload['symptoms'],
            'ctg_data':ctg,'location':payload['location'],'followup':payload['followup'],'provenance':'patient_reported',
            'allow_llm_processing':False,'demographics':{'age':preset['age'],'gestational_age_weeks':preset['gestational_age_weeks']},
            'language':'en','channel':'app','audit_trail':[],'errors':[],'messages':[]}
        result=await run_workflow(state)
        rule=result['clinical_risk_result']['who_red_flags']['triage_level']
        action=result['anc_result']['recommended_action']
        actual=(rule,result['emergency'],action,result['status'])
        assert actual==expected[name],(name,actual,expected[name])
        assert len({e['agent'] for e in result['audit_trail']})==9 and not result['errors']
        if ctg:assert result['fetal_result']['fetal_status']==preset.get('ctg_label','pathological')
        check={'scenario':name,'passed':True,'rule_triage':rule,'emergency':result['emergency'],'status':result['status'],
             'followup_action':action,'maternal_prediction':result['clinical_risk_result']['maternal_risk']['risk_level'],
             'fetal_prediction':result['fetal_result']['fetal_status'],'audited_agents':len({e['agent'] for e in result['audit_trail']})}
        write('scenarios/'+slug+'.json',{'test_only':True,'payload':payload,'expected':check})
        write('results/'+slug+'.json',result)
        cases.append((name,preset,slug,check))
        checks.append(check)
    invalid=[('temperature_wrong_unit',{'temperature_celsius':98.6},None),
             ('bp_relationship',{'systolic_bp':100,'diastolic_bp':120},None),
             ('boolean_heart_rate',{'heart_rate':True},None),
             ('invalid_ctg_rate',None,{**examples['pathological'],'AC':12})]
    for slug,vitals,ctg in invalid:
        payload={'patient_id':'REPLACE_WITH_YOUR_OWN_PATIENT_ID','vitals':vitals or {},'ctg_features':ctg}
        try:WorkflowRequest.model_validate(payload)
        except ValidationError:pass
        else:raise AssertionError('Invalid case was not rejected: '+slug)
        write('invalid_inputs/'+slug+'.json',{'payload':payload,'expected_http_status':422})
    write('workflow_checks.json',{'tested_at':datetime.now(timezone.utc).isoformat(),'passed':len(checks),'failed':0,'cases':checks,
          'invalid_payloads_rejected':len(invalid),'external_calls':'None in these seven graph checks; separate running-app check verifies live providers.'})
    return cases

async def main():
    registry=ModelRegistry();registry.load_all()
    datasets=[]
    sources=[]
    for path in sorted((ROOT/'data').glob('*.parquet')):
        df=pd.read_parquet(path)
        row={'file':path.name,'rows':len(df),'columns':len(df.columns),'fields':[{'name':c,'dtype':str(df[c].dtype),'missing':int(df[c].isna().sum())} for c in df.columns],
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'preview':json.loads(df.head(3).to_json(orient='records',date_format='iso'))}
        datasets.append(row)
        sources.append((path,'data/'+path.name))
    for path in sorted((ROOT/'data/ctu-uhb-ctgdb').glob('*')):
        if path.is_file() and path.suffix in ('.dat','.hea'):sources.append((path,'data/ctu-uhb-ctgdb/'+path.name))
    allowed_names={'best_model.joblib','pipeline-v1.joblib','preprocessor.joblib','label_encoder.joblib','manifest.json','metadata.json','results.json','ctu_uhb_features.parquet','shap_summary.png'}
    for path in sorted((ROOT/'artifacts').rglob('*')):
        if path.is_file() and path.name in allowed_names:sources.append((path,path.relative_to(ROOT).as_posix()))
    model_results=[]
    for model in catalog():
        assert model['executable'],model
        output=predict(model['name'],model['example'])
        assert output['probabilities'] and abs(sum(output['probabilities'].values())-1)<1e-6
        write('models/'+model['name']+'_features.json',model['example'])
        write('models/'+model['name']+'_request.json',{'model':model['name'],'features':model['example']})
        write('models/'+model['name']+'_expected.json',output)
        model_results.append({k:model[k] for k in ('name','version','target','intended_use','internal_macro_f1','care_decision_use')})
    write('data_catalog.json',{'dataset_count':len(datasets),'total_prepared_rows':sum(d['rows'] for d in datasets),'raw_ctg_records':15,'datasets':datasets})
    write('model_catalog.json',model_results)
    cases=await scenarios(ctg_examples(registry))
    guide=['# MaaHifazat: tamam data aur test inputs','',
       'Yeh local testing ka pack hai. `data/` mein original prepared datasets aur 15 raw signal records hain. `artifacts/` mein current pipelines aur purane estimators alag folders mein preserve hain. Current app `artifacts/serving` aur `artifacts/research` pipelines use karti hai. Original app databases aur API credentials is training/test archive ka hissa nahi hain.','',
       '## Dashboard mein test karein','',
       '1. http://localhost:8501 par apna account banayein/sign in karein.','2. New assessment mein neeche ke observations aur follow-up inputs enter karein. Har row ek alag software-test case hai; real patient data nahi. Unknown measurements blank chhorein.','3. Fetal case ke liye `inputs/ctg_pathological.json` ya `inputs/ctg_suspect.json` ka poora JSON Optional measured CTG JSON field mein paste karein.','4. Run all nine agents and save case click karein. Expected rule urgency aur follow-up action neeche hain.','5. Model evidence mein model select karein aur `models/<name>_features.json` ka JSON paste karein. Run model prediction ka result `<name>_expected.json` se compare karein.','',
       '| Test | Age | Weeks | BP mmHg | HR bpm | Temp C | Glucose mmol/L | Symptoms | Expected action |','|---|---:|---:|---|---:|---:|---:|---|---|']
    for name,s,slug,check in cases:
        bp=str(s.get('systolic_bp','blank'))+'/'+str(s.get('diastolic_bp','blank'))
        guide.append(f"| {name} | {s['age']} | {s['gestational_age_weeks']} | {bp} | {s.get('heart_rate','blank')} | {s.get('temperature_celsius','blank')} | {s.get('blood_sugar_mmol_l','blank')} | {', '.join(s.get('symptoms',[])) or 'None'} | {check['followup_action']} |")
    guide += ['', 'Routine ANC: completed contacts 12,20,26. Maternal emergency: 12,20,26,30. Fetal cases: 12,20,26,30,34. Missed checkups: completed 12,20; missed visits 2; transport barrier Yes; phone access No. Incomplete danger case: completed 12,20,26. Urgent BP: completed 12,20,26.', '',
       'Routine test ka MaternalGuard output mid risk aa sakta hai: rule LOW_RISK aur model category alag cheezein hain. Synthetic scenario se medical accuracy prove nahi hoti. Full holdout scores `reports/model_audit.json` mein hain.', '',
       '## Location aur live services','',
       'Public Peshawar test coordinates: latitude 34.01, longitude 71.53. Overview mein Manual location save karein, OpenStreetMap aur road-provider consents select karke Find nearby hospitals click karein. Actual GPS capture ke liye Use current location ya Start live location click karein aur browser permission dein; Stop tracking band karta hai. Yeh pack user ki real GPS location contain nahi karta.',
       'Assessment par Groq consent enable karne se configured provider explanation banata hai. API keys `.env` mein rehti hain. Overpass fail ho to 2 km bounded-map fallback clearly limited coverage dikhata hai. Hospital services/bed acceptance ki tasdeeq map data se nahi hoti.', '',
       '## API aur reproducible tests','',
       'Staff POST `/api/agents/run` use karein; patient POST `/api/care/assess`. Scenario JSON ke `payload.patient_id` mein apni registered profile ID rakhein. Har new case ke liye `case_id` omit karein ya unique ID dein. Test inputs default mein external processing consent nahi dete; live services sirf explicit UI consent par activate karein.', '',
       '```powershell', '.venv\\Scripts\\python.exe -m pytest backend/tests -q -p no:cacheprovider', '.venv\\Scripts\\python.exe scripts/audit_models.py', '.venv\\Scripts\\python.exe scripts/verify_real_app.py --live-providers', '.venv\\Scripts\\python.exe scripts/export_test_pack.py', '```', '',
       'Live verification command ek labelled local software-verification account/profile/case create karta hai. De-identified synthetic observations aur public coordinates configured providers ko bhejta hai. Automatic SMS/WhatsApp/call delivery is command se test nahi hoti; buttons composer/dialer kholte hain.', '',
       '## Model target ki had','',
       'MaternalGuard RiskLevel aur FetalWatch NSP par chalte hain. Repaired PretermGuard CLASS ke 10 CTG patterns predict karta hai; preterm birth outcomes nahi. CareReach general no-show proxy aur GestationInsight Pima-derived proxy hai. In teen research outputs ko obstetric urgency/diagnosis ke liye use nahi kiya jata. OncoTrace dataset preserved hai, maternity workflow mein use nahi hota.']
    write('TEST_GUIDE_ROMAN_URDU.md','\n'.join(guide)+'\n')
    for filename in ('model_audit.json','real_app_verification.json','latest-test-results.xml','latest_project_test_report.json','LATEST_TEST_REPORT.md'):
        path=ROOT/'docs'/filename
        if path.exists():sources.append((path,'reports/'+filename))
    for filename in ('scripts/export_test_pack.py','scripts/verify_real_app.py','requirements-app.txt','DATASET_REGISTRY.md','docs/API_SETUP.md','docs/REAL_APP_GUIDE.md'):
        path=ROOT/filename
        if path.exists():sources.append((path,filename))
    entries=sources+WRITTEN
    assert len({rel for _,rel in entries})==len(entries)
    manifest={'generated_at':datetime.now(timezone.utc).isoformat(),'source_data_preserved':True,
         'scope':'All five prepared datasets, all 15 local raw CTG records, saved model artifacts, model/assessment test inputs and verification evidence; excludes application databases and secrets.',
         'files':[{'path':rel,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p,rel in entries]}
    write('PACKAGE_MANIFEST.json',manifest)
    archive=ROOT/'exports/MaaHifazat_data_and_tests.zip'
    with ZipFile(archive,'w',ZIP_DEFLATED,compresslevel=6) as zipped:
        for path,relative in entries+[(OUT/'PACKAGE_MANIFEST.json','PACKAGE_MANIFEST.json')]:zipped.write(path,relative)
    with ZipFile(archive) as zipped:
        assert zipped.testzip() is None
        assert not any('.env' in n or n.endswith('.db') for n in zipped.namelist())
        for item in manifest['files']:
            assert hashlib.sha256(zipped.read(item['path'])).hexdigest()==item['sha256']
    print(json.dumps({'archive':str(archive),'bytes':archive.stat().st_size,'prepared_datasets':len(datasets),
          'prepared_rows':sum(d['rows'] for d in datasets),'raw_ctg_records':15,'five_models_executed':True,
          'workflow_cases_passed':len(cases),'invalid_payloads_rejected':4,'archive_hashes_verified':True}))
if __name__=='__main__':asyncio.run(main())
