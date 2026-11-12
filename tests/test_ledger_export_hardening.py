"""Ledger output must not invent settlement or trust caller financial fields."""
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import HTTPException
from backend.app.api.erp import sync_google_sheets_ledger
from backend.app.db.models import PayPalOrderRecord
from backend.app.services.erp.google_sheets_ledger import GoogleSheetsERPLedger


@pytest.mark.asyncio
@pytest.mark.parametrize("state,simulated", [("AUTHORIZED", False), ("CAPTURE_PENDING", False), ("CAPTURED", True)])
async def test_unsettled_or_simulated_order_cannot_export(state, simulated):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = PayPalOrderRecord(status=state, is_simulated=simulated, capture_id="CAP-1")
    with pytest.raises(HTTPException) as exc:
        await sync_google_sheets_ledger({"paypal_order_id": "ORD-1"}, current_user=None, db=db)
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_export_uses_persisted_amount_and_capture():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = PayPalOrderRecord(
        paypal_order_id="ORD-1", status="CAPTURED", is_simulated=False,
        capture_id="CAP-REAL", amount_value="480.00", currency_code="USD",
    )
    with patch("backend.app.api.erp.sheets_ledger.sync_ledger_entry", new_callable=AsyncMock) as export:
        await sync_google_sheets_ledger({"paypal_order_id": "ORD-1", "amount": 1, "capture_id": "FORGED"}, current_user=None, db=db)
        assert export.call_args.kwargs["amount"] == "480.00"
        assert export.call_args.kwargs["capture_id"] == "CAP-REAL"


@pytest.mark.asyncio
@pytest.mark.parametrize("body", [{}, {"success": False}, {"success": "true"}])
async def test_http_200_is_not_ledger_acknowledgement(body):
    ledger = GoogleSheetsERPLedger(webapp_url="https://example.com/ledger", secret="test-only")
    response = MagicMock(status_code=200)
    response.json.return_value = body
    with patch("httpx.AsyncClient.post", AsyncMock(return_value=response)):
        result = await ledger.sync_ledger_entry("ORD-1", "CAP-1", "450.00")
    assert result["success"] is False


@pytest.mark.asyncio
@pytest.mark.parametrize("amount", ["not-money", "nan", "inf", -1])
async def test_invalid_amount_never_defaults_to_450(amount):
    ledger = GoogleSheetsERPLedger(webapp_url="https://example.com/ledger", secret="test-only")
    with patch("httpx.AsyncClient.post", AsyncMock()) as post:
        assert (await ledger.sync_ledger_entry("ORD-1", "CAP-1", amount))["success"] is False
        post.assert_not_awaited()
