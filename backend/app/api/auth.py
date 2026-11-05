"""Authentication & Token Service REST API.
Provides enterprise personas, JWT issuance, and session verification.
"""
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.core.auth import (
    AppRole,
    UserProfile,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])

PERSONA_ROLES: Dict[str, List[str]] = {
    "procurement-agent": [AppRole.ProcurementAgent.value, AppRole.PlantOperator.value],
    "buyer": [AppRole.Buyer.value, AppRole.PlantOperator.value],
    "supervisor": [AppRole.Supervisor.value, AppRole.ReliabilityEngineer.value],
    "operator": [AppRole.PlantOperator.value],
    "auditor": [AppRole.Auditor.value, AppRole.ComplianceOfficer.value],
    "payment-service": [AppRole.PaymentService.value, AppRole.AutomationAdmin.value],
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
def issue_token(req: TokenRequest):
    """Issues a cryptographically signed JWT for the requested role/persona."""
    persona_key = req.persona.lower().strip()
    if persona_key not in PERSONA_ROLES:
        persona_key = "operator"

    roles = PERSONA_ROLES[persona_key]
    user_id = req.user_id or (
        "SUP-CHIEF-09" if persona_key == "supervisor"
        else f"usr-{persona_key}"
    )
    name = PERSONA_NAMES.get(persona_key, "Enterprise Operator")

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
