import { useDashboardStats } from '@/hooks/useDashboard'
import { Loader2, AlertCircle, BarChart3, PieChart } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'


export default function AnalyticsPage() {
  const { data, isLoading, isError } = useDashboardStats()

  if (isLoading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="size-8 animate-spin text-teal-600" />
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="mx-auto w-full max-w-7xl px-4 py-8">
        <div className="rounded-xl border border-red-100 bg-red-50 p-8 text-center">
          <AlertCircle className="mx-auto size-10 text-red-500 mb-4" />
          <h3 className="text-base font-semibold text-red-900">Failed to load analytics</h3>
        </div>
      </div>
    )
  }

  const riskData = [
    { name: 'Low Risk', value: data.risk_distribution.low, color: '#10b981' },
    { name: 'Medium Risk', value: data.risk_distribution.medium, color: '#3b82f6' },
    { name: 'High Risk', value: data.risk_distribution.high, color: '#ef4444' },
    { name: 'Unknown', value: data.risk_distribution.unknown, color: '#9ca3af' },
  ]

  const referralStatusData = Object.entries(data.referral_stats.by_status).map(([key, value]) => ({
    name: key.charAt(0).toUpperCase() + key.slice(1),
    value
  }))

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">Analytics Workspace</h1>
        <p className="mt-2 text-sm text-gray-500">
          Aggregate clinical metrics and operational trends.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Risk Distribution Chart */}
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm flex flex-col">
          <div className="border-b border-gray-100 bg-gray-50/50 px-6 py-4 flex items-center gap-2">
            <PieChart className="size-5 text-gray-500" />
            <h2 className="text-sm font-semibold text-gray-900">Patient Risk Distribution</h2>
          </div>
          <div className="p-6 flex-1 min-h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6b7280' }} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6b7280' }} />
                <Tooltip 
                  cursor={{ fill: '#f9fafb' }}
                  contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb', boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' }}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {riskData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Referrals Chart */}
        <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm flex flex-col">
          <div className="border-b border-gray-100 bg-gray-50/50 px-6 py-4 flex items-center gap-2">
            <BarChart3 className="size-5 text-gray-500" />
            <h2 className="text-sm font-semibold text-gray-900">Referral Volumes</h2>
          </div>
          <div className="p-6 flex-1 min-h-[300px]">
            {referralStatusData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={referralStatusData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f3f4f6" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6b7280' }} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#6b7280' }} />
                  <Tooltip 
                    cursor={{ fill: '#f9fafb' }}
                    contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb', boxShadow: '0 1px 2px 0 rgb(0 0 0 / 0.05)' }}
                  />
                  <Bar dataKey="value" fill="#0d9488" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-sm text-gray-500">
                No referral data available.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
