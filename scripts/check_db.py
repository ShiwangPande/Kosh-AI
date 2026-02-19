
import os
from sqlalchemy import create_engine, text

# Hardcode to verify environment variable isn't the issue first
DB_URL = os.getenv("DATABASE_URL_SYNC", "postgresql://kosh:kosh_secret@db:5432/kosh_ai")

try:
    print(f"Connecting to {DB_URL}...")
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT count(*) FROM invoices"))
        print(f"Invoice count: {result.scalar()}")
        
        # Check specific invoice
        target_id = "7343f691-16ec-4913-8c1d-858d22c8828c"
        result = conn.execute(text(f"SELECT id, ocr_status FROM invoices WHERE id = '{target_id}'"))
        row = result.fetchone()
        if row:
            print(f"Found target invoice: {row}")
        else:
            print(f"Target invoice {target_id} NOT FOUND")
except Exception as e:
    print(f"Error: {e}")
