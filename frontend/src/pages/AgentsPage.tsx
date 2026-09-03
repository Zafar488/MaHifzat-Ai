import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Bot, Loader2, Activity, AlertCircle, Play, FileText, Share2, MessageSquare, AlertTriangle, CheckCircle2 } from 'lucide-react'
import { api } from '@/lib/api-client'
import { usePatients } from '@/hooks/usePatients'

interface NodeInfo {
  name: string
  description: string
}

export default function AgentsPage() {
  const [isRunning, setIsRunning] = useState(false)
  const [workflowResult, setWorkflowResult] = useState<any>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)
  const [selectedScenario, setSelectedScenario] = useState<'emergency' | 'routine'>('emergency')
  const [selectedPatientId, setSelectedPatientId] = useState<string>('')

  const { data: patientsList } = usePatients(0, 100)

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
      const isEmergencyScenario = selectedScenario === 'emergency'
      const p = patientsList?.find(item => item.patient_id === selectedPatientId)

      const requestData = {
        patient_id: selectedPatientId || "pat_agent_" + Math.floor(Math.random() * 10000),
        case_id: "case-" + Math.floor(Math.random() * 10000),
        language: p?.language || "ur",
        channel: "sms",
        vitals: isEmergencyScenario ? {
          systolic_bp: 175,
          diastolic_bp: 110,
          heart_rate: 112,
          temperature_celsius: 37.8,
          gestational_age_weeks: p?.gestational_age_weeks || 34,
          headache_severity: "severe",
          visual_disturbance: true
        } : {
          systolic_bp: 118,
          diastolic_bp: 76,
          heart_rate: 72,
          temperature_celsius: 36.6,
          gestational_age_weeks: p?.gestational_age_weeks || 28,
          headache_severity: "none",
          visual_disturbance: false
        },
        symptoms: isEmergencyScenario ? ["Severe Headache", "Blurred Vision", "Epigastric Pain"] : ["Mild Fatigue"]
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
          Operational visibility into the 9-Agent LangGraph Orchestration pipeline.
        </p>
      </div>

      {/* Workflow Runner Controls */}
      <div className="overflow-hidden rounded-xl border border-teal-200 bg-teal-50/30 shadow-sm">
        <div className="border-b border-teal-200 bg-teal-50 px-6 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <h2 className="flex items-center gap-2 text-base font-semibold leading-6 text-teal-900">
            <Play className="size-5" />
            Live 9-Agent Orchestration Runner
          </h2>

          <div className="flex flex-wrap items-center gap-3">
            <select
              value={selectedPatientId}
              onChange={(e) => setSelectedPatientId(e.target.value)}
              className="rounded-lg border border-teal-300 bg-white px-3 py-1.5 text-xs text-gray-900 focus:outline-none focus:ring-1 focus:ring-teal-500"
            >
              <option value="">-- Select Patient (Optional) --</option>
              {patientsList?.map(p => (
                <option key={p.patient_id} value={p.patient_id}>
                  {p.name} (Age: {p.age})
                </option>
              ))}
            </select>

            <div className="flex rounded-lg border border-teal-300 bg-white overflow-hidden text-xs">
              <button
                type="button"
                onClick={() => setSelectedScenario('emergency')}
                className={`px-3 py-1.5 font-semibold transition-colors ${selectedScenario === 'emergency' ? 'bg-red-600 text-white' : 'text-gray-700 hover:bg-gray-50'}`}
              >
                🔴 Emergency Scenario
              </button>
              <button
                type="button"
                onClick={() => setSelectedScenario('routine')}
                className={`px-3 py-1.5 font-semibold transition-colors ${selectedScenario === 'routine' ? 'bg-teal-600 text-white' : 'text-gray-700 hover:bg-gray-50'}`}
              >
                🟢 Routine Scenario
              </button>
            </div>

            <button
              onClick={runWorkflow}
              disabled={isRunning}
              className="inline-flex items-center gap-2 rounded-lg bg-teal-600 px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-teal-500 disabled:opacity-50 transition-colors"
            >
              {isRunning ? <Loader2 className="size-4 animate-spin" /> : <Bot className="size-4" />}
              {isRunning ? 'Agents Processing...' : 'Execute 9-Agent Graph'}
            </button>
          </div>
        </div>
        
        {errorMsg && (
          <div className="p-6 bg-red-50 border-t border-red-100 text-red-700 text-sm">
            {errorMsg}
          </div>
        )}

        {workflowResult && (
          <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6 bg-white border-t border-teal-100">
            <div className="col-span-1 md:col-span-2">
              <div className={`p-4 rounded-lg flex items-start gap-3 ${workflowResult.emergency ? 'bg-red-50 border border-red-200 text-red-900' : 'bg-green-50 border border-green-200 text-green-900'}`}>
                {workflowResult.emergency ? <AlertTriangle className="size-6 text-red-600 shrink-0 mt-0.5" /> : <CheckCircle2 className="size-6 text-green-600 shrink-0 mt-0.5" />}
                <div>
                  <h3 className="font-bold text-base">Agent Network Consensus: {workflowResult.emergency ? 'EMERGENCY TRIAGE DETECTED' : 'ROUTINE ANC MONITORING'}</h3>
                  <p className="text-xs mt-1 leading-relaxed">{workflowResult.clinical_summary || 'No clinical summary generated.'}</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <h4 className="flex items-center gap-2 font-semibold text-gray-900 text-xs uppercase tracking-wider mb-2">
                <Share2 className="size-4 text-teal-600" /> Smart Referral Agent Output
              </h4>
              <p className="text-xs text-gray-700 whitespace-pre-wrap leading-relaxed">
                {workflowResult.referral_info?.recommendation || workflowResult.referral_info?.facility_name || 'No referral needed.'}
              </p>
            </div>

            <div className="bg-gray-50 p-4 rounded-lg border border-gray-200">
              <h4 className="flex items-center gap-2 font-semibold text-gray-900 text-xs uppercase tracking-wider mb-2">
                <MessageSquare className="size-4 text-teal-600" /> Communication Agent Output
              </h4>
              <div className="text-xs text-gray-700 space-y-1">
                <p><span className="font-semibold">Dispatch Status:</span> {workflowResult.communication_status || 'Delivered'}</p>
                <p><span className="font-semibold">Channel Message:</span> {workflowResult.alert_message || 'Alert dispatched to local clinician & LHW.'}</p>
              </div>
            </div>

            {workflowResult.report_content && (
              <div className="col-span-1 md:col-span-2 bg-gray-50 p-4 rounded-lg border border-gray-200">
                <h4 className="flex items-center gap-2 font-semibold text-gray-900 text-xs uppercase tracking-wider mb-2">
                  <FileText className="size-4 text-teal-600" /> Final Structured Case Report
                </h4>
                <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono bg-white p-3 rounded border border-gray-200 max-h-60 overflow-y-auto">
                  {workflowResult.report_content}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 9 Agent Nodes Registry Overview */}
      <div className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="border-b border-gray-200 bg-gray-50/50 px-6 py-4">
          <h2 className="flex items-center gap-2 text-base font-semibold leading-6 text-gray-900">
            <Activity className="size-5 text-gray-500" />
            Registered Agent Nodes (9 Specialized Sub-Agents)
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
              <p className="text-sm font-semibold text-red-900">Failed to load agent node status</p>
            </div>
          ) : nodes && nodes.length > 0 ? (
            <ul className="divide-y divide-gray-100">
              {nodes.map((node) => (
                <li key={node.name} className="flex items-center justify-between gap-x-6 p-5 hover:bg-gray-50 transition-colors">
                  <div className="min-w-0 flex items-start gap-4">
                    <div className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-lg bg-teal-50 text-teal-700 ring-1 ring-inset ring-teal-200">
                      <Bot className="size-4" />
                    </div>
                    <div>
                      <h3 className="text-xs font-bold leading-5 text-gray-900 font-mono uppercase">{node.name}</h3>
                      <p className="mt-0.5 text-xs text-gray-500">{node.description}</p>
                    </div>
                  </div>
                  <div className="flex flex-none items-center gap-x-4">
                    <span className="inline-flex items-center rounded-md bg-green-50 px-2 py-1 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-600/20">
                      Active Node
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
