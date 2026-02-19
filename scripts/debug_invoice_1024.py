
import asyncio
from backend.services.ocr_service import OCRService
from backend.database import async_session_factory
from backend.models.models import Invoice
from sqlalchemy import select

async def debug_invoice():
    service = OCRService()
    async with async_session_factory() as db:
        result = await db.execute(
            select(Invoice).where(Invoice.invoice_number == '1024').limit(1)
        )
        invoice = result.scalar_one_or_none()
        if not invoice:
            print("Invoice 1024 not found")
            return
        
        print(f"--- Raw Text for 1024 ---")
        print(invoice.ocr_raw_text)
        print(f"--- End Raw Text ---")
        
        items = service._extract_line_items(invoice.ocr_raw_text)
        print(f"Extracted {len(items)} items.")
        
        import json
        with open("items_1024.json", "w") as f:
            json.dump(items, f, indent=2)
        print("Results saved to items_1024.json")

if __name__ == "__main__":
    asyncio.run(debug_invoice())
