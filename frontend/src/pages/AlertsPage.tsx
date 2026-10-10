import { BellRing, AlertCircle } from 'lucide-react'

export default function AlertsPage() {
  const alerts = [
    {
      id: 'alt-001',
      type: 'clinical_emergency',
      priority: 'high',
      patient: 'Fatima Bibi (P-2093)',
      message: 'EMERGENCY: Severe pre-eclampsia indicators detected. Blood pressure 170/110. Immediate intervention required.',
      time: '10 mins ago',
      status: 'unresolved'
    },
    {
      id: 'alt-002',
      type: 'system_alert',
      priority: 'medium',
      patient: 'System',
      message: 'Data synchronization delayed for Rural Clinic Alpha.',
      time: '2 hours ago',
      status: 'acknowledged'
    },
    {
      id: 'alt-003',
      type: 'missed_visit',
      priority: 'medium',
      patient: 'Ayesha Khan (P-1042)',
      message: 'High-risk patient missed 3rd Trimester ANC visit. Follow-up SMS sent.',
      time: '5 hours ago',
      status: 'unresolved'
    }
  ]

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">Alert Center</h1>
        <p className="mt-2 text-sm text-gray-500">
          Operational and clinical alerts requiring attention.
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="border-b border-gray-200 bg-gray-50/50 px-6 py-4 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-base font-semibold leading-6 text-gray-900">
            <BellRing className="size-5 text-rose-600" />
            Active Alerts
          </h2>
          <span className="inline-flex items-center rounded-md bg-rose-50 px-2 py-1 text-xs font-medium text-rose-700 ring-1 ring-inset ring-rose-600/20">
            3 Unread
          </span>
        </div>

        <ul className="divide-y divide-gray-100">
          {alerts.map((alert) => (
            <li key={alert.id} className={`p-6 hover:bg-gray-50 transition-colors ${alert.status === 'unresolved' ? 'bg-white' : 'bg-gray-50/30'}`}>
              <div className="flex items-start gap-4">
                <div className={`mt-1 flex size-10 shrink-0 items-center justify-center rounded-full ${
                  alert.priority === 'high' ? 'bg-red-100 text-red-600' : 'bg-orange-100 text-orange-600'
                }`}>
                  <AlertCircle className="size-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-4">
                    <p className={`text-sm font-semibold ${alert.priority === 'high' ? 'text-red-900' : 'text-gray-900'}`}>
                      {alert.patient}
                    </p>
                    <span className="text-xs text-gray-500 whitespace-nowrap">{alert.time}</span>
                  </div>
                  <p className="mt-1 text-sm text-gray-600 leading-relaxed">
                    {alert.message}
                  </p>
                  <div className="mt-3 flex gap-3">
                    {alert.status === 'unresolved' && (
                      <button className="text-xs font-medium text-teal-600 hover:text-teal-700">Acknowledge</button>
                    )}
                    <button className="text-xs font-medium text-gray-500 hover:text-gray-700">View Details</button>
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
