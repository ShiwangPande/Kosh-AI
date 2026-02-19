"""Cloudinary storage utility."""
import asyncio
from typing import Tuple
import cloudinary
import cloudinary.uploader
import cloudinary.utils
import httpx
import uuid
from fastapi import UploadFile

from backend.config import get_settings

settings = get_settings()

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)

def _sync_upload(content: bytes, folder: str, filename: str) -> dict:
    # Force raw for PDFs to avoid "image" transformation complexity
    resource_type = "raw" if filename.lower().endswith(".pdf") else "auto"
    
    return cloudinary.uploader.upload(
        content,
        folder=folder,
        resource_type=resource_type,
        type="upload",
        access_mode="public",
        public_id=str(uuid.uuid4())
    )

async def upload_file_to_cloudinary(file: UploadFile, folder: str = "kosh_ai_invoices", filename: str = None) -> Tuple[str, str]:
    content = await file.read()
    result = await asyncio.to_thread(_sync_upload, content, folder, filename or file.filename)
    return result.get("secure_url"), result.get("public_id")

async def delete_file_from_cloudinary(public_id: str):
    await asyncio.to_thread(cloudinary.uploader.destroy, public_id)

def get_file_bytes_from_cloudinary(public_id: str, resource_type: str = "raw") -> bytes:
    signed_url, _ = cloudinary.utils.cloudinary_url(
        public_id,
        resource_type=resource_type,
        type="upload",
        sign_url=True,
        secure=True,
    )
    with httpx.Client(timeout=60.0) as client:
        resp = client.get(signed_url)
        resp.raise_for_status()
        return resp.content
