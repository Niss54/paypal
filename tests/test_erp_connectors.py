"""Comprehensive tests for Enterprise ERP Connectors (SAP S/4HANA & IBM Maximo).

Verifies OData/OSLC schema fidelity, double-entry GL liability tracking (2100-PAYPAL-CLEARING),
and evidence-gated completion settlement synchronization.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.core.auth import create_access_token
from backend.app.main import app
from backend.app.services.erp.ibm_maximo import IBMMaximoConnector
from backend.app.services.erp.models import (
    ERPConnectorMode,
    IBMMaximoWorkOrderRequest,
    MaximoWorkType,
    SAPMaintenanceOrderRequest,
    SAPOrderType,
)
from backend.app.services.erp.sap_s4hana import SAPS4HANAConnector

client = TestClient(app)


@pytest.mark.asyncio
async def test_sap_s4hana_connector_lifecycle():
    connector = SAPS4HANAConnector()

    # Step 1: Pre-authorization commitment sync
    req = SAPMaintenanceOrderRequest(
        equipment_id="P-101A",
        order_type=SAPOrderType.PM01,
        short_text="Emergency Bearing Replacement on P-101A",
        vendor_id="US-MOT-10821",
        vendor_name="Motion Industries",
        estimated_amount="450.00",
        paypal_order_id="ORD-TEST-12345",
        paypal_auth_id="AUTH-TEST-67890",
    )
    res = await connector.sync_maintenance_order(req)
    assert res.success is True
    assert res.status == "REL"  # Released
    assert res.gl_clearing_account == "2100-PAYPAL-CLEARING"
    assert res.accounting_posting.debit_account == "6100-MAINT-EXPENSE"
    assert res.accounting_posting.credit_account == "2100-PAYPAL-CLEARING"
    assert res.accounting_posting.cleared is False
    assert res.sap_order_id.startswith("4")

    # Step 2: Evidence-backed capture and GL liability clearance
    req_captured = SAPMaintenanceOrderRequest(
        equipment_id="P-101A",
        order_type=SAPOrderType.PM01,
        short_text="Emergency Bearing Replacement on P-101A",
        vendor_id="US-MOT-10821",
        vendor_name="Motion Industries",
        estimated_amount="450.00",
        paypal_order_id="ORD-TEST-12345",
        paypal_auth_id="AUTH-TEST-67890",
        paypal_capture_id="CAP-TEST-99999",
        evidence_hash="a" * 64,
    )
    res_captured = await connector.sync_maintenance_order(req_captured)
    assert res_captured.success is True
    assert res_captured.status == "TECO"  # Technically Completed
    assert res_captured.accounting_posting.cleared is True
    assert res_captured.accounting_posting.clearing_document is not None

    # Step 3: Ledger verification
    ledger = connector.get_ledger_status()
    assert ledger["gl_account"] == "2100-PAYPAL-CLEARING"
    assert ledger["settled_cleared_usd"] == 450.00


@pytest.mark.asyncio
async def test_ibm_maximo_connector_lifecycle():
    connector = IBMMaximoConnector()

    # Step 1: Draft / WAPPR
    req_draft = IBMMaximoWorkOrderRequest(
        asset_num="P-101A",
        description="Overhaul bearing assembly",
        vendor_id="US-MOT-10821",
        estimated_cost="450.00",
    )
    res_draft = await connector.sync_work_order(req_draft)
    assert res_draft.success is True
    assert res_draft.status == "WAPPR"
    assert res_draft.evidence_validated is False

    # Step 2: Approved with PayPal Authorization
    req_appr = IBMMaximoWorkOrderRequest(
        wonum=res_draft.wonum,
        asset_num="P-101A",
        description="Overhaul bearing assembly",
        vendor_id="US-MOT-10821",
        estimated_cost="450.00",
        paypal_auth_id="AUTH-TEST-67890",
    )
    res_appr = await connector.sync_work_order(req_appr)
    assert res_appr.success is True
    assert res_appr.status == "APPR"

    # Step 3: Completed with Evidence and PayPal Capture
    req_comp = IBMMaximoWorkOrderRequest(
        wonum=res_draft.wonum,
        asset_num="P-101A",
        description="Overhaul bearing assembly",
        vendor_id="US-MOT-10821",
        estimated_cost="450.00",
        paypal_auth_id="AUTH-TEST-67890",
        paypal_capture_id="CAP-TEST-99999",
        evidence_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )
    res_comp = await connector.sync_work_order(req_comp)
    assert res_comp.success is True
    assert res_comp.status == "COMP"
    assert res_comp.evidence_validated is True


def test_erp_api_endpoints_governed():
    payload = {
        "equipment_id": "P-101A",
        "order_type": "PM01",
        "short_text": "Bearing repair on P-101A",
        "plant": "1000",
        "work_center": "MECH-01",
        "cost_center": "CC-MUMBAI-01",
        "gl_clearing_account": "2100-PAYPAL-CLEARING",
        "vendor_id": "US-MOT-10821",
        "vendor_name": "Motion Industries",
        "estimated_amount": "450.00",
        "currency": "USD",
        "paypal_auth_id": "AUTH-TEST-123",
    }

    # 1. Malformed / forged token rejected
    bad_token_res = client.post(
        "/api/erp/sap/sync",
        json=payload,
        headers={"Authorization": "Bearer invalid.forged.jwt.token"},
    )
    assert bad_token_res.status_code == 401

    # 2. Authenticated operator request
    token = create_access_token("operator-1", ["operator"])
    headers = {"Authorization": f"Bearer {token}"}

    sap_res = client.post("/api/erp/sap/sync", json=payload, headers=headers)
    assert sap_res.status_code == 200
    sap_data = sap_res.json()
    assert sap_data["success"] is True
    assert sap_data["status"] == "REL"
    assert sap_data["accounting_posting"]["credit_account"] == "2100-PAYPAL-CLEARING"

    # 3. Status check endpoint
    status_res = client.get("/api/erp/status", headers=headers)
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert "sap_s4hana" in status_data
    assert "ibm_maximo" in status_data
    assert status_data["gl_clearing_account"]["gl_account"] == "2100-PAYPAL-CLEARING"
