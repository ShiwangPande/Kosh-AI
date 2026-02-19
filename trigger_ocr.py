
import sys
import os
sys.path.append('/app')
from backend.workers.celery_app import celery_app

invoice_id = 'bdb96301-535c-4efd-85fc-68d7c2f3b759'
print(f"Triggering OCR for {invoice_id}")
task = celery_app.send_task("backend.workers.ocr_worker.process_invoice_ocr", args=[invoice_id])
print(f"Task ID: {task.id}")
