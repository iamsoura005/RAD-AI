import os
import numpy as np
from PIL import Image
import tensorflow as tf

_MODEL = None
_MODEL_PATH = None

MODALITY_LABELS = ["brain", "chest_ct", "chest_xray", "bone"]


def _get_model_path() -> str:
    env_path = os.getenv("MODALITY_MODEL_PATH", "").strip()
    if env_path:
        return env_path

    # Default: place the CNN model at the workspace root
    model_root = os.path.abspath(os.path.join(os.getcwd(), ".."))
    return os.path.join(model_root, "modality_classifier.h5")


def _load_model() -> tf.keras.Model | None:
    global _MODEL, _MODEL_PATH
    if _MODEL is not None:
        return _MODEL

    path = _get_model_path()
    _MODEL_PATH = path
    if not os.path.exists(path):
        print(f"[WARN] Modality CNN not found at: {path}")
        return None

    try:
        _MODEL = tf.keras.models.load_model(path)
        print(f"[OK] Loaded modality CNN: {_MODEL_PATH}")
        return _MODEL
    except Exception as exc:
        print(f"[ERROR] Failed to load modality CNN: {exc}")
        return None


def _preprocess(image_path: str) -> np.ndarray:
    img = Image.open(image_path).convert("RGB").resize((224, 224))
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)


def detect_modality(image_path: str) -> str:
    """CNN-based modality detection. Returns a label or 'unknown' on failure."""
    model = _load_model()
    if model is None:
        return "unknown"

    try:
        batch = _preprocess(image_path)
        preds = model.predict(batch, verbose=0)
        idx = int(np.argmax(preds[0]))

        if 0 <= idx < len(MODALITY_LABELS):
            return MODALITY_LABELS[idx]
        return "unknown"
    except Exception as exc:
        print(f"[WARN] Modality CNN inference failed: {exc}")
        return "unknown"
