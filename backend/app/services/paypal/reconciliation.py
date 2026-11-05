"""PayPal Order & Transaction Reconciliation Service.
Synchronizes local database state against PayPal REST API source of truth.
Adheres to Master PRD V2 Section 8.7.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from backend.app.db.models import PayPalOrderRecord
from backend.app.services.paypal.client import PayPalClient
from backend.app.services.paypal.orders import PayPalOrderService
from backend.app.services.paypal.authorization import PayPalAuthorizationService
from backend.app.services.paypal.capture import PayPalCaptureService

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PayPalReconciliationService:
    """Reconciles local PayPalOrderRecord against real-time PayPal API resources."""

    def __init__(self, client: Optional[PayPalClient] = None):
        self.client = client or PayPalClient()
        self.order_service = PayPalOrderService(self.client)
        self.auth_service = PayPalAuthorizationService(self.client)
        self.capture_service = PayPalCaptureService(self.client)

    async def reconcile_order(self, db: Session, paypal_order_id: str) -> Dict[str, Any]:
        """Query PayPal REST API and reconcile the local order record."""
        record = db.query(PayPalOrderRecord).filter_by(paypal_order_id=paypal_order_id).first()
        if not record:
            return {"status": "NOT_FOUND", "paypal_order_id": paypal_order_id}

        order_data = await self.order_service.get_order(paypal_order_id)
        now = utcnow()
        updated = False

        # Check order status mapping
        if order_data.status.value == "APPROVED" and record.status in ("DRAFT", "ORDER_CREATED"):
            record.status = "BUYER_APPROVED"
            updated = True

        # Check authorization if available
        pus = order_data.raw_response.get("purchase_units", [])
        if pus:
            payments = pus[0].get("payments", {})
            auths = payments.get("authorizations", [])
            if auths and not record.authorization_id:
                record.authorization_id = auths[0].get("id")
                record.status = "AUTHORIZED"
                record.authorized_at = now
                updated = True

            captures = payments.get("captures", [])
            if captures and not record.capture_id:
                cap = captures[0]
                record.capture_id = cap.get("id")
                if cap.get("status") == "COMPLETED":
                    record.status = "CAPTURED"
                    record.captured_at = now
                    updated = True

        if updated:
            record.updated_at = now
            db.commit()
            db.refresh(record)
            logger.info("Reconciled PayPal order %s to status %s", paypal_order_id, record.status)

        return {
            "status": "RECONCILED",
            "paypal_order_id": paypal_order_id,
            "local_status": record.status,
            "paypal_status": order_data.status.value,
            "authorization_id": record.authorization_id,
            "capture_id": record.capture_id,
        }
