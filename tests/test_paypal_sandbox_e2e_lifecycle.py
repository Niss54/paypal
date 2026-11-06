"""
End-to-end live sandbox lifecycle test:
Order Create → HATEOAS Approval Link → Retrieve → Verify Intent
Runs against api-m.sandbox.paypal.com with real credentials.
Separated from mocked unit tests to ensure absolute integration truthfulness.

FIX 1 from Battle Plan: Proves full PayPal Orders v2 lifecycle authenticity.
"""
import os
import socket
import pytest
from dotenv import load_dotenv

load_dotenv()

from backend.app.services.paypal.client import PayPalClient
from backend.app.services.paypal.orders import PayPalOrderService
from backend.app.services.paypal.authorization import PayPalAuthorizationService

LIVE_KEYS_CONFIGURED = bool(
    os.getenv("PAYPAL_CLIENT_ID")
    and os.getenv("PAYPAL_CLIENT_SECRET")
    and "your_paypal" not in os.getenv("PAYPAL_CLIENT_ID", "").lower()
)


def _is_paypal_sandbox_reachable() -> bool:
    if not LIVE_KEYS_CONFIGURED:
        return False
    try:
        socket.getaddrinfo("api-m.sandbox.paypal.com", 443)
        return True
    except Exception:
        return False


skip_if_no_live_keys = pytest.mark.skipif(
    not _is_paypal_sandbox_reachable(),
    reason="PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET required and api-m.sandbox.paypal.com must be reachable",
)


@skip_if_no_live_keys
@pytest.mark.asyncio
async def test_live_e2e_order_create_with_hateoas_approval_link():
    """Verify full Order v2 creation returns real PayPal Order ID and genuine HATEOAS approval URL."""
    client = PayPalClient()
    orders = PayPalOrderService(client=client)

    order = await orders.create_order(
        amount_value="1.00",
        currency_code="USD",
        work_order_id="WO-E2E-LIFECYCLE-TEST",
        quote_id="Q-E2E-LIFECYCLE",
        description="E2E Lifecycle Verification (Battle Plan FIX 1)",
    )

    # Real PayPal Order ID must be non-empty and substantial
    assert order.id is not None
    assert len(order.id) >= 10
    assert not order.id.startswith("SIM-")
    assert not order.id.startswith("mock_")

    # Intent must be AUTHORIZE (not CAPTURE)
    assert order.intent.value == "AUTHORIZE"

    # Status must be CREATED or SAVED (not already COMPLETED)
    assert order.status.value in ("CREATED", "SAVED")

    # HATEOAS approval link must exist and point to sandbox
    approve_url = None
    for link in (order.links or []):
        if link.rel in ("approve", "payer-action"):
            approve_url = link.href
    assert approve_url is not None, "PayPal must return an approve/payer-action HATEOAS link"
    assert "sandbox.paypal.com" in approve_url, "Approval URL must point to PayPal Sandbox"

    # Self link must exist for order retrieval
    self_url = None
    for link in (order.links or []):
        if link.rel == "self":
            self_url = link.href
    assert self_url is not None, "PayPal must return a self HATEOAS link for order retrieval"


@skip_if_no_live_keys
@pytest.mark.asyncio
async def test_live_e2e_order_retrieval_matches_creation():
    """Verify that a created order can be retrieved and all fields match."""
    client = PayPalClient()
    orders = PayPalOrderService(client=client)

    # Create
    created = await orders.create_order(
        amount_value="450.00",
        currency_code="USD",
        work_order_id="WO-2026-IMS-001",
        quote_id="Q-2026-001",
        description="Evidence-Gated Bearing Replacement (E2E Retrieval Test)",
    )

    # Retrieve
    retrieved = await orders.get_order(created.id)

    assert retrieved.id == created.id
    assert retrieved.intent.value == "AUTHORIZE"
    assert retrieved.status.value in ("CREATED", "SAVED")

    # Verify purchase unit amount matches
    raw = retrieved.raw_response
    pus = raw.get("purchase_units", [])
    assert len(pus) >= 1
    assert pus[0]["amount"]["value"] == "450.00"
    assert pus[0]["amount"]["currency_code"] == "USD"


@skip_if_no_live_keys
@pytest.mark.asyncio
async def test_live_e2e_idempotency_key_produces_stable_order():
    """Verify that the same idempotency key returns the same PayPal Order ID on retry."""
    client = PayPalClient()
    orders = PayPalOrderService(client=client)

    idempotency_key = "e2e-idempotency-test-key-fixed-2026"

    order1 = await orders.create_order(
        amount_value="100.00",
        currency_code="USD",
        work_order_id="WO-IDEMPOTENCY",
        quote_id="Q-IDEMPOTENCY",
        description="Idempotency Key Verification",
        idempotency_key=idempotency_key,
    )

    order2 = await orders.create_order(
        amount_value="100.00",
        currency_code="USD",
        work_order_id="WO-IDEMPOTENCY",
        quote_id="Q-IDEMPOTENCY",
        description="Idempotency Key Verification",
        idempotency_key=idempotency_key,
    )

    # PayPal should return the same order ID for the same idempotency key
    assert order1.id == order2.id


@skip_if_no_live_keys
@pytest.mark.asyncio
async def test_live_e2e_multi_currency_order_usd_only():
    """Verify PayPal creates USD orders correctly and amount is preserved exactly."""
    client = PayPalClient()
    orders = PayPalOrderService(client=client)

    amount = "250.50"
    order = await orders.create_order(
        amount_value=amount,
        currency_code="USD",
        work_order_id=f"WO-AMT-{amount.replace('.', '')}",
        quote_id=f"Q-AMT-{amount.replace('.', '')}",
        description=f"Amount precision test: ${amount}",
    )
    assert order.id
    # Query back with get_order to verify purchase_units amount and currency
    queried = await orders.get_order(order.id)
    raw = queried.raw_response
    pus = raw.get("purchase_units", [])
    assert len(pus) >= 1
    assert pus[0]["amount"]["value"] == amount
    assert pus[0]["amount"]["currency_code"] == "USD"
