import numpy as np
from PIL import Image
from app.models.model_loader import get_models
from app.utils.label_mapper import get_label, LABELS


def preprocess_image(image_path: str, input_shape: tuple) -> np.ndarray | None:
    if len(input_shape) != 4:
        return None

    _, height, width, channels = input_shape
    if height is None or width is None or channels is None:
        return None

    if channels == 1:
        img = Image.open(image_path).convert("L").resize((width, height))
        arr = np.array(img, dtype=np.float32) / 255.0
        arr = np.expand_dims(arr, axis=-1)
    else:
        img = Image.open(image_path).convert("RGB").resize((width, height))
        arr = np.array(img, dtype=np.float32) / 255.0

    return np.expand_dims(arr, axis=0)


def ensemble_predict(image_path: str, modality: str) -> dict | None:
    models = get_models(modality)
    if not models:
        return None

    predictions = []
    raw_preds = []

    for idx, model in enumerate(models):
        input_shape = getattr(model, "input_shape", None)
        if not input_shape:
            print(f"[WARN] Model_{idx + 1} missing input_shape; skipping.")
            continue

        img = preprocess_image(image_path, input_shape)
        if img is None:
            print(f"[WARN] Model_{idx + 1} expects unsupported input shape {input_shape}; skipping.")
            continue

        pred = model.predict(img, verbose=0)
        raw_preds.append(pred[0])

        label_index = int(np.argmax(pred[0]))
        confidence = float(np.max(pred[0]))

        predictions.append({
            "model": f"Model_{idx + 1}",
            "label": get_label(modality, label_index),
            "confidence": round(confidence, 3)
        })

    if not raw_preds:
        return None

    avg_pred = np.mean(raw_preds, axis=0)
    final_idx = int(np.argmax(avg_pred))
    final_confidence = float(np.max(avg_pred))

    class_probs = {}
    modality_labels = LABELS.get(modality, [])
    for i, prob in enumerate(avg_pred):
        class_name = modality_labels[i] if i < len(modality_labels) else f"Class {i}"
        class_probs[class_name] = round(float(prob), 4)

    labels = [item["label"] for item in predictions]
    agreement_score = 1.0
    if labels:
        top_label = max(set(labels), key=labels.count)
        agreement_score = round(labels.count(top_label) / len(labels), 2)

    return {
        "individual": predictions,
        "ensemble": {
            "label": get_label(modality, final_idx),
            "label_index": final_idx,
            "confidence": round(final_confidence, 4),
            "class_probabilities": class_probs
        },
        "agreement_score": agreement_score
    }
