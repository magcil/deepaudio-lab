import sys
from pathlib import Path

from schemas.train_params import TrainParams
from services.training_service import TrainingService
from worker.app import celery_app

sys.path.insert(0, str(Path(__file__).parent.parent))


@celery_app.task(bind=True)
def run_training(self, params: dict, class_mapping: dict):
    def progress_callback(epoch, total_epochs, train_loss, val_loss):
        self.update_state(
            state="PROGRESS",
            meta={
                "epoch": epoch,
                "total_epochs": total_epochs,
                "train_loss": train_loss,
                "val_loss": val_loss,
            },
        )

    service = TrainingService()
    service.perform_training(TrainParams(**params), class_mapping, progress_callback=progress_callback)
    return {"status": "done"}
