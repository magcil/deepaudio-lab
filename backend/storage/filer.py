import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

FILER_URL = os.getenv("SEAWEEDFS_FILER_URL", "http://localhost:8888")
# SeaweedFS stores S3 bucket contents under this Filer path prefix by default.
FILER_BUCKETS_PATH = os.getenv("SEAWEEDFS_FILER_BUCKETS_PATH", "/buckets")


def delete_prefix(bucket: str, prefix: str) -> None:
    """Delete a prefix and all objects beneath it via the SeaweedFS Filer API.

    A single recursive DELETE replaces the multi-round-trip S3
    list-then-batch-delete approach and also removes the empty directory
    entries that the S3 API leaves behind.

    Args:
        bucket: S3 bucket name (e.g. ``"raw-audios"``).
        prefix: Key prefix to remove (e.g. ``"default/gtzan/"``).

    Raises:
        requests.HTTPError: If the Filer returns a non-2xx status.
    """
    url = f"{FILER_URL}{FILER_BUCKETS_PATH}/{bucket}/{prefix}"
    response = requests.delete(url, params={"recursive": "true"})
    response.raise_for_status()
