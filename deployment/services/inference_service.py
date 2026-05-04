from pathlib import Path
import json

from deployment.config import CLASS_MAPPING_PATH


def inference_on_file(
    model,
    segment_duration: float,
    sample_file: Path,
    sample_rate: int
):
    with open(CLASS_MAPPING_PATH, "r", encoding="utf-8") as f:
        class_mapping = json.load(f)

    result = model.inference_on_file(
        path=str(sample_file),
        sample_rate=sample_rate,
        class_mapping=class_mapping,
        segment_duration=segment_duration,
    )

    return result
