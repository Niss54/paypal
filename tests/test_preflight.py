"""Preflight must distinguish integration evidence from local simulations."""
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from scripts import verify_sandbox as preflight


@pytest.mark.parametrize("status", ["FAIL", "SIMULATED", "UNVERIFIED", "SKIPPED"])
def test_required_nonpass_exits_nonzero(status, capsys):
    result = preflight.summarize({"PayPal": preflight.CheckResult(status, "Not verified")})
    assert result == 1
    assert "PREFLIGHT REQUIRED CHECKS: FAIL" in capsys.readouterr().out


def test_optional_simulation_stays_visible_and_is_not_counted_as_pass(capsys):
    result = preflight.summarize({
        "Policy": preflight.CheckResult("PASS", "Local policy"),
        "ERP": preflight.CheckResult("SIMULATED", "No external posting", required=False),
    })
    assert result == 0
    output = capsys.readouterr().out
    assert "[SIMULATED] ERP" in output
    assert "[PASS] ERP" not in output
    assert "not live integration passes" in output


def test_optional_failure_also_fails_preflight():
    assert preflight.summarize({
        "Policy": preflight.CheckResult("PASS", "OK"),
        "Graph": preflight.CheckResult("FAIL", "Broken query", required=False),
    }) == 1


def test_empty_preflight_cannot_pass():
    assert preflight.summarize({}) == 1


def test_exception_is_retained_as_failure_without_printing_secrets(monkeypatch, capsys):
    async def rejected(*args):
        raise RuntimeError("sensitive-access-token")
    monkeypatch.setattr(preflight, "verify_paypal", rejected)
    monkeypatch.setattr(preflight, "verify_neo4j", lambda: preflight.CheckResult("PASS", "local"))
    monkeypatch.setattr(preflight, "verify_evidence_and_mandates", lambda: preflight.CheckResult("PASS", "local"))
    monkeypatch.setattr(preflight, "verify_merkle_tree", lambda: preflight.CheckResult("PASS", "local"))
    monkeypatch.setattr(preflight, "verify_erp", lambda: preflight.CheckResult("SIMULATED", "demo", False))
    assert asyncio.run(preflight.main()) == 1
    output = capsys.readouterr().out
    assert "RuntimeError" in output
    assert "sensitive-access-token" not in output


def test_disconnected_graph_never_queries_fallback_as_live(monkeypatch):
    from backend.app.core import neo4j
    get_session = MagicMock(side_effect=AssertionError("Must not query fallback as live"))
    monkeypatch.setattr(neo4j, "check_neo4j_health", lambda: {"connected": False, "fallback_active": True})
    monkeypatch.setattr(neo4j, "get_session", get_session)
    assert preflight.verify_neo4j().status == "SIMULATED"
    get_session.assert_not_called()


def test_rejected_mandate_is_not_reported_allowed(monkeypatch):
    from backend.app.services.procurement.orchestrator import ProcurementOrchestrator
    monkeypatch.setattr(ProcurementOrchestrator, "evaluate_quote", lambda *a: {"decision": "DENIED"})
    assert preflight.verify_evidence_and_mandates().status == "FAIL"


def test_local_gate_and_merkle_checks_pass_without_network():
    assert preflight.verify_evidence_and_mandates().passed
    assert preflight.verify_merkle_tree().passed


def test_paypal_default_only_authenticates_and_never_creates_order(monkeypatch):
    from backend.app.services.paypal import client, orders
    paypal = SimpleNamespace(base_url="https://api-m.sandbox.paypal.com", is_configured=True,
                             client_id="configured", get_access_token=AsyncMock(return_value="redacted"))
    monkeypatch.setattr(client, "PayPalClient", lambda: paypal)
    create = MagicMock(side_effect=AssertionError("Order creation not requested"))
    monkeypatch.setattr(orders, "PayPalOrderService", create)
    result = asyncio.run(preflight.verify_paypal())
    assert result.passed
    assert "capture NOT tested" in result.detail
    create.assert_not_called()


def test_preflight_rejects_production_paypal_endpoint_before_auth(monkeypatch):
    from backend.app.services.paypal import client
    paypal = SimpleNamespace(base_url="https://api-m.paypal.com", get_access_token=AsyncMock())
    monkeypatch.setattr(client, "PayPalClient", lambda: paypal)
    assert asyncio.run(preflight.verify_paypal(create_order=True)).status == "FAIL"
    paypal.get_access_token.assert_not_called()


def test_configured_erp_is_unverified_and_never_writes(monkeypatch):
    from backend.app.services.erp import ibm_maximo, sap_s4hana
    sap = SimpleNamespace(is_live_configured=True, sync_maintenance_order=AsyncMock())
    maximo = SimpleNamespace(is_live_configured=True, sync_work_order=AsyncMock())
    monkeypatch.setattr(sap_s4hana, "SAPS4HANAConnector", lambda: sap)
    monkeypatch.setattr(ibm_maximo, "IBMMaximoConnector", lambda: maximo)
    assert asyncio.run(preflight.verify_erp()).status == "UNVERIFIED"
    sap.sync_maintenance_order.assert_not_called()
    maximo.sync_work_order.assert_not_called()
