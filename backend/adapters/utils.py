import io
import struct

import librosa
import numpy as np

from ..storage.client import s3_client


def get_class_mapping_from_s3_dataset(user_id: str, dataset_name: str, split: str, bucket: str) -> dict[str, int]:
    """Generate the DeepAudioX class mapping from a dataset stored in S3.

    Lists virtual subdirectories under ``{user_id}/{dataset_name}/{split}/``
    using the S3 delimiter API — no file content is downloaded.

    Expected key structure::

        bucket/
        └── {user_id}/
            └── {dataset_name}/
                └── {split}/
                    ├── class_a/
                    │   └── audio1.wav
                    └── class_b/
                        └── audio2.wav

    Args:
        user_id: The ID of the user who owns the dataset.
        dataset_name: The name of the dataset.
        split: The dataset split (e.g., 'train', 'val', 'test').
        bucket: The S3 bucket where datasets are stored.

    Returns:
        A dictionary mapping class names to integer labels, ordered alphabetically.

    Raises:
        ValueError: If no classes are found under the given prefix.
    """
    prefix = f"{user_id}/{dataset_name}/{split}/"

    paginator = s3_client.get_paginator("list_objects_v2")
    class_names = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter="/"):
        for cp in page.get("CommonPrefixes", []):
            # cp["Prefix"] looks like "user/dataset/split/class_name/"
            class_name = cp["Prefix"].rstrip("/").split("/")[-1]
            class_names.append(class_name)

    if not class_names:
        raise ValueError(f"No classes found in s3://{bucket}/{prefix}")

    return {name: idx for idx, name in enumerate(sorted(class_names))}


def get_audio_duration_from_s3(bucket: str, key: str) -> float:
    """Get the duration of a WAV file stored in S3 by reading only its 44-byte header.

    Args:
        bucket: The S3 bucket where the audio file is stored.
        key: The S3 key (path) to the audio file.

    Returns:
        The duration of the audio file in seconds.
    """
    response = s3_client.get_object(Bucket=bucket, Key=key, Range="bytes=0-43")
    header = response["Body"].read()

    sample_rate = struct.unpack_from("<I", header, 24)[0]
    bits_per_sample = struct.unpack_from("<H", header, 34)[0]
    num_channels = struct.unpack_from("<H", header, 22)[0]
    data_size = struct.unpack_from("<I", header, 40)[0]

    num_samples = data_size // (num_channels * (bits_per_sample // 8))
    return num_samples / sample_rate


def load_audio_from_s3(
    bucket: str,
    key: str,
    sample_rate: int,
    offset: float = 0.0,
    duration: float | None = None,
) -> np.ndarray:
    """Load audio from S3, downloading only the requested segment.

    For unsegmented loads (offset=0, duration=None) the full file is fetched
    in a single request. For segmented loads, the WAV header is read first
    (44 bytes) to derive byte offsets, then only the needed PCM bytes are
    fetched in a second request — avoiding a full file download per segment.

    Args:
        bucket: S3 bucket where the file is stored.
        key: S3 key of the WAV file.
        sample_rate: Target sample rate; resampling is applied if it differs
            from the file's native rate.
        offset: Start position in seconds. Defaults to 0.0.
        duration: Length to load in seconds. None loads to end of file.

    Returns:
        1-D float32 numpy array of the waveform.
    """
    if offset == 0.0 and duration is None:
        response = s3_client.get_object(Bucket=bucket, Key=key)
        y, _ = librosa.load(io.BytesIO(response["Body"].read()), sr=sample_rate, mono=True)
        return y

    # Read WAV header to derive byte positions
    header = s3_client.get_object(Bucket=bucket, Key=key, Range="bytes=0-43")["Body"].read()
    orig_sr = struct.unpack_from("<I", header, 24)[0]
    num_channels = struct.unpack_from("<H", header, 22)[0]
    bits_per_sample = struct.unpack_from("<H", header, 34)[0]
    bytes_per_frame = num_channels * (bits_per_sample // 8)

    start_byte = 44 + int(offset * orig_sr) * bytes_per_frame
    end_byte = start_byte + int(duration * orig_sr) * bytes_per_frame - 1 if duration is not None else ""
    audio_data = s3_client.get_object(Bucket=bucket, Key=key, Range=f"bytes={start_byte}-{end_byte}")["Body"].read()
    data_size = len(audio_data)

    # Reconstruct a valid in-memory WAV so librosa can decode it
    byte_rate = orig_sr * bytes_per_frame
    wav = io.BytesIO()
    wav.write(b"RIFF")
    wav.write(struct.pack("<I", 36 + data_size))
    wav.write(b"WAVE")
    wav.write(b"fmt ")
    wav.write(struct.pack("<IHHIIHH", 16, 1, num_channels, orig_sr, byte_rate, bytes_per_frame, bits_per_sample))
    wav.write(b"data")
    wav.write(struct.pack("<I", data_size))
    wav.write(audio_data)
    wav.seek(0)

    y, _ = librosa.load(wav, sr=sample_rate, mono=True)
    return y
