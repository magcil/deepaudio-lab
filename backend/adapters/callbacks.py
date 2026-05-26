import io
import logging

import torch
from deepaudiox.callbacks.base_callback import BaseCallback
from deepaudiox.utils.training_utils import get_logger

from storage.client import CHECKPOINTS_BUCKET, s3_client

GREEN = "\033[92m"
ENDC = "\033[0m"


class S3Checkpointer(BaseCallback):
    """Drop-in replacement for DeepAudioX's Checkpointer that saves to S3.

    Saves the model checkpoint directly to S3 as a BytesIO buffer whenever
    validation loss improves — no local file is written.

    Must remain at index 0 in ``trainer.callbacks`` (before EarlyStopper)
    because it updates ``trainer.state.lowest_loss``, which EarlyStopper
    reads on the same epoch.

    Attributes:
        bucket: S3 bucket to save checkpoints to.
        key: S3 object key for the checkpoint (e.g. 'run_42/best.pt').
        logger: Logger instance.
    """

    def __init__(self, run_id: int, checkpoint_name: str, logger: logging.Logger | None = None):
        """Initialize the S3Checkpointer.

        Args:
            run_id: Training run ID, used to scope the checkpoint key.
            logger: Optional logger. Defaults to the DeepAudioX logger.
        """
        #TODO: REMOVE HARDCODED USER
        user_id = 'default'
        self.bucket = CHECKPOINTS_BUCKET
        self.key = f"run_{run_id}/{user_id}/{checkpoint_name}"
        self.logger = logger or get_logger()

    def on_epoch_end(self, trainer) -> None:
        """Save checkpoint to S3 if validation loss improved.

        Args:
            trainer: The DeepAudioX Trainer instance.
        """
        latest_val_loss = trainer.state.validation_loss[-1]

        if trainer.state.lowest_loss <= latest_val_loss:
            return

        decrease_pct = (trainer.state.lowest_loss - latest_val_loss) / trainer.state.lowest_loss * 100

        if trainer.verbose:
            self.logger.info(
                f"[S3 CHECKPOINTER] Validation loss decreased: "
                f"({trainer.state.lowest_loss:.6f} --> {latest_val_loss:.6f}), "
                f"{GREEN}(-{decrease_pct:.2f}%){ENDC}."
            )

        # Update before EarlyStopper reads it on this same epoch
        trainer.state.lowest_loss = latest_val_loss

        try:
            buffer = io.BytesIO()
            torch.save(
                {
                    "state_dict": trainer.model.state_dict(),
                    "config": getattr(trainer.model, "config", {}),
                },
                buffer,
            )
            buffer.seek(0)
            s3_client.put_object(Bucket=self.bucket, Key=self.key, Body=buffer.getvalue())

            if trainer.verbose:
                self.logger.info(f"[S3 CHECKPOINTER] Checkpoint saved to s3://{self.bucket}/{self.key}")
        except Exception as e:
            self.logger.error(f"[S3 CHECKPOINTER] Failed to upload checkpoint: {e}")
