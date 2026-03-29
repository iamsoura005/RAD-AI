import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Scan, DatabaseZap, FileText, CheckCircle2 } from 'lucide-react';

const STEPS = [
  { id: 1, text: "Detecting modality...", icon: <Scan className="w-5 h-5" /> },
  { id: 2, text: "Running core ML model...", icon: <DatabaseZap className="w-5 h-5" /> },
  { id: 3, text: "Generating explainability heatmaps...", icon: <Scan className="w-5 h-5" /> },
  { id: 4, text: "Fetching Gemini AI report...", icon: <FileText className="w-5 h-5" /> }
];

export default function ProcessingScreen({ 
  file, 
  onComplete 
}: { 
  file: File;
  onComplete: () => void;
}) {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    // Simulate steps timing (API takes ~4s)
    const timers = [
      setTimeout(() => setCurrentStep(1), 800),
      setTimeout(() => setCurrentStep(2), 1800),
      setTimeout(() => setCurrentStep(3), 2800),
      setTimeout(() => setCurrentStep(4), 3800),
      setTimeout(() => onComplete(), 4500)
    ];
    return () => timers.forEach(clearTimeout);
  }, [onComplete]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] w-full max-w-lg mx-auto">
      
      {/* Scanning effect box */}
      <div className="relative w-48 h-48 mb-12 glass-card overflow-hidden flex items-center justify-center">
        {file.type.startsWith('image/') ? (
          <img 
            src={URL.createObjectURL(file)} 
            alt="Upload Preview" 
            className="w-full h-full object-cover opacity-50 grayscale blur-[1px]" 
          />
        ) : (
          <FileText className="w-20 h-20 text-gray-500" />
        )}
        
        {/* Animated scanner line */}
        <motion.div 
          className="absolute top-0 left-0 right-0 h-1 bg-primary shadow-[0_0_15px_3px_rgba(79,70,229,0.8)] z-10"
          animate={{ y: [0, 192, 0] }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        />
        
        <div className="absolute inset-0 bg-primary/10 mix-blend-overlay z-0" />
      </div>

      {/* Dynamic Status List */}
      <div className="w-full space-y-4">
        {STEPS.map((step, index) => {
          const isActive = index === currentStep;
          const isDone = index < currentStep;
          
          return (
            <motion.div 
              key={step.id}
              initial={{ opacity: 0, x: -20 }}
              animate={(isActive || isDone) ? { opacity: 1, x: 0 } : { opacity: 0.3, x: 0 }}
              className={`flex items-center gap-4 p-4 rounded-xl border ${
                isActive ? 'bg-primary/10 border-primary/30 text-primary' : 
                isDone ? 'bg-success/5 border-success/20 text-success' : 
                'bg-card border-cardBorder text-gray-500'
              }`}
            >
              <div className="flex-shrink-0">
                {isDone ? <CheckCircle2 className="w-5 h-5 text-success" /> : step.icon}
              </div>
              <span className={`font-medium ${isActive ? 'animate-pulse' : ''}`}>
                {step.text}
              </span>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
