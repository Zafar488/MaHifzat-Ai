import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Brain,
  AlertCircle,
  Loader2,
  Play,
  Cpu,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  BarChart2,
  Code,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  Activity,
  Layers,
} from 'lucide-react';
import { api } from '@/lib/api-client';
import { getErrorMessage } from '@/lib/utils';
import { FallbackNotice } from '@/components/shared/FallbackNotice';
import { NearestHospitalMapCard } from '@/components/shared/NearestHospitalMapCard';

interface ModelInfo {
  name: string;
  executable: boolean;
  care_decision_use: boolean;
  intended_use?: string;
  target?: string;
  internal_macro_f1?: number;
  features?: string[];
  example?: Record<string, any>;
  version?: string;
  reason?: string;
}

export default function ModelWorkbenchPage() {
  const [selectedModel, setSelectedModel] = useState<string>('maternalguard');
  const [featureInputs, setFeatureInputs] = useState<Record<string, any>>({
    Age: 30,
    SystolicBP: 120,
    DiastolicBP: 80,
    BS: 7.0,
    BodyTemp: 98.6,
    HeartRate: 76,
  });

  const [predictionResult, setPredictionResult] = useState<any>(null);
  const [isPredicting, setIsPredicting] = useState(false);
  const [predictError, setPredictError] = useState<string | null>(null);
  const [showRawJson, setShowRawJson] = useState(false);
  const [copiedJson, setCopiedJson] = useState(false);

  // Fetch 5-Model Catalog
  const { data: catalogData, isLoading, isError, refetch } = useQuery({
    queryKey: ['models', 'catalog'],
    queryFn: async () => {
      const { data } = await api.get<{ models: ModelInfo[] }>('/models/catalog');
      return data.models;
    },
  });

  const activeModelInfo = catalogData?.find((m) => m.name === selectedModel);

  const handleSelectModel = (modelName: string) => {
    setSelectedModel(modelName);
    setPredictionResult(null);
    setPredictError(null);
    setShowRawJson(false);

    const model = catalogData?.find((m) => m.name === modelName);
    if (model && model.example) {
      setFeatureInputs(model.example);
    } else if (model && model.features) {
      const defaults: Record<string, any> = {};
      model.features.forEach((f) => (defaults[f] = 0));
      setFeatureInputs(defaults);
    }
  };

  const handlePredict = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsPredicting(true);
    setPredictError(null);
    setPredictionResult(null);
    setShowRawJson(false);

    try {
      const res = await api.post('/models/predict', {
        model: selectedModel,
        features: featureInputs,
      });
      setPredictionResult(res.data);
    } catch (err: any) {
      setPredictError(getErrorMessage(err, 'Inference call failed.'));
    } finally {
      setIsPredicting(false);
    }
  };

  const copyJsonToClipboard = () => {
    if (predictionResult) {
      navigator.clipboard.writeText(JSON.stringify(predictionResult, null, 2));
      setCopiedJson(true);
      setTimeout(() => setCopiedJson(false), 2000);
    }
  };

  const primaryOutcome =
    predictionResult?.prediction ??
    predictionResult?.risk_level ??
    predictionResult?.fetal_status ??
    predictionResult?.label ??
    'Result Generated';

  const getOutcomeStyle = (targetVal: any) => {
    const normalized = String(targetVal || '').toLowerCase();
    if (['high', 'high risk', 'emergency', 'pathological', '1', 'severe'].some((k) => normalized.includes(k))) {
      return {
        badgeBg: 'bg-red-600 text-white border-red-700',
        cardBg: 'bg-red-50/70 border-red-200 text-red-950',
        barBg: 'bg-red-500',
        icon: AlertTriangle,
        iconColor: 'text-red-600',
      };
    }
    if (['mid', 'medium', 'moderate', 'suspect', 'warning'].some((k) => normalized.includes(k))) {
      return {
        badgeBg: 'bg-amber-600 text-white border-amber-700',
        cardBg: 'bg-amber-50/70 border-amber-200 text-amber-950',
        barBg: 'bg-amber-500',
        icon: AlertCircle,
        iconColor: 'text-amber-600',
      };
    }
    return {
      badgeBg: 'bg-emerald-600 text-white border-emerald-700',
      cardBg: 'bg-emerald-50/70 border-emerald-200 text-emerald-950',
      barBg: 'bg-emerald-500',
      icon: CheckCircle2,
      iconColor: 'text-emerald-600',
    };
  };

  const getBarColor = (label: string, index: number) => {
    const l = label.toLowerCase();
    if (l.includes('high') || l.includes('pathological') || l.includes('1')) return 'bg-red-500';
    if (l.includes('mid') || l.includes('moderate') || l.includes('suspect')) return 'bg-amber-500';
    if (l.includes('low') || l.includes('normal') || l.includes('0')) return 'bg-emerald-500';
    const colors = ['bg-teal-500', 'bg-blue-500', 'bg-indigo-500', 'bg-purple-500', 'bg-pink-500'];
    return colors[index % colors.length];
  };

  const outcomeStyle = getOutcomeStyle(primaryOutcome);
  const OutcomeIcon = outcomeStyle.icon;

  const probabilitiesMap: Record<string, number> = predictionResult?.probabilities || {};
  const probEntries = Object.entries(probabilitiesMap);

  return (
    <div className="mx-auto w-full max-w-7xl px-4 py-8 sm:px-6 lg:px-8 space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-gray-900 flex items-center gap-2">
          <Brain className="size-6 text-teal-600" />
          5-Model Research & Prediction Workbench
        </h1>
        <p className="mt-2 text-sm text-gray-500">
          Direct contract inference against the 5 specialized machine learning models (MaternalGuard, FetalWatch, PretermGuard, GestationInsight, CareReach).
        </p>
      </div>

      {/* Model Selection Tabs */}
      {isLoading ? (
        <div className="flex h-32 items-center justify-center bg-white rounded-xl border border-gray-200">
          <Loader2 className="size-6 animate-spin text-teal-600" />
        </div>
      ) : isError ? (
        <div className="p-6 rounded-xl bg-red-50 border border-red-200 text-center">
          <AlertCircle className="size-8 text-red-500 mx-auto mb-2" />
          <h3 className="text-sm font-semibold text-red-900">Failed to load model catalog</h3>
          <button onClick={() => refetch()} className="mt-3 text-xs font-bold text-teal-700 underline">
            Retry Loading Catalog
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {catalogData?.map((m) => (
            <button
              key={m.name}
              onClick={() => handleSelectModel(m.name)}
              className={`p-4 rounded-xl border text-left transition-all flex flex-col justify-between ${
                selectedModel === m.name
                  ? 'border-teal-600 bg-teal-50/70 ring-2 ring-teal-600/20 shadow-sm'
                  : 'border-gray-200 bg-white hover:bg-gray-50'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-1 gap-1">
                  <span className="text-xs font-mono font-bold uppercase tracking-wider text-gray-900 truncate">
                    {m.name}
                  </span>
                  <span
                    className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase shrink-0 ${
                      m.care_decision_use ? 'bg-teal-100 text-teal-800 border border-teal-200' : 'bg-purple-100 text-purple-800 border border-purple-200'
                    }`}
                  >
                    {m.care_decision_use ? 'Clinical' : 'Research'}
                  </span>
                </div>
                <p className="text-[11px] text-gray-500 line-clamp-2 mt-1">
                  Target: {m.target || 'Classification'}
                </p>
              </div>

              <div className="mt-3 pt-2 border-t border-gray-100 flex items-center justify-between text-[11px]">
                <span className="text-gray-400">Macro-F1</span>
                <span className="font-semibold text-gray-800">
                  {m.internal_macro_f1 ? (m.internal_macro_f1 * 100).toFixed(1) + '%' : 'N/A'}
                </span>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Model Details & Dynamic Inference Panel */}
      {activeModelInfo && (
        <div className="grid grid-cols-1 xl:grid-cols-12 gap-8">
          {/* Left Column: Model Metadata & Feature Input Form */}
          <div className="xl:col-span-6 bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden flex flex-col">
            <div className="border-b border-gray-200 bg-gray-50/50 px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cpu className="size-5 text-teal-600" />
                <h3 className="text-base font-bold text-gray-900 uppercase font-mono">
                  {activeModelInfo.name} Inference Contract
                </h3>
              </div>
              <span className="text-xs px-2.5 py-1 rounded-full bg-teal-100 text-teal-900 font-semibold">
                Version: {activeModelInfo.version || 'v1.0'}
              </span>
            </div>

            <div className="p-6 space-y-6 flex-1 flex flex-col justify-between">
              {/* Intended Use Notice */}
              <div className="text-xs p-3 rounded-lg bg-gray-50 border border-gray-200 text-gray-700">
                <strong>Intended Use:</strong> {activeModelInfo.intended_use || 'Clinical risk classification research.'}
              </div>

              {!activeModelInfo.executable && (
                <FallbackNotice
                  modelName={activeModelInfo.name}
                  source={activeModelInfo.reason || 'heuristic_fallback'}
                />
              )}

              {/* Dynamic Inputs */}
              <form onSubmit={handlePredict} className="space-y-4 flex-1 flex flex-col justify-between">
                <div>
                  <h4 className="text-xs font-bold text-gray-800 uppercase tracking-wider mb-3 flex items-center justify-between">
                    <span>Model Input Features ({Object.keys(featureInputs).length})</span>
                    <span className="text-[11px] font-normal text-gray-400">Values editable</span>
                  </h4>

                  <div className="grid grid-cols-2 gap-3 max-h-80 overflow-y-auto pr-1">
                    {Object.keys(featureInputs).map((featKey) => (
                      <div key={featKey} className="bg-gray-50/50 p-2 rounded-lg border border-gray-200/80">
                        <label className="block text-[11px] font-medium text-gray-700 truncate mb-1" title={featKey}>
                          {featKey}
                        </label>
                        <input
                          type="number"
                          step="any"
                          value={featureInputs[featKey]}
                          onChange={(e) =>
                            setFeatureInputs({ ...featureInputs, [featKey]: Number(e.target.value) })
                          }
                          className="block w-full rounded-md border border-gray-300 px-2.5 py-1 text-xs text-gray-900 bg-white focus:border-teal-500 focus:outline-none focus:ring-1 focus:ring-teal-500 font-mono"
                        />
                      </div>
                    ))}
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isPredicting}
                  className="w-full flex justify-center items-center gap-2 rounded-xl bg-teal-600 px-4 py-3 text-sm font-semibold text-white shadow-sm hover:bg-teal-500 disabled:opacity-50 transition-colors mt-4"
                >
                  {isPredicting ? <Loader2 className="size-5 animate-spin" /> : <Play className="size-4" />}
                  {isPredicting ? 'Executing Model Inference...' : `Run ${activeModelInfo.name} Prediction`}
                </button>
              </form>
            </div>
          </div>

          {/* Right Column: Visual Graphical Output Panel */}
          <div className="xl:col-span-6 flex flex-col">
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden flex-1 flex flex-col">
              <div className="border-b border-gray-200 bg-gray-50/50 px-6 py-4 flex items-center justify-between">
                <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
                  <ShieldCheck className="size-5 text-teal-600" />
                  Model Output & Graphical Assessment
                </h3>
                {predictionResult && (
                  <span className="text-xs font-mono text-gray-500 px-2 py-0.5 rounded bg-gray-100 border border-gray-200">
                    Source: {predictionResult.source || 'ml_pipeline'}
                  </span>
                )}
              </div>

              <div className="p-6 flex-1 flex flex-col justify-between space-y-6">
                {predictError && (
                  <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700 flex items-start gap-2">
                    <AlertCircle className="size-4 shrink-0 text-red-500 mt-0.5" />
                    <span>{predictError}</span>
                  </div>
                )}

                {predictionResult ? (
                  <div className="space-y-6">
                    {/* Fallback Notice if model response flagged heuristic */}
                    {(predictionResult.model_available === false || predictionResult.source === 'heuristic_fallback') && (
                      <FallbackNotice
                        modelName={selectedModel}
                        source={predictionResult.source || 'heuristic_fallback'}
                      />
                    )}

                    {/* Primary Prediction Hero Banner (GUI Result Card) */}
                    <div className={`p-5 rounded-2xl border shadow-sm transition-all space-y-4 ${outcomeStyle.cardBg}`}>
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                        <div className="space-y-1">
                          <span className="text-[11px] font-bold uppercase tracking-wider text-gray-500 flex items-center gap-1.5">
                            <Activity className="size-3.5 text-teal-600" />
                            Predicted Target Classification
                          </span>
                          <h4 className="text-lg font-bold text-gray-900 capitalize flex items-center gap-2">
                            <OutcomeIcon className={`size-5 ${outcomeStyle.iconColor}`} />
                            <span>{primaryOutcome}</span>
                          </h4>
                        </div>

                        <span className={`self-start sm:self-center px-4 py-1.5 rounded-full text-xs font-extrabold uppercase border shadow-sm ${outcomeStyle.badgeBg}`}>
                          {primaryOutcome}
                        </span>
                      </div>

                      {/* Confidence Score Bar */}
                      {typeof predictionResult.confidence === 'number' && (
                        <div className="space-y-1.5 pt-3 border-t border-gray-200/60">
                          <div className="flex justify-between items-center text-xs">
                            <span className="font-semibold text-gray-700">Model Certainty / Confidence Score:</span>
                            <span className="font-extrabold text-gray-900">
                              {(predictionResult.confidence * 100).toFixed(1)}%
                            </span>
                          </div>

                          <div className="h-2.5 w-full bg-gray-200/80 rounded-full overflow-hidden">
                            <div
                              className={`h-full transition-all duration-500 ${outcomeStyle.barBg}`}
                              style={{ width: `${Math.min(100, Math.max(0, predictionResult.confidence * 100))}%` }}
                            />
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Probabilities Breakdown Bar Chart (GUI Graphic Gauges) */}
                    {probEntries.length > 0 && (
                      <div className="p-5 rounded-2xl bg-gray-50/70 border border-gray-200 space-y-4">
                        <h4 className="text-xs font-bold text-gray-800 uppercase tracking-wider flex items-center gap-1.5">
                          <BarChart2 className="size-4 text-teal-600" />
                          Class Probability Distribution ({probEntries.length} Classes)
                        </h4>

                        <div className="space-y-3">
                          {probEntries.map(([label, probVal], idx) => {
                            const pct = (probVal * 100).toFixed(1);
                            const barClass = getBarColor(label, idx);
                            return (
                              <div key={label} className="space-y-1">
                                <div className="flex justify-between items-center text-xs">
                                  <span className="font-medium text-gray-800 capitalize truncate max-w-[220px]" title={label}>
                                    {label}
                                  </span>
                                  <span className="font-mono font-semibold text-gray-600">{pct}%</span>
                                </div>
                                <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                                  <div
                                    className={`h-full transition-all duration-500 ${barClass}`}
                                    style={{ width: `${Math.min(100, Math.max(0, probVal * 100))}%` }}
                                  />
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* Out of Training Range Feature Alerts */}
                    {Array.isArray(predictionResult.out_of_training_range_features) && predictionResult.out_of_training_range_features.length > 0 && (
                      <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs space-y-1">
                        <div className="font-bold flex items-center gap-1.5">
                          <AlertTriangle className="size-4 text-amber-600 shrink-0" />
                          <span>Out-of-Training Bounds Notice:</span>
                        </div>
                        <p className="text-amber-800 leading-relaxed">
                          The following feature inputs exceed typical training dataset distributions:
                        </p>
                        <div className="flex flex-wrap gap-1.5 pt-1">
                          {predictionResult.out_of_training_range_features.map((f: string) => (
                            <span key={f} className="px-2 py-0.5 rounded bg-amber-100 text-amber-900 font-mono font-semibold text-[11px] border border-amber-300">
                              {f}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Developer Raw JSON Inspector Toggle */}
                    <div className="pt-2 border-t border-gray-100">
                      <button
                        onClick={() => setShowRawJson(!showRawJson)}
                        className="flex items-center justify-between w-full text-xs font-semibold text-gray-500 hover:text-gray-800 transition-colors p-2 rounded-lg hover:bg-gray-100"
                      >
                        <span className="flex items-center gap-1.5">
                          <Code className="size-4 text-teal-600" />
                          {showRawJson ? 'Hide Raw API JSON Response' : 'Inspect Raw API JSON Contract Response'}
                        </span>
                        {showRawJson ? <ChevronUp className="size-4" /> : <ChevronDown className="size-4" />}
                      </button>

                      {showRawJson && (
                        <div className="mt-3 relative">
                          <div className="flex items-center justify-between bg-gray-800 text-gray-200 px-4 py-2 rounded-t-xl text-[11px] font-mono">
                            <span>HTTP 200 OK — Model Payload</span>
                            <button
                              onClick={copyJsonToClipboard}
                              className="flex items-center gap-1 hover:text-white text-gray-300 transition-colors"
                            >
                              {copiedJson ? <Check className="size-3.5 text-emerald-400" /> : <Copy className="size-3.5" />}
                              <span>{copiedJson ? 'Copied!' : 'Copy JSON'}</span>
                            </button>
                          </div>
                          <pre className="text-xs text-emerald-400 bg-gray-900 p-4 rounded-b-xl font-mono overflow-x-auto max-h-72 border border-gray-800">
                            {JSON.stringify(predictionResult, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>

                    {/* Nearest Hospital Routing for Mid & High Risk Verification */}
                    <div className="pt-4">
                      <NearestHospitalMapCard
                        riskLevel={primaryOutcome}
                        title={`Nearest Emergency Hospital Route for ${activeModelInfo.name} Output`}
                      />
                    </div>
                  </div>
                ) : (
                  <div className="flex-1 flex flex-col items-center justify-center p-12 text-center border-2 border-dashed border-gray-200 rounded-2xl bg-gray-50/50 min-h-[340px]">
                    <div className="size-14 rounded-full bg-teal-100 text-teal-700 flex items-center justify-center mb-4">
                      <Layers className="size-7" />
                    </div>
                    <h4 className="text-base font-bold text-gray-900">Execute Model Input Contract</h4>
                    <p className="mt-1 text-xs text-gray-500 max-w-sm leading-relaxed">
                      Adjust feature values on the left and click <strong>Run {activeModelInfo.name} Prediction</strong> to see graphical prediction indicators and class probabilities.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
