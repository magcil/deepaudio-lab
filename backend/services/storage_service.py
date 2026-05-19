from storage.s3_storage import put_presigned_url


def put_user_presigned_url(user: str, bucket: str, suffix_file_path: str, expires_in: int = 3600) -> tuple[str, str]:
    """Generate a presigned PUT URL for a user-specific path in the given bucket.

    Args:
        user: Username to include in the path.
        bucket: Target bucket name, either DATA_BUCKET or CHECKPOINTS_BUCKET.
        suffix_file_path: Additional file path suffix (e.g., filename) to append after the user.
        expires_in: Time in seconds for the presigned URL to remain valid (default 3600 seconds).

    Returns:
        Tuple of (key, presigned URL) for the specified user path.
    """
    key = f"{user}/{suffix_file_path}"
    url = put_presigned_url(bucket=bucket, key=key, expires_in=expires_in)
    return key, url
