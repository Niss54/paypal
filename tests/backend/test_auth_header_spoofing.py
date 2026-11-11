"""Exercise deployed authentication behavior without pytest's identity shortcut."""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.mark.parametrize("role", ["Supervisor", "FinanceAdmin", "Buyer", "AutomationAdmin"])
def test_anonymous_headers_cannot_grant_roles_or_identity(monkeypatch, role):
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setenv("AUTH_ENABLED", "false")
    response = TestClient(app).get("/api/auth/me", headers={
        "X-User-ID": "SUP-CHIEF-09", "X-User-Roles": role,
        "X-Site-ID": "another-tenant",
    })
    assert response.status_code == 200
    profile = response.json()
    assert profile["user_id"] == "local-operator"
    assert role not in profile["roles"]
    assert profile["site_id"] == "plant-mumbai-01"


def test_forged_supervisor_header_cannot_reach_signoff(monkeypatch):
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setenv("AUTH_ENABLED", "false")
    response = TestClient(app).post("/api/paypal/orders/UNAUTHORIZED-ORDER/sign-off", headers={
        "X-User-ID": "SUP-CHIEF-09", "X-User-Roles": "Supervisor",
    }, json={"supervisor_id": "SUP-CHIEF-09", "notes": "Forged approval"})
    assert response.status_code == 403
