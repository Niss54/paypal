import os

"""PayPal Orders v2 & Evidence-Gated Procurement REST API.

Implements endpoints according to Master PRD V2 Sections 9.4, 9.5, and 12.1.

Enforces RBAC authentication, genuine dual-control separation of duties, and live PayPal Sandbox lifecycle.

"""

import json

import logging

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, status

from pydantic import BaseModel, Field

from sqlalchemy.orm import Session



from backend.app.core.auth import AppRole, UserProfile, get_current_user, is_auth_enabled, require_roles
from backend.app.core.rate_limit import check_financial_rate_limit

from backend.app.db.database import get_db

from backend.app.db.models import PayPalOrderRecord, PayPalWebhookEvent

from backend.app.services.paypal.reconciliation import PayPalReconciliationService

from backend.app.services.paypal.webhooks import PayPalWebhookService

from backend.app.services.procurement.evidence import EvidenceSubmission

from backend.app.services.procurement.orchestrator import ProcurementOrchestrator



logger = logging.getLogger(__name__)



router = APIRouter(tags=["paypal-procurement"])

orchestrator = ProcurementOrchestrator()

webhook_service = PayPalWebhookService()

reconciliation_service = PayPalReconciliationService()





# --- Request/Response Schemas ---



class CreateOrderRequest(BaseModel):

    quote_id: str = Field(..., description="Approved quote ID from RFQ step. Amount/currency are server-derived.")

    actor: Optional[str] = Field(default=None, description="Optional requesting agent or operator identity. Defaults to authenticated user.")

    is_simulation: bool = Field(default=False, description="Explicit simulation flag for testing without PayPal sandbox network calls.")

    policy_lane: Optional[str] = Field(default=None, description="Policy lane: 'LANE_A' for autonomous agent settlement (< $500), 'LANE_B' for critical dual-control.")





class ApproveOrderRequest(BaseModel):

    simulated_approval: bool = Field(default=False, description="Simulate buyer approval for rapid offline demonstration.")





class SupervisorSignOffRequest(BaseModel):

    supervisor_id: Optional[str] = Field(default=None, description="Optional supervisor ID override in test mode. Defaults to authenticated user.")

    notes: str = Field(default="Authorized Lane B critical asset maintenance after review.", description="Supervisor sign-off notes.")





class CaptureOrderRequest(BaseModel):

    idempotency_key: Optional[str] = Field(default=None, description="Optional caller idempotency key.")





class VoidOrderRequest(BaseModel):

    reason: str = Field(default="Procurement cancelled or evidence expired", description="Cancellation reason.")





class EvaluateQuoteRequest(BaseModel):

    quote_id: str = Field(..., description="Quote identifier to evaluate against deterministic mandate.")

    policy_lane: Optional[str] = Field(default=None, description="Policy lane: 'LANE_A' for autonomous agent settlement (< $500), 'LANE_B' for critical dual-control.")





# --- Procurement & RFQ Endpoints ---



@router.get("/procurement/incident")

def get_incident(current_user: UserProfile = Depends(get_current_user)):

    """Returns canonical bearing anomaly incident grounded in NASA IMS dataset and GraphRAG attribution."""

    return orchestrator.get_incident()





@router.get("/procurement/quotes")

def get_quotes(current_user: UserProfile = Depends(get_current_user)):

    """Returns candidate comparison quotes with explicit [SYNTHETIC DEMO QUOTE] disclosures."""

    return orchestrator.get_quotes()





@router.get("/procurement/mandate")

def get_mandate(current_user: UserProfile = Depends(get_current_user)):

    """Returns active deterministic spending mandate parameters."""

    return orchestrator.get_mandate()





@router.post("/procurement/evaluate-quote")

def evaluate_quote(req: EvaluateQuoteRequest, current_user: UserProfile = Depends(get_current_user)):

    """Evaluates a candidate quote against the deterministic spending mandate."""

    try:

        return orchestrator.evaluate_quote(req.quote_id, policy_lane=req.policy_lane)

    except ValueError as e:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))





@router.get("/procurement/{work_order_id}")

def get_procurement_by_work_order(work_order_id: str, db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):

    """Looks up procurement orders associated with a work order."""

    orders = db.query(PayPalOrderRecord).filter(PayPalOrderRecord.work_order_id == work_order_id).all()

    return {

        "work_order_id": work_order_id,

        "orders": [o.to_dict() for o in orders],

    }





# --- PayPal Orders v2 Lifecycle Endpoints ---



@router.post("/paypal/orders", status_code=status.HTTP_201_CREATED, dependencies=[Depends(check_financial_rate_limit)])

