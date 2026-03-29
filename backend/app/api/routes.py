import os
import uuid
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from PIL import Image, UnidentifiedImageError

from app.services.ensemble_service import ensemble_predict
from app.services.gemini_service import analyze_with_gemini, detect_modality_with_gemini
from app.services.gradcam_service import overlay_heatmap, create_gradcam_gif, ensemble_gradcam
from app.services.report_service import generate_report
from app.services.segmentation_service import create_overlay
from app.services.modality_classifier import predict_modality, model as modality_model, LABELS
from app.models.model_loader import get_model, get_models, get_model_status
from app.utils.confidence import calibrate_confidence
import numpy as np


def _fallback_heatmap_from_image(image_path: str) -> np.ndarray | None:
    try:
        gray = Image.open(image_path).convert("L").resize((224, 224))
        arr = np.array(gray, dtype=np.float32)
        arr -= arr.min()
        max_val = arr.max()
        if max_val > 0:
            arr /= max_val
        return arr
    except Exception:
        return None

router = APIRouter()

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
ENABLE_GRADCAM_GIF = os.getenv("ENABLE_GRADCAM_GIF", "false").strip().lower() in {"1", "true", "yes", "on"}
ENABLE_PER_MODEL_GRADCAM = os.getenv("ENABLE_PER_MODEL_GRADCAM", "false").strip().lower() in {"1", "true", "yes", "on"}


def _filename_modality_hint(filename: str) -> str:
    name = (filename or "").lower()
    token_map = {
        "bone": ["bone", "fracture", "xray", "x-ray", "humerus", "radius", "ulna", "femur", "tibia"],
        "chest_xray": ["chest", "lung", "cxr", "pneumonia", "xray", "x-ray"],
        "chest_ct": ["ct", "ctscan", "scan", "thorax"],
        "brain": ["brain", "mri", "flair", "tumor", "head"],
    }

    for modality, tokens in token_map.items():
        if any(token in name for token in tokens):
            return modality
    return "unknown"


def _best_available_model_prediction(image_path: str) -> tuple[str, dict | None]:
    candidates: list[tuple[str, dict, float]] = []
    for modality in ["brain", "chest_ct", "chest_xray", "bone"]:
        if not get_models(modality):
            continue

        result = ensemble_predict(image_path, modality)
        if not result or not result.get("ensemble"):
            continue

        conf = float(result["ensemble"].get("confidence", 0.0))
        candidates.append((modality, result, conf))

    if not candidates:
        return "unknown", None

    candidates.sort(key=lambda x: x[2], reverse=True)
    best_modality, best_result, _ = candidates[0]
    return best_modality, best_result


@router.get("/modality/status")
def modality_status():
    if modality_model is None:
        return {
            "status": "not_loaded",
            "message": "Modality model not found"
        }

    return {
        "status": "loaded",
        "classes": LABELS,
        "num_classes": len(LABELS),
        "input_shape": modality_model.input_shape
    }


@router.get("/models/status")
def models_status():
    return get_model_status()


