import { Link, NavLink } from 'react-router-dom'
import {
  Activity,
  ArrowRightLeft,
  BarChart3,
  Bell,
  Bot,
  ChevronsLeft,
  ChevronsRight,
  FileText,
  HeartPulse,
  LayoutDashboard,
  LogOut,
  Settings,
  Users,
  X,
  type LucideIcon,
} from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { UserRole } from '@/types'
import { cn } from '@/lib/utils'
import { getUserInitials, ROLE_BADGE_STYLES } from './user'

interface NavItem {
  to: string
  label: string
  icon: LucideIcon
  /** When set, only these roles can see the item. Omit for all roles. */
  roles?: readonly UserRole[]
}

interface NavGroup {
  label: string
  items: readonly NavItem[]
}

const NAV_GROUPS: readonly NavGroup[] = [
  {
    label: 'Overview',
    items: [{ to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard }],
  },
  {
    label: 'Clinical',
    items: [
      { to: '/patients', label: 'Patients', icon: Users },
      { to: '/risk-assessment', label: 'Risk Assessment', icon: Activity },
      { to: '/referrals', label: 'Referrals', icon: ArrowRightLeft },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      {
        to: '/agents',
        label: 'AI Agents',
        icon: Bot,
        roles: [UserRole.CLINICIAN, UserRole.ADMIN],
      },
      { to: '/alerts', label: 'Alerts', icon: Bell },
      { to: '/analytics', label: 'Analytics', icon: BarChart3 },
    ],
  },
  {
    label: 'System',
    items: [
      { to: '/audit', label: 'Audit Log', icon: FileText, roles: [UserRole.ADMIN] },
      { to: '/settings', label: 'Settings', icon: Settings },
    ],
  },
]

export interface SidebarProps {
  /** Whether the mobile drawer is open. */
  mobileOpen: boolean
  /** Closes the mobile drawer (backdrop, scrim, X button, route change). */
  onMobileClose: () => void
  /** Whether the desktop sidebar is collapsed to icon-only mode. */
  collapsed: boolean
  /** Toggles the desktop collapsed state. */
  onToggleCollapsed: () => void
}

export function Sidebar({ mobileOpen, onMobileClose, collapsed, onToggleCollapsed }: SidebarProps) {
  const { user, logout } = useAuth()

  const visibleGroups = NAV_GROUPS.map((group) => ({
    ...group,
    items: group.items.filter((item) => !item.roles || (user !== null && item.roles.includes(user.role))),
  })).filter((group) => group.items.length > 0)

  const initials = user ? getUserInitials(user.user_id) : '··'

  return (
    <>
      {/* Mobile scrim behind the drawer. */}
      <div
        aria-hidden="true"
        onClick={onMobileClose}
        className={cn(
          'fixed inset-0 z-40 bg-gray-900/40 backdrop-blur-[2px] transition-opacity duration-200 md:hidden',
          mobileOpen ? 'opacity-100' : 'pointer-events-none opacity-0',
        )}
      />

      {/*
       * Desktop: static column that animates between w-64 and w-20.
       * Mobile: fixed drawer that slides in from the left (always full
       * width with labels — the collapsed state only applies from `md:` up).
       */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex w-72 shrink-0 flex-col border-r border-gray-200 bg-white transition-all duration-200 ease-out',
          'md:static md:z-auto md:translate-x-0',
          collapsed ? 'md:w-20' : 'md:w-64',
          mobileOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        {/* Brand */}
        <div className="flex h-16 shrink-0 items-center gap-2 border-b border-gray-100 px-4">
          <Link
            to="/dashboard"
            className={cn(
              'flex min-w-0 flex-1 items-center gap-3 rounded-lg py-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-600',
              collapsed && 'md:justify-center',
            )}
          >
            <span className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-teal-500 to-teal-700 text-white shadow-sm shadow-teal-600/30">
              <HeartPulse className="size-5" aria-hidden="true" />
            </span>
            <span className={cn('min-w-0', collapsed && 'md:hidden')}>
              <span className="block text-[15px] font-extrabold leading-none tracking-tight text-gray-900">
                MaaHifazat <span className="text-teal-600">AI</span>
              </span>
              <span className="mt-1 block font-mono text-[9px] uppercase leading-none tracking-[0.28em] text-gray-400">
                Maternal Care
              </span>
            </span>
          </Link>
          <button
            type="button"
            onClick={onMobileClose}
            aria-label="Close navigation menu"
            className="rounded-lg p-2 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-600 md:hidden"
          >
            <X className="size-5" aria-hidden="true" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-4" aria-label="Primary">
          {visibleGroups.map((group) => (
            <div key={group.label}>
              <p
                className={cn(
                  'px-3 pb-1.5 font-mono text-[9px] font-semibold uppercase tracking-[0.3em] text-gray-400',
                  collapsed && 'md:hidden',
                )}
              >
                {group.label}
              </p>
              <ul className="space-y-1">
                {group.items.map((item) => (
                  <li key={item.to}>
                    <NavLink
                      to={item.to}
                      end={item.to === '/dashboard'}
                      title={item.label}
                      className={({ isActive }) =>
                        cn(
                          'group flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-600',
                          collapsed && 'md:justify-center md:px-2',
                          isActive
                            ? 'bg-teal-600 text-white shadow-sm shadow-teal-600/30'
                            : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900',
                        )
                      }
                    >
                      <item.icon className="size-[18px] shrink-0" aria-hidden="true" />
                      <span className={cn('truncate', collapsed && 'md:hidden')}>{item.label}</span>
                    </NavLink>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </nav>

        {/* Footer — collapse toggle (desktop) + signed-in user + sign out */}
        <div className="shrink-0 border-t border-gray-100 p-3">
          <button
            type="button"
            onClick={onToggleCollapsed}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className={cn(
              'hidden w-full items-center gap-3 rounded-lg px-3 py-1.5 text-xs font-medium text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-600 md:flex',
              collapsed && 'md:justify-center md:px-2',
            )}
          >
            {collapsed ? (
              <ChevronsRight className="size-4 shrink-0" aria-hidden="true" />
            ) : (
              <ChevronsLeft className="size-4 shrink-0" aria-hidden="true" />
            )}
            <span className={cn(collapsed && 'md:hidden')}>Collapse</span>
          </button>

          <div
            className={cn(
              'mt-2 flex items-center gap-3',
              collapsed && 'md:flex-col md:items-center md:gap-1.5',
            )}
          >
            <span className="flex size-9 shrink-0 items-center justify-center rounded-full bg-teal-50 text-xs font-semibold text-teal-700 ring-1 ring-inset ring-teal-600/20">
              {initials}
            </span>
            <div className={cn('min-w-0 flex-1', collapsed && 'md:hidden')}>
              <p className="truncate text-sm font-semibold leading-tight text-gray-900">
                {user?.user_id ?? 'Signed in'}
              </p>
              <span
                className={cn(
                  'mt-1 inline-flex items-center rounded-full px-1.5 py-px text-[10px] font-medium capitalize ring-1 ring-inset',
                  user ? ROLE_BADGE_STYLES[user.role] : 'bg-gray-100 text-gray-600 ring-gray-500/20',
                )}
              >
                {user?.role ?? '—'}
              </span>
            </div>
            <button
              type="button"
              onClick={logout}
              title="Sign out"
              aria-label="Sign out"
              className="shrink-0 rounded-lg p-2 text-gray-400 transition-colors hover:bg-red-50 hover:text-red-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500"
            >
              <LogOut className="size-4" aria-hidden="true" />
            </button>
          </div>
        </div>
      </aside>
    </>
  )
}
