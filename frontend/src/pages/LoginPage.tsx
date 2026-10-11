import { useState } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { HeartPulse, Loader2, Lock, User, ShieldCheck } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'
import { MaternalHealthIllustration } from '@/components/illustrations/MaternalHealthIllustration'
import { getErrorMessage } from '@/lib/utils'

const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
})

type LoginValues = z.infer<typeof loginSchema>

export default function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { login } = useAuth()
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
  })

  // Where to redirect after successful login
  const from = location.state?.from?.pathname || '/'

  const onSubmit = async (data: LoginValues) => {
    setErrorMsg(null)
    try {
      await login(data.username, data.password)
      navigate(from, { replace: true })
    } catch (err: any) {
      setErrorMsg(getErrorMessage(err, 'Login failed'))
    }
  }

  return (
    <div className="app-canvas flex min-h-dvh flex-col items-center justify-center px-4 py-8 md:py-12">
      <div className="w-full max-w-5xl flex flex-col lg:flex-row items-center justify-between gap-8 lg:gap-12">
        {/* Left Hero Section: Custom Vector Illustration & Emotional Hook */}
        <div className="flex-1 flex flex-col items-center lg:items-start text-center lg:text-left space-y-4 max-w-lg animate-card-fade-in">
          <div className="flex items-center gap-3">
            <span className="flex size-12 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-500 to-teal-700 text-white shadow-lg shadow-teal-600/25">
              <HeartPulse className="size-6" aria-hidden="true" />
            </span>
            <div>
              <h1 className="text-2xl font-extrabold tracking-tight text-gray-900">
                MaaHifazat <span className="text-teal-600">AI</span>
              </h1>
              <p className="font-mono text-[10px] uppercase tracking-[0.3em] text-teal-700 font-semibold">
                Maternal Care Platform
              </p>
            </div>
          </div>

          <p className="text-base text-gray-600 leading-relaxed font-normal">
            A digital safety net empowering Lady Health Workers and clinicians with instant WHO red-flag triage, bilingual care guidance, and transparent decision support.
          </p>

          <div className="w-full max-w-md my-2 py-2">
            <MaternalHealthIllustration />
          </div>

          <div className="hidden sm:flex items-center gap-6 text-xs text-gray-500 pt-2 border-t border-gray-200/60 w-full justify-center lg:justify-start">
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="size-4 text-teal-600" />
              WHO Guidelines Triage
            </span>
            <span className="flex items-center gap-1.5">
              <HeartPulse className="size-4 text-teal-600" />
              Bilingual Care Reports
            </span>
          </div>
        </div>

        {/* Right Form Card Section */}
        <div className="w-full max-w-sm shrink-0 rounded-2xl border border-gray-200 bg-white p-8 shadow-sm animate-card-fade-in" style={{ animationDelay: '100ms' }}>
          <div className="mb-6 text-center">
            <p className="font-mono text-[10px] font-medium uppercase tracking-[0.28em] text-teal-600">
              Secure Access
            </p>
            <h2 className="mt-1 text-lg font-semibold tracking-tight text-gray-900">Sign In</h2>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
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
                  placeholder="Username (e.g. admin or clinician)"
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
                  autoComplete="current-password"
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
              className="mt-2 flex w-full justify-center rounded-lg bg-teal-600 px-3 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-teal-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-600 disabled:opacity-50 transition-colors"
            >
              {isSubmitting ? (
                <Loader2 className="mr-2 size-5 animate-spin" />
              ) : null}
              {isSubmitting ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 border-t border-gray-100 pt-6">
            <p className="text-center text-xs text-gray-500 mb-2">Test Accounts:</p>
            <div className="flex flex-wrap justify-center gap-2">
              <span className="inline-flex items-center rounded-md bg-gray-50 px-2 py-1 text-[10px] font-medium text-gray-600 ring-1 ring-inset ring-gray-500/10">admin / admin</span>
              <span className="inline-flex items-center rounded-md bg-gray-50 px-2 py-1 text-[10px] font-medium text-gray-600 ring-1 ring-inset ring-gray-500/10">clinician / clinician</span>
              <span className="inline-flex items-center rounded-md bg-gray-50 px-2 py-1 text-[10px] font-medium text-gray-600 ring-1 ring-inset ring-gray-500/10">lhw / lhw</span>
            </div>
          </div>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-500">
              Don't have an account?{' '}
              <Link to="/signup" className="font-semibold text-teal-600 hover:text-teal-500">
                Sign up
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
