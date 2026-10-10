import type { HTMLAttributes } from 'react'
import { Sparkles } from 'lucide-react'
import { Card } from '@/components/ui'
import { RiskBadge, type RiskLevel } from './RiskBadge'
import { cn, formatDateTime } from '@/lib/utils'

export interface AIInsightCardProps extends HTMLAttributes<HTMLDivElement> {
  title: string
  /** Maps to a RiskBadge: high / medium / low. */
  severity?: Exclude<RiskLevel, 'unknown' | 'emergency'>
  /** Model confidence between 0 and 1. */
  confidence?: number
  /** Key drivers the model weighed most heavily. */
  factors?: string[]
  /** Suggested next step for the clinician. */
  recommendation?: string
  /** ISO timestamp of when the insight was generated. */
  timestamp?: string
  /** Name of the model that produced the insight, e.g. "maternalguard v1.2". */
  model?: string
}

/**
 * Presents an AI-generated clinical insight with provenance.
 * Marked by a teal left border so machine-generated content is always
 * visually distinct from clinician-authored content.
 */
export function AIInsightCard({
  title,
  severity,
  confidence,
  factors = [],
  recommendation,
  timestamp,
  model,
  className,
  ...props
}: AIInsightCardProps) {
  const confidencePercent =
    typeof confidence === 'number'
      ? Math.round(Math.min(1, Math.max(0, confidence)) * 100)
      : null

  return (
    <Card className={cn('border-l-4 border-l-teal-600', className)} {...props}>
      <div className="flex flex-col gap-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-teal-50 px-2.5 py-0.5 text-xs font-semibold text-teal-700 ring-1 ring-inset ring-teal-600/20">
              <Sparkles className="size-3" aria-hidden="true" />
              AI-Generated
            </span>
            <h3 className="mt-2 text-sm font-semibold text-gray-900">{title}</h3>
          </div>
          {severity && <RiskBadge level={severity} />}
        </div>

        {confidencePercent !== null && (
          <div>
            <div className="mb-1 flex items-center justify-between text-xs">
              <span className="font-medium text-gray-500">Model confidence</span>
              <span className="font-semibold text-gray-700 tabular-nums">
                {confidencePercent}%
              </span>
            </div>
            <div
              role="progressbar"
              aria-valuenow={confidencePercent}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Model confidence"
              className="h-1.5 w-full overflow-hidden rounded-full bg-gray-100"
            >
              <div
                className="h-full rounded-full bg-teal-600 transition-[width]"
                style={{ width: `${confidencePercent}%` }}
              />
            </div>
          </div>
        )}

        {factors.length > 0 && (
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-gray-400">
              Contributing factors
            </p>
            <ul className="mt-2 flex flex-col gap-1.5">
              {factors.map((factor, index) => (
                <li
                  key={`${factor}-${index}`}
                  className="flex items-start gap-2 text-sm text-gray-600"
                >
                  <span
                    className="mt-1.5 size-1.5 shrink-0 rounded-full bg-teal-500"
                    aria-hidden="true"
                  />
                  {factor}
                </li>
              ))}
            </ul>
          </div>
        )}

        {recommendation && (
          <div className="rounded-lg bg-teal-50/70 p-3">
            <p className="text-sm font-medium text-teal-800">Recommendation</p>
            <p className="mt-1 text-sm text-gray-700">{recommendation}</p>
          </div>
        )}

        {(model || timestamp) && (
          <div className="flex flex-wrap items-center justify-between gap-2 border-t border-gray-100 pt-3 text-xs text-gray-400">
            {model && <span className="font-mono">{model}</span>}
            {timestamp && <time dateTime={timestamp}>{formatDateTime(timestamp)}</time>}
          </div>
        )}
      </div>
    </Card>
  )
}
