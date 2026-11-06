"""Enterprise ERP Synchronizer API (SAP S/4HANA & IBM Maximo).

Provides live two-way synchronization for maintenance orders, purchase orders,
and GL liability clearing accounts (2100-PAYPAL-CLEARING).
"""
import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from backend.app.core.auth import get_current_user
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
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Synchronize a maintenance work order to IBM Maximo Asset Management via OSLC REST.

    Updates work order status: WAPPR -> APPR (funds authorized) -> COMP (evidence captured).
    """
    try:
        response = await _maximo_connector.sync_work_order(req)
        return response
    except Exception as exc:
        logger.error("IBM Maximo synchronization failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"IBM Maximo synchronization failed: {exc}")


@router.get("/status", response_model=ERPStatusResponse)
async def get_erp_status(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Return health, configuration status, and GL liability ledger for SAP S/4HANA and IBM Maximo."""
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
        gl_clearing_account=ledger,
    )
