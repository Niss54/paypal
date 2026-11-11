"""Honest local preflight; this is not proof of a deployed payment lifecycle.

Default: sandbox OAuth, live graph read, local policy checks and ERP configuration.
No payment or ERP records are created unless --create-sandbox-order is supplied.
That flag creates an unapproved Sandbox order only, never authorizes or captures.
"""
import argparse
import asyncio
from dataclasses import dataclass
import hashlib
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv


@dataclass(frozen=True)
class CheckResult:
    status: str
    detail: str
    required: bool = True

    @property
    def passed(self) -> bool:
        return self.status == "PASS"


def print_result(label: str, result: CheckResult) -> None:
    scope = "required" if result.required else "optional"
    print(f"[{result.status}] {label} ({scope}): {result.detail}")


async def verify_paypal(create_order: bool = False) -> CheckResult:
    from backend.app.services.paypal.client import PayPalClient

    client = PayPalClient()
    # A preflight must never send credentials or create records against production.
    if client.base_url != "https://api-m.sandbox.paypal.com":
        return CheckResult("FAIL", "PAYPAL_API_BASE_URL must be the official Sandbox endpoint")
    if not client.is_configured or "your_paypal" in client.client_id.lower():
        return CheckResult("FAIL", "Sandbox credentials missing or placeholder")
    await client.get_access_token()
    if not create_order:
        return CheckResult("PASS", "Sandbox OAuth authenticated; checkout, authorization and capture NOT tested")

    from backend.app.services.paypal.orders import PayPalOrderService

    order = await PayPalOrderService(client=client).create_order(
        amount_value="450.00", currency_code="USD", work_order_id="WO-DIAG-001",
        quote_id="Q-2026-001", description="KinetixRAG explicit preflight Sandbox order",
    )
    intent = getattr(order.intent, "value", order.intent)
    if not order.id or intent != "AUTHORIZE":
        return CheckResult("FAIL", "Sandbox response missing order ID or AUTHORIZE intent")
    return CheckResult("PASS", f"Sandbox order {order.id} created; buyer approval, authorization and capture NOT tested")


def verify_neo4j() -> CheckResult:
    from backend.app.core.neo4j import check_neo4j_health, FallbackNeo4jSession, get_session

    health = check_neo4j_health()
    if not health.get("connected") or health.get("fallback_active"):
        return CheckResult("SIMULATED", "Remote Neo4j unavailable; fallback does not verify a live graph", required=False)
    sessions = get_session()
    try:
        session = next(sessions)
        if isinstance(session, FallbackNeo4jSession):
            return CheckResult("SIMULATED", "Graph session fell back after health check", required=False)
        records = list(session.run("""
            MATCH (eq:Equipment {tag_id: 'P-101A'})-[:HAS_COMPONENT]->(comp:Component)
            RETURN eq, comp LIMIT 1
        """))
        if not records:
            return CheckResult("FAIL", "Connected graph has no P-101A component path", required=False)
        return CheckResult("PASS", "Live Neo4j query returned P-101A and a component", required=False)
    finally:
        sessions.close()


async def verify_erp() -> CheckResult:
    from backend.app.services.erp.ibm_maximo import IBMMaximoConnector
    from backend.app.services.erp.sap_s4hana import SAPS4HANAConnector

    sap = SAPS4HANAConnector()
    maximo = IBMMaximoConnector()
    configured = []
    if sap.is_live_configured:
        configured.append("SAP")
    if maximo.is_live_configured:
        configured.append("Maximo")
    if configured:
        return CheckResult("UNVERIFIED", f"{', '.join(configured)} configured; no external ERP writes or ledger verification performed", required=False)
    return CheckResult("SIMULATED", "No live ERP configured; payload adapters are demo-only, no external posting verified", required=False)


def verify_evidence_and_mandates() -> CheckResult:
    from types import SimpleNamespace
    from backend.app.services.procurement.orchestrator import ProcurementOrchestrator
    from backend.app.services.procurement.evidence import EvidenceGatedCaptureController

    orch = ProcurementOrchestrator()
    for quote_id in ("Q-2026-001", "Q-2026-COLD-01"):
        result = orch.evaluate_quote(quote_id)
        if result.get("decision") != "ALLOWED":
            return CheckResult("FAIL", f"Seeded quote {quote_id} rejected by mandate: {result.get('decision')}")
        if result.get("requires_supervisor_signoff") is not True:
            return CheckResult("FAIL", f"Seeded critical quote {quote_id} did not require supervisor approval")
    order = SimpleNamespace(
        status="AUTHORIZED", authorization_id="AUTH-LOCAL-PREFLIGHT", is_simulated=True,
        evidence_record_id=None, mandate_snapshot_json="{}",
    )
    allowed, _ = EvidenceGatedCaptureController.verify_capture_eligibility(order, None, None)
    if allowed:
        return CheckResult("FAIL", "Local policy allowed capture without evidence")
    return CheckResult("PASS", "Local fixture mandates and missing-evidence denial checked; no HTTP endpoint or physical sensor tested")


