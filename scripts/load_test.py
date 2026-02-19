"""Kosh-AI Load Testing Suite — k6-style benchmarks using Locust.

Run:   locust -f scripts/load_test.py --headless -u 100 -r 10 --run-time 2m --host http://localhost:8000
Web UI: locust -f scripts/load_test.py --host http://localhost:8000   (opens at :8089)
"""
import json
import random
import string
from locust import HttpUser, task, between, events


def random_email():
    return f"load_{''.join(random.choices(string.ascii_lowercase, k=8))}@test.com"


class AuthenticatedMerchant(HttpUser):
    """Simulates a merchant using the platform."""
    wait_time = between(1, 3)
    token = None

    def on_start(self):
        """Register + login to get JWT."""
        email = random_email()
        pw = "LoadTest123!"

        # Register
        self.client.post("/api/v1/auth/register", json={
            "email": email,
            "password": pw,
            "business_name": "LoadTest Corp",
            "phone": "+91" + "".join(random.choices(string.digits, k=10)),
        })

        # Login
        resp = self.client.post("/api/v1/auth/login", json={
            "email": email,
            "password": pw,
        })
        if resp.status_code == 200:
            self.token = resp.json().get("access_token")

    @property
    def auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(5)
    def get_dashboard(self):
        """Most common action: view dashboard data."""
        self.client.get("/api/v1/auth/me", headers=self.auth_headers, name="/api/v1/auth/me")

    @task(3)
    def list_invoices(self):
        self.client.get("/api/v1/invoices?page=1&per_page=20", headers=self.auth_headers,
                        name="/api/v1/invoices")

    @task(3)
    def list_suppliers(self):
        self.client.get("/api/v1/suppliers?page=1&per_page=20", headers=self.auth_headers,
                        name="/api/v1/suppliers")

    @task(2)
    def list_recommendations(self):
        self.client.get("/api/v1/recommendations?page=1&per_page=20", headers=self.auth_headers,
                        name="/api/v1/recommendations")

    @task(1)
    def health_check(self):
        self.client.get("/health", name="/health")

    @task(1)
    def metrics(self):
        self.client.get("/metrics", name="/metrics")


class AdminUser(HttpUser):
    """Simulates admin dashboard usage."""
    wait_time = between(2, 5)
    token = None
    weight = 1  # 1 admin per 10 merchants

    def on_start(self):
        resp = self.client.post("/api/v1/auth/login", json={
            "email": "admin@kosh.ai",
            "password": "admin123456",
        })
        if resp.status_code == 200:
            self.token = resp.json().get("access_token")

    @property
    def auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task(3)
    def get_analytics(self):
        self.client.get("/api/v1/admin/analytics", headers=self.auth_headers,
                        name="/api/v1/admin/analytics")

    @task(2)
    def get_weights(self):
        self.client.get("/api/v1/admin/weights", headers=self.auth_headers,
                        name="/api/v1/admin/weights")

    @task(2)
    def get_activity_logs(self):
        self.client.get("/api/v1/admin/logs?page=1&per_page=50", headers=self.auth_headers,
                        name="/api/v1/admin/logs")


# ── SLO Validation ────────────────────────────────────────

SLO_TARGETS = {
    "/api/v1/auth/me":           {"p95_ms": 200, "error_rate": 0.01},
    "/api/v1/invoices":          {"p95_ms": 300, "error_rate": 0.01},
    "/api/v1/suppliers":         {"p95_ms": 300, "error_rate": 0.01},
    "/api/v1/recommendations":   {"p95_ms": 300, "error_rate": 0.01},
    "/api/v1/admin/analytics":   {"p95_ms": 500, "error_rate": 0.02},
    "/health":                   {"p95_ms": 100, "error_rate": 0.001},
}


@events.quitting.add_listener
def check_slos(environment, **kwargs):
    """Validate SLOs after test run and print report."""
    stats = environment.runner.stats

    print("\n" + "=" * 70)
    print("  SLO VALIDATION REPORT")
    print("=" * 70)

    all_passed = True
    for name, targets in SLO_TARGETS.items():
        entry = stats.entries.get((name, "GET"))
        if not entry:
            print(f"  ⚠️  {name:40s}  NO DATA")
            continue

        p95 = entry.get_response_time_percentile(0.95) or 0
        total = entry.num_requests + entry.num_failures
        error_rate = entry.num_failures / total if total > 0 else 0

        latency_ok = p95 <= targets["p95_ms"]
        error_ok = error_rate <= targets["error_rate"]
        passed = latency_ok and error_ok

        status = "✅ PASS" if passed else "❌ FAIL"
        if not passed:
            all_passed = False

        print(f"  {status}  {name:40s}  "
              f"p95={p95:>6.0f}ms (target: {targets['p95_ms']}ms)  "
              f"errors={error_rate:.2%} (target: {targets['error_rate']:.1%})")

    print("=" * 70)
    if all_passed:
        print("  ✅ ALL SLOs MET")
    else:
        print("  ❌ SOME SLOs BREACHED — investigate before scaling")
    print("=" * 70 + "\n")
