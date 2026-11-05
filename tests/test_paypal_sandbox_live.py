"""Live integration tests running against official PayPal Developer Sandbox endpoints.
Requires PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET in the environment.
Separated cleanly from mocked unit test suites to ensure absolute test truthfulness.
"""
import os
import pytest
from dotenv import load_dotenv

load_dotenv()

from backend.app.services.paypal.client import PayPalClient
from backend.app.services.paypal.orders import PayPalOrderService

LIVE_KEYS_CONFIGURED = bool(
    os.getenv("PAYPAL_CLIENT_ID")
    and os.getenv("PAYPAL_CLIENT_SECRET")
    and "your_paypal" not in os.getenv("PAYPAL_CLIENT_ID", "").lower()
)

skip_if_no_live_keys = pytest.mark.skipif(
    not LIVE_KEYS_CONFIGURED,
    reason="PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET required for live sandbox tests",
)


@skip_if_no_live_keys
@pytest.mark.asyncio
async def test_live_sandbox_oauth2_token():
    """Verify live OAuth2 client credentials token acquisition against api-m.sandbox.paypal.com."""
    client = PayPalClient()
    token = await client.get_access_token()
    assert token is not None
    assert len(token) > 30
    assert not token.startswith("mock_")
    assert not token.startswith("sim_")


@skip_if_no_live_keys
@pytest.mark.asyncio
async def test_live_sandbox_order_creation_and_retrieval():
    """Verify creating a real Order v2 in Sandbox with intent: AUTHORIZE and retrieving it."""
    client = PayPalClient()
    orders_service = PayPalOrderService(client=client)

    # Create real sandbox order for $450.00 USD
    order_res = await orders_service.create_order(
        amount_value="450.00",
        currency_code="USD",
        work_order_id="WO-2026-IMS-001",
        quote_id="Q-2026-001",
        description="Emergency Slurry Pump P-101A Bearing Replacement",
    )

    assert order_res is not None
    order_id = order_res.id
    assert order_id is not None
    assert len(order_id) >= 10
    assert order_res.status in ("CREATED", "SAVED")
    assert order_res.intent.value == "AUTHORIZE"

    # Retrieve the order directly from PayPal
    retrieved = await orders_service.get_order(order_id)
    assert retrieved.id == order_id
    assert retrieved.intent.value == "AUTHORIZE"
    assert len(retrieved.purchase_units) > 0
    assert retrieved.purchase_units[0].amount.value == "450.00"
    assert retrieved.purchase_units[0].amount.currency_code == "USD"