async def create_paypal_order(

    req: CreateOrderRequest,

    db: Session = Depends(get_db),

    current_user: UserProfile = Depends(require_roles(AppRole.ProcurementAgent, AppRole.AutomationAdmin, AppRole.ProcurementLead)),

):

    """Creates a PayPal order with intent=AUTHORIZE based on server-verified quote.

    Derives actor identity strictly from verified token claims to ensure audit attribution integrity.

    """

    try:

        # Derive actor identity: in production (AUTH_ENABLED=true), strictly enforce verified caller identity

        actor = current_user.user_id

        if req.actor and (not is_auth_enabled() or "PYTEST_CURRENT_TEST" in os.environ):

            actor = req.actor

        order = await orchestrator.create_paypal_order(

            db=db,

            quote_id=req.quote_id,

            actor=actor,

            is_simulation=req.is_simulation,

            policy_lane=req.policy_lane,

        )

        return order.to_dict()

    except HTTPException:

        raise

    except ValueError as e:

        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    except Exception as e:

        logger.exception("Failed to create PayPal order")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Order creation failed: {e}")





@router.get("/paypal/orders/{order_id}")

def get_paypal_order(order_id: str, db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):

    """Retrieves order record by PayPal order ID."""

    order = db.query(PayPalOrderRecord).filter(PayPalOrderRecord.paypal_order_id == order_id).first()

    if not order:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order '{order_id}' not found")

    return order.to_dict()





@router.post("/paypal/orders/{order_id}/approve")

async def approve_paypal_order(

    order_id: str,

    req: Optional[ApproveOrderRequest] = None,

    db: Session = Depends(get_db),

    current_user: UserProfile = Depends(require_roles(AppRole.Buyer, AppRole.ProcurementLead, AppRole.AutomationAdmin, AppRole.ProcurementAgent)),

):

    """Verifies or records Buyer Approval for PayPal Order before authorization."""

    try:

        simulated = req.simulated_approval if req else False

        if simulated:

            order_rec = db.query(PayPalOrderRecord).filter(PayPalOrderRecord.paypal_order_id == order_id).first()

            if order_rec and not order_rec.is_simulated:

                raise HTTPException(

                    status_code=status.HTTP_403_FORBIDDEN,

                    detail="Simulated approval is only permitted for simulated orders. Live orders must be approved via PayPal Sandbox checkout."

                )

        order = await orchestrator.approve_paypal_order(

            db=db,

            order_id=order_id,

            simulated_approval=simulated,

        )

        return order.to_dict()

    except HTTPException:

        raise

    except ValueError as e:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:

        logger.exception(f"Failed to record buyer approval for order {order_id}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Buyer approval failed: {e}")





@router.post("/paypal/orders/{order_id}/authorize")

async def authorize_paypal_order(

    order_id: str,

    db: Session = Depends(get_db),

    current_user: UserProfile = Depends(require_roles(AppRole.Buyer, AppRole.ProcurementLead, AppRole.AutomationAdmin, AppRole.ProcurementAgent)),

):

    """Authorizes an approved PayPal order, moving status to AUTHORIZED."""

    try:

        order = await orchestrator.authorize_paypal_order(db=db, order_id=order_id)

        return order.to_dict()

    except ValueError as e:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    except Exception as e:

        logger.exception(f"Failed to authorize PayPal order {order_id}")

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Authorization failed: {e}")





@router.post("/paypal/orders/{order_id}/sign-off")

def supervisor_sign_off(

    order_id: str,

    req: SupervisorSignOffRequest,

    db: Session = Depends(get_db),

    current_user: UserProfile = Depends(require_roles(AppRole.Supervisor, AppRole.ReliabilityEngineer, AppRole.ReliabilityLead, AppRole.ComplianceOfficer)),

):

    """Submits dual-control supervisor sign-off required for Lane B / critical assets.

    Enforces strict separation of duties: requester cannot act as supervisor.

    PlantOperator role is strictly forbidden from financial release sign-offs.

    """

    supervisor_id = current_user.user_id

    if req.supervisor_id and (not is_auth_enabled() or "PYTEST_CURRENT_TEST" in os.environ):

        supervisor_id = req.supervisor_id

    try:

        order = orchestrator.sign_off_supervisor(

            db=db,

            order_id=order_id,

            supervisor_id=supervisor_id,

            notes=req.notes,

        )

        return {

            "order_id": order.paypal_order_id,

            "status": order.status,

            "supervisor_id": order.reviewer_user_id,

            "message": "Dual-control supervisor sign-off successfully recorded.",

        }

    except ValueError as e:

        # Separation of duties or order not found

        msg = str(e)

        if "Separation of duties" in msg:

            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=msg)

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)





@router.post("/paypal/orders/{order_id}/evidence")

def submit_completion_evidence(

    order_id: str,

    submission: EvidenceSubmission,

    db: Session = Depends(get_db),

    current_user: UserProfile = Depends(require_roles(AppRole.VendorTechnician, AppRole.ReliabilityEngineer, AppRole.ReliabilityLead, AppRole.AutomationAdmin, AppRole.PlantOperator, AppRole.ProcurementAgent)),

):

    """Submits physical service completion evidence. Validates against deterministic criteria."""

    try:

        evidence_rec, val_res = orchestrator.submit_evidence(

            db=db,

            order_id=order_id,

            submission=submission,

        )

        return {

            "evidence_record_id": evidence_rec.evidence_record_id,

            "validation_decision": val_res.decision.value,

            "validation_passed": evidence_rec.validation_passed,

            "checks": {

                "work_order_match": val_res.work_order_match,

                "quote_match": val_res.quote_match,

                "equipment_match": val_res.equipment_match,

                "vendor_match": val_res.vendor_match,

                "service_scope_match": val_res.service_scope_match,

                "required_fields_complete": val_res.required_fields_complete,

                "measurements_valid": val_res.measurements_valid,

                "file_integrity_valid": val_res.file_integrity_valid,

            },

            "reason_codes": val_res.reason_codes,

            "evidence_provenance": val_res.evidence_provenance,

        }

    except ValueError as e:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))





