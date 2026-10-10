import React from 'react';
import { AlertTriangle, ShieldAlert } from 'lucide-react';

interface FallbackNoticeProps {
  modelName?: string;
  source?: string;
  compact?: boolean;
  className?: string;
}

export const FallbackNotice: React.FC<FallbackNoticeProps> = ({
  modelName = 'ML Model',
  source = 'heuristic_fallback',
  compact = false,
  className = '',
}) => {
  if (compact) {
    return (
      <div
        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-amber-100 text-amber-900 border border-amber-300 ${className}`}
        title="Heuristic Rule-of-Thumb Fallback (Model Unavailable)"
      >
        <AlertTriangle className="w-3.5 h-3.5 text-amber-700 flex-shrink-0" aria-hidden="true" />
        <span>⚠️ Heuristic Fallback ({modelName} Unavailable)</span>
      </div>
    );
  }

  return (
    <div
      role="alert"
      aria-label="Model Fallback Warning"
      className={`p-3.5 rounded-lg border-2 border-amber-300 bg-amber-50/90 text-amber-950 flex items-start gap-3 shadow-sm ${className}`}
    >
      <ShieldAlert className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" aria-hidden="true" />
      <div className="space-y-1 text-xs sm:text-sm">
        <div className="font-bold tracking-wide uppercase flex items-center gap-2 text-amber-900">
          <span>⚠️ HEURISTIC FALLBACK RESULT</span>
          <span className="text-[10px] font-mono px-1.5 py-0.5 bg-amber-200 text-amber-900 rounded border border-amber-400">
            {source}
          </span>
        </div>
        <p className="text-amber-900 font-medium leading-relaxed">
          The primary <strong>{modelName}</strong> machine learning model was offline or unavailable.
          This result was generated using deterministic clinical rule-of-thumb heuristics.
        </p>
        <p className="text-amber-800 text-xs italic">
          * Clinical Safety Directive: Heuristic estimates must be verified manually by a clinician.
        </p>
      </div>
    </div>
  );
};
