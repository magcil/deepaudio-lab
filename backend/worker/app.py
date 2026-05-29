from celery import Celery

import models.user  # noqa: F401 — registers User with SQLAlchemy mapper before Run is loaded

celery_app = Celery(
    "deepaudio",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["worker.training", "worker.evaluation"],
)

celery_app.conf.update(
    task_track_started=True,
    task_track_progress=True,
    worker_prefetch_multiplier=1,
)
