"""OCR processing service — abstraction over Google Vision + Tesseract fallback."""
import json
import re
from typing import Optional, Dict, List
from dataclasses import dataclass, field

from backend.config import get_settings

settings = get_settings()


@dataclass
class OCRResult:
    raw_text: str
    confidence: float
    provider: str
    line_items: List[Dict] = field(default_factory=list)
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    total_amount: Optional[float] = None
    supplier_name: Optional[str] = None



class TesseractOCR:
    """Tesseract OCR provider."""

    async def extract_text(self, file_bytes: bytes, mime_type: str = "application/pdf") -> OCRResult:
        print(f"DEBUG OCR SERVICE: mime_type={mime_type} bytes_len={len(file_bytes)}", flush=True)
        try:
            import pytesseract
            from PIL import Image
            import io

            if settings.TESSERACT_CMD:
                pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

            # Robust mime_type check
            is_pdf = "pdf" in mime_type.lower()
            
            # Fallback: Check magic bytes if PIL might fail or if it's explicitly marked as PDF
            if not is_pdf and file_bytes.startswith(b"%PDF"):
                print("DEBUG OCR SERVICE: Detected PDF header in non-PDF mime_type, forcing PDF processing", flush=True)
                is_pdf = True

            if is_pdf:
                import pdf2image
                kwargs = {}
                if settings.POPPLER_PATH:
                    kwargs["poppler_path"] = settings.POPPLER_PATH
                
                images = pdf2image.convert_from_bytes(file_bytes, **kwargs)
                texts = []
                for img in images:
                    text = pytesseract.image_to_string(img)
                    texts.append(text)
                raw_text = "\n".join(texts)
            else:
                try:
                    img = Image.open(io.BytesIO(file_bytes))
                    raw_text = pytesseract.image_to_string(img)
                except Exception as img_err:
                    # Final fallback: if PIL fails but file looks like PDF, try pdf2image
                    if file_bytes.startswith(b"%PDF"):
                        import pdf2image
                        print(f"DEBUG OCR SERVICE: PIL failed ({img_err}), but found PDF header. Trying pdf2image fallback.", flush=True)
                        kwargs = {}
                        if settings.POPPLER_PATH:
                            kwargs["poppler_path"] = settings.POPPLER_PATH
                        images = pdf2image.convert_from_bytes(file_bytes, **kwargs)
                        raw_text = "\n".join([pytesseract.image_to_string(i) for i in images])
                    else:
                        raise img_err

            # Tesseract doesn't provide a global confidence — estimate from data
            # WORKAROUND: image_to_data causes hangs on some systems. 
            # Skipping detailed confidence calculation for now.
            confidence = 0.90 
            
            return OCRResult(
                raw_text=raw_text,
                confidence=confidence,
                provider="tesseract",
            )
        except ImportError:
            raise RuntimeError("pytesseract or pdf2image not installed")
        except Exception as e:
            raise RuntimeError(f"Tesseract OCR failed: {str(e)}")


