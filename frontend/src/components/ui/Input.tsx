import { forwardRef, useId, type InputHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  /** Label rendered above the input. */
  label?: string
  /** Error message. Renders a red border and replaces helper text when present. */
  error?: string
  /** Hint text rendered below the input (hidden when `error` is present). */
  helperText?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, id, label, error, helperText, ...props }, ref) => {
    const autoId = useId()
    const inputId = id ?? autoId
    const errorId = `${inputId}-error`
    const helperId = `${inputId}-helper`

    return (
      <div className="flex w-full flex-col gap-1.5">
        {label && (
          <label htmlFor={inputId} className="text-sm font-medium text-gray-700">
            {label}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : helperText ? helperId : undefined}
          className={cn(
            'h-10 w-full rounded-lg border bg-white px-3 text-sm text-gray-900 shadow-sm transition-colors',
            'placeholder:text-gray-400',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1',
            error
              ? 'border-red-500 focus-visible:border-red-500 focus-visible:ring-red-500'
              : 'border-gray-300 focus-visible:border-teal-600 focus-visible:ring-teal-600',
            'disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500',
            className,
          )}
          {...props}
        />
        {error ? (
          <p id={errorId} role="alert" className="text-xs font-medium text-red-600">
            {error}
          </p>
        ) : helperText ? (
          <p id={helperId} className="text-xs text-gray-500">
            {helperText}
          </p>
        ) : null}
      </div>
    )
  },
)

Input.displayName = 'Input'
