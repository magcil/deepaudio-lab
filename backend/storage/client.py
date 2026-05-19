import os
from pathlib import Path

import boto3
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
S3_API = os.getenv("S3_API")
if not S3_API:
    raise ValueError("S3_API is not set in .env")

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
if not AWS_ACCESS_KEY_ID:
    raise ValueError("AWS_ACCESS_KEY_ID is not set in .env")

AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
if not AWS_SECRET_ACCESS_KEY:
    raise ValueError("AWS_SECRET_ACCESS_KEY is not set in .env")

# Paths in filestorage for raw datasets and checkpoints, can be overridden by .env
DATA_BUCKET = os.getenv("DATA_BUCKET", "raw-audios")
CHECKPOINTS_BUCKET = os.getenv("CHECKPOINTS_BUCKET", "checkpoints")

s3_client = boto3.client(
    "s3", endpoint_url=S3_API, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)
