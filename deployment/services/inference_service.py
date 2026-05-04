from pathlib import Path
from typing import Any, Dict
import json

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CLASS_MAP_FILE_PATH = BASE_DIR / "pretrained_models" / "class_mapping.json"

def inference_on_file(
    model,
    segment_duration: float,
    sample_file: Path,
    sample_rate: int
):
    with open(CLASS_MAP_FILE_PATH, 'r') as f:
        class_mapping = json.load(f)
        
    result = model.inference_on_file(
        path=str(sample_file),
        sample_rate=sample_rate,
        class_mapping=class_mapping,
        segment_duration=segment_duration,
    )

    return result
