import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Brain,
  AlertCircle,
  Loader2,
  Play,
  Cpu,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import { api } from '@/lib/api-client';
import { FallbackNotice } from '@/components/shared/FallbackNotice';

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

    try {
      const res = await api.post('/models/predict', {
        model: selectedModel,
        features: featureInputs,
      });
      setPredictionResult(res.data);
    } catch (err: any) {
      setPredictError(err.response?.data?.detail || err.message || 'Inference call failed.');
    } finally {
      setIsPredicting(false);
    }
  };

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
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-mono font-bold uppercase tracking-wider text-gray-900">
                    {m.name}
                  </span>
                  {m.executable ? (
                    <span className="size-2 rounded-full bg-emerald-500" title="Model Executable" />
                  ) : (
                    <span className="size-2 rounded-full bg-amber-500" title="Heuristic / Fallback" />
                  )}
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
          <div className="xl:col-span-6 bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
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

            <div className="p-6 space-y-6">
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
              <form onSubmit={handlePredict} className="space-y-4">
                <h4 className="text-xs font-bold text-gray-800 uppercase tracking-wider">
                  Model Input Features ({Object.keys(featureInputs).length})
                </h4>

                <div className="grid grid-cols-2 gap-3 max-h-80 overflow-y-auto pr-1">
                  {Object.keys(featureInputs).map((featKey) => (
                    <div key={featKey}>
                      <label className="block text-[11px] font-medium text-gray-600 truncate" title={featKey}>
                        {featKey}
                      </label>
                      <input
                        type="number"
                        step="any"
                        value={featureInputs[featKey]}
                        onChange={(e) =>
                          setFeatureInputs({ ...featureInputs, [featKey]: Number(e.target.value) })
                        }
                        className="mt-1 block w-full rounded-lg border border-gray-300 px-3 py-1.5 text-xs text-gray-900 focus:border-teal-500 focus:outline-none"
                      />
                    </div>
                  ))}
                </div>

                <button
                  type="submit"
                  disabled={isPredicting}
                  className="w-full flex justify-center items-center gap-2 rounded-xl bg-teal-600 px-4 py-3 text-sm font-semibold text-white shadow-sm hover:bg-teal-500 disabled:opacity-50 transition-colors"
                >
                  {isPredicting ? <Loader2 className="size-5 animate-spin" /> : <Play className="size-4" />}
                  {isPredicting ? 'Executing Model Inference...' : `Run ${activeModelInfo.name} Prediction`}
                </button>
              </form>
            </div>
          </div>

          {/* Right Column: Prediction Output Window */}
          <div className="xl:col-span-6 flex flex-col">
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden flex-1 flex flex-col">
              <div className="border-b border-gray-200 bg-gray-50/50 px-6 py-4 flex items-center justify-between">
                <h3 className="text-base font-bold text-gray-900 flex items-center gap-2">
                  <ShieldCheck className="size-5 text-teal-600" />
                  Model Output & Probabilities
                </h3>
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

                    {/* Result Metrics Box */}
                    <div className="p-5 rounded-xl bg-teal-50/60 border border-teal-200 space-y-4">
                      <div className="flex justify-between items-center">
                        <span className="text-xs font-semibold text-teal-900 uppercase tracking-wider">
                          Primary Target Outcome
                        </span>
                        <span className="px-3 py-1 rounded-full text-xs font-bold bg-teal-700 text-white uppercase">
                          {predictionResult.prediction ?? predictionResult.risk_level ?? predictionResult.fetal_status ?? 'Output Generated'}
                        </span>
                      </div>

                      {predictionResult.confidence !== undefined && (
                        <div className="flex justify-between items-center text-xs text-teal-950 pt-2 border-t border-teal-200">
                          <span>Confidence Score:</span>
                          <span className="font-bold">{(predictionResult.confidence * 100).toFixed(1)}%</span>
                        </div>
                      )}
                    </div>

                    {/* Raw Contract JSON */}
                    <div>
                      <h4 className="text-xs font-bold text-gray-700 uppercase tracking-wider mb-2">
                        Raw API JSON Response
                      </h4>
                      <pre className="text-xs text-gray-800 bg-gray-50 p-4 rounded-xl border border-gray-200 font-mono overflow-x-auto max-h-72">
                        {JSON.stringify(predictionResult, null, 2)}
                      </pre>
                    </div>
                  </div>
                ) : (
                  <div className="flex-1 flex flex-col items-center justify-center p-12 text-center border-2 border-dashed border-gray-200 rounded-xl bg-gray-50/50 min-h-[300px]">
                    <Zap className="size-10 text-teal-500 mb-3" />
                    <h4 className="text-sm font-semibold text-gray-900">Execute Model Input Contract</h4>
                    <p className="mt-1 text-xs text-gray-500 max-w-xs">
                      Adjust feature values on the left and click Run to execute live inference against this model.
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
