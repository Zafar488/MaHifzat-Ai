import { cn } from '@/lib/utils'

export type ReferralStatus = 'pending' | 'accepted' | 'in_transit' | 'completed' | 'cancelled'

interface StatusConfig {
  label: string
  className: string
}

const statusConfig: Record<ReferralStatus, StatusConfig> = {
  pending: {
    label: 'Pending',
    className: 'bg-amber-50 text-amber-700 ring-amber-600/25',
  },
  accepted: {
    label: 'Accepted',
    className: 'bg-blue-50 text-blue-700 ring-blue-600/25',
  },
  in_transit: {
    label: 'In Transit',
    className: 'bg-purple-50 text-purple-700 ring-purple-600/25',
  },
  completed: {
    label: 'Completed',
    className: 'bg-green-50 text-green-700 ring-green-600/25',
  },
  cancelled: {
    label: 'Cancelled',
    className: 'bg-gray-100 text-gray-600 ring-gray-500/25',
  },
}

export interface StatusBadgeProps {
  /** Status value, e.g. 'in_transit'. Unknown values fall back to a neutral gray badge. */
  status: string
  className?: string
}

/** Referral/workflow status indicator with a leading colored dot. */
export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = statusConfig[status as ReferralStatus]
  const label = config?.label ?? status.replace(/_/g, ' ')

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium capitalize ring-1 ring-inset',
        config?.className ?? 'bg-gray-100 text-gray-600 ring-gray-500/25',
        className,
      )}
    >
      <span className="size-1.5 rounded-full bg-current" aria-hidden="true" />
      {label}
    </span>
  )
}
