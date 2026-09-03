import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Activity, Bot, Loader2, ShieldAlert, HeartPulse, Brain, Baby, CalendarClock, ArrowRight } from 'lucide-react'
import { api } from '@/lib/api-client'
import { cn } from '@/lib/utils'
import { useNavigate } from 'react-router-dom'

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

export default function RiskIntelligencePage() {
  const [result, setResult] = useState<RiskAssessmentResponse | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const navigate = useNavigate()

  const { handleSubmit, formState: { isSubmitting } } = useForm()

  const onSubmit = async () => {
    setErrorMsg(null)
    setResult(null)
    try {
      // Mock data that explicitly triggers all 5 ML models
      const payload = {
        patient_id: "pat_" + Math.floor(Math.random() * 100000),
        vitals: { Age: 28, SystolicBP: 165, DiastolicBP: 105, BS: 8.5, BodyTemp: 99.2, HeartRate: 110 },
        ctg_features: { baseline_value: 115, accelerations: 0, fetal_movement: 0, uterine_contractions: 0.005, light_decelerations: 0.002, severe_decelerations: 0, prolongued_decelerations: 0 },
        clinical_features: { Glucose: 130, BloodPressure: 105, BMI: 32, Insulin: 45, SkinThickness: 20, Pregnancies: 3 },
        anc_features: { last_visit_days_ago: 45, total_visits: 1, age: 28, risk_level: "high" }
      }
      
      const res = await api.post<RiskAssessmentResponse>('/risks/assess', payload)
      setResult(res.data)
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to run risk assessment.')
    }
  }

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">MaaHifazat Risk Intelligence (5 ML Models)</h1>
        <p className="mt-2 text-sm text-gray-500">
          Run patient data through all 5 specialized Machine Learning models simultaneously for a complete diagnostic view.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
        
        {/* Input Form Simulation */}
        <div className="xl:col-span-4 bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden h-fit">
          <div className="border-b border-gray-200 bg-gray-50/50 px-6 py-4">
            <h2 className="flex items-center gap-2 text-base font-semibold leading-6 text-gray-900">
              <Activity className="size-5 text-teal-600" />
              Patient Data Input
            </h2>
          </div>
          <div className="p-6">
            <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
              <div className="text-sm text-gray-600 space-y-3 mb-6 bg-teal-50 p-4 rounded-lg border border-teal-100">
                <p><strong>System Note:</strong> For demonstration, clicking "Analyze" will automatically inject a comprehensive clinical dataset (Vitals, CTG readings, ANC history, Glucose levels) to trigger all 5 ML models at once.</p>
              </div>

              {errorMsg && (
                <div className="rounded-md bg-red-50 p-4 border border-red-200 text-sm text-red-700">
                  {errorMsg}
                </div>
              )}

              <button
                type="submit"
                disabled={isSubmitting}
                className="flex w-full justify-center items-center rounded-lg bg-teal-600 px-3 py-3 text-sm font-semibold text-white shadow-sm hover:bg-teal-500 disabled:opacity-50"
              >
                {isSubmitting ? <Loader2 className="mr-2 size-5 animate-spin" /> : <Brain className="mr-2 size-5" />}
                Run 5-Model Intelligence Scan
              </button>
            </form>
          </div>
        </div>

        {/* 5-Model Results Section */}
        <div className="xl:col-span-8 flex flex-col">
          {result ? (
            <div className="space-y-6">
              
              {/* WHO Emergency Banner */}
              {result.is_emergency && (
                <div className="rounded-xl bg-red-50 p-5 border-2 border-red-200 flex items-start gap-4">
                  <ShieldAlert className="size-8 text-red-600 shrink-0" />
                  <div>
                    <h3 className="text-lg font-bold text-red-900 uppercase">WHO EMERGENCY TRIAGE TRIGGERED</h3>
                    <p className="mt-1 text-sm text-red-800">
                      The deterministic safety engine has overridden ML scores due to critical red flags:
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
                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
                    <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                      <HeartPulse className="size-4 text-rose-500" /> Model 1: MaternalGuard
                    </h4>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-gray-900">Maternal Risk</span>
                      <span className={cn("px-2.5 py-1 rounded-full text-xs font-bold uppercase",
                        result.maternal_risk.risk_level === 'high risk' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                      )}>{result.maternal_risk.risk_level}</span>
                    </div>
                    <p className="text-xs text-gray-500 text-right">Confidence: {(result.maternal_risk.confidence * 100).toFixed(1)}%</p>
                  </div>
                )}

                {/* 2. FetalWatch */}
                {result.fetal_health && (
                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
                    <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                      <Baby className="size-4 text-blue-500" /> Model 2: FetalWatch
                    </h4>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-gray-900">CTG Distress Status</span>
                      <span className={cn("px-2.5 py-1 rounded-full text-xs font-bold uppercase",
                        result.fetal_health.fetal_status === 'Suspect' ? 'bg-amber-100 text-amber-800' : 
                        result.fetal_health.fetal_status === 'Pathological' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                      )}>{result.fetal_health.fetal_status}</span>
                    </div>
                    <p className="text-xs text-gray-500 text-right">Confidence: {(result.fetal_health.confidence * 100).toFixed(1)}%</p>
                  </div>
                )}

                {/* 3. PretermGuard */}
                {result.preterm_risk && (
                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
                    <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                      <Activity className="size-4 text-purple-500" /> Model 3: PretermGuard
                    </h4>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-gray-900">Preterm Risk</span>
                      <span className={cn("px-2.5 py-1 rounded-full text-xs font-bold uppercase",
                        result.preterm_risk.preterm_prediction === 1 ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                      )}>{result.preterm_risk.preterm_prediction === 1 ? 'High Risk' : 'Normal'}</span>
                    </div>
                    <p className="text-xs text-gray-500 text-right">Probability: {(result.preterm_risk.preterm_probability * 100).toFixed(1)}%</p>
                  </div>
                )}

                {/* 4. GestationInsight */}
                {result.gestational_complication && (
                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
                    <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                      <Brain className="size-4 text-teal-500" /> Model 4: GestationInsight
                    </h4>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-gray-900">GDM Complication</span>
                      <span className={cn("px-2.5 py-1 rounded-full text-xs font-bold uppercase",
                        result.gestational_complication.risk_level === 'high risk' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                      )}>{result.gestational_complication.risk_level}</span>
                    </div>
                    <p className="text-xs text-gray-500 text-right">Confidence: {(result.gestational_complication.confidence * 100).toFixed(1)}%</p>
                  </div>
                )}

                {/* 5. CareReach */}
                {result.anc_followup && (
                  <div className="md:col-span-2 bg-white rounded-xl shadow-sm border border-gray-200 p-5">
                    <h4 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                      <CalendarClock className="size-4 text-orange-500" /> Model 5: CareReach (ANC Dropout)
                    </h4>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-gray-900">Missed Visit Risk</span>
                      <span className={cn("px-2.5 py-1 rounded-full text-xs font-bold uppercase",
                        result.anc_followup.priority === 'high' ? 'bg-red-100 text-red-800' : 'bg-green-100 text-green-800'
                      )}>{result.anc_followup.priority}</span>
                    </div>
                    <p className="text-sm text-gray-600 mt-2">Recommended Action: <strong>{result.anc_followup.recommended_action}</strong></p>
                  </div>
                )}
              </div>

              {/* Escalate to Agents Call To Action */}
              <div className="mt-8 bg-gradient-to-r from-teal-900 to-teal-700 rounded-xl p-6 text-white shadow-lg flex flex-col md:flex-row items-center justify-between gap-6">
                <div>
                  <h3 className="text-lg font-bold flex items-center gap-2"><Bot className="size-6" /> Multi-Agent Workflow Required</h3>
                  <p className="text-teal-100 text-sm mt-1 max-w-xl">
                    The predictive models have identified complex high-risk conditions. Escalate this case to our 9-Agent Orchestration network to automatically generate a clinical summary, identify referral facilities, and dispatch SMS alerts.
                  </p>
                </div>
                <button
                  onClick={() => navigate('/agents')}
                  className="shrink-0 flex items-center gap-2 bg-white text-teal-900 px-5 py-3 rounded-lg font-bold text-sm hover:bg-teal-50 transition-colors shadow-sm"
                >
                  Escalate to Agents <ArrowRight className="size-4" />
                </button>
              </div>

            </div>
          ) : (
            <div className="flex-1 rounded-xl border-2 border-dashed border-gray-200 flex flex-col items-center justify-center p-12 text-center h-full min-h-[400px]">
              <Brain className="size-12 text-gray-300 mb-4" />
              <h3 className="text-sm font-medium text-gray-900">No Assessment Run</h3>
              <p className="mt-1 text-sm text-gray-500 max-w-sm">
                Click the button to run the patient data against MaternalGuard, FetalWatch, PretermGuard, GestationInsight, and CareReach.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
