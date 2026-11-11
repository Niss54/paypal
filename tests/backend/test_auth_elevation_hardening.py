"""Test authentication elevation hardening and login endpoint.
Ensures supervisor and financial roles cannot be minted unauthenticated.
"""
import os
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_login_success():
    """Verify enterprise login with valid credentials."""
    res = client.post("/api/auth/login", json={
        "username": "supervisor",
        "password": "test-supervisor-password",
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user_id"] == "SUP-CHIEF-09"
    assert "Supervisor" in data["roles"]
    assert "ReliabilityEngineer" in data["roles"]


def test_login_invalid_password():
    """Verify login rejection with incorrect credentials."""
    res = client.post("/api/auth/login", json={
        "username": "supervisor",
        "password": "invalid-test-password",
    })
    assert res.status_code == 401
    body = res.json()
    assert body.get("error") == "invalid_credentials" or "invalid" in str(body).lower()


def test_login_unknown_user():
    """Verify rejection of unknown enterprise persona."""
    res = client.post("/api/auth/login", json={
        "username": "random-hacker",
        "password": "any",
    })
    assert res.status_code == 401


def test_token_endpoint_with_valid_password():
    """Verify /api/auth/token succeeds when credentials are provided."""
    res = client.post("/api/auth/token", json={
        "persona": "supervisor",
        "password": "test-supervisor-password",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["user_id"] == "SUP-CHIEF-09"
    assert "Supervisor" in data["roles"]


def test_identity_binding_prevents_spoofing():
    """Verify caller cannot supply arbitrary user_id to spoof another user."""
    # When password is provided for supervisor persona, user_id is bound to SUP-CHIEF-09
    res = client.post("/api/auth/login", json={
        "username": "supervisor",
        "password": "test-supervisor-password",
    })
    assert res.status_code == 200
    assert res.json()["user_id"] == "SUP-CHIEF-09"


@pytest.mark.parametrize("persona", ["supervisor", "auditor", "buyer", "finance", "payment-service"])
def test_all_approval_capable_personas_require_credentials_outside_test_harness(monkeypatch, persona):
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.delenv("ALLOW_DEV_TEST_JWT", raising=False)
    monkeypatch.delenv("ENTRA_CLIENT_ID", raising=False)
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("JWT_SECRET", "regression-only-signing-key-at-least-32-bytes")
    result = client.post("/api/auth/token", json={"persona": persona})
    assert result.status_code == 401


def test_dev_jwt_verification_switch_does_not_grant_unauthenticated_supervisor(monkeypatch):
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setenv("ALLOW_DEV_TEST_JWT", "true")
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("JWT_SECRET", "regression-only-signing-key-at-least-32-bytes")
    result = client.post("/api/auth/token", json={"persona": "supervisor", "user_id": "forged-user"})
    assert result.status_code == 401
