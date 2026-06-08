import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH)

CHECKPOINT_PATH = BASE_DIR / "pretrained_models" / os.getenv("CHECKPOINT_FILENAME", "checkpoint.pt")
CLASS_MAPPING_PATH = BASE_DIR / "pretrained_models" / "class_mapping.json"


def get_float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return float(value)
    except ValueError:
        return default


def get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError:
        return default
