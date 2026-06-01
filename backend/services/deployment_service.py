import io
import json
import zipfile
from pathlib import Path

from sqlalchemy.orm import Session

from exceptions.exceptions import EntityNotFoundError, InvalidStateError
from models.run import TrainingStatus
from repositories import run_repository
from storage.client import ARTIFACTS_BUCKET, CHECKPOINTS_BUCKET, s3_client

DEPLOYMENT_DIR = Path(__file__).resolve().parents[2] / "deployment"

# Files inside deployment/ included verbatim in every bundle (relative to DEPLOYMENT_DIR).
_APP_FILES = [
    "Dockerfile",
    "requirements.txt",
    "README.md",
    "main.py",
    "config.py",
    "__init__.py",
    "routers/__init__.py",
    "routers/inference.py",
    "services/inference_service.py",
]


def build_bundle(db: Session, run_id: int, user_id: str, name: str, progress_callback=None) -> None:
    """Fetch the trained checkpoint from SeaweedFS, assemble a self-contained
    inference zip bundle, upload it to the artifacts bucket, and persist the
    artifact key on the Run record.

    The zip layout mirrors the ``deployment/`` package so the user can
    unzip and run ``docker build .`` immediately::

        <name>.zip
        ├── Dockerfile
        ├── requirements.txt
        ├── README.md
        ├── main.py
        ├── config.py
        ├── __init__.py
        ├── routers/
        │   ├── __init__.py
        │   └── inference.py
        ├── services/
        │   ├── __init__.py
        │   └── inference_service.py
        └── pretrained_models/
            ├── checkpoint.pt
            └── class_mapping.json

    Args:
        db (Session): Active SQLAlchemy session.
        run_id (int): Primary key of the run to deploy.
        user_id (str): Keycloak sub of the run owner.
        name (str): User-provided bundle name stored in deploy_name.

    Raises:
        EntityNotFoundError: Run not found or not owned by user_id.
        InvalidStateError: Training has not completed successfully.
    """
    def _progress(step: str, pct: int) -> None:
        if progress_callback is not None:
            progress_callback(step, pct)

    run = run_repository.get_by_id(db, run_id, owner_id=user_id)
    if run is None:
        raise EntityNotFoundError("Run", run_id)
    if run.training_status != TrainingStatus.success:
        raise InvalidStateError("Cannot deploy a run that has not completed training successfully.")

    exp_params = run.experiment_params
    params: dict = exp_params.params
    checkpoint_name: str = params["checkpoint"]
    sample_rate: int = params.get("sampling_rate", 32000)
    segment_duration: float = params.get("segment_duration", 3.0)
    class_mapping: dict = params["class_mapping"]

    _progress("Downloading checkpoint", 20)
    checkpoint_bytes = s3_client.get_object(
        Bucket=CHECKPOINTS_BUCKET,
        Key=f"run_{run_id}/{user_id}/{checkpoint_name}.pt",
    )["Body"].read()

    _progress("Building bundle", 60)
    zip_buf = _build_zip(
        checkpoint_bytes=checkpoint_bytes,
        class_mapping=class_mapping,
        sample_rate=sample_rate,
        segment_duration=segment_duration,
    )

    _progress("Uploading bundle", 85)
    artifact_key = f"run_{run_id}/{user_id}/bundle.zip"
    s3_client.put_object(
        Bucket=ARTIFACTS_BUCKET,
        Key=artifact_key,
        Body=zip_buf.getvalue(),
        ContentType="application/zip",
    )

    run_repository.update_deploy_fields(
        db, run_id=run_id, deploy_name=name, deploy_artifact_key=artifact_key
    )


def generate_download_url(db: Session, run_id: int, user_id: str) -> str:
    """Generate a short-lived presigned GET URL for an existing deployment bundle.

    Args:
        db (Session): Active SQLAlchemy session.
        run_id (int): Primary key of the run.
        user_id (str): Keycloak sub of the run owner.

    Raises:
        EntityNotFoundError: Run not found or not owned by user_id.
        InvalidStateError: No bundle has been built for this run yet.

    Returns:
        str: Presigned URL valid for 5 minutes.
    """
    run = run_repository.get_by_id(db, run_id, owner_id=user_id)
    if run is None:
        raise EntityNotFoundError("Run", run_id)
    if not run.deploy_artifact_key:
        raise InvalidStateError("No deployment bundle has been built for this run.")

    return s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": ARTIFACTS_BUCKET,
            "Key": run.deploy_artifact_key,
            "ResponseContentDisposition": f'attachment; filename="{run.deploy_name}.zip"',
        },
        ExpiresIn=300,
    )


def _build_zip(
    checkpoint_bytes: bytes,
    class_mapping: dict,
    sample_rate: int,
    segment_duration: float,
) -> io.BytesIO:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for rel in _APP_FILES:
            src = DEPLOYMENT_DIR / rel
            if src.is_file():
                zf.write(src, rel)

        zf.writestr("services/__init__.py", "")

        zf.writestr("pretrained_models/checkpoint.pt", checkpoint_bytes)
        zf.writestr(
            "pretrained_models/class_mapping.json",
            json.dumps(class_mapping, indent=2),
        )
        zf.writestr(".env", f"SAMPLE_RATE={sample_rate}\nSEGMENT_DURATION={segment_duration}\n")

    buf.seek(0)
    return buf
