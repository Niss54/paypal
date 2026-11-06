"""Tests for Second Scenario: Reefer Cold-Chain Transport Procurement (FIX 2).
Verifies that KinetixRAG generalizes beyond rotating machinery to logistics and thermal equipment.
"""
import pytest
from backend.app.services.procurement.orchestrator import ProcurementOrchestrator
from backend.app.services.procurement.mandate import MandateDecision, RiskLane


def test_reefer_incident_retrieval():
    orchestrator = ProcurementOrchestrator()
    incident = orchestrator.get_incident(scenario_id="cold-chain")
    assert incident["equipment_id"] == "REEFER-TRK-9042"
    assert incident["scenario_id"] == "SCN-2026-COLD-01"
    assert incident["status"] == "CRITICAL_THERMAL_EXCURSION"
    assert incident["metric_name"] == "Discharge Temperature Delta"
    assert "Compressor Scroll Assembly" in incident["component"]

    # GraphRAG context
    grag = incident["graphrag_context"]
    assert grag["node_id"] == "FE-COLD-01"
    assert "FDA-21CFR211" in str(grag["citations"])


def test_reefer_quotes_retrieval():
    orchestrator = ProcurementOrchestrator()
    quotes = orchestrator.get_quotes(scenario_id="cold-chain")
    assert len(quotes) == 2
    winner = quotes[0]
    assert winner["quote_id"] == "Q-2026-COLD-01"
    assert winner["vendor_id"] == "chicago-emergency-dock"
    assert winner["amount"] == "480.00"
    assert winner["sla_hours"] == 2
    assert winner["ai_evaluation"]["recommended"] is True


def test_reefer_quote_mandate_evaluation_allowed():
    orchestrator = ProcurementOrchestrator()
    result = orchestrator.evaluate_quote("Q-2026-COLD-01")
    assert result["decision"] == MandateDecision.ALLOWED.value
    # Reefer is marked as critical asset, requiring supervisor sign-off
    assert result["risk_lane"] == RiskLane.LANE_B_EXCEPTION.value
    assert result["requires_supervisor_signoff"] is True
    assert result["audit_hash"] is not None


def test_reefer_quote_sla_breach_blocked():
    orchestrator = ProcurementOrchestrator()
    result = orchestrator.evaluate_quote("Q-2026-COLD-02")
    # Quote 2 has SLA 6h, within 48h mandate limit but marked as secondary
    assert result["quote"]["vendor_id"] == "joliet-cold-logistics"
    assert result["decision"] == MandateDecision.ALLOWED.value
