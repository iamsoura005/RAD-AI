import { AlignLeft, Sparkles, AlertCircle } from 'lucide-react';

interface Props {
  report: string;
  source: string;
  raw: string;
}

export default function GeminiExplanation({ report, source, raw }: Props) {
  const isFallback = source === 'failed_all';
  const displayText = report || raw || "AI report unavailable.";

  return (
    <div className="glass-card p-6 w-full flex flex-col h-full border-t-2 border-t-accent hover:border-t-primary transition-colors">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Sparkles className="text-accent" size={20} />
          <h3 className="font-bold text-lg">
            {isFallback ? 'AI Explanation (Unavailable)' : 'AI Explanation'}
          </h3>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full border font-medium ${
          source === 'gemini' ? 'text-accent border-accent/30 bg-accent/10' :
          source === 'gemini_raw' ? 'text-warning border-warning/30 bg-warning/10' :
          source === 'minimax_fallback' ? 'text-primary border-primary/30 bg-primary/10' :
          'text-gray-500 border-gray-600 bg-gray-800'
        }`}>
          {source === 'gemini' ? 'Gemini' :
           source === 'gemini_raw' ? 'Gemini (raw)' :
           source === 'minimax_fallback' ? 'MiniMax' :
           'Unavailable'}
        </span>
      </div>

      {isFallback ? (
        <div className="flex items-center gap-3 text-warning bg-warning/10 p-4 rounded-xl border border-warning/20">
          <AlertCircle size={20} />
          <p className="text-sm">AI explanation service is currently unavailable. The ML model result stands.</p>
        </div>
      ) : (
        <>
          <div className="flex gap-3 mb-5">
            <AlignLeft className="text-gray-500 flex-shrink-0 mt-1" size={16} />
            <p className="text-gray-300 leading-relaxed text-sm">{displayText}</p>
          </div>

          <div className="mt-auto bg-cardBorder/60 rounded-xl p-4">
            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Source</h4>
            <p className="text-xs text-gray-400">{source}</p>
          </div>
        </>
      )}
    </div>
  );
}
