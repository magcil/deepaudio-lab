from __future__ import annotations

import os
from pathlib import Path

from deepaudiox.schemas.items import AudioClassificationItem
from torch.utils.data import Dataset

from .utils import (
    get_audio_duration_from_s3,
    load_audio_from_s3,
)

from ..storage.client import DATA_BUCKET


class S3AudioClassificationDataset(Dataset):
    """
    PyTorch Dataset for audio classification tasks using SeaweedFS Filer storage.

    This dataset mirrors the behavior and interface of DeepAudioX's
    AudioClassificationDataset, but reads WAV files directly from SeaweedFS on-the-fly.

    The ``file_to_class_mapping`` argument must be a dictionary of the form::

        {"<seaweedfs-key>": "class_name"}

    Optionally, the dataset can segment each audio file into fixed-duration
    chunks using ``segment_duration``. When enabled, each segment becomes an
    individual dataset sample.

    Attributes:
        file_to_class_mapping (dict): Mapping from SeaweedFS object paths to class names.
        sample_rate (int): Target sampling rate for audio loading.
        class_mapping (dict): Mapping from string class labels to integer IDs.
    """

    def __init__(
        self,
        file_to_class_mapping: dict[str, str],
        sample_rate: int,
        class_mapping: dict[str, int],
        segment_duration: float | None = None,
    ):
        """
        Initialize the dataset.

        Args:
            file_to_class_mapping (dict):
                Mapping from SeaweedFS object paths to class names.
            sample_rate (int):
                Target sampling rate for audio loading.
            class_mapping (dict):
                Mapping from string labels to integer IDs.
            segment_duration (float | None):
                Duration of audio segments in seconds. If None, load full audio.
                When set, the last partial segment is dropped.
        """

        self.sample_rate = sample_rate
        self.class_mapping = class_mapping
        self.file_to_class_mapping = file_to_class_mapping

        # Keep attribute naming aligned with DeepAudioX
        self.items = [
            AudioClassificationItem(
                path=Path(key),
                class_name=class_name,
                y_true=self.class_mapping[class_name],
            )
            for key, class_name in file_to_class_mapping.items()
        ]

        self.segment_duration = segment_duration

        if self.segment_duration is not None:
            self._apply_segmentation(self.segment_duration)

    def __len__(self) -> int:
        """
        Return the number of items in the dataset.

        Returns:
            int: Total number of samples.
        """
        return len(self.items)

    def __getitem__(self, idx: int) -> dict:
        """
        Get a single dataset item by index.

        Args:
            idx (int): Index of the item to retrieve.

        Returns:
            dict: An AudioClassificationItem in dictionary form.
        """

        item = self.items[idx]

        offset = item.segment_idx * self.segment_duration if self.segment_duration else 0.0

        item.feature = load_audio_from_s3(
            bucket=DATA_BUCKET,
            key=str(item.path),
            sample_rate=self.sample_rate,
            offset=offset,
            duration=self.segment_duration,
        )

        return item.to_dict()

    def _apply_segmentation(self, segment_duration: float):
        """
        Segmentize all audio files into fixed-duration segments.

        Drops the last partial segment.
        Files shorter than segment_duration are excluded.
        """

        valid_items = []

        for item in self.items:
            total_duration = get_audio_duration_from_s3(
                bucket=DATA_BUCKET,
                key=str(item.path),
            )

            if total_duration < segment_duration:
                continue

            num_segments = int(total_duration // segment_duration)

            for seg_idx in range(num_segments):
                valid_items.append(
                    AudioClassificationItem(
                        path=item.path,
                        y_true=item.y_true,
                        segment_idx=seg_idx,
                        class_name=item.class_name,
                    )
                )

        self.items = valid_items
