export interface DashboardData {
  total_patients: number
  risk_distribution: {
    high: number
    medium: number
    low: number
    unknown: number
  }
  referral_stats: {
    total: number
    by_status: Record<string, number>
  }
  recent_cases: number
}

export interface ModelHealth {
  models: Record<string, boolean>
  all_loaded: boolean
  loaded_count: number
  total_count: number
}

export interface HealthCheck {
  status: string
  models: Record<string, boolean>
}
