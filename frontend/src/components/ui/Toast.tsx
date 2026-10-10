import { useCallback, useSyncExternalStore, type ReactNode } from 'react'
import { AlertCircle, CheckCircle, Info, X } from 'lucide-react'
import { cn } from '@/lib/utils'

export type ToastVariant = 'success' | 'error' | 'info'

export interface ToastItem {
  id: number
  message: ReactNode
  variant: ToastVariant
}

const TOAST_DURATION_MS = 5000

/*
 * Tiny module-level store shared between the imperative `toast` API and
 * the <ToastContainer /> rendered at the app root. The container subscribes
 * with useSyncExternalStore, so toasts work from anywhere — including
 * event handlers and non-component modules.
 */
let toasts: ToastItem[] = []
let nextId = 1
const listeners = new Set<() => void>()

function emitChange() {
  for (const listener of listeners) {
    listener()
  }
}

function setToasts(update: (previous: ToastItem[]) => ToastItem[]) {
  toasts = update(toasts)
  emitChange()
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

function getSnapshot(): ToastItem[] {
  return toasts
}

function dismissToast(id: number) {
  setToasts((previous) => previous.filter((toastItem) => toastItem.id !== id))
}

function pushToast(message: ReactNode, variant: ToastVariant) {
  const id = nextId++
  setToasts((previous) => [...previous, { id, message, variant }])
  window.setTimeout(() => dismissToast(id), TOAST_DURATION_MS)
}

export const toast = {
  success: (message: ReactNode) => pushToast(message, 'success'),
  error: (message: ReactNode) => pushToast(message, 'error'),
  info: (message: ReactNode) => pushToast(message, 'info'),
  dismiss: (id: number) => dismissToast(id),
}

const variantConfig: Record<ToastVariant, { icon: typeof CheckCircle; iconClassName: string }> = {
  success: { icon: CheckCircle, iconClassName: 'text-green-600' },
  error: { icon: AlertCircle, iconClassName: 'text-red-600' },
  info: { icon: Info, iconClassName: 'text-blue-600' },
}

/** Render once at the application root. Shows toasts pushed via `toast.*`. */
export function ToastContainer() {
  const currentToasts = useSyncExternalStore(subscribe, getSnapshot)
  const handleDismiss = useCallback((id: number) => dismissToast(id), [])

  return (
    <div
      aria-live="polite"
      aria-label="Notifications"
      className="pointer-events-none fixed inset-x-4 bottom-4 z-[60] flex flex-col gap-2 sm:left-auto sm:w-full sm:max-w-sm"
    >
      {currentToasts.map((toastItem) => {
        const { icon: Icon, iconClassName } = variantConfig[toastItem.variant]
        return (
          <div
            key={toastItem.id}
            role="status"
            className="pointer-events-auto flex items-start gap-3 rounded-lg border border-gray-200 bg-white p-4 shadow-lg animate-toast-slide-in"
          >
            <Icon className={cn('mt-0.5 size-5 shrink-0', iconClassName)} aria-hidden="true" />
            <div className="min-w-0 flex-1 pt-0.5 text-sm text-gray-700">
              {toastItem.message}
            </div>
            <button
              type="button"
              onClick={() => handleDismiss(toastItem.id)}
              aria-label="Dismiss notification"
              className="rounded-md p-0.5 text-gray-400 transition-colors hover:text-gray-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-600"
            >
              <X className="size-4" aria-hidden="true" />
            </button>
          </div>
        )
      })}
    </div>
  )
}
