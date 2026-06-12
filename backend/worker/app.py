import multiprocessing
import os

from celery import Celery

import models.user  # noqa: F401 — registers User with SQLAlchemy mapper before Run is loaded
from config.limits import REAPER_INTERVAL_SECONDS

# Force the "spawn" start method for child processes (e.g. PyTorch DataLoader
# workers). On Linux the default is "fork", which clones the entire parent
# process — every DataLoader worker inherits the loaded model, multiplying RAM
# usage and triggering OOM kills and process-tree assertion errors inside a
# container. "spawn" starts each worker as a fresh interpreter (the macOS
# default), so they don't inherit parent memory. Must run before any worker is
# created. force=True is safe if the method was already set to the same value.
try:
    multiprocessing.set_start_method("spawn", force=True)
except RuntimeError:
    # Start method already set in this interpreter; nothing to do.
    pass

_broker = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "deepaudio",
    broker=_broker,
    backend=_broker,
    # NOTE: task modules are intentionally NOT listed here. Each worker imports
    # only the tasks it needs via --include on its command line, so the lean
    # maintenance worker (and beat) never import the torch-heavy training tasks:
    #   GPU worker:  --include=worker.training,worker.evaluation,worker.deployment
    #   maintenance: --include=worker.maintenance
    # The API enqueues tasks by importing the functions directly, so dispatch is
    # unaffected by this.
)

celery_app.conf.update(
    task_track_started=True,
    task_track_progress=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1,
    # Maintenance tasks run on their own queue so they never wait behind a
    # long-running training job on the solo GPU worker.
    task_routes={"worker.maintenance.*": {"queue": "maintenance"}},
    # Celery Beat fires the reaper on a fixed interval.
    beat_schedule={
        "reaper": {
            "task": "worker.maintenance.run_reaper",
            "schedule": float(REAPER_INTERVAL_SECONDS),
        },
    },
)
