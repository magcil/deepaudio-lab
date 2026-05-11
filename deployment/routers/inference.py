import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict

import soundfile as sf

from fastapi import APIRouter, File, Form, UploadFile, HTTPException, Depends
from fastapi import Request

from deployment.config import get_float_env, get_int_env
from deployment.services.inference_service import inference_on_wav

router = APIRouter(prefix="/inference", tags=["Inference"])

ALLOWED_EXTENSIONS = {".wav", ".flac", ".mp3"}
MIN_DURATION = 1.0          # seconds
MAX_DURATION = 300.0        # 5 minutes
MAX_SEGMENT_DURATION = 10.0 # seconds
DEFAULT_SAMPLE_RATE = get_int_env("SAMPLE_RATE", 32000)
DEFAULT_SEGMENT_DURATION = get_float_env("SEGMENT_DURATION", 3.0)

def get_model(request: Request):
    return request.app.state.model


@router.post("/")
async def inference(
    model=Depends(get_model),
    path: UploadFile = File(...),
    segment_duration: float = Form(DEFAULT_SEGMENT_DURATION),
    sample_rate: int = Form(DEFAULT_SAMPLE_RATE),
) -> Dict[str, Any]:

    # --- File extension check ---
    suffix = Path(path.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format {suffix}. Allowed: {ALLOWED_EXTENSIONS}",
        )

    try:
        # --- Load audio for validation ---
        try:
            audio_waveform, sr = sf.read(path.file, dtype="float32")
        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Could not read audio file. File may be corrupted or unsupported.",
            )

        duration = len(audio_waveform) / sr

        # --- Duration checks ---
        if duration < MIN_DURATION:
            raise HTTPException(
                status_code=400,
                detail="Audio must be at least 1 second long.",
            )

        if duration > MAX_DURATION:
            raise HTTPException(
                status_code=400,
                detail="Audio must be less than 5 minutes.",
            )

        # --- Segment duration checks ---
        if segment_duration > duration:
            raise HTTPException(
                status_code=400,
                detail="segment_duration cannot exceed audio duration.",
            )

        if segment_duration > MAX_SEGMENT_DURATION:
            raise HTTPException(
                status_code=400,
                detail="segment_duration must be <= 10 seconds.",
            )

        # --- Run inference ---
        result = inference_on_wav(
            model=model,
            segment_duration=segment_duration,
            audio_waveform=audio_waveform,
            sample_rate=sample_rate,
        )

        return {"result": result}

    finally:
        await path.close()
