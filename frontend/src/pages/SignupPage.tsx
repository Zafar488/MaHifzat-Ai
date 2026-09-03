import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { HeartPulse, Loader2, Lock, User, UserPlus } from 'lucide-react'
import { api } from '@/lib/api-client'

const signupSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  full_name: z.string().min(2, 'Full name is required'),
})

type SignupValues = z.infer<typeof signupSchema>

export default function SignupPage() {
  const navigate = useNavigate()
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<SignupValues>({
    resolver: zodResolver(signupSchema),
  })

  const onSubmit = async (data: SignupValues) => {
    setErrorMsg(null)
    try {
      await api.post('/auth/signup', {
        ...data,
        role: 'clinician', // Default role for open signups in this MVP
      })
      navigate('/login', { replace: true })
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || err.message || 'Signup failed')
    }
  }

  return (
    <div className="app-canvas flex min-h-dvh flex-col items-center justify-center px-4 py-12">
      <div className="flex flex-col items-center gap-3 mb-8">
        <span className="flex size-14 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-500 to-teal-700 text-white shadow-lg shadow-teal-600/25">
          <HeartPulse className="size-7" aria-hidden="true" />
        </span>
        <div className="text-center">
          <h1 className="text-xl font-extrabold tracking-tight text-gray-900">
            MaaHifazat <span className="text-teal-600">AI</span>
          </h1>
          <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.3em] text-gray-400">
            Maternal Care Platform
          </p>
        </div>
      </div>

      <div className="w-full max-w-sm rounded-2xl border border-gray-200 bg-white p-8 shadow-sm">
        <div className="mb-6 text-center">
          <p className="font-mono text-[10px] font-medium uppercase tracking-[0.28em] text-teal-600">
            Create Account
          </p>
          <h2 className="mt-1 text-lg font-semibold tracking-tight text-gray-900">Sign Up</h2>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="sr-only" htmlFor="full_name">Full Name</label>
            <div className="relative">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                <UserPlus className="size-4 text-gray-400" aria-hidden="true" />
              </div>
              <input
                id="full_name"
                type="text"
                placeholder="Full Name"
                {...register('full_name')}
                className="block w-full rounded-lg border-0 py-2.5 pl-10 pr-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-teal-600 sm:text-sm sm:leading-6"
              />
            </div>
            {errors.full_name && (
              <p className="mt-1 text-xs text-red-600">{errors.full_name.message}</p>
            )}
          </div>

          <div>
            <label className="sr-only" htmlFor="username">Username</label>
            <div className="relative">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                <User className="size-4 text-gray-400" aria-hidden="true" />
              </div>
              <input
                id="username"
                type="text"
                autoComplete="username"
                placeholder="Username"
                {...register('username')}
                className="block w-full rounded-lg border-0 py-2.5 pl-10 pr-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-teal-600 sm:text-sm sm:leading-6"
              />
            </div>
            {errors.username && (
              <p className="mt-1 text-xs text-red-600">{errors.username.message}</p>
            )}
          </div>

          <div>
            <label className="sr-only" htmlFor="password">Password</label>
            <div className="relative">
              <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                <Lock className="size-4 text-gray-400" aria-hidden="true" />
              </div>
              <input
                id="password"
                type="password"
                autoComplete="new-password"
                placeholder="Password"
                {...register('password')}
                className="block w-full rounded-lg border-0 py-2.5 pl-10 pr-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-teal-600 sm:text-sm sm:leading-6"
              />
            </div>
            {errors.password && (
              <p className="mt-1 text-xs text-red-600">{errors.password.message}</p>
            )}
          </div>

          {errorMsg && (
            <div className="rounded-md bg-red-50 p-3">
              <p className="text-sm text-red-700">{errorMsg}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="mt-2 flex w-full justify-center rounded-lg bg-teal-600 px-3 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-teal-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-600 disabled:opacity-50"
          >
            {isSubmitting ? (
              <Loader2 className="mr-2 size-5 animate-spin" />
            ) : null}
            {isSubmitting ? 'Creating account...' : 'Sign Up'}
          </button>
        </form>
        
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-500">
            Already have an account?{' '}
            <Link to="/login" className="font-semibold text-teal-600 hover:text-teal-500">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
