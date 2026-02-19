"""Test the improved OCR Extraction logic."""
from backend.services.ocr_service import OCRService
import asyncio

def test_extraction():
    service = OCRService()
    
    # Test cases based on failed invoices
    test_cases = [
        """INVOICE
Camera Supplier Inc.
123 Flash St.
New York, NY 12210

Item Qty Price Total
Canon EOS R5 2 250000 500000
Sony A7IV 1 180000 180000
""",
        """Particulars  Qty  UnitPrice  Total
Organic Bread  5  45.00  225.00
Milk 1L  2  60  120
"""
    ]
    
    for i, text in enumerate(test_cases):
        print(f"--- Test Case {i+1} ---")
        items = service._extract_line_items(text)
        print(f"Extracted {len(items)} items:")
        for item in items:
            print(f"  - {item['description']}: {item['quantity']} @ {item['unit_price']} = {item['total_price']}")
        print()

if __name__ == "__main__":
    test_extraction()
