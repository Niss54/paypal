"""PayPal REST API v2 Integration Package for KinetixRAG.
Provides decoupled Orders v2 lifecycle (Create -> Authorize -> Gated Capture -> Void -> Webhooks).
"""
from backend.app.services.paypal.client import (
    PayPalClient,
    PayPalError,
    PayPalAuthError,
    PayPalAPIError,
    PayPalConnectionError,
)
from backend.app.services.paypal.schemas import (
    OrderIntent,
    OrderStatus,
    AuthorizationStatus,
    CaptureStatus,
    Money,
    ItemUnit,
    PurchaseUnit,
    PurchaseUnitAmount,
    PayPalOrderCreateRequest,
    PayPalOrderResponse,
    PayPalAuthorizeResponse,
    PayPalCaptureRequest,
    PayPalCaptureResponse,
    PayPalVoidResponse,
)
from backend.app.services.paypal.orders import PayPalOrderService
from backend.app.services.paypal.authorization import PayPalAuthorizationService
from backend.app.services.paypal.capture import PayPalCaptureService

__all__ = [
    "PayPalClient",
    "PayPalError",
    "PayPalAuthError",
    "PayPalAPIError",
    "PayPalConnectionError",
    "OrderIntent",
    "OrderStatus",
    "AuthorizationStatus",
    "CaptureStatus",
    "Money",
    "ItemUnit",
    "PurchaseUnit",
    "PurchaseUnitAmount",
    "PayPalOrderCreateRequest",
    "PayPalOrderResponse",
    "PayPalAuthorizeResponse",
    "PayPalCaptureRequest",
    "PayPalCaptureResponse",
    "PayPalVoidResponse",
    "PayPalOrderService",
    "PayPalAuthorizationService",
    "PayPalCaptureService",
]
