export interface NodeInfo {
  name: string
  description: string
}

export interface WorkflowRequest {
  patient_id: string
  case_id: string
  language?: string
  channel?: string
  vitals: Record<string, any>
  symptoms: string[]
  demographics: Record<string, any>
  ctg_data?: Record<string, any> | null
}

export interface WorkflowResponse {
  status: string
  result: Record<string, any>
}
