from fastapi import FastAPI
from deployment.routers.inference import router as inference_router
from deepaudiox import AudioClassifier

from deployment.config import CHECKPOINT_PATH


app = FastAPI(title="Audio Inference API")


@app.on_event("startup")
def load_model():
    app.state.model = AudioClassifier.from_checkpoint(CHECKPOINT_PATH)


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


# Include inference router
app.include_router(inference_router)
