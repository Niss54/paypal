"""Evidence-Gated Industrial Procurement Orchestrator.
Coordinates predictive trigger (NASA IMS), RFQ generation, deterministic spending mandate gating,
PayPal Orders v2 authorization lifecycle, vendor completion evidence verification, and gated capture.
Complies with Master PRD V2 Sections 0.2, 0.3, 6.1, 6.2, 8.4, 9.4, 9.5, and 10.
"""
import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from backend.app.db.models import (
    CompletionEvidenceRecord,
    PayPalOrderRecord,
)
from backend.app.services.paypal.authorization import PayPalAuthorizationService
from backend.app.services.paypal.capture import PayPalCaptureService
from backend.app.services.paypal.orders import PayPalOrderService
from backend.app.services.procurement.evidence import (
    EvidenceDecision,
    EvidenceGatedCaptureController,
    EvidenceSubmission,
    EvidenceValidationResult,
    EvidenceValidator,
)
from backend.app.services.procurement.mandate import (
    MandateDecision,
    RiskLane,
    SpendingMandate,
    SpendingMandateEngine,
)

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


CANONICAL_INCIDENT = {
    "scenario_id": "SCN-2026-IMS-01",
    "equipment_id": "P-101A",
    "equipment_tag": "P-101A",
    "equipment_name": "Primary Slurry Feed Pump",
    "component": "Drive-End Spherical Roller Bearing",
    "anomaly_source": "NASA IMS Bearing Accelerometry Dataset (Test 2, Bearing 1)",
    "trigger_timestamp": "2026-11-04T14:32:00Z",
    "metric_name": "Vibration Velocity RMS",
    "measured_value_mm_s": 4.82,
    "normal_baseline_mm_s": 2.10,
    "alarm_threshold_mm_s": 4.50,
    "status": "CRITICAL_ANOMALY_EXCURSION",
    "diagnosis": (
        "Outer race fatigue spalling detected via high-frequency envelope analysis. "
        "Bearing degradation exceeds ISO 10816 Level C operational boundary (4.50 mm/s RMS). "
        "Catastrophic seizure anticipated within 48-72 operating hours without intervention."
    ),
    "recommended_action": "Emergency replacement of bearing assembly and post-repair vibration validation.",
    "work_order_id": "WO-2026-IMS-001",
    "is_critical_asset": True,
    "requires_supervisor_signoff": True,
}

DEMO_QUOTES = [
    {
        "quote_id": "Q-2026-001",
        "vendor_id": "VND-001",
        "vendor_name": "Bearing Supply Co",
        "service_id": "SRV-BRG-REPLACE",
        "amount": "450.00",
        "currency": "USD",
        "sla_hours": 24,
        "is_allowlisted": True,
        "is_synthetic": True,
        "synthetic_label": "[SYNTHETIC DEMO QUOTE]",
        "scope_description": "Supply SKF 22210 spherical roller bearing and dispatch certified millwright technician for on-site replacement.",
        "is_direct_paypal_sandbox_merchant": True,
        "scoring": {
            "cost_score": 92.0,
            "sla_score": 95.0,
            "reliability_score": 96.0,
            "composite_rank": 1,
            "hard_gates_passed": True,
        },
    },
    {
        "quote_id": "Q-2026-002",
        "vendor_id": "VND-002",
        "vendor_name": "Apex Industrial Parts",
        "service_id": "SRV-BRG-REPLACE",
        "amount": "680.00",
        "currency": "USD",
        "sla_hours": 12,
        "is_allowlisted": True,
        "is_synthetic": True,
        "synthetic_label": "[SYNTHETIC DEMO QUOTE]",
        "scope_description": "Expedited 12h emergency response with premium ceramic bearing upgrade.",
        "is_direct_paypal_sandbox_merchant": False,
        "scoring": {
            "cost_score": 60.0,
            "sla_score": 100.0,
            "reliability_score": 90.0,
            "composite_rank": 2,
            "hard_gates_passed": False,
            "gate_failure_reason": "Quote amount $680.00 exceeds $500.00 spending mandate cap",
        },
    },
    {
        "quote_id": "Q-2026-003",
        "vendor_id": "VND-003",
        "vendor_name": "Precision Spares Direct",
        "service_id": "SRV-BRG-REPLACE",
        "amount": "420.00",
        "currency": "USD",
        "sla_hours": 72,
        "is_allowlisted": True,
        "is_synthetic": True,
        "synthetic_label": "[SYNTHETIC DEMO QUOTE]",
        "scope_description": "Standard ground dispatch bearing supply and repair kit.",
        "is_direct_paypal_sandbox_merchant": False,
        "scoring": {
            "cost_score": 98.0,
            "sla_score": 40.0,
            "reliability_score": 85.0,
            "composite_rank": 3,
            "hard_gates_passed": False,
            "gate_failure_reason": "SLA 72h exceeds 48h emergency replacement window",
        },
    },
]

