def calibrate_confidence(conf: float) -> str:
    """Converts a raw model probability string into a human readable risk level."""
    if conf > 0.90:
        return "High"
    elif conf > 0.70:
        return "Medium"
    else:
        return "Low"
