import {
  createContext,
  useContext,
  useId,
  type HTMLAttributes,
  type KeyboardEvent,
  type ReactNode,
} from 'react'
import { cn } from '@/lib/utils'

interface TabsContextValue {
  value: string
  onValueChange: (value: string) => void
  baseId: string
}

const TabsContext = createContext<TabsContextValue | null>(null)

function useTabsContext(component: string): TabsContextValue {
  const context = useContext(TabsContext)
  if (!context) {
    throw new Error(`<${component}> must be used within a <Tabs> component.`)
  }
  return context
}

export interface TabsProps extends HTMLAttributes<HTMLDivElement> {
  /** The currently active tab value (controlled). */
  value: string
  onValueChange: (value: string) => void
  children: ReactNode
}

export function Tabs({ value, onValueChange, className, children, ...props }: TabsProps) {
  const baseId = useId()
  return (
    <TabsContext.Provider value={{ value, onValueChange, baseId }}>
      <div className={cn('flex flex-col', className)} {...props}>
        {children}
      </div>
    </TabsContext.Provider>
  )
}

export function TabsList({ className, onKeyDown, ...props }: HTMLAttributes<HTMLDivElement>) {
  const { onValueChange } = useTabsContext('TabsList')

  const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    onKeyDown?.(event)
    const handledKeys = ['ArrowLeft', 'ArrowRight', 'Home', 'End']
    if (!handledKeys.includes(event.key)) return

    const tabs = Array.from(
      event.currentTarget.querySelectorAll<HTMLElement>('[role="tab"]:not([disabled])'),
    )
    if (tabs.length === 0) return

    event.preventDefault()
    const currentIndex = tabs.findIndex((tab) => tab.getAttribute('aria-selected') === 'true')
    let nextIndex = 0
    switch (event.key) {
      case 'ArrowLeft':
        nextIndex = (currentIndex - 1 + tabs.length) % tabs.length
        break
      case 'ArrowRight':
        nextIndex = (currentIndex + 1) % tabs.length
        break
      case 'Home':
        nextIndex = 0
        break
      case 'End':
        nextIndex = tabs.length - 1
        break
    }
    const nextTab = tabs[nextIndex]
    const nextValue = nextTab?.dataset.value
    if (nextTab && nextValue !== undefined) {
      nextTab.focus()
      onValueChange(nextValue)
    }
  }

  return (
    <div
      role="tablist"
      onKeyDown={handleKeyDown}
      className={cn('flex gap-1 overflow-x-auto border-b border-gray-200', className)}
      {...props}
    />
  )
}

export interface TabsTriggerProps extends HTMLAttributes<HTMLButtonElement> {
  value: string
  disabled?: boolean
}

export function TabsTrigger({
  value,
  disabled = false,
  className,
  children,
  ...props
}: TabsTriggerProps) {
  const { value: activeValue, onValueChange, baseId } = useTabsContext('TabsTrigger')
  const isActive = activeValue === value

  return (
    <button
      type="button"
      role="tab"
      data-value={value}
      aria-selected={isActive}
      aria-controls={`${baseId}-content-${value}`}
      id={`${baseId}-trigger-${value}`}
      tabIndex={isActive ? 0 : -1}
      disabled={disabled}
      onClick={() => onValueChange(value)}
      className={cn(
        '-mb-px inline-flex items-center gap-2 whitespace-nowrap border-b-2 px-3 py-2.5 text-sm font-medium transition-colors',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-teal-600',
        isActive
          ? 'border-teal-600 text-teal-700'
          : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700',
        disabled && 'pointer-events-none opacity-50',
        className,
      )}
      {...props}
    >
      {children}
    </button>
  )
}

export interface TabsContentProps extends HTMLAttributes<HTMLDivElement> {
  value: string
}

export function TabsContent({ value, className, children, ...props }: TabsContentProps) {
  const { value: activeValue, baseId } = useTabsContext('TabsContent')
  if (activeValue !== value) return null

  return (
    <div
      role="tabpanel"
      id={`${baseId}-content-${value}`}
      aria-labelledby={`${baseId}-trigger-${value}`}
      tabIndex={0}
      className={cn(
        'rounded-lg pt-4 outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-teal-600',
        className,
      )}
      {...props}
    >
      {children}
    </div>
  )
}
