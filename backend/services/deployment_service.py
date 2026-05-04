import os
import shlex
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from exceptions.exceptions import InvalidResourceError, ResourceNotFoundError

REPO_ROOT = Path(__file__).resolve().parents[2]
DEPLOYMENT_DIR = REPO_ROOT / "deployment"
DEPLOYMENT_DOCKERFILE = DEPLOYMENT_DIR / "Dockerfile"
IMAGE_TAG = "deepaudio-inference:latest"
ARCHIVE_NAME = "deepaudio_inference.tar"
DOCKER_COMMAND = shlex.split(os.getenv("DEPLOYMENT_DOCKER_COMMAND", "docker"))


@dataclass
class DeploymentArchive:
    archive_path: Path
    temp_dir: Path
    image_tag: str = IMAGE_TAG
    download_name: str = ARCHIVE_NAME

    def cleanup(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

        try:
            subprocess.run(
                [*DOCKER_COMMAND, "image", "rm", "-f", self.image_tag],
                check=False,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            pass


def build_deployment_archive(
    checkpoint_path: str,
    class_mapping_path: str,
    segment_duration: float,
    sample_rate: int,
) -> DeploymentArchive:
    checkpoint = _validate_file_path(checkpoint_path, "checkpoint")
    class_mapping = _validate_file_path(class_mapping_path, "class mapping")

    temp_dir = Path(tempfile.mkdtemp(prefix="deepaudio-deploy-"))

    try:
        _copy_build_context(
            temp_dir=temp_dir,
            checkpoint_path=checkpoint,
            class_mapping_path=class_mapping,
        )
        _build_image(
            build_context=temp_dir,
            segment_duration=segment_duration,
            sample_rate=sample_rate,
        )

        archive_path = temp_dir / ARCHIVE_NAME
        _save_image_archive(archive_path)
        return DeploymentArchive(archive_path=archive_path, temp_dir=temp_dir)
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def _validate_file_path(path_str: str, resource_type: str) -> Path:
    path = Path(path_str)
    if not path.is_absolute():
        raise InvalidResourceError(resource_type, path_str, "path must be absolute")

    if not path.is_file():
        raise ResourceNotFoundError(resource_type, path_str)

    return path


def _copy_build_context(
    temp_dir: Path,
    checkpoint_path: Path,
    class_mapping_path: Path,
) -> None:
    if not DEPLOYMENT_DOCKERFILE.is_file():
        raise ResourceNotFoundError("deployment Dockerfile", str(DEPLOYMENT_DOCKERFILE))

    build_deployment_dir = temp_dir / "deployment"

    shutil.copytree(
        DEPLOYMENT_DIR,
        build_deployment_dir,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
    )

    pretrained_dir = build_deployment_dir / "pretrained_models"
    pretrained_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(checkpoint_path, pretrained_dir / "checkpoint.pt")
    shutil.copy2(class_mapping_path, pretrained_dir / "class_mapping.json")

def _build_image(build_context: Path, segment_duration: float, sample_rate: int) -> None:
    _run_docker_command(
        [
            *DOCKER_COMMAND,
            "build",
            "-t",
            IMAGE_TAG,
            "-f",
            "deployment/Dockerfile",
            "--build-arg",
            f"SAMPLE_RATE={sample_rate}",
            "--build-arg",
            f"SEGMENT_DURATION={segment_duration}",
            ".",
        ],
        cwd=build_context,
        action="build image",
    )


def _save_image_archive(archive_path: Path) -> None:
    _run_docker_command(
        [*DOCKER_COMMAND, "save", "-o", str(archive_path), IMAGE_TAG],
        cwd=archive_path.parent,
        action="save image archive",
    )


def _run_docker_command(command: list[str], cwd: Path, action: str) -> None:
    try:
        subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Docker is not installed or is not available on PATH") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.strip()
        stdout = exc.stdout.strip()
        details = stderr or stdout or "unknown Docker error"
        raise RuntimeError(f"Failed to {action}: {details}") from exc
