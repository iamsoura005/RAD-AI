import os
import numpy as np
from PIL import Image
import tensorflow as tf

MODEL_PATH = os.getenv("MODALITY_MODEL_PATH", "model_files/modality_model.h5")
LABELS = ["brain", "chest", "ct", "ecg"]

LABEL_MAP = {
    "brain": "brain",
    "chest": "chest_xray",
    "ct": "chest_ct",
    "ecg": "unknown"
}

model = None


def load_modality_model() -> None:
    global model
    if model is not None:
        return

    if os.path.exists(MODEL_PATH):
        model = tf.keras.models.load_model(MODEL_PATH)
        print(f"[OK] Loaded modality model: {MODEL_PATH}")
    else:
        print(f"[WARN] Modality model not found at: {MODEL_PATH}")


def predict_modality(image_path: str) -> str:
    if model is None:
        return "unknown"

    img = Image.open(image_path).convert("RGB").resize((224, 224))
    arr = np.array(img, dtype=np.float32) / 255.0
    arr = np.expand_dims(arr, axis=0)

    preds = model.predict(arr, verbose=0)
    idx = int(np.argmax(preds[0]))

    if 0 <= idx < len(LABELS):
        return LABEL_MAP.get(LABELS[idx], "unknown")
    return "unknown"
