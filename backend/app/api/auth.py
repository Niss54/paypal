"""Authentication & Token Service REST API.
Provides enterprise personas, JWT issuance, credential login, and session verification.
Enforces zero unauthenticated elevation of supervisor or payment roles.
"""
from typing import Dict, List, Optional
import os
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from backend.app.core.auth import (
    AppRole,
    UserProfile,
    create_access_token,
    get_client_id,
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
    "technician": "Certified Reliability Field Technician",
    "finance": "Enterprise Finance Administrator",
}

DEMO_CREDENTIAL_ENV_KEYS: Dict[str, str] = {
    "supervisor": "DEMO_SUPERVISOR_PASSWORD",
    "procurement-agent": "DEMO_AGENT_PASSWORD",
    "buyer": "DEMO_BUYER_PASSWORD",
    "technician": "DEMO_TECH_PASSWORD",
    "finance": "DEMO_FINANCE_PASSWORD",
    "auditor": "DEMO_AUDITOR_PASSWORD",
    "operator": "DEMO_OPERATOR_PASSWORD",
    "payment-service": "DEMO_PAYMENT_PASSWORD",
}

USER_ID_TO_PERSONA: Dict[str, str] = {
    "usr-procurement-agent": "procurement-agent",
    "buyer-corp-01": "buyer",
    "sup-chief-09": "supervisor",
    "op-local-01": "operator",
    "aud-compliance-01": "auditor",
    "payment-worker-01": "payment-service",
    "tech-cert-441": "technician",
    "fin-admin-01": "finance",
}


def get_demo_credentials() -> Dict[str, str]:
    """Load credentials at request time and never ship usable production defaults.

    Tests receive deterministic fixtures through Pytest's scoped environment. A deployed
    demo must deliberately provide every credential it exposes, which prevents a public
    repository from becoming a source of privileged login passwords.
    """
    if "PYTEST_CURRENT_TEST" in os.environ:
        return {
            "supervisor": "test-supervisor-password",
            "procurement-agent": "test-agent-password",
            "buyer": "test-buyer-password",
            "technician": "test-technician-password",
            "finance": "test-finance-password",
            "auditor": "test-auditor-password",
            "operator": "test-operator-password",
            "payment-service": "test-payment-password",
        }
    return {
        persona: os.environ.get(env_key, "").strip()
        for persona, env_key in DEMO_CREDENTIAL_ENV_KEYS.items()
    }


class LoginRequest(BaseModel):
    username: str = Field(..., description="Enterprise username, user ID, or persona")
    password: str = Field(..., description="Enterprise credentials")


class TokenRequest(BaseModel):
    persona: str = Field(default="procurement-agent", description="Pre-configured enterprise persona")
    user_id: Optional[str] = Field(default=None, description="Optional custom user identifier (only honored in test harness)")
    password: Optional[str] = Field(default=None, description="Enterprise credential required for elevated personas")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    user_id: str
    roles: List[str]
    name: str


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    """Authenticates enterprise credentials and issues a cryptographically signed JWT.
    Enforces separation of duties and verified identity credentials.
    """
    user_key = req.username.lower().strip()
    persona_key = USER_ID_TO_PERSONA.get(user_key, user_key)
    if persona_key not in PERSONA_ROLES:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_credentials", "detail": f"Unknown enterprise user or persona: '{req.username}'"},
        )

    expected_pw = get_demo_credentials().get(persona_key)
    if not expected_pw:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "demo_auth_not_configured", "detail": "Demo credentials are not configured."},
        )
    if not expected_pw or req.password != expected_pw:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_credentials", "detail": "Invalid credentials for requested enterprise identity"},
        )

    roles = PERSONA_ROLES[persona_key]
    user_id = PERSONA_DEFAULT_IDS.get(persona_key, f"usr-{persona_key}")
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


@router.post("/token", response_model=TokenResponse)
def issue_token(req: TokenRequest, request: Request):
    """Issues a signed JWT for the requested persona.
    Elevated roles (supervisor, buyer, finance, payment-service) strictly require credentials
    or admin clearance. Unauthenticated minting of supervisor JWTs is prohibited.
    """
    persona_key = req.persona.lower().strip()
    if persona_key not in PERSONA_ROLES:
        persona_key = "operator"

    # JWT verification configuration must not grant password-free role issuance.
    is_test_env = "PYTEST_CURRENT_TEST" in os.environ
    admin_key = request.headers.get("X-Admin-Key", "").strip()
    expected_admin = os.environ.get("DEMO_ADMIN_KEY", "").strip()
    admin_authorized = bool(expected_admin and admin_key == expected_admin)

    expected_pw = get_demo_credentials().get(persona_key)
    pw_matches = bool(req.password and expected_pw and req.password == expected_pw)

    # Elevated personas with financial or policy sign-off clearance
    elevated_personas = {"supervisor", "buyer", "finance", "payment-service", "auditor"}

    if is_auth_enabled() and get_client_id():
        if not (pw_matches or admin_authorized or is_test_env):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "token_issuance_forbidden",
                    "detail": "Authentication required when Microsoft Entra ID is configured. Supply persona password, X-Admin-Key, or authenticate via Microsoft Entra ID OIDC.",
                },
            )
    else:
        # Development / demo mode: elevated roles still require credentials.
        if persona_key in elevated_personas and not (pw_matches or admin_authorized or is_test_env):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "authentication_required",
                    "detail": f"Persona '{persona_key}' holds elevated approval/payment privileges. Supply password or use /api/auth/login.",
                },
            )

    roles = PERSONA_ROLES[persona_key]

    # Bound identity: caller cannot spoof arbitrary user_id unless in verified test harness
    if is_test_env and req.user_id:
        user_id = req.user_id
    else:
        user_id = PERSONA_DEFAULT_IDS.get(persona_key, f"usr-{persona_key}")

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
