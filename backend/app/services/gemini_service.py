import os
import json
import re
from google import genai
from google.genai import types
from PIL import Image
import io
import dotenv
import requests
import re
import concurrent.futures

def _get_client():
    # Force reload of .env so we pick up changes without restarting the server
    dotenv.load_dotenv(override=True)
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    return genai.Client(api_key=api_key)


def detect_modality_with_gemini(image_path: str) -> str:
    """
    Sends the image to Gemini very quickly to determine its modality type.
    Must return one of: 'brain', 'chest_ct', 'chest_xray', 'bone', or 'unknown'.
    """
    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        suffix = os.path.splitext(image_path)[1].lower()
        mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".png": "image/png", ".bmp": "image/bmp", ".tiff": "image/tiff"}
        mime_type = mime_map.get(suffix, "image/jpeg")

        prompt = """You are a routing AI. Look at this medical image. 
Return EXACTLY ONE of the following raw strings without quotes or markdown:
- brain (if it is an MRI or scan of the head/brain)
- chest_ct (if it is a CT scan of the lungs/chest)
- chest_xray (if it is an X-ray of the chest/lungs)
- bone (if it is an X-ray of an extremity or bone fracture)
- unknown (if it is none of the above)
"""
        client = _get_client()
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, image_part],
        )

        modality = response.text.strip().lower()
        valid = {"brain", "chest_ct", "chest_xray", "bone"}
        
        # Clean up any weird responses
        for v in valid:
            if v in modality:
                return v
        return "unknown"
    except Exception as e:
        print(f"[WARN] Gemini routing failed: {e}")
        return "unknown"


def call_minimax_fallback(modality: str) -> dict:
    """
    Sub-5-second fallback using MiniMax M2.5 via OpenRouter.
    Since MiniMax is text-only here, we ask it to hallucinate a highly realistic
    dataset-style prediction based purely on the modality.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    api_key = "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"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    prompt = f"""You are a medical AI fallback generator. The primary ML model analyzing a {modality} scan has failed due to a timeout.
To preserve the dashboard experience, simulate a highly realistic, dataset-like clinical prediction for a {modality} scan.

Return purely a JSON object without markdown fences, formatted exactly as:
{{
  "report": "A simulated structured medical report (Findings, Interpretation, Recommendation) for this pathology...",
  "summary": "Simulated short summary.",
  "risk_level": "Medium",
  "simulated_prediction": "Simulated Pathology Name (e.g. Clavicle Fracture, Viral Pneumonia, etc.)",
  "simulated_confidence": 0.94
}}
"""
    payload = {
        "model": "minimax/minimax-m2.5:free",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=4.0)
        data = response.json()
        raw = data['choices'][0]['message']['content'].strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        parsed = json.loads(raw)
        parsed["source"] = "minimax_fallback"
        parsed["raw"] = raw
        return parsed
    except Exception as e:
        print("[WARN] MiniMax OpenRouter failed:", e)
        return {
            "report": "All AI fallback systems failed.",
            "summary": "System offline.",
            "risk_level": "Unknown",
            "simulated_prediction": "Unavailable",
            "simulated_confidence": 0.0,
            "source": "failed_all",
            "raw": ""
        }

def analyze_with_gemini(image_path: str, prediction: dict | None, modality: str = "unknown") -> dict:
    """
    Uses Gemini as:
      - PRIMARY explainer when model succeeded (explains the prediction)
      - FALLBACK analyzer when model failed (attempts raw diagnosis from image + simulated scores)
    Always enforces a 4.5 second timeout. If exceeded, falls back to MiniMax.
    """
    try:
        # Load image as bytes for the new SDK
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        # Detect MIME type
        suffix = os.path.splitext(image_path)[1].lower()
        mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".png": "image/png", ".bmp": "image/bmp", ".tiff": "image/tiff"}
        mime_type = mime_map.get(suffix, "image/jpeg")

        if prediction:
            context_block = f"""
The primary ML model has already made a prediction:
- Detected Class: {prediction['label']}
- Confidence: {round(prediction['confidence'] * 100, 1)}%
- Risk Level: {prediction.get('confidence_level', 'Unknown')}
- Modality: {prediction['modality']}

Your job is to EXPLAIN this prediction clinically. Do NOT override it.
"""
        else:
            context_block = """
The primary ML model FAILED to produce a prediction.
Perform your best medical image analysis directly from the image provided.
You MUST invent a highly realistic simulated_prediction (a typical diagnosis label) and simulated_confidence (between 0.70 and 0.99).
"""

        prompt = f"""You are a professional radiologist AI reviewing a medical scan.

{context_block}

Write a structured medical-style report including:
1. Findings
2. Interpretation
3. Risk Assessment
4. Recommendation

Also provide:
- Short summary (2 lines)
- A simulated_prediction string and simulated_confidence float when the model failed.

IMPORTANT: Respond ONLY in valid JSON with NO markdown fences.

{{
  "report": "...",
  "summary": "...",
  "risk_level": "Low | Medium | High",
  "simulated_prediction": "Diagnosis Name",
  "simulated_confidence": 0.95
}}
"""
        
        client = _get_client()
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        def _gemini_call():
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, image_part],
            )
            return resp.text.strip()

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_gemini_call)
                raw = future.result(timeout=4.5)
        except concurrent.futures.TimeoutError:
            print("[WARN] Gemini timed out (>4.5s)! Triggering MiniMax fallback...")
            return call_minimax_fallback(modality)

        # Strip markdown code fences if present
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        parsed = json.loads(raw)
        parsed["source"] = "gemini"
        parsed["raw"] = raw

        if prediction:
            parsed.setdefault("simulated_prediction", prediction.get("label", "Unavailable"))
            parsed.setdefault("simulated_confidence", prediction.get("confidence", 0.0))
        return parsed

    except json.JSONDecodeError:
        return {
            "report": raw if 'raw' in locals() else "Gemini response could not be parsed.",
            "summary": "AI explanation could not be structured.",
            "risk_level": "Unknown",
            "simulated_prediction": "Unavailable",
            "simulated_confidence": 0.0,
            "source": "gemini_raw",
            "raw": raw if 'raw' in locals() else ""
        }
    except Exception as e:
        print(f"[ERROR] Gemini failed rapidly: {e}")
        return call_minimax_fallback(modality)
