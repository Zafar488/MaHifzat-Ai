import { AlertCircle, AlertTriangle, CheckCircle, HelpCircle, type LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

export type RiskLevel = 'high' | 'medium' | 'low' | 'unknown' | 'emergency'

interface RiskConfig {
  label: string
  icon: LucideIcon
  className: string
}

const riskConfig: Record<RiskLevel, RiskConfig> = {
  emergency: {
    label: 'Emergency',
    icon: AlertTriangle,
    className: 'bg-red-600 text-white ring-red-600',
  },
  high: {
    label: 'High Risk',
    icon: AlertTriangle,
    className: 'bg-red-50 text-red-700 ring-red-600/25',
  },
  medium: {
    label: 'Medium Risk',
    icon: AlertCircle,
    className: 'bg-amber-50 text-amber-700 ring-amber-600/25',
  },
  low: {
    label: 'Low Risk',
    icon: CheckCircle,
    className: 'bg-green-50 text-green-700 ring-green-600/25',
  },
  unknown: {
    label: 'Unknown Risk',
    icon: HelpCircle,
    className: 'bg-gray-100 text-gray-600 ring-gray-500/25',
  },
}

export interface RiskBadgeProps {
  level: RiskLevel
  className?: string
}

/**
 * Clinical risk indicator. Always shows an icon AND a text label so
 * information is never conveyed by color alone.
 */
export function RiskBadge({ level, className }: RiskBadgeProps) {
  const { label, icon: Icon, className: badgeClassName } = riskConfig[level] ?? riskConfig.unknown

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset',
        badgeClassName,
        className,
      )}
    >
      <Icon className="size-3.5 shrink-0" aria-hidden="true" />
      {label}
    </span>
  )
}
