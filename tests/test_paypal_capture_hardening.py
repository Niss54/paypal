"""Adversarial regressions for the boundary immediately before provider capture."""
import asyncio
import hashlib
import json
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.db.models import Base, CompletionEvidenceRecord, PayPalOrderRecord
from backend.app.services.procurement.evidence import (
    EvidenceDecision, EvidenceGatedCaptureController, EvidenceSubmission,
    EvidenceValidator,
)
from backend.app.services.procurement.orchestrator import ProcurementOrchestrator


@pytest.fixture
def order():
    return PayPalOrderRecord(
        paypal_order_id="ORDER-HARDENING", work_order_id="WO-TEST", quote_id="Q-TEST",
        equipment_tag="P-101A", vendor_id="VND-001", amount_value="450.00",
        predictive_event_id="EVENT-TEST", create_request_id="CREATE-TEST",
        currency_code="USD", status="AUTHORIZED", authorization_id="AUTH-TEST",
        is_simulated=True, requester_user_id="requester", reviewer_user_id="supervisor",
        mandate_snapshot_json=json.dumps({"risk_lane": "LANE_B_EXCEPTION", "human_approval_required": True}),
    )


def report(**updates):
    fields = dict(
        evidence_id="EVIDENCE-HARDENING", work_order_id="WO-TEST", quote_id="Q-TEST",
        equipment_tag="P-101A", vendor_id="VND-001", service_id="bearing-inspection",
        checklist_items=["Bearing replacement completed", "Laser alignment checked"],
        measurements={"vibration_after_mm_s": 1.25}, file_content="Submitted repair report",
    )
    fields.update(updates)
    return EvidenceSubmission(**fields)


@pytest.mark.parametrize("measurement", ["NaN", "Infinity", "-Infinity", True])
def test_nonphysical_measurement_rejected(order, measurement):
    result = EvidenceValidator.validate(report(measurements={"vibration_after_mm_s": measurement}), order)
    assert result.decision == EvidenceDecision.FAIL
    assert result.measurements_valid is False


@pytest.mark.parametrize("snapshot", [None, "not-json", "{}", '[]', '{"risk_lane":"UNKNOWN","human_approval_required":false}'])
def test_corrupt_mandate_cannot_drop_supervisor_gate(order, snapshot):
    valid = EvidenceValidator.validate(report(), order)
    order.mandate_snapshot_json = snapshot
    allowed, _ = EvidenceGatedCaptureController.verify_capture_eligibility(order, valid)
    assert allowed is False


def test_failed_evidence_flag_overrides_pass_label(order):
    valid = EvidenceValidator.validate(report(), order)
    valid.equipment_match = False
    allowed, _ = EvidenceGatedCaptureController.verify_capture_eligibility(
        order, valid, {"reviewer_id": "supervisor"},
    )
    assert allowed is False


def test_caller_cannot_downgrade_critical_asset_to_lane_a():
    # Attempting to force Lane A on a critical asset with quote exceeding $500 cap (Q-2026-002: $680)
    # must fail closed to Lane B exception requiring human supervisor sign-off.
    result = ProcurementOrchestrator().evaluate_quote("Q-2026-002", policy_lane="LANE_A")
    assert result["risk_lane"] == "LANE_B_EXCEPTION"
    assert result["requires_supervisor_signoff"] is True


def test_critical_asset_defaults_to_lane_b_supervisor_dual_control():
    # Critical assets default to Lane B supervisor dual-control unless explicitly delegated under routine cap.
    result = ProcurementOrchestrator().evaluate_quote("Q-2026-001")
    assert result["risk_lane"] == "LANE_B_EXCEPTION"
    assert result["requires_supervisor_signoff"] is True


@pytest.fixture
def stored_order(order):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(order)
        db.commit()
        orch = ProcurementOrchestrator()
        evidence, result = orch.submit_evidence(db, order.paypal_order_id, report())
        assert result.decision == EvidenceDecision.PASS
        # Sign-off follows the evidence it approves.
        orch.sign_off_supervisor(db, order.paypal_order_id, "supervisor")
        yield db, orch, order, evidence
    engine.dispose()


@pytest.mark.parametrize("mutation", ["order", "equipment", "content", "hash"])
def test_stored_evidence_tampering_blocks_capture(stored_order, mutation):
    db, orch, order, evidence = stored_order
    if mutation == "order":
        evidence.order_id = "OTHER-ORDER"
    elif mutation == "equipment":
        evidence.equipment_tag = "OTHER-ASSET"
    elif mutation == "content":
        evidence.file_content = "Replaced after validation"
    else:
        evidence.file_sha256 = hashlib.sha256(b"Different artifact").hexdigest()
    db.commit()
    success, _, _ = asyncio.run(orch.execute_gated_capture(db, order.paypal_order_id))
    assert success is False
    assert order.capture_id is None


def test_self_report_is_not_independent_sensor_attestation(order):
    order.is_simulated = False
    result = EvidenceValidator.validate(report(is_synthetic=False), order)
    assert result.decision == EvidenceDecision.PASS
    assert result.evidence_provenance == "SUBMITTED_REPORT"


def test_live_money_capture_rejects_unattested_report(stored_order):
    db, orch, order, evidence = stored_order
    order.is_simulated = False
    evidence.is_synthetic = False
    evidence.provenance_classification = "SUBMITTED_REPORT"
    orch.capture_service.client.base_url = "https://api-m.paypal.com"
    orch.capture_service.capture_authorization = AsyncMock()
    db.commit()
    success, reason, _ = asyncio.run(orch.execute_gated_capture(db, order.paypal_order_id))
    assert success is False
    assert "sandbox" in reason.lower() or "attestation" in reason.lower()
    orch.capture_service.capture_authorization.assert_not_awaited()


def test_new_evidence_invalidates_previous_supervisor_approval(stored_order):
    db, orch, order, _ = stored_order
    orch.submit_evidence(db, order.paypal_order_id, report(evidence_id="EVIDENCE-REPLACEMENT"))
    success, reason, _ = asyncio.run(orch.execute_gated_capture(db, order.paypal_order_id))
    assert success is False
    assert "sign" in reason.lower() or "supervisor" in reason.lower()


def test_sandbox_uploaded_report_positive_capture(stored_order):
    from backend.app.services.paypal.schemas import PayPalCaptureResponse, CaptureStatus, Money

    db, orch, order, evidence = stored_order
    order.is_simulated = False
    evidence.is_synthetic = False
    evidence.provenance_classification = "SUBMITTED_REPORT"
    orch.capture_service.client.base_url = "https://api-m.sandbox.paypal.com"
    orch.capture_service.capture_authorization = AsyncMock(return_value=PayPalCaptureResponse(
        capture_id="CAPTURE-PROVIDER", status=CaptureStatus.COMPLETED,
        amount=Money(value="450.00", currency_code="USD"),
    ))
    db.commit()
    success, _, details = asyncio.run(orch.execute_gated_capture(db, order.paypal_order_id))
    assert success is True
    assert details["capture_id"] == "CAPTURE-PROVIDER"
    orch.capture_service.capture_authorization.assert_awaited_once()
