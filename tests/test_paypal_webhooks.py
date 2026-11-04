"""Unit and integration tests for PayPal Webhook Verification and Reconciliation.
Complies with Master PRD V2 Section 8.7 and Section 12.3 (WH-01, WH-02, WH-03, WH-04, WH-05).
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.database import Base
from backend.app.db.models import PayPalOrderRecord, PayPalWebhookEvent
from backend.app.services.paypal.client import PayPalClient
from backend.app.services.paypal.webhooks import PayPalWebhookService
from backend.app.services.paypal.reconciliation import PayPalReconciliationService
from backend.app.services.paypal.schemas import OrderStatus, OrderIntent, PayPalOrderResponse, PurchaseUnit, PurchaseUnitAmount


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    yield session
    session.close()


@pytest.fixture
def mock_client():
    return PayPalClient(
        client_id="test_client_id_123",
        client_secret="test_client_secret_456",
    )


@pytest.mark.asyncio
async def test_webhook_signature_verification_success(mock_client):
    service = PayPalWebhookService(mock_client, webhook_id="WH-TEST-99")
    with patch.object(mock_client, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"verification_status": "SUCCESS"}
        headers = {
            "PAYPAL-AUTH-ALGO": "SHA256withRSA",
            "PAYPAL-CERT-URL": "https://api.sandbox.paypal.com/v1/notifications/certs/CERT-1",
            "PAYPAL-TRANSMISSION-ID": "trans-123",
            "PAYPAL-TRANSMISSION-SIG": "sig-abc",
            "PAYPAL-TRANSMISSION-TIME": "2026-11-05T01:00:00Z",
        }
        body = {"id": "WH-EVT-001", "event_type": "PAYMENT.CAPTURE.COMPLETED"}
        valid = await service.verify_signature(headers, body)
        assert valid is True


@pytest.mark.asyncio
async def test_webhook_signature_verification_rejected(mock_client):
    service = PayPalWebhookService(mock_client, webhook_id="WH-TEST-99")
    with patch.object(mock_client, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {"verification_status": "FAILURE"}
        headers = {
            "PAYPAL-AUTH-ALGO": "SHA256withRSA",
            "PAYPAL-CERT-URL": "https://api.sandbox.paypal.com/v1/notifications/certs/CERT-1",
            "PAYPAL-TRANSMISSION-ID": "trans-123",
            "PAYPAL-TRANSMISSION-SIG": "sig-forged",
            "PAYPAL-TRANSMISSION-TIME": "2026-11-05T01:00:00Z",
        }
        body = {"id": "WH-EVT-FORGED", "event_type": "PAYMENT.CAPTURE.COMPLETED"}
        valid = await service.verify_signature(headers, body)
        assert valid is False


def test_webhook_idempotent_deduplication(in_memory_db, mock_client):
    service = PayPalWebhookService(mock_client)
    event_data = {
        "id": "WH-EVT-DEDUPE-01",
        "event_type": "CHECKOUT.ORDER.APPROVED",
        "resource": {"id": "ORDER-DEDUPE-01"},
    }

    # First call -> Processed
    res1 = service.process_event(in_memory_db, event_data, signature_verified=True)
    assert res1["status"] == "PROCESSED"

    # Second call with same event_id -> ALREADY_PROCESSED (idempotent no-op)
    res2 = service.process_event(in_memory_db, event_data, signature_verified=True)
    assert res2["status"] == "ALREADY_PROCESSED"


def test_webhook_capture_completed_updates_order(in_memory_db, mock_client):
    service = PayPalWebhookService(mock_client)
    # Seed an authorized order
    order = PayPalOrderRecord(
        paypal_order_id="ORDER-CAP-001",
        authorization_id="AUTH-CAP-001",
        status="AUTHORIZED",
        work_order_id="WO-CAP-001",
        predictive_event_id="EVT-01",
        equipment_tag="P-101A",
        quote_id="quote-01",
        vendor_id="apex-diagnostics",
        amount_value="450.00",
        currency_code="USD",
        create_request_id="req-create-cap",
    )
    in_memory_db.add(order)
    in_memory_db.commit()

    event_data = {
        "id": "WH-EVT-CAP-99",
        "event_type": "PAYMENT.CAPTURE.COMPLETED",
        "resource": {
            "id": "CAPTURE-SANDBOX-777",
            "links": [{"rel": "up", "href": "https://api.sandbox.paypal.com/v2/payments/authorizations/AUTH-CAP-001"}],
        },
    }

    res = service.process_event(in_memory_db, event_data, signature_verified=True)
    assert res["status"] == "PROCESSED"

    in_memory_db.refresh(order)
    assert order.status == "CAPTURED"
    assert order.capture_id == "CAPTURE-SANDBOX-777"
    assert order.captured_at is not None


def test_webhook_capture_pending_does_not_mark_complete(in_memory_db, mock_client):
    service = PayPalWebhookService(mock_client)
    order = PayPalOrderRecord(
        paypal_order_id="ORDER-PEND-001",
        capture_id="CAPTURE-PEND-001",
        status="AUTHORIZED",
        work_order_id="WO-PEND-001",
        predictive_event_id="EVT-02",
        equipment_tag="P-101A",
        quote_id="quote-02",
        vendor_id="apex-diagnostics",
        amount_value="450.00",
        create_request_id="req-create-pend",
    )
    in_memory_db.add(order)
    in_memory_db.commit()

    event_data = {
        "id": "WH-EVT-PEND-01",
        "event_type": "PAYMENT.CAPTURE.PENDING",
        "resource": {"id": "CAPTURE-PEND-001"},
    }

    res = service.process_event(in_memory_db, event_data, signature_verified=True)
    assert res["status"] == "PROCESSED"

    in_memory_db.refresh(order)
    # Master PRD V2 Rule: Must be CAPTURE_PENDING, NEVER CAPTURED!
    assert order.status == "CAPTURE_PENDING"


@pytest.mark.asyncio
async def test_reconciliation_service_sync(in_memory_db, mock_client):
    recon_service = PayPalReconciliationService(mock_client)
    order = PayPalOrderRecord(
        paypal_order_id="ORDER-RECON-001",
        status="ORDER_CREATED",
        work_order_id="WO-RECON-001",
        predictive_event_id="EVT-03",
        equipment_tag="P-101A",
        quote_id="quote-03",
        vendor_id="apex-diagnostics",
        amount_value="450.00",
        create_request_id="req-create-recon",
    )
    in_memory_db.add(order)
    in_memory_db.commit()

    fake_order_res = PayPalOrderResponse(
        id="ORDER-RECON-001",
        status=OrderStatus.APPROVED,
        intent=OrderIntent.AUTHORIZE,
        purchase_units=[
            PurchaseUnit(
                reference_id="pu-WO-RECON-001",
                amount=PurchaseUnitAmount(currency_code="USD", value="450.00"),
            )
        ],
        raw_response={
            "id": "ORDER-RECON-001",
            "status": "APPROVED",
            "purchase_units": [
                {
                    "payments": {
                        "authorizations": [{"id": "AUTH-RECON-999"}]
                    }
                }
            ],
        },
    )

    with patch.object(recon_service.order_service, "get_order", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = fake_order_res
        res = await recon_service.reconcile_order(in_memory_db, "ORDER-RECON-001")
        assert res["status"] == "RECONCILED"

        in_memory_db.refresh(order)
        assert order.authorization_id == "AUTH-RECON-999"
        assert order.status == "AUTHORIZED"
