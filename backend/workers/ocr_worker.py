"""OCR processing Celery worker.

Pipeline:
1. Fetch file from S3 (with circuit breaker)
2. Run OCR (Google Vision -> Tesseract fallback, with circuit breaker)
3. Validate OCR output (confidence scoring + data quality checks)
4. Parse line items + normalize SKUs
5. Route: auto-accept / verification queue / reject
6. Compute value scores + generate recommendations
7. Update invoice record
8. On terminal failure -> dead letter queue
"""
import logging
import time
import asyncio
from datetime import datetime

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.workers.celery_app import celery_app
from backend.config import get_settings
from backend.database import async_session_factory
from backend.models.models import Invoice, InvoiceItem, Supplier
from backend.services.ocr_service import OCRService
from backend.services.sku_service import create_or_match_product
from backend.services.comparison_engine import generate_recommendations
from backend.services.validation_pipeline import (
    validate_invoice_data,
    validate_line_item,
    CONFIDENCE_THRESHOLDS,
)
from backend.services.validation_pipeline import enqueue_for_verification
from backend.utils.failure_handler import (
    OCR_RETRY_POLICY,
    dlq,
    ocr_circuit,
    s3_circuit,
    TaskTimeout,
)
from backend.utils.observability import inc_ocr_metric, observe_histogram, inc_simple
from backend.utils.cloudinary_storage import get_file_bytes_from_cloudinary

settings = get_settings()
logger = logging.getLogger(__name__)

# ── Task timeout (5 minutes per invoice) ───────────────────
OCR_TASK_TIMEOUT = 300  # seconds


