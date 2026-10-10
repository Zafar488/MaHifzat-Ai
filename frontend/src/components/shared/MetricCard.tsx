import type { HTMLAttributes } from 'react'
import { Minus, TrendingDown, TrendingUp, type LucideIcon } from 'lucide-react'
import { Card } from '@/components/ui'
import { cn } from '@/lib/utils'

export type MetricTrend = 'up' | 'down' | 'neutral'

const trendConfig: Record<MetricTrend, { icon: LucideIcon; className: string }> = {
  up: { icon: TrendingUp, className: 'text-green-600' },
  down: { icon: TrendingDown, className: 'text-red-600' },
  neutral: { icon: Minus, className: 'text-gray-400' },
}

export interface MetricCardProps extends HTMLAttributes<HTMLDivElement> {
  /** Label shown under the value, e.g. "Active patients". */
  title: string
  /** The metric itself, rendered large. */
  value: string | number
  icon?: LucideIcon
  trend?: MetricTrend
  /** Extra context shown under the title. */
  description?: string
}

/** Dashboard KPI card: large value, title underneath, optional icon and trend arrow. */
export function MetricCard({
  title,
  value,
  icon: Icon,
  trend,
  description,
  className,
  ...props
}: MetricCardProps) {
  const trendEntry = trend ? trendConfig[trend] : undefined
  const TrendIcon = trendEntry?.icon

  return (
    <Card className={className} {...props}>
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-3xl font-bold tracking-tight text-gray-900 tabular-nums">
            {value}
          </p>
          <p className="mt-1 text-sm font-medium text-gray-500">{title}</p>
          {description && <p className="mt-1 text-xs text-gray-400">{description}</p>}
        </div>
        {(Icon || TrendIcon) && (
          <div className="flex shrink-0 flex-col items-end gap-2">
            {Icon && (
              <div className="flex size-10 items-center justify-center rounded-lg bg-teal-50">
                <Icon className="size-5 text-teal-600" aria-hidden="true" />
              </div>
            )}
            {trendEntry && TrendIcon && (
              <span
                className={cn('inline-flex items-center', trendEntry.className)}
                aria-label={`Trend: ${trend}`}
              >
                <TrendIcon className="size-4" aria-hidden="true" />
              </span>
            )}
          </div>
        )}
      </div>
    </Card>
  )
}
