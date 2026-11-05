"""Unit tests for Evidence Validation and the signature 'No Evidence, No Capture' policy gate.
Complies with Master PRD V2 Section 0.3, Section 10, and Section 12.1 (TC-02, TC-03, TC-08).
"""
import json
import pytest
from backend.app.db.models import PayPalOrderRecord
from backend.app.services.procurement.evidence import (
    EvidenceSubmission,
    EvidenceValidator,
    EvidenceDecision,
    EvidenceGatedCaptureController,
)


@pytest.fixture
def sample_order():
    return PayPalOrderRecord(
        paypal_order_id="ORDER-TEST-1001",
        authorization_id="AUTH-TEST-5555",
        status="AUTHORIZED",
        work_order_id="WO-2026-P101",
        predictive_event_id="EVT-VIB-001",
        equipment_tag="P-101A",
        quote_id="quote-apex-01",
        vendor_id="apex-diagnostics",
        amount_value="450.00",
        currency_code="USD",
        requester_user_id="agent-procure-01",
        mandate_snapshot_json=json.dumps({
            "risk_lane": "LANE_A_ROUTINE",
            "human_approval_required": False,
        }),
    )


def test_evidence_validation_success(sample_order):
    submission = EvidenceSubmission(
        evidence_id="EVD-TEST-001",
        work_order_id="WO-2026-P101",
        quote_id="quote-apex-01",
        equipment_tag="P-101A",
        vendor_id="apex-diagnostics",
        service_id="bearing-inspection",
        checklist_items=[
            "Asset tag and serial number physically verified",
            "Disassembly and bearing replacement executed per SOP",
            "Laser shaft alignment completed",
        ],
        measurements={"vibration_after_mm_s": 1.20},
    )

    res = EvidenceValidator.validate(submission, sample_order)
    assert res.decision == EvidenceDecision.PASS
    assert res.work_order_match is True
    assert res.quote_match is True
    assert res.equipment_match is True
    assert res.vendor_match is True
    assert res.service_scope_match is True
    assert res.measurements_valid is True
    assert len(res.reason_codes) == 0


def test_evidence_work_order_mismatch_fails(sample_order):
    submission = EvidenceSubmission(
        evidence_id="EVD-TEST-002",
        work_order_id="WO-WRONG-999",  # Wrong WO
        quote_id="quote-apex-01",
        equipment_tag="P-101A",
        vendor_id="apex-diagnostics",
        service_id="bearing-inspection",
        checklist_items=["Asset verified and completed"],
        measurements={"vibration_after_mm_s": 1.45},
    )

    res = EvidenceValidator.validate(submission, sample_order)
    assert res.decision == EvidenceDecision.FAIL
    assert res.work_order_match is False
    assert any("EVD-WO-MISMATCH" in r for r in res.reason_codes)


def test_evidence_quote_mismatch_fails(sample_order):
    submission = EvidenceSubmission(
        evidence_id="EVD-TEST-QUOTE-FAIL",
        work_order_id="WO-2026-P101",
        quote_id="quote-forged-999",  # Wrong Quote
        equipment_tag="P-101A",
        vendor_id="apex-diagnostics",
        service_id="bearing-inspection",
        checklist_items=["Asset verified and completed"],
        measurements={"vibration_after_mm_s": 1.45},
    )

    res = EvidenceValidator.validate(submission, sample_order)
    assert res.decision == EvidenceDecision.FAIL
    assert res.quote_match is False
    assert any("EVD-QUOTE-MISMATCH" in r for r in res.reason_codes)


def test_evidence_measurement_excursion_fails(sample_order):
    submission = EvidenceSubmission(
        evidence_id="EVD-TEST-003",
        work_order_id="WO-2026-P101",
        quote_id="quote-apex-01",
        equipment_tag="P-101A",
        vendor_id="apex-diagnostics",
        service_id="bearing-inspection",
        checklist_items=["Asset verified and completed"],
        measurements={"vibration_after_mm_s": 5.80},  # Fails limit (> 4.50 mm/s)
    )

    res = EvidenceValidator.validate(submission, sample_order)
    assert res.decision == EvidenceDecision.FAIL
    assert res.measurements_valid is False
    assert any("EVD-MEASUREMENT-EXCURSION" in r for r in res.reason_codes)


