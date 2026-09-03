import { cn } from '@/lib/utils'

export type SkeletonVariant = 'text' | 'circular' | 'rectangular'

const variantClasses: Record<SkeletonVariant, string> = {
  text: 'h-4 rounded-md',
  circular: 'aspect-square rounded-full',
  rectangular: 'rounded-lg',
}

export interface SkeletonProps {
  className?: string
  variant?: SkeletonVariant
}

/**
 * Pulsing placeholder for loading states. Compose multiple skeletons
 * (e.g. inside a Card) to sketch the shape of the content being loaded.
 */
export function Skeleton({ className, variant = 'text' }: SkeletonProps) {
  return (
    <div
      aria-hidden="true"
      className={cn('animate-pulse bg-gray-200/80', variantClasses[variant], className)}
    />
  )
}
