import { forwardRef, useId, type SelectHTMLAttributes } from 'react'
import { ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface SelectOption {
  value: string
  label: string
}

export interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  /** Label rendered above the select. */
  label?: string
  /** Error message. Renders a red border and replaces helper text when present. */
  error?: string
  /** Hint text rendered below the select (hidden when `error` is present). */
  helperText?: string
  /** Options rendered inside the native select. */
  options: SelectOption[]
  /** Renders a disabled placeholder option with empty value. */
  placeholder?: string
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  (
    { className, id, label, error, helperText, options, placeholder, children, ...props },
    ref,
  ) => {
    const autoId = useId()
    const selectId = id ?? autoId
    const errorId = `${selectId}-error`
    const helperId = `${selectId}-helper`

    return (
      <div className="flex w-full flex-col gap-1.5">
        {label && (
          <label htmlFor={selectId} className="text-sm font-medium text-gray-700">
            {label}
          </label>
        )}
        <div className="relative">
          <select
            ref={ref}
            id={selectId}
            aria-invalid={error ? true : undefined}
            aria-describedby={error ? errorId : helperText ? helperId : undefined}
            className={cn(
              'h-10 w-full appearance-none rounded-lg border bg-white py-0 pl-3 pr-9 text-sm text-gray-900 shadow-sm transition-colors',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1',
              error
                ? 'border-red-500 focus-visible:border-red-500 focus-visible:ring-red-500'
                : 'border-gray-300 focus-visible:border-teal-600 focus-visible:ring-teal-600',
              'disabled:cursor-not-allowed disabled:bg-gray-50 disabled:text-gray-500',
              className,
            )}
            {...props}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
            {children}
          </select>
          <ChevronDown
            className="pointer-events-none absolute right-3 top-1/2 size-4 -translate-y-1/2 text-gray-400"
            aria-hidden="true"
          />
        </div>
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

Select.displayName = 'Select'
