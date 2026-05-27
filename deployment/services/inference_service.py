from pathlib import Path
import json
import numpy as np


BASE_DIR = Path(__file__).resolve().parent.parent
CLASS_MAP_FILE = BASE_DIR / "pretrained_models" / "class_mapping.json"

def inference_on_wav(
    model,
    segment_duration: float,
    audio_waveform: np.ndarray,
    sample_rate: int
):
    with open(CLASS_MAP_FILE, 'r') as f:
        class_mapping = json.load(f)
        
    prediction = model.inference_on_waveform(
        x=audio_waveform,
        sample_rate=sample_rate,
        class_mapping=class_mapping,
        segment_duration=segment_duration,
        batch_size=4,
    )

    return prediction
