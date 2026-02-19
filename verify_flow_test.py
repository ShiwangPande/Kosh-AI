
import httpx
import asyncio
from uuid import UUID

BASE_URL = "http://localhost:8000/api/v1"
INVOICE_ID = "1dac016e-8608-42e0-8974-bec52f7f2f47"
ITEM_ID = "64fa1b55-b93c-489d-8060-d3d441229c15"

async def verify_flow():
    # 1. Login to get token
    async with httpx.AsyncClient() as client:
        login_res = await client.post(f"{BASE_URL}/auth/login", json={
            "email": "admin@kosh.ai",
            "password": "admin123456"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Call verify endpoint
        payload = {
            "corrections": [
                {
                    "item_id": ITEM_ID,
                    "description": "VERIFIED: set of pedal arms",
                    "quantity": 10.0,
                    "unit_price": 450.0,
                    "total_price": 4500.0
                }
            ]
        }
        print(f"Verifying invoice {INVOICE_ID}...")
        res = await client.post(f"{BASE_URL}/invoices/{INVOICE_ID}/verify", json=payload, headers=headers)
        print(f"Status: {res.status_code}")
        print(res.json())

        # 3. Check final status
        inv_res = await client.get(f"{BASE_URL}/invoices/{INVOICE_ID}", headers=headers)
        print(f"New Status: {inv_res.json()['ocr_status']}")

if __name__ == "__main__":
    asyncio.run(verify_flow())
