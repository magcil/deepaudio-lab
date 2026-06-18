import os
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
S3_API = os.getenv("S3_API")
if not S3_API:
    raise ValueError("S3_API is not set in .env")

# Public URL used when generating presigned URLs that the browser will fetch.
# In Docker this differs from S3_API (which uses the internal container hostname).
S3_PUBLIC_URL = os.getenv("S3_PUBLIC_URL", S3_API)

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
if not AWS_ACCESS_KEY_ID:
    raise ValueError("AWS_ACCESS_KEY_ID is not set in .env")

AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
if not AWS_SECRET_ACCESS_KEY:
    raise ValueError("AWS_SECRET_ACCESS_KEY is not set in .env")

# Paths in filestorage for raw datasets and checkpoints, can be overridden by .env
DATA_BUCKET = os.getenv("DATA_BUCKET", "raw-audios")
CHECKPOINTS_BUCKET = os.getenv("CHECKPOINTS_BUCKET", "checkpoints")
ARTIFACTS_BUCKET = os.getenv("ARTIFACTS_BUCKET", "artifacts")

s3_client = boto3.client(
    "s3", endpoint_url=S3_API, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# Separate client whose endpoint is the browser-reachable URL, used only for
# generating presigned URLs. Bucket operations always use s3_client.
s3_presign_client = boto3.client(
    "s3", endpoint_url=S3_PUBLIC_URL, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

ALL_BUCKETS = (DATA_BUCKET, CHECKPOINTS_BUCKET, ARTIFACTS_BUCKET)


def ensure_buckets(retries: int = 15, delay: float = 2.0) -> None:
    """Create the configured buckets if they don't exist.

    SeaweedFS auto-creates buckets only on first WRITE; on a fresh deployment
    a LIST against a missing bucket fails with NoSuchBucket, which breaks the
    storage-usage check before the first upload can ever happen. Called from
    the FastAPI lifespan (API process only — workers never hit that path).

    Retries because the backend container can start before SeaweedFS's S3
    port is serving (depends_on only waits for the container to start).

    Raises:
        RuntimeError: If storage is still unreachable after all retries.
    """
    last_err: Exception | None = None
    for _ in range(retries):
        try:
            existing = {b["Name"] for b in s3_client.list_buckets()["Buckets"]}
            for bucket in ALL_BUCKETS:
                if bucket not in existing:
                    s3_client.create_bucket(Bucket=bucket)
            return
        except (EndpointConnectionError, ClientError) as e:
            last_err = e
            time.sleep(delay)
    raise RuntimeError(f"Could not ensure S3 buckets exist: {last_err}")
