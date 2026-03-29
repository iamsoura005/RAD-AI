import os
import numpy as np
import tensorflow as tf
import cv2
import imageio
from PIL import Image


def find_last_conv_layer(model: tf.keras.Model) -> str | None:
    for layer in reversed(model.layers):
        if isinstance(layer, tf.keras.layers.Conv2D):
            return layer.name
    return None


def get_gradcam_heatmap(model: tf.keras.Model, image_path: str) -> np.ndarray | None:
    last_conv_layer_name = find_last_conv_layer(model)
    if last_conv_layer_name is None:
        return None

    img = Image.open(image_path).convert("RGB").resize((224, 224))
    arr = np.array(img, dtype=np.float32) / 255.0
    arr = np.expand_dims(arr, axis=0)

    grad_model = tf.keras.models.Model(
        [model.inputs],
        [model.get_layer(last_conv_layer_name).output, model.output]
    )

    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(arr)
        class_idx = tf.argmax(predictions[0])
        loss = predictions[:, class_idx]

    grads = tape.gradient(loss, conv_outputs)
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

    conv_outputs = conv_outputs[0]
    heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)

    heatmap = np.maximum(heatmap, 0)
    max_val = np.max(heatmap)
    if max_val > 0:
        heatmap /= max_val

    return heatmap


def overlay_heatmap(image_path: str, heatmap: np.ndarray, alpha: float = 0.4) -> str:
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image at {image_path}")

    heatmap_resized = cv2.resize(heatmap, (img.shape[1], img.shape[0]))
    heatmap_uint8 = np.uint8(255 * heatmap_resized)
    heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)

    superimposed = cv2.addWeighted(img, 1 - alpha, heatmap_color, alpha, 0)

    filename = os.path.basename(image_path)
    name_root = os.path.splitext(filename)[0]
    output_dir = os.path.join(os.path.dirname(os.path.dirname(image_path)), "outputs")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{name_root}_gradcam.jpg")

    cv2.imwrite(output_path, superimposed)
    return output_path


def create_gradcam_gif(image_path: str, heatmap: np.ndarray) -> str:
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image at {image_path}")

    heatmap_resized = cv2.resize(heatmap, (img.shape[1], img.shape[0]))

    frames = []
    for alpha in np.linspace(0, 0.8, 10):
        heatmap_uint8 = np.uint8(255 * heatmap_resized)
        heatmap_color = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)
        blended = cv2.addWeighted(img, 1 - alpha, heatmap_color, alpha, 0)
        frames.append(cv2.cvtColor(blended, cv2.COLOR_BGR2RGB))

    filename = os.path.basename(image_path)
    name_root = os.path.splitext(filename)[0]
    output_dir = os.path.join(os.path.dirname(os.path.dirname(image_path)), "outputs")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{name_root}_gradcam.gif")

    imageio.mimsave(output_path, frames, duration=0.2)
    return output_path


def ensemble_gradcam(models: list[tf.keras.Model], image_path: str) -> np.ndarray | None:
    heatmaps = []
    for model in models:
        try:
            heatmap = get_gradcam_heatmap(model, image_path)
            if heatmap is not None:
                heatmaps.append(heatmap)
        except Exception:
            continue

    if not heatmaps:
        return None

    avg_heatmap = np.mean(heatmaps, axis=0)
    avg_heatmap = np.maximum(avg_heatmap, 0)
    max_val = np.max(avg_heatmap)
    if max_val > 0:
        avg_heatmap /= max_val

    return avg_heatmap
