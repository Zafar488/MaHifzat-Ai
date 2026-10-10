"""New structured intake, bilingual reports, strict CTG import and research boundaries."""
import json
from copy import deepcopy
import pytest
from pydantic import ValidationError
from backend.schemas.assessment import WorkflowRequest
from backend.schemas.care import FollowupContext
from backend.services.ctg_import import parse_ctg_csv, complete_ctg, ctg_template_csv
from backend.services.bilingual_reports import build_two_reports, report_html
from backend.services.case_research import research_for_case
from backend.services.inference import ModelRegistry, CTG_FEATURES
from backend.tests.test_api import VITALS


def sample_ctg():
    r=ModelRegistry();r.load_all()
    return dict(zip(CTG_FEATURES,r._models['fetalwatch']['known_input']))


def csv_record(features):
    return (','.join(CTG_FEATURES)+'\n'+','.join(str(features[k]) for k in CTG_FEATURES)+'\n').encode()


def test_ctg_single_patient_template_import_and_units():
    features=sample_ctg()
    assert parse_ctg_csv(csv_record(features))==features
    assert ctg_template_csv().splitlines()[0].split(',')==CTG_FEATURES
    with pytest.raises(ValueError):parse_ctg_csv(ctg_template_csv().encode())
    with pytest.raises(ValueError):complete_ctg({'LB':120})


@pytest.mark.parametrize('kind',['multiple_rows','duplicate_header','wrong_rate','nan','boolean','oversized'])
def test_ctg_import_rejects_ambiguous_or_incompatible_data(kind):
    features=sample_ctg();data=csv_record(features)
    if kind=='multiple_rows':data+=data.splitlines()[1]+b'\n'
    elif kind=='duplicate_header':data=data.replace(b'AC,',b'LB,',1)
    elif kind=='wrong_rate':features['AC']=5;data=csv_record(features)
    elif kind=='nan':features['LB']=float('nan');data=csv_record(features)
    elif kind=='boolean':features['LB']=True;data=csv_record(features)
    elif kind=='oversized':data=b'x'*1_000_001
    with pytest.raises(ValueError):parse_ctg_csv(data)


def test_movement_changes_are_mapped_but_never_felt_is_not_reduction():
    p=WorkflowRequest(patient_id='x',encounter={'movements_reduced':True})
    assert p.vitals.fetal_movement_present is False
    p=WorkflowRequest(patient_id='x',encounter={'movements_started':False})
    assert p.vitals.fetal_movement_present is None
    with pytest.raises(ValidationError):WorkflowRequest(patient_id='x',vitals={'fetal_movement_present':True},encounter={'movements_reduced':True})
    with pytest.raises(ValidationError):WorkflowRequest(patient_id='x',encounter={'movements_started':False,'movements_reduced':True})
    with pytest.raises(ValidationError):WorkflowRequest(patient_id='x',encounter={'storage_consent':False})
    with pytest.raises(ValidationError):FollowupContext(booking_date='2026-10-12',next_appointment_date='2026-10-11')


def report_state():
    return {'case_id':'report-test','patient_id':'test-patient','vitals':{'systolic_bp':180,'diastolic_bp':120},
        'patient_context':{'name':'<script>alert(1)</script>','phone':None},'encounter':{'movements_started':None},
        'clinical_risk_result':{'maternal_risk':{'risk_level':'high risk'},'who_red_flags':{'is_emergency':True,'triage_level':'HIGH_RISK_EMERGENCY','triggered_rules':['severe_hypertension'],'recommended_actions':['Seek immediate maternity assessment.']}},
        'referral_result':{'status':'unverified_candidate_requires_confirmation','capabilities_needed':{'has_maternity':True,'has_emergency':True},
          'selected_facility':{'facility_id':'mapped'},'coverage_limited':True,'coverage_radius_km':2,
          'ranked_facilities':[{'facility_id':'mapped','name':'Synthetic fixture hospital','latitude':34.01,'longitude':71.53,
            'distance_km':.25,'distance_kind':'straight_line','travel_time_minutes':None,'capabilities_verified':False,
            'reported_services':{'has_maternity':None,'has_emergency':True,'has_nicu':None},'availability':'unknown'}]}}


def test_two_reports_preserve_urgency_unknown_services_distance_and_safe_html():
    reports=build_two_reports(report_state())
    assert set(reports)=={'care','referral'}
    for report in reports.values():
        assert report['urgency']=='emergency' and set(report['languages'])=={'en','ur'}
        assert any('\u0600'<=ch<='\u06ff' for ch in report['languages']['ur']['text'])
        html=report_html(report)
        assert '<script>' not in html and '&lt;script&gt;' in html and 'dir="rtl"' in html
    referral=reports['referral']['languages']['en']['text']
    assert '250 m' in referral and 'straight_line' in referral and 'map-reported, unverified' in referral
    assert 'Road' not in referral or 'Road ETA is an estimate' in referral
    assert 'No measured CTG' in reports['care']['languages']['en']['text']
    assert 'No local clinical validation' in reports['care']['languages']['en']['text']


