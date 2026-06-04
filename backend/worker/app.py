import multiprocessing
import os

from celery import Celery

import models.user  # noqa: F401 — registers User with SQLAlchemy mapper before Run is loaded

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
    include=["worker.training", "worker.evaluation", "worker.deployment"],
)

celery_app.conf.update(
    task_track_started=True,
    task_track_progress=True,
    worker_prefetch_multiplier=1,
)