async def process_invoice_ocr_async(invoice_id: str, retry_count: int, task_id: str):
    """Async implementation of the OCR pipeline."""
    start_time = time.time()
    
    async with async_session_factory() as session:
        try:
            # 1. Fetch invoice
            result = await session.execute(select(Invoice).where(Invoice.id == invoice_id))
            invoice = result.scalar_one_or_none()
            
            if not invoice:
                logger.error(f"Invoice {invoice_id} not found")
                return {"status": "error", "detail": "Invoice not found"}

            # Update status
            invoice.ocr_status = "processing"
            await session.commit() 
            # Commit immediately so status is visible

            # 2. Fetch file from Cloudinary
            try:
                public_id = invoice.file_key
                
                # Determine resource type
                if "/image/upload/" in invoice.file_url:
                    resource_type = "image"
                elif "/video/upload/" in invoice.file_url:
                    resource_type = "video"
                elif "/raw/upload/" in invoice.file_url:
                    resource_type = "raw"
                else:
                    resource_type = "raw" 

                ext = invoice.file_url.split('.')[-1].lower() if '.' in invoice.file_url else ""
                if ext == "pdf":
                    resource_type = "raw"
                elif ext in ["jpg", "jpeg", "png", "webp"]:
                    resource_type = "image"

                # Note: get_file_bytes_from_cloudinary is synchronous blocking I/O
                # Ideally this should be async, but for now we run it. 
                # If it blocks too long, we might need run_in_executor.
                # Assuming it's fast enough or we accept blocking the thread for this HTTP call.
                # To be improved: Make get_file_bytes_from_cloudinary async.
                loop = asyncio.get_running_loop()
                file_bytes = await loop.run_in_executor(
                    None, 
                    get_file_bytes_from_cloudinary, 
                    public_id, 
                    resource_type
                )
                
                content_type = "application/pdf" if (resource_type == "raw" or ext == "pdf") else "image/jpeg"
                
                logger.info(f"Fetched {len(file_bytes)} bytes. Type: {content_type}")
                s3_circuit.record_success()
            except Exception as e:
                s3_circuit.record_failure()
                raise RuntimeError(f"File fetch failed: {e}") from e

            # 3. Run OCR
            if not ocr_circuit.can_execute():
                raise RuntimeError("OCR circuit breaker is OPEN")

            try:
                ocr_service = OCRService()
                ocr_result = await ocr_service.process(file_bytes, content_type)
                ocr_circuit.record_success()
            except Exception as e:
                ocr_circuit.record_failure()
                raise RuntimeError(f"OCR processing failed: {e}") from e

            # Update invoice with OCR results
            # We need to re-fetch invoice or just update the object attached to session
            # It's attached to session so we can modify it.
            invoice.ocr_raw_text = ocr_result.raw_text
            invoice.ocr_confidence = ocr_result.confidence
            invoice.ocr_provider = ocr_result.provider
            invoice.invoice_number = ocr_result.invoice_number or invoice.invoice_number
            invoice.total_amount = ocr_result.total_amount or invoice.total_amount

            # Try to match supplier
            if ocr_result.supplier_name and not invoice.supplier_id:
                try:
                    s_result = await session.execute(
                        select(Supplier).where(Supplier.name.ilike(f"%{ocr_result.supplier_name}%"))
                    )
                    supplier = s_result.scalar_one_or_none()
                    
                    if supplier:
                        invoice.supplier_id = supplier.id
                    else:
                        logger.info(f"Auto-creating supplier: {ocr_result.supplier_name}")
                        new_supplier = Supplier(
                            name=ocr_result.supplier_name,
                            is_approved=False,
                            category="Uncategorized"
                        )
                        session.add(new_supplier)
                        await session.flush()
                        invoice.supplier_id = new_supplier.id
                except Exception as e:
                    logger.error(f"Supplier match failed: {e}")

            # 4. Validate OCR quality
            # Commit preliminary data first
            await session.commit() 
            
            validation_report = validate_invoice_data(
                ocr_confidence=ocr_result.confidence,
                line_items=ocr_result.line_items,
                total_amount=ocr_result.total_amount,
            )

            logger.info(
                f"Invoice {invoice_id} validation: "
                f"quality={validation_report['overall_quality']:.2f}, "
                f"action={validation_report['action']}"
            )

            if validation_report["action"] == "reject":
                 # Handle rejection logic here if needed
                 pass

            # 5. Process line items
            # Clear existing items for idempotency
            await session.execute(delete(InvoiceItem).where(InvoiceItem.invoice_id == invoice.id))

            for i, item_data in enumerate(ocr_result.line_items):
                is_valid, issues, item_quality = validate_line_item(item_data)

                product, confidence = await create_or_match_product(
                    raw_description=item_data["description"],
                    db=session,
                )

                # Date parsing helper
                def parse_expiry(date_str):
                    if not date_str: return None
                    try:
                        from dateutil import parser
                        dt = parser.parse(date_str)
                        return dt.date()
                    except:
                        return None

                inv_item = InvoiceItem(
                    invoice_id=invoice.id,
                    product_id=product.id,
                    raw_description=item_data["description"],
                    quantity=item_data.get("quantity"),
                    unit_price=item_data.get("unit_price"),
                    total_price=item_data.get("total_price"),
                    matched_sku=product.sku_code,
                    match_confidence=confidence,
                    batch_number=item_data.get("batch_number"),
                    expiry_date=parse_expiry(item_data.get("expiry_date")),
                    hsn_code=item_data.get("hsn_code"),
                    mrp=item_data.get("mrp"),
                )
                session.add(inv_item)

            await session.commit()

            # 6. Recommendations & Routing
            rec_count = 0
            if validation_report["action"] == "auto_accept" and invoice.merchant_id:
                recs = await generate_recommendations(
                    db=session,
                    merchant_id=invoice.merchant_id,
                    invoice_id=invoice.id,
                )
                rec_count = len(recs)
                inc_simple("recommendations_generated_total", rec_count)
            
            elif validation_report["action"] == "needs_review":
                await enqueue_for_verification(session, invoice.id, validation_report)

            # 7. Final Status Update
            final_status = "completed" if validation_report["action"] == "auto_accept" else "needs_review"
            
            # Using update statement to ensure we don't conflict with other updates
            await session.execute(
                update(Invoice)
                .where(Invoice.id == invoice_id)
                .values(
                    ocr_status=final_status,
                    processed_at=datetime.utcnow()
                )
            )
            await session.commit()

            # Metrics
            duration = time.time() - start_time
            inc_ocr_metric("completed")
            observe_histogram("ocr_processing_seconds", duration)
            inc_simple("invoice_uploads_total")

            return {
                "status": validation_report["action"],
                "invoice_id": invoice_id,
                "recommendations_count": rec_count,
            }

        except Exception as e:
            await session.rollback()
            raise e


@celery_app.task(
    name="backend.workers.ocr_worker.process_invoice_ocr",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
    reject_on_worker_lost=True,
)
def process_invoice_ocr(self, invoice_id: str):
    """Sync wrapper for async OCR pipeline."""
    logger.info(f"Processing OCR for invoice {invoice_id} (attempt {self.request.retries + 1})")
    
    try:
        asyncio.run(process_invoice_ocr_async(invoice_id, self.request.retries, self.request.id))
    except Exception as e:
        logger.exception(f"OCR processing failed for invoice {invoice_id}: {e}")
        
        # Async cleanup/failure status update in a separate run
        async def mark_failure():
             async with async_session_factory() as session:
                await session.execute(
                    update(Invoice)
                    .where(Invoice.id == invoice_id)
                    .values(ocr_status="failed")
                )
                await session.commit()
        
        try:
            asyncio.run(mark_failure())
        except Exception:
            pass

        # Retry logic
        attempt = self.request.retries
        if OCR_RETRY_POLICY.should_retry(attempt, e):
            delay = OCR_RETRY_POLICY.get_delay(attempt)
            inc_ocr_metric("retried")
            raise self.retry(exc=e, countdown=delay, max_retries=OCR_RETRY_POLICY.max_retries)
        else:
            inc_ocr_metric("failed")
            inc_simple("dlq_messages_total")
            dlq.push(
                task_name="backend.workers.ocr_worker.process_invoice_ocr",
                task_args={"invoice_id": invoice_id},
                error=str(e),
                retry_count=attempt,
                original_id=self.request.id,
            )
