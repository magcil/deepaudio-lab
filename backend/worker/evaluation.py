import sys
from pathlib import Path

import models  # noqa: F401 — registers all SQLAlchemy models in this process
from db.session import SessionLocal
from models.classification_report import ClassificationReport
from repositories import classification_report_repository
from services.evaluation_service import EvaluationService
from worker.app import celery_app

sys.path.insert(0, str(Path(__file__).parent.parent))


@celery_app.task(bind=True)
def run_evaluation(self, run_id: int, exp_params: dict):
    def progress_callback(current_batch, total_batches, elapsed, eta):
        self.update_state(
            state="PROGRESS",
            meta={
                "current_batch": current_batch,
                "total_batches": total_batches,
                "progress": round(current_batch / total_batches * 100, 1),
                "elapsed_seconds": int(elapsed),
                "eta_seconds": int(eta),
            },
        )

    service = EvaluationService()
    report = service.perform_evaluation(run_id, exp_params, progress_callback=progress_callback)

    if report is None:
        return {"status": "failed"}

    # TODO: DECOUPLE DB COMMUNICATION FROM CELERY WORKER
    db = SessionLocal()
    try:
        classification_report_repository.create(
            db=db,
            report=ClassificationReport(run_id=run_id, report=report),
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return {"status": "done"}
