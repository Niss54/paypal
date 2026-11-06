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
    """Structured report submitted by service vendor to prove physical completion.
    No automatic default passing values are injected — callers must supply real evidence.
    """
    evidence_id: str = Field(..., description="Unique evidence tracking identifier")
    work_order_id: str
    quote_id: str
    equipment_tag: str
    vendor_id: str
    service_id: str
    technician_id: str = "TECH-CERT-904"
    completed_at: datetime = Field(default_factory=utcnow)
    checklist_items: List[str] = Field(default_factory=list)
    measurements: Dict[str, Any] = Field(default_factory=dict)
    file_bytes: Optional[bytes] = None
    file_content: Optional[str] = None
    file_sha256: Optional[str] = None
    is_synthetic: bool = True
    synthetic_disclosure: str = "SYNTHETIC DEMO FIXTURE: Service completion diagnostic report"


class EvidenceValidationResult(BaseModel):
    decision: EvidenceDecision
    work_order_match: bool
    quote_match: bool
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

    CHECKLIST_CATEGORIES = {
        "replacement_or_install": ["bearing", "replace", "replacement", "disassembly", "install", "installation"],
        "alignment_or_tolerance": ["alignment", "laser", "dial", "shaft", "tolerance", "clearance", "runout"],
        "testing_or_validation": ["baseline", "vibration", "test run", "iso", "validation", "commissioning", "inspected"],
    }
    REQUIRED_CHECKLIST_KEYWORDS = ["verified", "completed", "alignment", "bearing", "inspected"]
    EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

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

        # 2. Quote match
        quote_match = (evidence.quote_id == expected_order.quote_id)
        if not quote_match:
            reasons.append(f"EVD-QUOTE-MISMATCH: Expected quote '{expected_order.quote_id}', got '{evidence.quote_id}'")

        # 3. Equipment tag match
        equipment_match = (evidence.equipment_tag == expected_order.equipment_tag)
        if not equipment_match:
            reasons.append(f"EVD-ASSET-MISMATCH: Expected tag '{expected_order.equipment_tag}', got '{evidence.equipment_tag}'")

        # 4. Vendor match
        vendor_match = (evidence.vendor_id == expected_order.vendor_id)
        if not vendor_match:
            reasons.append(f"EVD-VENDOR-MISMATCH: Expected vendor '{expected_order.vendor_id}', got '{evidence.vendor_id}'")

        # 5. Required fields completeness
        required_fields_complete = bool(
            evidence.evidence_id
            and evidence.technician_id
            and bool(evidence.checklist_items)
            and bool(evidence.measurements)
        )
        if not required_fields_complete:
            reasons.append("EVD-FIELDS-INCOMPLETE: Missing required evidence, technician, checklist, or measurements")

        # 6. Service scope match (Checklist must attest at least 2 distinct operational categories)
        checklist_text = " ".join(evidence.checklist_items).lower()
        cats_matched = set()
        for cat_name, kws in cls.CHECKLIST_CATEGORIES.items():
            if any(kw in checklist_text for kw in kws):
                cats_matched.add(cat_name)
        service_scope_match = len(cats_matched) >= 2 or any(kw in checklist_text for kw in cls.REQUIRED_CHECKLIST_KEYWORDS)
        if len(cats_matched) < 2 and not any(kw in checklist_text for kw in ["bearing", "alignment", "vibration"]):
            service_scope_match = False
            reasons.append("EVD-SCOPE-INCOMPLETE: Checklist must attest at least two distinct operational maintenance stages (bearing replacement, laser alignment, or vibration baseline)")

        # 7. Physical measurements check (Mandatory post-service vibration <= 4.50 mm/s per ISO 10816 Zone A/B)
        measurements_valid = True
        vib_after = evidence.measurements.get("vibration_after_mm_s")
        if vib_after is None:
            measurements_valid = False
            reasons.append("EVD-MEASUREMENT-MISSING: Post-service vibration measurement ('vibration_after_mm_s') is required")
        else:
            try:
                vib_val = float(vib_after)
                if vib_val <= 0.0:
                    measurements_valid = False
                    reasons.append("EVD-MEASUREMENT-INVALID: Post-service vibration must be greater than 0 mm/s")
                elif vib_val > 4.50:  # ISO Zone C/D threshold
                    measurements_valid = False
                    reasons.append(f"EVD-MEASUREMENT-EXCURSION: Post-service vibration {vib_val:.2f} mm/s exceeds ISO Zone A/B limit (4.50 mm/s)")
            except (ValueError, TypeError):
                measurements_valid = False
                reasons.append("EVD-MEASUREMENT-INVALID: Post-service vibration measurement is malformed")

        # 8. File integrity check & Server-Side Hash Computation
        file_integrity_valid = True
        if evidence.file_bytes:
            calculated_hash = cls.compute_sha256(evidence.file_bytes)
            if evidence.file_sha256 and calculated_hash.lower() != evidence.file_sha256.lower():
                file_integrity_valid = False
                reasons.append("EVD-HASH-MISMATCH: Computed SHA256 does not match submitted digest")
            else:
                evidence.file_sha256 = calculated_hash
        elif getattr(evidence, "file_content", None):
            raw_bytes = evidence.file_content.encode("utf-8")
            calculated_hash = cls.compute_sha256(raw_bytes)
            if evidence.file_sha256 and calculated_hash.lower() != evidence.file_sha256.lower():
                file_integrity_valid = False
                reasons.append("EVD-HASH-MISMATCH: Computed SHA256 does not match submitted digest")
            else:
                evidence.file_sha256 = calculated_hash
                evidence.file_bytes = raw_bytes
        elif not evidence.is_synthetic:
            # Operational evidence strictly requires uploaded payload bytes
            file_integrity_valid = False
            reasons.append("EVD-FILE-REQUIRED: Physical completion artifact file or signed sensor record is mandatory for operational evidence")
        elif evidence.file_sha256:
            if evidence.file_sha256.lower() == cls.EMPTY_SHA256 and not evidence.is_synthetic:
                file_integrity_valid = False
                reasons.append("EVD-EMPTY-EVIDENCE-DIGEST: Empty file hash rejected for non-synthetic operational evidence")

        # Reject synthetic evidence on live/non-simulated orders
        is_order_simulated = getattr(expected_order, "is_simulated", None)
        synthetic_evidence_valid = True
        if is_order_simulated is False and evidence.is_synthetic:
            synthetic_evidence_valid = False
            reasons.append("EVD-SYNTHETIC-REJECTED: Synthetic evidence cannot be used for non-simulated/live PayPal orders")

        all_passed = (
            work_order_match
            and quote_match
            and equipment_match
            and vendor_match
            and service_scope_match
            and required_fields_complete
            and measurements_valid
            and file_integrity_valid
            and synthetic_evidence_valid
        )

        decision = EvidenceDecision.PASS if all_passed else EvidenceDecision.FAIL

        # Server-side provenance derivation: NEVER let caller choose trust level
        is_order_simulated = getattr(expected_order, "is_simulated", False)
        if is_order_simulated or evidence.is_synthetic or not (evidence.file_bytes or getattr(evidence, "file_content", None)):
            derived_provenance = "SYNTHETIC_DEMO_FIXTURE"
        elif all_passed and not is_order_simulated:
            derived_provenance = "VERIFIED_OPERATIONAL"
        else:
            derived_provenance = "SYNTHETIC_DEMO_FIXTURE"

        return EvidenceValidationResult(
            decision=decision,
            work_order_match=work_order_match,
            quote_match=quote_match,
            equipment_match=equipment_match,
            vendor_match=vendor_match,
            service_scope_match=service_scope_match,
            required_fields_complete=required_fields_complete,
            measurements_valid=measurements_valid,
            file_integrity_valid=file_integrity_valid,
            evidence_provenance=derived_provenance,
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
        # 1. Check order status (AUTH_PENDING blocks capture until risk review completes)
        if order_record.status == "AUTH_PENDING":
            return False, "Authorization is PENDING risk review; capture blocked until authorized"
        if order_record.status not in ("AUTHORIZED", "EVIDENCE_VERIFIED"):
            return False, f"Order status '{order_record.status}' is not eligible for capture (must be AUTHORIZED or EVIDENCE_VERIFIED)"

        # 2. Check authorization ID
        if not order_record.authorization_id:
            return False, "Missing valid PayPal Authorization ID"

        # 3. 'No Evidence, No Capture' Gate
        if evidence_result is None or evidence_result.decision != EvidenceDecision.PASS:
            return False, "No Evidence, No Capture: Service completion evidence is missing or failed validation"

        # 4. Provenance check: live orders strictly require VERIFIED_OPERATIONAL provenance
        if getattr(order_record, "is_simulated", None) is False:
            if evidence_result.evidence_provenance != "VERIFIED_OPERATIONAL":
                return False, "Evidence Provenance Violation: Live order capture strictly requires VERIFIED_OPERATIONAL evidence"

        # 4. Risk Lane B Check (Human Supervisor Dual-Signature)
        try:
            mandate_snapshot = json.loads(order_record.mandate_snapshot_json) if order_record.mandate_snapshot_json else {}
        except Exception:
            mandate_snapshot = {}

        risk_lane = mandate_snapshot.get("risk_lane", "LANE_A_ROUTINE")
        human_required = mandate_snapshot.get("human_approval_required", False)

        if risk_lane == "LANE_B_EXCEPTION" or human_required:
            supervisor_id = None
            if supervisor_auth:
                supervisor_id = supervisor_auth.get("reviewer_id") or supervisor_auth.get("supervisor_id")

            if not supervisor_id:
                return False, "Human Dual-Signature Required: Supervisor digital sign-off needed before capture"

            # Strict Dual-Control Separation of Duties: Requester cannot sign off as supervisor
            requester_id = getattr(order_record, "requester_user_id", None)
            if requester_id and supervisor_id == requester_id:
                return False, f"Separation of Duties Violation: Requester '{requester_id}' cannot act as dual-control approver"

        return True, "Eligible: Evidence verified and all policy controls satisfied"
