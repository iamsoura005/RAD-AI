import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion, AnimatePresence } from 'framer-motion';
import { UploadCloud, FileImage, FileWarning } from 'lucide-react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export default function UploadArea({ onUpload }: { onUpload: (file: File) => void }) {
  const [errorDetails, setErrorDetails] = useState('');

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    if (rejectedFiles.length > 0) {
      setErrorDetails("Invalid file format or file too large");
      setTimeout(() => setErrorDetails(''), 4000);
      return;
    }
    
    if (acceptedFiles.length > 0) {
      // Small fake delay to simulate reading blob
      setTimeout(() => {
        onUpload(acceptedFiles[0]);
      }, 800);
    }
  }, [onUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: {
      'image/jpeg': [],
      'image/png': [],
      'text/csv': []
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024 // 50MB
  });

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] w-full max-w-2xl mx-auto">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="text-center mb-8"
      >
        <h2 className="text-3xl font-semibold mb-3">Upload Medical Data</h2>
        <p className="text-gray-400">Drag and drop your scan (PNG, JPG) or signal data (CSV)</p>
      </motion.div>
      
      <div 
        {...getRootProps()} 
        className={twMerge(
          clsx(
            "w-full glass-card border-2 border-dashed p-16 flex flex-col items-center justify-center cursor-pointer transition-all duration-300 relative overflow-hidden",
            isDragActive ? "border-primary bg-primary/5 scale-105" : "border-cardBorder hover:border-primary/50"
          )
        )}
      >
        <input {...getInputProps()} />
        
        {/* Pulse effect when dragging */}
        {isDragActive && (
          <motion.div 
            className="absolute inset-0 bg-primary/10"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          />
        )}
        
        <motion.div 
          animate={isDragActive ? { y: -10, scale: 1.1 } : { y: 0, scale: 1 }}
          className="mb-6 relative"
        >
          {isDragActive ? (
            <UploadCloud className="w-20 h-20 text-primary animate-pulse" />
          ) : (
            <div className="relative">
              <UploadCloud className="w-20 h-20 text-gray-500" />
              <FileImage className="w-8 h-8 text-primary absolute -bottom-2 -right-2 bg-background rounded-full p-1" />
            </div>
          )}
        </motion.div>
        
        <p className="text-xl font-medium mb-2 text-gray-200">
          {isDragActive ? "Drop to analyze..." : "Select file or drag here"}
        </p>
        <p className="text-sm text-gray-500 font-medium">
          Supports JPG, PNG, CSV up to 50MB
        </p>
      </div>

      <AnimatePresence>
        {errorDetails && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            className="mt-6 flex items-center gap-2 text-danger bg-danger/10 px-4 py-3 rounded-xl border border-danger/20"
          >
            <FileWarning size={20} />
            <span>{errorDetails}</span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
