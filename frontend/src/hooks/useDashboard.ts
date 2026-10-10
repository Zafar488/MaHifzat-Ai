import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '@/services/api/analytics'

export function useDashboardStats() {
  return useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: analyticsApi.getDashboardStats,
    staleTime: 60 * 1000, // 1 minute
  })
}

export function useModelHealth() {
  return useQuery({
    queryKey: ['dashboard', 'modelHealth'],
    queryFn: analyticsApi.getModelHealth,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}
