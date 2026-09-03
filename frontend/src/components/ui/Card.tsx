import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from '@/lib/utils'

export interface CardProps extends Omit<HTMLAttributes<HTMLDivElement>, 'title'> {
  /** Card heading rendered in the optional header section. */
  title?: ReactNode
  /** Secondary text rendered under the title. */
  description?: ReactNode
  children?: ReactNode
}

/**
 * Surface container with a calm clinical style:
 * white background, subtle border, rounded corners, soft shadow.
 */
export function Card({ title, description, children, className, ...props }: CardProps) {
  return (
    <div
      className={cn('rounded-xl border border-gray-200 bg-white shadow-sm', className)}
      {...props}
    >
      {(title || description) && (
        <div className="border-b border-gray-100 px-5 py-4">
          {title && <h3 className="text-sm font-semibold text-gray-900">{title}</h3>}
          {description && <p className="mt-0.5 text-sm text-gray-500">{description}</p>}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  )
}
