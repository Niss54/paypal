"""PayPal Capture Service: Capturing Authorized Funds for Verified Orders.
Adheres to Master PRD V2 Section 8.4.
"""
import logging
from typing import Optional
from backend.app.services.paypal.client import PayPalClient
from backend.app.services.paypal.schemas import (
    CaptureStatus,
    LinkDescription,
    Money,
    PayPalCaptureResponse,
)

logger = logging.getLogger(__name__)


class PayPalCaptureService:
    """Executes capture calls against authorized PayPal transactions."""

    def __init__(self, client: Optional[PayPalClient] = None):
        self.client = client or PayPalClient()

    async def capture_authorization(
        self,
        authorization_id: str,
        amount_value: str,
        currency_code: str = "USD",
        final_capture: bool = True,
        note_to_payer: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> PayPalCaptureResponse:
        """Call PayPal to capture previously authorized funds."""
        payload = {
            "amount": {
                "currency_code": currency_code,
                "value": amount_value,
            },
            "final_capture": final_capture,
        }
        if note_to_payer:
            payload["note_to_payer"] = note_to_payer

        data = await self.client.request(
            method="POST",
            path=f"/v2/payments/authorizations/{authorization_id}/capture",
            json_data=payload,
            idempotency_key=idempotency_key,
        )

        capture_id = data.get("id", "")
        raw_status = data.get("status")
        # Fail closed: never default an unknown or missing status to COMPLETED!
        if not raw_status:
            status = CaptureStatus.UNKNOWN
        elif raw_status in CaptureStatus._value2member_map_:
            status = CaptureStatus(raw_status)
        else:
            status = CaptureStatus.UNKNOWN

        # If capture_id is missing, it cannot be considered COMPLETED
        if not capture_id and status == CaptureStatus.COMPLETED:
            status = CaptureStatus.UNKNOWN

        amt_dict = data.get("amount", {})
        ret_curr = amt_dict.get("currency_code")
        ret_val = amt_dict.get("value")

        if not ret_curr or not ret_val:
            logger.error("Capture response missing required amount or currency: %s", amt_dict)
            status = CaptureStatus.UNKNOWN
            money = Money(
                currency_code=ret_curr or currency_code,
                value=ret_val or "0.00",
            )
        else:
            money = Money(currency_code=ret_curr, value=ret_val)

        # Fail closed on amount or currency mismatch! Never allow mismatch to be marked COMPLETED!
        if ret_curr != currency_code or ret_val != amount_value:
            logger.error(
                "Capture amount mismatch: expected %s %s, PayPal returned %s %s",
                amount_value, currency_code, ret_val, ret_curr
            )
            status = CaptureStatus.UNKNOWN

        links = [
            LinkDescription(
                href=lk.get("href", ""),
                rel=lk.get("rel", ""),
                method=lk.get("method", "GET"),
            )
            for lk in data.get("links", [])
        ]

        logger.info("Captured PayPal Authorization %s -> Capture %s (status=%s, amount=%s %s)",
                    authorization_id, capture_id, status.value, money.value, money.currency_code)

        return PayPalCaptureResponse(
            capture_id=capture_id,
            status=status,
            amount=money,
            final_capture=data.get("final_capture", final_capture),
            seller_protection=data.get("seller_protection"),
            seller_receivable_breakdown=data.get("seller_receivable_breakdown"),
            links=links,
            raw_response=data,
        )

    async def get_capture(self, capture_id: str) -> PayPalCaptureResponse:
        """Fetch details of a previously executed capture."""
        data = await self.client.request(
            method="GET",
            path=f"/v2/payments/captures/{capture_id}",
        )

        raw_status = data.get("status")
        if not raw_status:
            status = CaptureStatus.UNKNOWN
        elif raw_status in CaptureStatus._value2member_map_:
            status = CaptureStatus(raw_status)
        else:
            status = CaptureStatus.UNKNOWN

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

        return PayPalCaptureResponse(
            capture_id=data.get("id", capture_id),
            status=status,
            amount=money,
            final_capture=data.get("final_capture", True),
            seller_protection=data.get("seller_protection"),
            seller_receivable_breakdown=data.get("seller_receivable_breakdown"),
            links=links,
            raw_response=data,
        )
