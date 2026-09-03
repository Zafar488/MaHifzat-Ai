import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Bot, Loader2, Activity, AlertCircle, Play, FileText, Share2, MessageSquare, AlertTriangle, CheckCircle2 } from 'lucide-react'
import { api } from '@/lib/api-client'

interface NodeInfo {
  name: string
  description: string
}

export default function AgentsPage() {
  const [isRunning, setIsRunning] = useState(false)
  const [workflowResult, setWorkflowResult] = useState<any>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const { data: nodes, isLoading, isError } = useQuery({
    queryKey: ['agents', 'status'],
    queryFn: async () => {
      const { data } = await api.get<NodeInfo[]>('/agents/status')
      return data
    },
  })

  const runWorkflow = async () => {
    setIsRunning(true)
    setErrorMsg(null)
    setWorkflowResult(null)
    try {
      // Dummy data representing a High Risk emergency for demonstration
      const requestData = {
        patient_id: "test-patient-001",
        case_id: "case-" + Math.floor(Math.random() * 10000),
        language: "ur",
        channel: "sms",
        vitals: {
          systolic_bp: 170, // High BP -> emergency
          diastolic_bp: 110,
          heart_rate: 105,
          temperature_celsius: 37.2,
          gestational_age_weeks: 34,
          headache_severity: "severe",
          visual_disturbance: true
        },
        symptoms: ["Severe Headache", "Blurred Vision"] // Signs of severe preeclampsia
      }

      const response = await api.post('/agents/run', requestData)
      setWorkflowResult(response.data?.result || response.data)
    } catch (err: any) {
      setErrorMsg(err.response?.data?.detail || err.message || 'Workflow failed to execute')
    } finally {
      setIsRunning(false)
    }
  }

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900">AI Agents Hub</h1>
        <p className="mt-2 text-sm text-gray-500">
          Operational visibility into the MaaHifazat AI agent network and Multi-Agent Orchestration.
        </p>
      </div>

      {/* Workflow Runner Section */}
      <div className="overflow-hidden rounded-xl border border-teal-200 bg-teal-50/30 shadow-sm">
        <div className="border-b border-teal-200 bg-teal-50 px-6 py-4 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-base font-semibold leading-6 text-teal-900">
            <Play className="size-5" />
            Live Agent Workflow Runner
          </h2>
          <button
            onClick={runWorkflow}
            disabled={isRunning}
            className="inline-flex items-center gap-2 rounded-md bg-teal-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-teal-500 disabled:opacity-50"
          >
            {isRunning ? <Loader2 className="size-4 animate-spin" /> : <Bot className="size-4" />}
            {isRunning ? 'Agents Processing...' : 'Run High-Risk Scenario'}
          </button>
        </div>
        
        {errorMsg && (
          <div className="p-6 bg-red-50 border-t border-red-100 text-red-700 text-sm">
            {errorMsg}
          </div>
        )}

        {workflowResult && (
          <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6 bg-white">
            <div className="col-span-1 md:col-span-2">
              <div className={`p-4 rounded-lg flex items-start gap-3 ${workflowResult.emergency ? 'bg-red-50 border border-red-200 text-red-900' : 'bg-green-50 border border-green-200 text-green-900'}`}>
                {workflowResult.emergency ? <AlertTriangle className="size-6 text-red-600" /> : <CheckCircle2 className="size-6 text-green-600" />}
                <div>
                  <h3 className="font-bold text-lg">Agent Consensus: {workflowResult.emergency ? 'EMERGENCY DETECTED' : 'NORMAL'}</h3>
                  <p className="text-sm mt-1">{workflowResult.clinical_summary || 'No clinical summary generated.'}</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <h4 className="flex items-center gap-2 font-semibold text-gray-900 mb-2">
                <Share2 className="size-4 text-teal-600" /> Smart Referral Agent
              </h4>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">
                {workflowResult.referral_info?.recommendation || 'No referral generated'}
              </p>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <h4 className="flex items-center gap-2 font-semibold text-gray-900 mb-2">
                <MessageSquare className="size-4 text-teal-600" /> Communication Agent
              </h4>
              <p className="text-sm text-gray-700">
                <span className="font-semibold block mb-1">Status: {workflowResult.communication_status || 'Pending'}</span>
                {workflowResult.alert_message || 'No alert message sent.'}
              </p>
            </div>

            {workflowResult.report_content && (
              <div className="col-span-1 md:col-span-2 bg-gray-50 p-4 rounded-lg border border-gray-200">
                <h4 className="flex items-center gap-2 font-semibold text-gray-900 mb-2">
                  <FileText className="size-4 text-teal-600" /> Final Structured Report
                </h4>
                <pre className="text-xs text-gray-700 whitespace-pre-wrap overflow-x-auto">
                  {workflowResult.report_content}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="border-b border-gray-200 bg-gray-50/50 px-6 py-4 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-base font-semibold leading-6 text-gray-900">
            <Activity className="size-5 text-gray-500" />
            Agent Nodes Status
          </h2>
        </div>

        <div className="p-0">
          {isLoading ? (
            <div className="flex h-40 items-center justify-center">
              <Loader2 className="size-6 animate-spin text-teal-600" />
            </div>
          ) : isError ? (
            <div className="flex h-40 flex-col items-center justify-center text-center">
              <AlertCircle className="size-8 text-red-500 mb-3" />
              <p className="text-sm font-semibold text-red-900">Failed to load agent status</p>
            </div>
          ) : nodes && nodes.length > 0 ? (
            <ul className="divide-y divide-gray-100">
              {nodes.map((node) => (
                <li key={node.name} className="flex items-center justify-between gap-x-6 p-6 hover:bg-gray-50 transition-colors">
                  <div className="min-w-0 flex items-start gap-4">
                    <div className="mt-1 flex size-10 shrink-0 items-center justify-center rounded-lg bg-gray-100 ring-1 ring-inset ring-gray-200">
                      <Bot className="size-5 text-gray-500" />
                    </div>
                    <div>
                      <h3 className="text-sm font-semibold leading-6 text-gray-900 font-mono">{node.name}</h3>
                      <p className="mt-1 text-sm leading-5 text-gray-500">{node.description}</p>
                    </div>
                  </div>
                  <div className="flex flex-none items-center gap-x-4">
                    <span className="inline-flex items-center rounded-md bg-green-50 px-2 py-1 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-600/20">
                      Operational
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <div className="p-8 text-center text-sm text-gray-500">
              No agent nodes registered in the system.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
