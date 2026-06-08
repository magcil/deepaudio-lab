from contextlib import asynccontextmanager

from deepaudiox import AudioClassifier
from fastapi import FastAPI

from .config import CHECKPOINT_PATH
from .routers.inference import router as inference_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model = AudioClassifier.from_checkpoint(str(CHECKPOINT_PATH))
    yield


app = FastAPI(title="Audio Inference API", lifespan=lifespan)


@app.get("/")
async def root():
    return {
        "message": "Audio Inference API is running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model": f"loaded: {CHECKPOINT_PATH}",
    }


app.include_router(inference_router)
