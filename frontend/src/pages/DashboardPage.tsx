import { Link } from 'react-router-dom'
import {
  Activity,
  AlertCircle,
  ArrowRightLeft,
  Bot,
  HeartPulse,
  Users,
} from 'lucide-react'
import { useDashboardStats, useModelHealth } from '@/hooks/useDashboard'
import { useReferrals } from '@/hooks/useReferrals'
import { cn } from '@/lib/utils'

export default function DashboardPage() {
  const { data: stats, isLoading: statsLoading, isError: statsError } = useDashboardStats()
  const { data: modelHealth, isLoading: modelsLoading } = useModelHealth()
  const { data: pendingReferrals, isLoading: referralsLoading } = useReferrals({ status: 'pending', limit: 5 })

  if (statsLoading || modelsLoading || referralsLoading) {
    return (
      <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-6">
        <div className="h-20 w-1/3 bg-gray-100 animate-pulse rounded-lg" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="h-40 bg-gray-100 animate-pulse rounded-xl" />
          <div className="h-40 bg-gray-100 animate-pulse rounded-xl" />
          <div className="h-40 bg-gray-100 animate-pulse rounded-xl" />
        </div>
      </div>
    )
  }

  if (statsError || !stats) {
    return (
      <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="rounded-xl border border-red-100 bg-red-50 p-6 text-center">
          <AlertCircle className="mx-auto size-8 text-red-500 mb-3" />
          <h3 className="text-sm font-semibold text-red-900">Unable to load dashboard data</h3>
          <p className="mt-1 text-sm text-red-700">Please check your connection and try again.</p>
        </div>
      </div>
    )
  }

  const { total_patients, risk_distribution, referral_stats } = stats

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">Clinical Intelligence</h1>
        <p className="mt-2 max-w-xl text-sm leading-6 text-gray-500">
          Command center overview of patient volume, risk status, and operational alerts.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm animate-card-fade-in" style={{ animationDelay: '0ms' }}>
          <div className="p-5">
            <div className="flex items-center gap-4">
              <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-teal-50">
                <Users className="size-5 text-teal-600" aria-hidden="true" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-500">Total Patients</p>
                <p className="text-2xl font-semibold tracking-tight text-gray-900">{total_patients}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="overflow-hidden rounded-xl border border-red-200 bg-red-50 shadow-sm animate-card-fade-in" style={{ animationDelay: '60ms' }}>
          <div className="p-5">
            <div className="flex items-center gap-4">
              <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-red-100">
                <Activity className="size-5 text-red-600" aria-hidden="true" />
              </div>
              <div>
                <p className="text-sm font-medium text-red-900/70">High Risk Patients</p>
                <p className="text-2xl font-semibold tracking-tight text-red-900">
                  {risk_distribution.high}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="overflow-hidden rounded-xl border border-amber-200 bg-amber-50 shadow-sm animate-card-fade-in" style={{ animationDelay: '120ms' }}>
          <div className="p-5">
            <div className="flex items-center gap-4">
              <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-amber-100">
                <ArrowRightLeft className="size-5 text-amber-600" aria-hidden="true" />
              </div>
              <div>
                <p className="text-sm font-medium text-amber-900/70">Pending Referrals</p>
                <p className="text-2xl font-semibold tracking-tight text-amber-900">
                  {referral_stats.by_status?.pending || 0}
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="overflow-hidden rounded-xl border border-blue-200 bg-blue-50 shadow-sm animate-card-fade-in" style={{ animationDelay: '180ms' }}>
          <div className="p-5">
            <div className="flex items-center gap-4">
              <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-blue-100">
                <HeartPulse className="size-5 text-blue-600" aria-hidden="true" />
              </div>
              <div>
                <p className="text-sm font-medium text-blue-900/70">Medium Risk</p>
                <p className="text-2xl font-semibold tracking-tight text-blue-900">
                  {risk_distribution.medium}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
        {/* Pending Actions */}
        <section className="flex flex-col rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
          <div className="border-b border-gray-200 bg-gray-50/50 px-5 py-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold leading-6 text-gray-900">Requires Attention</h2>
              <Link to="/referrals" className="text-sm font-medium text-teal-600 hover:text-teal-700">
                View all
              </Link>
            </div>
          </div>
          <div className="flex-1 p-0">
            {pendingReferrals && pendingReferrals.length > 0 ? (
              <ul className="divide-y divide-gray-100">
                {pendingReferrals.map((referral) => (
                  <li key={referral.id} className="flex items-center justify-between gap-x-6 px-5 py-4 hover:bg-gray-50 transition-colors">
                    <div className="min-w-0">
                      <div className="flex items-start gap-x-3">
                        <p className="text-sm font-semibold leading-6 text-gray-900">
                          {referral.patient_id}
                        </p>
                        <span className={cn(
                          "rounded-md whitespace-nowrap mt-0.5 px-1.5 py-0.5 text-xs font-medium ring-1 ring-inset",
                          referral.urgency_level === 'emergency' ? 'text-red-700 bg-red-50 ring-red-600/10' :
                          referral.urgency_level === 'urgent' ? 'text-amber-700 bg-amber-50 ring-amber-600/10' :
                          'text-gray-600 bg-gray-50 ring-gray-500/10'
                        )}>
                          {referral.urgency_level}
                        </span>
                      </div>
                      <div className="mt-1 flex items-center gap-x-2 text-xs leading-5 text-gray-500">
                        <p className="truncate">To: {referral.facility_name || 'Unassigned Facility'}</p>
                      </div>
                    </div>
                    <div className="flex flex-none items-center gap-x-4">
                      <Link
                        to={`/referrals/${referral.id}`}
                        className="hidden rounded-md bg-white px-2.5 py-1.5 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:block"
                      >
                        Review<span className="sr-only">, {referral.patient_id}</span>
                      </Link>
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="p-8 text-center text-sm text-gray-500">
                No pending referrals at this time.
              </div>
            )}
          </div>
        </section>

        {/* System & AI Intelligence */}
        <section className="flex flex-col rounded-xl border border-gray-200 bg-white shadow-sm overflow-hidden">
          <div className="border-b border-gray-200 bg-gray-50/50 px-5 py-4">
            <h2 className="text-base font-semibold leading-6 text-gray-900">AI Intelligence Status</h2>
          </div>
          <div className="flex-1 p-5">
            {modelHealth ? (
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className={cn(
                    "flex size-10 shrink-0 items-center justify-center rounded-lg",
                    modelHealth.all_loaded ? "bg-teal-50" : "bg-amber-50"
                  )}>
                    <Bot className={cn(
                      "size-5",
                      modelHealth.all_loaded ? "text-teal-600" : "text-amber-600"
                    )} />
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">Model Registry</h3>
                    <p className="text-sm text-gray-500">
                      {modelHealth.loaded_count} of {modelHealth.total_count} models operational
                    </p>
                  </div>
                </div>

                <div className="mt-4 border-t border-gray-100 pt-4">
                  <ul className="space-y-3">
                    {Object.entries(
                      modelHealth.models || {
                        ...(modelHealth.clinical_models || {}),
                        ...(modelHealth.research_workbench_models || {})
                      }
                    ).map(([modelName, isLoaded]) => (
                      <li key={modelName} className="flex items-center justify-between text-sm">
                        <span className="font-mono text-xs text-gray-600">{modelName}</span>
                        <span className={cn(
                          "inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ring-1 ring-inset",
                          isLoaded ? "bg-green-50 text-green-700 ring-green-600/20" : "bg-red-50 text-red-700 ring-red-600/20"
                        )}>
                          {isLoaded ? 'Online' : 'Offline'}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ) : (
              <div className="text-sm text-gray-500">System intelligence models not available.</div>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}
