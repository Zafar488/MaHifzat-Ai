export interface PatientCreate {
  name: string
  age: number
  gender: 'male' | 'female' | 'other'
  phone?: string
  location?: string
  gestational_age_weeks?: number
  parity?: number
  language?: string
  channel?: string
}

export interface PatientProfile extends PatientCreate {
  patient_id: string
  created_at: string
  updated_at: string | null
}
