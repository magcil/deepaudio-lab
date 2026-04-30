from celery import Celery

celery_app = Celery(
    "deepaudio",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["worker.training"],
)

celery_app.conf.update(task_track_started=True, task_track_progress=True)
