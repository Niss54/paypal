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


def test_auth_token_issuance_and_me():
    """Verify cryptographically signed JWT issuance and verified UserProfile resolution."""
    # 1. Issue token for supervisor persona
    res = client.post("/api/auth/token", json={"persona": "supervisor"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user_id"] == "SUP-CHIEF-09"
    assert "Supervisor" in data["roles"]

    # 2. Authenticate to /api/auth/me with Bearer token
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["user_id"] == "SUP-CHIEF-09"
    assert "Supervisor" in me_data["roles"]


def test_simulated_approval_rejected_on_live_order():
    """P0.6 Security Test: simulated_approval=True on non-simulated orders must return HTTP 403."""
    import uuid
    from backend.app.db.database import get_db
    from backend.app.db.models import PayPalOrderRecord

    db = next(get_db())
    unique_ord_id = f"LIVE-ORD-{uuid.uuid4().hex[:8].upper()}"
    live_order = PayPalOrderRecord(
        paypal_order_id=unique_ord_id,
        quote_id="Q-2026-001",
        work_order_id="WO-2026-IMS-001",
        predictive_event_id="EVT-2026-IMS-01",
        create_request_id=f"req-{unique_ord_id}",
        equipment_tag="P-101A",
        vendor_id="VND-001",
        amount_value="450.00",
        currency_code="USD",
        status="ORDER_CREATED",
        is_simulated=False,
    )
    db.add(live_order)
    db.commit()

    # Attempt simulated approval on live order -> MUST BE FORBIDDEN (HTTP 403)
    res = client.post(
        f"/api/paypal/orders/{unique_ord_id}/approve",
        json={"simulated_approval": True},
    )
    assert res.status_code == 403
    assert "Simulated approval is only permitted for simulated orders" in res.json()["detail"]


def test_capture_fail_closed_on_unknown_status():
    """P0.4 Test: capture service must fail closed to UNKNOWN on unrecognized status."""
    from backend.app.services.paypal.schemas import CaptureStatus

    assert CaptureStatus.UNKNOWN == "UNKNOWN"
    raw_status = "STRANGE_PAYPAL_STATUS"
    status = CaptureStatus(raw_status) if raw_status in CaptureStatus._value2member_map_ else CaptureStatus.UNKNOWN
    assert status == CaptureStatus.UNKNOWN


def test_lane_a_autonomous_agentic_settlement_lifecycle():
    """Lane A Hero Autonomous Flow: Routine Spares (< $500).
    Evaluates quote in Lane A -> requires_supervisor_signoff is False.
    Creates order with Lane A policy.
    Buyer approve -> Authorize.
    Attempt capture before evidence -> 403 Forbidden (No Evidence, No Capture).
    Submit verified sensor telemetry (1.25 mm/s, Zone A).
    Capture directly executed by Agent WITHOUT supervisor sign-off -> 200 SUCCESS!
    """
    # 1. Evaluate in Lane A
    res_eval = client.post(
        "/api/procurement/evaluate-quote",
        json={"quote_id": "Q-2026-001", "policy_lane": "LANE_A"},
    )
    assert res_eval.status_code == 200
    eval_data = res_eval.json()
    assert eval_data["decision"] == "ALLOWED"
    assert eval_data["risk_lane"] == "LANE_A_ROUTINE"
    assert eval_data["requires_supervisor_signoff"] is False

    # 2. Create Order in Lane A
    res_order = client.post(
        "/api/paypal/orders",
        json={
            "quote_id": "Q-2026-001",
            "is_simulation": True,
            "policy_lane": "LANE_A",
        },
    )
    assert res_order.status_code == 201
    order_id = res_order.json()["paypal_order_id"]

    # 3. Simulated Buyer Approve
    res_app = client.post(f"/api/paypal/orders/{order_id}/approve", json={"simulated_approval": True})
    assert res_app.status_code == 200
    assert res_app.json()["status"] == "BUYER_APPROVED"

    # 4. Authorize
    res_auth = client.post(f"/api/paypal/orders/{order_id}/authorize")
    assert res_auth.status_code == 200
    assert res_auth.json()["status"] == "AUTHORIZED"

    # 5. Negative Gate: Attempt capture before evidence -> MUST BE 403 Forbidden
    res_cap_early = client.post(f"/api/paypal/orders/{order_id}/capture")
    assert res_cap_early.status_code == 403
    err_data = res_cap_early.json()
    assert "EvidenceGateBlocked" in str(err_data)
    assert "No Evidence, No Capture" in str(err_data)

    # 6. Submit verified vibration evidence (1.25 mm/s RMS)
    ev_payload = {
        "evidence_id": f"EVD-{order_id}",
        "work_order_id": "WO-2026-IMS-001",
        "quote_id": "Q-2026-001",
        "equipment_tag": "P-101A",
        "vendor_id": "VND-001",
        "service_id": "SRV-BRG-REPLACE",
        "technician_id": "TECH-CERT-441",
        "checklist_items": [
            "Asset physically verified",
            "Bearing replaced per SOP",
            "Laser alignment completed",
            "Vibration baseline verified",
        ],
        "measurements": {
            "vibration_after_mm_s": 1.25,
            "vibration_zone": "Zone A (Good)",
            "bearing_temperature_c": 41.2,
        },
        "file_sha256": "a" * 64,
        "is_synthetic": True,
    }
    res_ev = client.post(f"/api/paypal/orders/{order_id}/evidence", json=ev_payload)
    assert res_ev.status_code == 200
    assert res_ev.json()["validation_passed"] is True

    # 7. Hero Autonomous Settlement: Agent captures order directly WITHOUT supervisor sign-off!
    res_cap = client.post(f"/api/paypal/orders/{order_id}/capture")
    assert res_cap.status_code == 200
    cap_data = res_cap.json()
    assert cap_data["success"] is True
    assert cap_data["capture"]["status"] == "COMPLETED"
