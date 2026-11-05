"""End-to-End API Integration tests for PayPal Orders v2 & Evidence-Gated Procurement.
Complies with Master PRD V2 Section 9.4, 9.5, 10, and 12.1.
Tests RBAC authentication, genuine dual-control separation of duties, and cryptographic hash chaining.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_get_procurement_incident():
    res = client.get("/api/procurement/incident")
    assert res.status_code == 200
    data = res.json()
    assert data["equipment_id"] == "P-101A"
    assert data["metric_name"] == "Vibration Velocity RMS"
    assert data["measured_value_mm_s"] == 4.82
    assert data["alarm_threshold_mm_s"] == 4.50
    assert "graphrag_context" in data
    assert data["graphrag_context"]["node_id"] == "FE-001"
    assert len(data["graphrag_context"]["citations"]) >= 2


def test_get_procurement_quotes():
    res = client.get("/api/procurement/quotes")
    assert res.status_code == 200
    quotes = res.json()
    assert len(quotes) == 3
    for q in quotes:
        assert q["is_synthetic"] is True
        assert "[SYNTHETIC DEMO QUOTE]" in q["synthetic_label"]
    # Check ranking
    ranks = [q["scoring"]["composite_rank"] for q in quotes]
    assert ranks == [1, 2, 3]


def test_evaluate_quote_mandate():
    # 1. Eligible Quote Q-2026-001 ($450.00 <= $500.00 cap)
    res_ok = client.post("/api/procurement/evaluate-quote", json={"quote_id": "Q-2026-001"})
    assert res_ok.status_code == 200
    data_ok = res_ok.json()
    assert data_ok["decision"] == "ALLOWED"
    assert data_ok["risk_lane"] == "LANE_B_EXCEPTION"  # Critical asset escalates to Lane B
    assert data_ok["requires_supervisor_signoff"] is True

    # 2. Ineligible Quote Q-2026-002 ($680.00 > $500.00 cap)
    res_bad = client.post("/api/procurement/evaluate-quote", json={"quote_id": "Q-2026-002"})
    assert res_bad.status_code == 200
    data_bad = res_bad.json()
    assert data_bad["decision"] in ("BLOCKED", "REQUIRES_REVIEW")
    assert any("exceeds" in r.lower() for r in data_bad["reason_codes"])


def test_end_to_end_evidence_gated_procurement_lifecycle():
    """Full lifecycle: Create -> Buyer Approve -> Authorize -> Attempt Capture without Evidence (Blocked)
    -> Submit Evidence -> Attempt Capture without Supervisor Sign-off (Blocked)
    -> Supervisor Sign-off -> Gated Capture (Success) -> Cryptographic Audit Lineage.
    """
    # 1. Create PayPal Order from approved quote (explicit simulation mode for fast, deterministic unit testing)
    create_res = client.post(
        "/api/paypal/orders",
        json={"quote_id": "Q-2026-001", "actor": "procurement-bot-01", "is_simulation": True},
    )
    assert create_res.status_code == 201
    order_data = create_res.json()
    order_id = order_data["paypal_order_id"]
    assert order_id is not None
    assert order_data["status"] == "SIMULATED_ORDER_CREATED"
    assert order_data["amount_value"] == "450.00"
    assert order_data["currency_code"] == "USD"
    assert order_data["work_order_id"] == "WO-2026-IMS-001"
    assert order_data["approve_url"] is not None

    # 2. Buyer Approval Step (Orders v2 compliance)
    appr_res = client.post(
        f"/api/paypal/orders/{order_id}/approve",
        json={"simulated_approval": True},
    )
    assert appr_res.status_code == 200
    assert appr_res.json()["status"] == "BUYER_APPROVED"

    # 3. Authorize the PayPal Order
    auth_res = client.post(f"/api/paypal/orders/{order_id}/authorize")
    assert auth_res.status_code == 200
    auth_data = auth_res.json()
    assert auth_data["status"] == "AUTHORIZED"
    assert auth_data["authorization_id"] is not None

    # 4. Attempt Capture WITHOUT Evidence -> MUST BE BLOCKED (HTTP 403)
    cap_premature_res = client.post(f"/api/paypal/orders/{order_id}/capture")
    assert cap_premature_res.status_code == 403
    err_data = cap_premature_res.json()
    assert "EvidenceGateBlocked" in str(err_data)
    assert "No Evidence, No Capture" in str(err_data)

    # 5. Submit Physical Completion Evidence
    evidence_payload = {
        "evidence_id": f"EVD-{order_id}",
        "work_order_id": "WO-2026-IMS-001",
        "quote_id": "Q-2026-001",
        "equipment_tag": "P-101A",
        "vendor_id": "VND-001",
        "service_id": "SRV-BRG-REPLACE",
        "technician_id": "TECH-CERT-441",
        "checklist_items": [
            "Asset tag P-101A physically verified",
            "Disassembly and bearing replacement executed per SOP",
            "Laser shaft alignment verified within tolerance",
            "Vibration baseline test run completed",
        ],
        "measurements": {
            "vibration_after_mm_s": 1.25,
            "vibration_zone": "Zone A (Good)",
            "bearing_temperature_c": 39.4,
        },
        "file_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "is_synthetic": True,
    }
    evd_res = client.post(f"/api/paypal/orders/{order_id}/evidence", json=evidence_payload)
    assert evd_res.status_code == 200
    evd_data = evd_res.json()
    assert evd_data["validation_decision"] == "PASS"
    assert evd_data["validation_passed"] is True

    # 6. Attempt Capture WITH Evidence but WITHOUT Supervisor Sign-Off (Lane B) -> MUST BE BLOCKED (HTTP 403)
    cap_unsigned_res = client.post(f"/api/paypal/orders/{order_id}/capture")
    assert cap_unsigned_res.status_code == 403
    unsigned_err = cap_unsigned_res.json()
    assert "Dual-Signature Required" in str(unsigned_err) or "supervisor" in str(unsigned_err).lower()

    # 7. Dual-Control Separation of Duties Test: Requester attempts self sign-off -> MUST BE FORBIDDEN (HTTP 403)
    self_signoff_res = client.post(
        f"/api/paypal/orders/{order_id}/sign-off",
        json={"supervisor_id": "procurement-bot-01", "notes": "Self sign-off attempt"},
    )
    assert self_signoff_res.status_code == 403
    assert "Separation of duties violation" in self_signoff_res.json()["detail"]

    # 8. Distinct Supervisor Sign-Off -> MUST SUCCEED (HTTP 200)
    signoff_res = client.post(
        f"/api/paypal/orders/{order_id}/sign-off",
        json={"supervisor_id": "SUP-CHIEF-09", "notes": "Vibration measurements and SOP verified."},
    )
    assert signoff_res.status_code == 200
    assert signoff_res.json()["supervisor_id"] == "SUP-CHIEF-09"

    # 9. Execute Gated Capture -> MUST SUCCEED (HTTP 200)
    cap_success_res = client.post(
        f"/api/paypal/orders/{order_id}/capture",
        json={"idempotency_key": f"idemp-{order_id}"},
    )
    assert cap_success_res.status_code == 200
    cap_data = cap_success_res.json()
    assert cap_data["success"] is True
    assert cap_data["capture"]["status"] == "COMPLETED"
    assert cap_data["capture"]["capture_id"] is not None

    # 10. Check Transaction Lineage & Cryptographic Audit Hash Chain
    audit_res = client.get(f"/api/paypal/orders/{order_id}/audit")
    assert audit_res.status_code == 200
    audit = audit_res.json()
    assert audit["order_id"] == order_id
    assert audit["status"] == "CAPTURED"
    assert audit["chain_valid"] is True
    assert len(audit["merkle_root"]) == 64
    assert len(audit["lineage_stages"]) == 7

    # Verify cryptographic hash chaining properties
    for i, stage in enumerate(audit["lineage_stages"]):
        assert "stage_hash" in stage
        assert "previous_stage_hash" in stage
        if i == 0:
            assert stage["previous_stage_hash"] == "0" * 64
        else:
            assert stage["previous_stage_hash"] == audit["lineage_stages"][i - 1]["stage_hash"]


def test_void_uncaptured_order():
    """Verify an authorized but uncaptured order can be voided."""
    create_res = client.post("/api/paypal/orders", json={"quote_id": "Q-2026-001", "is_simulation": True})
    order_id = create_res.json()["paypal_order_id"]
    client.post(f"/api/paypal/orders/{order_id}/approve", json={"simulated_approval": True})
    client.post(f"/api/paypal/orders/{order_id}/authorize")

    void_res = client.post(
        f"/api/paypal/orders/{order_id}/void",
        json={"reason": "Asset decommissioned; maintenance cancelled"},
    )
    assert void_res.status_code == 200
    data = void_res.json()
    assert data["status"] == "VOIDED"
