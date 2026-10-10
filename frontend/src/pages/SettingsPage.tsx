import { User, Bell } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'

export default function SettingsPage() {
  const { user } = useAuth()

  return (
    <div className="mx-auto w-full max-w-4xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">Settings</h1>
        <p className="mt-2 text-sm text-gray-500">
          Manage your account preferences and application settings.
        </p>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="border-b border-gray-200 bg-gray-50/50 px-6 py-4">
          <h2 className="flex items-center gap-2 text-base font-semibold leading-6 text-gray-900">
            <User className="size-5 text-gray-400" />
            Profile Information
          </h2>
        </div>
        <div className="p-6">
          <dl className="divide-y divide-gray-100 text-sm">
            <div className="py-4 sm:grid sm:grid-cols-3 sm:gap-4">
              <dt className="font-medium text-gray-900">User ID</dt>
              <dd className="mt-1 text-gray-700 sm:col-span-2 sm:mt-0 font-mono">{user?.user_id}</dd>
            </div>
            <div className="py-4 sm:grid sm:grid-cols-3 sm:gap-4">
              <dt className="font-medium text-gray-900">Assigned Role</dt>
              <dd className="mt-1 text-gray-700 sm:col-span-2 sm:mt-0 capitalize">
                <span className="inline-flex items-center rounded-md bg-gray-50 px-2 py-1 text-xs font-medium text-gray-600 ring-1 ring-inset ring-gray-500/10">
                  {user?.role}
                </span>
              </dd>
            </div>
          </dl>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="border-b border-gray-200 bg-gray-50/50 px-6 py-4">
          <h2 className="flex items-center gap-2 text-base font-semibold leading-6 text-gray-900">
            <Bell className="size-5 text-gray-400" />
            Notification Preferences
          </h2>
        </div>
        <div className="p-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-sm font-medium text-gray-900">Critical Alerts</h4>
                <p className="text-sm text-gray-500">Receive immediate notifications for emergency triage.</p>
              </div>
              <button type="button" className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent bg-teal-600 transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-teal-600 focus:ring-offset-2">
                <span className="translate-x-5 pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out" />
              </button>
            </div>
            <div className="flex items-center justify-between pt-4 border-t border-gray-100">
              <div>
                <h4 className="text-sm font-medium text-gray-900">Referral Updates</h4>
                <p className="text-sm text-gray-500">Notify when a referral status changes.</p>
              </div>
              <button type="button" className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent bg-gray-200 transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-teal-600 focus:ring-offset-2">
                <span className="translate-x-0 pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out" />
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div className="flex justify-end">
        <button className="rounded-lg bg-teal-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-teal-500">
          Save Preferences
        </button>
      </div>
    </div>
  )
}
