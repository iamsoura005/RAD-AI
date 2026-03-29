import numpy as np
from PIL import Image
from app.models.model_loader import get_model
from app.utils.label_mapper import get_label, LABELS
from app.utils.confidence import calibrate_confidence

SUPPORTED_MODALITIES = ["brain", "chest_ct", "chest_xray", "bone"]

def preprocess_image(image_path: str) -> np.ndarray:
    """Open image, resize to 224x224, normalize to [0, 1]."""
    img = Image.open(image_path).convert("RGB").resize((224, 224))
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)  # shape: (1, 224, 224, 3)


def predict_with_model(image_path: str, modality: str) -> dict | None:
    """
    Run the .h5 model. Returns a structured result or None on failure.
    None triggers Gemini-only fallback in the route.
    """
    model = get_model(modality)
    if model is None:
        print(f"[WARN] No model loaded for modality: {modality}")
        return None

    try:
        img = preprocess_image(image_path)
        preds = model.predict(img, verbose=0)  # shape: (1, num_classes)

        label_index = int(np.argmax(preds[0]))
        confidence = float(np.max(preds[0]))

        label_name = get_label(modality, label_index)

        # Full probability distribution for frontend charts
        class_probs = {}
        modality_labels = LABELS.get(modality, [])
        for i, prob in enumerate(preds[0]):
            class_name = modality_labels[i] if i < len(modality_labels) else f"Class {i}"
            class_probs[class_name] = round(float(prob), 4)

        return {
            "label": label_name,
            "label_index": label_index,
            "confidence": round(confidence, 4),
            "confidence_level": calibrate_confidence(confidence),
            "modality": modality,
            "class_probabilities": class_probs,
            "status": "success"
        }

    except Exception as e:
        print(f"[ERROR] Model prediction failed ({modality}): {e}")
        return None
