import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRightLeft, Loader2, AlertCircle, Clock } from 'lucide-react'
import { useReferrals } from '@/hooks/useReferrals'
import { cn } from '@/lib/utils'

export default function ReferralsPage() {
  const [filter, setFilter] = useState<string>('all')
  const { data: referrals, isLoading, isError } = useReferrals(filter !== 'all' ? { status: filter } : undefined)

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">Referrals</h1>
        <p className="mt-2 text-sm text-gray-500">
          Track and manage patient facility transfers and care escalations.
        </p>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex overflow-hidden rounded-lg border border-gray-300 bg-white shadow-sm">
          {['all', 'pending', 'accepted', 'in_transit', 'completed'].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={cn(
                "px-4 py-2 text-sm font-medium border-r border-gray-200 last:border-0 capitalize transition-colors",
                filter === status 
                  ? "bg-teal-50 text-teal-700 hover:bg-teal-100" 
                  : "bg-white text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              )}
            >
              {status.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        {isLoading ? (
          <div className="flex h-64 flex-col items-center justify-center">
            <Loader2 className="size-8 animate-spin text-teal-600" />
            <p className="mt-4 text-sm text-gray-500">Loading referrals...</p>
          </div>
        ) : isError ? (
          <div className="flex h-64 flex-col items-center justify-center text-center">
            <AlertCircle className="size-8 text-red-500 mb-3" />
            <h3 className="text-sm font-semibold text-red-900">Failed to load referrals</h3>
            <p className="mt-1 text-sm text-red-700">Please try again later.</p>
          </div>
        ) : referrals && referrals.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-xs font-semibold text-gray-900 sm:pl-6">
                    Patient ID
                  </th>
                  <th scope="col" className="px-3 py-3.5 text-left text-xs font-semibold text-gray-900">
                    Facility
                  </th>
                  <th scope="col" className="px-3 py-3.5 text-left text-xs font-semibold text-gray-900">
                    Urgency
                  </th>
                  <th scope="col" className="px-3 py-3.5 text-left text-xs font-semibold text-gray-900">
                    Status
                  </th>
                  <th scope="col" className="px-3 py-3.5 text-left text-xs font-semibold text-gray-900">
                    Created
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {referrals.map((referral) => (
                  <tr key={referral.id} className="hover:bg-gray-50 transition-colors">
                    <td className="whitespace-nowrap py-4 pl-4 pr-3 sm:pl-6">
                      <Link to={`/patients/${referral.patient_id}`} className="font-medium text-teal-600 hover:text-teal-900">
                        {referral.patient_id}
                      </Link>
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-900">
                      {referral.facility_name || <span className="text-gray-400 italic">Unassigned</span>}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm">
                      <span className={cn(
                        "rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset capitalize",
                        referral.urgency_level === 'emergency' ? 'text-red-700 bg-red-50 ring-red-600/10' :
                        referral.urgency_level === 'urgent' ? 'text-amber-700 bg-amber-50 ring-amber-600/10' :
                        'text-gray-600 bg-gray-50 ring-gray-500/10'
                      )}>
                        {referral.urgency_level}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm">
                      <span className={cn(
                        "rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset capitalize",
                        referral.status === 'pending' ? 'bg-amber-50 text-amber-700 ring-amber-600/20' :
                        referral.status === 'completed' ? 'bg-green-50 text-green-700 ring-green-600/20' :
                        'bg-blue-50 text-blue-700 ring-blue-600/20'
                      )}>
                        {referral.status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      <div className="flex items-center gap-1.5">
                        <Clock className="size-3.5 text-gray-400" />
                        {new Date(referral.created_at || '').toLocaleDateString()}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex h-64 flex-col items-center justify-center text-center px-4">
            <ArrowRightLeft className="size-10 text-gray-300 mb-3" />
            <h3 className="text-sm font-semibold text-gray-900">No referrals found</h3>
            <p className="mt-1 text-sm text-gray-500">
              There are no {filter !== 'all' ? filter : ''} referrals in the system.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