def verify_merkle_tree() -> CheckResult:
    from backend.app.services.procurement.orchestrator import ProcurementOrchestrator

    leaves = [hashlib.sha256(f"stage-{i}".encode()).hexdigest() for i in range(7)]
    root, depth = ProcurementOrchestrator.compute_merkle_root(leaves)
    changed = leaves.copy()
    changed[3] = hashlib.sha256(b"altered-stage").hexdigest()
    changed_root, _ = ProcurementOrchestrator.compute_merkle_root(changed)
    repeated_root, _ = ProcurementOrchestrator.compute_merkle_root(leaves)
    if len(root) != 64 or depth != 3 or root == changed_root or root != repeated_root:
        return CheckResult("FAIL", "Merkle root reproducibility or changed-leaf check failed")
    return CheckResult("PASS", "Local 7-leaf fixture: repeatable root, changed leaf changes root; O(N) construction, O(log N) depth. No external anchoring tested")


async def collect_checks(create_order: bool = False) -> dict[str, CheckResult]:
    checks = {}
    for label, verifier, required in (
        ("PayPal Sandbox", lambda: verify_paypal(create_order), True),
        ("Neo4j graph", verify_neo4j, False),
        ("Evidence and mandates", verify_evidence_and_mandates, True),
        ("Merkle audit", verify_merkle_tree, True),
        ("ERP connectors", verify_erp, False),
    ):
        try:
            result = verifier()
            if asyncio.iscoroutine(result):
                result = await result
            if not isinstance(result, CheckResult):
                raise TypeError("Verifier returned no structured result")
            checks[label] = result
        except Exception as exc:
            # Do not print credential-bearing HTTP exception text.
            checks[label] = CheckResult("FAIL", f"Check raised {type(exc).__name__}; inspect local service logs", required=required)
    return checks


def summarize(checks: dict[str, CheckResult]) -> int:
    print("\n--- PREFLIGHT COMPONENT BREAKDOWN ---")
    pass_count = 0
    fail_count = 0
    sim_count = 0

    for label, result in checks.items():
        print_result(label, result)
        if result.status == "PASS":
            pass_count += 1
        elif result.status == "FAIL":
            fail_count += 1
        else:
            sim_count += 1

    total = len(checks)
    print(f"\nSummary counts: {pass_count}/{total} PASS, {sim_count}/{total} SIMULATED/UNVERIFIED, {fail_count}/{total} FAIL")

    required = [result for result in checks.values() if result.required]
    required_passed = bool(required) and all(r.passed for r in required)
    has_failures = any(r.status == "FAIL" for r in checks.values())

    passed = required_passed and not has_failures
    print(f"PREFLIGHT REQUIRED CHECKS: {'PASS' if passed else 'FAIL'}")

    if has_failures:
        print(f"PREFLIGHT OVERALL STATUS: FAIL ({fail_count} component check(s) failed)")
        exit_code = 1
    elif not required_passed:
        print("PREFLIGHT OVERALL STATUS: FAIL (one or more required checks did not pass)")
        exit_code = 1
    elif sim_count > 0:
        print("PREFLIGHT OVERALL STATUS: PASS (REQUIRED CONTROLS MET, WITH OPTIONAL SIMULATED COMPONENTS)")
        exit_code = 0
    else:
        print("PREFLIGHT OVERALL STATUS: ALL PASS (ALL CHECKS FULLY VERIFIED)")
        exit_code = 0

    print("Scope: this process only. SIMULATED/UNVERIFIED checks are not live integration passes.")
    print("Not verified: hosted deployment, full PayPal checkout lifecycle, external ERP posting, physical sensor authenticity, submission eligibility.")
    return exit_code


async def main(create_order: bool = False) -> int:
    return summarize(await collect_checks(create_order))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--create-sandbox-order", action="store_true", help="Explicitly create one unapproved Sandbox order (no capture)")
    args = parser.parse_args()
    load_dotenv(REPO_ROOT / ".env")
    sys.exit(asyncio.run(main(args.create_sandbox_order)))
