"""Unit and integration tests for PayPal Enterprise Provider (KinetixPay Agentic Commerce)."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from backend.app.services.machine_money.exceptions import ProviderError
from backend.app.services.machine_money.providers.paypal import PayPalProvider
from backend.app.services.machine_money.providers.factory import get_payment_provider
from backend.app.services.machine_money.schemas import InvoiceRequest, PaymentStatus


@pytest.fixture
def mock_paypal_provider():
    return PayPalProvider(
        client_id="sandbox_client_id_test_123",
        client_secret="sandbox_client_secret_test_456",
        base_url="https://api-m.sandbox.paypal.com",
        mode="sandbox",
    )


@pytest.mark.asyncio
async def test_paypal_provider_unconfigured_health():
    """Unconfigured provider must report UNCONFIGURED status gracefully without crashing."""
    provider = PayPalProvider(client_id="", client_secret="")
    assert not provider.is_configured

    health = await provider.health()
    assert health.provider_name == "paypal"
    assert not health.is_live
    assert not health.is_connected
    assert health.details.get("status") == "UNCONFIGURED"


@pytest.mark.asyncio
async def test_paypal_provider_oauth2_token_fetch_and_cache(mock_paypal_provider):
    """Verifies OAuth2 client credentials token fetch and subsequent in-memory cache hit."""
    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "access_token": "A21AALiveSandboxBearerTokenXYZ987",
        "expires_in": 3600,
        "token_type": "Bearer",
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = fake_response

        # First call: network fetch
        token1 = await mock_paypal_provider.get_access_token()
        assert token1 == "A21AALiveSandboxBearerTokenXYZ987"
        assert mock_post.call_count == 1

        # Second call: cached, should NOT invoke HTTP POST again
        token2 = await mock_paypal_provider.get_access_token()
        assert token2 == token1
        assert mock_post.call_count == 1

        # Force refresh: should invoke HTTP POST again
        token3 = await mock_paypal_provider.get_access_token(force_refresh=True)
        assert token3 == token1
        assert mock_post.call_count == 2


@pytest.mark.asyncio
async def test_paypal_provider_oauth2_token_failure(mock_paypal_provider):
    """Handles OAuth2 401 error fail-closed."""
    fake_response = MagicMock()
    fake_response.status_code = 401
    fake_response.text = '{"error": "invalid_client", "error_description": "Client Authentication failed"}'

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = fake_response
        with pytest.raises(ProviderError) as exc_info:
            await mock_paypal_provider.get_access_token()
        assert "PayPal OAuth2 token request failed [HTTP 401]" in str(exc_info.value)


@pytest.mark.asyncio
async def test_paypal_provider_execute_payout_success(mock_paypal_provider):
    """Executes B2B emergency dock payout with verified request headers and payload structure."""
    # Pre-populate cached token
    mock_paypal_provider._cached_token = "valid_cached_token_123"
    from datetime import datetime, timezone, timedelta
    mock_paypal_provider._token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    fake_payout_response = MagicMock()
    fake_payout_response.status_code = 201
    fake_payout_response.json.return_value = {
        "batch_header": {
            "payout_batch_id": "BATCH-SANDBOX-778899",
            "batch_status": "SUCCESS",
            "sender_batch_header": {
                "sender_batch_id": "custom-batch-001",
            },
        },
        "links": [
            {
                "href": "https://api-m.sandbox.paypal.com/v1/payments/payouts/BATCH-SANDBOX-778899",
                "rel": "self",
                "method": "GET",
            }
        ],
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = fake_payout_response

        res = await mock_paypal_provider.execute_payout(
            recipient="chicago-redn-depot@kinetixpay-depot.com",
            amount_usd=450.00,
            note="Emergency Industrial Slurry Pump Bearing Replacement",
            sender_batch_id="custom-batch-001",
            sender_item_id="item-001",
        )

        assert res["success"] is True
        assert res["payout_batch_id"] == "BATCH-SANDBOX-778899"
        assert res["batch_status"] == "SUCCESS"
        assert res["amount_usd"] == 450.00

        # Verify posted payload
        assert mock_post.call_count == 1
        call_kwargs = mock_post.call_args.kwargs
        posted_json = call_kwargs["json"]
        assert posted_json["sender_batch_header"]["sender_batch_id"] == "custom-batch-001"
        assert posted_json["items"][0]["amount"]["value"] == "450.00"
        assert posted_json["items"][0]["amount"]["currency"] == "USD"
        assert posted_json["items"][0]["receiver"] == "chicago-redn-depot@kinetixpay-depot.com"


@pytest.mark.asyncio
async def test_paypal_provider_execute_payout_api_error(mock_paypal_provider):
    """Propagates PayPal API errors with exact diagnostics."""
    mock_paypal_provider._cached_token = "valid_cached_token_123"
    from datetime import datetime, timezone, timedelta
    mock_paypal_provider._token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    fake_response = MagicMock()
    fake_response.status_code = 400
    fake_response.text = '{"name": "INSUFFICIENT_FUNDS", "message": "Sender has insufficient funds"}'

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = fake_response
        with pytest.raises(ProviderError) as exc_info:
            await mock_paypal_provider.execute_payout(
                recipient="depot@example.com",
                amount_usd=10000.0,
                note="Excessive payout",
            )
        assert "INSUFFICIENT_FUNDS" in str(exc_info.value)


@pytest.mark.asyncio
async def test_paypal_provider_get_payout_batch_status(mock_paypal_provider):
    """Queries batch status via PayPal REST GET endpoint."""
    mock_paypal_provider._cached_token = "valid_cached_token_123"
    from datetime import datetime, timezone, timedelta
    mock_paypal_provider._token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "batch_header": {
            "payout_batch_id": "BATCH-SANDBOX-778899",
            "batch_status": "SUCCESS",
            "time_completed": "2026-10-27T16:00:05Z",
        },
        "items": [
            {
                "payout_item_id": "ITEM-9988",
                "transaction_id": "TXN-PP-00112233",
                "transaction_status": "SUCCESS",
            }
        ],
    }

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = fake_response
        res = await mock_paypal_provider.get_payout_batch_status("BATCH-SANDBOX-778899")
        assert res["batch_header"]["batch_status"] == "SUCCESS"
        assert res["items"][0]["transaction_id"] == "TXN-PP-00112233"


def test_paypal_provider_factory_resolution(monkeypatch):
    """Verifies get_payment_provider returns PayPalProvider when configured."""
    monkeypatch.setenv("MACHINE_MONEY_PROVIDER", "paypal")
    provider = get_payment_provider(force_refresh=True)
    assert isinstance(provider, PayPalProvider)
    assert provider.name == "paypal"


@pytest.mark.asyncio
async def test_paypal_legacy_adapter_cannot_bypass_procurement(mock_paypal_provider):
    """No fixed-amount payout or synthetic receipt may escape the Orders gate."""
    with patch.object(mock_paypal_provider, "execute_payout", new_callable=AsyncMock) as payout:
        with pytest.raises(ProviderError, match="Orders v2"):
            await mock_paypal_provider.create_invoice(InvoiceRequest(amount_sats=250, memo="repair"))
        with pytest.raises(ProviderError, match="Orders v2"):
            await mock_paypal_provider.pay_invoice("paypal:payout?amount=1.00&currency=USD")
        payout.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("payment_hash", ["unknown", "paypal-payout-unknown", ""])
async def test_paypal_unknown_receipt_never_settles(mock_paypal_provider, payment_hash):
    with pytest.raises(ProviderError, match="unsupported"):
        await mock_paypal_provider.check_payment(payment_hash)
