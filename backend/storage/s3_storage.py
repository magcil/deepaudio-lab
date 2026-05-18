from .client import s3_client as s3


def get_presigned_url(bucket: str, key: str, expires_in: int = 3600) -> str:
    """Generate a presigned URL for GET access to an S3 object.

    Args:
        bucket: Name of the S3 bucket.
        key: Object key within the bucket.
        expires_in: URL expiry time in seconds (default 3600).

    Returns:
        Presigned URL string.
    """
    return s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires_in,
    )


def put_presigned_url(bucket: str, key: str, expires_in: int = 3600) -> str:
    """Generate a presigned URL for PUT access to an S3 object.

    Args:
        bucket: Name of the S3 bucket.
        key: Object key within the bucket.
        expires_in: URL expiry time in seconds (default 3600).
    Returns:
        Presigned URL string.
    """
    return s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expires_in,
    )


def delete_object(bucket: str, key: str) -> None:
    """Delete an object from an S3 bucket.

    Args:
        bucket: Name of the S3 bucket.
        key: Object key within the bucket.
    """
    s3.delete_object(Bucket=bucket, Key=key)


def get_object(bucket: str, key: str) -> dict:
    """Get an object from an S3 bucket.

    Args:
        bucket: Name of the S3 bucket.
        key: Object key within the bucket.
    Returns:
        Response from S3 containing the object data.
    """
    return s3.get_object(Bucket=bucket, Key=key)
