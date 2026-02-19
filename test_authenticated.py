import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
EMAIL = "shiwangpande1@gmail.com"
PASSWORD = "kosh_secret" # Assuming this is the password from previous context or default

def test_full_flow():
    # 1. Login
    print(f"Logging in as {EMAIL}...")
    try:
        login_res = requests.post(f"{BASE_URL}/auth/login", json={
            "email": EMAIL,
            "password": PASSWORD
        }, timeout=10)
        
        if login_res.status_code != 200:
            print(f"Login failed: {login_res.status_code} {login_res.text}")
            return
            
        token = login_res.json().get("access_token")
        print("Login successful.")
        
        # 2. List Invoices
        print("Fetching invoices...")
        headers = {"Authorization": f"Bearer {token}"}
        start = time.time() if 'time' in globals() else 0
        import time
        start = time.time()
        inv_res = requests.get(f"{BASE_URL}/invoices", headers=headers, timeout=15)
        
        if inv_res.status_code == 200:
            data = inv_res.json()
            print(f"Success! Found {len(data.get('items', []))} items (took {time.time() - start:.2f}s)")
        else:
            print(f"Failed to fetch invoices: {inv_res.status_code} {inv_res.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_full_flow()
