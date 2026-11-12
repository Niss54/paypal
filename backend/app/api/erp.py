"""Enterprise ERP Synchronizer API (SAP S/4HANA & IBM Maximo).

Provides live two-way synchronization for maintenance orders, purchase orders,
and GL liability clearing accounts (2100-PAYPAL-CLEARING).
"""
import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from backend.app.core.auth import get_current_user
from backend.app.services.erp.google_sheets_ledger import sheets_ledger
from backend.app.services.erp.ibm_maximo import IBMMaximoConnector
from backend.app.services.erp.models import (
    ERPStatusResponse,
    IBMMaximoWorkOrderRequest,
    IBMMaximoWorkOrderResponse,
    SAPMaintenanceOrderRequest,
    SAPMaintenanceOrderResponse,
)
from backend.app.services.erp.sap_s4hana import SAPS4HANAConnector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/erp", tags=["Enterprise ERP"])

_sap_connector = SAPS4HANAConnector()
_maximo_connector = IBMMaximoConnector()


@router.post("/sap/sync", response_model=SAPMaintenanceOrderResponse)
async def sync_sap_maintenance_order(
    req: SAPMaintenanceOrderRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Synchronize an industrial maintenance order to SAP S/4HANA Cloud (OData PM01).

    Enforces role-based governance: operator, engineer, supervisor, or automated agent.
    Posts pre-authorized liability to GL Account 2100-PAYPAL-CLEARING.
    Also dual-posts to Google Sheets ERP Ledger if configured.
    """
    try:
        response = await _sap_connector.sync_maintenance_order(req)
        # Asynchronously dual-post to Google Sheets ERP Ledger
        if req.paypal_order_id or req.paypal_capture_id:
            try:
                cap_id = req.paypal_capture_id or f"AUTH-{req.paypal_auth_id or 'PRE-SETTLE'}"
                await sheets_ledger.sync_ledger_entry(
                    paypal_order_id=req.paypal_order_id or "ORD-SAP-SYNC",
                    capture_id=cap_id,
                    amount=req.estimated_amount,
                    currency=req.currency,
                    status="COMPLETED" if req.paypal_capture_id else "COMPLETED",
                )
            except Exception as sheet_err:
                logger.warning("Dual Google Sheets ERP sync skipped: %s", sheet_err)
        return response
    except Exception as exc:
        logger.error("SAP S/4HANA synchronization failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"SAP S/4HANA synchronization failed: {exc}")


@router.post("/sheets/sync")
async def sync_google_sheets_ledger(
    payload: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Directly synchronizes an order/capture to the live Google Sheets ERP Ledger."""
    res = await sheets_ledger.sync_ledger_entry(
        paypal_order_id=payload.get("paypal_order_id", "ORD-DEMO-001"),
        capture_id=payload.get("capture_id", "CAP-DEMO-001"),
        amount=payload.get("amount", 450.0),
        currency=payload.get("currency", "USD"),
        status=payload.get("status", "COMPLETED"),
    )
    return res


@router.get("/status", response_model=ERPStatusResponse)
async def get_erp_status(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Return health, configuration status, and GL liability ledger for SAP S/4HANA, IBM Maximo, and Google Sheets."""
    ledger = _sap_connector.get_ledger_status()
    return ERPStatusResponse(
        sap_s4hana={
            "connector": "SAP S/4HANA Cloud OData (API_MAINTENANCEORDER)",
            "is_live_configured": _sap_connector.is_live_configured,
            "base_url": _sap_connector.base_url or "https://sandbox.api.sap.com/s4hanacloud",
            "mode": "LIVE_REST" if _sap_connector.is_live_configured else "ENTERPRISE_SANDBOX",
            "supported_order_types": ["PM01 (Corrective)", "PM02 (Preventive)", "PM03 (Emergency)"],
        },
        ibm_maximo={
            "connector": "IBM Maximo OSLC REST (/maximo/oslc/os/mxwo)",
            "is_live_configured": _maximo_connector.is_live_configured,
            "base_url": _maximo_connector.base_url or "https://maximo.enterprise.internal",
            "mode": "LIVE_REST" if _maximo_connector.is_live_configured else "ENTERPRISE_SANDBOX",
            "supported_work_types": ["CM (Corrective)", "EM (Emergency)", "PM (Preventive)"],
        },
        google_sheets_ledger={
            "connector": "Google Apps Script Web App ERP Ledger",
            "is_configured": sheets_ledger.is_configured,
            "spreadsheet_id": sheets_ledger.spreadsheet_id,
            "spreadsheet_url": sheets_ledger.spreadsheet_url,
            "gl_clearing_account": "2100-PAYPAL-CLEARING",
            "mode": "LIVE_CLOUD_SHEET" if sheets_ledger.is_configured else "LOCAL_MOCK",
        },
        gl_clearing_account=ledger,
    )
