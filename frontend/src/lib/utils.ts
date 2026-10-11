import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric'
  })
}

export function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
}

export function getErrorMessage(err: any, fallback: string = 'An error occurred'): string {
  if (!err) return fallback

  const detail = err?.response?.data?.detail ?? err?.data?.detail ?? err?.message ?? err

  if (typeof detail === 'string') {
    return detail
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object') {
          const field = Array.isArray(item.loc) ? item.loc.slice(-1)[0] : null
          const msg = item.msg || item.message || JSON.stringify(item)
          return field && field !== 'body' ? `${field}: ${msg}` : msg
        }
        return String(item)
      })
      .join('; ')
  }

  if (typeof detail === 'object' && detail !== null) {
    if (detail.msg) return String(detail.msg)
    if (detail.message) return String(detail.message)
    if (detail.detail && typeof detail.detail === 'string') return detail.detail
    return JSON.stringify(detail)
  }

  return String(detail)
}
