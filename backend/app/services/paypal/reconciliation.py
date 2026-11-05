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
            pu_amt = pus[0].get("amount", {})
            payments = pus[0].get("payments", {})
            auths = payments.get("authorizations", [])
            if auths and not record.authorization_id:
                auth_obj = auths[0]
                auth_status = auth_obj.get("status")
                auth_amt = auth_obj.get("amount", {})
                status_ok = auth_status in ("CREATED", "PENDING") if auth_status else True
                
                check_curr = auth_amt.get("currency_code") or pu_amt.get("currency_code")
                check_val = auth_amt.get("value") or pu_amt.get("value")
                amt_ok = True
                if check_curr and check_curr != record.currency_code:
                    amt_ok = False
                if check_val and str(check_val) != str(record.amount_value):
                    amt_ok = False
                    
                if status_ok and amt_ok:
                    record.authorization_id = auth_obj.get("id")
                    record.status = "AUTHORIZED"
                    record.authorized_at = now
                    updated = True
                else:
                    logger.warning(
                        "Reconciliation rejected authorization for %s: status_ok=%s, amt_ok=%s (expected %s %s, got %s %s)",
                        paypal_order_id, status_ok, amt_ok, record.amount_value, record.currency_code, check_val, check_curr
                    )

            captures = payments.get("captures", [])
            if captures and not record.capture_id:
                cap = captures[0]
                cap_status = cap.get("status")
                cap_amt = cap.get("amount", {})
                status_ok = cap_status == "COMPLETED" if cap_status else True
                
                check_curr = cap_amt.get("currency_code") or pu_amt.get("currency_code")
                check_val = cap_amt.get("value") or pu_amt.get("value")
                amt_ok = True
                if check_curr and check_curr != record.currency_code:
                    amt_ok = False
                if check_val and str(check_val) != str(record.amount_value):
                    amt_ok = False
                    
                if status_ok and amt_ok:
                    record.capture_id = cap.get("id")
                    if record.evidence_status == "VERIFIED":
                        record.status = "CAPTURED"
                        record.captured_at = now
                    else:
                        record.status = "RECONCILIATION_EXCEPTION_MISSING_EVIDENCE"
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
