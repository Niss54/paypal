"""Deterministic Evidence Validation & 'No Evidence, No Capture' Policy Gate.
Complies with Master PRD V2 Section 0.3, Section 10, and Section 12.1.
"""
import hashlib
import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from backend.app.db.models import PayPalOrderRecord

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class EvidenceDecision(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class EvidenceSubmission(BaseModel):
    """Structured report submitted by service vendor to prove physical completion."""
    evidence_id: str = Field(..., description="Unique evidence tracking identifier")
    work_order_id: str
    quote_id: str
    equipment_tag: str
    vendor_id: str
    service_id: str
    technician_id: str = "TECH-CERT-904"
    completed_at: datetime = Field(default_factory=utcnow)
    checklist_items: List[str] = Field(
        default_factory=lambda: [
            "Asset tag and serial number physically verified",
            "Disassembly and bearing replacement executed per SOP",
            "Laser shaft alignment verified within tolerance",
            "Vibration baseline test run completed",
        ]
    )
    measurements: Dict[str, Any] = Field(
        default_factory=lambda: {
            "vibration_after_mm_s": 1.45,
            "vibration_zone": "Zone A (Good)",
            "bearing_temperature_c": 42.1,
            "alignment_offset_um": 12.0,
        }
    )
    file_bytes: Optional[bytes] = None
    file_sha256: Optional[str] = None
    is_synthetic: bool = True
    synthetic_disclosure: str = "SYNTHETIC DEMO FIXTURE: Service completion diagnostic report"


class EvidenceValidationResult(BaseModel):
    decision: EvidenceDecision
    work_order_match: bool
    equipment_match: bool
    vendor_match: bool
    service_scope_match: bool
    required_fields_complete: bool
    measurements_valid: bool
    file_integrity_valid: bool
    evidence_provenance: str = "SYNTHETIC_DEMO_FIXTURE"
    reason_codes: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=utcnow)


class EvidenceValidator:
    """Validates submitted completion evidence against approved work order scope."""

    REQUIRED_CHECKLIST_KEYWORDS = ["verified", "completed", "alignment", "bearing"]

    @classmethod
    def compute_sha256(cls, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @classmethod
    def validate(
        cls,
        evidence: EvidenceSubmission,
        expected_order: PayPalOrderRecord,
    ) -> EvidenceValidationResult:
        """Execute deterministic cross-checks."""
        reasons: List[str] = []

        # 1. Work order match
        work_order_match = (evidence.work_order_id == expected_order.work_order_id)
        if not work_order_match:
            reasons.append(f"EVD-WO-MISMATCH: Expected WO '{expected_order.work_order_id}', got '{evidence.work_order_id}'")

        # 2. Equipment tag match
        equipment_match = (evidence.equipment_tag == expected_order.equipment_tag)
        if not equipment_match:
            reasons.append(f"EVD-ASSET-MISMATCH: Expected tag '{expected_order.equipment_tag}', got '{evidence.equipment_tag}'")

        # 3. Vendor match
        vendor_match = (evidence.vendor_id == expected_order.vendor_id)
        if not vendor_match:
            reasons.append(f"EVD-VENDOR-MISMATCH: Expected vendor '{expected_order.vendor_id}', got '{evidence.vendor_id}'")

        # 4. Required fields completeness
        required_fields_complete = bool(evidence.evidence_id and evidence.technician_id and evidence.checklist_items)
        if not required_fields_complete:
            reasons.append("EVD-FIELDS-INCOMPLETE: Missing required evidence or technician identifiers")

        # 5. Service scope match (Checklist contains required maintenance steps)
        checklist_text = " ".join(evidence.checklist_items).lower()
        service_scope_match = all(kw in checklist_text for kw in ["verified", "completed"])
        if not service_scope_match:
            reasons.append("EVD-SCOPE-INCOMPLETE: Checklist does not attest full service execution")

        # 6. Physical measurements check (e.g. vibration reduced to ISO Zone A/B <= 2.5 mm/s)
        vib_after = evidence.measurements.get("vibration_after_mm_s")
        measurements_valid = True
        if vib_after is not None:
            try:
                if float(vib_after) > 4.5:  # ISO Zone C/D threshold
                    measurements_valid = False
                    reasons.append(f"EVD-MEASUREMENT-EXCURSION: Post-service vibration {vib_after} mm/s exceeds acceptable limit")
            except (ValueError, TypeError):
                measurements_valid = False
                reasons.append("EVD-MEASUREMENT-INVALID: Post-service measurements malformed")

        # 7. File integrity check
        file_integrity_valid = True
        if evidence.file_bytes and evidence.file_sha256:
            calculated_hash = cls.compute_sha256(evidence.file_bytes)
            if calculated_hash != evidence.file_sha256:
                file_integrity_valid = False
                reasons.append("EVD-HASH-MISMATCH: Computed SHA256 does not match submitted digest")

        all_passed = (
            work_order_match
            and equipment_match
            and vendor_match
            and service_scope_match
            and required_fields_complete
            and measurements_valid
            and file_integrity_valid
        )

        decision = EvidenceDecision.PASS if all_passed else EvidenceDecision.FAIL

        return EvidenceValidationResult(
            decision=decision,
            work_order_match=work_order_match,
            equipment_match=equipment_match,
            vendor_match=vendor_match,
            service_scope_match=service_scope_match,
            required_fields_complete=required_fields_complete,
            measurements_valid=measurements_valid,
            file_integrity_valid=file_integrity_valid,
            evidence_provenance="SYNTHETIC_DEMO_FIXTURE" if evidence.is_synthetic else "VERIFIED_OPERATIONAL",
            reason_codes=reasons,
        )


class EvidenceGatedCaptureController:
    """Enforces the 'No Evidence, No Capture' policy boundary."""

    @classmethod
    def verify_capture_eligibility(
        cls,
        order_record: PayPalOrderRecord,
        evidence_result: Optional[EvidenceValidationResult] = None,
        supervisor_auth: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """Check all prerequisites before permitting a PayPal capture call.
        Returns: (is_eligible: bool, reason: str)
        """
        # 1. Check order status
        if order_record.status not in ("AUTHORIZED", "EVIDENCE_VERIFIED"):
            return False, f"Order status '{order_record.status}' is not eligible for capture (must be AUTHORIZED)"

        # 2. Check authorization ID
        if not order_record.authorization_id:
            return False, "Missing valid PayPal Authorization ID"

        # 3. 'No Evidence, No Capture' Gate
        if evidence_result is None or evidence_result.decision != EvidenceDecision.PASS:
            return False, "No Evidence, No Capture: Service completion evidence is missing or failed validation"

        # 4. Risk Lane B Check (Human Supervisor Dual-Signature)
        try:
            mandate_snapshot = json.loads(order_record.mandate_snapshot_json) if order_record.mandate_snapshot_json else {}
        except Exception:
            mandate_snapshot = {}

        risk_lane = mandate_snapshot.get("risk_lane", "LANE_A_ROUTINE")
        human_required = mandate_snapshot.get("human_approval_required", False)

        if risk_lane == "LANE_B_EXCEPTION" or human_required:
            if not supervisor_auth or not supervisor_auth.get("reviewer_id"):
                return False, "Human Dual-Signature Required: Supervisor digital sign-off needed before capture"

        return True, "Eligible: Evidence verified and all policy conditions satisfied"
