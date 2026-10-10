export type AlertChannel = 'sms' | 'whatsapp' | 'emergency'

export interface SendAlertRequest {
  recipient: string
  message: string
  channel: AlertChannel
  patient_id?: string
  priority?: string
}

export interface AlertResponse {
  alert_id: string
  message_id: string
  channel: AlertChannel
  recipient: string
  status: string
  sent_at: string
  patient_id?: string
}
