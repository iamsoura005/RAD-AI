from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv
from pathlib import Path
from app.api.routes import router
from app.models.model_loader import load_models
from app.services.modality_classifier import load_modality_model

# Load environment variables from .env file
load_dotenv()

env_check = os.path.join(os.getcwd(), ".env.check")
root_env_check = os.path.abspath(os.path.join(os.getcwd(), "..", ".env.check"))
if os.path.exists(env_check):
    load_dotenv(env_check, override=True)
elif os.path.exists(root_env_check):
    load_dotenv(root_env_check, override=True)

app = FastAPI(
    title="RadiAI Backend",
    description="Medical image analysis: .h5 model (primary) + Gemini (explanation/fallback)",
    version="1.0.0"
)

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# Allow the React dev server to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    load_models()
    load_modality_model()

app.include_router(router, prefix="/api")
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")

@app.get("/")
def root():
    return {"message": "RadiAI API is running.", "docs": "/docs"}
