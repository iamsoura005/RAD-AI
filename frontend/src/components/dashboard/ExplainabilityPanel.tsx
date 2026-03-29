import { useState } from 'react';
import { motion } from 'framer-motion';
import { Layers } from 'lucide-react';

export default function ExplainabilityPanel({
  file,
  overlayUrl,
  gradcamUrl,
  gradcamGifUrl,
  perModelGradcam,
  modality
}: {
  file: File,
  overlayUrl?: string | null,
  gradcamUrl?: string | null,
  gradcamGifUrl?: string | null,
  perModelGradcam?: Array<{ model: string; image: string }>;
  modality?: string
}) {
  const [showOverlay, setShowOverlay] = useState(false);
  const [alpha, setAlpha] = useState(0.4);
  const [overlayMode, setOverlayMode] = useState<'gradcam' | 'segmentation'>('gradcam');
  
  // URL Object for image preview
  const imageUrl = file.type.startsWith('image/') ? URL.createObjectURL(file) : null;
  const overlaySrc = overlayUrl ? `http://localhost:8000${overlayUrl}` : null;
  const gradcamSrc = gradcamUrl ? `http://localhost:8000${gradcamUrl}` : null;
  const gradcamGifSrc = gradcamGifUrl ? `http://localhost:8000${gradcamGifUrl}` : null;
  const showSegmentationUnavailable = showOverlay && overlayMode === 'segmentation' && !overlaySrc && modality === "brain";
  const showGradcamUnavailable = showOverlay && overlayMode === 'gradcam' && !gradcamSrc;

  return (
    <div className="glass-card p-6 w-full flex flex-col gap-4">
      
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-lg flex items-center gap-2">
          <Layers className="text-primary w-5 h-5" /> Visual Explainability
        </h3>
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setOverlayMode('gradcam')}
            className={`px-3 py-1 rounded-full text-xs font-semibold border ${overlayMode === 'gradcam' ? 'bg-primary/20 text-primary border-primary/40' : 'border-cardBorder text-gray-400'}`}
          >
            Grad-CAM
          </button>
          <button
            type="button"
            onClick={() => setOverlayMode('segmentation')}
            className={`px-3 py-1 rounded-full text-xs font-semibold border ${overlayMode === 'segmentation' ? 'bg-primary/20 text-primary border-primary/40' : 'border-cardBorder text-gray-400'}`}
          >
            Segmentation
          </button>
        </div>
        <label className="flex items-center gap-3 cursor-pointer text-sm font-medium">
          <span className={showOverlay ? 'text-gray-400' : 'text-gray-100'}>Original</span>
          <div className="relative inline-block w-12 mr-2 align-middle select-none transition duration-200 ease-in">
            <input 
              type="checkbox" 
              name="toggle" 
              id="toggle" 
              className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer border-cardBorder focus:outline-none transition-transform duration-200"
              style={{ transform: showOverlay ? 'translateX(100%)' : 'translateX(0)' }}
              checked={showOverlay}
              onChange={() => setShowOverlay(!showOverlay)}
            />
            <label 
              htmlFor="toggle" 
              className={`toggle-label block overflow-hidden h-6 rounded-full cursor-pointer duration-200 ${showOverlay ? 'bg-primary' : 'bg-cardBorder'}`}
            ></label>
          </div>
          <span className={showOverlay ? 'text-primary drop-shadow-[0_0_8px_rgba(79,70,229,0.8)]' : 'text-gray-400'}>Heatmap</span>
        </label>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-xl border border-cardBorder bg-black/40 p-3">
          <h4 className="text-sm font-semibold text-gray-300 mb-2">Original Image</h4>
          <div className="relative w-full aspect-video rounded-lg overflow-hidden bg-black/30 flex items-center justify-center">
            {imageUrl ? (
              <img src={imageUrl} alt="Scan" className="w-full h-full object-contain" />
            ) : (
              <div className="text-gray-500 text-center">
                <p>Signal data (CSV) selected.</p>
                <p className="text-sm">Explainability waveforms visualized here.</p>
              </div>
            )}
          </div>
        </div>

        <div className="rounded-xl border border-cardBorder bg-black/40 p-3">
          <h4 className="text-sm font-semibold text-gray-300 mb-2">
            {overlayMode === 'segmentation' ? 'AI Focus (Segmentation)' : 'AI Focus (Ensemble Grad-CAM)'}
          </h4>
          <div className="relative w-full aspect-video rounded-lg overflow-hidden bg-black/30 flex items-center justify-center">
            {imageUrl ? (
              <>
                <img src={imageUrl} alt="Scan base" className="w-full h-full object-contain" />
                {overlayMode === 'gradcam' && gradcamSrc ? (
                  <motion.img
                    initial={{ opacity: 0 }}
                    animate={{ opacity: showOverlay ? alpha : 0 }}
                    transition={{ duration: 0.3 }}
                    src={gradcamSrc}
                    alt="Ensemble Grad-CAM Heatmap"
                    className="absolute inset-0 z-10 w-full h-full object-contain"
                  />
                ) : null}

                {overlayMode === 'segmentation' && overlaySrc ? (
                  <motion.img
                    initial={{ opacity: 0 }}
                    animate={{ opacity: showOverlay ? 0.9 : 0 }}
                    transition={{ duration: 0.3 }}
                    src={overlaySrc}
                    alt="Segmentation Overlay"
                    className="absolute inset-0 z-10 w-full h-full object-contain"
                  />
                ) : null}

                {showSegmentationUnavailable && (
                  <div className="absolute inset-0 z-20 flex items-center justify-center">
                    <div className="px-4 py-2 rounded-lg bg-black/70 text-gray-200 text-sm border border-cardBorder">
                      Overlay unavailable
                    </div>
                  </div>
                )}

                {showGradcamUnavailable && (
                  <div className="absolute inset-0 z-20 flex items-center justify-center">
                    <div className="px-4 py-2 rounded-lg bg-black/70 text-gray-200 text-sm border border-cardBorder">
                      Grad-CAM unavailable
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-gray-500 text-center">
                <p>Signal data (CSV) selected.</p>
                <p className="text-sm">Explainability waveforms visualized here.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between text-xs text-gray-400">
          <span>Overlay Strength</span>
          <span>{alpha.toFixed(1)}</span>
        </div>
        <input
          type="range"
          min="0"
          max="1"
          step="0.1"
          value={alpha}
          onChange={(event) => setAlpha(Number(event.target.value))}
          className="w-full"
          disabled={overlayMode === 'segmentation'}
        />
      </div>

      <div className="rounded-xl border border-cardBorder bg-black/40 p-4">
        <h4 className="text-sm font-semibold text-gray-200">Explainability Guide</h4>
        <p className="text-xs text-gray-400 mt-1">
          The highlighted regions indicate where the model focused while making the prediction.
        </p>
        <ul className="text-xs text-gray-300 mt-3 space-y-1">
          <li>Red: High attention (critical region)</li>
          <li>Yellow: Moderate attention</li>
          <li>Blue: Low relevance</li>
        </ul>
      </div>

      {gradcamGifSrc && (
        <div className="rounded-xl border border-cardBorder bg-black/40 p-3">
          <h4 className="text-sm font-semibold text-gray-300 mb-2">AI Focus Animation</h4>
          <img src={gradcamGifSrc} alt="Grad-CAM animation" className="w-full rounded-lg" />
        </div>
      )}

      {perModelGradcam && perModelGradcam.length > 0 && (
        <div className="rounded-xl border border-cardBorder bg-black/40 p-4">
          <h4 className="text-sm font-semibold text-gray-300 mb-3">Model-wise Explainability</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {perModelGradcam.map((item) => (
              <div key={item.model} className="rounded-lg border border-cardBorder bg-black/30 p-3">
                <p className="text-xs text-gray-400 mb-2">{item.model}</p>
                <img
                  src={`http://localhost:8000${item.image}`}
                  alt={`${item.model} Grad-CAM`}
                  className="w-full rounded-md"
                />
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}
