import { lazy, Suspense } from 'react'
import { createBrowserRouter, Navigate, Outlet } from 'react-router-dom'
import { HeartPulse, Loader2 } from 'lucide-react'
import { AppShell, ProtectedRoute } from '@/components/layout'
import { UserRole } from '@/types'

// --- Lazy pages (each becomes its own chunk under code splitting) ------------

const LoginPage = lazy(() => import('@/pages/LoginPage'))
const DashboardPage = lazy(() => import('@/pages/DashboardPage'))
const PatientListPage = lazy(() => import('@/pages/patients/PatientListPage'))
const PatientRegistrationPage = lazy(() => import('@/pages/patients/PatientRegistrationPage'))
const PatientProfilePage = lazy(() => import('@/pages/patients/PatientProfilePage'))
const RiskIntelligencePage = lazy(() => import('@/pages/RiskIntelligencePage'))
const ReferralsPage = lazy(() => import('@/pages/ReferralsPage'))
const AgentsPage = lazy(() => import('@/pages/AgentsPage'))
const AlertsPage = lazy(() => import('@/pages/AlertsPage'))
const AuditPage = lazy(() => import('@/pages/AuditPage'))
const AnalyticsPage = lazy(() => import('@/pages/AnalyticsPage'))
const SettingsPage = lazy(() => import('@/pages/SettingsPage'))
const SignupPage = lazy(() => import('@/pages/SignupPage'))
const PregnancyHelperPage = lazy(() => import('@/pages/PregnancyHelperPage'))
const ModelWorkbenchPage = lazy(() => import('@/pages/ModelWorkbenchPage'))
const FollowupsPage = lazy(() => import('@/pages/FollowupsPage'))

// --- Suspense fallbacks -------------------------------------------------------

/** Full-screen splash for routes suspending outside the app shell (e.g. /login). */
function RouteFallback() {
  return (
    <div className="app-canvas flex h-dvh flex-col items-center justify-center gap-4">
      <span className="flex size-12 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-500 to-teal-700 text-white shadow-lg shadow-teal-600/25">
        <HeartPulse className="size-6" aria-hidden="true" />
      </span>
      <Loader2 className="size-5 animate-spin text-teal-600" aria-hidden="true" />
    </div>
  )
}

// --- Router -------------------------------------------------------------------

export const router = createBrowserRouter([
  {
    // Global Suspense boundary so lazy elements can suspend anywhere in the
    // tree. Pages inside AppShell additionally get an in-shell fallback.
    element: (
      <Suspense fallback={<RouteFallback />}>
        <Outlet />
      </Suspense>
    ),
    children: [
      // Public
      { path: '/login', element: <LoginPage /> },
      { path: '/signup', element: <SignupPage /> },

      // Root → dashboard
      { path: '/', element: <Navigate to="/dashboard" replace /> },

      // Authenticated area (any signed-in role)
      {
        element: <ProtectedRoute />,
        children: [
          {
            element: <AppShell />,
            children: [
              { path: '/dashboard', element: <DashboardPage /> },
              { path: '/patients', element: <PatientListPage /> },
              { path: '/patients/new', element: <PatientRegistrationPage /> },
              { path: '/patients/:id', element: <PatientProfilePage /> },
              { path: '/patients/:patientId', element: <PatientProfilePage /> },
              { path: '/risk-assessment', element: <RiskIntelligencePage /> },
              { path: '/pregnancy-helper', element: <PregnancyHelperPage /> },
              { path: '/models', element: <ModelWorkbenchPage /> },
              { path: '/followups', element: <FollowupsPage /> },
              { path: '/referrals', element: <ReferralsPage /> },
              {
                // AI Agents — clinicians and admins only. Nested inside the
                // shell so a denied role still sees the layout.
                element: <ProtectedRoute allowedRoles={[UserRole.CLINICIAN, UserRole.ADMIN]} />,
                children: [{ path: '/agents', element: <AgentsPage /> }],
              },
              { path: '/alerts', element: <AlertsPage /> },
              {
                // Audit Log — admins only.
                element: <ProtectedRoute allowedRoles={[UserRole.ADMIN]} />,
                children: [{ path: '/audit', element: <AuditPage /> }],
              },
              { path: '/analytics', element: <AnalyticsPage /> },
              { path: '/settings', element: <SettingsPage /> },
            ],
          },
        ],
      },

      // Catch-all → dashboard
      { path: '*', element: <Navigate to="/dashboard" replace /> },
    ],
  },
])
