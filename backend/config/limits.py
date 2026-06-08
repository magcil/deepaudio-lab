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
MAX_EPOCHS = int(os.getenv("MAX_EPOCHS", "100"))
MAX_BATCH_SIZE = int(os.getenv("MAX_BATCH_SIZE", "128"))

# Set to 0 in containerised environments to avoid the Celery daemon-process
# restriction that prevents PyTorch DataLoader from spawning workers.
MAX_NUM_WORKERS = int(os.getenv("MAX_NUM_WORKERS", "4"))

# Concurrency / admission control: how many in-flight (queued + running) jobs
# are allowed per user and across the whole system. Enforced at request time
# before a job is dispatched. A submission must satisfy BOTH its per-type cap
# AND the overall (any-type) cap.
MAX_USER_TRAININGS = int(os.getenv("MAX_USER_TRAININGS", "1"))
MAX_SYSTEM_TRAININGS = int(os.getenv("MAX_SYSTEM_TRAININGS", "4"))
MAX_USER_EVALUATIONS = int(os.getenv("MAX_USER_EVALUATIONS", "2"))
MAX_SYSTEM_EVALUATIONS = int(os.getenv("MAX_SYSTEM_EVALUATIONS", "4"))
# Overall ceiling across all job types (training + evaluation).
MAX_USER_JOBS = int(os.getenv("MAX_USER_JOBS", "2"))
MAX_SYSTEM_JOBS = int(os.getenv("MAX_SYSTEM_JOBS", "4"))

# Liveness heartbeat: a running job writes a Redis key every INTERVAL seconds
# with a TTL; if it stops (worker died), the key expires after TTL and the job
# stops counting toward the caps. TTL must comfortably exceed INTERVAL (several
# missed beats) so a slow-but-alive job is never treated as dead.
HEARTBEAT_INTERVAL_SECONDS = int(os.getenv("HEARTBEAT_INTERVAL_SECONDS", "30"))
JOB_HEARTBEAT_TTL_SECONDS = int(os.getenv("JOB_HEARTBEAT_TTL_SECONDS", "180"))
