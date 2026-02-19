import jwt
import datetime
import requests
import time
from sqlalchemy import create_engine, text

SECRET = "leh8RC5KPTNekUEZcmr8h2PaCvpg1W_HKcx_fEpcV8w"
DATABASE_URL = "postgresql://neondb_owner:npg_6hw1VJIFzWCu@ep-sparkling-bird-aivv4fqk-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"
BASE_URL = "http://localhost:8000/api/v1"

def test_authenticated_api():
    # 1. Get Merchant ID
    engine = create_engine(DATABASE_URL)
    with engine.connect() as con:
        result = con.execute(text("SELECT id FROM merchants LIMIT 1"))
        row = result.fetchone()
        if not row:
            print("No merchants found.")
            return
        m_id = str(row[0])
    
    # 2. Generate Token
    token = jwt.encode({
        "sub": m_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)
    }, SECRET, algorithm="HS256")
    
    print(f"Generated token for merchant: {m_id}")
    
    # 3. Test API
    print("Requesting invoices...")
    headers = {"Authorization": f"Bearer {token}"}
    start = time.time()
    try:
        res = requests.get(f"{BASE_URL}/invoices", headers=headers, timeout=20)
        print(f"Status: {res.status_code} (took {time.time() - start:.2f}s)")
        if res.status_code == 200:
            print(f"Items found: {len(res.json().get('items', []))}")
        else:
            print(f"Body: {res.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_authenticated_api()
