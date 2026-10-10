import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api-client'
import type { PatientCreate, PatientProfile } from '@/types/patient'

export const patientsApi = {
  listPatients: async (skip = 0, limit = 100): Promise<PatientProfile[]> => {
    const { data } = await api.get<PatientProfile[]>('/patients', { params: { skip, limit } })
    return data
  },
  
  getPatient: async (patientId: string): Promise<PatientProfile> => {
    const { data } = await api.get<PatientProfile>(`/patients/${patientId}`)
    return data
  },
  
  createPatient: async (payload: PatientCreate): Promise<PatientProfile> => {
    const { data } = await api.post<PatientProfile>('/patients', payload)
    return data
  },
  
  updatePatient: async ({ id, payload }: { id: string; payload: PatientCreate }): Promise<PatientProfile> => {
    const { data } = await api.put<PatientProfile>(`/patients/${id}`, payload)
    return data
  }
}

export function usePatients(skip = 0, limit = 100) {
  return useQuery({
    queryKey: ['patients', skip, limit],
    queryFn: () => patientsApi.listPatients(skip, limit),
  })
}

export function usePatient(patientId: string) {
  return useQuery({
    queryKey: ['patient', patientId],
    queryFn: () => patientsApi.getPatient(patientId),
    enabled: !!patientId,
  })
}

export function useCreatePatient() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: patientsApi.createPatient,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patients'] })
    },
  })
}

export function useUpdatePatient() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: patientsApi.updatePatient,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['patient', data.patient_id] })
      queryClient.invalidateQueries({ queryKey: ['patients'] })
    },
  })
}
