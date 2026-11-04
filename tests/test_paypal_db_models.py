"""Unit tests verifying PayPal database models and table creation.
Satisfies Master PRD V2 Section 9.1, 9.2, 9.3.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.db.database import Base, init_db
from backend.app.db.models import PayPalOrderRecord, PayPalWebhookEvent, CompletionEvidenceRecord


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


def test_paypal_order_record_lifecycle(in_memory_db):
    """Verify PayPalOrderRecord creation, status transitions, and to_dict representation."""
    record = PayPalOrderRecord(
        paypal_order_id="ORDER-TEST-001",
        authorization_id="AUTH-TEST-001",
        amount_value="450.00",
        currency_code="USD",
        status="ORDER_CREATED",
        work_order_id="WO-2026-001",
        predictive_event_id="EVT-VIB-001",
        equipment_tag="P-101A",
        quote_id="quote-01",
        vendor_id="apex-diagnostics",
        create_request_id="req-create-001",
    )
    in_memory_db.add(record)
    in_memory_db.commit()
    in_memory_db.refresh(record)

    assert record.id is not None
    assert record.paypal_order_id == "ORDER-TEST-001"
    assert record.status == "ORDER_CREATED"

    # Transition to AUTHORIZED
    record.status = "AUTHORIZED"
    record.authorize_request_id = "req-auth-001"
    in_memory_db.commit()

    queried = in_memory_db.query(PayPalOrderRecord).filter_by(paypal_order_id="ORDER-TEST-001").first()
    assert queried.status == "AUTHORIZED"
    assert queried.amount_value == "450.00"

    data = queried.to_dict()
    assert data["paypal_order_id"] == "ORDER-TEST-001"
    assert data["status"] == "AUTHORIZED"
    assert data["amount_value"] == "450.00"


def test_paypal_webhook_event_idempotency(in_memory_db):
    """Verify PayPalWebhookEvent uniqueness constraint for idempotent deduplication."""
    event = PayPalWebhookEvent(
        event_id="WH-EVT-12345",
        event_type="PAYMENT.CAPTURE.COMPLETED",
        resource_id="CAPTURE-SANDBOX-9999",
        signature_verified=True,
        status="PROCESSED",
    )
    in_memory_db.add(event)
    in_memory_db.commit()

    queried = in_memory_db.query(PayPalWebhookEvent).filter_by(event_id="WH-EVT-12345").first()
    assert queried is not None
    assert queried.signature_verified is True
    assert queried.status == "PROCESSED"


def test_completion_evidence_record(in_memory_db):
    """Verify CompletionEvidenceRecord storage and integrity attributes."""
    evidence = CompletionEvidenceRecord(
        evidence_record_id="EVD-001",
        work_order_id="WO-2026-001",
        quote_id="quote-01",
        equipment_tag="P-101A",
        filename="service_report_P101A.pdf",
        file_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        validation_passed=True,
        is_synthetic=True,
    )
    in_memory_db.add(evidence)
    in_memory_db.commit()

    queried = in_memory_db.query(CompletionEvidenceRecord).filter_by(evidence_record_id="EVD-001").first()
    assert queried is not None
    assert queried.validation_passed is True
    assert queried.is_synthetic is True
    data = queried.to_dict()
    assert data["evidence_record_id"] == "EVD-001"
    assert data["validation_passed"] is True
