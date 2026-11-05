"""Unit tests verifying API error handling correctness and information disclosure defenses.
Satisfies Section 3.5 & Threat Model in KINETIXRAG_PAYPAL_HACKATHON_MASTER_PRD_V2.md.
"""
import pytest
from fastapi import APIRouter, HTTPException
from fastapi.testclient import TestClient

from backend.app.main import app

test_router = APIRouter(prefix="/test-errors")

@test_router.get("/raise-500")
def route_raise_500():
    raise HTTPException(status_code=500, detail="Database connection degraded")

@test_router.get("/unhandled-exception")
def route_unhandled_exception():
    raise RuntimeError("Unexpected simulated internal crash with sensitive /etc/shadow or credentials")

app.include_router(test_router)
client = TestClient(app, raise_server_exceptions=False)


def test_http_exception_500_preserves_status_code():
    """Verify that a 500 HTTPException returns HTTP 500, never converting to HTTP 200."""
    res = client.get("/test-errors/raise-500")
    assert res.status_code == 500
    data = res.json()
    assert data.get("error") == "Database connection degraded"


def test_unhandled_exception_returns_500_sanitized():
    """Verify that unhandled exceptions return HTTP 500 without leaking stack traces or internal secrets."""
    res = client.get("/test-errors/unhandled-exception")
    assert res.status_code == 500
    data = res.json()
    assert data.get("error") == "internal_error"
    assert "error_id" in data
    # Invariant: Traceback must never be exposed to public clients
    assert "traceback" not in data
    assert "sensitive" not in res.text
