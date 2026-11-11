"""HTTP boundary regressions: only verified provider events may change orders."""
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from backend.app.api import paypal
from backend.app.core.auth import AppRole, UserProfile, get_current_user
from backend.app.db.database import get_db
from backend.app.db.models import Base, PayPalOrderRecord, PayPalWebhookEvent


@pytest.fixture
def webhook_client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        order = PayPalOrderRecord(
            paypal_order_id="ORDER-WEBHOOK-SECURITY", authorization_id="AUTH-WEBHOOK-SECURITY",
            status="AUTHORIZED", work_order_id="WO-WEBHOOK-SECURITY", quote_id="Q-WEBHOOK",
            predictive_event_id="EVENT-WEBHOOK", equipment_tag="P-101A", vendor_id="VND-001",
            amount_value="450.00", currency_code="USD", create_request_id="CREATE-WEBHOOK",
            is_simulated=False,
        )
        db.add(order)
        db.commit()
        app = FastAPI()
        app.include_router(paypal.router, prefix="/api")
        app.dependency_overrides[get_db] = lambda: db
        with TestClient(app) as client:
            yield client, db, order
    engine.dispose()


def capture_event():
    return {
        "id": "WH-CAPTURE-SECURITY", "event_type": "PAYMENT.CAPTURE.COMPLETED",
        "resource": {
            "id": "CAPTURE-WEBHOOK-SECURITY",
            "amount": {"value": "450.00", "currency_code": "USD"},
            "links": [{"rel": "up", "href": "https://api-m.sandbox.paypal.com/v2/payments/authorizations/AUTH-WEBHOOK-SECURITY"}],
        },
    }


@pytest.mark.parametrize("mode", [None, "sandbox", "live"])
def test_unverified_capture_event_cannot_mark_order_paid(webhook_client, monkeypatch, mode):
    client, db, order = webhook_client
    if mode is None:
        monkeypatch.delenv("PAYPAL_MODE", raising=False)
    else:
        monkeypatch.setenv("PAYPAL_MODE", mode)
    monkeypatch.setattr(paypal.webhook_service, "verify_signature", AsyncMock(return_value=False))
    response = client.post("/api/paypal/webhook", json=capture_event())
    assert response.status_code == 401
    db.refresh(order)
    assert order.status == "AUTHORIZED"
    assert order.capture_id is None
    assert db.query(PayPalWebhookEvent).count() == 0


def test_verified_provider_capture_event_is_processed(webhook_client, monkeypatch):
    client, db, order = webhook_client
    monkeypatch.setattr(paypal.webhook_service, "verify_signature", AsyncMock(return_value=True))
    response = client.post("/api/paypal/webhook", json=capture_event())
    assert response.status_code == 200
    db.refresh(order)
    assert order.status == "CAPTURED"
    assert order.capture_id == "CAPTURE-WEBHOOK-SECURITY"
    assert db.query(PayPalWebhookEvent).one().signature_verified is True


@pytest.mark.parametrize("event_type", ["CHECKOUT.ORDER.APPROVED", "PAYMENT.CAPTURE.COMPLETED"])
def test_simulator_never_mutates_real_order_or_claims_signature(webhook_client, event_type):
    client, db, order = webhook_client
    order.status = "ORDER_CREATED"
    order.capture_id = order.paypal_order_id
    db.commit()
    response = client.post("/api/paypal/webhook/simulate-test", params={
        "event_type": event_type, "order_id": order.paypal_order_id,
    })
    assert response.status_code == 200
    db.refresh(order)
    assert order.status == "ORDER_CREATED"
    event = db.query(PayPalWebhookEvent).one()
    assert event.signature_verified is False
    assert event.status == "SIMULATED"
    assert response.json()["result"]["status"] == "SIMULATED"


def test_supervisor_cannot_override_identity_when_auth_disabled(webhook_client, monkeypatch):
    client, db, order = webhook_client
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setenv("AUTH_ENABLED", "false")
    order.requester_user_id = "same-user"
    db.commit()
    client.app.dependency_overrides[get_current_user] = lambda: UserProfile(
        user_id="same-user", name="Bound user", roles=[AppRole.Supervisor.value],
    )
    response = client.post(f"/api/paypal/orders/{order.paypal_order_id}/sign-off", json={
        "supervisor_id": "spoofed-other-user",
    })
    assert response.status_code == 403
    db.refresh(order)
    assert order.reviewer_user_id is None


def test_requester_cannot_override_identity_when_auth_disabled(webhook_client, monkeypatch):
    client, db, _ = webhook_client
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    monkeypatch.setenv("AUTH_ENABLED", "false")
    client.app.dependency_overrides[get_current_user] = lambda: UserProfile(
        user_id="bound-requester", name="Bound user", roles=[AppRole.ProcurementAgent.value],
    )
    response = client.post("/api/paypal/orders", json={
        "quote_id": "Q-2026-001", "actor": "spoofed-requester", "is_simulation": True,
    })
    assert response.status_code == 201
    saved = db.query(PayPalOrderRecord).filter_by(paypal_order_id=response.json()["paypal_order_id"]).one()
    assert saved.requester_user_id == "bound-requester"
