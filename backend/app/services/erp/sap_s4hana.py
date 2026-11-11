"""SAP S/4HANA Cloud OData Connector for Plant Maintenance (PM) & Payment Clearing.

Interacts with SAP S/4HANA Cloud REST/OData APIs (API_MAINTENANCEORDER and
API_PURCHASEORDER_PROCESS_SRV). Manages double-entry GL ledger commitments
under Account 2100-PAYPAL-CLEARING.
"""
import hashlib
import logging
import os
from typing import Any, Dict, Optional
import httpx
from backend.app.services.erp.models import (
    ERPConnectorMode,
    SAPDoubleEntryPosting,
    SAPMaintenanceOrderRequest,
    SAPMaintenanceOrderResponse,
    SAPOrderType,
    utcnow_str,
)

logger = logging.getLogger(__name__)


class SAPS4HANAConnector:
    """Connects industrial procurement workflow to SAP S/4HANA Cloud."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.base_url = (base_url or os.getenv("SAP_S4HANA_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("SAP_API_KEY", "")
        self.username = username or os.getenv("SAP_USERNAME", "")
        self.password = password or os.getenv("SAP_PASSWORD", "")

        # Ledger tracker in memory for verification
        self._ledger_postings: list[SAPDoubleEntryPosting] = []

    @property
    def is_live_configured(self) -> bool:
        return bool(self.base_url and (self.api_key or (self.username and self.password)))

    async def sync_maintenance_order(
        self, req: SAPMaintenanceOrderRequest
    ) -> SAPMaintenanceOrderResponse:
        """Create or synchronize a Maintenance Order in SAP S/4HANA.

        Maps the PayPal pre-authorized commitment to General Ledger clearing
        account 2100-PAYPAL-CLEARING.
        """
        # Determine status: if captured, TECO (Technically Completed); if authorized, REL (Released); else CRTD (Created)
        if req.paypal_capture_id:
            sap_status = "TECO"
            cleared = True
            clearing_doc = f"CLR-SAP-{hashlib.sha256(req.paypal_capture_id.encode()).hexdigest()[:8].upper()}"
        elif req.paypal_auth_id:
            sap_status = "REL"
            cleared = False
            clearing_doc = None
        else:
            sap_status = "CRTD"
            cleared = False
            clearing_doc = None

        odata_payload = {
            "d": {
                "MaintenanceOrderType": req.order_type.value,
                "MaintenanceOrderDesc": req.short_text,
                "MainWorkCenterPlant": req.plant,
                "MainWorkCenter": req.work_center,
                "Equipment": req.equipment_id,
                "CostCenter": req.cost_center,
                "BusinessPartner": req.vendor_id,
                "EstimatedTotalCostAmount": req.estimated_amount,
                "Currency": req.currency,
                "ReferenceKey": req.paypal_auth_id or req.paypal_order_id or "NONE",
                "GeneralLedgerClearingAccount": req.gl_clearing_account,
                "EvidenceHash": req.evidence_hash or "PENDING_REPAIR_COMPLETION",
                "SystemStatusText": sap_status,
            }
        }

        posting = SAPDoubleEntryPosting(
            posting_date=utcnow_str()[:10],
            document_type="SA",
            company_code=req.plant,
            currency=req.currency,
            debit_account="6100-MAINT-EXPENSE",
            credit_account=req.gl_clearing_account,
            amount=req.estimated_amount,
            reference_key=req.paypal_auth_id or req.paypal_order_id or "SIM-REF",
            cleared=cleared,
            clearing_document=clearing_doc,
        )
        self._ledger_postings.append(posting)

        # If live credentials exist, execute live HTTP request to SAP S/4HANA
        if self.is_live_configured:
            headers = {"Accept": "application/json", "Content-Type": "application/json"}
            if self.api_key:
                headers["APIKey"] = self.api_key

            auth = (self.username, self.password) if (self.username and self.password) else None

            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    target_url = f"{self.base_url}/MaintenanceOrder"
                    res = await client.post(target_url, json=odata_payload, headers=headers, auth=auth)
                    if res.status_code in (200, 201):
                        data = res.json().get("d", {})
                        return SAPMaintenanceOrderResponse(
                            success=True,
                            sap_order_id=str(data.get("MaintenanceOrder", "4001928")),
                            sap_notification_id=str(data.get("MaintenanceNotification", "1002341")),
                            odata_url=f"{self.base_url}/MaintenanceOrder('{data.get('MaintenanceOrder', '4001928')}')",
                            status=sap_status,
                            equipment_id=req.equipment_id,
                            vendor_id=req.vendor_id,
                            gl_clearing_account=req.gl_clearing_account,
                            accounting_posting=posting,
                            connector_mode=ERPConnectorMode.LIVE_REST,
                            odata_payload_preview=odata_payload,
                        )
                    else:
                        logger.error("SAP S/4HANA live call returned HTTP %s: %s", res.status_code, res.text)
                        raise RuntimeError(f"SAP S/4HANA live dispatch failed with HTTP {res.status_code}: {res.text}")
            except Exception as exc:
                logger.error("SAP S/4HANA live dispatch error: %s", exc)
                raise RuntimeError(f"SAP S/4HANA live dispatch error: {exc}") from exc

        # Standard deterministic sandbox mode
        # Deterministically derive SAP order ID from equipment and vendor
        seed_bytes = f"{req.equipment_id}:{req.vendor_id}:{req.estimated_amount}".encode()
        order_num = 4000000 + (int(hashlib.sha256(seed_bytes).hexdigest()[:6], 16) % 900000)
        notif_num = 1000000 + (int(hashlib.md5(seed_bytes).hexdigest()[:6], 16) % 900000)

        return SAPMaintenanceOrderResponse(
            success=True,
            sap_order_id=str(order_num),
            sap_notification_id=str(notif_num),
            odata_url=f"https://sandbox.api.sap.com/s4hanacloud/sap/opu/odata/sap/API_MAINTENANCEORDER/MaintenanceOrder('{order_num}')",
            status=sap_status,
            equipment_id=req.equipment_id,
            vendor_id=req.vendor_id,
            gl_clearing_account=req.gl_clearing_account,
            accounting_posting=posting,
            connector_mode=ERPConnectorMode.ENTERPRISE_SANDBOX,
            odata_payload_preview=odata_payload,
        )

    def get_ledger_status(self) -> Dict[str, Any]:
        """Summary of GL account 2100-PAYPAL-CLEARING liability ledger."""
        total_committed = sum(float(p.amount) for p in self._ledger_postings if not p.cleared)
        total_cleared = sum(float(p.amount) for p in self._ledger_postings if p.cleared)
        return {
            "gl_account": "2100-PAYPAL-CLEARING",
            "description": "PayPal Agentic Pre-Authorized Liability Clearing",
            "currency": "USD",
            "active_commitments_usd": round(total_committed, 2),
            "settled_cleared_usd": round(total_cleared, 2),
            "total_postings_count": len(self._ledger_postings),
        }
