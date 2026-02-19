"""Test script for Kosh-AI API endpoints."""
import requests
import json
import sys
import os

BASE_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")
ACCESS_TOKEN = None


def pprint(label: str, response):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"  {response.request.method} {response.url}")
    print(f"  Status: {response.status_code}")
    print(f"{'='*60}")
    try:
        print(json.dumps(response.json(), indent=2))
    except Exception:
        print(response.text[:500])


def auth_headers():
    return {"Authorization": f"Bearer {ACCESS_TOKEN}"} if ACCESS_TOKEN else {}


def test_health():
    r = requests.get(f"{BASE_URL.replace('/api/v1', '')}/health")
    pprint("Health Check", r)
    assert r.status_code == 200


def test_register():
    r = requests.post(f"{BASE_URL}/auth/register", json={
        "email": "test@kosh.ai",
        "password": "testpassword123",
        "business_name": "Test Merchant",
        "phone": "+919999999999",
    })
    pprint("Register", r)
    return r


def test_login():
    global ACCESS_TOKEN
    r = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "test@kosh.ai",
        "password": "testpassword123",
    })
    pprint("Login", r)
    if r.status_code == 200:
        ACCESS_TOKEN = r.json()["access_token"]
    return r


def test_get_me():
    r = requests.get(f"{BASE_URL}/auth/me", headers=auth_headers())
    pprint("Get Me", r)
    return r


def test_create_supplier():
    r = requests.post(f"{BASE_URL}/suppliers", json={
        "name": "Test Supplier Inc",
        "contact_person": "John Doe",
        "email": "john@testsupplier.com",
        "phone": "+919888888888",
        "category": "Electronics",
        "city": "Bangalore",
        "credit_terms": 30,
        "avg_delivery_days": 3,
        "reliability_score": 0.8,
    }, headers=auth_headers())
    pprint("Create Supplier", r)
    return r


def test_list_suppliers():
    r = requests.get(f"{BASE_URL}/suppliers", params={
        "approved_only": "false",
    }, headers=auth_headers())
    pprint("List Suppliers", r)
    return r


def test_list_invoices():
    r = requests.get(f"{BASE_URL}/invoices", headers=auth_headers())
    pprint("List Invoices", r)
    return r


def test_list_recommendations():
    r = requests.get(f"{BASE_URL}/recommendations", headers=auth_headers())
    pprint("List Recommendations", r)
    return r


def test_admin_login():
    global ACCESS_TOKEN
    r = requests.post(f"{BASE_URL}/auth/login", json={
        "email": "admin@kosh.ai",
        "password": "admin123456",
    })
    pprint("Admin Login", r)
    if r.status_code == 200:
        ACCESS_TOKEN = r.json()["access_token"]
    return r


def test_admin_analytics():
    r = requests.get(f"{BASE_URL}/admin/analytics", headers=auth_headers())
    pprint("Admin Analytics", r)
    return r


def test_admin_weights():
    r = requests.get(f"{BASE_URL}/admin/weights", headers=auth_headers())
    pprint("Admin Weights", r)
    return r


def test_admin_logs():
    r = requests.get(f"{BASE_URL}/admin/logs", headers=auth_headers())
    pprint("Admin Logs", r)
    return r


def main():
    print("\n🧪 Kosh-AI API Test Suite")
    print(f"   Base URL: {BASE_URL}\n")

    tests = [
        ("Health Check", test_health),
        ("Register Merchant", test_register),
        ("Login Merchant", test_login),
        ("Get Profile", test_get_me),
        ("Create Supplier", test_create_supplier),
        ("List Suppliers", test_list_suppliers),
        ("List Invoices", test_list_invoices),
        ("List Recommendations", test_list_recommendations),
        ("Admin Login", test_admin_login),
        ("Admin Analytics", test_admin_analytics),
        ("Admin Weights", test_admin_weights),
        ("Admin Logs", test_admin_logs),
    ]

    passed = 0
    failed = 0

    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"\n❌ FAILED: {name} — {e}")
            failed += 1

    print(f"\n\n{'='*60}")
    print(f"  Results: {passed} passed, {failed} failed")
    print(f"{'='*60}\n")

    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
