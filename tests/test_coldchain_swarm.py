"""Unit and integration tests for Cold-Chain Telemetry, Swarm Orchestration, and PayPal API."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from telemetry.adapters.coldchain import ColdChainTelemetryAdapter
from backend.app.services.machine_money.coldchain_swarm import ColdChainSwarmOrchestrator
from backend.app.services.machine_money.schemas import VendorTier
from backend.app.main import app

client = TestClient(app)


def test_coldchain_telemetry_adapter_nominal_and_excursion():
    """Verifies temperature slope, MKT calculation, and critical 30-min window detection."""
    adapter = ColdChainTelemetryAdapter()

    # Step 0: Nominal
    r0 = adapter.generate_step(0)
    assert r0.internal_temp_c < 6.0
    assert r0.usp_1079_status == "COMPLIANT"
    assert r0.minutes_until_irreversible_denaturation > 60

    # Step 4: Critical excursion
    r4 = adapter.generate_step(4)
    assert r4.internal_temp_c > 8.0
    assert r4.compressor_vibration_mm_s >= 4.5
    assert r4.usp_1079_status == "EXCURSION_CRITICAL"
    # Formulation specific window is ~28.5 minutes (well under general 4-hour insulin guideline)
    assert r4.minutes_until_irreversible_denaturation < 35.0


def test_coldchain_mkt_arrhenius_formula():
    """Validates Mean Kinetic Temperature formula math."""
    adapter = ColdChainTelemetryAdapter()
    temps = [4.0, 5.0, 6.0, 8.5]
    mkt = adapter.calculate_mean_kinetic_temperature(temps)
    # MKT gives greater weight to higher excursions
    assert mkt > 5.0
    assert mkt < 9.0


@pytest.mark.asyncio
async def test_coldchain_swarm_orchestrator_consensus():
    """Verifies 4-agent consensus, SLA qualification, and PayPal settlement dispatch."""
    orchestrator = ColdChainSwarmOrchestrator()

    with patch(
        "backend.app.services.machine_money.providers.paypal.PayPalProvider.execute_payout",
        new_callable=AsyncMock,
    ) as mock_payout:
        mock_payout.return_value = {
            "success": True,
            "payout_batch_id": "BATCH-SWARM-TEST-001",
            "sender_batch_id": "kinetix-batch-test",
            "batch_status": "SUCCESS",
            "amount_usd": 450.00,
            "recipient": "chicago-redn@kinetixpay-depot.com",
            "sender_item_id": "item-test-01",
        }

        res = await orchestrator.execute_swarm_consensus(
            step=4,
            autonomous_policy_cap_usd=1000.00,
        )

        assert res.scenario_id == "COLDCHAIN-EXCURSION-TRK-9042"
        assert res.cargo_valuation_usd == 1400000.00
        assert "Trastuzumab" in res.cargo_manifest

        # Verify 4 Swarm Agents
        assert len(res.swarm_agents) == 4
        agent_ids = [a.agent_id for a in res.swarm_agents]
        assert "SensorProbe-01" in agent_ids
        assert "PharmGraph-02" in agent_ids
        assert "Auctioneer-03" in agent_ids
        assert "PayPalGovernor-04" in agent_ids

        # Agent 1 Check
        a1 = next(a for a in res.swarm_agents if a.agent_id == "SensorProbe-01")
        assert a1.verdict == "THERMAL_EXCURSION_CONFIRMED"

        # Agent 2 Check (Biological stability & USP <1079>)
        a2 = next(a for a in res.swarm_agents if a.agent_id == "PharmGraph-02")
        assert a2.verdict == "REGULATORY_INTERVENTION_MANDATED"
        assert a2.details["critical_action_window_minutes"] < 35.0

        # Agent 3 Check (Winner selection: Chicago Emergency Bio-Vault)
        a3 = next(a for a in res.swarm_agents if a.agent_id == "Auctioneer-03")
        assert "Chicago Emergency Bio-Vault" in a3.verdict
        assert a3.details["distance_sla_minutes"] == 18.0

        # Agent 4 Check (PayPal execution)
        a4 = next(a for a in res.swarm_agents if a.agent_id == "PayPalGovernor-04")
        assert a4.verdict == "PAYPAL_SETTLEMENT_EXECUTED"
        assert a4.details["cargo_value_preserved_usd"] == "$1,400,000.00"

        # Verify Post-Payment ERP Reconciliation Record
        assert res.reconciliation is not None
        assert res.reconciliation.gl_account == "GL-6410"
        assert res.reconciliation.bill_of_lading == "BOL-99412"
        assert res.reconciliation.payout_batch_id == "BATCH-SWARM-TEST-001"
        assert len(res.reconciliation.proof_hash) == 64


def test_fastapi_paypal_endpoints():
    """Tests the new FastAPI endpoints for PayPal Swarm and Config."""
    # Test Config endpoint
    config_res = client.get("/api/v1/machine-money/paypal/config")
    assert config_res.status_code == 200
    config_data = config_res.json()
    assert "erp_gl_account" in config_data
    assert config_data["erp_gl_account"] == "GL-6410"

    # Test Swarm endpoint with patched payout
    with patch(
        "backend.app.services.machine_money.providers.paypal.PayPalProvider.execute_payout",
        new_callable=AsyncMock,
    ) as mock_payout:
        mock_payout.return_value = {
            "success": True,
            "payout_batch_id": "BATCH-FASTAPI-001",
            "batch_status": "SUCCESS",
            "amount_usd": 450.00,
            "recipient": "depot@example.com",
        }

        swarm_res = client.post(
            "/api/v1/machine-money/paypal/swarm-auction",
            json={"step": 4, "policy_cap_usd": 1000.0},
        )
        assert swarm_res.status_code == 200
        swarm_data = swarm_res.json()
        assert swarm_data["scenario_id"] == "COLDCHAIN-EXCURSION-TRK-9042"
        assert len(swarm_data["swarm_agents"]) == 4
        assert swarm_data["reconciliation"]["gl_account"] == "GL-6410"
