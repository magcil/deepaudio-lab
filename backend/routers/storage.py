from fastapi import APIRouter, HTTPException, status

from schemas.storage_params import PresignedItem, PresignRequest, PresignResponse
from services.storage_service import put_user_presigned_url
from storage.client import DATA_BUCKET

router = APIRouter(prefix="/storage", tags=["Storage"])


@router.post("/upload/dataset/presigned", status_code=status.HTTP_200_OK, response_model=PresignResponse)
async def get_presigned_urls_for_dataset_upload(request: PresignRequest) -> PresignResponse:
    """Generate presigned URLs for uploading dataset files to S3.

    Args:
        request (PresignRequest): Request body containing the list of file paths and the user.

    Returns:
        PresignResponse: Response containing the list of presigned URLs for each requested file path.
    """
    if not request.paths:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No file paths provided.")
    urls = []
    for path in request.paths:
        key, url = put_user_presigned_url(user=request.user, bucket=DATA_BUCKET, suffix_file_path=path)
        urls.append(PresignedItem(path=path, key=key, url=url))
    return PresignResponse(urls=urls)
