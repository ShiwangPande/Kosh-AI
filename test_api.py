import requests
import json

def test_invoices():
    url = "http://localhost:8000/api/v1/invoices"
    # We might need a token if it's protected
    headers = {
        "Authorization": "Bearer leh8RC5KPTNekUEZcmr8h2PaCvpg1W_HKcx_fEpcV8w" # This is a JWT_SECRET_KEY, not a token... Wait.
    }
    
    print(f"Requesting {url}...")
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Content: {response.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_invoices()
