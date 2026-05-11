from pathlib import Path
import json
import numpy as np

from deployment.config import CLASS_MAPPING_PATH


def inference_on_wav(
    model,
    segment_duration: float,
    audio_waveform: np.ndarray,
    sample_rate: int
):
    with open(CLASS_MAPPING_PATH, "r", encoding="utf-8") as f:
        class_mapping = json.load(f)
        
    prediction = model.inference_on_waveform(
        x=audio_waveform,
        sample_rate=sample_rate,
        class_mapping=class_mapping,
        segment_duration=segment_duration,
        batch_size=4,
    )

    return prediction
