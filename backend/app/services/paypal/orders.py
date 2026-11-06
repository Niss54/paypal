"""PayPal Orders v2 API Service: Order Creation with intent=AUTHORIZE and Order Retrieval.
Adheres to Master PRD V2 Section 8.4.
"""
import logging
from typing import Any, Dict, Optional
from backend.app.services.paypal.client import PayPalClient
from backend.app.services.paypal.schemas import (
    LinkDescription,
    Money,
    OrderIntent,
    OrderStatus,
    PayPalOrderCreateRequest,
    PayPalOrderResponse,
    PurchaseUnit,
    PurchaseUnitAmount,
)

logger = logging.getLogger(__name__)


class PayPalOrderService:
    """Manages creation and retrieval of PayPal Orders v2."""

    def __init__(self, client: Optional[PayPalClient] = None):
        self.client = client or PayPalClient()

    async def create_order(
        self,
        amount_value: str,
        currency_code: str = "USD",
        work_order_id: Optional[str] = None,
        quote_id: Optional[str] = None,
        description: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        return_url: Optional[str] = None,
        cancel_url: Optional[str] = None,
        payee_email: Optional[str] = None,
    ) -> PayPalOrderResponse:
        """Create a PayPal order with intent=AUTHORIZE for deferred capture."""
        purchase_unit = PurchaseUnit(
            reference_id=f"pu-{work_order_id or 'default'}",
            description=description or f"Industrial Equipment Maintenance [{work_order_id or 'N/A'}]",
            custom_id=f"wo:{work_order_id}|quote:{quote_id}",
            amount=PurchaseUnitAmount(
                currency_code=currency_code,
                value=amount_value,
            ),
        )

        app_context: Dict[str, Any] = {
            "brand_name": "KinetixRAG Industrial Procurement",
            "landing_page": "LOGIN",
            "user_action": "CONTINUE",
        }
        if return_url:
            app_context["return_url"] = return_url
        if cancel_url:
            app_context["cancel_url"] = cancel_url

        pu_dict: Dict[str, Any] = {
            "reference_id": purchase_unit.reference_id,
            "description": purchase_unit.description,
            "custom_id": purchase_unit.custom_id,
            "amount": {
                "currency_code": purchase_unit.amount.currency_code,
                "value": purchase_unit.amount.value,
            },
        }
        if payee_email:
            pu_dict["payee"] = {"email_address": payee_email}

        payload = {
            "intent": OrderIntent.AUTHORIZE.value,
            "purchase_units": [pu_dict],
            "application_context": app_context,
        }

        data = await self.client.request(
            method="POST",
            path="/v2/checkout/orders",
            json_data=payload,
            idempotency_key=idempotency_key,
        )

        order_id = data.get("id", "")
        status = OrderStatus(data.get("status", OrderStatus.CREATED.value))
        intent = OrderIntent(data.get("intent", OrderIntent.AUTHORIZE.value))

        raw_pus = data.get("purchase_units", [])
        units = []
        for pu in raw_pus:
            amt = pu.get("amount", {})
            units.append(
                PurchaseUnit(
                    reference_id=pu.get("reference_id", "default"),
                    description=pu.get("description"),
                    custom_id=pu.get("custom_id"),
                    amount=PurchaseUnitAmount(
                        currency_code=amt.get("currency_code", currency_code),
                        value=amt.get("value", amount_value),
                    ),
                )
            )

        links = [
            LinkDescription(
                href=lk.get("href", ""),
                rel=lk.get("rel", ""),
                method=lk.get("method", "GET"),
            )
            for lk in data.get("links", [])
        ]

        logger.info("Successfully created PayPal Order %s (intent=%s, status=%s, amount=%s %s)",
                    order_id, intent.value, status.value, amount_value, currency_code)

        return PayPalOrderResponse(
            id=order_id,
            status=status,
            intent=intent,
            purchase_units=units,
            links=links,
            raw_response=data,
        )

    async def get_order(self, order_id: str) -> PayPalOrderResponse:
        """Query state and details of an existing PayPal Order."""
        data = await self.client.request(
            method="GET",
            path=f"/v2/checkout/orders/{order_id}",
        )

        order_id = data.get("id", order_id)
        status = OrderStatus(data.get("status", OrderStatus.CREATED.value))
        intent = OrderIntent(data.get("intent", OrderIntent.AUTHORIZE.value))

        raw_pus = data.get("purchase_units", [])
        units = []
        for pu in raw_pus:
            amt = pu.get("amount", {})
            units.append(
                PurchaseUnit(
                    reference_id=pu.get("reference_id", "default"),
                    description=pu.get("description"),
                    custom_id=pu.get("custom_id"),
                    amount=PurchaseUnitAmount(
                        currency_code=amt.get("currency_code", "USD"),
                        value=amt.get("value", "0.00"),
                    ),
                )
            )

        links = [
            LinkDescription(
                href=lk.get("href", ""),
                rel=lk.get("rel", ""),
                method=lk.get("method", "GET"),
            )
            for lk in data.get("links", [])
        ]

        return PayPalOrderResponse(
            id=order_id,
            status=status,
            intent=intent,
            purchase_units=units,
            links=links,
            raw_response=data,
        )
