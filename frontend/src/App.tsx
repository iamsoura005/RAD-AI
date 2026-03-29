import { useState } from 'react';
import LandingPage from './components/LandingPage';
import UploadArea from './components/UploadArea';
import ProcessingScreen from './components/ProcessingScreen';
import Dashboard from './components/Dashboard';

export type AppState = 'landing' | 'uploading' | 'processing' | 'dashboard';

function App() {
  const [appState, setAppState] = useState<AppState>('landing');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleStartAnalysis = () => {
    setAppState('uploading');
  };

  const handleUploadComplete = (file: File) => {
    setSelectedFile(file);
    setAppState('dashboard');
  };

  const handleProcessingComplete = () => {
    setAppState('dashboard');
  };

  return (
    <div className="min-h-screen bg-background relative overflow-x-hidden selection:bg-primary/30 text-gray-100 flex flex-col">
      {/* Background ambient light effects */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-primary/20 blur-[120px] pointer-events-none" />
      <div className="absolute top-[40%] right-[-10%] w-[30%] h-[30%] rounded-full bg-accent/10 blur-[120px] pointer-events-none" />
      
      <main className="flex-1 w-full max-w-7xl mx-auto p-4 md:p-8 relative z-10 flex flex-col">
        {appState === 'landing' && <LandingPage onStart={handleStartAnalysis} />}
        {appState === 'uploading' && <UploadArea onUpload={handleUploadComplete} />}
        {appState === 'processing' && selectedFile && (
          <ProcessingScreen file={selectedFile} onComplete={handleProcessingComplete} />
        )}
        {appState === 'dashboard' && selectedFile && (
          <Dashboard file={selectedFile} onReset={() => {
            setSelectedFile(null);
            setAppState('landing');
          }} />
        )}
      </main>
    </div>
  );
}

export default App;
