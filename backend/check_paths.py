import os
from app.models.model_loader import MODEL_PATHS

for k, v in MODEL_PATHS.items():
    print(k, '->', v, ':', os.path.exists(v))
