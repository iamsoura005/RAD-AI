import { motion } from 'framer-motion';
import { ArrowRight, Activity, Cpu, ScanSearch } from 'lucide-react';

export default function LandingPage({ onStart }: { onStart: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] text-center w-full">
      
      {/* Small top badge */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 text-primary text-sm font-medium mb-8"
      >
        <Activity size={16} />
        <span>Next-Gen Medical Diagnostics</span>
      </motion.div>

      {/* Main Heading */}
      <motion.h1 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-5xl md:text-7xl font-bold tracking-tight mb-6 bg-gradient-to-r from-gray-100 to-gray-400 bg-clip-text text-transparent"
      >
        AI-Powered Radiology<br/>Assistant
      </motion.h1>

      <motion.p 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="text-lg md:text-xl text-gray-400 max-w-2xl mb-12"
      >
        Upload medical images or signals and get instant, highly accurate ML predictions, deep explainability mapping, and human-readable Gemini AI insights.
      </motion.p>
      
      {/* Call to action */}
      <motion.button 
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.4 }}
        onClick={onStart}
        className="glass-button text-lg gap-3"
      >
        <span>Analyze Now</span>
        <ArrowRight size={20} />
      </motion.button>
      
      {/* Features Grid below */}
      <motion.div 
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.6 }}
        className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-24 w-full max-w-4xl"
      >
        {[
          { icon: <Cpu />, title: "Precision ML", desc: "High confidence predictions trained on vast medical datasets." },
          { icon: <ScanSearch />, title: "Visual Explainability", desc: "Interactive heatmaps over images indicating decision points." },
          { icon: <Activity />, title: "Gemini Insights", desc: "Plain-text AI diagnosis summaries for clarity and patient reports." },
        ].map((feat, i) => (
          <div key={i} className="glass-card p-6 flex flex-col items-center text-center">
            <div className="w-12 h-12 rounded-full bg-primary/10 text-primary flex items-center justify-center mb-4">
              {feat.icon}
            </div>
            <h3 className="text-xl font-semibold mb-2">{feat.title}</h3>
            <p className="text-gray-400 text-sm">{feat.desc}</p>
          </div>
        ))}
      </motion.div>

    </div>
  );
}
