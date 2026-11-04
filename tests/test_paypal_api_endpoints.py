"""Integration tests for PayPal Orders v2 & Evidence-Gated Procurement API Endpoints.
Complies with Master PRD V2 Sections 0.2, 0.3, 6.1, 9.4, 9.5, and 12.1.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.db.database import Base, get_db, init_db
from backend.app.main import app

# Setup isolated SQLite database for integration test using StaticPool so in-memory DB is shared
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)
init_db(target_engine=test_engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_get_procurement_incident():
    """Verify endpoint returns canonical NASA IMS bearing anomaly scenario."""
    res = client.get("/api/procurement/incident")
    assert res.status_code == 200
    data = res.json()
    assert data["equipment_id"] == "P-101A"
    assert "NASA IMS" in data["anomaly_source"]
    assert data["measured_value_mm_s"] == 4.82
    assert data["alarm_threshold_mm_s"] == 4.50
    assert data["status"] == "CRITICAL_ANOMALY_EXCURSION"


def test_get_procurement_quotes():
    """Verify comparison quotes are returned with explicit synthetic demo disclosures."""
    res = client.get("/api/procurement/quotes")
    assert res.status_code == 200
    quotes = res.json()
    assert len(quotes) == 3
    # Check synthetic labeling on all demo quotes
    for q in quotes:
        assert q["is_synthetic"] is True
        assert "[SYNTHETIC DEMO QUOTE]" in q["synthetic_label"]
    # Check that only one is direct paypal sandbox merchant
    sandbox_merchants = [q for q in quotes if q["is_direct_paypal_sandbox_merchant"]]
    assert len(sandbox_merchants) == 1
    assert sandbox_merchants[0]["vendor_id"] == "VND-001"


def test_evaluate_quote_mandate():
    """Verify quote evaluation enforces deterministic budget and allowlist constraints."""
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
    """Full lifecycle: Create -> Authorize -> Attempt Capture without Evidence (Blocked)
    -> Submit Evidence -> Attempt Capture without Supervisor Sign-off (Blocked)
    -> Supervisor Sign-off -> Gated Capture (Success) -> Audit Lineage.
    """
    # 1. Create PayPal Order from approved quote
    create_res = client.post(
        "/api/paypal/orders",
        json={"quote_id": "Q-2026-001", "actor": "procurement-bot-01"},
    )
    assert create_res.status_code == 201
    order_data = create_res.json()
    order_id = order_data["paypal_order_id"]
    assert order_id is not None
    assert order_data["status"] == "ORDER_CREATED"
    assert order_data["amount_value"] == "450.00"
    assert order_data["currency_code"] == "USD"
    assert order_data["work_order_id"] == "WO-2026-IMS-001"

    # 2. Authorize the PayPal Order
    auth_res = client.post(f"/api/paypal/orders/{order_id}/authorize")
    assert auth_res.status_code == 200
    auth_data = auth_res.json()
    assert auth_data["status"] == "AUTHORIZED"
    assert auth_data["authorization_id"] is not None

    # 3. Attempt Capture WITHOUT Evidence -> MUST BE BLOCKED (HTTP 403)
    cap_premature_res = client.post(f"/api/paypal/orders/{order_id}/capture")
    assert cap_premature_res.status_code == 403
    err_data = cap_premature_res.json()
    assert "EvidenceGateBlocked" in str(err_data)
    assert "No Evidence, No Capture" in str(err_data)

    # 4. Submit Physical Completion Evidence
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

    # 5. Attempt Capture WITH Evidence but WITHOUT Supervisor Sign-Off (Lane B) -> MUST BE BLOCKED (HTTP 403)
    cap_unsigned_res = client.post(f"/api/paypal/orders/{order_id}/capture")
    assert cap_unsigned_res.status_code == 403
    unsigned_err = cap_unsigned_res.json()
    assert "Dual-Control Required" in str(unsigned_err) or "supervisor" in str(unsigned_err).lower()

    # 6. Supervisor Dual-Control Sign-Off
    signoff_res = client.post(
        f"/api/paypal/orders/{order_id}/sign-off",
        json={"supervisor_id": "SUP-CHIEF-09", "notes": "Vibration measurements and SOP verified."},
    )
    assert signoff_res.status_code == 200
    assert signoff_res.json()["supervisor_id"] == "SUP-CHIEF-09"

    # 7. Execute Gated Capture -> MUST SUCCEED (HTTP 200)
    cap_success_res = client.post(
        f"/api/paypal/orders/{order_id}/capture",
        json={"idempotency_key": f"idemp-{order_id}"},
    )
    assert cap_success_res.status_code == 200
    cap_data = cap_success_res.json()
    assert cap_data["success"] is True
    assert cap_data["capture"]["status"] == "COMPLETED"
    assert cap_data["capture"]["capture_id"] is not None

    # 8. Check Transaction Lineage & Audit
    audit_res = client.get(f"/api/paypal/orders/{order_id}/audit")
    assert audit_res.status_code == 200
    audit = audit_res.json()
    assert audit["order_id"] == order_id
    assert audit["status"] == "CAPTURED"
    assert len(audit["lineage_stages"]) == 7
    stage_titles = [s["title"] for s in audit["lineage_stages"]]
    assert "Predictive Anomaly Excursion" in stage_titles
    assert "GraphRAG Diagnostic Attribution" in stage_titles
    assert "PayPal Orders v2 Two-Phase Authorization" in stage_titles
    assert "Evidence-Gated Capture & Settlement" in stage_titles


def test_void_uncaptured_order():
    """Verify an authorized but uncaptured order can be voided."""
    create_res = client.post("/api/paypal/orders", json={"quote_id": "Q-2026-001"})
    order_id = create_res.json()["paypal_order_id"]
    client.post(f"/api/paypal/orders/{order_id}/authorize")

    void_res = client.post(
        f"/api/paypal/orders/{order_id}/void",
        json={"reason": "Asset decommissioned; maintenance cancelled"},
    )
    assert void_res.status_code == 200
    data = void_res.json()
    assert data["status"] == "VOIDED"