@router.post("/analyze")
def analyze(file: UploadFile = File(...)):
    """
    Main analysis endpoint.

    Flow:
      1. Save uploaded file
    2. Auto-detect modality from image
      3. Run .h5 model  → structured prediction
      4. Pass result to Gemini for explanation (or fallback if model failed)
      5. Generate PDF report
      6. Return full structured JSON
    """
    # --- Validate file extension ---
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: {ALLOWED_EXTENSIONS}"
        )

    # --- Save upload with unique name to avoid collisions ---
    unique_name = f"{uuid.uuid4().hex}{suffix}"
    upload_path = UPLOAD_DIR / unique_name

    with open(upload_path, "wb") as buf:
        shutil.copyfileobj(file.file, buf)

    str_path = str(upload_path)

    # --- Validate image content ---
    try:
        with Image.open(str_path) as img:
            img.verify()
    except (UnidentifiedImageError, OSError) as exc:
        try:
            os.remove(str_path)
        except OSError:
            pass
        raise HTTPException(status_code=400, detail=f"Invalid or corrupt image: {exc}")

    # --- Step 1: CNN routing then Gemini fallback ---
    modality = predict_modality(str_path)

    # Filename hint fallback when modality is unknown
    if modality == "unknown":
        modality = _filename_modality_hint(file.filename or "")

    if modality == "unknown":
        modality = detect_modality_with_gemini(str_path)

    # --- Step 2: Run ensemble prediction if routing succeeded ---
    ensemble_result = None
    if modality != "unknown":
        ensemble_result = ensemble_predict(str_path, modality)

    # If routing failed or selected modality has no usable model, probe all loaded models.
    if ensemble_result is None:
        auto_modality, auto_result = _best_available_model_prediction(str_path)
        if auto_result is not None:
            modality = auto_modality
            ensemble_result = auto_result

    prediction = ensemble_result["ensemble"] if ensemble_result else None
        
    model_status = "success" if prediction else "failed_fallback_to_gemini"

    # --- Step 3: Gemini (explanation OR fallback) ---
    gemini = analyze_with_gemini(str_path, prediction, modality)

    # --- Build unified response ---
    if prediction:
        prediction_payload = {
            **prediction,
            "confidence_level": calibrate_confidence(prediction["confidence"]),
            "modality": modality,
            "status": "success"
        }
    elif gemini.get("simulated_prediction"):
        simulated_conf = float(gemini.get("simulated_confidence", 0.0))
        prediction_payload = {
            "label": gemini.get("simulated_prediction"),
            "label_index": -1,
            "confidence": simulated_conf,
            "confidence_level": calibrate_confidence(simulated_conf),
            "modality": modality,
            "class_probabilities": {},
            "status": "simulated"
        }
    else:
        prediction_payload = None

    # --- Step 4: Segmentation Overlay (Brain Tumor Fake Mask) ---
    overlay_url = None
    if modality == "brain":
        # Create a dummy segmentation mask
        mask = np.random.rand(224, 224)
        try:
            overlay_file_path = create_overlay(str_path, mask)
            overlay_url = f"/api/overlay/{os.path.basename(overlay_file_path)}"
        except Exception as e:
            print(f"[WARN] Segmentation overlay failed: {e}")

    # --- Step 5: Ensemble Grad-CAM explainability ---
    gradcam_url = None
    gradcam_gif_url = None
    per_model_gradcam = []
    models = get_models(modality) if modality != "unknown" else []
    try:
        if prediction and models:
                filename_root = os.path.splitext(os.path.basename(str_path))[0]
                output_dir = os.path.join(os.path.dirname(os.path.dirname(str_path)), "outputs")

                ensemble_path = os.path.join(output_dir, f"{filename_root}_gradcam.jpg")
                ensemble_gif_path = os.path.join(output_dir, f"{filename_root}_gradcam.gif")

                if os.path.exists(ensemble_path):
                    gradcam_url = f"/outputs/{os.path.basename(ensemble_path)}"
                if ENABLE_GRADCAM_GIF and os.path.exists(ensemble_gif_path):
                    gradcam_gif_url = f"/outputs/{os.path.basename(ensemble_gif_path)}"

                if gradcam_url is None or (ENABLE_GRADCAM_GIF and gradcam_gif_url is None):
                    heatmap = ensemble_gradcam(models, str_path)
                    if heatmap is not None:
                        if gradcam_url is None:
                            ensemble_path = overlay_heatmap(str_path, heatmap)
                            gradcam_url = f"/outputs/{os.path.basename(ensemble_path)}"
                        if ENABLE_GRADCAM_GIF and gradcam_gif_url is None:
                            ensemble_gif_path = create_gradcam_gif(str_path, heatmap)
                            gradcam_gif_url = f"/outputs/{os.path.basename(ensemble_gif_path)}"

                if ENABLE_PER_MODEL_GRADCAM:
                    for i, model in enumerate(models):
                        model_path = os.path.join(output_dir, f"{filename_root}_gradcam_m{i + 1}.jpg")
                        if os.path.exists(model_path):
                            per_model_gradcam.append({
                                "model": f"Model_{i + 1}",
                                "image": f"/outputs/{os.path.basename(model_path)}"
                            })
                        elif gradcam_url is not None:
                            continue
                        else:
                            heatmap = ensemble_gradcam([model], str_path)
                            if heatmap is not None:
                                model_path = overlay_heatmap(str_path, heatmap)
                                model_named = os.path.join(output_dir, f"{filename_root}_gradcam_m{i + 1}.jpg")
                                if model_path != model_named:
                                    try:
                                        os.replace(model_path, model_named)
                                    except Exception:
                                        model_named = model_path
                                per_model_gradcam.append({
                                    "model": f"Model_{i + 1}",
                                    "image": f"/outputs/{os.path.basename(model_named)}"
                                })
        if gradcam_url is None:
            heatmap = _fallback_heatmap_from_image(str_path)
            if heatmap is not None:
                fallback_path = overlay_heatmap(str_path, heatmap)
                gradcam_url = f"/outputs/{os.path.basename(fallback_path)}"
                if ENABLE_GRADCAM_GIF and gradcam_gif_url is None:
                    fallback_gif = create_gradcam_gif(str_path, heatmap)
                    gradcam_gif_url = f"/outputs/{os.path.basename(fallback_gif)}"
    except Exception as e:
        print(f"[WARN] Grad-CAM failed: {e}")

    result = {
        "prediction": prediction_payload,
        "modality": modality,
        "model_status": model_status,
        "overlay": overlay_url,
        "models": ensemble_result["individual"] if ensemble_result else [],
        "agreement_score": ensemble_result["agreement_score"] if ensemble_result else 0.0,
        "explainability": {
            "gradcam": gradcam_url,
            "ensemble_gradcam": gradcam_url,
            "gif": gradcam_gif_url,
            "segmentation": overlay_url,
            "per_model": per_model_gradcam
        },
        "gemini": {
            "report": gemini.get("report", ""),
            "summary": gemini.get("summary", ""),
            "risk_level": gemini.get("risk_level", "Unknown"),
            "source": gemini.get("source", "unknown"),
            "raw": gemini.get("raw", "")
        }
    }

    legacy_prediction = prediction_payload or {
        "label": "Unavailable",
        "label_index": -1,
        "confidence": 0.0,
        "confidence_level": "Unknown",
        "class_probabilities": {},
    }

    legacy_result = {
        "prediction": legacy_prediction.get("label", "Unavailable"),
        "confidence": legacy_prediction.get("confidence", 0.0),
        "confidence_level": legacy_prediction.get("confidence_level", "Unknown"),
        "label_index": legacy_prediction.get("label_index", -1),
        "modality": modality,
        "model_status": model_status,
        "class_probabilities": legacy_prediction.get("class_probabilities", {}),
        "overlay": overlay_url,
        "models": ensemble_result["individual"] if ensemble_result else [],
        "agreement_score": ensemble_result["agreement_score"] if ensemble_result else 0.0,
        "explainability": {
            "gradcam": gradcam_url,
            "ensemble_gradcam": gradcam_url,
            "gif": gradcam_gif_url,
            "segmentation": overlay_url,
            "per_model": per_model_gradcam
        },
        "gemini": {
            "report": gemini.get("report", ""),
            "summary": gemini.get("summary", ""),
            "risk_level": gemini.get("risk_level", "Unknown"),
            "source": gemini.get("source", "unknown"),
        }
    }

    # --- Generate PDF ---
    report_filename = OUTPUT_DIR / f"{unique_name}.pdf"
    try:
        generate_report({**result, "model_status": model_status}, str(report_filename))
        report_url = f"/api/report/{report_filename.name}"
    except Exception as e:
        print(f"[WARN] PDF generation failed: {e}")
        report_url = None

    return {
        "data": result,
        "report": report_url,
        "result": legacy_result,
        "report_url": report_url,
    }

@router.get("/overlay/{filename}")
async def get_overlay(filename: str):
    """Serve the generated segmentation overlay image."""
    path = OUTPUT_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Overlay not found.")
    return FileResponse(str(path))


@router.get("/report/{filename}")
async def download_report(filename: str):
    """Serve the generated PDF for direct download."""
    path = OUTPUT_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not found.")
    return FileResponse(str(path), media_type="application/pdf",
                        filename="RadiAI_Report.pdf")
