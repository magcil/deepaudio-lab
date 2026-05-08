import sys
from pathlib import Path

import models  # noqa: F401 — registers all SQLAlchemy models in this process
from schemas.train_params import TrainParams
from services.training_service import TrainingService
from worker.app import celery_app

sys.path.insert(0, str(Path(__file__).parent.parent))


@celery_app.task(bind=True)
def run_training(self, params: dict, class_mapping: dict, run_id: int):
    def progress_callback(
        epoch, total_epochs, train_loss, val_loss, best_val_loss, current_patience, total_patience, elapsed, eta
    ):
        self.update_state(
            state="PROGRESS",
            meta={
                "epoch": epoch,
                "total_epochs": total_epochs,
                "progress": 100
                if (total_patience and current_patience == total_patience)
                else round(epoch / total_epochs * 100, 1),
                "train_loss": train_loss,
                "val_loss": val_loss,
                "best_val_loss": best_val_loss,
                "elapsed_seconds": int(elapsed),
                "eta_seconds": int(eta),
                "current_patience": current_patience,
                "total_patience": total_patience,
            },
        )

    service = TrainingService()
    service.perform_training(TrainParams(**params), class_mapping, run_id=run_id, progress_callback=progress_callback)
    return {"status": "done"}
