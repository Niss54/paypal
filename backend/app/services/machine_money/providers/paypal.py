"""PayPal Enterprise Agentic Commerce Provider using PayPal REST Payouts API.
Complies with PayPal Payouts v1 REST endpoints and OAuth2 Client Credentials grant.
Designed for autonomous industrial MRO equipment maintenance procurement and vendor settlement.
"""
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
import httpx

from backend.app.services.machine_money.exceptions import ProviderError
from backend.app.services.machine_money.providers.base import LightningProvider
from backend.app.services.machine_money.schemas import (
    BOLT11Invoice,
    InvoiceRequest,
    PaymentReceipt,
    PaymentStatus,
    ProviderHealth,
    utcnow,
)

logger = logging.getLogger(__name__)


class PayPalProvider(LightningProvider):
    """Production/Sandbox PayPal Enterprise Provider for Autonomous Agentic Commerce.
    Interacts directly with PayPal REST API (v1/payments/payouts & v1/oauth2/token).
    """
    name = "paypal"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        mode: Optional[str] = None,
        timeout_seconds: float = 15.0,
    ):
        self.client_id = (client_id if client_id is not None else os.environ.get("PAYPAL_CLIENT_ID", "")).strip()
        self.client_secret = (client_secret if client_secret is not None else os.environ.get("PAYPAL_CLIENT_SECRET", "")).strip()
        self.base_url = (
            base_url or os.environ.get("PAYPAL_API_BASE_URL", "https://api-m.sandbox.paypal.com")
        ).rstrip("/")
        self.mode = (mode or os.environ.get("PAYPAL_MODE", "sandbox")).lower()
        self.timeout = timeout_seconds

        # In-memory OAuth2 token cache
        self._cached_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

    @property
    def is_configured(self) -> bool:
        """True if non-empty PayPal API credentials are present."""
        return bool(self.client_id and self.client_secret)

    async def get_access_token(self, force_refresh: bool = False) -> str:
        """Retrieve valid OAuth2 Bearer token from PayPal using client credentials grant.
        Caches the token with an expiration buffer.
        """
        now = utcnow()
        if (
            not force_refresh
            and self._cached_token
            and self._token_expires_at
            and now < self._token_expires_at - timedelta(seconds=60)
        ):
            return self._cached_token

        if not self.is_configured:
            raise ProviderError(
                "PayPal credentials missing: PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET are required. "
                "Configure them in .env to execute live PayPal Sandbox settlement."
            )

        token_url = f"{self.base_url}/v1/oauth2/token"
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US",
        }
        data = {"grant_type": "client_credentials"}

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(
                    token_url,
                    data=data,
                    headers=headers,
                    auth=(self.client_id, self.client_secret),
                )
                if res.status_code == 200:
                    body = res.json()
                    access_token = body.get("access_token")
                    expires_in = body.get("expires_in", 3600)
                    if not access_token:
                        raise ProviderError("PayPal token response missing access_token field")
                    self._cached_token = access_token
                    self._token_expires_at = now + timedelta(seconds=expires_in)
                    logger.info("Successfully fetched fresh PayPal OAuth2 token; expires in %ds", expires_in)
                    return access_token
                else:
                    raise ProviderError(
                        f"PayPal OAuth2 token request failed [HTTP {res.status_code}]: {res.text[:300]}"
                    )
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"Network error contacting PayPal OAuth2 endpoint ({token_url}): {exc}") from exc

    async def health(self) -> ProviderHealth:
        """Check PayPal Sandbox/Live connectivity, authentication, and endpoint availability."""
        is_sandbox = "sandbox" in self.base_url or self.mode == "sandbox"
        provider_mode = "SANDBOX" if is_sandbox else "LIVE"

        if not self.is_configured:
            return ProviderHealth(
                provider_name="paypal",
                provider_mode=provider_mode,
                settlement_source="PAYPAL_REST_API",
                is_live=False,
                is_connected=False,
                network=self.mode,
                details={
                    "status": "UNCONFIGURED",
                    "notice": (
                        "PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET not set in environment. "
                        "Add PayPal Developer Sandbox credentials to activate live payouts."
                    ),
                    "base_url": self.base_url,
                },
            )

        try:
            # Test live authentication handshake
            token = await self.get_access_token()
            return ProviderHealth(
                provider_name="paypal",
                provider_mode=provider_mode,
                settlement_source="PAYPAL_REST_API",
                is_live=True,
                is_connected=True,
                network=self.mode,
                details={
                    "status": "CONNECTED",
                    "base_url": self.base_url,
                    "auth": "OAUTH2_AUTHENTICATED",
                    "token_cached": bool(self._cached_token),
                    "currency": "USD",
                },
            )
        except Exception as exc:
            logger.warning(f"PayPal health probe failed: {exc}")
            return ProviderHealth(
                provider_name="paypal",
                provider_mode=provider_mode,
                settlement_source="PAYPAL_REST_API",
                is_live=False,
                is_connected=False,
                network=self.mode,
                details={"status": "CONNECTION_FAILED", "error": str(exc), "base_url": self.base_url},
            )

    async def execute_payout(
        self,
        recipient: str,
        amount_usd: float,
        note: str,
        sender_item_id: Optional[str] = None,
        sender_batch_id: Optional[str] = None,
        recipient_type: str = "EMAIL",
        email_subject: str = "KinetixRAG Industrial Equipment Dispatch",
    ) -> Dict[str, Any]:
        """Execute autonomous settlement to a vendor depot via PayPal Payouts REST API.
        
        Args:
            recipient: Receiver email or phone or PayPal ID
            amount_usd: Amount in USD (e.g. 450.00)
            note: Memo / item note
            sender_item_id: Idempotent item tracking ID
            sender_batch_id: Idempotent batch tracking ID
            recipient_type: "EMAIL", "PHONE", or "PAYPAL_ID"
            email_subject: Subject line for notification
        """
        token = await self.get_access_token()
        batch_id = sender_batch_id or f"kinetix-batch-{uuid.uuid4().hex[:12]}"
        item_id = sender_item_id or f"item-{uuid.uuid4().hex[:10]}"

        payout_url = f"{self.base_url}/v1/payments/payouts"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "PayPal-Request-Id": batch_id,
        }

        payload = {
            "sender_batch_header": {
                "sender_batch_id": batch_id,
                "recipient_type": recipient_type,
                "email_subject": email_subject,
                "email_message": f"Autonomous industrial equipment emergency maintenance settlement: {note}",
            },
            "items": [
                {
                    "recipient_type": recipient_type,
                    "amount": {
                        "value": f"{amount_usd:.2f}",
                        "currency": "USD",
                    },
                    "note": note,
                    "sender_item_id": item_id,
                    "receiver": recipient,
                }
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(payout_url, json=payload, headers=headers)
                if res.status_code in (201, 200):
                    data = res.json()
                    batch_header = data.get("batch_header", {})
                    payout_batch_id = batch_header.get("payout_batch_id", "")
                    batch_status = batch_header.get("batch_status", "PENDING")

                    logger.info(
                        "Created PayPal Payout batch %s (status=%s, amount=$%.2f)",
                        payout_batch_id,
                        batch_status,
                        amount_usd,
                    )
                    return {
                        "success": True,
                        "payout_batch_id": payout_batch_id,
                        "sender_batch_id": batch_id,
                        "batch_status": batch_status,
                        "amount_usd": amount_usd,
                        "recipient": recipient,
                        "sender_item_id": item_id,
                        "links": data.get("links", []),
                        "raw_response": data,
                    }
                else:
                    raise ProviderError(
                        f"PayPal Payout creation failed [HTTP {res.status_code}]: {res.text[:400]}"
                    )
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"Network error executing PayPal Payout: {exc}") from exc

    async def execute_batch_payout(
        self,
        items: List[Dict[str, Any]],
        email_subject: str = "KinetixPay Biopharma Split Emergency Dispatch",
        sender_batch_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a multi-recipient batch payout via PayPal Payouts REST API.
        
        Args:
            items: List of dicts, each with keys: 'recipient', 'amount_usd', 'note', optional 'sender_item_id'
        """
        token = await self.get_access_token()
        batch_id = sender_batch_id or f"kinetix-split-{uuid.uuid4().hex[:12]}"

        formatted_items = []
        total_usd = 0.0
        for idx, it in enumerate(items):
            amt = float(it.get("amount_usd", 0.0))
            total_usd += amt
            formatted_items.append({
                "recipient_type": it.get("recipient_type", "EMAIL"),
                "amount": {
                    "value": f"{amt:.2f}",
                    "currency": it.get("currency", "USD"),
                },
                "note": it.get("note", "BioPharma Cold-Chain Emergency Split Reimbursement"),
                "sender_item_id": it.get("sender_item_id") or f"split-item-{idx}-{uuid.uuid4().hex[:6]}",
                "receiver": it.get("recipient"),
            })

        payout_url = f"{self.base_url}/v1/payments/payouts"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "PayPal-Request-Id": batch_id,
        }

        payload = {
            "sender_batch_header": {
                "sender_batch_id": batch_id,
                "recipient_type": "EMAIL",
                "email_subject": email_subject,
                "email_message": f"Autonomous industrial multi-party emergency maintenance payout (Total ${total_usd:.2f})",
            },
            "items": formatted_items,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(payout_url, json=payload, headers=headers)
                if res.status_code in (201, 200):
                    data = res.json()
                    batch_header = data.get("batch_header", {})
                    payout_batch_id = batch_header.get("payout_batch_id", "")
                    batch_status = batch_header.get("batch_status", "PENDING")

                    logger.info(
                        "Created PayPal Multi-Party Batch %s (%d items, status=%s, total=$%.2f)",
                        payout_batch_id,
                        len(formatted_items),
                        batch_status,
                        total_usd,
                    )
                    return {
                        "success": True,
                        "payout_batch_id": payout_batch_id,
                        "sender_batch_id": batch_id,
                        "batch_status": batch_status,
                        "total_amount_usd": total_usd,
                        "item_count": len(formatted_items),
                        "items": formatted_items,
                        "links": data.get("links", []),
                        "raw_response": data,
                    }
                else:
                    raise ProviderError(
                        f"PayPal Multi-Party Payout creation failed [HTTP {res.status_code}]: {res.text[:400]}"
                    )
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"Network error executing PayPal Multi-Party Payout: {exc}") from exc

    async def get_payout_batch_status(self, payout_batch_id: str) -> Dict[str, Any]:
        """Fetch real-time settlement status of a previously executed PayPal Payout batch."""
        token = await self.get_access_token()
        url = f"{self.base_url}/v1/payments/payouts/{payout_batch_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    return res.json()
                else:
                    raise ProviderError(
                        f"PayPal Payout status check failed [HTTP {res.status_code}]: {res.text[:300]}"
                    )
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"Network error querying PayPal Payout batch {payout_batch_id}: {exc}") from exc

    async def get_payout_item_status(self, payout_item_id: str) -> Dict[str, Any]:
        """Fetch settlement details of an individual payout line item."""
        token = await self.get_access_token()
        url = f"{self.base_url}/v1/payments/payouts-item/{payout_item_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    return res.json()
                else:
                    raise ProviderError(
                        f"PayPal Payout item query failed [HTTP {res.status_code}]: {res.text[:300]}"
                    )
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"Network error querying PayPal Payout item {payout_item_id}: {exc}") from exc

    # =========================================================================
    # LightningProvider Compatibility Interface
    # Allows PayPalProvider to act as drop-in replacement across existing services
    # =========================================================================

    async def create_invoice(self, request: InvoiceRequest) -> BOLT11Invoice:
        """A Lightning invoice cannot safely represent a USD procurement order."""
        raise ProviderError("PayPal does not support Lightning invoices. Use evidence-gated PayPal Orders v2 procurement.")

    async def pay_invoice(self, bolt11: str, max_fee_sats: int = 20) -> PaymentReceipt:
        """Reject the legacy adapter rather than invent an amount or bypass evidence."""
        raise ProviderError("PayPal invoice payouts are disabled. Use evidence-gated PayPal Orders v2 procurement.")

    async def check_payment(self, payment_hash: str) -> PaymentReceipt:
        """Never fabricate a Lightning receipt, preimage or settlement for PayPal."""
        raise ProviderError("PayPal Lightning receipt lookup is unsupported. Query the PayPal order or payout batch explicitly.")
