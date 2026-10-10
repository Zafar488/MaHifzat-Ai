import { Link, Navigate, Outlet, useLocation } from 'react-router-dom'
import { HeartPulse, Loader2, ShieldAlert } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import type { UserRole } from '@/types'

export interface ProtectedRouteProps {
  /** When provided, only these roles may pass. Omit to allow any authenticated user. */
  allowedRoles?: readonly UserRole[]
}

/** Splash shown while the stored session is being restored on first load. */
function AuthSplash() {
  return (
    <div className="app-canvas flex h-dvh flex-col items-center justify-center gap-5">
      <span className="flex size-14 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-500 to-teal-700 text-white shadow-lg shadow-teal-600/25">
        <HeartPulse className="size-7" aria-hidden="true" />
      </span>
      <div className="flex items-center gap-2.5">
        <Loader2 className="size-4 animate-spin text-teal-600" aria-hidden="true" />
        <span className="font-mono text-[11px] uppercase tracking-[0.3em] text-gray-400">
          Restoring session
        </span>
      </div>
    </div>
  )
}

/** Shown when the signed-in user's role is not permitted for a route. */
function AccessDenied({ role }: { role: UserRole }) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-5 px-4 py-16 text-center">
      <span className="flex size-14 items-center justify-center rounded-2xl bg-red-50 text-red-500 ring-1 ring-inset ring-red-600/15">
        <ShieldAlert className="size-7" aria-hidden="true" />
      </span>
      <div className="max-w-md">
        <h2 className="text-lg font-semibold tracking-tight text-gray-900">
          Insufficient Permissions
        </h2>
        <p className="mt-1.5 text-sm leading-6 text-gray-500">
          The{' '}
          <span className="font-mono text-xs font-medium uppercase tracking-wider text-red-600">
            {role}
          </span>{' '}
          role does not have access to this area. Contact an administrator if you believe this is a
          mistake.
        </p>
      </div>
      <Link
        to="/dashboard"
        className="inline-flex h-10 items-center rounded-lg bg-teal-600 px-4 text-sm font-medium text-white shadow-sm transition-colors hover:bg-teal-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-600 focus-visible:ring-offset-2"
      >
        Return to Dashboard
      </Link>
    </div>
  )
}

/**
 * Route guard used as a layout route:
 * - unauthenticated → redirect to /login (remembering the current location)
 * - wrong role       → inline "Insufficient Permissions" screen
 * - authorized       → render the nested routes via <Outlet />
 */
export function ProtectedRoute({ allowedRoles }: ProtectedRouteProps) {
  const { isAuthenticated, isInitializing, user } = useAuth()
  const location = useLocation()

  if (isInitializing) {
    return <AuthSplash />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return <AccessDenied role={user.role} />
  }

  return <Outlet />
}
