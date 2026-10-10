import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { ArrowLeft, Loader2, Save, User } from 'lucide-react'
import { useCreatePatient } from '@/hooks/usePatients'
import { cn } from '@/lib/utils'

const patientSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  age: z.number().min(10, 'Age must be at least 10').max(100, 'Age is invalid'),
  gender: z.enum(['male', 'female', 'other']).default('female'),
  phone: z.string().optional(),
  location: z.string().optional(),
  gestational_age_weeks: z.number().min(0).max(42).optional().or(z.literal('')),
  parity: z.number().min(0).optional().or(z.literal('')),
  language: z.string().default('ur'),
  channel: z.string().default('app'),
})


export default function PatientRegistrationPage() {
  const navigate = useNavigate()
  const createPatient = useCreatePatient()
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(patientSchema),
    defaultValues: {
      gender: 'female',
      language: 'ur',
      channel: 'app',
    },
  })

  const onSubmit = async (data: any) => {
    setErrorMsg(null)
    try {
      const cleanNum = (val: any) => {
        if (val === '' || val === null || val === undefined || Number.isNaN(Number(val))) {
          return undefined
        }
        return Number(val)
      }

      const payload = {
        ...data,
        gestational_age_weeks: cleanNum(data.gestational_age_weeks),
        parity: cleanNum(data.parity),
      }
      const newPatient = await createPatient.mutateAsync(payload as any)
      if (newPatient && newPatient.patient_id) {
        navigate(`/patients/${newPatient.patient_id}`)
      } else {
        navigate('/patients')
      }
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || 'Failed to register patient. Please try again.')
    }
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      <div>
        <Link to="/patients" className="inline-flex items-center text-sm font-medium text-teal-600 hover:text-teal-700 mb-4">
          <ArrowLeft className="mr-1 size-4" />
          Back to Patients
        </Link>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">Register New Patient</h1>
        <p className="mt-2 text-sm text-gray-500">
          Enter the patient's identity and initial clinical context.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
        {errorMsg && (
          <div className="rounded-lg bg-red-50 p-4 border border-red-200">
            <h3 className="text-sm font-medium text-red-800">Registration Error</h3>
            <p className="mt-1 text-sm text-red-700">{errorMsg}</p>
          </div>
        )}

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="border-b border-gray-200 bg-gray-50/50 px-6 py-4">
            <h2 className="flex items-center gap-2 text-base font-semibold leading-6 text-gray-900">
              <User className="size-5 text-gray-400" />
              Identity & Demographics
            </h2>
          </div>
          
          <div className="p-6 grid grid-cols-1 gap-x-6 gap-y-6 sm:grid-cols-6">
            <div className="sm:col-span-4">
              <label htmlFor="name" className="block text-sm font-medium leading-6 text-gray-900">
                Full Name <span className="text-red-500">*</span>
              </label>
              <div className="mt-2">
                <input
                  type="text"
                  id="name"
                  {...register('name')}
                  className={cn(
                    "block w-full rounded-lg border-0 py-2 text-gray-900 shadow-sm ring-1 ring-inset focus:ring-2 focus:ring-inset sm:text-sm sm:leading-6",
                    errors.name ? "ring-red-300 focus:ring-red-600" : "ring-gray-300 focus:ring-teal-600"
                  )}
                />
                {errors.name && <p className="mt-1 text-xs text-red-600">{errors.name.message}</p>}
              </div>
            </div>

            <div className="sm:col-span-2">
              <label htmlFor="age" className="block text-sm font-medium leading-6 text-gray-900">
                Age <span className="text-red-500">*</span>
              </label>
              <div className="mt-2">
                <input
                  type="number"
                  id="age"
                  {...register('age', { valueAsNumber: true })}
                  className={cn(
                    "block w-full rounded-lg border-0 py-2 text-gray-900 shadow-sm ring-1 ring-inset focus:ring-2 focus:ring-inset sm:text-sm sm:leading-6",
                    errors.age ? "ring-red-300 focus:ring-red-600" : "ring-gray-300 focus:ring-teal-600"
                  )}
                />
                {errors.age && <p className="mt-1 text-xs text-red-600">{errors.age.message}</p>}
              </div>
            </div>

            <div className="sm:col-span-3">
              <label htmlFor="phone" className="block text-sm font-medium leading-6 text-gray-900">
                Phone Number
              </label>
              <div className="mt-2">
                <input
                  type="tel"
                  id="phone"
                  {...register('phone')}
                  className="block w-full rounded-lg border-0 py-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-teal-600 sm:text-sm sm:leading-6"
                />
              </div>
            </div>

            <div className="sm:col-span-3">
              <label htmlFor="location" className="block text-sm font-medium leading-6 text-gray-900">
                Location
              </label>
              <div className="mt-2">
                <input
                  type="text"
                  id="location"
                  {...register('location')}
                  className="block w-full rounded-lg border-0 py-2 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-teal-600 sm:text-sm sm:leading-6"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="border-b border-gray-200 bg-gray-50/50 px-6 py-4">
            <h2 className="text-base font-semibold leading-6 text-gray-900">Maternal Context</h2>
          </div>
          
          <div className="p-6 grid grid-cols-1 gap-x-6 gap-y-6 sm:grid-cols-6">
            <div className="sm:col-span-3">
              <label htmlFor="gestational_age_weeks" className="block text-sm font-medium leading-6 text-gray-900">
                Gestational Age (weeks)
              </label>
              <div className="mt-2">
                <input
                  type="number"
                  id="gestational_age_weeks"
                  {...register('gestational_age_weeks', { valueAsNumber: true })}
                  className={cn(
                    "block w-full rounded-lg border-0 py-2 text-gray-900 shadow-sm ring-1 ring-inset focus:ring-2 focus:ring-inset sm:text-sm sm:leading-6",
                    errors.gestational_age_weeks ? "ring-red-300 focus:ring-red-600" : "ring-gray-300 focus:ring-teal-600"
                  )}
                />
                {errors.gestational_age_weeks && <p className="mt-1 text-xs text-red-600">{errors.gestational_age_weeks.message}</p>}
              </div>
            </div>

            <div className="sm:col-span-3">
              <label htmlFor="parity" className="block text-sm font-medium leading-6 text-gray-900">
                Parity
              </label>
              <div className="mt-2">
                <input
                  type="number"
                  id="parity"
                  {...register('parity', { valueAsNumber: true })}
                  className={cn(
                    "block w-full rounded-lg border-0 py-2 text-gray-900 shadow-sm ring-1 ring-inset focus:ring-2 focus:ring-inset sm:text-sm sm:leading-6",
                    errors.parity ? "ring-red-300 focus:ring-red-600" : "ring-gray-300 focus:ring-teal-600"
                  )}
                />
                {errors.parity && <p className="mt-1 text-xs text-red-600">{errors.parity.message}</p>}
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end gap-x-4 pt-4">
          <Link
            to="/patients"
            className="text-sm font-semibold leading-6 text-gray-900 hover:text-gray-700"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={isSubmitting}
            className="inline-flex items-center gap-2 rounded-lg bg-teal-600 px-6 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-teal-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
            Register Patient
          </button>
        </div>
      </form>
    </div>
  )
}
