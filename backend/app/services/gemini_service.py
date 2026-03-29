import concurrent.futures
import json
import os
import re

import dotenv
import requests
from google import genai
from google.genai import types


def _env_flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _explain_timeout_sec() -> float:
    try:
        return float(os.getenv("GEMINI_TIMEOUT_SEC", "2.5"))
    except ValueError:
        return 2.5


def _get_gemini_api_key() -> str:
    dotenv.load_dotenv(override=True)
    return os.getenv("GEMINI_API_KEY", "").strip()


def _has_usable_gemini_key() -> bool:
    key = _get_gemini_api_key()
    if not key:
        return False
    blocked_prefixes = ("your_", "replace_", "example", "xxxx", "test")
    lowered = key.lower()
    return not any(lowered.startswith(p) for p in blocked_prefixes) and len(key) > 20


def _risk_from_confidence(confidence: float) -> str:
    if confidence >= 0.85:
        return "High"
    if confidence >= 0.6:
        return "Medium"
    if confidence > 0:
        return "Low"
    return "Unknown"


def _model_based_explanation(modality: str, prediction: dict, reason: str = "model_explainer") -> dict:
    label = str(prediction.get("label", "Unavailable"))
    confidence = float(prediction.get("confidence", 0.0))
    risk = _risk_from_confidence(confidence)
    conf_pct = round(confidence * 100, 1)

    return {
        "report": (
            f"Model-driven analysis for {modality}: the ensemble selected '{label}' with {conf_pct}% confidence. "
            "This summary is derived directly from trained model outputs. "
            "Please correlate with full clinical context and radiologist interpretation."
        ),
        "summary": f"Model result: {label} ({conf_pct}% confidence).",
        "risk_level": risk,
        "source": reason,
        "raw": "",
    }


def _analysis_unavailable(reason: str = "analysis_unavailable") -> dict:
    return {
        "report": (
            "Validated model prediction is unavailable and remote explanation services could not be reached. "
            "Please retry after confirming model status and API keys."
        ),
        "summary": "No validated diagnosis available.",
        "risk_level": "Unknown",
        "source": reason,
        "raw": "",
    }


def _get_client():
    api_key = _get_gemini_api_key()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is missing")
    return genai.Client(api_key=api_key)


def detect_modality_with_gemini(image_path: str) -> str:
    """
    Sends the image to Gemini quickly to determine modality type.
    Returns one of: 'brain', 'chest_ct', 'chest_xray', 'bone', or 'unknown'.
    """
    if not _has_usable_gemini_key():
        return "unknown"

    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        suffix = os.path.splitext(image_path)[1].lower()
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".bmp": "image/bmp",
            ".tiff": "image/tiff",
        }
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

        modality = (response.text or "").strip().lower()
        valid = {"brain", "chest_ct", "chest_xray", "bone"}
        for value in valid:
            if value in modality:
                return value
        return "unknown"
    except Exception as e:
        print(f"[WARN] Gemini routing failed: {e}")
        return "unknown"


def call_minimax_fallback(modality: str) -> dict:
    """
    Optional text fallback via OpenRouter. Disabled by default because mock
    diagnoses are not desired in production.
    """
    if not _env_flag("ENABLE_OPENROUTER_FALLBACK", "false"):
        return _analysis_unavailable("analysis_unavailable")

    dotenv.load_dotenv(override=True)
    url = "https://openrouter.ai/api/v1/chat/completions"
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        return _analysis_unavailable("analysis_unavailable")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    prompt = f"""You are assisting with a medical workflow for modality {modality}.
The primary ML model prediction is unavailable. Do not invent a diagnosis label.

Return valid JSON (no markdown) with this schema:
{{
  "report": "Brief operational note and recommendation to retry/verify model status.",
  "summary": "Short status summary.",
  "risk_level": "Unknown"
}}
"""

    payload = {
        "model": "minimax/minimax-m2.5:free",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=4.0)
        if response.status_code >= 400:
            print(f"[WARN] MiniMax/OpenRouter HTTP {response.status_code}: {response.text[:200]}")
            return _analysis_unavailable("analysis_unavailable")

        data = response.json()
        choices = data.get("choices", []) if isinstance(data, dict) else []
        if not choices:
            return _analysis_unavailable("analysis_unavailable")

        raw = choices[0].get("message", {}).get("content", "").strip()
        if not raw:
            return _analysis_unavailable("analysis_unavailable")

        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        parsed = json.loads(raw)
        parsed.setdefault("report", "AI fallback unavailable.")
        parsed.setdefault("summary", "No validated diagnosis available.")
        parsed.setdefault("risk_level", "Unknown")
        parsed["source"] = "minimax_fallback"
        parsed["raw"] = raw
        return parsed
    except Exception as e:
        print("[WARN] MiniMax OpenRouter failed:", e)
        return _analysis_unavailable("analysis_unavailable")


def analyze_with_gemini(image_path: str, prediction: dict | None, modality: str = "unknown") -> dict:
    """
    Fast-path behavior:
      - If model prediction exists, return model-based explanation immediately.
      - Optional remote Gemini explanation can be enabled with ENABLE_REMOTE_EXPLANATION=true.
      - If no model prediction, do not invent diagnosis labels.
    """
    if prediction is not None and not _env_flag("ENABLE_REMOTE_EXPLANATION", "false"):
        return _model_based_explanation(modality, prediction)

    if not _has_usable_gemini_key():
        if prediction is not None:
            return _model_based_explanation(modality, prediction)
        return call_minimax_fallback(modality)

    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        suffix = os.path.splitext(image_path)[1].lower()
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".bmp": "image/bmp",
            ".tiff": "image/tiff",
        }
        mime_type = mime_map.get(suffix, "image/jpeg")

        if prediction:
            context_block = f"""
The primary ML model has already made a prediction:
- Detected Class: {prediction['label']}
- Confidence: {round(float(prediction['confidence']) * 100, 1)}%
- Modality: {modality}

Explain this prediction clinically. Do NOT override it.
"""
        else:
            context_block = """
The primary ML model failed to produce a validated prediction.
Do not invent diagnosis labels. Provide operational guidance only.
"""

        prompt = f"""You are a professional radiology assistant.

{context_block}

Return only valid JSON with this schema:
{{
  "report": "...",
  "summary": "...",
  "risk_level": "Low | Medium | High | Unknown"
}}
"""

        client = _get_client()
        image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        def _gemini_call() -> str:
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt, image_part],
            )
            return (resp.text or "").strip()

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_gemini_call)
                raw = future.result(timeout=_explain_timeout_sec())
        except concurrent.futures.TimeoutError:
            print("[WARN] Gemini timed out; using local explanation.")
            if prediction is not None:
                return _model_based_explanation(modality, prediction, reason="model_explainer_timeout")
            return call_minimax_fallback(modality)

        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        parsed = json.loads(raw)
        parsed.setdefault("report", "AI explanation unavailable.")
        parsed.setdefault("summary", "No summary available.")
        parsed.setdefault("risk_level", "Unknown")
        parsed["source"] = "gemini"
        parsed["raw"] = raw
        return parsed

    except json.JSONDecodeError:
        if prediction is not None:
            return _model_based_explanation(modality, prediction, reason="model_explainer_parse_fallback")
        return call_minimax_fallback(modality)
    except Exception as e:
        print(f"[ERROR] Gemini failed rapidly: {e}")
        if prediction is not None:
            return _model_based_explanation(modality, prediction, reason="model_explainer_error")
        return call_minimax_fallback(modality)
