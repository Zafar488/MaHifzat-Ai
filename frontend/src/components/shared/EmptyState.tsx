import type { HTMLAttributes, ReactNode } from 'react'
import { Inbox, type LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface EmptyStateProps extends HTMLAttributes<HTMLDivElement> {
  /** Lucide icon component shown above the title. */
  icon?: LucideIcon
  title: string
  description?: string
  /** Optional call-to-action (e.g. a Button) rendered below the text. */
  action?: ReactNode
}

/** Centered "nothing here yet" placeholder for lists and tables. */
export function EmptyState({
  icon: Icon = Inbox,
  title,
  description,
  action,
  className,
  ...props
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center px-6 py-16 text-center',
        className,
      )}
      {...props}
    >
      <div className="flex size-12 items-center justify-center rounded-full bg-gray-100">
        <Icon className="size-6 text-gray-400" aria-hidden="true" />
      </div>
      <h3 className="mt-4 text-sm font-semibold text-gray-900">{title}</h3>
      {description && (
        <p className="mt-1 max-w-sm text-sm text-gray-500">{description}</p>
      )}
      {action && <div className="mt-6">{action}</div>}
    </div>
  )
}
