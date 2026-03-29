import { Zap } from 'lucide-react';

export default function QuickSummary({
  summary,
  risk
}: {
  summary: string;
  risk: "Low" | "Medium" | "High" | "Unknown";
}) {
  const cleanedSummary = (summary || "").replace(/^fallback summary:\s*/i, "").trim() || "Analysis summary not available.";
  const riskTone =
    risk === "High" ? "text-danger border-danger/30 bg-danger/10" :
    risk === "Medium" ? "text-warning border-warning/30 bg-warning/10" :
    risk === "Low" ? "text-success border-success/30 bg-success/10" :
    "text-gray-400 border-gray-500/30 bg-gray-500/10";
  return (
    <div className="rounded-2xl w-full h-full p-[1px] bg-gradient-to-br from-primary via-accent to-purple-600 shadow-[0_0_20px_0_rgba(79,70,229,0.3)]">
      <div className="bg-card w-full h-full rounded-[15px] p-6 flex flex-col items-center justify-center text-center relative overflow-hidden">
        
        <div className="absolute top-0 right-0 w-32 h-32 bg-primary/20 blur-3xl -translate-y-1/2 translate-x-1/2 rounded-full" />
        
        <Zap className="text-accent w-10 h-10 mb-4 drop-shadow-[0_0_8px_rgba(6,182,212,0.8)]" />
        
        <div className="flex items-center gap-2 mb-3">
          <h3 className="text-xl font-bold">Quick Summary</h3>
          <span className={`text-xs px-2 py-1 rounded-full border font-semibold ${riskTone}`}>
            {risk}
          </span>
        </div>
        <p className="text-gray-300 font-medium leading-base text-lg">
          {cleanedSummary}
        </p>
        
      </div>
    </div>
  );
}
