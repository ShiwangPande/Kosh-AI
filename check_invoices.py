from backend.workers.ocr_worker import SyncSession
from backend.models.models import Invoice

session = SyncSession()
invoices = session.query(Invoice).all()

print(f"{'ID':<40} | {'Status':<15} | {'Provider':<15}")
print("-" * 75)
for inv in invoices:
    print(f"{str(inv.id):<40} | {inv.ocr_status:<15} | {inv.ocr_provider or 'N/A':<15}")

session.close()
