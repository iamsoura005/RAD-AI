import cv2
import numpy as np
import os

def create_overlay(image_path: str, mask: np.ndarray) -> str:
    """Creates a red overlay on the original image for the given mask."""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image at {image_path}")

    # Resize mask to match image
    mask_resized = cv2.resize(mask, (img.shape[1], img.shape[0]))

    # Create red overlay
    overlay = img.copy()
    overlay[mask_resized > 0.5] = [0, 0, 255] # BGR format: Red

    # Save to outputs directory
    # Get basename of image_path
    basename = os.path.basename(image_path)
    # Output path replacing uploads with outputs seamlessly, independent of absolute path
    output_dir = os.path.join(os.path.dirname(os.path.dirname(image_path)), "outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, f"seg_{basename}")
    cv2.imwrite(output_path, overlay)

    return output_path