def test_research_derivation_preserves_missing_and_does_not_modify_clinical_state(monkeypatch):
    state={'vitals':{'age':30,'diastolic_bp':80,'blood_sugar_mmol_l':6},'ctg_data':sample_ctg(),
      'encounter':{'run_research_models':True,'previous_pregnancies':2,
        'gestation_labs':{'skin_thickness_mm':20,'insulin_mu_ml':100,'bmi':25,'diabetes_pedigree_function':.3},
        'appointment_research':{'scholarship':False,'hypertension':False,'diabetes':False,'alcoholism':False,'handicap_code':0,'sms_received':True}},
      'followup':{'booking_date':'2026-10-01','next_appointment_date':'2026-10-15','last_completed_checkup_date':'2026-09-01'},'emergency':False}
    original=deepcopy(state);calls={}
    def predict(name,features):
        calls[name]=features
        return {'status':'research_prediction','care_decision_use':False}
    monkeypatch.setattr('backend.services.case_research.predict',predict)
    result=research_for_case(state)
    assert len(calls)==3 and state==original
    assert calls['gestationinsight']['Pregnancies']==3
    assert calls['gestationinsight']['Glucose']==pytest.approx(108.1092)
    assert calls['gestationinsight']['SBP_estimated']==120
    assert calls['carereach']['booking_delta_days']==14
    assert calls['carereach']['sms_x_delta']==14
    assert all(r['care_decision_use'] is False for r in result.values())
    state['encounter']['gestation_labs']['diabetes_pedigree_function']=None
    assert research_for_case(state)['gestationinsight']['status']=='not_assessed'


@pytest.mark.asyncio
async def test_full_case_stores_intake_and_two_reports_with_access_control(async_client,auth_headers,patient_id):
    payload={'patient_id':patient_id,'vitals':VITALS,'encounter':{'storage_consent':True,'previous_pregnancies':2,
      'previous_births':1,'dating_source':'ultrasound','measurement_taken_at':'2026-10-10T10:00:00+05:00',
      'history_notes':'Original local history','movements_started':True,'movements_reduced':True,'preferred_language':'ur'},
      'followup':{'booking_date':'2026-10-01','next_appointment_date':'2026-10-15','reminder_actually_sent':None}}
    response=await async_client.post('/api/agents/run',json=payload,headers=auth_headers)
    assert response.status_code==200,response.text
    result=response.json()['result']
    assert result['emergency'] is True and len({e['agent'] for e in result['audit_trail']})==9
    assert result['encounter']['history_notes']=='Original local history'
    assert result['vitals']['fetal_movement_present'] is False
    reports=result['reporting_result']['reports']
    assert reports['care']['urgency']==reports['referral']['urgency']=='emergency'
    assert 'Original local history' in reports['care']['languages']['en']['text']
    assert 'ultrasound' in reports['care']['languages']['en']['text']
    saved=await async_client.get('/api/agents/cases/'+result['case_id'],headers=auth_headers)
    assert saved.json()['result']['reporting_result']['reports']==reports
    from backend.tests.conftest import login_as
    other=await login_as(async_client,'patient')
    assert (await async_client.get('/api/agents/cases/'+result['case_id'],headers=other)).status_code==404


@pytest.mark.asyncio
async def test_ai_withholds_all_identifying_case_notes_and_requires_urdu_script(monkeypatch):
    from backend.services.ai_assistant import explain_case
    from backend.tests.test_real_app import ai_state,valid_ai
    from backend.config import settings
    import httpx
    monkeypatch.setattr(settings,'ENABLE_LLM',True);monkeypatch.setattr(settings,'GROQ_API_KEY','synthetic-key')
    calls=[];content=valid_ai()
    async def post(self,url,**kwargs):
        calls.append(kwargs['json'])
        return httpx.Response(200,request=httpx.Request('POST',url),json={'choices':[{'message':{'content':json.dumps(content)}}]})
    monkeypatch.setattr(httpx.AsyncClient,'post',post)
    state={**ai_state(),'encounter':{'history_notes':'PRIVATE-CASE-NOTE','additional_symptoms':'PRIVATE-SYMPTOM-NOTE','fetal_notes':'PRIVATE-FETAL-NOTE','previous_pregnancies':2,'notification_consent':True}}
    result=await explain_case(state)
    assert result['status']=='generated'
    assert not any(v in json.dumps(calls) for v in ['PRIVATE-CASE-NOTE','PRIVATE-SYMPTOM-NOTE','PRIVATE-FETAL-NOTE'])
    content['care_explanation_urdu']='Roman Urdu only, no native script'
    assert (await explain_case(state))['status']=='provider_failed'


def test_four_sections_render_without_invented_observations():
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_string("""
import streamlit as st
from ui.assessment_form import render_assessment_form
st.session_state['user']={'full_name':'Synthetic UI test'}
render_assessment_form(None,{},'test',False,None,True)
""").run(timeout=20)
    assert not app.exception
    headings=[s.value for s in app.subheader]
    assert len(headings)==4 and "Mother's assessment" in headings[1]
    assert next(v for v in app.number_input if v.label=='Systolic BP (mmHg)').value is None
    assert next(v for v in app.selectbox if v.label=='Vision disturbance').value=='Unknown'
    assert next(v for v in app.checkbox if v.label=='Patient consent obtained to store this case').value is False


def test_clinician_date_gestation_is_separate_from_contact_milestone():
    from datetime import date
    from backend.services.followup import plan_followup
    output=plan_followup({'gestational_age_weeks':28,'completed_contact_weeks':[12,20,26],'next_appointment_date':'2026-10-17'},today=date(2026,10,10))
    assert output['next_contact_week']==30
    assert output['next_appointment_gestational_age_weeks']==29
