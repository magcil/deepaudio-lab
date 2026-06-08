import os
from pathlib import Path

from dotenv import load_dotenv

# Load backend/.env up front so limits resolve correctly even if this module is
# imported in isolation (a standalone script or test) before any other module
# triggers load_dotenv. In Docker the file is absent and values come from the
# container env — load_dotenv is then a harmless no-op. Existing env vars are
# never overridden, so the container environment always wins.
load_dotenv(Path(__file__).parent.parent / ".env")

# Per-user upload quota in bytes (default 10 GB)
USER_SPACE_LIMIT = int(os.getenv("USER_SPACE_LIMIT", "10737418240"))

# System-wide total storage cap across all users in bytes (default 100 GB)
TOTAL_STORAGE_LIMIT = int(os.getenv("TOTAL_STORAGE_LIMIT", "107374182400"))

# Training hyperparameter ceilings
MAX_SEGMENT_DURATION = float(os.getenv("MAX_SEGMENT_DURATION", "10.0"))  # seconds
MAX_EPOCHS           = int(os.getenv("MAX_EPOCHS",             "100"))
MAX_BATCH_SIZE       = int(os.getenv("MAX_BATCH_SIZE",         "128"))

# Set to 0 in containerised environments to avoid the Celery daemon-process
# restriction that prevents PyTorch DataLoader from spawning workers.
MAX_NUM_WORKERS      = int(os.getenv("MAX_NUM_WORKERS",        "4"))