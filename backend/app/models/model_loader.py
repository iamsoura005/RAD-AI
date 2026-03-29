import tensorflow as tf
import os

# Models live in the parent of the backend/ folder (i.e., "best data set/")
_DEFAULT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_MODEL_ROOT = os.getenv("MODEL_ROOT", _DEFAULT_ROOT)

MODEL_PATHS = {
    "brain":      [os.path.join(_MODEL_ROOT, "model_files", "best_model (1).h5")],
    "chest_ct":   [os.path.join(_MODEL_ROOT, "model_files", "manual_chest_ctscan_model.h5")],
    "chest_xray": [os.path.join(_MODEL_ROOT, "model_files", "manual_chest_xray_model.h5")],
    "bone":       [os.path.join(_MODEL_ROOT, "model_files", "bone_fracture_enhanced.h5")],
}

# Human-readable label maps per modality
LABEL_MAPS = {
    "brain":      ["Glioma", "Meningioma", "No Tumor", "Pituitary"],
    "chest_ct":   ["Normal", "Pneumonia", "COVID-19", "Lung Cancer"],
    "chest_xray": ["Normal", "Pneumonia", "Pleural Effusion", "Cardiomegaly"],
    "bone":       ["Normal", "Fractured"],
}

models: dict = {}
model_errors: dict = {}

def load_models():
    """Load all available .h5 models at startup."""
    for modality, paths in MODEL_PATHS.items():
        if modality == "bone" and os.getenv("BONE_MODEL_MODE", "gemini").lower() == "gemini":
            models[modality] = []
            model_errors[modality] = ["disabled: using Gemini for bone"]
            print("[INFO] Bone model disabled; Gemini-only mode enabled.")
            continue
        models[modality] = []
        model_errors[modality] = []
        for path in paths:
            abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), path))
            if os.path.exists(abs_path):
                try:
                    models[modality].append(tf.keras.models.load_model(abs_path, compile=False))
                    print(f"[OK] Loaded model: {modality} ← {abs_path}")
                except Exception as e:
                    err_msg = f"{abs_path}: {e}"
                    model_errors[modality].append(err_msg)
                    print(f"[ERROR] Failed to load {modality}: {e}")
            else:
                err_msg = f"missing: {abs_path}"
                model_errors[modality].append(err_msg)
                print(f"[WARN] Model file missing: {abs_path}")

def get_model(modality: str):
    modality_models = models.get(modality, [])
    return modality_models[0] if modality_models else None


def get_models(modality: str):
    return models.get(modality, [])

def get_labels(modality: str):
    return LABEL_MAPS.get(modality, [])


def get_model_status() -> dict:
    status = {}
    for modality, paths in MODEL_PATHS.items():
        status[modality] = {
            "expected": paths,
            "loaded": len(models.get(modality, [])),
            "errors": model_errors.get(modality, [])
        }
    return status
