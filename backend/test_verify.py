import urllib.request
import json
import sys

def test_verify():
    url = "http://localhost:8000/api/v1/invoices/3760446e-8608-42e0-8974-bec52f7f2f47/verify"
    data = json.dumps({"corrections": []}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    
    try:
        with urllib.request.urlopen(req) as res:
            print(f"Status: {res.getcode()}")
    except urllib.error.HTTPError as e:
        print(f"HTTP Status: {e.code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_verify()
