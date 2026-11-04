"""Unit and integration tests for the decoupled PayPal Orders v2 service package.
Complies with Master PRD V2 Section 8.4 and Section 12.1.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.services.paypal import (
    PayPalClient,
    PayPalAuthError,
    PayPalAPIError,
    PayPalOrderService,
    PayPalAuthorizationService,
    PayPalCaptureService,
    OrderIntent,
    OrderStatus,
    AuthorizationStatus,
    CaptureStatus,
)


@pytest.fixture
def mock_client():
    return PayPalClient(
        client_id="test_client_id_123",
        client_secret="test_client_secret_456",
        base_url="https://api-m.sandbox.paypal.com",
    )


@pytest.mark.asyncio
async def test_paypal_client_unconfigured_error():
    client = PayPalClient(client_id="", client_secret="")
    assert not client.is_configured
    with pytest.raises(PayPalAuthError, match="credentials missing"):
        await client.get_access_token()


@pytest.mark.asyncio
async def test_paypal_client_token_fetch_and_cache(mock_client):
    fake_token_response = MagicMock(
        status_code=200,
        json=lambda: {"access_token": "ACCESS_TOKEN_XYZ_999", "expires_in": 3600},
    )
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = fake_token_response
        token1 = await mock_client.get_access_token()
        assert token1 == "ACCESS_TOKEN_XYZ_999"

        # Second call should use cache without invoking post again
        token2 = await mock_client.get_access_token()
        assert token2 == "ACCESS_TOKEN_XYZ_999"
        assert mock_post.call_count == 1


@pytest.mark.asyncio
async def test_paypal_order_create_nominal(mock_client):
    service = PayPalOrderService(mock_client)
    fake_order_data = {
        "id": "ORDER-SANDBOX-1001",
        "status": "CREATED",
        "intent": "AUTHORIZE",
        "purchase_units": [
            {
                "reference_id": "pu-WO-2026-001",
                "description": "Bearing Replacement Inspection",
                "custom_id": "wo:WO-2026-001|quote:quote-apex-01",
                "amount": {
                    "currency_code": "USD",
                    "value": "450.00",
                },
            }
        ],
        "links": [
            {
                "href": "https://www.sandbox.paypal.com/checkoutnow?token=ORDER-SANDBOX-1001",
                "rel": "approve",
                "method": "GET",
            }
        ],
    }

    with patch.object(mock_client, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = fake_order_data
        order = await service.create_order(
            amount_value="450.00",
            currency_code="USD",
            work_order_id="WO-2026-001",
            quote_id="quote-apex-01",
            idempotency_key="idemp-key-test-001",
        )

        assert order.id == "ORDER-SANDBOX-1001"
        assert order.status == OrderStatus.CREATED
        assert order.intent == OrderIntent.AUTHORIZE
        assert len(order.purchase_units) == 1
        assert order.purchase_units[0].amount.value == "450.00"
        assert len(order.links) == 1
        assert order.links[0].rel == "approve"


@pytest.mark.asyncio
async def test_paypal_order_authorization(mock_client):
    auth_service = PayPalAuthorizationService(mock_client)
    fake_auth_data = {
        "id": "ORDER-SANDBOX-1001",
        "status": "COMPLETED",
        "purchase_units": [
            {
                "reference_id": "pu-WO-2026-001",
                "payments": {
                    "authorizations": [
                        {
                            "id": "AUTH-SANDBOX-5555",
                            "status": "CREATED",
                            "amount": {
                                "currency_code": "USD",
                                "value": "450.00",
                            },
                        }
                    ]
                },
            }
        ],
    }

    with patch.object(mock_client, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = fake_auth_data
        auth = await auth_service.authorize_order("ORDER-SANDBOX-1001", idempotency_key="idemp-auth-001")

        assert auth.authorization_id == "AUTH-SANDBOX-5555"
        assert auth.status == AuthorizationStatus.CREATED
        assert auth.amount.value == "450.00"
        assert auth.amount.currency_code == "USD"


@pytest.mark.asyncio
async def test_paypal_capture_success(mock_client):
    capture_service = PayPalCaptureService(mock_client)
    fake_capture_data = {
        "id": "CAPTURE-SANDBOX-9999",
        "status": "COMPLETED",
        "amount": {
            "currency_code": "USD",
            "value": "450.00",
        },
        "final_capture": True,
    }

    with patch.object(mock_client, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = fake_capture_data
        capture = await capture_service.capture_authorization(
            authorization_id="AUTH-SANDBOX-5555",
            amount_value="450.00",
            currency_code="USD",
            idempotency_key="idemp-cap-001",
        )

        assert capture.capture_id == "CAPTURE-SANDBOX-9999"
        assert capture.status == CaptureStatus.COMPLETED
        assert capture.amount.value == "450.00"
        assert capture.final_capture is True


@pytest.mark.asyncio
async def test_paypal_void_success(mock_client):
    auth_service = PayPalAuthorizationService(mock_client)
    with patch.object(mock_client, "request", new_callable=AsyncMock) as mock_req:
        mock_req.return_value = {}
        res = await auth_service.void_authorization("AUTH-SANDBOX-5555", idempotency_key="idemp-void-001")
        assert res.authorization_id == "AUTH-SANDBOX-5555"
        assert res.status == "VOIDED"
