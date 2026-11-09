"""PayPal Webhook Verification, Deduplication, and Event Processing Service.
Adheres to Master PRD V2 Section 8.7 and Section 12.3.
"""
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.app.db.models import PayPalOrderRecord, PayPalWebhookEvent
from backend.app.services.paypal.client import PayPalClient

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PayPalWebhookService:
    """Handles signature verification and idempotent processing of PayPal Webhook events."""

    def __init__(self, client: Optional[PayPalClient] = None, webhook_id: Optional[str] = None):
        self.client = client or PayPalClient()
        self.webhook_id = (webhook_id or os.environ.get("PAYPAL_WEBHOOK_ID", "6AC51894PA229561H")).strip()

    async def verify_signature(
        self,
        headers: Dict[str, str],
        body: Dict[str, Any],
    ) -> bool:
        """Verify authenticity using PayPal's REST /v1/notifications/verify-webhook-signature."""
        # Case-insensitive header lookup
        h = {k.upper(): v for k, v in headers.items()}
        auth_algo = h.get("PAYPAL-AUTH-ALGO")
        cert_url = h.get("PAYPAL-CERT-URL")
        transmission_id = h.get("PAYPAL-TRANSMISSION-ID")
        transmission_sig = h.get("PAYPAL-TRANSMISSION-SIG")
        transmission_time = h.get("PAYPAL-TRANSMISSION-TIME")

        if not all([auth_algo, cert_url, transmission_id, transmission_sig, transmission_time]):
            logger.warning("Missing required PayPal webhook signature headers")
            return False

        verify_payload = {
            "auth_algo": auth_algo,
            "cert_url": cert_url,
            "transmission_id": transmission_id,
            "transmission_sig": transmission_sig,
            "transmission_time": transmission_time,
            "webhook_id": self.webhook_id,
            "webhook_event": body,
        }

        try:
            res = await self.client.request(
                method="POST",
                path="/v1/notifications/verify-webhook-signature",
                json_data=verify_payload,
            )
            verification_status = res.get("verification_status", "").upper()
            is_valid = (verification_status == "SUCCESS")
            logger.info("PayPal Webhook verification outcome: %s (valid=%s)", verification_status, is_valid)
            return is_valid
        except Exception as exc:
            logger.error(f"Error during PayPal webhook signature verification: {exc}")
            return False

    def process_event(
        self,
        db: Session,
        event_data: Dict[str, Any],
        signature_verified: bool,
    ) -> Dict[str, Any]:
        """Durable, idempotent processing of verified webhook events."""
        event_id = event_data.get("id")
        event_type = event_data.get("event_type", "UNKNOWN")
        resource = event_data.get("resource", {})
        resource_id = resource.get("id", "UNKNOWN")

        if not event_id:
            return {"status": "REJECTED", "reason": "Missing event ID"}

        # 1. Idempotency Check: Don't re-process duplicate events
        existing_event = db.query(PayPalWebhookEvent).filter_by(event_id=event_id).first()
        if existing_event:
            logger.info("Webhook event %s already processed (idempotent no-op)", event_id)
            return {
                "status": "ALREADY_PROCESSED",
                "event_id": event_id,
                "event_type": event_type,
            }

        if not signature_verified:
            logger.warning("Rejecting unverified webhook event %s (%s)", event_id, event_type)
            evt_rec = PayPalWebhookEvent(
                event_id=event_id,
                event_type=event_type,
                resource_id=resource_id,
                signature_verified=False,
                status="SIGNATURE_FAILED",
                payload_summary_json=json.dumps({"event_type": event_type, "resource_id": resource_id}),
            )
            db.add(evt_rec)
            db.commit()
            return {"status": "UNAUTHORIZED", "reason": "Invalid signature"}

        # 2. Extract correlating order / authorization
        # Depending on event_type, resource can be an order or a capture
        order_record: Optional[PayPalOrderRecord] = None
        now = utcnow()

        if event_type == "CHECKOUT.ORDER.APPROVED":
            order_record = db.query(PayPalOrderRecord).filter_by(paypal_order_id=resource_id).first()
            if order_record and order_record.status == "ORDER_CREATED":
                order_record.status = "BUYER_APPROVED"
                order_record.webhook_last_event_id = event_id
                order_record.updated_at = now

        elif event_type == "PAYMENT.CAPTURE.COMPLETED":
            # For capture, parent_payment or links may contain order ID, or look up by authorization_id / capture_id
            capture_id = resource.get("id")
            # In PayPal, supplementary_data or custom_id often holds the order reference
            custom_id = resource.get("custom_id", "")
            auth_id = ""
            for lk in resource.get("links", []):
                if lk.get("rel") == "up" and "authorizations" in lk.get("href", ""):
                    auth_id = lk.get("href", "").split("/")[-1]

            if auth_id:
                order_record = db.query(PayPalOrderRecord).filter_by(authorization_id=auth_id).order_by(PayPalOrderRecord.created_at.desc()).first()
            elif custom_id and "wo:" in custom_id and "quote:" in custom_id:
                # Disambiguate by both work_order_id and quote_id
                parts = dict(p.split(":", 1) for p in custom_id.split("|") if ":" in p)
                wo = parts.get("wo")
                q = parts.get("quote")
                order_record = db.query(PayPalOrderRecord).filter_by(work_order_id=wo, quote_id=q).order_by(PayPalOrderRecord.created_at.desc()).first()
            elif custom_id and "wo:" in custom_id:
                wo = custom_id.split("|")[0].replace("wo:", "")
                order_record = db.query(PayPalOrderRecord).filter_by(work_order_id=wo).order_by(PayPalOrderRecord.created_at.desc()).first()
            elif capture_id:
                order_record = db.query(PayPalOrderRecord).filter_by(capture_id=capture_id).first()

            if order_record:
                # Financial Integrity: Validate amount and currency match if provided
                res_amount = resource.get("amount", {})
                res_curr = res_amount.get("currency_code")
                res_val = res_amount.get("value")
                if res_curr and res_val:
                    if res_curr != order_record.currency_code or res_val != str(order_record.amount_value):
                        logger.error(
                            "PAYPAL WEBHOOK MISMATCH: Order %s expected %s %s, received %s %s",
                            order_record.paypal_order_id, order_record.amount_value, order_record.currency_code, res_val, res_curr
                        )
                        order_record.status = "CAPTURE_AMOUNT_MISMATCH"
                        order_record.updated_at = now
                        db.commit()
                        return {
                            "status": "AMOUNT_MISMATCH_REJECTED",
                            "event_id": event_id,
                            "order_id": order_record.paypal_order_id,
                        }
                elif res_amount and (not res_curr or not res_val):
                    logger.error(
                        "PAYPAL WEBHOOK MALFORMED AMOUNT: Order %s received capture event with partial amount fields",
                        order_record.paypal_order_id
                    )
                    order_record.status = "CAPTURE_AMOUNT_MALFORMED"
                    order_record.updated_at = now
                    db.commit()
                    return {
                        "status": "AMOUNT_MALFORMED_REJECTED",
                        "event_id": event_id,
                        "order_id": order_record.paypal_order_id,
                    }
                else:
                    logger.warning(
                        "PAYPAL WEBHOOK: Capture event %s for order %s omitted amount object; falling back to order record amount %s %s",
                        event_id, order_record.paypal_order_id, order_record.amount_value, order_record.currency_code
                    )

                order_record.status = "CAPTURED"
                order_record.capture_id = capture_id
                order_record.captured_at = now
                order_record.webhook_last_event_id = event_id
                order_record.updated_at = now

        elif event_type == "PAYMENT.CAPTURE.PENDING":
            capture_id = resource.get("id")
            order_record = db.query(PayPalOrderRecord).filter_by(capture_id=capture_id).first()
            if order_record and order_record.status != "CAPTURED":
                # Master PRD V2 Section 8.7 Rule: Treat PAYMENT.CAPTURE.PENDING as pending, never paid!
                order_record.status = "CAPTURE_PENDING"
                order_record.webhook_last_event_id = event_id
                order_record.updated_at = now

        elif event_type == "PAYMENT.CAPTURE.DENIED":
            order_record = db.query(PayPalOrderRecord).filter_by(capture_id=resource_id).first()
            if order_record:
                order_record.status = "CAPTURE_DENIED"
                order_record.webhook_last_event_id = event_id
                order_record.updated_at = now

        # Record durable processed webhook receipt
        webhook_record = PayPalWebhookEvent(
            event_id=event_id,
            event_type=event_type,
            resource_id=resource_id,
            signature_verified=True,
            status="PROCESSED",
            payload_summary_json=json.dumps({
                "event_type": event_type,
                "resource_id": resource_id,
                "summary": event_data.get("summary", ""),
            }),
            processed_at=now,
        )
        try:
            db.add(webhook_record)
            db.commit()
        except IntegrityError:
            db.rollback()
            logger.info("Concurrent webhook delivery deduplicated by DB constraint for event %s", event_id)
            return {
                "status": "ALREADY_PROCESSED",
                "event_id": event_id,
                "event_type": event_type,
            }

        return {
            "status": "PROCESSED",
            "event_id": event_id,
            "event_type": event_type,
            "order_status": order_record.status if order_record else None,
        }
