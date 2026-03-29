const BASE_URL = `${import.meta.env.VITE_API_URL ?? "http://localhost:8000"}/api`;

export interface GeminiResult {
  report: string;
  summary: string;
  risk_level: "Low" | "Medium" | "High" | "Unknown";
  source: string;
  raw: string;
}

export interface PredictionPayload {
  label: string;
  label_index: number;
  confidence: number;
  confidence_level: "Low" | "Medium" | "High" | "Unknown";
  modality: string;
  class_probabilities: Record<string, number>;
  status: string;
}

export interface AnalyzeResponse {
  prediction: PredictionPayload | null;
  modality: string;
  model_status: "success" | "failed_fallback_to_gemini";
  overlay: string | null;
  models: Array<{
    model: string;
    label: string;
    confidence: number;
  }>;
  agreement_score?: number;
  explainability?: {
    gradcam: string | null;
    ensemble_gradcam?: string | null;
    gif: string | null;
    segmentation: string | null;
    per_model?: Array<{
      model: string;
      image: string;
    }>;
  };
  gemini: GeminiResult;
}

export interface ApiResponse {
  data: AnalyzeResponse;
  report: string | null;
}

export const analyzeImage = async (file: File): Promise<ApiResponse> => {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${BASE_URL}/analyze`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Server error: ${res.status}`);
  }

  return res.json();
};
