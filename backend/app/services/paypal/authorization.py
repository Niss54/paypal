"""PayPal Authorization Service: Authorize Approved Orders, Query & Void Authorizations.
Adheres to Master PRD V2 Section 8.4.
"""
import logging
from typing import Optional
from backend.app.services.paypal.client import PayPalClient
from backend.app.services.paypal.schemas import (
    AuthorizationStatus,
    LinkDescription,
    Money,
    PayPalAuthorizeResponse,
    PayPalVoidResponse,
)

logger = logging.getLogger(__name__)


class PayPalAuthorizationService:
    """Manages two-phase authorization holds under Orders v2."""

    def __init__(self, client: Optional[PayPalClient] = None):
        self.client = client or PayPalClient()

    async def authorize_order(
        self,
        order_id: str,
        idempotency_key: Optional[str] = None,
    ) -> PayPalAuthorizeResponse:
        """Call PayPal to authorize funds for a buyer-approved order."""
        data = await self.client.request(
            method="POST",
            path=f"/v2/checkout/orders/{order_id}/authorize",
            idempotency_key=idempotency_key,
        )

        # In Orders v2 authorize response, purchase_units contain payments.authorizations list
        auth_obj = {}
        pus = data.get("purchase_units", [])
        if pus:
            payments = pus[0].get("payments", {})
            auths = payments.get("authorizations", [])
            if auths:
                auth_obj = auths[0]

        auth_id = auth_obj.get("id", "")
        raw_status = auth_obj.get("status")
        if not auth_id or not raw_status:
            logger.error("Missing authorization object or status in PayPal authorize response: %s", data)
            status = AuthorizationStatus.DENIED
        elif raw_status in AuthorizationStatus._value2member_map_:
            status = AuthorizationStatus(raw_status)
        else:
            logger.warning("Unrecognized PayPal authorization status: %s", raw_status)
            status = AuthorizationStatus.DENIED

        amt_dict = auth_obj.get("amount", {})
        money = Money(
            currency_code=amt_dict.get("currency_code", "USD"),
            value=amt_dict.get("value", "0.00"),
        )

        links = [
            LinkDescription(
                href=lk.get("href", ""),
                rel=lk.get("rel", ""),
                method=lk.get("method", "GET"),
            )
            for lk in (auth_obj.get("links") or data.get("links", []))
        ]

        logger.info("Authorized PayPal Order %s -> Authorization %s (status=%s, amount=%s %s)",
                    order_id, auth_id, status.value, money.value, money.currency_code)

        return PayPalAuthorizeResponse(
            authorization_id=auth_id,
            status=status,
            amount=money,
            invoice_id=auth_obj.get("invoice_id"),
            custom_id=auth_obj.get("custom_id"),
            links=links,
            raw_response=data,
        )

    async def get_authorization(self, authorization_id: str) -> PayPalAuthorizeResponse:
        """Fetch real-time state of an active authorization hold."""
        data = await self.client.request(
            method="GET",
            path=f"/v2/payments/authorizations/{authorization_id}",
        )

        raw_status = data.get("status", AuthorizationStatus.CREATED.value)
        status = AuthorizationStatus(raw_status) if raw_status in AuthorizationStatus._value2member_map_ else AuthorizationStatus.CREATED

        amt_dict = data.get("amount", {})
        money = Money(
            currency_code=amt_dict.get("currency_code", "USD"),
            value=amt_dict.get("value", "0.00"),
        )

        links = [
            LinkDescription(
                href=lk.get("href", ""),
                rel=lk.get("rel", ""),
                method=lk.get("method", "GET"),
            )
            for lk in data.get("links", [])
        ]

        return PayPalAuthorizeResponse(
            authorization_id=data.get("id", authorization_id),
            status=status,
            amount=money,
            invoice_id=data.get("invoice_id"),
            custom_id=data.get("custom_id"),
            links=links,
            raw_response=data,
        )

    async def void_authorization(
        self,
        authorization_id: str,
        idempotency_key: Optional[str] = None,
    ) -> PayPalVoidResponse:
        """Void an uncaptured authorization (e.g. on order cancellation)."""
        data = await self.client.request(
            method="POST",
            path=f"/v2/payments/authorizations/{authorization_id}/void",
            idempotency_key=idempotency_key,
        )
        logger.info("Successfully voided PayPal authorization %s", authorization_id)
        return PayPalVoidResponse(
            authorization_id=authorization_id,
            status="VOIDED",
            raw_response=data if isinstance(data, dict) else {},
        )
