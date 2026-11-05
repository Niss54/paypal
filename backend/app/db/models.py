"""Relational models for enterprise audit ledger, connector state, and quarantine review."""
import json
import uuid
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from backend.app.db.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AuditEvent(Base):
    """Immutable audit trail for all operator queries, model actions, and work-order decisions.
    Satisfies OSHA 1910.119 Process Safety Management and ISO 45001 compliance standards.
    """
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime(timezone=True), default=utcnow, index=True)
    user_id = Column(String(128), nullable=False, index=True)
    site_id = Column(String(64), nullable=False, index=True)
    role = Column(String(64), nullable=False)
    action_type = Column(String(64), nullable=False, index=True)
    resource_type = Column(String(64), nullable=True)
    resource_id = Column(String(128), nullable=True)
    details_json = Column(Text, default="{}")
    status = Column(String(32), default="SUCCESS")
    ip_address = Column(String(64), nullable=True)

    def to_dict(self) -> dict:
        try:
            details = json.loads(self.details_json) if self.details_json else {}
        except Exception:
            details = {"raw": self.details_json}
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "user_id": self.user_id,
            "site_id": self.site_id,
            "role": self.role,
            "action_type": self.action_type,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": details,
            "status": self.status,
            "ip_address": self.ip_address,
        }


class ConnectorSync(Base):
    """Tracks synchronization status, delta cursors, and lag across enterprise connectors."""
    __tablename__ = "connector_syncs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    connector_id = Column(String(64), unique=True, index=True, nullable=False)
    source_type = Column(String(32), nullable=False, index=True)  # SAP_PM, SHAREPOINT, OSISOFT_PI, QMS
    site_id = Column(String(64), nullable=False, index=True)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    cursor_token = Column(String(256), nullable=True)
    records_synced = Column(Integer, default=0)
    status = Column(String(32), default="IDLE")  # IDLE, SYNCING, HEALTHY, FAILED
    error_message = Column(Text, nullable=True)

    def to_dict(self) -> dict:
        return {
            "connector_id": self.connector_id,
            "source_type": self.source_type,
            "site_id": self.site_id,
            "last_sync_at": self.last_sync_at.isoformat() if self.last_sync_at else None,
            "cursor_token": self.cursor_token,
            "records_synced": self.records_synced,
            "status": self.status,
            "error_message": self.error_message,
        }


class QuarantineItem(Base):
    """Quarantine review ledger for corrupted files, checksum duplicates, or low-confidence P&IDs."""
    __tablename__ = "quarantine_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(String(64), unique=True, index=True, default=lambda: f"QRN-{uuid.uuid4().hex[:8]}")
    source_system = Column(String(32), nullable=False)
    filename = Column(String(256), nullable=False)
    sha256 = Column(String(64), index=True, nullable=False)
    quarantine_reason = Column(String(256), nullable=False)
    severity = Column(String(32), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(32), default="PENDING_REVIEW")  # PENDING_REVIEW, APPROVED, REJECTED
    created_at = Column(DateTime(timezone=True), default=utcnow)
    reviewed_by = Column(String(128), nullable=True)
    review_notes = Column(Text, nullable=True)

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "source_system": self.source_system,
            "filename": self.filename,
            "sha256": self.sha256,
            "quarantine_reason": self.quarantine_reason,
            "severity": self.severity,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "reviewed_by": self.reviewed_by,
            "review_notes": self.review_notes,
        }


class ApprovalRecord(Base):
    """Governance ledger for human-in-the-loop approvals before external system writes (e.g. SAP work orders)."""
    __tablename__ = "approval_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    approval_id = Column(String(64), unique=True, index=True, default=lambda: f"APP-{uuid.uuid4().hex[:8]}")
    action_type = Column(String(64), nullable=False)  # WORK_ORDER_WRITE, POLICY_CHANGE, PND_OVERRIDE
    target_system = Column(String(32), nullable=False)  # SAP_PM, QMS
    payload_json = Column(Text, nullable=False)
    requested_by = Column(String(128), nullable=False)
    site_id = Column(String(64), nullable=False, index=True)
    status = Column(String(32), default="PENDING")  # PENDING, APPROVED, REJECTED
    reviewed_by = Column(String(128), nullable=True)
    rollback_guidance = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        try:
            payload = json.loads(self.payload_json) if self.payload_json else {}
        except Exception:
            payload = {"raw": self.payload_json}
        return {
            "approval_id": self.approval_id,
            "action_type": self.action_type,
            "target_system": self.target_system,
            "payload": payload,
            "requested_by": self.requested_by,
            "site_id": self.site_id,
            "status": self.status,
            "reviewed_by": self.reviewed_by,
            "rollback_guidance": self.rollback_guidance,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
        }


