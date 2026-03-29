import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Download, RotateCcw, AlertTriangle } from 'lucide-react';
import { analyzeImage, resolveBackendUrl, type ApiResponse } from '../lib/api';

import PredictionCard from './dashboard/PredictionCard';
import ExplainabilityPanel from './dashboard/ExplainabilityPanel';
import GeminiExplanation from './dashboard/GeminiExplanation';
import QuickSummary from './dashboard/QuickSummary';
import HistoryPanel from './dashboard/HistoryPanel';

export default function Dashboard({ file, onReset }: { file: File, onReset: () => void }) {
  const [apiData, setApiData] = useState<ApiResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    analyzeImage(file)
      .then(res => { if (mounted) setApiData(res); })
      .catch(err => { if (mounted) setError(err.message ?? "Analysis failed."); });
    return () => { mounted = false; };
  }, [file]);

  const handleDownload = () => {
    const reportUrl = resolveBackendUrl(apiData?.report ?? null);
    if (reportUrl) {
      window.open(reportUrl, "_blank");
    }
  };

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-6">
        <AlertTriangle className="w-16 h-16 text-danger" />
        <h2 className="text-2xl font-bold text-danger">Analysis Failed</h2>
        <p className="text-gray-400 max-w-md text-center">{error}</p>
        <button onClick={onReset} className="glass-button">Try Again</button>
      </div>
    );
  }

  if (!apiData) return null;

  const { data, report } = apiData;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className="w-full flex-col flex h-full"
    >
      {/* Top Bar */}
      <div className="flex flex-wrap items-center justify-between mb-8 gap-4">
        <div className="flex items-center gap-4">
          <button onClick={onReset} className="p-2 hover:bg-card rounded-full transition-colors text-gray-400 hover:text-white">
            <ArrowLeft size={24} />
          </button>
          <div>
            <h2 className="text-2xl font-bold">Analysis Results</h2>
            <p className="text-xs text-gray-500 mt-0.5">
              Modality: <span className="text-accent font-medium">{data.modality.replace('_', ' ').toUpperCase()}</span>
              <span className="ml-3 text-primary">
                {data.model_status === 'success'
                  ? 'Multi-model confidence pipeline active'
                  : 'Adaptive analysis pipeline active'}
              </span>
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button className="glass-card hover:bg-primary/20 px-4 py-2 flex items-center gap-2 text-sm font-medium transition-colors cursor-pointer rounded-xl" onClick={onReset}>
            <RotateCcw size={16} /> New Scan
          </button>
          <button
            onClick={handleDownload}
            disabled={!report}
            className={`glass-button py-2 text-sm ${!report ? 'opacity-40 cursor-not-allowed' : ''}`}
          >
            <Download size={16} className="mr-2" /> Download PDF Report
          </button>
        </div>
      </div>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 content-start">
        <div className="lg:col-span-3 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-1 rounded-2xl overflow-hidden glass-card aspect-square">
              {file.type.startsWith('image/') ? (
                <img src={URL.createObjectURL(file)} alt="Uploaded Scan" className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-card text-gray-500">CSV Signal Data</div>
              )}
            </div>
            <div className="md:col-span-2 flex">
              <PredictionCard
                prediction={data.prediction}
                modelStatus={data.model_status}
              />
            </div>
          </div>

          {data.models?.length > 0 && (
            <div className="glass-card p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold">Model Comparison</h3>
                  <p className="text-xs text-gray-500">Agreement score: {data.agreement_score?.toFixed(2) ?? '0.00'}</p>
                </div>
                {new Set(data.models.map((m) => m.label)).size > 1 && (
                  <span className="text-xs px-2 py-1 rounded-full border border-danger/30 bg-danger/10 text-danger">
                    Models disagree — review carefully
                  </span>
                )}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {data.models.map((m, i) => (
                  <div key={i} className="rounded-xl border border-cardBorder bg-black/30 p-4">
                    <h4 className="text-sm font-semibold text-gray-200">{m.model}</h4>
                    <p className="text-sm text-gray-400 mt-1">{m.label}</p>
                    <p className="text-xs text-gray-500 mt-2">Confidence: {(m.confidence * 100).toFixed(1)}%</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <ExplainabilityPanel
            file={file}
            overlayUrl={data.overlay}
            gradcamUrl={data.explainability?.gradcam ?? null}
            gradcamGifUrl={data.explainability?.gif ?? null}
            perModelGradcam={data.explainability?.per_model ?? []}
            modality={data.modality}
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <GeminiExplanation
              report={data.gemini.report}
              source={data.gemini.source}
              raw={data.gemini.raw}
            />
            <QuickSummary
              summary={data.gemini.summary}
              risk={data.gemini.risk_level}
            />
          </div>
        </div>

        <div className="lg:col-span-1 h-full">
          <HistoryPanel currentFile={file.name} modality={data.modality} risk={data.gemini.risk_level} />
        </div>
      </div>
    </motion.div>
  );
}
