import { useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { Bell, ChevronDown, LogOut, Menu } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { cn } from '@/lib/utils'
import { getUserInitials } from './user'

interface PageMeta {
  section: string
  title: string
  match: (pathname: string) => boolean
}

/**
 * Route → page context for the header title area.
 * Ordered most-specific-first so `/patients/new` wins over `/patients`.
 */
const PAGE_META: readonly PageMeta[] = [
  { section: 'Overview', title: 'Dashboard', match: (p) => p.startsWith('/dashboard') },
  { section: 'Clinical', title: 'Register Patient', match: (p) => p.startsWith('/patients/new') },
  { section: 'Clinical', title: 'Patient Profile', match: (p) => /^\/patients\/[^/]+/.test(p) },
  { section: 'Clinical', title: 'Patients', match: (p) => p.startsWith('/patients') },
  { section: 'Clinical', title: 'Risk Assessment', match: (p) => p.startsWith('/risk-assessment') },
  { section: 'Clinical', title: 'Referrals', match: (p) => p.startsWith('/referrals') },
  { section: 'Intelligence', title: 'AI Agents', match: (p) => p.startsWith('/agents') },
  { section: 'Intelligence', title: 'Alerts', match: (p) => p.startsWith('/alerts') },
  { section: 'Intelligence', title: 'Analytics', match: (p) => p.startsWith('/analytics') },
  { section: 'System', title: 'Audit Log', match: (p) => p.startsWith('/audit') },
  { section: 'System', title: 'Settings', match: (p) => p.startsWith('/settings') },
]

const FALLBACK_PAGE: PageMeta = { section: 'MaaHifazat AI', title: 'Dashboard', match: () => false }

export interface HeaderProps {
  /** Opens the mobile navigation drawer. */
  onMenuClick: () => void
}

export function Header({ onMenuClick }: HeaderProps) {
  const { user, logout } = useAuth()
  const { pathname } = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  const page = PAGE_META.find((meta) => meta.match(pathname)) ?? FALLBACK_PAGE
  const initials = user ? getUserInitials(user.user_id) : '··'

  // Dismiss the account dropdown on any outside pointer press.
  useEffect(() => {
    if (!menuOpen) return
    const handlePointerDown = (event: PointerEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener('pointerdown', handlePointerDown)
    return () => document.removeEventListener('pointerdown', handlePointerDown)
  }, [menuOpen])

  return (
    <header className="sticky top-0 z-30 flex h-16 shrink-0 items-center gap-3 border-b border-gray-200 bg-white/90 px-4 backdrop-blur sm:gap-4 sm:px-6">
      {/* Left — mobile nav toggle + page context */}
      <button
        type="button"
        onClick={onMenuClick}
        aria-label="Open navigation menu"
        className="rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-600 md:hidden"
      >
        <Menu className="size-5" aria-hidden="true" />
      </button>

      <div className="min-w-0">
        <p className="hidden font-mono text-[10px] font-medium uppercase tracking-[0.28em] text-gray-400 sm:block">
          {page.section}
        </p>
        <h1 className="truncate text-base font-semibold tracking-tight text-gray-900">
          {page.title}
        </h1>
      </div>

      {/* Right — notifications + account */}
      <div className="ml-auto flex items-center gap-1.5 sm:gap-3">
        <button
          type="button"
          aria-label="Notifications"
          className="relative rounded-lg p-2 text-gray-500 transition-colors hover:bg-gray-100 hover:text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-600"
        >
          <Bell className="size-5" aria-hidden="true" />
          {/* Placeholder indicator — wired to real alerts in a later task. */}
          <span
            className="absolute right-1.5 top-1.5 size-2 rounded-full bg-red-500 ring-2 ring-white"
            aria-hidden="true"
          />
        </button>

        <div className="hidden h-6 w-px bg-gray-200 sm:block" aria-hidden="true" />

        <div className="relative" ref={menuRef}>
          <button
            type="button"
            onClick={() => setMenuOpen((open) => !open)}
            aria-haspopup="menu"
            aria-expanded={menuOpen}
            className="flex items-center gap-2.5 rounded-lg py-1.5 pl-1.5 pr-2 transition-colors hover:bg-gray-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-600"
          >
            <span className="flex size-8 items-center justify-center rounded-full bg-teal-600 text-xs font-semibold text-white">
              {initials}
            </span>
            <span className="hidden text-left sm:block">
              <span className="block max-w-32 truncate text-sm font-medium leading-tight text-gray-900">
                {user?.user_id ?? 'Signed in'}
              </span>
              <span className="block font-mono text-[10px] uppercase leading-tight tracking-[0.22em] text-gray-400">
                {user?.role ?? '—'}
              </span>
            </span>
            <ChevronDown
              className={cn(
                'size-4 shrink-0 text-gray-400 transition-transform duration-200',
                menuOpen && 'rotate-180',
              )}
              aria-hidden="true"
            />
          </button>

          {menuOpen && (
            <div
              role="menu"
              aria-label="Account menu"
              className="absolute right-0 top-full z-50 mt-2 w-60 origin-top-right animate-modal-pop-in rounded-xl border border-gray-200 bg-white p-1.5 shadow-lg shadow-gray-900/10"
            >
              <div className="flex items-center gap-3 rounded-lg px-2 py-2">
                <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-teal-600 text-xs font-semibold text-white">
                  {initials}
                </span>
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-gray-900">
                    {user?.user_id ?? 'Signed in'}
                  </p>
                  <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-gray-400">
                    {user?.role ?? '—'}
                  </p>
                </div>
              </div>
              <div className="mx-1 my-1 h-px bg-gray-100" aria-hidden="true" />
              <button
                type="button"
                role="menuitem"
                onClick={logout}
                className="flex w-full items-center gap-2.5 rounded-lg px-2 py-2 text-sm font-medium text-red-600 transition-colors hover:bg-red-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500"
              >
                <LogOut className="size-4" aria-hidden="true" />
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
