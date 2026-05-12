from contextlib import asynccontextmanager
from pathlib import Path

from deepaudiox import AudioClassifier
from fastapi import FastAPI

from routers.inference import router as inference_router

BASE_DIR = Path(__file__).resolve().parent
CHECKPOINT = BASE_DIR / "pretrained_models" / "checkpoint.pt"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = AudioClassifier.from_checkpoint(str(CHECKPOINT))
    yield


app = FastAPI(title="Audio Inference API", lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Audio Inference API is running", 
            "docs": "/docs"}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model": f"loaded: {CHECKPOINT}"
    }


# Include inference router
app.include_router(inference_router)