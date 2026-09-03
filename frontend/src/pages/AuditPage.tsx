import { useQuery } from '@tanstack/react-query'
import { FileText, Loader2, AlertCircle, Clock, Shield, Activity } from 'lucide-react'
import { api } from '@/lib/api-client'
import { cn } from '@/lib/utils'

interface AuditLog {
  id: string | number
  agent_name: string
  action: string
  case_id?: string
  timestamp: string
  patient_id?: string
  details?: any
  severity?: string
}

interface AuditResponse {
  total: number
  skip: number
  limit: number
  logs: AuditLog[]
}

export default function AuditPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['audit', 'logs'],
    queryFn: async () => {
      const { data } = await api.get<AuditResponse>('/audit/logs')
      return data
    },
  })

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">System Audit Log</h1>
        <p className="mt-2 text-sm text-gray-500">
          Complete system traceability, AI agent activity, and clinical action audit trail.
        </p>
      </div>

      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm flex flex-col min-h-[500px]">
        <div className="border-b border-gray-100 bg-gray-50/50 px-6 py-4 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-sm font-semibold text-gray-900">
            <Shield className="size-5 text-teal-600" />
            Audit Records ({data?.logs.length || 0})
          </h2>
          <span className="inline-flex items-center rounded-md bg-teal-50 px-2 py-1 text-xs font-semibold text-teal-700 ring-1 ring-inset ring-teal-600/20">
            Live Accountability Log
          </span>
        </div>
        
        <div className="flex-1 p-0">
          {isLoading ? (
            <div className="flex h-64 flex-col items-center justify-center">
              <Loader2 className="size-8 animate-spin text-teal-600" />
              <p className="mt-4 text-sm text-gray-500">Loading audit records...</p>
            </div>
          ) : isError ? (
            <div className="flex h-64 flex-col items-center justify-center text-center">
              <AlertCircle className="size-8 text-red-500 mb-3" />
              <h3 className="text-sm font-semibold text-red-900">Failed to load audit records</h3>
              <p className="mt-1 text-sm text-red-700">Please check your connection and try again.</p>
            </div>
          ) : data && data.logs.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-xs font-semibold text-gray-900 sm:pl-6">Timestamp</th>
                    <th scope="col" className="px-3 py-3.5 text-left text-xs font-semibold text-gray-900">Agent / Actor</th>
                    <th scope="col" className="px-3 py-3.5 text-left text-xs font-semibold text-gray-900">Action</th>
                    <th scope="col" className="px-3 py-3.5 text-left text-xs font-semibold text-gray-900">Context / Details</th>
                    <th scope="col" className="px-3 py-3.5 text-left text-xs font-semibold text-gray-900">Severity</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {data.logs.map((log) => (
                    <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                      <td className="whitespace-nowrap py-4 pl-4 pr-3 sm:pl-6 text-xs text-gray-500">
                        <div className="flex items-center gap-1.5 font-mono">
                          <Clock className="size-3.5 text-gray-400" />
                          {new Date(log.timestamp).toLocaleString()}
                        </div>
                      </td>
                      <td className="whitespace-nowrap px-3 py-4 text-xs font-bold font-mono uppercase text-gray-900">
                        <span className="inline-flex items-center gap-1 bg-gray-100 px-2 py-1 rounded">
                          <Activity className="size-3 text-teal-600" />
                          {log.agent_name}
                        </span>
                      </td>
                      <td className="whitespace-nowrap px-3 py-4 text-xs font-semibold text-gray-800">
                        {log.action}
                      </td>
                      <td className="px-3 py-4 text-xs text-gray-600 max-w-md">
                        <p>{log.details || log.action}</p>
                        {log.case_id && (
                          <span className="mt-1 inline-block font-mono text-[10px] bg-teal-50 text-teal-700 px-1.5 py-0.5 rounded border border-teal-200">
                            ID: {log.case_id}
                          </span>
                        )}
                      </td>
                      <td className="whitespace-nowrap px-3 py-4 text-xs">
                        <span className={cn(
                          "rounded-md px-2 py-0.5 text-[10px] font-bold uppercase ring-1 ring-inset",
                          log.severity === 'critical' ? 'bg-red-50 text-red-700 ring-red-600/20' :
                          log.severity === 'warning' ? 'bg-amber-50 text-amber-700 ring-amber-600/20' :
                          'bg-teal-50 text-teal-700 ring-teal-600/20'
                        )}>
                          {log.severity || 'info'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="flex h-64 flex-col items-center justify-center text-center px-4">
              <FileText className="size-10 text-gray-300 mb-3" />
              <h3 className="text-sm font-semibold text-gray-900">No audit records found</h3>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
