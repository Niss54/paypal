"""Enterprise ERP Synchronizer API (SAP S/4HANA & IBM Maximo).

Provides live two-way synchronization for maintenance orders, purchase orders,
and GL liability clearing accounts (2100-PAYPAL-CLEARING).
"""
import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from backend.app.core.auth import get_current_user, require_roles, AppRole
from backend.app.db.database import get_db
from backend.app.db.models import PayPalOrderRecord
from sqlalchemy.orm import Session
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
    current_user=Depends(require_roles(AppRole.Supervisor, AppRole.FinanceAdmin, AppRole.AutomationAdmin)),
):
    """Synchronize an industrial maintenance order to SAP S/4HANA Cloud (OData PM01).

    Requires an authorized reviewer. Adapter mode distinguishes simulated payloads
    from configured external requests; this endpoint does not export settlement.
    """
    try:
        response = await _sap_connector.sync_maintenance_order(req)
        return response
    except Exception as exc:
        logger.error("SAP S/4HANA synchronization failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"SAP S/4HANA synchronization failed: {exc}")


@router.post("/maximo/sync", response_model=IBMMaximoWorkOrderResponse)
async def sync_maximo_work_order(
    req: IBMMaximoWorkOrderRequest,
    current_user=Depends(require_roles(AppRole.Supervisor, AppRole.FinanceAdmin, AppRole.AutomationAdmin)),
):
    """Submit a Maximo adapter request, retaining the returned connector mode."""
    try:
        return await _maximo_connector.sync_work_order(req)
    except Exception as exc:
        logger.error("Maximo synchronization failed: %s", type(exc).__name__)
        raise HTTPException(status_code=502, detail="Maximo synchronization failed") from exc


@router.post("/sheets/sync")
async def sync_google_sheets_ledger(
    payload: Dict[str, Any],
    current_user=Depends(require_roles(AppRole.Supervisor, AppRole.FinanceAdmin)),
    db: Session = Depends(get_db),
):
    """Export only a persisted, completed Sandbox capture using server-owned values."""
    order_id = payload.get("paypal_order_id")
    if not isinstance(order_id, str) or not order_id:
        raise HTTPException(status_code=422, detail="paypal_order_id is required")
    order = db.query(PayPalOrderRecord).filter(PayPalOrderRecord.paypal_order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status != "CAPTURED" or not order.capture_id:
        raise HTTPException(status_code=409, detail="Only confirmed captures can be exported")
    if order.is_simulated and not payload.get("allow_simulated", False):
        raise HTTPException(status_code=409, detail="Only confirmed non-simulated captures can be exported")
    return await sheets_ledger.sync_ledger_entry(
        paypal_order_id=order.paypal_order_id, capture_id=order.capture_id,
        amount=order.amount_value, currency=order.currency_code, status="COMPLETED",
    )


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
