import requests
import json

base_url = "http://localhost:8000/api/v1"

def test_api():
    # 1. Login
    print("Logging in...")
    login_data = {"email": "shiwangpande1@gmail.com", "password": "password123"} # Trying password123
    res = requests.post(f"{base_url}/auth/login", json=login_data)
    if res.status_code != 200:
        print(f"Login failed: {res.status_code} {res.text}")
        # Try merchant1
        print("Trying merchant1@example.com...")
        login_data = {"email": "merchant1@example.com", "password": "password123"}
        res = requests.post(f"{base_url}/auth/login", json=login_data)
        if res.status_code != 200:
            print(f"Login failed for merchant1: {res.status_code}")
            return
            
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Login successful.")

    # 2. Get Invoices
    res = requests.get(f"{base_url}/invoices", headers=headers)
    if res.status_code != 200:
        print(f"Failed to get invoices: {res.status_code}")
        return
        
    items = res.json().get("items", [])
    if not items:
        print("No invoices found.")
        return
        
    test_inv = items[0]
    inv_id = test_inv["id"]
    print(f"Found Invoice ID: {inv_id}, Status: {test_inv['ocr_status']}")

    # 3. Test DELETE
    print(f"Testing DELETE /invoices/{inv_id}...")
    res = requests.delete(f"{base_url}/invoices/{inv_id}", headers=headers)
    print(f"DELETE Response: {res.status_code} {res.text}")

    # 4. Test CANCEL
    if len(items) > 1:
        test_inv = items[1]
        inv_id = test_inv["id"]
        print(f"Testing POST /invoices/{inv_id}/cancel...")
        res = requests.post(f"{base_url}/invoices/{inv_id}/cancel", headers=headers)
        print(f"CANCEL Response: {res.status_code} {res.text}")

if __name__ == "__main__":
    test_api()
