import sys
import os
import uuid
from jose import jwt
from datetime import datetime, timedelta
import requests

# Add current dir to path to import backend
sys.path.insert(0, os.getcwd())

from backend.config import get_settings
settings = get_settings()

def create_access_token(sub: str, role: str):
    expire = datetime.utcnow() + timedelta(minutes=30)
    payload = {"sub": sub, "role": role, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def test_api():
    with open("reproduction_results.txt", "w") as f:
        try:
            # 1. Get ID from DB
            from sqlalchemy import create_engine
            from sqlalchemy.orm import sessionmaker
            from backend.models.models import Merchant, Invoice
            
            engine = create_engine(settings.DATABASE_URL_SYNC)
            Session = sessionmaker(bind=engine)
            session = Session()
            
            merchant = session.query(Merchant).filter(Merchant.email == "shiwangpande1@gmail.com").first()
            if not merchant:
                f.write("Merchant not found.\n")
                return
                
            f.write(f"Merchant ID: {merchant.id}\n")
            token = create_access_token(str(merchant.id), merchant.role)
            headers = {"Authorization": f"Bearer {token}"}
            
            # 2. Get an invoice ID
            invoice = session.query(Invoice).filter(Invoice.merchant_id == merchant.id).first()
            if not invoice:
                f.write("No invoices found for this merchant.\n")
                invoice = session.query(Invoice).first()
                if not invoice:
                    f.write("No invoices at all.\n")
                    return

            f.write(f"Testing with Invoice ID: {invoice.id}, Status: {invoice.ocr_status}\n")
            
            base_url = "http://localhost:8000/api/v1"
            
            # 3. Test DELETE
            f.write(f"Testing DELETE {base_url}/invoices/{invoice.id}...\n")
            res = requests.delete(f"{base_url}/invoices/{invoice.id}", headers=headers)
            f.write(f"DELETE Response: {res.status_code} {res.text}\n")
            
            # 4. Test CANCEL
            f.write(f"Testing POST {base_url}/invoices/{invoice.id}/cancel...\n")
            res = requests.post(f"{base_url}/invoices/{invoice.id}/cancel", headers=headers)
            f.write(f"CANCEL Response: {res.status_code} {res.text}\n")
            
            session.close()
        except Exception as e:
            f.write(f"Error during reproduction: {e}\n")

if __name__ == "__main__":
    test_api()
