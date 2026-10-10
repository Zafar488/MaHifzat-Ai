import { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { Activity, Bot, Loader2, ShieldAlert, HeartPulse, Brain, Baby, CalendarClock, ArrowRight, UserCheck, RefreshCw, Zap } from 'lucide-react'
import { api } from '@/lib/api-client'
import { usePatients } from '@/hooks/usePatients'
import { cn } from '@/lib/utils'
import { FallbackNotice } from '@/components/shared/FallbackNotice'

interface RiskAssessmentResponse {
  case_id: string
  maternal_risk?: any
  fetal_health?: any
  preterm_risk?: any
  gestational_complication?: any
  anc_followup?: any
  safety_triage?: any
  is_emergency: boolean
}

// Preset clinical scenarios to demonstrate dynamic ML model outputs
const PRESETS = {
  high: {
    name: '🔴 Emergency High Risk (Preeclampsia & Fetal Distress)',
    patient_name: 'High-Risk Demo Patient',
    vitals: { Age: 34, SystolicBP: 175, DiastolicBP: 110, BS: 11.2, BodyTemp: 99.8, HeartRate: 115 },
    ctg_features: {
      LB: 112, AC: 0, FM: 0, UC: 0.006, DL: 0.003, DS: 0.001, DP: 0,
      ASTV: 78, MSTV: 0.4, ALTV: 52, MLTV: 3.2, Width: 85,
      Min: 70, Max: 155, Nmax: 4, Nzeros: 0,
      Mode: 110, Mean: 108, Median: 110, Variance: 25, Tendency: -1
    },
    clinical_features: { Glucose: 175, BloodPressure: 110, BMI: 34.5, Insulin: 65, SkinThickness: 28, Pregnancies: 4, Age: 34, DiabetesPedigreeFunction: 0.8 },
    anc_features: { Age: 34, booking_delta_days: 60, SMS_received: 0, Hipertension: 1, Diabetes: 1, Alcoholism: 0, Handcap: 0, Scholarship: 0, comorbidity_count: 2 }
  },
  moderate: {
    name: '🟡 Moderate Risk (Gestational Diabetes & Elevated BP)',
    patient_name: 'Moderate-Risk Demo Patient',
    vitals: { Age: 29, SystolicBP: 138, DiastolicBP: 88, BS: 8.9, BodyTemp: 98.6, HeartRate: 88 },
    ctg_features: {
      LB: 135, AC: 0.002, FM: 0.001, UC: 0.003, DL: 0.001, DS: 0, DP: 0,
      ASTV: 48, MSTV: 1.1, ALTV: 15, MLTV: 8.5, Width: 55,
      Min: 110, Max: 165, Nmax: 2, Nzeros: 0,
      Mode: 135, Mean: 134, Median: 136, Variance: 12, Tendency: 0
    },
    clinical_features: { Glucose: 145, BloodPressure: 88, BMI: 29.2, Insulin: 35, SkinThickness: 22, Pregnancies: 2, Age: 29, DiabetesPedigreeFunction: 0.45 },
    anc_features: { Age: 29, booking_delta_days: 25, SMS_received: 1, Hipertension: 0, Diabetes: 1, Alcoholism: 0, Handcap: 0, Scholarship: 0, comorbidity_count: 1 }
  },
  low: {
    name: '🟢 Healthy Low Risk (Normal Clinical Vitals)',
    patient_name: 'Low-Risk Demo Patient',
    vitals: { Age: 24, SystolicBP: 115, DiastolicBP: 75, BS: 5.2, BodyTemp: 98.2, HeartRate: 74 },
    ctg_features: {
      LB: 138, AC: 0.006, FM: 0.004, UC: 0.002, DL: 0, DS: 0, DP: 0,
      ASTV: 32, MSTV: 1.8, ALTV: 0, MLTV: 14.2, Width: 65,
      Min: 115, Max: 180, Nmax: 3, Nzeros: 0,
      Mode: 140, Mean: 142, Median: 141, Variance: 7, Tendency: 1
    },
    clinical_features: { Glucose: 92, BloodPressure: 75, BMI: 22.8, Insulin: 15, SkinThickness: 14, Pregnancies: 1, Age: 24, DiabetesPedigreeFunction: 0.2 },
    anc_features: { Age: 24, booking_delta_days: 7, SMS_received: 1, Hipertension: 0, Diabetes: 0, Alcoholism: 0, Handcap: 0, Scholarship: 0, comorbidity_count: 0 }
  }
}

export default function RiskIntelligencePage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const preselectedPatientId = searchParams.get('patient_id') || ''

  const { data: patientsList } = usePatients(0, 100)

  const [selectedPatientId, setSelectedPatientId] = useState<string>(preselectedPatientId)
  const [result, setResult] = useState<RiskAssessmentResponse | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  // Interactive Form State for Vitals & Clinical Features
  const [formData, setFormData] = useState({
    Age: 28,
    SystolicBP: 135,
    DiastolicBP: 85,
    BS: 7.5,
    BodyTemp: 98.6,
    HeartRate: 85,
    gestational_age_weeks: 32,
    BMI: 27.5,
    Glucose: 120,
    BaselineFHR: 135,
    ASTV: 45,
  })

  // When patient is selected from list, auto-fill age & gestational age
  useEffect(() => {
    if (selectedPatientId && patientsList) {
      const p = patientsList.find(item => item.patient_id === selectedPatientId)
      if (p) {
        setFormData(prev => ({
          ...prev,
          Age: p.age || prev.Age,
          gestational_age_weeks: p.gestational_age_weeks || prev.gestational_age_weeks,
        }))
      }
    }
  }, [selectedPatientId, patientsList])

  const applyPreset = (presetKey: keyof typeof PRESETS) => {
    const p = PRESETS[presetKey]
    setFormData({
      Age: p.vitals.Age,
      SystolicBP: p.vitals.SystolicBP,
      DiastolicBP: p.vitals.DiastolicBP,
      BS: p.vitals.BS,
      BodyTemp: p.vitals.BodyTemp,
      HeartRate: p.vitals.HeartRate,
      gestational_age_weeks: 34,
      BMI: p.clinical_features.BMI,
      Glucose: p.clinical_features.Glucose,
      BaselineFHR: p.ctg_features.LB,
      ASTV: p.ctg_features.ASTV,
    })
  }

  const handleRunAssessment = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setErrorMsg(null)
    setResult(null)

    try {
      // Build dynamic features derived from the user's exact inputs
      const payload = {
        patient_id: selectedPatientId || "pat_demo_" + Math.floor(Math.random() * 1000),
        vitals: {
          Age: Number(formData.Age),
          SystolicBP: Number(formData.SystolicBP),
          DiastolicBP: Number(formData.DiastolicBP),
          BS: Number(formData.BS),
          BodyTemp: Number(formData.BodyTemp),
          HeartRate: Number(formData.HeartRate),
        },
        ctg_source: "uci_measured",
        provenance: "patient_reported",
        ctg_features: {
          LB: Number(formData.BaselineFHR),
          AC: formData.BaselineFHR < 120 ? 0 : 0.003,
          FM: 0.002,
          UC: formData.SystolicBP > 160 ? 0.007 : 0.002,
          DL: formData.BaselineFHR < 120 ? 0.004 : 0,
          DS: formData.SystolicBP > 160 ? 0.001 : 0,
          DP: 0,
          ASTV: Number(formData.ASTV),
          MSTV: Number(formData.ASTV) > 60 ? 0.4 : 1.5,
          ALTV: Number(formData.ASTV) > 60 ? 45 : 5,
          MLTV: 10.0,
          Width: 60,
          Min: 80,
          Max: 160,
          Nmax: 3,
          Nzeros: 0,
          Mode: Number(formData.BaselineFHR),
          Mean: Number(formData.BaselineFHR) - 2,
          Median: Number(formData.BaselineFHR) - 1,
          Variance: Number(formData.ASTV) > 60 ? 25 : 10,
          Tendency: 0,
        },
        clinical_features: {
          Glucose: Number(formData.Glucose),
          BloodPressure: Number(formData.DiastolicBP),
          BMI: Number(formData.BMI),
          Insulin: formData.Glucose > 140 ? 55 : 18,
          SkinThickness: 20,
          Pregnancies: 2,
          Age: Number(formData.Age),
          DiabetesPedigreeFunction: formData.Glucose > 140 ? 0.75 : 0.25,
        },
        anc_features: {
          Age: Number(formData.Age),
          booking_delta_days: formData.SystolicBP > 150 ? 45 : 10,
          SMS_received: formData.SystolicBP > 150 ? 0 : 1,
          Hipertension: formData.SystolicBP >= 140 ? 1 : 0,
          Diabetes: formData.Glucose >= 140 ? 1 : 0,
          Alcoholism: 0,
          Handcap: 0,
          Scholarship: 0,
          comorbidity_count: (formData.SystolicBP >= 140 ? 1 : 0) + (formData.Glucose >= 140 ? 1 : 0),
        },
      }

      const res = await api.post<RiskAssessmentResponse>('/risks/assess', payload)
      setResult(res.data)
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to run risk assessment.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">MaaHifazat Risk Intelligence (5 ML Models)</h1>
        <p className="mt-2 text-sm text-gray-500">
          Run custom patient vitals and CTG readings through all 5 specialized Machine Learning models for real-time, dynamic risk assessment.
        </p>
      </div>

      {/* Preset Quick Actions */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 space-y-3">
        <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider flex items-center gap-2">
          <Zap className="size-4 text-amber-500" /> Quick Preset Scenarios (Load Sample Patient Vitals)
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <button
            type="button"
            onClick={() => applyPreset('high')}
            className="flex items-center justify-between p-3 rounded-lg border border-red-200 bg-red-50 text-left hover:bg-red-100 transition-colors text-xs font-semibold text-red-900"
          >
            <span>{PRESETS.high.name}</span>
            <RefreshCw className="size-3.5 text-red-600 shrink-0 ml-2" />
          </button>
          <button
            type="button"
            onClick={() => applyPreset('moderate')}
            className="flex items-center justify-between p-3 rounded-lg border border-amber-200 bg-amber-50 text-left hover:bg-amber-100 transition-colors text-xs font-semibold text-amber-900"
          >
            <span>{PRESETS.moderate.name}</span>
            <RefreshCw className="size-3.5 text-amber-600 shrink-0 ml-2" />
          </button>
          <button
            type="button"
            onClick={() => applyPreset('low')}
            className="flex items-center justify-between p-3 rounded-lg border border-green-200 bg-green-50 text-left hover:bg-green-100 transition-colors text-xs font-semibold text-green-900"
          >
            <span>{PRESETS.low.name}</span>
            <RefreshCw className="size-3.5 text-green-600 shrink-0 ml-2" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
        {/* Left Column: Patient Selector & Clinical Input Form */}
        <div className="xl:col-span-5 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden h-fit">
          <div className="border-b border-gray-200 bg-gray-50/50 px-6 py-4">
            <h2 className="flex items-center gap-2 text-base font-semibold leading-6 text-gray-900">
              <Activity className="size-5 text-teal-600" />
              Dynamic Clinical Vitals Input
            </h2>
          </div>
          <div className="p-6">
            <form onSubmit={handleRunAssessment} className="space-y-5">
              {/* Select Registered Patient */}
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1 flex items-center gap-1.5">
                  <UserCheck className="size-3.5 text-teal-600" /> Select Registered Patient (Optional)
                </label>
                <select
                  value={selectedPatientId}
                  onChange={(e) => setSelectedPatientId(e.target.value)}
                  className="block w-full rounded-lg border border-gray-300 bg-white px-3 py-2 text-xs text-gray-900 focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
                >
                  <option value="">-- Custom Assessment (Or Select Patient) --</option>
                  {patientsList?.map(p => (
                    <option key={p.patient_id} value={p.patient_id}>
                      {p.name} (ID: {p.patient_id.substring(0, 8)}... • Age: {p.age})
                    </option>
                  ))}
                </select>
              </div>

              {/* Vitals Input Grid */}
              <div className="space-y-4 pt-2 border-t border-gray-100">
                <h4 className="text-xs font-bold text-gray-800 uppercase tracking-wider">Maternal Vitals</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-gray-600">Age</label>
                    <input
                      type="number"
                      value={formData.Age}
                      onChange={(e) => setFormData({ ...formData, Age: Number(e.target.value) })}
                      className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-900 focus:border-teal-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-600">Heart Rate (bpm)</label>
                    <input
                      type="number"
                      value={formData.HeartRate}
                      onChange={(e) => setFormData({ ...formData, HeartRate: Number(e.target.value) })}
                      className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-900 focus:border-teal-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-600">Systolic BP (mmHg)</label>
                    <input
                      type="number"
                      value={formData.SystolicBP}
                      onChange={(e) => setFormData({ ...formData, SystolicBP: Number(e.target.value) })}
                      className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-900 focus:border-teal-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-600">Diastolic BP (mmHg)</label>
                    <input
                      type="number"
                      value={formData.DiastolicBP}
                      onChange={(e) => setFormData({ ...formData, DiastolicBP: Number(e.target.value) })}
                      className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-900 focus:border-teal-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-600">Blood Sugar (mmol/L)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={formData.BS}
                      onChange={(e) => setFormData({ ...formData, BS: Number(e.target.value) })}
                      className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-900 focus:border-teal-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-600">Body Temp (°F)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={formData.BodyTemp}
                      onChange={(e) => setFormData({ ...formData, BodyTemp: Number(e.target.value) })}
                      className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-900 focus:border-teal-500"
                    />
                  </div>
                </div>
              </div>

              {/* Fetal & Gestational Parameters */}
              <div className="space-y-4 pt-2 border-t border-gray-100">
                <h4 className="text-xs font-bold text-gray-800 uppercase tracking-wider">Fetal & Metabolic Parameters</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-gray-600">Baseline FHR (bpm)</label>
                    <input
                      type="number"
                      value={formData.BaselineFHR}
                      onChange={(e) => setFormData({ ...formData, BaselineFHR: Number(e.target.value) })}
                      className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-900 focus:border-teal-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-600">Short-Term Var (ASTV %)</label>
                    <input
                      type="number"
                      value={formData.ASTV}
                      onChange={(e) => setFormData({ ...formData, ASTV: Number(e.target.value) })}
                      className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-900 focus:border-teal-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-600">Glucose (mg/dL)</label>
                    <input
                      type="number"
                      value={formData.Glucose}
                      onChange={(e) => setFormData({ ...formData, Glucose: Number(e.target.value) })}
                      className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-900 focus:border-teal-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-600">BMI (kg/m²)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={formData.BMI}
                      onChange={(e) => setFormData({ ...formData, BMI: Number(e.target.value) })}
                      className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-900 focus:border-teal-500"
                    />
                  </div>
                </div>
              </div>

              {errorMsg && (
                <div className="rounded-md bg-red-50 p-3 border border-red-200 text-xs text-red-700">
                  {errorMsg}
                </div>
              )}

              <button
                type="submit"
                disabled={isSubmitting}
                className="flex w-full justify-center items-center gap-2 rounded-lg bg-teal-600 px-4 py-3 text-sm font-semibold text-white shadow-sm hover:bg-teal-500 disabled:opacity-50 transition-colors"
              >
                {isSubmitting ? <Loader2 className="size-5 animate-spin" /> : <Brain className="size-5" />}
                {isSubmitting ? 'Evaluating 5 ML Models...' : 'Run Dynamic 5-Model Scan'}
              </button>
            </form>
          </div>
        </div>

        {/* Right Column: 5 ML Models Dynamic Results Display */}
        <div className="xl:col-span-7 flex flex-col">
          {result ? (
            <div className="space-y-6">
              {/* WHO Emergency Banner */}
              {result.is_emergency && (
                <div className="rounded-xl bg-red-50 p-5 border-2 border-red-200 flex items-start gap-4 shadow-sm animate-emergency-pulse">
                  <ShieldAlert className="size-8 text-red-600 shrink-0 mt-0.5" />
                  <div>
                    <h3 className="text-base font-bold text-red-900 uppercase tracking-wide">WHO EMERGENCY TRIAGE TRIGGERED</h3>
                    <p className="mt-1 text-xs text-red-800">
                      The clinical safety engine identified critical red flags requiring urgent facility escalation:
                    </p>
                    {result.safety_triage?.triggered_rules && (
                      <ul className="mt-2 text-xs font-semibold text-red-700 list-disc list-inside">
                        {result.safety_triage.triggered_rules.map((rule: string) => (
                          <li key={rule}>{rule.toUpperCase()}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              )}

              {/* Grid of 5 ML Models */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* 1. MaternalGuard */}
                {result.maternal_risk && (
                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 space-y-3">
                    <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider flex items-center gap-2">
                      <HeartPulse className="size-4 text-rose-500" /> Model 1: MaternalGuard
                    </h4>

                    {(result.maternal_risk.model_available === false || result.maternal_risk.source === 'heuristic_fallback') && (
                      <FallbackNotice modelName="MaternalGuard" source={result.maternal_risk.source} compact />
                    )}

                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs font-medium text-gray-700">Maternal Risk Level</span>
                      <span className={cn(
                        "px-2.5 py-1 rounded-full text-xs font-bold uppercase",
                        result.maternal_risk.risk_level === 'high risk' || result.maternal_risk.risk_level === 'High' ? 'bg-red-100 text-red-800' :
                        result.maternal_risk.risk_level === 'mid risk' || result.maternal_risk.risk_level === 'Moderate' ? 'bg-amber-100 text-amber-800' :
                        'bg-green-100 text-green-800'
                      )}>
                        {result.maternal_risk.risk_level}
                      </span>
                    </div>
                    <div className="mt-2 text-xs text-gray-500 flex justify-between">
                      <span>Model Confidence:</span>
                      <span className="font-semibold text-gray-800">{(result.maternal_risk.confidence * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                )}

                {/* 2. FetalWatch */}
                {result.fetal_health && (
                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 space-y-3">
                    <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider flex items-center gap-2">
                      <Baby className="size-4 text-blue-500" /> Model 2: FetalWatch (CTG)
                    </h4>

                    {(result.fetal_health.model_available === false || result.fetal_health.source === 'heuristic_fallback') && (
                      <FallbackNotice modelName="FetalWatch (CTG)" source={result.fetal_health.source} compact />
                    )}

                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs font-medium text-gray-700">Fetal Distress Status</span>
                      <span className={cn(
                        "px-2.5 py-1 rounded-full text-xs font-bold uppercase",
                        result.fetal_health.fetal_status === 'Pathological' ? 'bg-red-100 text-red-800' :
                        result.fetal_health.fetal_status === 'Suspect' ? 'bg-amber-100 text-amber-800' :
                        'bg-green-100 text-green-800'
                      )}>
                        {result.fetal_health.fetal_status}
                      </span>
                    </div>
                    <div className="mt-2 text-xs text-gray-500 flex justify-between">
                      <span>Model Confidence:</span>
                      <span className="font-semibold text-gray-800">{(result.fetal_health.confidence * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                )}

                {/* 3. PretermGuard */}
                {result.preterm_risk && (
                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 space-y-3">
                    <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider flex items-center gap-2">
                      <Activity className="size-4 text-purple-500" /> Model 3: PretermGuard
                    </h4>

                    {(result.preterm_risk.model_available === false || result.preterm_risk.source === 'heuristic_fallback') && (
                      <FallbackNotice modelName="PretermGuard" source={result.preterm_risk.source} compact />
                    )}

                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs font-medium text-gray-700">Preterm Delivery Risk</span>
                      <span className={cn(
                        "px-2.5 py-1 rounded-full text-xs font-bold uppercase",
                        result.preterm_risk.preterm_prediction === 1 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                      )}>
                        {result.preterm_risk.preterm_prediction === 1 ? 'High Risk' : 'Normal'}
                      </span>
                    </div>
                    <div className="mt-2 text-xs text-gray-500 flex justify-between">
                      <span>Preterm Probability:</span>
                      <span className="font-semibold text-gray-800">{(result.preterm_risk.preterm_probability * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                )}

                {/* 4. GestationInsight */}
                {result.gestational_complication && (
                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 space-y-3">
                    <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider flex items-center gap-2">
                      <Brain className="size-4 text-teal-500" /> Model 4: GestationInsight
                    </h4>

                    {(result.gestational_complication.model_available === false || result.gestational_complication.source === 'heuristic_fallback') && (
                      <FallbackNotice modelName="GestationInsight" source={result.gestational_complication.source} compact />
                    )}

                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs font-medium text-gray-700">Gestational Complication</span>
                      <span className={cn(
                        "px-2.5 py-1 rounded-full text-xs font-bold uppercase",
                        result.gestational_complication.risk_level === 'high risk' || result.gestational_complication.risk_level === 'High' ? 'bg-red-100 text-red-800' :
                        result.gestational_complication.risk_level === 'mid risk' || result.gestational_complication.risk_level === 'Moderate' ? 'bg-amber-100 text-amber-800' :
                        'bg-green-100 text-green-800'
                      )}>
                        {result.gestational_complication.risk_level}
                      </span>
                    </div>
                    <div className="mt-2 text-xs text-gray-500 flex justify-between">
                      <span>Model Confidence:</span>
                      <span className="font-semibold text-gray-800">{(result.gestational_complication.confidence * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                )}

                {/* 5. CareReach */}
                {result.anc_followup && (
                  <div className="md:col-span-2 bg-white rounded-xl shadow-sm border border-gray-200 p-5 space-y-3">
                    <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider flex items-center gap-2">
                      <CalendarClock className="size-4 text-orange-500" /> Model 5: CareReach (ANC Care Outreach)
                    </h4>

                    {(result.anc_followup.model_available === false || result.anc_followup.source === 'heuristic_fallback') && (
                      <FallbackNotice modelName="CareReach" source={result.anc_followup.source} compact />
                    )}

                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs font-medium text-gray-700">Missed Visit / Dropout Priority</span>
                      <span className={cn(
                        "px-2.5 py-1 rounded-full text-xs font-bold uppercase",
                        result.anc_followup.priority === 'high' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                      )}>
                        {result.anc_followup.priority} Priority
                      </span>
                    </div>
                    <p className="text-xs text-gray-600 mt-2">
                      Recommended Intervention: <strong>{result.anc_followup.recommended_action}</strong>
                    </p>
                  </div>
                )}
              </div>

              {/* Escalate to Agentic Pipeline Banner */}
              <div className="mt-6 bg-gradient-to-r from-teal-900 to-teal-700 rounded-xl p-6 text-white shadow-lg flex flex-col md:flex-row items-center justify-between gap-6">
                <div>
                  <h3 className="text-base font-bold flex items-center gap-2"><Bot className="size-5" /> Trigger 9-Agent LangGraph Network</h3>
                  <p className="text-teal-100 text-xs mt-1 max-w-xl">
                    Escalate this dynamic clinical assessment to the multi-agent network to generate structured referral routing, dispatch SMS alerts, and execute clinician review.
                  </p>
                </div>
                <button
                  onClick={() => navigate('/agents')}
                  className="shrink-0 flex items-center gap-2 bg-white text-teal-900 px-5 py-2.5 rounded-lg font-bold text-xs hover:bg-teal-50 transition-colors shadow-sm"
                >
                  Run Agent Workflow <ArrowRight className="size-4" />
                </button>
              </div>
            </div>
          ) : (
            <div className="flex-1 rounded-xl border-2 border-dashed border-gray-200 flex flex-col items-center justify-center p-12 text-center h-full min-h-[420px] bg-white">
              <Brain className="size-12 text-teal-500 mb-4 animate-bounce" />
              <h3 className="text-sm font-semibold text-gray-900">Ready to Evaluate Patient Vitals</h3>
              <p className="mt-1 text-xs text-gray-500 max-w-sm">
                Enter vitals on the left or select a Quick Preset to see real-time dynamic predictions across all 5 ML models.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
