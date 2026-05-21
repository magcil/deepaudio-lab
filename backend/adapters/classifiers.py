import io

import torch
from deepaudiox import AudioClassifier

from storage.client import CHECKPOINTS_BUCKET
from storage.s3_storage import get_object


class S3AudioClassifier(AudioClassifier):
    """AudioClassifier subclass that loads checkpoints directly from S3.

    All training and inference behaviour is inherited unchanged from
    AudioClassifier. Only ``from_checkpoint`` is overridden to stream
    the ``.pt`` file from S3 into memory rather than reading from a
    local path.
    """

    @classmethod
    def from_checkpoint(cls, path: str) -> "S3AudioClassifier":
        """Load an S3AudioClassifier from a checkpoint stored in S3.

        Args:
            path: S3 key of the checkpoint file (e.g. 'run_42/best.pt').
                The bucket is always CHECKPOINTS_BUCKET from storage config.

        Returns:
            S3AudioClassifier with weights and config restored.

        Raises:
            ValueError: If the checkpoint was saved with a custom BaseBackbone
                instance that cannot be reconstructed from config alone.
        """
        response = get_object(bucket=CHECKPOINTS_BUCKET, key=path)
        buffer = io.BytesIO(response["Body"].read())

        ckpt = torch.load(buffer, weights_only=True, map_location="cpu")
        if ckpt["config"].get("backbone") is None:
            raise ValueError(
                "Cannot reconstruct model from checkpoint: a custom BaseBackbone "
                "instance was used. Instantiate the model manually and call "
                "model.load_state_dict(ckpt['state_dict'])."
            )
        model = cls(**ckpt["config"])
        model.load_state_dict(ckpt["state_dict"])
        return model
