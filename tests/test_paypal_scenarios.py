"""Unit and integration tests for all 4 PayPal Agentic Commerce Scenarios (PRD Section 4 Step 4)."""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from backend.app.services.machine_money.coldchain_swarm import ColdChainSwarmOrchestrator
from backend.app.main import app

client = TestClient(app)


@pytest.fixture
def swarm_orchestrator():
    return ColdChainSwarmOrchestrator()


@pytest.mark.asyncio
async def test_scenario_1_critical_excursion_happy_path(swarm_orchestrator):
    """Scenario 1: Critical BioPharma Excursion ($450 Emergency Dock) -> Autonomous PayPal Payout."""
    with patch(
        "backend.app.services.machine_money.providers.paypal.PayPalProvider.execute_payout",
        new_callable=AsyncMock,
    ) as mock_payout:
        mock_payout.return_value = {
            "success": True,
            "payout_batch_id": "BATCH-SCENARIO-1",
            "sender_batch_id": "kinetix-batch-001",
            "batch_status": "SUCCESS",
            "amount_usd": 450.00,
            "recipient": "chicago-redn@kinetixpay-depot.com",
        }

        res = await swarm_orchestrator.execute_swarm_consensus(
            step=4,
            autonomous_policy_cap_usd=1000.00,
            scenario="CRITICAL_EXCURSION",
        )

        assert res.scenario_id == "COLDCHAIN-EXCURSION-TRK-9042"
        assert res.payout_result is not None
        assert res.payout_result.batch_status == "SUCCESS"
        assert res.payout_result.amount_usd == 450.00

        a4 = next(a for a in res.swarm_agents if a.agent_id == "PayPalGovernor-04")
        assert a4.verdict == "PAYPAL_SETTLEMENT_EXECUTED"
        assert res.reconciliation.gl_account == "GL-6410"
        assert res.reconciliation.bill_of_lading == "BOL-99412"


@pytest.mark.asyncio
async def test_scenario_2_policy_escalation(swarm_orchestrator):
    """Scenario 2: Policy Escalation (> $1,000 threshold) -> Human-in-the-loop approval."""
    res = await swarm_orchestrator.execute_swarm_consensus(
        step=4,
        autonomous_policy_cap_usd=1000.00,
        scenario="POLICY_ESCALATION",
    )

    a4 = next(a for a in res.swarm_agents if a.agent_id == "PayPalGovernor-04")
    assert a4.verdict == "POLICY_ESCALATION_REQUIRED"
    assert a4.details["status"] == "HELD_FOR_HUMAN_SIGN_OFF"
    assert a4.details["quote_amount_usd"] == 1450.00
    assert a4.details["excess_over_cap_usd"] == 450.00
    # Zero funds moved autonomously
    assert res.payout_result is None


@pytest.mark.asyncio
async def test_scenario_3_multi_party_split_payout(swarm_orchestrator):
    """Scenario 3: Multi-Party Split Payout ($300 Mechanic + $150 Dry Ice Supplier)."""
    with patch(
        "backend.app.services.machine_money.providers.paypal.PayPalProvider.execute_batch_payout",
        new_callable=AsyncMock,
    ) as mock_batch:
        mock_batch.return_value = {
            "success": True,
            "payout_batch_id": "BATCH-SPLIT-99",
            "sender_batch_id": "kinetix-split-001",
            "batch_status": "SUCCESS",
            "total_amount_usd": 450.00,
            "item_count": 2,
        }

        res = await swarm_orchestrator.execute_swarm_consensus(
            step=4,
            autonomous_policy_cap_usd=1000.00,
            scenario="MULTI_PARTY_SPLIT",
        )

        assert res.payout_result is not None
        assert res.payout_result.amount_usd == 450.00
        a4 = next(a for a in res.swarm_agents if a.agent_id == "PayPalGovernor-04")
        assert a4.verdict == "PAYPAL_SPLIT_PAYOUT_EXECUTED"
        assert len(a4.details["split_breakdown"]) == 2
        assert a4.details["split_breakdown"][0]["vendor"] == "Mobile Reefer Mechanic"
        assert a4.details["split_breakdown"][1]["vendor"] == "Emergency Dry Ice Supplier"
        assert res.reconciliation.reconciliation_id.startswith("REC-SPLIT-")


@pytest.mark.asyncio
async def test_scenario_4_provider_degradation_recovery(swarm_orchestrator):
    """Scenario 4: Provider Degradation & Retry -> Graceful fail-closed recovery."""
    res = await swarm_orchestrator.execute_swarm_consensus(
        step=4,
        autonomous_policy_cap_usd=1000.00,
        scenario="PROVIDER_DEGRADATION",
    )

    a4 = next(a for a in res.swarm_agents if a.agent_id == "PayPalGovernor-04")
    assert a4.verdict == "PROVIDER_FAILSAFE_RECOVERY"
    assert a4.details["status"] == "RETRY_SCHEDULED"
    assert "fail_closed_guarantee" in a4.details
    assert res.payout_result is None


def test_fastapi_all_scenarios_integration():
    """Validates FastAPI endpoint handling across all 4 scenarios."""
    scenarios = ["CRITICAL_EXCURSION", "POLICY_ESCALATION", "MULTI_PARTY_SPLIT", "PROVIDER_DEGRADATION"]

    with patch(
        "backend.app.services.machine_money.providers.paypal.PayPalProvider.execute_payout",
        new_callable=AsyncMock,
    ) as mock_payout, patch(
        "backend.app.services.machine_money.providers.paypal.PayPalProvider.execute_batch_payout",
        new_callable=AsyncMock,
    ) as mock_batch:
        mock_payout.return_value = {
            "success": True,
            "payout_batch_id": "BATCH-FASTAPI-01",
            "batch_status": "SUCCESS",
            "amount_usd": 450.00,
        }
        mock_batch.return_value = {
            "success": True,
            "payout_batch_id": "BATCH-FASTAPI-SPLIT",
            "batch_status": "SUCCESS",
            "total_amount_usd": 450.00,
            "item_count": 2,
        }

        for sc in scenarios:
            res = client.post(
                "/api/v1/machine-money/paypal/swarm-auction",
                json={"step": 4, "policy_cap_usd": 1000.0, "scenario": sc},
            )
            assert res.status_code == 200
            data = res.json()
            assert len(data["swarm_agents"]) == 4
            a4 = next(a for a in data["swarm_agents"] if a["agent_id"] == "PayPalGovernor-04")
            assert a4["verdict"] in [
                "PAYPAL_SETTLEMENT_EXECUTED",
                "POLICY_ESCALATION_REQUIRED",
                "PAYPAL_SPLIT_PAYOUT_EXECUTED",
                "PROVIDER_FAILSAFE_RECOVERY",
            ]
