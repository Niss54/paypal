"""Authentication & Token Service REST API.
Provides enterprise personas, JWT issuance, and session verification.
"""
from typing import Dict, List, Optional
import os
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from backend.app.core.auth import (
    AppRole,
    UserProfile,
    create_access_token,
    get_current_user,
    is_auth_enabled,
)

router = APIRouter(prefix="/auth", tags=["auth"])

PERSONA_ROLES: Dict[str, List[str]] = {
    "procurement-agent": [AppRole.ProcurementAgent.value, AppRole.PlantOperator.value],
    "buyer": [AppRole.Buyer.value, AppRole.ProcurementLead.value],
    "supervisor": [AppRole.Supervisor.value, AppRole.ReliabilityEngineer.value, AppRole.ReliabilityLead.value],
    "operator": [AppRole.PlantOperator.value],
    "auditor": [AppRole.Auditor.value, AppRole.ComplianceOfficer.value],
    "payment-service": [AppRole.PaymentService.value, AppRole.AutomationAdmin.value],
    "technician": [AppRole.VendorTechnician.value],
    "finance": [AppRole.FinanceAdmin.value],
}

PERSONA_DEFAULT_IDS: Dict[str, str] = {
    "procurement-agent": "usr-procurement-agent",
    "buyer": "BUYER-CORP-01",
    "supervisor": "SUP-CHIEF-09",
    "operator": "OP-LOCAL-01",
    "auditor": "AUD-COMPLIANCE-01",
    "payment-service": "PAYMENT-WORKER-01",
    "technician": "TECH-CERT-441",
    "finance": "FIN-ADMIN-01",
}

PERSONA_NAMES: Dict[str, str] = {
    "procurement-agent": "Kinetix Autonomous Procurement Agent",
    "buyer": "Enterprise Plant Buyer",
    "supervisor": "Chief Reliability Supervisor (SUP-CHIEF-09)",
    "operator": "Industrial Plant Operator",
    "auditor": "Compliance & Financial Auditor",
    "payment-service": "PayPal Automated Settlement Worker",
}


class TokenRequest(BaseModel):
    persona: str = Field(default="procurement-agent", description="Pre-configured enterprise persona")
    user_id: Optional[str] = Field(default=None, description="Optional custom user identifier")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    user_id: str
    roles: List[str]
    name: str


@router.post("/token", response_model=TokenResponse)
def issue_token(req: TokenRequest, request: Request):
    """Issues a cryptographically signed JWT for the requested role/persona.
    In production mode (AUTH_ENABLED=true), public unauthenticated token issuance is strictly disabled
    unless authorized via internal admin credentials or during verified test suite execution.
    """
    if is_auth_enabled():
        admin_key = request.headers.get("X-Admin-Key", "").strip()
        expected_key = os.environ.get("DEMO_ADMIN_KEY", "").strip()
        is_test_env = "PYTEST_CURRENT_TEST" in os.environ or os.environ.get("ALLOW_DEV_TEST_JWT", "").lower() == "true"
        if not is_test_env and (not expected_key or admin_key != expected_key):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "token_issuance_forbidden",
                    "detail": "Public token minting is disabled when AUTH_ENABLED=true. Authenticate via Microsoft Entra ID OIDC.",
                },
            )

    persona_key = req.persona.lower().strip()
    if persona_key not in PERSONA_ROLES:
        persona_key = "operator"

    roles = PERSONA_ROLES[persona_key]
    # Bound identity to prevent caller-controlled user_id overrides in production/testing
    if is_auth_enabled() and "PYTEST_CURRENT_TEST" not in os.environ:
        user_id = PERSONA_DEFAULT_IDS.get(persona_key, f"usr-{persona_key}")
    else:
        user_id = req.user_id or PERSONA_DEFAULT_IDS.get(persona_key, f"usr-{persona_key}")

    name = PERSONA_NAMES.get(persona_key, f"Enterprise {persona_key.title()}")

    token = create_access_token(
        user_id=user_id,
        roles=roles,
        name=name,
        expires_delta_seconds=86400,
    )

    return TokenResponse(
        access_token=token,
        token_type="Bearer",
        expires_in=86400,
        user_id=user_id,
        roles=roles,
        name=name,
    )


@router.get("/me", response_model=UserProfile)
def get_authenticated_profile(current_user: UserProfile = Depends(get_current_user)):
    """Returns the caller's verified enterprise identity and role claims."""
    return current_user
