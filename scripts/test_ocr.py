"""Test OCR Worker Functionality."""
import pytesseract
from PIL import Image, ImageDraw
import io
import pdf2image
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ocr():
    logger.info("Starting OCR Test...")
    
    # 1. Test Tesseract directly with a synthetic image
    try:
        img = Image.new('RGB', (200, 100), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        d.text((10, 10), "TEST INVOICE", fill=(0, 0, 0))
        d.text((10, 40), "Item1 10 100.00 1000.00", fill=(0, 0, 0))
        
        text = pytesseract.image_to_string(img)
        logger.info(f"Tesseract raw output: '{text.strip()}'")
        if "TEST" in text.upper():
            logger.info("Tesseract basic test PASS")
        else:
            logger.warning("Tesseract basic test FAIL (empty or wrong text)")
    except Exception as e:
        logger.error(f"Tesseract test error: {e}")

    # 2. Test pdf2image if possible (needs a real PDF or bytes)
    # Skipping deep PDF test for now unless first part fails.

if __name__ == "__main__":
    test_ocr()
