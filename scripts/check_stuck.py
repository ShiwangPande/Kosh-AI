
import os
import httpx
from sqlalchemy import create_engine, text

# Hardcode to verify environment variable isn't the issue first
DB_URL = os.getenv("DATABASE_URL_SYNC", "postgresql://kosh:kosh_secret@db:5432/kosh_ai")

try:
    print(f"Connecting to {DB_URL}...")
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        print("Querying for stuck invoices (ocr_status='processing')...")
        result = conn.execute(text("SELECT id, ocr_status, file_url FROM invoices WHERE ocr_status = 'processing'"))
        rows = result.fetchall()
        print(f"Found {len(rows)} stuck invoices.")
        
        for row in rows:
            invoice_id = row[0]
            status = row[1]
            url = row[2]
            
            print(f"\n--- Invoice {invoice_id} ---")
            print(f"Status: {status}")
            print(f"URL: {url}")
            
            try:
                print(f"Testing download from within container...")
                # Verify we can reach the URL
                resp = httpx.get(url, timeout=30.0, follow_redirects=True)
                print(f"Download status: {resp.status_code}")
                
                if resp.status_code == 200:
                    print(f"Download success! Size: {len(resp.content)} bytes")
                    # Check first few bytes to verify it's a PDF or Image
                    header = resp.content[:10]
                    print(f"File header: {header}")
                else:
                    print(f"Download FAILED with status {resp.status_code}")
                    print(f"Response: {resp.text[:200]}")
            except Exception as e:
                print(f"Download ERROR: {e}")
                
except Exception as e:
    print(f"Script Error: {e}")