class AutomationPolicy(Base):
    """Configurable enterprise automation rule governing automated writes to SAP PM or QMS."""
    __tablename__ = "automation_policies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_id = Column(String(64), unique=True, index=True, nullable=False)
    site_id = Column(String(64), nullable=False, index=True, default="*")
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    trigger_type = Column(String(64), nullable=False, index=True)  # HEALTH_INDEX_CRITICAL, STATUTORY_OVERDUE, VIBRATION_SPIKE
    action_type = Column(String(64), nullable=False)  # CREATE_SAP_WORK_ORDER, LOG_QMS_CAPA, SEND_ALERT
    target_system = Column(String(32), nullable=False)  # SAP_PM, QMS, NOTIFY
    approval_threshold = Column(String(32), default="REQUIRES_APPROVAL")  # REQUIRES_APPROVAL, AUTONOMOUS
    parameters_json = Column(Text, default="{}")
    rollback_guidance = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    def to_dict(self) -> dict:
        try:
            params = json.loads(self.parameters_json) if self.parameters_json else {}
        except Exception:
            params = {"raw": self.parameters_json}
        return {
            "policy_id": self.policy_id,
            "site_id": self.site_id,
            "name": self.name,
            "description": self.description,
            "trigger_type": self.trigger_type,
            "action_type": self.action_type,
            "target_system": self.target_system,
            "approval_threshold": self.approval_threshold,
            "parameters": params,
            "rollback_guidance": self.rollback_guidance,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class EvaluationRemediation(Base):
    """Operational feedback and remediation queue for low-faithfulness or hallucinated answers."""
    __tablename__ = "evaluation_remediations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    remediation_id = Column(String(64), unique=True, index=True, default=lambda: f"REM-{uuid.uuid4().hex[:8]}")
    score_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(128), nullable=False, index=True)
    site_id = Column(String(64), nullable=False, index=True, default="plant-mumbai-01")
    reason = Column(String(128), nullable=False)
    incorrect_snippets_json = Column(Text, default="[]")
    correction_notes = Column(Text, nullable=False)
    status = Column(String(32), default="PENDING_REINDEX", index=True)  # PENDING_REINDEX, REINDEXED, RESOLVED
    created_at = Column(DateTime(timezone=True), default=utcnow)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(128), nullable=True)

    def to_dict(self) -> dict:
        try:
            snippets = json.loads(self.incorrect_snippets_json) if self.incorrect_snippets_json else []
        except Exception:
            snippets = [self.incorrect_snippets_json]
        return {
            "remediation_id": self.remediation_id,
            "score_id": self.score_id,
            "user_id": self.user_id,
            "site_id": self.site_id,
            "reason": self.reason,
            "incorrect_snippets": snippets,
            "correction_notes": self.correction_notes,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
        }


class PaymentRecord(Base):
    """Persistent audit and settlement ledger for Machine Money Bitcoin/Lightning transactions."""
    __tablename__ = "payment_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    payment_id = Column(String(64), unique=True, index=True, default=lambda: f"PAY-{uuid.uuid4().hex[:12]}")
    provider = Column(String(32), nullable=False, default="mock")  # mock, lnbits, cln, nwc
    network = Column(String(32), nullable=False, default="regtest")  # regtest, signet, testnet, mainnet
    status = Column(String(32), nullable=False, index=True, default="PENDING")
    # Statuses: QUOTED, INVOICE_CREATED, PENDING, PAID, FAILED, REJECTED, EXPIRED, REFUNDED, MOCK_PAID
    invoice = Column(Text, nullable=True)  # BOLT11 payment request
    payment_hash = Column(String(128), index=True, nullable=True)
    preimage = Column(String(128), nullable=True)
    amount_msat = Column(Integer, nullable=False, default=0)
    amount_sats = Column(Integer, nullable=False, default=0)
    fee_msat = Column(Integer, default=0)
    fee_sats = Column(Integer, default=0)
    recipient = Column(String(128), nullable=True)
    service_id = Column(String(64), nullable=True)
    quote_id = Column(String(64), nullable=True)
    work_order_id = Column(String(64), index=True, nullable=True)
    predictive_event_id = Column(String(64), index=True, nullable=True)
    automation_policy_id = Column(String(64), nullable=True)
    approval_id = Column(String(64), nullable=True)
    idempotency_key = Column(String(128), unique=True, index=True, nullable=True)
    error_code = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, index=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    metadata_json = Column(Text, default="{}")

    def to_dict(self) -> dict:
        try:
            metadata = json.loads(self.metadata_json) if self.metadata_json else {}
        except Exception:
            metadata = {"raw": self.metadata_json}
        return {
            "payment_id": self.payment_id,
            "provider": self.provider,
            "network": self.network,
            "status": self.status,
            "invoice": self.invoice,
            "payment_hash": self.payment_hash,
            "preimage": self.preimage,
            "amount_msat": self.amount_msat,
            "amount_sats": self.amount_sats,
            "fee_msat": self.fee_msat,
            "fee_sats": self.fee_sats,
            "recipient": self.recipient,
            "service_id": self.service_id,
            "quote_id": self.quote_id,
            "work_order_id": self.work_order_id,
            "predictive_event_id": self.predictive_event_id,
            "automation_policy_id": self.automation_policy_id,
            "approval_id": self.approval_id,
            "idempotency_key": self.idempotency_key,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "metadata": metadata,
        }



