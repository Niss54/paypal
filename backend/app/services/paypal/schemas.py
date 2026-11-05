"""Strict Pydantic schemas for PayPal Orders v2 REST API (Authorization & Capture Lifecycle).
Complies with PayPal REST API v2 Specifications and Master PRD V2 Section 8.4.
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OrderIntent(str, Enum):
    AUTHORIZE = "AUTHORIZE"
    CAPTURE = "CAPTURE"


class OrderStatus(str, Enum):
    CREATED = "CREATED"
    SAVED = "SAVED"
    APPROVED = "APPROVED"
    VOIDED = "VOIDED"
    COMPLETED = "COMPLETED"
    PAYER_ACTION_REQUIRED = "PAYER_ACTION_REQUIRED"


class AuthorizationStatus(str, Enum):
    CREATED = "CREATED"
    CAPTURED = "CAPTURED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"
    PARTIALLY_CAPTURED = "PARTIALLY_CAPTURED"
    VOIDED = "VOIDED"
    PENDING = "PENDING"


class CaptureStatus(str, Enum):
    COMPLETED = "COMPLETED"
    DECLINED = "DECLINED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
    PENDING = "PENDING"
    REFUNDED = "REFUNDED"
    FAILED = "FAILED"


class Money(BaseModel):
    currency_code: str = Field(default="USD", description="ISO 4217 3-letter currency code")
    value: str = Field(..., description="Decimal representation string (e.g. '450.00'), never float")


class ItemUnit(BaseModel):
    name: str = Field(..., max_length=127)
    quantity: str = Field(default="1", max_length=10)
    unit_amount: Money
    description: Optional[str] = Field(default=None, max_length=127)
    sku: Optional[str] = Field(default=None, max_length=127)
    category: Optional[str] = Field(default="PHYSICAL_GOODS")


class AmountBreakdown(BaseModel):
    item_total: Optional[Money] = None
    shipping: Optional[Money] = None
    handling: Optional[Money] = None
    tax_total: Optional[Money] = None
    insurance: Optional[Money] = None
    shipping_discount: Optional[Money] = None
    discount: Optional[Money] = None


class PurchaseUnitAmount(BaseModel):
    currency_code: str = "USD"
    value: str
    breakdown: Optional[AmountBreakdown] = None


class PurchaseUnit(BaseModel):
    reference_id: str = Field(default="default", max_length=256)
    description: Optional[str] = Field(default=None, max_length=127)
    custom_id: Optional[str] = Field(default=None, max_length=127, description="Correlates work order or quote")
    invoice_id: Optional[str] = Field(default=None, max_length=127)
    amount: PurchaseUnitAmount
    items: Optional[List[ItemUnit]] = None


class LinkDescription(BaseModel):
    href: str
    rel: str
    method: Optional[str] = "GET"


class PayPalOrderCreateRequest(BaseModel):
    intent: OrderIntent = OrderIntent.AUTHORIZE
    purchase_units: List[PurchaseUnit]
    application_context: Optional[Dict[str, Any]] = None


class PayPalOrderResponse(BaseModel):
    id: str
    status: OrderStatus
    intent: OrderIntent
    purchase_units: List[PurchaseUnit]
    links: List[LinkDescription] = Field(default_factory=list)
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    raw_response: Dict[str, Any] = Field(default_factory=dict)


class PayPalAuthorizeResponse(BaseModel):
    authorization_id: str
    status: AuthorizationStatus
    amount: Money
    invoice_id: Optional[str] = None
    custom_id: Optional[str] = None
    expiration_time: Optional[datetime] = None
    links: List[LinkDescription] = Field(default_factory=list)
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    raw_response: Dict[str, Any] = Field(default_factory=dict)


class PayPalCaptureRequest(BaseModel):
    amount: Optional[Money] = None
    invoice_id: Optional[str] = None
    note_to_payer: Optional[str] = None
    final_capture: bool = True


class PayPalCaptureResponse(BaseModel):
    capture_id: str
    status: CaptureStatus
    amount: Money
    final_capture: bool = True
    seller_protection: Optional[Dict[str, Any]] = None
    seller_receivable_breakdown: Optional[Dict[str, Any]] = None
    links: List[LinkDescription] = Field(default_factory=list)
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    raw_response: Dict[str, Any] = Field(default_factory=dict)


class PayPalVoidResponse(BaseModel):
    authorization_id: str
    status: str = "VOIDED"
    links: List[LinkDescription] = Field(default_factory=list)
    raw_response: Dict[str, Any] = Field(default_factory=dict)
