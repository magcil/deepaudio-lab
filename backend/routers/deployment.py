from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from services.deployment_service import build_deployment_archive

router = APIRouter(prefix="/deploy", tags=["Deployment"])


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_class=FileResponse,
    responses={
        200: {
            "content": {
                "application/octet-stream": {}
            },
            "description": "Deployment archive",
        }
    },
)
def deploy(
    checkpoint_path: str = Query(..., description="Absolute path to the .pt checkpoint on the server."),
    class_mapping_path: str = Query(..., description="Absolute path to the class_mapping.json file on the server."),
    segment_duration: float = Query(..., gt=0, description="Default segment duration used during inference."),
    sample_rate: int = Query(..., gt=0, description="Expected sample rate of the input audio."),
):
    try:
        artifact = build_deployment_archive(
            checkpoint_path=checkpoint_path,
            class_mapping_path=class_mapping_path,
            segment_duration=segment_duration,
            sample_rate=sample_rate,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return FileResponse(
        path=artifact.archive_path,
        media_type="application/octet-stream",
        filename=artifact.download_name,
        background=BackgroundTask(artifact.cleanup),
    )
