import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, AlertCircle, Calendar, Phone, MapPin, Loader2, Activity, Bot, ArrowRightLeft, Clock } from 'lucide-react'
import { usePatient } from '@/hooks/usePatients'
import { useReferrals } from '@/hooks/useReferrals'
import { cn } from '@/lib/utils'

export default function PatientProfilePage() {
  const { patientId } = useParams<{ patientId: string }>()
  const { data: patient, isLoading, isError } = usePatient(patientId || '')
  
  // We fetch referrals and filter by patientId since there's no patient-specific endpoint
  const { data: allReferrals, isLoading: referralsLoading } = useReferrals({ limit: 500 })
  const patientReferrals = allReferrals?.filter(r => r.patient_id === patientId) || []

  if (isLoading) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center">
        <Loader2 className="size-8 animate-spin text-teal-600 mb-4" />
        <p className="text-sm text-gray-500">Loading patient profile...</p>
      </div>
    )
  }

  if (isError || !patient) {
    return (
      <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="rounded-xl border border-red-100 bg-red-50 p-8 text-center">
          <AlertCircle className="mx-auto size-10 text-red-500 mb-4" />
          <h3 className="text-base font-semibold text-red-900">Patient not found</h3>
          <p className="mt-2 text-sm text-red-700">The requested patient could not be loaded or does not exist.</p>
          <Link to="/patients" className="mt-6 inline-block text-sm font-medium text-teal-600 hover:text-teal-700">
            &larr; Back to Patients
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      {/* Navigation */}
      <div>
        <Link to="/patients" className="inline-flex items-center text-sm font-medium text-teal-600 hover:text-teal-700 mb-4">
          <ArrowLeft className="mr-1 size-4" />
          Back to Patients
        </Link>
      </div>

      {/* Identity Header */}
      <div className="overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-gray-200">
        <div className="p-6 sm:p-8 flex flex-col sm:flex-row sm:items-start sm:justify-between gap-6">
          <div className="flex items-start gap-6">
            <div className="flex size-20 shrink-0 items-center justify-center rounded-2xl bg-teal-100 ring-4 ring-white shadow-sm">
              <span className="text-2xl font-bold text-teal-800">
                {patient.name.substring(0, 2).toUpperCase()}
              </span>
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-gray-900">{patient.name}</h1>
                <span className="inline-flex items-center rounded-md bg-gray-50 px-2 py-1 text-xs font-medium text-gray-600 ring-1 ring-inset ring-gray-500/10">
                  ID: {patient.patient_id}
                </span>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-gray-600">
                <div className="flex items-center gap-1.5">
                  <Calendar className="size-4 text-gray-400" />
                  Age: {patient.age}
                </div>
                {patient.phone && (
                  <div className="flex items-center gap-1.5">
                    <Phone className="size-4 text-gray-400" />
                    {patient.phone}
                  </div>
                )}
                {patient.location && (
                  <div className="flex items-center gap-1.5">
                    <MapPin className="size-4 text-gray-400" />
                    {patient.location}
                  </div>
                )}
                {patient.gestational_age_weeks && (
                  <div className="flex items-center gap-1.5 font-medium text-teal-700">
                    <Activity className="size-4 text-teal-500" />
                    {patient.gestational_age_weeks} Weeks Gestation
                  </div>
                )}
              </div>
            </div>
          </div>
          
          <div className="flex flex-col gap-3 sm:items-end shrink-0">
            <Link
              to={`/patients/${patient.patient_id}/edit`}
              className="inline-flex items-center justify-center gap-2 rounded-lg bg-white px-4 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
            >
              Edit Profile
            </Link>
            <button className="inline-flex items-center justify-center gap-2 rounded-lg bg-teal-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-teal-500">
              <Activity className="size-4" />
              Run Assessment
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Context & Overview */}
        <div className="space-y-8 lg:col-span-1">
          {/* Clinical Context */}
          <div className="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-gray-200">
            <div className="border-b border-gray-100 bg-gray-50/50 px-5 py-4">
              <h3 className="text-sm font-semibold text-gray-900">Clinical Context</h3>
            </div>
            <div className="p-5">
              <dl className="divide-y divide-gray-100 text-sm">
                <div className="py-3 flex justify-between">
                  <dt className="text-gray-500">Gestational Age</dt>
                  <dd className="font-medium text-gray-900">{patient.gestational_age_weeks ? `${patient.gestational_age_weeks} weeks` : 'Unknown'}</dd>
                </div>
                <div className="py-3 flex justify-between">
                  <dt className="text-gray-500">Parity</dt>
                  <dd className="font-medium text-gray-900">{patient.parity !== null ? patient.parity : 'Unknown'}</dd>
                </div>
                <div className="py-3 flex justify-between">
                  <dt className="text-gray-500">Language</dt>
                  <dd className="font-medium text-gray-900 uppercase">{patient.language}</dd>
                </div>
                <div className="py-3 flex justify-between">
                  <dt className="text-gray-500">Registered</dt>
                  <dd className="font-medium text-gray-900">{new Date(patient.created_at).toLocaleDateString()}</dd>
                </div>
              </dl>
            </div>
          </div>
        </div>

        {/* Right Column: Intelligence, Records & Timeline */}
        <div className="space-y-8 lg:col-span-2">
          {/* Risk & Intelligence (Placeholder since no GET API exists) */}
          <div className="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-gray-200">
            <div className="border-b border-gray-100 bg-gray-50/50 px-5 py-4 flex items-center gap-2">
              <Bot className="size-5 text-teal-600" />
              <h3 className="text-sm font-semibold text-gray-900">AI Risk Intelligence</h3>
            </div>
            <div className="p-8 text-center">
              <div className="mx-auto flex size-12 items-center justify-center rounded-full bg-gray-50 mb-3">
                <Activity className="size-6 text-gray-400" />
              </div>
              <h4 className="text-sm font-medium text-gray-900">No recent assessments</h4>
              <p className="mt-1 text-sm text-gray-500">
                Run a new risk assessment to generate AI-assisted clinical insights.
              </p>
              <button className="mt-4 inline-flex items-center gap-2 rounded-lg bg-teal-50 px-3 py-2 text-sm font-semibold text-teal-700 hover:bg-teal-100">
                Start Assessment
              </button>
            </div>
          </div>

          {/* Referrals */}
          <div className="overflow-hidden rounded-xl bg-white shadow-sm ring-1 ring-gray-200">
            <div className="border-b border-gray-100 bg-gray-50/50 px-5 py-4 flex justify-between items-center">
              <div className="flex items-center gap-2">
                <ArrowRightLeft className="size-5 text-gray-500" />
                <h3 className="text-sm font-semibold text-gray-900">Referral History</h3>
              </div>
            </div>
            <div className="p-0">
              {referralsLoading ? (
                <div className="p-8 text-center text-sm text-gray-500 flex justify-center">
                  <Loader2 className="size-5 animate-spin text-teal-600" />
                </div>
              ) : patientReferrals.length > 0 ? (
                <ul className="divide-y divide-gray-100">
                  {patientReferrals.map((ref) => (
                    <li key={ref.id} className="p-5 flex items-start justify-between gap-4 hover:bg-gray-50">
                      <div>
                        <div className="flex items-center gap-2">
                          <h4 className="text-sm font-medium text-gray-900">
                            {ref.facility_name || 'Unassigned Facility'}
                          </h4>
                          <span className={cn(
                            "rounded-md px-1.5 py-0.5 text-xs font-medium ring-1 ring-inset capitalize",
                            ref.status === 'pending' ? 'bg-amber-50 text-amber-700 ring-amber-600/20' :
                            ref.status === 'completed' ? 'bg-green-50 text-green-700 ring-green-600/20' :
                            'bg-gray-50 text-gray-600 ring-gray-500/20'
                          )}>
                            {ref.status}
                          </span>
                        </div>
                        <div className="mt-1 flex items-center gap-2 text-xs text-gray-500">
                          <Clock className="size-3.5" />
                          Created {new Date(ref.created_at || '').toLocaleDateString()}
                        </div>
                      </div>
                      <Link to={`/referrals/${ref.id}`} className="text-sm font-medium text-teal-600 hover:text-teal-700">
                        View
                      </Link>
                    </li>
                  ))}
                </ul>
              ) : (
                <div className="p-8 text-center text-sm text-gray-500">
                  No referrals have been generated for this patient.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
