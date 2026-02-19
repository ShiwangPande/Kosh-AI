import urllib.request
import json

def test_compare():
    base_url = "http://localhost:8000/api/v1/invoices"
    invoice_id = "3760446e-8608-42e0-8974-bec52f7f2f47"
    
    endpoints = [
        {"name": "Cancel (POST)", "url": f"{base_url}/{invoice_id}/cancel", "method": "POST", "data": {}},
        {"name": "Cancel (GET)", "url": f"{base_url}/{invoice_id}/cancel", "method": "GET"},
        {"name": "Verify (POST)", "url": f"{base_url}/{invoice_id}/verify", "method": "POST", "data": {"corrections": []}},
        {"name": "Verify (GET)", "url": f"{base_url}/{invoice_id}/verify", "method": "GET"},
    ]
    
    for ep in endpoints:
        print(f"Testing {ep['name']} ({ep['method']} {ep['url']})...")
        data = json.dumps(ep.get("data", {})).encode() if ep["method"] == "POST" else None
        req = urllib.request.Request(ep["url"], data=data, method=ep["method"])
        if ep["method"] == "POST":
            req.add_header("Content-Type", "application/json")
        
        try:
            with urllib.request.urlopen(req) as res:
                print(f"  Result: Success ({res.getcode()})")
        except urllib.error.HTTPError as e:
            print(f"  Result: HTTP {e.code}")
        except Exception as e:
            print(f"  Result: Error {e}")
        print("-" * 20)

if __name__ == "__main__":
    test_compare()
