"""IBM Maximo Enterprise Asset Management OSLC REST Connector.

Connects industrial work order lifecycle to IBM Maximo Asset Management
using the Open Services for Lifecycle Collaboration (OSLC) REST API (/maximo/oslc/os/mxwo).
"""
import hashlib
import logging
import os
from typing import Any, Dict, Optional
import httpx
from backend.app.services.erp.models import (
    ERPConnectorMode,
    IBMMaximoWorkOrderRequest,
    IBMMaximoWorkOrderResponse,
    utcnow_str,
)

logger = logging.getLogger(__name__)


class IBMMaximoConnector:
    """Connects industrial procurement workflow to IBM Maximo OSLC REST."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.base_url = (base_url or os.getenv("MAXIMO_URL", "")).rstrip("/")
        self.api_key = api_key or os.getenv("MAXIMO_API_KEY", "")

    @property
    def is_live_configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    async def sync_work_order(
        self, req: IBMMaximoWorkOrderRequest
    ) -> IBMMaximoWorkOrderResponse:
        """Create or update a Work Order in IBM Maximo via OSLC REST."""
        # Determine status: COMP if captured & evidence verified; APPR if pre-authorized; WAPPR if draft
        if req.paypal_capture_id and req.evidence_hash:
            maximo_status = "COMP"
            evidence_validated = True
        elif req.paypal_auth_id:
            maximo_status = "APPR"
            evidence_validated = False
        else:
            maximo_status = "WAPPR"
            evidence_validated = False

        seed = f"{req.asset_num}:{req.vendor_id}:{req.estimated_cost}".encode()
        wonum = req.wonum or f"WO-MX-{int(hashlib.sha256(seed).hexdigest()[:6], 16) % 900000 + 100000}"

        oslc_payload = {
            "spi:wonum": wonum,
            "spi:siteid": req.site_id,
            "spi:assetnum": req.asset_num,
            "spi:worktype": req.work_type.value,
            "spi:description": req.description,
            "spi:status": maximo_status,
            "spi:estmatcost": float(req.estimated_cost),
            "spi:vendor": req.vendor_id,
            "spi:glcreditacct": req.gl_credit_account,
            "spi:paypal_auth_ref": req.paypal_auth_id or "",
            "spi:paypal_capture_ref": req.paypal_capture_id or "",
            "spi:evidence_hash": req.evidence_hash or "",
        }

        # If live credentials exist, dispatch OSLC REST request
        if self.is_live_configured:
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "apikey": self.api_key,
                "x-method-override": "PATCH" if req.wonum else "POST",
            }
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    target_url = f"{self.base_url}/oslc/os/mxwo"
                    res = await client.post(target_url, json=oslc_payload, headers=headers)
                    if res.status_code in (200, 201):
                        return IBMMaximoWorkOrderResponse(
                            success=True,
                            wonum=wonum,
                            status=maximo_status,
                            oslc_uri=f"{self.base_url}/oslc/os/mxwo/{wonum}",
                            asset_num=req.asset_num,
                            site_id=req.site_id,
                            paypal_auth_ref=req.paypal_auth_id,
                            paypal_capture_ref=req.paypal_capture_id,
                            evidence_validated=evidence_validated,
                            connector_mode=ERPConnectorMode.LIVE_REST,
                            oslc_payload_preview=oslc_payload,
                        )
                    else:
                        logger.error("IBM Maximo live call returned HTTP %s: %s", res.status_code, res.text)
                        raise RuntimeError(f"IBM Maximo live dispatch failed with HTTP {res.status_code}: {res.text}")
            except Exception as exc:
                logger.error("IBM Maximo live dispatch error: %s", exc)
                raise RuntimeError(f"IBM Maximo live dispatch error: {exc}") from exc

        return IBMMaximoWorkOrderResponse(
            success=True,
            wonum=wonum,
            status=maximo_status,
            oslc_uri=f"https://maximo.enterprise.internal/maximo/oslc/os/mxwo/{wonum}",
            asset_num=req.asset_num,
            site_id=req.site_id,
            paypal_auth_ref=req.paypal_auth_id,
            paypal_capture_ref=req.paypal_capture_id,
            evidence_validated=evidence_validated,
            connector_mode=ERPConnectorMode.ENTERPRISE_SANDBOX,
            oslc_payload_preview=oslc_payload,
        )
