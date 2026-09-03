import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Search, UserPlus, Users, Loader2, AlertCircle, ChevronRight, Phone, MapPin } from 'lucide-react'
import { usePatients } from '@/hooks/usePatients'

export default function PatientListPage() {
  const [search, setSearch] = useState('')
  const { data: patients, isLoading, isError } = usePatients(0, 100)

  const filteredPatients = patients?.filter(p => 
    p.name.toLowerCase().includes(search.toLowerCase()) || 
    p.patient_id.toLowerCase().includes(search.toLowerCase()) ||
    (p.phone && p.phone.includes(search))
  )

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      {/* Header */}
      <div className="sm:flex sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900">Patients</h1>
          <p className="mt-2 text-sm text-gray-500">
            A roster of all registered maternal care patients.
          </p>
        </div>
        <div className="mt-4 sm:ml-16 sm:mt-0 sm:flex-none">
          <Link
            to="/patients/new"
            className="inline-flex items-center gap-2 block rounded-lg bg-teal-600 px-3 py-2 text-center text-sm font-semibold text-white shadow-sm hover:bg-teal-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-600"
          >
            <UserPlus className="size-4" />
            Add Patient
          </Link>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative w-full max-w-md">
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
            <Search className="size-4 text-gray-400" aria-hidden="true" />
          </div>
          <input
            type="text"
            name="search"
            id="search"
            className="block w-full rounded-lg border-0 py-2 pl-9 pr-3 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-teal-600 sm:text-sm sm:leading-6"
            placeholder="Search by name, ID, or phone..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Content */}
      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        {isLoading ? (
          <div className="flex h-64 flex-col items-center justify-center">
            <Loader2 className="size-8 animate-spin text-teal-600" />
            <p className="mt-4 text-sm text-gray-500">Loading patients...</p>
          </div>
        ) : isError ? (
          <div className="flex h-64 flex-col items-center justify-center text-center">
            <AlertCircle className="size-8 text-red-500 mb-3" />
            <h3 className="text-sm font-semibold text-red-900">Failed to load patients</h3>
            <p className="mt-1 text-sm text-red-700">Please try again later.</p>
          </div>
        ) : filteredPatients && filteredPatients.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-xs font-semibold text-gray-900 sm:pl-6">
                    Patient
                  </th>
                  <th scope="col" className="px-3 py-3.5 text-left text-xs font-semibold text-gray-900">
                    Contact
                  </th>
                  <th scope="col" className="px-3 py-3.5 text-left text-xs font-semibold text-gray-900">
                    Gestational Age
                  </th>
                  <th scope="col" className="relative py-3.5 pl-3 pr-4 sm:pr-6">
                    <span className="sr-only">View</span>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {filteredPatients.map((patient) => (
                  <tr key={patient.patient_id} className="hover:bg-gray-50 transition-colors">
                    <td className="whitespace-nowrap py-4 pl-4 pr-3 sm:pl-6">
                      <div className="flex items-center">
                        <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-teal-100">
                          <span className="text-sm font-medium text-teal-800">
                            {patient.name.substring(0, 2).toUpperCase()}
                          </span>
                        </div>
                        <div className="ml-4">
                          <div className="font-medium text-gray-900">{patient.name}</div>
                          <div className="text-gray-500 text-xs">ID: {patient.patient_id} • Age: {patient.age}</div>
                        </div>
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      <div className="flex flex-col gap-1">
                        {patient.phone ? (
                          <div className="flex items-center gap-1.5 text-gray-700">
                            <Phone className="size-3.5" />
                            {patient.phone}
                          </div>
                        ) : (
                          <span className="text-gray-400 italic">No phone</span>
                        )}
                        {patient.location && (
                          <div className="flex items-center gap-1.5 text-gray-500">
                            <MapPin className="size-3.5" />
                            {patient.location}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      {patient.gestational_age_weeks ? (
                        <span className="inline-flex items-center rounded-md bg-gray-50 px-2 py-1 text-xs font-medium text-gray-600 ring-1 ring-inset ring-gray-500/10">
                          {patient.gestational_age_weeks} weeks
                        </span>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                      <Link
                        to={`/patients/${patient.patient_id}`}
                        className="inline-flex items-center gap-1 text-teal-600 hover:text-teal-900"
                      >
                        View<span className="sr-only">, {patient.name}</span>
                        <ChevronRight className="size-4" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="flex h-64 flex-col items-center justify-center text-center px-4">
            <Users className="size-10 text-gray-300 mb-3" />
            <h3 className="text-sm font-semibold text-gray-900">No patients found</h3>
            <p className="mt-1 text-sm text-gray-500">
              {search ? 'Try adjusting your search terms.' : 'Get started by registering a new patient.'}
            </p>
            {!search && (
              <div className="mt-6">
                <Link
                  to="/patients/new"
                  className="inline-flex items-center gap-2 rounded-lg bg-teal-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-teal-500"
                >
                  <UserPlus className="size-4" />
                  Add Patient
                </Link>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
