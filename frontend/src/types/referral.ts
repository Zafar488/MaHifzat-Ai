export type UrgencyLevel = 'routine' | 'urgent' | 'emergency'
export type ReferralStatus = 'pending' | 'accepted' | 'in_transit' | 'completed' | 'cancelled'

export interface ReferralCreate {
  patient_id: string
  case_id?: string
  facility_name?: string
  facility_type?: string
  facility_lat?: number
  facility_lon?: number
  distance_km?: number
  travel_time_min?: number
  urgency_level: UrgencyLevel
}

export interface Referral extends ReferralCreate {
  id: string
  status: ReferralStatus
  created_at: string | null
  completed_at: string | null
}
