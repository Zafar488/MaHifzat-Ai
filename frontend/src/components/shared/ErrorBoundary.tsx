import { useRouteError, Link } from 'react-router-dom'
import { AlertCircle, RefreshCw, LayoutDashboard } from 'lucide-react'
import { getErrorMessage } from '@/lib/utils'

export function RouteErrorBoundary() {
  const error = useRouteError()
  const errorString = getErrorMessage(error, 'An unexpected application error occurred.')

  return (
    <div className="app-canvas flex min-h-dvh flex-col items-center justify-center p-6 text-center">
      <div className="mx-auto w-full max-w-md bg-white rounded-2xl shadow-xl border border-gray-200 p-8 space-y-6 animate-modal-pop-in">
        <div className="flex justify-center">
          <span className="flex size-14 items-center justify-center rounded-2xl bg-red-50 text-red-600 border border-red-200 shadow-sm">
            <AlertCircle className="size-7" />
          </span>
        </div>

        <div className="space-y-2">
          <h2 className="text-xl font-bold tracking-tight text-gray-900">Application Recovered</h2>
          <p className="text-xs text-gray-500 max-w-sm mx-auto">
            MaaHifazat AI intercepted an unhandled runtime error and preserved your session state.
          </p>
        </div>

        <div className="rounded-lg bg-gray-50 p-4 border border-gray-200 text-left text-xs font-mono text-gray-800 break-words max-h-40 overflow-y-auto">
          {errorString}
        </div>

        <div className="flex flex-col sm:flex-row gap-3 justify-center pt-2">
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="flex items-center justify-center gap-2 rounded-lg bg-teal-600 px-4 py-2.5 text-xs font-semibold text-white shadow-sm hover:bg-teal-500 transition-colors"
          >
            <RefreshCw className="size-4" />
            <span>Reload Page</span>
          </button>
          <Link
            to="/dashboard"
            className="flex items-center justify-center gap-2 rounded-lg bg-gray-100 px-4 py-2.5 text-xs font-semibold text-gray-700 hover:bg-gray-200 transition-colors"
          >
            <LayoutDashboard className="size-4 text-gray-500" />
            <span>Go to Dashboard</span>
          </Link>
        </div>
      </div>
    </div>
  )
}
