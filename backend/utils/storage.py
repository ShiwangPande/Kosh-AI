"""S3-compatible storage utility."""
import asyncio
import uuid
from typing import Optional
import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile

from backend.config import get_settings

settings = get_settings()

# ── Singleton S3 client (SC4 fix) ──────────────────────────
_s3_client = None


def get_s3_client():
    global _s3_client
    if _s3_client is None:
        kwargs = {
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
            "region_name": settings.AWS_S3_REGION,
        }
        if settings.AWS_S3_ENDPOINT_URL:
            kwargs["endpoint_url"] = settings.AWS_S3_ENDPOINT_URL
        _s3_client = boto3.client("s3", **kwargs)
    return _s3_client


def _sync_upload(key: str, content: bytes, content_type: str) -> None:
    """Synchronous S3 upload — called via asyncio.to_thread()."""
    s3 = get_s3_client()
    s3.put_object(
        Bucket=settings.AWS_S3_BUCKET,
        Key=key,
        Body=content,
        ContentType=content_type,
    )


async def upload_file_to_s3(
    file: UploadFile,
    folder: str = "invoices",
    filename: Optional[str] = None,
) -> tuple[str, str]:
    """Upload a file to S3 and return (file_url, object_key)."""
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "bin"
    key = f"{folder}/{filename or uuid.uuid4().hex}.{ext}"

    content = await file.read()

    # Secondary size check (in case file.size was unavailable earlier)
    if len(content) > settings.max_upload_bytes:
        raise ValueError(
            f"File too large ({len(content)} bytes). Max: {settings.max_upload_bytes}"
        )

    # Run sync boto3 call in thread pool to avoid blocking event loop (SC3 fix)
    await asyncio.to_thread(
        _sync_upload, key, content, file.content_type or "application/octet-stream"
    )

    if settings.AWS_S3_ENDPOINT_URL:
        url = f"{settings.AWS_S3_ENDPOINT_URL}/{settings.AWS_S3_BUCKET}/{key}"
    else:
        url = f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_S3_REGION}.amazonaws.com/{key}"

    return url, key


def delete_file_from_s3(key: str) -> bool:
    """Delete a file from S3."""
    try:
        s3 = get_s3_client()
        s3.delete_object(Bucket=settings.AWS_S3_BUCKET, Key=key)
        return True
    except ClientError:
        return False


def generate_presigned_url(key: str, expiration: int = 3600) -> str:
    """Generate a presigned URL for temporary access."""
    s3 = get_s3_client()
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.AWS_S3_BUCKET, "Key": key},
        ExpiresIn=expiration,
    )
