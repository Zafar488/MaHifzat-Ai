import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  FileText,
  Download,
  Printer,
  Globe,
  Loader2,
  FileSpreadsheet,
  ChevronDown,
  ChevronRight,
  Shield,
  Hospital,
} from 'lucide-react';
import { api } from '@/lib/api-client';
import { FallbackNotice } from '@/components/shared/FallbackNotice';

interface Patient {
  patient_id: string;
  name: string;
  age?: number;
  gestational_age_weeks?: number;
  phone?: string;
}

interface AssessmentEncounter {
  case_id: string;
  created_at: string;
  triage_level: string;
  urgency?: string;
}

function escapeHtml(text: string): string {
  return (text || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function buildReportHtml(report: any): string {
  if (!report || !report.languages) return '';
  const articles = ['en', 'ur'].map((lang) => {
    const item = report.languages[lang];
    if (!item) return '';
    const body = (item.sections || [])
      .map(
        (s: any) =>
          `<section><h2>${escapeHtml(s.heading)}</h2><ul>` +
          (s.lines || []).map((line: string) => `<li>${escapeHtml(line)}</li>`).join('') +
          `</ul></section>`
      )
      .join('');
    const dir = lang === 'ur' ? 'rtl' : 'ltr';
    return `<article lang="${lang}" dir="${dir}"><h1>${escapeHtml(item.title)}</h1>${body}</article>`;
  });
  return `<!doctype html><html><head><meta charset="utf-8"><title>MaaHifazat report</title><style>body{max-width:960px;margin:24px auto;padding:20px;font:17px/1.8 Arial,sans-serif;color:#123b37}article{margin-bottom:48px}section{break-inside:avoid}li{white-space:pre-wrap;overflow-wrap:anywhere}h2{font-size:20px}@media print{article+article{break-before:page}}</style></head><body>${articles.join('')}</body></html>`;
}

function buildReportText(report: any): string {
  if (!report || !report.languages) return '';
  const enText = report.languages.en?.text || '';
  const urText = report.languages.ur?.text || '';
  return `${enText}\n\n========================================\n\n${urText}`;
}

function triggerDownload(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export default function ReportsPage() {
  const [searchParams] = useSearchParams();
  const urlPatientId = searchParams.get('patient_id') || '';
  const urlCaseId = searchParams.get('case_id') || '';

  const [selectedPatientId, setSelectedPatientId] = useState<string>(urlPatientId);
  const [selectedCaseId, setSelectedCaseId] = useState<string>(urlCaseId);
  const [activeLang, setActiveLang] = useState<'en' | 'ur'>('en');
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    care: true,
    referral: true,
  });

  // Fetch all patients
  const { data: patients, isLoading: loadingPatients } = useQuery({
    queryKey: ['patients-list'],
    queryFn: async () => {
      const { data } = await api.get<Patient[]>('/patients');
      return data;
    },
  });

  // Fetch cases for selected patient
  const { data: assessments, isLoading: loadingAssessments } = useQuery({
    queryKey: ['patient-assessments', selectedPatientId],
    queryFn: async () => {
      if (!selectedPatientId) return [];
      const { data } = await api.get<AssessmentEncounter[]>(`/patients/${selectedPatientId}/assessments`);
      return data;
    },
    enabled: Boolean(selectedPatientId),
  });

  // Fetch full case data when case selected
  const { data: caseData, isLoading: loadingCase } = useQuery({
    queryKey: ['case-detail', selectedCaseId],
    queryFn: async () => {
      if (!selectedCaseId) return null;
      const { data } = await api.get<any>(`/agents/cases/${selectedCaseId}`);
      return data;
    },
    enabled: Boolean(selectedCaseId),
  });

  // Sync URL params if provided
  React.useEffect(() => {
    if (urlPatientId && urlPatientId !== selectedPatientId) {
      setSelectedPatientId(urlPatientId);
    }
    if (urlCaseId && urlCaseId !== selectedCaseId) {
      setSelectedCaseId(urlCaseId);
    }
  }, [urlPatientId, urlCaseId]);

  // Auto-select first patient & first case if not URL specified
  React.useEffect(() => {
    if (patients && patients.length > 0 && !selectedPatientId && !urlPatientId) {
      setSelectedPatientId(patients[0].patient_id);
    }
  }, [patients, selectedPatientId, urlPatientId]);

  React.useEffect(() => {
    if (assessments && assessments.length > 0 && !urlCaseId) {
      const validCase = assessments.find((a) => Boolean(a.case_id));
      if (validCase && !selectedCaseId) {
        setSelectedCaseId(validCase.case_id);
      }
    }
  }, [assessments, urlCaseId, selectedCaseId]);

  const toggleSection = (key: string) => {
    setExpandedSections((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const caseResult = caseData?.result || {};
  const reportingResult = caseResult?.reporting_result || {};
  const reports = reportingResult?.reports;

  // Model fallback flag detection
  const isFallback =
    caseResult?.model_available === false ||
    caseResult?.source === 'heuristic_fallback' ||
    caseResult?.clinical_risk_result?.maternal_risk?.source === 'heuristic_fallback';

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-gray-200 pb-5">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2.5">
            <FileText className="w-7 h-7 text-teal-600" />
            Bilingual Clinical Case Reports · دو طرفہ رپورٹس
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            Mother &amp; Baby Care and Hospital Referral Reports in English and Urdu (اردو). Printable HTML &amp; plain text exports.
          </p>
        </div>

        {/* Language selector toggle */}
        <div className="flex items-center gap-2 bg-gray-100 p-1 rounded-lg border border-gray-200 self-start sm:self-auto">
          <Globe className="w-4 h-4 text-gray-500 ml-2" />
          <button
            type="button"
            onClick={() => setActiveLang('en')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
              activeLang === 'en' ? 'bg-teal-600 text-white shadow-sm' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            English
          </button>
          <button
            type="button"
            onClick={() => setActiveLang('ur')}
            className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-colors ${
              activeLang === 'ur' ? 'bg-teal-600 text-white shadow-sm' : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            اردو (Urdu)
          </button>
        </div>
      </div>

      {/* Patient & Case Selection Controls */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4 sm:p-5 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1.5">
            Select Patient (مریضہ کی پروفائل)
          </label>
          {loadingPatients ? (
            <div className="flex items-center gap-2 text-sm text-gray-500 py-2">
              <Loader2 className="w-4 h-4 animate-spin text-teal-600" /> Loading patients...
            </div>
          ) : (
            <select
              value={selectedPatientId}
              onChange={(e) => setSelectedPatientId(e.target.value)}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-teal-600 bg-white"
            >
              <option value="">-- Choose Patient --</option>
              {patients?.map((p) => (
                <option key={p.patient_id} value={p.patient_id}>
                  {p.name} ({p.patient_id.slice(0, 8)})
                </option>
              ))}
            </select>
          )}
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1.5">
            Select Saved Case / Assessment (محفوظ کیس)
          </label>
          {loadingAssessments ? (
            <div className="flex items-center gap-2 text-sm text-gray-500 py-2">
              <Loader2 className="w-4 h-4 animate-spin text-teal-600" /> Loading encounters...
            </div>
          ) : (
            <select
              value={selectedCaseId}
              onChange={(e) => setSelectedCaseId(e.target.value)}
              disabled={!selectedPatientId || !assessments?.length}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-teal-600 bg-white disabled:bg-gray-50 disabled:text-gray-400"
            >
              {!assessments?.length ? (
                <option value="">No saved assessments found</option>
              ) : (
                assessments.map((a) => (
                  <option key={a.case_id} value={a.case_id}>
                    {new Date(a.created_at).toLocaleString()} · {a.triage_level || 'Assessed'} · ({a.case_id.slice(0, 8)})
                  </option>
                ))
              )}
            </select>
          )}
        </div>
      </div>

      {/* Fallback Warning Notice if heuristic used */}
      {isFallback && (
        <FallbackNotice
          modelName="Maternal & Fetal Risk Models"
          source={caseResult?.source || 'heuristic_fallback'}
        />
      )}

      {/* Loading & Empty States */}
      {loadingCase && (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <Loader2 className="w-8 h-8 animate-spin text-teal-600 mx-auto mb-3" />
          <p className="text-sm font-medium text-gray-600">Generating bilingual clinical reports...</p>
        </div>
      )}

      {!loadingCase && !selectedCaseId && (
        <div className="bg-white rounded-xl border border-dashed border-gray-300 p-12 text-center">
          <FileSpreadsheet className="w-12 h-12 text-gray-400 mx-auto mb-3" />
          <h3 className="text-base font-bold text-gray-800">No Assessment Selected</h3>
          <p className="text-sm text-gray-500 max-w-md mx-auto mt-1">
            Please select a patient and a saved case above, or run a new risk assessment from the Risk Assessment page to view bilingual reports.
          </p>
        </div>
      )}

      {/* Reports Display Section */}
      {!loadingCase && reports && (
        <div className="space-y-6">
          {(['care', 'referral'] as const).map((kind) => {
            const report = reports[kind];
            if (!report) return null;

            const isExpanded = expandedSections[kind];
            const titleLabel =
              kind === 'care'
                ? 'Report 1 · Mother and Baby Care (رپورٹ ۱: ماں اور بچے کی دیکھ بھال)'
                : 'Report 2 · Location and Hospital Referral (رپورٹ ۲: مقام اور ہسپتال ریفرل)';
            const icon = kind === 'care' ? Shield : Hospital;

            const langItem = report.languages?.[activeLang] || report.languages?.en;
            const isUrdu = activeLang === 'ur';

            return (
              <div
                key={kind}
                className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden transition-all"
              >
                {/* Header card banner */}
                <div className="bg-gradient-to-r from-teal-900 to-teal-800 text-white px-5 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => toggleSection(kind)}
                      className="p-1 rounded hover:bg-white/10 transition-colors"
                      aria-label="Toggle section"
                    >
                      {isExpanded ? <ChevronDown className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
                    </button>
                    <div>
                      <h2 className="text-base font-bold flex items-center gap-2">
                        {React.createElement(icon, { className: 'w-5 h-5 text-teal-300' })}
                        {titleLabel}
                      </h2>
                      <p className="text-xs text-teal-100 mt-0.5">
                        Urgency: <span className="font-semibold uppercase tracking-wide">{report.urgency || 'routine'}</span> · Status: {report.review_status || 'pending'}
                      </p>
                    </div>
                  </div>

                  {/* Export buttons */}
                  <div className="flex items-center gap-2 self-end sm:self-auto">
                    <button
                      type="button"
                      onClick={() =>
                        triggerDownload(
                          buildReportHtml(report),
                          `${kind}-report-${report.case_id || 'case'}.html`,
                          'text/html'
                        )
                      }
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-teal-700 hover:bg-teal-600 text-white transition-colors border border-teal-600"
                      title="Download combined HTML for browser printing"
                    >
                      <Download className="w-3.5 h-3.5" /> HTML (En + Ur)
                    </button>
                    <button
                      type="button"
                      onClick={() =>
                        triggerDownload(
                          buildReportText(report),
                          `${kind}-report-${report.case_id || 'case'}.txt`,
                          'text/plain; charset=utf-8'
                        )
                      }
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors border border-white/20"
                      title="Download raw bilingual text"
                    >
                      <Printer className="w-3.5 h-3.5" /> Text (TXT)
                    </button>
                  </div>
                </div>

                {/* Collapsible Content */}
                {isExpanded && langItem && (
                  <div
                    className={`p-6 space-y-6 ${isUrdu ? 'text-right' : 'text-left'}`}
                    dir={isUrdu ? 'rtl' : 'ltr'}
                  >
                    <div className="border-b border-gray-100 pb-3">
                      <h3 className="text-lg font-bold text-gray-900">{langItem.title}</h3>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {report.llm_generated
                          ? 'Bilingual Groq AI explanation included (Clinician review required).'
                          : 'Recorded-fact report available; bilingual Groq explanation was not generated for this case.'}
                      </p>
                    </div>

                    {/* Report Sections */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {(langItem.sections || []).map((sec: any, idx: number) => (
                        <div
                          key={idx}
                          className="bg-gray-50 rounded-lg p-4 border border-gray-200/80 space-y-2"
                        >
                          <h4 className="font-bold text-sm text-teal-900 border-b border-gray-200 pb-1.5">
                            {sec.heading}
                          </h4>
                          <ul className="space-y-1.5 text-xs text-gray-700 leading-relaxed">
                            {(sec.lines || []).map((line: string, lIdx: number) => (
                              <li key={lIdx} className="flex items-start gap-2">
                                <span className="text-teal-600 font-bold select-none">•</span>
                                <span className="flex-1 whitespace-pre-wrap">{line}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
