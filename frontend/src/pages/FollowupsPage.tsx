import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  CalendarClock,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  AlertCircle,
  Filter,
  Check,
  X,
  FileText,
} from 'lucide-react';
import { api } from '@/lib/api-client';

interface FollowupTask {
  id: string;
  case_id: string;
  patient_id: string;
  action: string;
  priority: 'high' | 'medium' | 'low';
  due_date: string;
  status: 'pending' | 'completed' | 'cancelled';
  notes?: string;
  completed_by?: string;
  completed_at?: string;
}

export default function FollowupsPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<'pending' | 'completed' | 'cancelled' | 'all'>('pending');

  // Task Resolution Modal State
  const [selectedTask, setSelectedTask] = useState<FollowupTask | null>(null);
  const [resolveStatus, setResolveStatus] = useState<'completed' | 'cancelled'>('completed');
  const [notes, setNotes] = useState('');
  const [resolveError, setResolveError] = useState<string | null>(null);

  // Fetch Followup Tasks Queue
  const { data: tasks, isLoading, isError, refetch } = useQuery({
    queryKey: ['followups', statusFilter],
    queryFn: async () => {
      const url = statusFilter === 'all' ? '/followups' : `/followups?status=${statusFilter}`;
      const { data } = await api.get<FollowupTask[]>(url);
      return data;
    },
  });

  // Resolve Task Mutation
  const resolveMutation = useMutation({
    mutationFn: async ({ taskId, status, notes }: { taskId: string; status: 'completed' | 'cancelled'; notes: string }) => {
      const { data } = await api.put(`/followups/${taskId}`, { status, notes });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['followups'] });
      setSelectedTask(null);
      setNotes('');
      setResolveError(null);
    },
    onError: (err: any) => {
      setResolveError(err.response?.data?.detail || err.message || 'Failed to update task.');
    },
  });

  const handleOpenResolve = (task: FollowupTask, actionType: 'completed' | 'cancelled') => {
    setSelectedTask(task);
    setResolveStatus(actionType);
    setNotes(actionType === 'completed' ? 'Care visit completed successfully.' : 'Patient cancelled appointment.');
    setResolveError(null);
  };

  const handleSubmitResolve = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTask || !notes.trim()) return;
    resolveMutation.mutate({
      taskId: selectedTask.id,
      status: resolveStatus,
      notes: notes,
    });
  };

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-gray-900 flex items-center gap-2.5">
            <CalendarClock className="size-6 text-teal-600" />
            ANC Care Followups & Outreach Queue
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Persistent task queue for Lady Health Workers (LHWs) and clinicians to track antenatal care follow-ups and missed visits.
          </p>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-2 bg-gray-100 p-1 rounded-xl border border-gray-200 text-xs font-medium self-start sm:self-auto">
          <Filter className="size-3.5 text-gray-500 ml-2" />
          <button
            onClick={() => setStatusFilter('pending')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              statusFilter === 'pending' ? 'bg-white text-teal-900 font-bold shadow-sm' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Pending
          </button>
          <button
            onClick={() => setStatusFilter('completed')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              statusFilter === 'completed' ? 'bg-white text-teal-900 font-bold shadow-sm' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Completed
          </button>
          <button
            onClick={() => setStatusFilter('cancelled')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              statusFilter === 'cancelled' ? 'bg-white text-teal-900 font-bold shadow-sm' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Cancelled
          </button>
          <button
            onClick={() => setStatusFilter('all')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${
              statusFilter === 'all' ? 'bg-white text-teal-900 font-bold shadow-sm' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            All Tasks
          </button>
        </div>
      </div>

      {/* Task Queue List */}
      <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="flex h-48 items-center justify-center">
            <Loader2 className="size-8 animate-spin text-teal-600" />
          </div>
        ) : isError ? (
          <div className="p-8 text-center bg-red-50 text-red-900">
            <AlertCircle className="size-8 text-red-500 mx-auto mb-2" />
            <h3 className="text-sm font-semibold">Failed to load follow-up task queue</h3>
            <button onClick={() => refetch()} className="mt-2 text-xs font-bold text-teal-700 underline">
              Retry Loading
            </button>
          </div>
        ) : tasks && tasks.length > 0 ? (
          <div className="divide-y divide-gray-100">
            {tasks.map((task) => (
              <div
                key={task.id}
                className="p-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 hover:bg-gray-50/50 transition-colors"
              >
                <div className="space-y-2 max-w-2xl">
                  <div className="flex items-center gap-3">
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase ${
                        task.priority === 'high'
                          ? 'bg-red-100 text-red-800 border border-red-200'
                          : task.priority === 'medium'
                          ? 'bg-amber-100 text-amber-800 border border-amber-200'
                          : 'bg-green-100 text-green-800 border border-green-200'
                      }`}
                    >
                      {task.priority} Priority
                    </span>

                    <span className="text-xs font-mono text-gray-500">
                      Patient ID: {task.patient_id}
                    </span>

                    <span className="text-xs text-gray-400">
                      Due: {task.due_date ? new Date(task.due_date).toLocaleDateString() : 'Immediate'}
                    </span>
                  </div>

                  <h3 className="text-sm font-semibold text-gray-900 leading-snug">
                    {task.action}
                  </h3>

                  {task.notes && (
                    <p className="text-xs text-gray-600 bg-gray-50 p-2.5 rounded-lg border border-gray-200 font-mono">
                      <strong>Resolution Note:</strong> {task.notes}
                    </p>
                  )}
                </div>

                {/* Status / Action Buttons */}
                <div className="flex items-center gap-3 shrink-0">
                  {task.status === 'pending' ? (
                    <>
                      <button
                        onClick={() => handleOpenResolve(task, 'completed')}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-500 transition-colors shadow-sm"
                      >
                        <Check className="size-3.5" /> Complete
                      </button>
                      <button
                        onClick={() => handleOpenResolve(task, 'cancelled')}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gray-100 text-gray-700 text-xs font-semibold hover:bg-gray-200 transition-colors border border-gray-300"
                      >
                        <X className="size-3.5" /> Cancel
                      </button>
                    </>
                  ) : (
                    <span
                      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${
                        task.status === 'completed'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-gray-100 text-gray-600 border border-gray-200'
                      }`}
                    >
                      {task.status === 'completed' ? (
                        <CheckCircle2 className="size-3.5 text-emerald-600" />
                      ) : (
                        <XCircle className="size-3.5 text-gray-400" />
                      )}
                      {task.status.toUpperCase()}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-12 text-center text-sm text-gray-500 space-y-2">
            <Clock className="size-10 text-gray-300 mx-auto mb-2" />
            <h3 className="font-semibold text-gray-800">No {statusFilter} follow-up tasks</h3>
            <p className="text-xs text-gray-500">All outreach tasks for this filter have been completed.</p>
          </div>
        )}
      </div>

      {/* Task Resolution Modal */}
      {selectedTask && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 space-y-5 shadow-xl border border-gray-200 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
                <FileText className="size-5 text-teal-600" />
                Mark Task as {resolveStatus.toUpperCase()}
              </h3>
              <button onClick={() => setSelectedTask(null)} className="text-gray-400 hover:text-gray-600">
                <X className="size-5" />
              </button>
            </div>

            <p className="text-xs text-gray-600 leading-relaxed">
              <strong>Action:</strong> {selectedTask.action}
            </p>

            {resolveError && (
              <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-xs text-red-700">
                {resolveError}
              </div>
            )}

            <form onSubmit={handleSubmitResolve} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1">
                  Clinical / Outreach Resolution Notes (Required)
                </label>
                <textarea
                  rows={3}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Enter details of the home visit, phone call, or reason for cancellation..."
                  className="block w-full rounded-xl border border-gray-300 p-3 text-xs text-gray-900 focus:border-teal-500 focus:outline-none"
                  required
                />
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedTask(null)}
                  className="px-4 py-2 rounded-lg border border-gray-300 text-xs font-semibold text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={resolveMutation.isPending || !notes.trim()}
                  className="px-4 py-2 rounded-lg bg-teal-600 text-xs font-semibold text-white hover:bg-teal-500 disabled:opacity-50 flex items-center gap-1.5"
                >
                  {resolveMutation.isPending && <Loader2 className="size-3.5 animate-spin" />}
                  Submit Resolution
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
