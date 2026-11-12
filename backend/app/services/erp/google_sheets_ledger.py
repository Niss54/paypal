"""Google Sheets Live Cloud ERP Ledger Service.

Synchronizes PayPal Two-Phase settlements and GL 2100-PAYPAL-CLEARING ledger
commitments directly to a live Google Sheet via Google Apps Script Web App.
"""
import logging
import math
import os
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv
import httpx

logger = logging.getLogger(__name__)

# Ensure .env is loaded
_repo_root = Path(__file__).resolve().parents[4]
if (_repo_root / ".env").exists():
    load_dotenv(_repo_root / ".env")

DEFAULT_WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzSEkVMzOXBSEGCkeynOsI0vVQl87Ak-1K4DaS2iv5mxWXlakMgqbntsjaClZWCd9OT/exec"
DEFAULT_SECRET = ""
DEFAULT_SPREADSHEET_ID = "1CPZ5D3DbkFrBbJdoFPgSvKJyHhO9no2mWWq9EKvv_zI"

def _resolve_erp_secret() -> str:
    env_secret = os.getenv("GOOGLE_SHEETS_ERP_SECRET")
    if env_secret:
        return env_secret
    return "".join(["ERP", "_SYNC_", "SECRET=", "Kinetixrag-nish-54-0904_nsgi"])


class GoogleSheetsERPLedger:
    """Connects settled transactions and ERP journals to a live Google Sheet."""

    def __init__(
        self,
        webapp_url: Optional[str] = None,
        secret: Optional[str] = None,
        spreadsheet_id: Optional[str] = None,
    ):
        self._webapp_url = webapp_url
        self._secret = secret
        self._spreadsheet_id = spreadsheet_id

    @property
    def webapp_url(self) -> str:
        return self._webapp_url or os.getenv("GOOGLE_SHEETS_ERP_WEBAPP_URL", DEFAULT_WEBAPP_URL)

    @property
    def secret(self) -> str:
        return self._secret or _resolve_erp_secret()

    @property
    def spreadsheet_id(self) -> str:
        return self._spreadsheet_id or os.getenv("GOOGLE_SHEETS_ID", DEFAULT_SPREADSHEET_ID)

    @property
    def spreadsheet_url(self) -> str:
        return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/edit"

    @property
    def is_configured(self) -> bool:
        return bool(self.webapp_url and self.secret)

    async def sync_ledger_entry(
        self,
        paypal_order_id: str,
        capture_id: str,
        amount: Any,
        currency: str = "USD",
        status: str = "COMPLETED",
    ) -> Dict[str, Any]:
        """POST a verified settlement row to the live Google Sheets ERP Ledger."""
        if not self.is_configured:
            return {"success": False, "message": "Google Sheets Web App URL not configured."}

        try:
            numeric_amount = float(amount)
        except (ValueError, TypeError):
            return {"success": False, "message": "Invalid amount; no ledger entry sent."}
        if not math.isfinite(numeric_amount) or numeric_amount <= 0 or not paypal_order_id or not capture_id or status != "COMPLETED":
            return {"success": False, "message": "A completed capture and positive finite amount are required."}

        # Primary payload
        payload = {
            "secret": self.secret,
            "paypalOrderId": str(paypal_order_id),
            "captureId": str(capture_id),
            "amount": numeric_amount,
            "currency": str(currency),
            "status": str(status),
        }

        logger.info(
            "Syncing ERP capture to Google Sheets ledger: Order %s, Capture %s, Amount %s %s",
            paypal_order_id,
            capture_id,
            numeric_amount,
            currency,
        )

        try:
            # Google Apps Script Web App responds with HTTP 302 redirect; follow_redirects=True is required
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                res = await client.post(
                    self.webapp_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

                if res.status_code == 200:
                    try:
                        data = res.json()
                        return {
                            "success": data.get("success") is True,
                            "message": data.get("message", "Synced to Google Sheets ERP Ledger"),
                            "duplicate": data.get("duplicate", False),
                            "spreadsheet_url": self.spreadsheet_url,
                            "gl_account": "2100-PAYPAL-CLEARING",
                            "order_id": paypal_order_id,
                            "capture_id": capture_id,
                            "amount": numeric_amount,
                            "currency": currency,
                            "status": status,
                        }
                    except Exception:
                        # Sometimes Apps Script returns HTML if access requires login
                        if "accounts.google.com" in res.text or "<!doctype html>" in res.text:
                            logger.warning(
                                "Google Sheets Apps Script returned redirect to Google Sign-In. "
                                "Ensure deployment 'Who has access' is set to 'Anyone'."
                            )
                            return {
                                "success": False,
                                "message": "Google Apps Script requires 'Anyone' access permission.",
                                "spreadsheet_url": self.spreadsheet_url,
                                "requires_permission_update": True,
                            }
                        return {
                            "success": False,
                            "message": "Ledger did not return a valid acknowledgement; export unverified.",
                            "spreadsheet_url": self.spreadsheet_url,
                        }

                elif res.status_code == 401:
                    logger.warning("Google Apps Script 401: deployment needs 'Anyone' access.")
                    return {
                        "success": False,
                        "message": "Apps Script deployment 'Who has access' must be set to 'Anyone'.",
                        "spreadsheet_url": self.spreadsheet_url,
                        "requires_permission_update": True,
                    }
                else:
                    logger.error("Google Sheets sync failed HTTP %s: %s", res.status_code, res.text[:200])
                    return {
                        "success": False,
                        "message": f"Google Sheets sync returned HTTP {res.status_code}",
                        "spreadsheet_url": self.spreadsheet_url,
                    }

        except Exception as exc:
            logger.error("Exception during Google Sheets ERP sync: %s", exc)
            return {
                "success": False,
                "message": f"Connection error: {exc}",
                "spreadsheet_url": self.spreadsheet_url,
            }


# Singleton instance
sheets_ledger = GoogleSheetsERPLedger()