def test_evidence_missing_measurement_fails(sample_order):
    submission = EvidenceSubmission(
        evidence_id="EVD-TEST-NO-VIB",
        work_order_id="WO-2026-P101",
        quote_id="quote-apex-01",
        equipment_tag="P-101A",
        vendor_id="apex-diagnostics",
        service_id="bearing-inspection",
        checklist_items=["Asset verified and completed"],
        measurements={"temperature_c": 35.0},  # Missing vibration_after_mm_s
    )

    res = EvidenceValidator.validate(submission, sample_order)
    assert res.decision == EvidenceDecision.FAIL
    assert res.measurements_valid is False
    assert any("EVD-MEASUREMENT-MISSING" in r for r in res.reason_codes)


def test_no_evidence_no_capture_blocks_capture(sample_order):
    """The Signature Differentiator: Attempting capture without verified evidence is blocked."""
    eligible, reason = EvidenceGatedCaptureController.verify_capture_eligibility(
        order_record=sample_order,
        evidence_result=None,
    )
    assert eligible is False
    assert "No Evidence, No Capture" in reason


def test_lane_b_requires_supervisor_signoff(sample_order):
    """Lane B exceptions require human supervisor sign-off before capture."""
    sample_order.mandate_snapshot_json = json.dumps({
        "risk_lane": "LANE_B_EXCEPTION",
        "human_approval_required": True,
    })

    submission = EvidenceSubmission(
        evidence_id="EVD-TEST-004",
        work_order_id="WO-2026-P101",
        quote_id="quote-apex-01",
        equipment_tag="P-101A",
        vendor_id="apex-diagnostics",
        service_id="bearing-inspection",
        checklist_items=["Asset tag physically verified", "Completed bearing replacement per SOP"],
        measurements={"vibration_after_mm_s": 1.25},
    )
    ev_res = EvidenceValidator.validate(submission, sample_order)
    assert ev_res.decision == EvidenceDecision.PASS

    # Without supervisor signature -> Blocked
    eligible, reason = EvidenceGatedCaptureController.verify_capture_eligibility(
        order_record=sample_order,
        evidence_result=ev_res,
        supervisor_auth=None,
    )
    assert eligible is False
    assert "Human Dual-Signature Required" in reason

    # Separation of duties violation (Requester attempts self-approval) -> Blocked
    eligible_self, reason_self = EvidenceGatedCaptureController.verify_capture_eligibility(
        order_record=sample_order,
        evidence_result=ev_res,
        supervisor_auth={"reviewer_id": "agent-procure-01", "notes": "Self approval"},
    )
    assert eligible_self is False
    assert "Separation of Duties Violation" in reason_self

    # With distinct supervisor signature -> Allowed
    eligible, reason = EvidenceGatedCaptureController.verify_capture_eligibility(
        order_record=sample_order,
        evidence_result=ev_res,
        supervisor_auth={"reviewer_id": "supervisor-chief-42", "notes": "Approved after inspection"},
    )
    assert eligible is True
    assert "Eligible" in reason


def test_capture_eligible_nominal_lane_a(sample_order):
    submission = EvidenceSubmission(
        evidence_id="EVD-TEST-005",
        work_order_id="WO-2026-P101",
        quote_id="quote-apex-01",
        equipment_tag="P-101A",
        vendor_id="apex-diagnostics",
        service_id="bearing-inspection",
        checklist_items=["Verified alignment and completed replacement"],
        measurements={"vibration_after_mm_s": 1.30},
    )
    ev_res = EvidenceValidator.validate(submission, sample_order)

    eligible, reason = EvidenceGatedCaptureController.verify_capture_eligibility(
        order_record=sample_order,
        evidence_result=ev_res,
    )
    assert eligible is True
    assert "Eligible" in reason
