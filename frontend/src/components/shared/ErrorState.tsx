import type { HTMLAttributes } from 'react'
import { AlertTriangle, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui'
import { cn } from '@/lib/utils'

export interface ErrorStateProps extends HTMLAttributes<HTMLDivElement> {
  title?: string
  message: string
  /** When provided, renders a retry button that calls this handler. */
  onRetry?: () => void
}

/** Centered failure placeholder for data fetching or action errors. */
export function ErrorState({
  title = 'Something went wrong',
  message,
  onRetry,
  className,
  ...props
}: ErrorStateProps) {
  return (
    <div
      role="alert"
      className={cn(
        'flex flex-col items-center justify-center px-6 py-16 text-center',
        className,
      )}
      {...props}
    >
      <div className="flex size-12 items-center justify-center rounded-full bg-red-50">
        <AlertTriangle className="size-6 text-red-600" aria-hidden="true" />
      </div>
      <h3 className="mt-4 text-sm font-semibold text-gray-900">{title}</h3>
      <p className="mt-1 max-w-md text-sm text-gray-500">{message}</p>
      {onRetry && (
        <Button variant="secondary" size="sm" className="mt-6" onClick={onRetry}>
          <RefreshCw className="size-4" aria-hidden="true" />
          Retry
        </Button>
      )}
    </div>
  )
}
