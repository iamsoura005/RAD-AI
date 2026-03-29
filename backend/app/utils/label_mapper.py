LABELS = {
    "brain": ["Glioma", "Meningioma", "No Tumor", "Pituitary Tumor"],
    "chest_ct": ["Normal", "COVID-19", "Pneumonia"],
    "chest_xray": ["Normal", "Pneumonia"],
    "bone": ["Normal", "Fracture"]
}

def get_label(modality: str, index: int) -> str:
    """Safely return a human readable label, or Unknown if model structure deviates."""
    try:
        return LABELS.get(modality, ["Unknown Error"])[index]
    except IndexError:
        return f"Unknown Class {index}"
