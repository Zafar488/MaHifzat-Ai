import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from '@/lib/utils'

export type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info'

const variantClasses: Record<BadgeVariant, string> = {
  default: 'bg-gray-100 text-gray-700 ring-gray-500/20',
  success: 'bg-green-50 text-green-700 ring-green-600/25',
  warning: 'bg-amber-50 text-amber-700 ring-amber-600/25',
  danger: 'bg-red-50 text-red-700 ring-red-600/25',
  info: 'bg-blue-50 text-blue-700 ring-blue-600/25',
}

export interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant
  children: ReactNode
}

/** Small pill-shaped label with a soft background and subtle ring. */
export function Badge({ variant = 'default', className, children, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset',
        variantClasses[variant],
        className,
      )}
      {...props}
    >
      {children}
    </span>
  )
}