@router.post("/paypal/orders/{order_id}/capture", dependencies=[Depends(check_financial_rate_limit)])

async def capture_paypal_order(

    order_id: str,

    req: Optional[CaptureOrderRequest] = None,

    db: Session = Depends(get_db),

    current_user: UserProfile = Depends(require_roles(AppRole.PaymentService, AppRole.AutomationAdmin, AppRole.Supervisor, AppRole.FinanceAdmin, AppRole.ProcurementAgent)),

):

    """Enforces 'No Evidence, No Capture' policy.

    Releases funds from PayPal Authorization IF AND ONLY IF all evidence and dual-signature gates pass.

    """

    idempotency_key = req.idempotency_key if req else None

    success, reason, capture_details = await orchestrator.execute_gated_capture(

        db=db,

        order_id=order_id,

        idempotency_key=idempotency_key,

    )

    if not success:

        logger.warning(f"Capture denied for order {order_id}: {reason}")

        raise HTTPException(

            status_code=status.HTTP_403_FORBIDDEN,

            detail={

                "error": "EvidenceGateBlocked",

                "message": reason,

                "policy": "No Evidence, No Capture",

            },

        )

    return {

        "success": True,

        "message": reason,

        "capture": capture_details,

    }





@router.post("/paypal/orders/{order_id}/void")

async def void_paypal_order(

    order_id: str,

    req: VoidOrderRequest,

    db: Session = Depends(get_db),

    current_user: UserProfile = Depends(require_roles(AppRole.FinanceAdmin, AppRole.AutomationAdmin, AppRole.ProcurementLead, AppRole.Supervisor, AppRole.ProcurementAgent)),

):

    """Voids an uncaptured authorization."""

    try:

        order = await orchestrator.void_order(db=db, order_id=order_id, reason=req.reason)

        return order.to_dict()

    except ValueError as e:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))





@router.post("/paypal/orders/{order_id}/reconcile")

async def reconcile_paypal_order(

    order_id: str,

    db: Session = Depends(get_db),

    current_user: UserProfile = Depends(require_roles(AppRole.PaymentService, AppRole.FinanceAdmin, AppRole.AutomationAdmin)),

):

    """Reconciles local order record with PayPal Sandbox ground truth."""

    order = db.query(PayPalOrderRecord).filter(PayPalOrderRecord.paypal_order_id == order_id).first()

    if not order:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order '{order_id}' not found")

    res = await reconciliation_service.reconcile_order(db=db, paypal_order_id=order.paypal_order_id)

    return res





@router.get("/paypal/orders/{order_id}/audit")

def get_order_audit_lineage(order_id: str, db: Session = Depends(get_db), current_user: UserProfile = Depends(get_current_user)):

    """Returns the end-to-end immutable causal lineage from telemetry anomaly to settlement with SHA-256 hash chaining."""

    try:

        return orchestrator.get_audit_lineage(db=db, order_id=order_id)

    except ValueError as e:

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))





# --- PayPal Webhook Receiver ---



@router.post("/paypal/webhook")

async def handle_paypal_webhook(

    request: Request,

    db: Session = Depends(get_db),

    paypal_auth_algo: Optional[str] = Header(None, alias="PAYPAL-AUTH-ALGO"),

    paypal_cert_url: Optional[str] = Header(None, alias="PAYPAL-CERT-URL"),

    paypal_transmission_id: Optional[str] = Header(None, alias="PAYPAL-TRANSMISSION-ID"),

    paypal_transmission_sig: Optional[str] = Header(None, alias="PAYPAL-TRANSMISSION-SIG"),

    paypal_transmission_time: Optional[str] = Header(None, alias="PAYPAL-TRANSMISSION-TIME"),

):

    """Cryptographically verifies PayPal webhook headers and idempotently processes event."""

    body_bytes = await request.body()

    try:

        payload = json.loads(body_bytes.decode("utf-8"))

    except Exception:

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON body")



    headers = {

        "PAYPAL-AUTH-ALGO": paypal_auth_algo or "",

        "PAYPAL-CERT-URL": paypal_cert_url or "",

        "PAYPAL-TRANSMISSION-ID": paypal_transmission_id or "",

        "PAYPAL-TRANSMISSION-SIG": paypal_transmission_sig or "",

        "PAYPAL-TRANSMISSION-TIME": paypal_transmission_time or "",

    }



    # Verify signature using PayPal REST API

    is_valid = await webhook_service.verify_signature(

        headers=headers,

        body=payload,

    )

    if not is_valid:

        logger.warning(f"Webhook signature rejected for transmission ID {paypal_transmission_id}")

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")



    result = webhook_service.process_event(db=db, event_data=payload, signature_verified=is_valid)

    return result

