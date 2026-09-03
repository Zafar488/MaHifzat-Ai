import { api } from '@/lib/api-client'
import type { DashboardData, ModelHealth } from '@/types/analytics'

export const analyticsApi = {
  getDashboardStats: async (): Promise<DashboardData> => {
    const { data } = await api.get<DashboardData>('/analytics/dashboard')
    return data
  },

  getModelHealth: async (): Promise<ModelHealth> => {
    const { data } = await api.get<ModelHealth>('/analytics/models/health')
    return data
  },
}