class OCRService:
    """OCR service using Tesseract."""

    def __init__(self):
        self.engine = TesseractOCR()

    async def process(self, file_bytes: bytes, mime_type: str = "application/pdf") -> OCRResult:
        """Run OCR with Tesseract."""
        result = await self.engine.extract_text(file_bytes, mime_type)

        # Parse structured data from raw text
        result.line_items = self._extract_line_items(result.raw_text)
        result.invoice_number = self._extract_invoice_number(result.raw_text)
        result.invoice_date = self._extract_invoice_date(result.raw_text)
        result.total_amount = self._extract_total(result.raw_text)
        result.supplier_name = self._extract_supplier_name(result.raw_text)

        return result

    # ── Parsing helpers ─────────────────────────────────────

    def _extract_line_items(self, text: str) -> List[Dict]:
        """Extract line items using regex heuristics."""
        items = []
        # Pattern 1: description  qty  unit_price  total
        # Handles: Item Name  2  100.00  200.00
        # Anchored to line start/end to avoid splitting description numbers
        pattern1 = r"^(.+?)\s+(\d+(?:\.\d+)?)\s+[\₹$]?\s*(\d+(?:\.\d+)?)(?:/[a-zA-Z]+)?\s+[\₹$]?\s*(\d+(?:\.\d+)?)\s*$"
        
        # Pattern 2: Item Name (price/unit) x Qty = Total
        pattern2 = r"^(.+?)\s+[\₹$]?\s*(\d+(?:\.\d+)?)(?:/[a-zA-Z]+)?\s*[xX*]\s*(\d+(?:\.\d+)?)\s*[:=]?\s*[\₹$]?\s*(\d+(?:\.\d+)?)\s*$"

        # Pattern 3: Description Price Qty Total (No 'x')
        # Handles: Service 1   $50.00/hr   4   $200.00
        pattern3 = r"^(.+?)\s+[\₹$]?\s*(\d+(?:\.\d+)?)(?:/[a-zA-Z]+)?\s+(\d+(?:\.\d+)?)\s+[\₹$]?\s*(\d+(?:\.\d+)?)\s*$"

        # Try pattern 3 first (Best match for user's invoice types)
        for match in re.finditer(pattern3, text, re.MULTILINE):
            desc = match.group(1).strip()
            # Basic filtering for headers
            if desc.lower() in ("item", "description", "product", "particulars"):
                continue
            
            try:
                items.append({
                    "description": desc,
                    "unit_price": float(match.group(2)),
                    "quantity": float(match.group(3)),
                    "total_price": float(match.group(4)),
                })
            except (ValueError, IndexError):
                continue

        # If empty, try pattern 1 (Qty first)
        if not items:
            for match in re.finditer(pattern1, text, re.MULTILINE):
                try:
                    desc = match.group(1).strip()
                    if desc.lower() in ("item", "description", "product", "particulars"): continue
                    items.append({
                        "description": desc,
                        "quantity": float(match.group(2)),
                        "unit_price": float(match.group(3)),
                        "total_price": float(match.group(4)),
                    })
                except: continue

        # If still empty, try pattern 2 (Nx format)
        if not items:
            for match in re.finditer(pattern2, text, re.MULTILINE):
                try:
                    items.append({
                        "description": match.group(1).strip(),
                        "unit_price": float(match.group(2)),
                        "quantity": float(match.group(3)),
                        "total_price": float(match.group(4)),
                    })
                except: continue

        # Pattern 4: Simple "Description Amount" (for Receipts)
        # Handles: Fee Applicable 5,000.00
        # Must be careful not to match random text. Require 2 decimal places.
        pattern4 = r"^(.+?)\s+[\₹$]?\s*([\d,]+\.\d{2})\s*$"
        
        if not items:
             for match in re.finditer(pattern4, text, re.MULTILINE):
                try:
                    desc = match.group(1).strip()
                    if len(desc) < 3: continue 
                    # Filter out Date/Total lines to avoid duplicates
                    if any(x in desc.lower() for x in ["total", "amount", "date", "receipt", "gst number"]): continue
                    
                    amt = float(match.group(2).replace(",", ""))
                    items.append({
                        "description": desc,
                        "quantity": 1.0,
                        "unit_price": amt,
                        "total_price": amt,
                    })
                except: continue

        # If STILL empty, attempt columnar extraction (vertical columns)
        if not items:
            items = self._extract_columnar_items(text)

        return items

    def _extract_columnar_items(self, text: str) -> List[Dict]:
        """Handle cases where columns are extracted as vertical blocks."""
        items = []
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        # Find column boundaries by searching for keywords
        blocks = {}
        current_block = None
        
        keywords = {
            "description": ["description", "item", "product", "particulars", "name"],
            "quantity": ["qty", "quantity", "count", "pack"],
            "unit_price": ["unit price", "price/unit", "price (", "at @", "rate", "ptr"],
            "total_price": ["total", "amount", "total (", "taxable value"],
            "batch_number": ["batch", "batch no", "lot", "batch number"],
            "expiry_date": ["expiry", "exp", "exp date", "date of expiry"],
            "hsn_code": ["hsn", "hsn code", "hsn/sac"],
            "mrp": ["mrp", "max retail price"]
        }
        
        for line in lines:
            found_key = False
            for key, kws in keywords.items():
                if any(kw == line.lower() or line.lower().startswith(kw) for kw in kws):
                    current_block = key
                    blocks[current_block] = []
                    found_key = True
                    break
            
            if not found_key and current_block:
                blocks[current_block].append(line)
        
        # If we have at least description and some numbers, try to pair them
        if "description" in blocks and len(blocks["description"]) > 0:
            count = len(blocks["description"])
            for i in range(count):
                item = {"description": blocks["description"][i]}
                
                # Helper to extract number from string like "$500.00"
                def extract_num(s):
                    m = re.search(r"(\d+(?:\.\d+)?)", s.replace(",", ""))
                    return float(m.group(1)) if m else 0.0

                if "quantity" in blocks and len(blocks["quantity"]) > i:
                    item["quantity"] = extract_num(blocks["quantity"][i])
                else:
                    item["quantity"] = 1.0 # Default
                    
                if "unit_price" in blocks and len(blocks["unit_price"]) > i:
                    item["unit_price"] = extract_num(blocks["unit_price"][i])
                elif "total_price" in blocks and len(blocks["total_price"]) > i:
                    item["unit_price"] = extract_num(blocks["total_price"][i]) / item["quantity"]
                else:
                    item["unit_price"] = 0.0
                    
                if "total_price" in blocks and len(blocks["total_price"]) > i:
                    item["total_price"] = extract_num(blocks["total_price"][i])
                else:
                    item["total_price"] = item["quantity"] * item["unit_price"]

                # Extract Pharma Fields
                if "batch_number" in blocks and len(blocks["batch_number"]) > i:
                     item["batch_number"] = blocks["batch_number"][i].strip()
                
                if "expiry_date" in blocks and len(blocks["expiry_date"]) > i:
                     # Basic cleanup, maybe parse later
                     item["expiry_date"] = blocks["expiry_date"][i].strip()
                     
                if "hsn_code" in blocks and len(blocks["hsn_code"]) > i:
                     item["hsn_code"] = blocks["hsn_code"][i].strip()
                
                if "mrp" in blocks and len(blocks["mrp"]) > i:
                     item["mrp"] = extract_num(blocks["mrp"][i])

                if item["description"] and item["unit_price"] > 0:
                    items.append(item)
                    
        return items

    def _extract_invoice_number(self, text: str) -> Optional[str]:
        patterns = [
            r"(?:Invoice|Inv|Bill)\s*(?:No|Number|#)\s*[:\-]?\s*([A-Z0-9\-/]+)",
            r"(?:INV|BILL)\s*[:\-]?\s*([A-Z0-9\-/]+)",
        ]
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return None

    def _extract_invoice_date(self, text: str) -> Optional[str]:
        # Formats: DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY
        # Added: DD Month, YYYY (e.g., 02 June, 2023)
        patterns = [
            r"(?:Date|Invoice Date|Inv Date|Transaction Date|Payment Transaction Date)\s*[:\-.]?\s*(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})",
            # Handle "Date: 02 June, 2023"
            r"(?:Date|Invoice Date|Inv Date)?\s*[:\-.]?\s*(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s,]+\d{4})",
            r"(\d{4}-\d{2}-\d{2})",
            # Loose match for DD/MM/YYYY
            r"(\d{2}[/\-\.]\d{2}[/\-\.]\d{4})", 
        ]
        
        for p in patterns:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                 # Normalize date format if needed, but for now just return the string
                 # Some cleaning might be needed (remove commas)
                 return match.group(1).replace(",", " ").strip()
        return None

    def _extract_total(self, text: str) -> Optional[float]:
        patterns = [
            r"(?:Total|Grand Total|Net Amount|Amount Due|Total Amount)\s*(?:\(.*\))?\s*[:\-]?\s*[\₹$]?\s*([\d,]+\.?\d*)",
        ]
        for p in patterns:
            match = re.search(p, text, re.IGNORECASE)
            if match:
                return float(match.group(1).replace(",", ""))
        return None

    def _extract_supplier_name(self, text: str) -> Optional[str]:
        lines = text.strip().split("\n")
        if lines:
            # Heuristic: first non-empty line is often the supplier name
            for line in lines[:5]:
                clean = line.strip()
                if clean and len(clean) > 2 and not re.match(r"^[\d\-/]+$", clean) and "invoice" not in clean.lower():
                    return clean
        return None
