"""Test Cloudinary Connectivity."""
import cloudinary
import cloudinary.uploader
from backend.config import get_settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_upload():
    settings = get_settings()
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True
    )
    
    logger.info(f"Testing Cloudinary with cloud_name: {settings.CLOUDINARY_CLOUD_NAME}")
    
    try:
        # Small dummy upload
        result = cloudinary.uploader.upload(
            b"test content", 
            folder="test_folder",
            public_id="test_file"
        )
        logger.info(f"Upload Success: {result.get('secure_url')}")
    except Exception as e:
        logger.error(f"Upload Failed: {e}")

if __name__ == "__main__":
    test_upload()
