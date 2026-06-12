import models  # noqa: F401 — registers all SQLAlchemy models in this process
from db.session import SessionLocal
from services import reaper_service
from worker.app import celery_app


@celery_app.task
def run_reaper() -> dict:
    """Periodic maintenance: fail stale (dead-heartbeat) runs and reclaim old
    datasets. Scheduled by Celery Beat and executed on the maintenance queue so
    it never competes with the GPU training worker.
    """
    db = SessionLocal()
    try:
        return reaper_service.run_reaper(db)
    finally:
        db.close()