class PayPalOrderRecord(Base):
    """Persistent audit and settlement ledger for PayPal Orders v2 transactions.
    Tracks two-phase Authorization -> Evidence Verification -> Capture lifecycle.
    Satisfies Master PRD V2 Section 9.1.
    """
    __tablename__ = "paypal_order_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    paypal_order_id = Column(String(64), unique=True, index=True, nullable=False)
    authorization_id = Column(String(64), unique=True, index=True, nullable=True)
    capture_id = Column(String(64), unique=True, index=True, nullable=True)
    merchant_account_label = Column(String(128), default="KinetixRAG Demo Maintenance Vendor")
    environment = Column(String(32), default="sandbox")
    amount_value = Column(String(32), nullable=False, default="0.00")
    currency_code = Column(String(8), nullable=False, default="USD")
    status = Column(String(32), nullable=False, index=True, default="DRAFT")
    # Lifecycle: DRAFT -> POLICY_ALLOWED -> ORDER_CREATED -> BUYER_APPROVED -> AUTHORIZED -> EVIDENCE_PENDING -> EVIDENCE_VERIFIED -> CAPTURED -> VOIDED

    work_order_id = Column(String(64), index=True, nullable=False)
    predictive_event_id = Column(String(64), index=True, nullable=False)
    equipment_tag = Column(String(64), nullable=False)
    quote_id = Column(String(64), nullable=False)
    vendor_id = Column(String(64), nullable=False)

    mandate_id = Column(String(64), nullable=False, default="mnd-routine-01")
    mandate_version = Column(Integer, default=1)
    mandate_snapshot_json = Column(Text, default="{}")

    evidence_status = Column(String(32), default="PENDING")
    evidence_hash = Column(String(64), nullable=True)
    evidence_record_id = Column(String(64), nullable=True)

    reviewer_user_id = Column(String(128), nullable=True)
    reviewer_notes = Column(Text, nullable=True)
    requester_user_id = Column(String(128), default="kinetix-procurement-agent", nullable=False)
    approve_url = Column(String(512), nullable=True)
    is_simulated = Column(Boolean, default=False, nullable=False)
    site_id = Column(String(64), default="plant-mumbai-01", nullable=False, index=True)
    organization_id = Column(String(64), default="kinetix-industrial", nullable=False)

    create_request_id = Column(String(128), nullable=False)
    authorize_request_id = Column(String(128), nullable=True)
    capture_request_id = Column(String(128), nullable=True)
    void_request_id = Column(String(128), nullable=True)
    webhook_last_event_id = Column(String(128), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow, index=True)
    authorized_at = Column(DateTime(timezone=True), nullable=True)
    authorization_expires_at = Column(DateTime(timezone=True), nullable=True)
    captured_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    def to_dict(self) -> dict:
        try:
            mandate_snapshot = json.loads(self.mandate_snapshot_json) if self.mandate_snapshot_json else {}
        except Exception:
            mandate_snapshot = {"raw": self.mandate_snapshot_json}
        return {
            "id": self.id,
            "paypal_order_id": self.paypal_order_id,
            "authorization_id": self.authorization_id,
            "capture_id": self.capture_id,
            "merchant_account_label": self.merchant_account_label,
            "environment": self.environment,
            "amount_value": self.amount_value,
            "currency_code": self.currency_code,
            "status": self.status,
            "work_order_id": self.work_order_id,
            "predictive_event_id": self.predictive_event_id,
            "equipment_tag": self.equipment_tag,
            "quote_id": self.quote_id,
            "vendor_id": self.vendor_id,
            "mandate_id": self.mandate_id,
            "mandate_version": self.mandate_version,
            "mandate_snapshot": mandate_snapshot,
            "evidence_status": self.evidence_status,
            "evidence_hash": self.evidence_hash,
            "evidence_record_id": self.evidence_record_id,
            "reviewer_user_id": self.reviewer_user_id,
            "reviewer_notes": self.reviewer_notes,
            "requester_user_id": getattr(self, "requester_user_id", "kinetix-procurement-agent"),
            "approve_url": getattr(self, "approve_url", None),
            "is_simulated": getattr(self, "is_simulated", False),
            "site_id": getattr(self, "site_id", "plant-mumbai-01"),
            "organization_id": getattr(self, "organization_id", "kinetix-industrial"),
            "create_request_id": self.create_request_id,
            "authorize_request_id": self.authorize_request_id,
            "capture_request_id": self.capture_request_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "authorized_at": self.authorized_at.isoformat() if self.authorized_at else None,
            "captured_at": self.captured_at.isoformat() if self.captured_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PayPalWebhookEvent(Base):
    """Durable receipt and idempotency ledger for incoming PayPal Webhook deliveries.
    Satisfies Master PRD V2 Section 9.2.
    """
    __tablename__ = "paypal_webhook_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(128), unique=True, index=True, nullable=False)
    event_type = Column(String(64), index=True, nullable=False)
    resource_id = Column(String(128), index=True, nullable=False)
    signature_verified = Column(Boolean, default=False)
    status = Column(String(32), default="PROCESSED")
    payload_summary_json = Column(Text, default="{}")
    received_at = Column(DateTime(timezone=True), default=utcnow)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        try:
            summary = json.loads(self.payload_summary_json) if self.payload_summary_json else {}
        except Exception:
            summary = {"raw": self.payload_summary_json}
        return {
            "id": self.id,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "resource_id": self.resource_id,
            "signature_verified": self.signature_verified,
            "status": self.status,
            "payload_summary": summary,
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }


class CompletionEvidenceRecord(Base):
    """Structured evidence package validating service completion before capture.
    Satisfies Master PRD V2 Section 9.3 & Section 10.
    """
    __tablename__ = "completion_evidence_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    evidence_record_id = Column(String(64), unique=True, index=True, nullable=False)
    work_order_id = Column(String(64), index=True, nullable=False)
    quote_id = Column(String(64), nullable=False)
    equipment_tag = Column(String(64), nullable=False)
    evidence_type = Column(String(32), default="DIAGNOSTIC_REPORT")
    filename = Column(String(256), nullable=False)
    file_sha256 = Column(String(64), nullable=False)
    checklist_items_json = Column(Text, default="[]")
    measurements_json = Column(Text, default="{}")
    validation_passed = Column(Boolean, default=False)
    validation_reason_codes_json = Column(Text, default="[]")
    order_id = Column(String(64), index=True, nullable=True)
    file_content = Column(Text, nullable=True)
    file_size_bytes = Column(Integer, default=0)
    submitted_by = Column(String(128), nullable=True)
    provenance_classification = Column(String(64), default="SYNTHETIC_DEMO_FIXTURE")
    is_synthetic = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    def to_dict(self) -> dict:
        try:
            checklist = json.loads(self.checklist_items_json) if self.checklist_items_json else []
        except Exception:
            checklist = [self.checklist_items_json]
        try:
            measurements = json.loads(self.measurements_json) if self.measurements_json else {}
        except Exception:
            measurements = {"raw": self.measurements_json}
        try:
            reason_codes = json.loads(self.validation_reason_codes_json) if self.validation_reason_codes_json else []
        except Exception:
            reason_codes = [self.validation_reason_codes_json]
        return {
            "evidence_record_id": self.evidence_record_id,
            "work_order_id": self.work_order_id,
            "quote_id": self.quote_id,
            "equipment_tag": self.equipment_tag,
            "evidence_type": self.evidence_type,
            "filename": self.filename,
            "file_sha256": self.file_sha256,
            "checklist": checklist,
            "measurements": measurements,
            "validation_passed": self.validation_passed,
            "validation_reason_codes": reason_codes,
            "order_id": getattr(self, "order_id", None),
            "provenance_classification": getattr(self, "provenance_classification", "SYNTHETIC_DEMO_FIXTURE"),
            "file_size_bytes": getattr(self, "file_size_bytes", 0),
            "submitted_by": getattr(self, "submitted_by", None),
            "is_synthetic": self.is_synthetic,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