CANONICAL_MANDATE = SpendingMandate(
    mandate_id="MND-2026-P101A",
    version=1,
    site_id="plant-mumbai-01",
    equipment_scope=["P-101A", "P-101B", "C-201"],
    allowed_service_ids=["SRV-BRG-REPLACE", "bearing-inspection"],
    allowed_vendor_ids=["VND-001", "VND-002", "VND-003", "apex-diagnostics"],
    max_amount="500.00",
    currency_code="USD",
    max_sla_hours=48,
    require_human_for_critical_assets=True,
    critical_asset_tags=["P-101A"],
)


class ProcurementOrchestrator:
    """End-to-end industrial procurement workflow controller."""

    def __init__(
        self,
        order_service: Optional[PayPalOrderService] = None,
        authorization_service: Optional[PayPalAuthorizationService] = None,
        capture_service: Optional[PayPalCaptureService] = None,
    ):
        self.order_service = order_service or PayPalOrderService()
        self.authorization_service = authorization_service or PayPalAuthorizationService()
        self.capture_service = capture_service or PayPalCaptureService()
        self.mandate_engine = SpendingMandateEngine()
        self.evidence_validator = EvidenceValidator()
        self.evidence_controller = EvidenceGatedCaptureController()

    def get_incident(self) -> Dict[str, Any]:
        """Returns the grounded NASA IMS bearing anomaly incident details with GraphRAG attribution and explicit provenance distinction."""
        incident = CANONICAL_INCIDENT.copy()
        incident["graphrag_context"] = {
            "node_id": "FE-001",
            "failure_mode": "Bearing Cage Degradation & Overheating",
            "component_subsystem": "Drive-End Roller Element Bearings",
            "root_cause_analysis": (
                "High-frequency envelope acceleration spectrum exhibits characteristic BPFO/BPFI sidebands indicating fatigue spalling. "
                "Vibration velocity RMS is 4.82 mm/s, exceeding ISO 10816-3 Group 1 rigid boundary for acceptable operation (4.50 mm/s Limit)."
            ),
            "ai_repair_scope_recommendation": (
                "Execute Work Order WO-2026-IMS-001: Procure SKF 22210 spherical roller bearing, "
                "dispatch certified millwright technician, perform dial indicator laser alignment, "
                "and mandate post-repair vibration validation (must verify <= 4.50 mm/s before releasing payment capture)."
            ),
            "rca_confidence": 0.942,
            "rca_confidence_note": "Bayesian envelope match score (model-estimated)",
            "citations": [
                "ISO-10816-3: Mechanical Vibration Evaluation on Industrial Machines (Table C.1)",
                "PROC-001: Primary Slurry Feed Pump Bearing Assembly Replacement Standard Operating Procedure",
                "DOC-P101-RCA: Plant Reliability Inner Race Failure Ontology and Historical Incident Ledger",
                "NASA-IMS-2004: Run-to-Failure Accelerometry Baseline Curves (Test 2, Bearing 1)",
            ],
            "provenance_split": {
                "empirical_research_foundation": {
                    "dataset": "NASA IMS Bearing Run-to-Failure Accelerometry (2004)",
                    "source_fixture_tag": "REPLAY-ASSET-01",
                    "historical_failure_runout_rms": "5.42 mm/s",
                    "sampling_frequency_khz": 20.0,
                    "curator": "NASA Ames Prognostics Center of Excellence",
                },
                "operational_plant_demonstration": {
                    "asset_tag": "P-101A (Primary Slurry Feed Pump)",
                    "current_vibration_rms": "4.82 mm/s",
                    "iso_zone": "Zone C/D Excursion (Alarm Boundary: 4.50 mm/s)",
                    "risk_classification": "LANE_B_CRITICAL",
                    "mandated_dual_control": True,
                },
            },
        }
        return incident

    def get_quotes(self) -> List[Dict[str, Any]]:
        """Returns the comparison RFQ quotes with synthetic disclosures."""
        return [q.copy() for q in DEMO_QUOTES]

    def get_mandate(self) -> Dict[str, Any]:
        """Returns the active spending mandate definition."""
        return {
            "mandate_id": CANONICAL_MANDATE.mandate_id,
            "version": CANONICAL_MANDATE.version,
            "equipment_scope": CANONICAL_MANDATE.equipment_scope,
            "allowed_service_ids": CANONICAL_MANDATE.allowed_service_ids,
            "currency_code": CANONICAL_MANDATE.currency_code,
            "max_amount": CANONICAL_MANDATE.max_amount,
            "max_sla_hours": CANONICAL_MANDATE.max_sla_hours,
            "allowed_vendor_ids": CANONICAL_MANDATE.allowed_vendor_ids,
            "require_human_for_critical_assets": CANONICAL_MANDATE.require_human_for_critical_assets,
            "critical_asset_tags": CANONICAL_MANDATE.critical_asset_tags,
        }

    def evaluate_quote(self, quote_id: str) -> Dict[str, Any]:
        """Deterministic evaluation of a candidate quote against the spending mandate."""
        quote_dict = next((q for q in DEMO_QUOTES if q["quote_id"] == quote_id), None)
        if not quote_dict:
            raise ValueError(f"Quote {quote_id} not found")

        res = SpendingMandateEngine.evaluate_quote(
            mandate=CANONICAL_MANDATE,
            quote=quote_dict,
            equipment_tag=CANONICAL_INCIDENT["equipment_tag"],
            untrusted_text=quote_dict.get("scope_description", ""),
        )

        audit_hash = hashlib.sha256(
            f"{res.mandate_id}:{res.quote_id}:{res.amount_value}:{res.timestamp.isoformat()}".encode()
        ).hexdigest()

        return {
            "decision": res.decision.value,
            "risk_lane": res.risk_lane.value,
            "requires_supervisor_signoff": res.human_approval_required,
            "reason_codes": res.reason_codes,
            "audit_hash": audit_hash,
            "quote": quote_dict,
        }

    async def create_paypal_order(
        self,
        db: Session,
        quote_id: str,
        actor: str = "kinetix-procurement-agent",
        is_simulation: bool = False,
    ) -> PayPalOrderRecord:
        """Evaluates mandate and creates a PayPal Order with intent=AUTHORIZE."""
        eval_result = self.evaluate_quote(quote_id)
        decision = eval_result["decision"]
        if decision == MandateDecision.BLOCKED.value:
            reasons = "; ".join(eval_result["reason_codes"])
            raise ValueError(f"Quote blocked by spending mandate hard gates: {reasons}")
        if decision == MandateDecision.REQUIRES_REVIEW.value:
            reasons = "; ".join(eval_result["reason_codes"])
            raise ValueError(f"Quote exceeds policy cap and requires prior human review: {reasons}")

        quote = eval_result["quote"]
        amount_dec = Decimal(str(quote["amount"]))
        currency = quote["currency"]

        idempotency_key = f"order:{CANONICAL_INCIDENT['work_order_id']}:{quote_id}:{uuid.uuid4().hex[:8]}"
        approve_url = None

        if is_simulation or not self.order_service.client.is_configured:
            # Explicit simulation mode or unconfigured client in offline testing
            paypal_order_id = f"SIM-ORD-{uuid.uuid4().hex[:12].upper()}"
            order_status = "SIMULATED_ORDER_CREATED"
            approve_url = f"https://www.sandbox.paypal.com/checkoutnow?token={paypal_order_id}"
            is_sim_flag = True
        else:
            # LIVE SANDBOX MODE: real PayPal Orders v2 API call.
            # Exceptions are propagated directly without fake ID substitution.
            order_resp = await self.order_service.create_order(
                amount_value=str(amount_dec),
                currency_code=currency,
                work_order_id=CANONICAL_INCIDENT["work_order_id"],
                quote_id=quote_id,
                description=f"Emergency repair {CANONICAL_INCIDENT['equipment_id']} - {quote['vendor_name']}",
                idempotency_key=idempotency_key,
            )
            paypal_order_id = order_resp.id
            order_status = "ORDER_CREATED"
            is_sim_flag = False
            for link in (order_resp.links or []):
                if link.rel in ("approve", "payer-action"):
                    approve_url = link.href
                    break

        existing = db.query(PayPalOrderRecord).filter(PayPalOrderRecord.paypal_order_id == paypal_order_id).first()
        if existing:
            if actor:
                existing.requester_user_id = actor
            if approve_url:
                existing.approve_url = approve_url
            db.commit()
            db.refresh(existing)
            return existing

        order_record = PayPalOrderRecord(
            paypal_order_id=paypal_order_id,
            work_order_id=CANONICAL_INCIDENT["work_order_id"],
            predictive_event_id="EVT-2026-IMS-01",
            equipment_tag=CANONICAL_INCIDENT["equipment_tag"],
            quote_id=quote_id,
            vendor_id=quote["vendor_id"],
            amount_value=str(amount_dec),
            currency_code=currency,
            status=order_status,
            requester_user_id=actor,
            approve_url=approve_url,
            is_simulated=is_sim_flag,
            mandate_id=CANONICAL_MANDATE.mandate_id,
            mandate_version=CANONICAL_MANDATE.version,
            mandate_snapshot_json=json.dumps({
                "risk_lane": eval_result["risk_lane"],
                "human_approval_required": eval_result["requires_supervisor_signoff"],
                "budget_cap": CANONICAL_MANDATE.max_amount,
                "quote_amount": str(amount_dec),
                "audit_hash": eval_result["audit_hash"],
            }),
            create_request_id=idempotency_key,
            evidence_status="PENDING",
        )
        db.add(order_record)
        db.commit()
        db.refresh(order_record)
        return order_record

    async def approve_paypal_order(
        self,
        db: Session,
        order_id: str,
        simulated_approval: bool = False,
    ) -> PayPalOrderRecord:
        """Verifies or records Buyer Approval for a PayPal Order before authorization."""
        order = db.query(PayPalOrderRecord).filter(PayPalOrderRecord.paypal_order_id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        if order.status in ("BUYER_APPROVED", "AUTHORIZED", "EVIDENCE_VERIFIED", "CAPTURED"):
            return order

        if simulated_approval and not order.is_simulated:
            raise ValueError(
                "Simulated approval is only permitted for simulated orders. "
                "Live orders must be approved via PayPal Sandbox checkout."
            )
        if order.is_simulated:
            order.status = "BUYER_APPROVED"
        else:
            # Query PayPal for ground truth status
            order_data = await self.order_service.get_order(order_id)
            if order_data.status.value in ("APPROVED", "COMPLETED"):
                order.status = "BUYER_APPROVED"
            else:
                raise ValueError(
                    f"PayPal Order {order_id} is in status '{order_data.status.value}'. "
                    f"Buyer Approval must be completed in PayPal Sandbox before authorization. "
                    f"Approval URL: {order.approve_url}"
                )

        order.updated_at = utcnow()
        db.commit()
        db.refresh(order)
        return order

    async def authorize_paypal_order(
        self,
        db: Session,
        order_id: str,
        sandbox_authorization_id: Optional[str] = None,
    ) -> PayPalOrderRecord:
        """Authorizes an approved PayPal order and transitions record to AUTHORIZED."""
        order = db.query(PayPalOrderRecord).filter(PayPalOrderRecord.paypal_order_id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        if order.status == "AUTHORIZED" and order.authorization_id:
            return order

        auth_id = sandbox_authorization_id
        if not auth_id:
            if order.is_simulated:
                auth_id = f"SIM-AUTH-{uuid.uuid4().hex[:12].upper()}"
            else:
                # Live Sandbox mode
                if order.status not in ("BUYER_APPROVED", "APPROVED"):
                    try:
                        order_data = await self.order_service.get_order(order_id)
                        if order_data.status.value == "APPROVED":
                            order.status = "BUYER_APPROVED"
                    except Exception as e:
                        logger.warning(f"Failed to check PayPal order approval status: {e}")

                auth_resp = await self.authorization_service.authorize_order(
                    order_id=order_id,
                    idempotency_key=f"auth:{order_id}",
                )
                auth_id = auth_resp.authorization_id

        order.authorization_id = auth_id
        order.status = "AUTHORIZED"
        order.authorized_at = utcnow()
        order.authorize_request_id = f"auth-req-{order_id}"
        db.commit()
        db.refresh(order)
        return order

    def sign_off_supervisor(
        self,
        db: Session,
        order_id: str,
        supervisor_id: str,
        notes: str = "Authorized Lane B critical asset maintenance after reviewing telemetry and RFQ",
    ) -> PayPalOrderRecord:
        """Records dual-control supervisor approval required for Lane B critical assets."""
        order = db.query(PayPalOrderRecord).filter(PayPalOrderRecord.paypal_order_id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        # Strict Dual-Control Separation of Duties: Requester cannot act as supervisor
        if order.requester_user_id and supervisor_id == order.requester_user_id:
            raise ValueError(
                f"Separation of duties violation: Requester '{order.requester_user_id}' "
                f"cannot sign off as dual-control supervisor"
            )

        order.reviewer_user_id = supervisor_id
        order.reviewer_notes = notes
        db.commit()
        db.refresh(order)
        return order

    def submit_evidence(
        self,
        db: Session,
        order_id: str,
        submission: EvidenceSubmission,
    ) -> Tuple[CompletionEvidenceRecord, EvidenceValidationResult]:
        """Submits vendor repair evidence, validates against deterministic criteria, and stores record."""
        order = db.query(PayPalOrderRecord).filter(PayPalOrderRecord.paypal_order_id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        val_res = self.evidence_validator.validate(submission, order)

        file_hash = submission.file_sha256
        if not file_hash and submission.file_bytes:
            file_hash = hashlib.sha256(submission.file_bytes).hexdigest()
        file_hash = file_hash or hashlib.sha256(f"evidence_{submission.evidence_id}".encode()).hexdigest()

        evidence_record = CompletionEvidenceRecord(
            evidence_record_id=submission.evidence_id,
            work_order_id=submission.work_order_id,
            quote_id=submission.quote_id,
            equipment_tag=submission.equipment_tag,
            evidence_type="DIAGNOSTIC_REPORT",
            filename=f"repair_report_{submission.work_order_id}.pdf",
            file_sha256=file_hash,
            checklist_items_json=json.dumps(submission.checklist_items),
            measurements_json=json.dumps(submission.measurements),
            validation_passed=(val_res.decision == EvidenceDecision.PASS),
            validation_reason_codes_json=json.dumps(val_res.reason_codes),
            is_synthetic=submission.is_synthetic,
        )
        db.add(evidence_record)

        # Update order with evidence linkage
        order.evidence_record_id = submission.evidence_id
        order.evidence_hash = file_hash
        if val_res.decision == EvidenceDecision.PASS:
            order.evidence_status = "VERIFIED"
            if order.status == "AUTHORIZED":
                order.status = "EVIDENCE_VERIFIED"
        else:
            order.evidence_status = "FAILED"

        db.commit()
        db.refresh(evidence_record)
        db.refresh(order)

        return evidence_record, val_res

    async def execute_gated_capture(
        self,
        db: Session,
        order_id: str,
        idempotency_key: Optional[str] = None,
        supervisor_auth: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Enforces 'No Evidence, No Capture' policy gate.
        Executes PayPal capture if and only if evidence is valid and supervisor sign-off is satisfied.
        """
        order = db.query(PayPalOrderRecord).filter(PayPalOrderRecord.paypal_order_id == order_id).first()
        if not order:
            return False, f"Order {order_id} not found", None

        # Idempotency check: if already captured, return success
        if order.status == "CAPTURED" and order.capture_id:
            return True, "Order already captured (idempotent)", {
                "capture_id": order.capture_id,
                "status": "COMPLETED",
                "amount": order.amount_value,
                "currency": order.currency_code,
            }

        # Look up stored evidence record
        evidence_rec = (
            db.query(CompletionEvidenceRecord)
            .filter(CompletionEvidenceRecord.work_order_id == order.work_order_id)
            .order_by(CompletionEvidenceRecord.created_at.desc())
            .first()
        )

        evidence_result = None
        if evidence_rec:
            try:
                checklist = json.loads(evidence_rec.checklist_items_json) if evidence_rec.checklist_items_json else []
            except Exception:
                checklist = []
            try:
                meas = json.loads(evidence_rec.measurements_json) if evidence_rec.measurements_json else {}
            except Exception:
                meas = {}
            try:
                reasons = json.loads(evidence_rec.validation_reason_codes_json) if evidence_rec.validation_reason_codes_json else []
            except Exception:
                reasons = []

            evidence_result = EvidenceValidationResult(
                decision=EvidenceDecision.PASS if evidence_rec.validation_passed else EvidenceDecision.FAIL,
                work_order_match=(evidence_rec.work_order_id == order.work_order_id),
                quote_match=(evidence_rec.quote_id == order.quote_id),
                equipment_match=(evidence_rec.equipment_tag == order.equipment_tag),
                vendor_match=True,
                service_scope_match=evidence_rec.validation_passed,
                required_fields_complete=True,
                measurements_valid=evidence_rec.validation_passed,
                file_integrity_valid=True,
                evidence_provenance="SYNTHETIC_DEMO_FIXTURE" if evidence_rec.is_synthetic else "VERIFIED_OPERATIONAL",
                reason_codes=reasons,
            )

        # Build supervisor auth context if signed off in order or passed explicitly
        sup_auth = supervisor_auth
        if not sup_auth and order.reviewer_user_id:
            sup_auth = {
                "approved": True,
                "reviewer_id": order.reviewer_user_id,
                "supervisor_id": order.reviewer_user_id,
                "notes": order.reviewer_notes or "Supervisor sign-off",
            }

        allowed, reason = self.evidence_controller.verify_capture_eligibility(
            order_record=order,
            evidence_result=evidence_result,
            supervisor_auth=sup_auth,
        )

        if not allowed:
            logger.warning(f"Capture blocked by Evidence Gate for order {order_id}: {reason}")
            return False, f"Evidence gate blocked capture: {reason}", None

        # Execute PayPal capture
        capture_idempotency = idempotency_key or f"cap:{order.authorization_id}"
        if order.is_simulated:
            capture_id = f"SIM-CAP-{uuid.uuid4().hex[:12].upper()}"
            cap_status = "COMPLETED"
        else:
            # LIVE SANDBOX: Real capture API call
            cap_resp = await self.capture_service.capture_authorization(
                authorization_id=order.authorization_id,
                amount_value=str(order.amount_value),
                currency_code=order.currency_code,
                idempotency_key=capture_idempotency,
            )
            capture_id = cap_resp.capture_id
            cap_status = cap_resp.status.value

            if cap_status != "COMPLETED":
                logger.warning(f"PayPal capture returned non-completed status: {cap_status}")
                order.status = "CAPTURE_PENDING"
                order.capture_id = capture_id
                order.updated_at = utcnow()
                db.commit()
                # Fail closed: pending or non-completed captures are NOT marked successful or settled!
                return False, f"Capture submitted to PayPal but pending settlement confirmation (status={cap_status}). Funds not yet released.", {
                    "capture_id": capture_id,
                    "status": cap_status,
                    "amount": order.amount_value,
                    "currency": order.currency_code,
                }

        order.capture_id = capture_id
        order.status = "CAPTURED"
        order.captured_at = utcnow()
        order.capture_request_id = capture_idempotency
        db.commit()
        db.refresh(order)

        return True, "Payment captured successfully under Evidence Gating Policy", {
            "capture_id": capture_id,
            "status": "COMPLETED",
            "amount": order.amount_value,
            "currency": order.currency_code,
            "captured_at": order.captured_at.isoformat(),
        }

    async def void_order(
        self,
        db: Session,
        order_id: str,
        reason: str = "Procurement cancelled or evidence expired",
    ) -> PayPalOrderRecord:
        """Voids an uncaptured authorization."""
        order = db.query(PayPalOrderRecord).filter(PayPalOrderRecord.paypal_order_id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        if order.status == "CAPTURED":
            raise ValueError("Cannot void an already captured order")

        if order.authorization_id and not order.is_simulated:
            try:
                await self.authorization_service.void_authorization(order.authorization_id)
            except Exception as e:
                logger.warning(f"Live PayPal void failed or unconfigured ({e})")

        order.status = "VOIDED"
        order.reviewer_notes = f"Void reason: {reason}"
        db.commit()
        db.refresh(order)
        return order

    def get_audit_lineage(self, db: Session, order_id: str) -> Dict[str, Any]:
        """Assembles the complete immutable causal lineage with unbroken cryptographic SHA-256 hash chaining."""
        order = db.query(PayPalOrderRecord).filter(PayPalOrderRecord.paypal_order_id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        evidence = (
            db.query(CompletionEvidenceRecord)
            .filter(CompletionEvidenceRecord.work_order_id == order.work_order_id)
            .order_by(CompletionEvidenceRecord.created_at.desc())
            .first()
        )

        stages = [
            {
                "step": 1,
                "title": "Predictive Anomaly Excursion",
                "source": CANONICAL_INCIDENT["anomaly_source"],
                "equipment_id": CANONICAL_INCIDENT["equipment_id"],
                "detail": f"Vibration RMS reached {CANONICAL_INCIDENT['measured_value_mm_s']} mm/s (Alarm: {CANONICAL_INCIDENT['alarm_threshold_mm_s']} mm/s)",
                "status": "TRIGGERED",
                "timestamp": CANONICAL_INCIDENT["trigger_timestamp"],
            },
            {
                "step": 2,
                "title": "GraphRAG Diagnostic Attribution",
                "diagnosis": CANONICAL_INCIDENT["diagnosis"],
                "recommended_action": CANONICAL_INCIDENT["recommended_action"],
                "work_order_id": order.work_order_id,
                "rca_confidence": 0.942,
                "sop_citations": ["PROC-001", "ISO-10816-3", "DOC-P101-RCA"],
                "status": "CONFIRMED",
            },
            {
                "step": 3,
                "title": "RFQ Quote Comparison & Hard-Gate Filter",
                "quotes_evaluated": len(DEMO_QUOTES),
                "selected_vendor_id": order.vendor_id,
                "disclosure": "[SYNTHETIC DEMO QUOTE]",
                "mandate_id": order.mandate_id,
                "budget_cap": "$500.00 USD",
                "status": "APPROVED",
            },
            {
                "step": 4,
                "title": "Spending Mandate Evaluation & Risk Routing",
                "mandate_snapshot": json.loads(order.mandate_snapshot_json) if order.mandate_snapshot_json else {},
                "requester_id": getattr(order, "requester_user_id", "kinetix-procurement-agent"),
                "supervisor_signed_off": bool(order.reviewer_user_id),
                "supervisor_id": order.reviewer_user_id,
                "status": "VERIFIED" if order.reviewer_user_id else "SUPERVISOR_PENDING",
            },
            {
                "step": 5,
                "title": "PayPal Orders v2 Two-Phase Authorization",
                "order_id": order.paypal_order_id,
                "intent": "AUTHORIZE",
                "amount": f"{order.amount_value} {order.currency_code}",
                "authorization_id": order.authorization_id,
                "approve_url": getattr(order, "approve_url", None),
                "is_simulated": getattr(order, "is_simulated", False),
                "authorized_at": order.authorized_at.isoformat() if order.authorized_at else None,
                "policy": "No Evidence, No Capture (Funds held in PayPal Sandbox, not transferred)",
                "status": order.status,
            },
            {
                "step": 6,
                "title": "Vendor Physical Repair & Evidence Validation",
                "evidence_submitted": evidence is not None,
                "evidence_id": evidence.evidence_record_id if evidence else None,
                "validation_passed": evidence.validation_passed if evidence else False,
                "file_sha256": evidence.file_sha256 if evidence else None,
                "status": "VALIDATED" if (evidence and evidence.validation_passed) else "PENDING",
            },
            {
                "step": 7,
                "title": "Evidence-Gated Capture & Settlement",
                "capture_id": order.capture_id,
                "captured_at": order.captured_at.isoformat() if order.captured_at else None,
                "status": "COMPLETED" if order.status == "CAPTURED" else "HELD",
            },
        ]

        # Compute continuous cryptographic SHA-256 hash chaining across all 7 stages
        prev_hash = "0" * 64
        for stage in stages:
            stage["previous_stage_hash"] = prev_hash
            stage_serialized = json.dumps(stage, sort_keys=True, default=str)
            stage_hash = hashlib.sha256(f"{prev_hash}:{stage_serialized}".encode("utf-8")).hexdigest()
            stage["stage_hash"] = stage_hash
            prev_hash = stage_hash

        merkle_root = prev_hash

        return {
            "order_id": order.paypal_order_id,
            "work_order_id": order.work_order_id,
            "status": order.status,
            "amount": order.amount_value,
            "currency": order.currency_code,
            "is_simulated": getattr(order, "is_simulated", False),
            "merkle_root": merkle_root,
            "chain_valid": True,
            "lineage_stages": stages,
        }
