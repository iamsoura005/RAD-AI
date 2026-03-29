---
title: Rad AI
emoji: 🏆
colorFrom: green
colorTo: yellow
sdk: docker
pinned: false
---

# RadiAI

RadiAI is an end-to-end medical imaging analysis system with a FastAPI backend and a React frontend.

## Structure

- backend/ — FastAPI API, ML inference, explainability, reports
- frontend/ — React UI (Vite)
- model_files/ — .h5 model files and modality classifier

## Development

### Backend

1. Create and activate a venv
2. Install dependencies: `pip install -r backend/requirements.txt`
3. Run: `python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`

### Frontend

1. `cd frontend`
2. `npm install`
3. `npm run dev`

Set API base URL in `frontend/.env.local`:

```
VITE_API_URL=http://localhost:8000
```

## Deployment

Backend can be deployed to Hugging Face Spaces (Docker). Frontend can be deployed to Vercel.
