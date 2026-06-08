import io
import struct

import librosa
import numpy as np

from storage.client import s3_client


def get_class_mapping_from_s3_dataset(s3_prefix: str, split: str, bucket: str) -> dict[str, int]:
    """Generate the DeepAudioX class mapping from a dataset stored in S3.

    Lists virtual subdirectories under ``{s3_prefix}{split}/``
    using the S3 delimiter API — no file content is downloaded.

    Expected key structure::

        bucket/
        └── {user_id}/
            └── {dataset_id}/
                └── {split}/
                    ├── class_a/
                    │   └── audio1.wav
                    └── class_b/
                        └── audio2.wav

    Args:
        s3_prefix: The dataset's storage prefix (e.g. ``"default/1/"``).
        split: The dataset split (e.g., 'train', 'val', 'test').
        bucket: The S3 bucket where datasets are stored.

    Returns:
        A dictionary mapping class names to integer labels, ordered alphabetically.

    Raises:
        ValueError: If no classes are found under the given prefix.
    """
    prefix = f"{s3_prefix}{split}/"

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


def create_file_to_class_mapping_from_s3(s3_prefix: str, split: str, bucket: str) -> dict[str, str]:
    """Build the file-to-class mapping required by DeepAudioX's AudioClassificationDataset.

    Lists all ``.wav`` objects under ``{s3_prefix}{split}/`` and maps each S3
    key to its class name, derived from the subdirectory level immediately
    after the split.

    Expected key structure::

        bucket/
        └── {user_id}/
            └── {dataset_id}/
                └── {split}/
                    ├── class_a/
                    │   └── audio1.wav
                    └── class_b/
                        └── audio2.wav

    Args:
        s3_prefix: The dataset's storage prefix, trailing slash included
            (e.g. ``"default/1/"``).
        split: The dataset split (e.g., 'train', 'val', 'test').
        bucket: The S3 bucket where datasets are stored.

    Returns:
        A dictionary mapping S3 keys to class name strings,
        e.g. ``{"default/1/train/class_a/audio1.wav": "class_a"}``.

    Raises:
        ValueError: If no .wav files are found under the given prefix.
    """
    prefix = f"{s3_prefix}{split}/"

    paginator = s3_client.get_paginator("list_objects_v2")
    file_to_class: dict[str, str] = {}
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            key: str = obj["Key"]
            if not key.lower().endswith(".wav"):
                continue
            # Strip the prefix to get "class_name/filename.wav"
            relative = key[len(prefix) :]
            class_name = relative.split("/")[0]
            file_to_class[key] = class_name

    if not file_to_class:
        raise ValueError(f"No .wav files found in s3://{bucket}/{prefix}")

    return file_to_class


def _parse_wav_chunks(header_bytes: bytes) -> tuple[int, int, int, int, int]:
    """Locate the fmt and data chunks in a WAV header.

    Handles non-standard WAV files that insert extra chunks between fmt and
    data (e.g. LIST, INFO, id3 written by macOS tools), which push the PCM
    data beyond the assumed byte-44 position. Also handles odd-sized chunks
    per the RIFF spec (each chunk is padded to an even byte boundary).

    Args:
        header_bytes: The leading bytes of the WAV file (at least 512 recommended).

    Returns:
        (sample_rate, num_channels, bits_per_sample, data_offset, data_size)

    Raises:
        ValueError: If the bytes are not a valid WAV or the data chunk is not
            found within the supplied bytes.
    """
    if header_bytes[:4] != b"RIFF" or header_bytes[8:12] != b"WAVE":
        raise ValueError("Not a valid WAV file")

    # fmt chunk always begins at byte 12; read its size to skip it correctly.
    fmt_chunk_size = struct.unpack_from("<I", header_bytes, 16)[0]
    num_channels = struct.unpack_from("<H", header_bytes, 22)[0]
    sample_rate = struct.unpack_from("<I", header_bytes, 24)[0]
    bits_per_sample = struct.unpack_from("<H", header_bytes, 34)[0]

    # Scan forward chunk by chunk until the data chunk is found.
    # Add one padding byte when chunk_size is odd (RIFF even-alignment rule).
    pos = 12 + 8 + fmt_chunk_size + (fmt_chunk_size % 2)
    while pos + 8 <= len(header_bytes):
        chunk_id = header_bytes[pos : pos + 4]
        chunk_size = struct.unpack_from("<I", header_bytes, pos + 4)[0]
        if chunk_id == b"data":
            return sample_rate, num_channels, bits_per_sample, pos + 8, chunk_size
        pos += 8 + chunk_size + (chunk_size % 2)

    raise ValueError("Could not find 'data' chunk within the supplied header bytes")


def get_audio_duration_from_s3(bucket: str, key: str) -> float:
    """Get the duration of a WAV file stored in S3 by reading only its header.

    Args:
        bucket: The S3 bucket where the audio file is stored.
        key: The S3 key (path) to the audio file.

    Returns:
        The duration of the audio file in seconds.
    """
    header = s3_client.get_object(Bucket=bucket, Key=key, Range="bytes=0-511")["Body"].read()
    sample_rate, num_channels, bits_per_sample, _, data_size = _parse_wav_chunks(header)
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
    in a single request. For segmented loads, the WAV header is parsed to
    locate the PCM data chunk, then only the needed bytes are fetched in a
    second request — avoiding a full file download per segment.

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

    header = s3_client.get_object(Bucket=bucket, Key=key, Range="bytes=0-511")["Body"].read()
    orig_sr, num_channels, bits_per_sample, data_offset, _ = _parse_wav_chunks(header)
    bytes_per_frame = num_channels * (bits_per_sample // 8)

    start_byte = data_offset + int(offset * orig_sr) * bytes_per_frame
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
