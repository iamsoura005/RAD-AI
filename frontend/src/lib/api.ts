const rawApiUrl = (import.meta.env.VITE_API_URL as string | undefined)?.trim();
const normalizedApiBase = (rawApiUrl && rawApiUrl.length > 0 ? rawApiUrl : "http://localhost:8000")
  .replace(/\/+$/, "")
  .replace(/\/api$/i, "");

const BASE_URL = `${normalizedApiBase}/api`;

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
    const errJson = await res.json().catch(() => null);
    const errText = await res.text().catch(() => "");
    const detail = errJson?.detail || errText || `Server error: ${res.status}`;
    throw new Error(`${detail} (endpoint: ${BASE_URL}/analyze)`);
  }

  return res.json();
};
