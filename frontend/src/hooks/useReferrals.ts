import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import type { Referral } from '@/types/referral'

export const referralApi = {
  listReferrals: async (params?: { status?: string; limit?: number }): Promise<Referral[]> => {
    const { data } = await api.get<Referral[]>('/referrals', { params })
    return data
  },
}

export function useReferrals(params?: { status?: string; limit?: number }) {
  return useQuery({
    queryKey: ['referrals', params],
    queryFn: () => referralApi.listReferrals(params),
  })
}
