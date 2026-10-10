export interface VitalsInput {
  Age: number
  SystolicBP: number
  DiastolicBP: number
  BS: number
  BodyTemp: number
  HeartRate: number
}

export interface RiskAssessmentRequest {
  patient_id: string
  case_id?: string
  vitals: VitalsInput
  ctg_features?: Record<string, number>
  clinical_features?: Record<string, number>
  anc_features?: Record<string, any>
}

export interface RiskAssessmentResponse {
  case_id: string
  maternal_risk?: Record<string, any>
  fetal_health?: Record<string, any>
  preterm_risk?: Record<string, any>
  gestational_complication?: Record<string, any>
  anc_followup?: Record<string, any>
  safety_triage?: Record<string, any>
  is_emergency: boolean
}

export interface ClinicalRecord {
  case_id: string
  patient_id: string
  maternal_risk_level?: string
  fetal_status?: string
  complication_risk?: string
  triage_level?: string
  who_red_flags?: string[]
  is_emergency: boolean
  model_outputs?: Record<string, any>
  created_at: string | null
}
