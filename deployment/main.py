from fastapi import FastAPI
from deployment.routers.inference import router as inference_router
from deepaudiox import AudioClassifier


from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CHECKPOINT = BASE_DIR / "pretrained_models" / "checkpoint.pt"

app = FastAPI(title="Audio Inference API")

@app.on_event("startup")
def load_model():
    app.state.model = AudioClassifier.from_checkpoint(CHECKPOINT)


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