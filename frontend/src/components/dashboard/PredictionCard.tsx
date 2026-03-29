import { motion } from 'framer-motion';
import { Activity, ShieldAlert, ShieldCheck, AlertTriangle, Cpu } from 'lucide-react';

interface PredictionPayload {
  label: string;
  confidence: number;
  confidence_level?: string;
  class_probabilities?: Record<string, number>;
  status?: string;
}

interface Props {
  prediction: PredictionPayload | null;
  modelStatus: string;
}

export default function PredictionCard({ prediction, modelStatus }: Props) {
  const confidence = prediction?.confidence ?? 0;
  const confidenceLevel = prediction?.confidence_level ?? "Unknown";
  const label = prediction?.label ?? "Unavailable";
  const classProbs = prediction?.class_probabilities ?? {};
  const percentage = (confidence * 100).toFixed(1);

  const riskColor =
    confidenceLevel === "High" ? "text-danger bg-danger/10 border-danger/30" :
    confidenceLevel === "Medium" ? "text-warning bg-warning/10 border-warning/30" :
    confidenceLevel === "Low" ? "text-success bg-success/10 border-success/30" :
    "text-gray-400 bg-gray-500/10 border-gray-500/30";

  const RiskIcon = confidenceLevel === "High" ? ShieldAlert : confidenceLevel === "Medium" ? AlertTriangle : ShieldCheck;

  const barColor =
    confidence > 0.85 ? 'bg-primary' :
    confidence > 0.65 ? 'bg-warning' : 'bg-danger';

  const topClasses = Object.entries(classProbs)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4);

  return (
    <div className="glass-card w-full h-full p-6 flex flex-col gap-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-gray-400 font-medium mb-1 flex items-center gap-2 text-sm">
            <Cpu size={14} />
            {modelStatus === 'success' ? 'ML Model Prediction' : 'Gemini Fallback'}
          </p>
          <h3 className="text-3xl font-bold bg-gradient-to-r from-gray-100 to-gray-400 bg-clip-text text-transparent">
            {label}
          </h3>
        </div>
        <div className={`px-3 py-1.5 rounded-full border flex items-center gap-1.5 font-semibold text-sm ${riskColor}`}>
          <RiskIcon size={16} />
          {confidenceLevel}
        </div>
      </div>

      {/* Confidence bar */}
      <div className="space-y-2">
        <div className="flex justify-between items-end">
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Confidence</span>
          <span className="text-2xl font-bold">{percentage}%</span>
        </div>
        <div className="h-2.5 w-full bg-cardBorder rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${percentage}%` }}
            transition={{ duration: 1, ease: 'easeOut', delay: 0.2 }}
            className={`h-full ${barColor} rounded-full`}
          />
        </div>
      </div>

      {/* Class probability breakdown */}
      {topClasses.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-gray-500 uppercase tracking-wider font-medium">All Classes</p>
          {topClasses.map(([name, prob]) => (
            <div key={name} className="flex items-center gap-2">
              <span className="text-xs text-gray-400 w-28 truncate">{name}</span>
              <div className="flex-1 h-1.5 bg-cardBorder rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${(prob * 100).toFixed(1)}%` }}
                  transition={{ duration: 0.8, ease: 'easeOut', delay: 0.4 }}
                  className="h-full bg-primary/50 rounded-full"
                />
              </div>
              <span className="text-xs text-gray-500 w-10 text-right">{(prob * 100).toFixed(1)}%</span>
            </div>
          ))}
        </div>
      )}

      <div className="flex items-center gap-2 mt-auto">
        <Activity size={13} className="text-gray-600" />
        <span className="text-xs text-gray-600">
          {modelStatus === 'success' ? 'Prediction from .h5 model' : 'ML model unavailable — Gemini used'}
        </span>
      </div>
    </div>
  );
}
