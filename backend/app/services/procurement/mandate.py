"""Deterministic Spending Mandate Engine for Industrial Procurement.
Enforces hard server-side policy caps, allowlisted vendors, asset criticality,
and structural prompt-injection isolation.
Satisfies Master PRD V2 Section 6.3, 6.4, 6.5, and 11.2.
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from enum import Enum
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MandateDecision(str, Enum):
    ALLOWED = "ALLOWED"
    BLOCKED = "BLOCKED"
    REQUIRES_REVIEW = "REQUIRES_REVIEW"


class RiskLane(str, Enum):
    LANE_A_ROUTINE = "LANE_A_ROUTINE"
    LANE_B_EXCEPTION = "LANE_B_EXCEPTION"


class SpendingMandate(BaseModel):
    """Server-owned policy record. Versioned and immutable for each payment decision."""
    mandate_id: str = "mnd-routine-01"
    version: int = 1
    site_id: str = "plant-mumbai-01"
    equipment_scope: List[str] = Field(
        default_factory=lambda: ["P-101A", "P-101B", "C-201", "P-102", "P-103", "REEFER-TRK-9042"]
    )
    allowed_service_ids: List[str] = Field(
        default_factory=lambda: [
            "bearing-inspection",
            "laser-alignment",
            "vibration-analysis",
            "thermal-diagnostics",
            "emergency-cold-dock",
        ]
    )
    allowed_vendor_ids: List[str] = Field(
        default_factory=lambda: [
            "apex-diagnostics",
            "precision-dynamics",
            "quantum-reliability",
            "chicago-emergency-dock",
            "joliet-cold-logistics",
        ]
    )
    max_amount: str = "1000.00"  # Decimal string representation
    currency_code: str = "USD"
    max_sla_hours: int = 48
    max_quote_age_seconds: int = 86400  # 24 hours
    min_evidence_requirements: List[str] = Field(
        default_factory=lambda: ["checklist", "diagnostic_report"]
    )
    auto_authorize_enabled: bool = True
    auto_capture_enabled: bool = True
    require_human_for_critical_assets: bool = True
    critical_asset_tags: List[str] = Field(
        default_factory=lambda: ["P-101A", "TURB-01"]
    )
    min_evidence_confidence: float = 0.85
    risk_tier: str = "ROUTINE"
    valid_from: datetime = Field(default_factory=lambda: utcnow() - timedelta(days=1))
    valid_until: datetime = Field(default_factory=lambda: utcnow() + timedelta(days=365))
    created_by: str = "admin-treasury"
    created_at: datetime = Field(default_factory=utcnow)


class MandateEvaluationResult(BaseModel):
    decision: MandateDecision
    mandate_id: str
    mandate_version: int
    quote_id: str
    equipment_tag: str
    vendor_id: str
    amount_value: str
    currency_code: str
    risk_lane: RiskLane
    human_approval_required: bool
    reason_codes: List[str]
    details: Dict[str, Any] = Field(default_factory=dict)
    prompt_injection_warning: bool = False
    timestamp: datetime = Field(default_factory=utcnow)


class SpendingMandateEngine:
    """Deterministic server-side evaluator of spending authority."""

    PROMPT_INJECTION_INDICATORS = [
        "ignore previous",
        "override budget",
        "bypass policy",
        "system override",
        "set limit",
        "authorize maximum",
        "disregard rules",
        "prompt injection",
        "sudo pay",
        "elevate privilege",
    ]

    @classmethod
    def scan_untrusted_text(cls, text: str) -> bool:
        """Scan untrusted user/vendor notes for hostile instruction override attempts."""
        if not text:
            return False
        lower = text.lower()
        return any(pattern in lower for pattern in cls.PROMPT_INJECTION_INDICATORS)

    @classmethod
    def evaluate_quote(
        cls,
        mandate: SpendingMandate,
        quote: Dict[str, Any],
        equipment_tag: str,
        untrusted_text: str = "",
    ) -> MandateEvaluationResult:
        """Evaluate an accepted quotation against the immutable server mandate snapshot."""
        reasons: List[str] = []
        details: Dict[str, Any] = {}
        decision = MandateDecision.ALLOWED
        risk_lane = RiskLane.LANE_A_ROUTINE
        human_approval_required = False

        quote_id = str(quote.get("quote_id", "quote-unknown"))
        vendor_id = str(quote.get("vendor_id", "unknown"))
        service_id = str(quote.get("service_id", "unknown"))
        raw_amount = str(quote.get("amount", quote.get("amount_usd", "0.00")))
        currency = str(quote.get("currency", quote.get("currency_code", "USD"))).upper()

        # 1. Structural prompt injection scan (Flags warning, never allows text to mutate policy)
        injection_found = cls.scan_untrusted_text(untrusted_text) or cls.scan_untrusted_text(str(quote.get("notes", "")))
        if injection_found:
            reasons.append("SEC-INJECTION-WARNING: Hostile override language detected in memo; quarantined")
            details["prompt_injection_flagged"] = True
            logger.warning("Prompt injection pattern detected in procurement memo for quote %s", quote_id)

        # 2. Currency check
        if currency != mandate.currency_code.upper():
            reasons.append(f"POL-CURRENCY-MISMATCH: Currency {currency} != mandate {mandate.currency_code}")
            decision = MandateDecision.BLOCKED

        # 3. Vendor Allowlist check
        if vendor_id not in mandate.allowed_vendor_ids:
            reasons.append(f"POL-VENDOR-UNAPPROVED: Vendor '{vendor_id}' is not in approved list")
            decision = MandateDecision.BLOCKED

        # 4. Equipment Scope check
        if equipment_tag not in mandate.equipment_scope:
            reasons.append(f"POL-EQUIPMENT-OUT-OF-SCOPE: Asset '{equipment_tag}' not covered by mandate")
            decision = MandateDecision.BLOCKED

        # 5. Service ID check
        if service_id not in mandate.allowed_service_ids:
            reasons.append(f"POL-SERVICE-UNAUTHORIZED: Service '{service_id}' not covered by mandate")
            decision = MandateDecision.BLOCKED

        # 6. Amount validation using Decimal arithmetic
        try:
            quote_amount_dec = Decimal(raw_amount)
            mandate_cap_dec = Decimal(mandate.max_amount)
        except Exception as exc:
            reasons.append(f"POL-AMOUNT-MALFORMED: Invalid decimal format '{raw_amount}': {exc}")
            decision = MandateDecision.BLOCKED
            quote_amount_dec = Decimal(0)
            mandate_cap_dec = Decimal(0)

        if quote_amount_dec <= Decimal("0.00"):
            reasons.append(f"POL-AMOUNT-NONPOSITIVE: Quote amount ${quote_amount_dec} must be strictly positive")
            decision = MandateDecision.BLOCKED
        elif quote_amount_dec > mandate_cap_dec:
            excess = quote_amount_dec - mandate_cap_dec
            reasons.append(f"POL-BUDGET-EXCEEDED: Quote ${quote_amount_dec} exceeds cap ${mandate_cap_dec} by ${excess}")
            decision = MandateDecision.REQUIRES_REVIEW
            risk_lane = RiskLane.LANE_B_EXCEPTION
            human_approval_required = True
            details["excess_amount"] = str(excess)

        # 7. SLA hours limit check
        sla_val = quote.get("sla_hours")
        if sla_val is not None:
            try:
                sla_hours = float(sla_val)
                max_sla = getattr(mandate, "max_sla_hours", 48)
                if sla_hours > max_sla:
                    reasons.append(f"POL-SLA-EXCEEDED: SLA {sla_hours:g}h exceeds maximum allowed {max_sla}h window")
                    decision = MandateDecision.BLOCKED
            except (ValueError, TypeError):
                pass

        # 8. Quote Expiry check
        created_at_val = quote.get("created_at")
        if isinstance(created_at_val, str):
            try:
                created_at_dt = datetime.fromisoformat(created_at_val)
                if created_at_dt.tzinfo is None:
                    created_at_dt = created_at_dt.replace(tzinfo=timezone.utc)
                age = (utcnow() - created_at_dt).total_seconds()
                if age > mandate.max_quote_age_seconds:
                    reasons.append(f"POL-QUOTE-EXPIRED: Quote age {int(age)}s exceeds limit {mandate.max_quote_age_seconds}s")
                    decision = MandateDecision.BLOCKED
            except Exception:
                pass

        # 9. Critical Asset Escalation (Risk Lane B)
        if equipment_tag in mandate.critical_asset_tags and mandate.require_human_for_critical_assets:
            if decision == MandateDecision.ALLOWED:
                reasons.append(f"POL-CRITICAL-ASSET: '{equipment_tag}' requires human supervisor dual-signature")
                risk_lane = RiskLane.LANE_B_EXCEPTION
                human_approval_required = True

        return MandateEvaluationResult(
            decision=decision,
            mandate_id=mandate.mandate_id,
            mandate_version=mandate.version,
            quote_id=quote_id,
            equipment_tag=equipment_tag,
            vendor_id=vendor_id,
            amount_value=f"{quote_amount_dec:.2f}",
            currency_code=currency,
            risk_lane=risk_lane,
            human_approval_required=human_approval_required,
            reason_codes=reasons,
            details=details,
            prompt_injection_warning=injection_found,
        )
