import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "shiwangpande1@gmail.com"
PASSWORD = "Password123!"

def get_token():
    url = f"{BASE_URL}/auth/login"
    payload = {"email": EMAIL, "password": PASSWORD} # Match MerchantLogin schema
    try:
        response = requests.post(url, json=payload) # Send as JSON
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        logger.error(f"Login failed: {e}")
        return None

def test_create_order(token, supplier_id, product_id):
    url = f"{BASE_URL}/orders"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "supplier_id": supplier_id,
        "items": [
            {
                "product_id": product_id,
                "description": "Test Product Order",
                "quantity": 10,
                "unit_price": 500.0
            }
        ],
        "expected_delivery_date": "2024-03-01",
        "po_number": None # Auto-generate
    }
    
    logger.info(f"Sending Order payload: {json.dumps(payload, indent=2)}")
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 201:
        logger.info("Order Created Successfully!")
        logger.info(json.dumps(response.json(), indent=2))
        return response.json()
    else:
        logger.error(f"Failed to create order: {response.status_code} - {response.text}")
        return None

if __name__ == "__main__":
    token = get_token()
    if token:
        SUPPLIER_ID = "1152b006-9f3c-45cc-b440-5a7a8d1d85e5"
        PRODUCT_ID = "e5ef0d1c-6d96-4a32-82b6-01056a414cdb"
        test_create_order(token, SUPPLIER_ID, PRODUCT_ID)
