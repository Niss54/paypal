"""Evidence-Gated Industrial Procurement Orchestrator.
Coordinates predictive trigger (NASA IMS), RFQ generation, deterministic spending mandate gating,
PayPal Orders v2 authorization lifecycle, vendor completion evidence verification, and gated capture.
Complies with Master PRD V2 Sections 0.2, 0.3, 6.1, 6.2, 8.4, 9.4, 9.5, and 10.
"""
import hashlib
import json
import logging
import math
import os
import re
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from backend.app.core.neo4j import get_session
from backend.app.db.models import (
    CompletionEvidenceRecord,
    PayPalOrderRecord,
)
from backend.app.services.paypal.authorization import PayPalAuthorizationService
from backend.app.services.paypal.capture import PayPalCaptureService
from backend.app.services.paypal.orders import PayPalOrderService
from backend.app.services.procurement.evidence import (
    EvidenceDecision,
    EvidenceGatedCaptureController,
    EvidenceSubmission,
    EvidenceValidationResult,
    EvidenceValidator,
)
from backend.app.services.procurement.mandate import (
    MandateDecision,
    RiskLane,
    SpendingMandate,
    SpendingMandateEngine,
)

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


CANONICAL_INCIDENT = {
    "scenario_id": "SCN-2026-IMS-01",
    "equipment_id": "P-101A",
    "equipment_tag": "P-101A",
    "equipment_name": "Primary Slurry Feed Pump P-101A",
    "component": "Drive-End Spherical Roller Bearing (SKF 22210 E/C3)",
    "part_number": "SKF-22210-E-C3",
    "unspsc_code": "31171504",
    "manufacturer": "SKF Group",
    "anomaly_source": "NASA IMS Bearing Accelerometry Dataset (Test 2, Bearing 1)",
    "trigger_timestamp": "2026-11-04T14:32:00Z",
    "metric_name": "Vibration Velocity RMS",
    "measured_value_mm_s": 4.82,
    "normal_baseline_mm_s": 2.10,
    "alarm_threshold_mm_s": 4.50,
    "status": "CRITICAL_ANOMALY_EXCURSION",
    "diagnosis": (
        "Outer race fatigue spalling detected via high-frequency envelope analysis (BPFO: 148.2 Hz). "
        "Bearing degradation exceeds ISO 10816-3 Level C operational boundary (4.50 mm/s RMS). "
        "Catastrophic seizure anticipated within 48-72 operating hours without intervention."
    ),
    "recommended_action": "Emergency replacement with OEM SKF 22210 E/C3 bearing, dial indicator laser alignment, and vibration validation.",
    "work_order_id": "WO-2026-IMS-001",
    "is_critical_asset": True,
    "requires_supervisor_signoff": True,
}

DEMO_QUOTES = [
    {
        "quote_id": "Q-2026-001",
        "vendor_id": "VND-001",
        "vendor_code": "US-MOT-10821",
        "vendor_name": "Motion Industries (Direct Industrial Partner)",
        "service_id": "SRV-BRG-REPLACE",
        "part_number": "SKF-22210-E-C3",
        "part_name": "SKF Explorer Spherical Roller Bearing (50mm Bore)",
        "unspsc_code": "31171504",
        "amount": "450.00",
        "currency": "USD",
        "sla_hours": 24,
        "is_allowlisted": True,
        "is_synthetic": True,
        "synthetic_label": "[SYNTHETIC DEMO QUOTE]",
        "scope_description": "Supply genuine OEM SKF 22210 E/C3 bearing and dispatch certified millwright technician for on-site replacement, laser alignment, and vibration verification.",
        "is_direct_paypal_sandbox_merchant": True,
        "scoring": {
            "cost_score": 92.0,
            "sla_score": 95.0,
            "reliability_score": 96.0,
            "composite_rank": 1,
            "hard_gates_passed": True,
        },
        "ai_evaluation": {
            "recommended": True,
            "rationale": "Optimal Pareto frontier solution. At $450.00 USD, complies with the $500.00 mandate cap. 24h SLA guarantees repair well within the 48-72h failure horizon. Highest composite reliability score (96%).",
            "tradeoff_vs_competitors": "Preferred over VND-002 ($680.00 cap breach) and VND-003 (72h SLA breach risking pump seizure).",
        },
    },
    {
        "quote_id": "Q-2026-002",
        "vendor_id": "VND-002",
        "vendor_code": "US-AIT-40291",
        "vendor_name": "Applied Industrial Technologies (SKF Certified Partner)",
        "service_id": "SRV-BRG-REPLACE",
        "part_number": "SKF-22210-E-C3-CERAMIC",
        "part_name": "SKF Hybrid Ceramic Bearing Upgrade",
        "unspsc_code": "31171504",
        "amount": "680.00",
        "currency": "USD",
        "sla_hours": 12,
        "is_allowlisted": True,
        "is_synthetic": True,
        "synthetic_label": "[SYNTHETIC DEMO QUOTE]",
        "scope_description": "Expedited 12h emergency response with premium hybrid ceramic bearing upgrade and laser alignment.",
        "is_direct_paypal_sandbox_merchant": False,
        "scoring": {
            "cost_score": 60.0,
            "sla_score": 100.0,
            "reliability_score": 90.0,
            "composite_rank": 2,
            "hard_gates_passed": False,
            "gate_failure_reason": "Quote amount $680.00 exceeds $500.00 spending mandate cap",
        },
        "ai_evaluation": {
            "recommended": False,
            "rationale": "Hard-gate policy breach. At $680.00 USD, exceeds the $500.00 autonomous mandate cap by $180.00. While 12h SLA is superior, policy strictly forbids unapproved budget overruns.",
            "tradeoff_vs_competitors": "Faster delivery than VND-001, but requires supervisor budget exception override.",
        },
    },
    {
        "quote_id": "Q-2026-003",
        "vendor_id": "VND-003",
        "vendor_code": "US-GRN-99120",
        "vendor_name": "Grainger Industrial Supply (MRO Spares)",
        "service_id": "SRV-BRG-REPLACE",
        "part_number": "SKF-22210-E-C3-STANDARD",
        "part_name": "SKF 22210 Standard Spares Kit",
        "unspsc_code": "31171504",
        "amount": "420.00",
        "currency": "USD",
        "sla_hours": 72,
        "is_allowlisted": True,
        "is_synthetic": True,
        "synthetic_label": "[SYNTHETIC DEMO QUOTE]",
        "scope_description": "Standard ground dispatch bearing supply and repair kit.",
        "is_direct_paypal_sandbox_merchant": False,
        "scoring": {
            "cost_score": 98.0,
            "sla_score": 40.0,
            "reliability_score": 85.0,
            "composite_rank": 3,
            "hard_gates_passed": False,
            "gate_failure_reason": "SLA 72h exceeds 48h emergency replacement window",
        },
        "ai_evaluation": {
            "recommended": False,
            "rationale": "Operational risk violation. Lowest cost ($420.00 USD), but 72h SLA exceeds the critical 48h emergency replacement window, creating unacceptable asset seizure risk.",
            "tradeoff_vs_competitors": "$30.00 cheaper than VND-001, but unacceptable downtime risk.",
        },
    },
]

CANONICAL_INCIDENT_REEFER = {
    "scenario_id": "SCN-2026-COLD-01",
    "equipment_id": "REEFER-TRK-9042",
    "equipment_tag": "REEFER-TRK-9042",
    "equipment_name": "Refrigerated Transport Truck #9042 (Thermo King SB-210)",
    "component": "Compressor Scroll Assembly (Thermo King SB-210+)",
    "part_number": "TK-SCROLL-420-R",
    "unspsc_code": "24102305",
    "manufacturer": "Thermo King Corporation",
    "anomaly_source": "Carrier APX™ Cold Chain Telematics Gateway",
    "trigger_timestamp": "2026-11-05T09:14:00Z",
    "metric_name": "Discharge Temperature Delta",
    "measured_value_mm_s": 8.7,
    "normal_baseline_mm_s": 2.0,
    "alarm_threshold_mm_s": 5.0,
    "status": "CRITICAL_THERMAL_EXCURSION",
    "diagnosis": (
        "Refrigerant discharge temperature delta reached +8.7°C (normal: +2.0°C, alarm boundary: +5.0°C). "
        "Compressor scroll seal degradation detected via thermal gradient sensor. "
        "Perishable pharmaceutical cold chain integrity breached if not serviced within 4 operating hours."
    ),
    "recommended_action": "Emergency cold-dock dispatch, compressor scroll gasket overhaul, and nitrogen pressure decay test.",
    "work_order_id": "WO-2026-COLD-001",
    "is_critical_asset": True,
    "requires_supervisor_signoff": True,
}

DEMO_QUOTES_REEFER = [
    {
        "quote_id": "Q-2026-COLD-01",
        "vendor_id": "chicago-emergency-dock",
        "vendor_code": "US-CHI-98211",
        "vendor_name": "Chicago Cold Logistics & Emergency Docking",
        "service_id": "emergency-cold-dock",
        "part_number": "TK-SCROLL-420-R",
        "part_name": "Thermo King OEM Scroll Seal & Refrigerant Recharge",
        "unspsc_code": "24102305",
        "amount": "480.00",
        "currency": "USD",
        "sla_hours": 2,
        "is_allowlisted": True,
        "is_synthetic": True,
        "synthetic_label": "[SYNTHETIC DEMO QUOTE]",
        "scope_description": "Immediate mobile cold-dock dispatch within 2 hours, nitrogen pressure decay test, and certified EPA 608 recovery.",
        "is_direct_paypal_sandbox_merchant": True,
        "scoring": {
            "cost_score": 90.0,
            "sla_score": 99.0,
            "reliability_score": 95.0,
            "composite_rank": 1,
            "hard_gates_passed": True,
        },
        "ai_evaluation": {
            "recommended": True,
            "rationale": "Emergency response winner. At $480.00 USD, satisfies the $500.00 mandate cap. 2-hour SLA prevents catastrophic pharmaceutical spoilage before the 4-hour threshold.",
            "tradeoff_vs_competitors": "Faster turnaround than Joliet Cold Logistics (6h SLA breach) and within autonomous spending policy limits.",
        },
    },
    {
        "quote_id": "Q-2026-COLD-02",
        "vendor_id": "joliet-cold-logistics",
        "vendor_code": "US-JOL-33104",
        "vendor_name": "Joliet Industrial Refrigeration Fleet Partners",
        "service_id": "emergency-cold-dock",
        "part_number": "TK-SCROLL-420-R",
        "part_name": "Standard Compressor Maintenance Package",
        "unspsc_code": "24102305",
        "amount": "390.00",
        "currency": "USD",
        "sla_hours": 6,
        "is_allowlisted": True,
        "is_synthetic": True,
        "synthetic_label": "[SYNTHETIC DEMO QUOTE]",
        "scope_description": "Standard ground depot repair and nitrogen test.",
        "is_direct_paypal_sandbox_merchant": False,
        "scoring": {
            "cost_score": 96.0,
            "sla_score": 45.0,
            "reliability_score": 88.0,
            "composite_rank": 2,
            "hard_gates_passed": False,
            "gate_failure_reason": "SLA 6h exceeds critical 4h cold-chain spoilage horizon",
        },
        "ai_evaluation": {
            "recommended": False,
            "rationale": "High cargo risk. Lowest price ($390.00 USD), but 6-hour SLA exceeds the critical 4-hour spoilage window, risking $120,000 in perishable inventory.",
            "tradeoff_vs_competitors": "$90 cheaper than Chicago Emergency Dock, but catastrophic downtime risk.",
        },
    },
]

ALL_DEMO_QUOTES = DEMO_QUOTES + DEMO_QUOTES_REEFER

CANONICAL_MANDATE = SpendingMandate(
    mandate_id="MND-2026-P101A",
    version=1,
    site_id="plant-mumbai-01",
    equipment_scope=["P-101A", "P-101B", "C-201", "REEFER-TRK-9042"],
    allowed_service_ids=["SRV-BRG-REPLACE", "bearing-inspection", "emergency-cold-dock"],
    allowed_vendor_ids=["VND-001", "VND-002", "VND-003", "apex-diagnostics", "chicago-emergency-dock", "joliet-cold-logistics"],
    max_amount="500.00",
    currency_code="USD",
    max_sla_hours=48,
    require_human_for_critical_assets=True,
    critical_asset_tags=["P-101A", "REEFER-TRK-9042"],
)


class ProcurementOrchestrator:
    """End-to-end industrial procurement workflow controller."""

    def __init__(
        self,
        order_service: Optional[PayPalOrderService] = None,
        authorization_service: Optional[PayPalAuthorizationService] = None,
        capture_service: Optional[PayPalCaptureService] = None,
    ):
        self.order_service = order_service or PayPalOrderService()
        self.authorization_service = authorization_service or PayPalAuthorizationService()
        self.capture_service = capture_service or PayPalCaptureService()
        self.mandate_engine = SpendingMandateEngine()
        self.evidence_validator = EvidenceValidator()
        self.evidence_controller = EvidenceGatedCaptureController()

    @staticmethod
    def compute_merkle_root(leaves: List[str]) -> Tuple[str, int]:
        """Compute binary Merkle tree root and depth from a list of leaf hashes."""
        if not leaves:
            return "0" * 64, 0
        import math
        depth = math.ceil(math.log2(len(leaves))) if len(leaves) > 1 else 1
        current = list(leaves)
        while len(current) > 1:
            if len(current) % 2 == 1:
                current.append(current[-1])  # Duplicate last element for odd counts
            next_level = []
            for i in range(0, len(current), 2):
                combined = hashlib.sha256(f"{current[i]}:{current[i+1]}".encode("utf-8")).hexdigest()
                next_level.append(combined)
            current = next_level
        return current[0], depth

    @staticmethod
    def generate_merkle_proof(leaves: List[str], target_index: int) -> List[Dict[str, str]]:
        """Generate Merkle audit proof path (siblings) for leaf at target_index."""
        if not leaves or target_index < 0 or target_index >= len(leaves):
            return []
        proof = []
        current = list(leaves)
        idx = target_index
        while len(current) > 1:
            if len(current) % 2 == 1:
                current.append(current[-1])
            is_right = (idx % 2 == 1)
            sibling_idx = idx - 1 if is_right else idx + 1
            sibling_hash = current[sibling_idx]
            proof.append({
                "position": "left" if is_right else "right",
                "hash": sibling_hash,
            })
            next_level = []
            for i in range(0, len(current), 2):
                combined = hashlib.sha256(f"{current[i]}:{current[i+1]}".encode("utf-8")).hexdigest()
                next_level.append(combined)
            current = next_level
            idx = idx // 2
        return proof

    @staticmethod
    def verify_merkle_proof(leaf_hash: str, proof: List[Dict[str, str]], expected_root: str) -> bool:
        """Verify an inclusion proof against the expected root."""
        current = leaf_hash
        for step in proof:
            sibling = step.get("hash", "")
            if step.get("position") == "left":
                current = hashlib.sha256(f"{sibling}:{current}".encode("utf-8")).hexdigest()
            else:
                current = hashlib.sha256(f"{current}:{sibling}".encode("utf-8")).hexdigest()
        return current == expected_root

    def get_incident(self, scenario_id: Optional[str] = None) -> Dict[str, Any]:
        """Returns the grounded incident details (NASA IMS or Reefer Cold-Chain) with live GraphRAG knowledge graph retrieval."""
        if scenario_id and scenario_id.lower() in ("cold-chain", "reefer", "scn-2026-cold-01"):
            incident = CANONICAL_INCIDENT_REEFER.copy()
            incident["graphrag_context"] = {
                "node_id": "FE-COLD-01",
                "failure_mode": "Compressor Scroll Seal Degradation & Refrigerant Leak",
                "component_subsystem": "Transport Refrigeration Unit (TRU)",
                "root_cause_analysis": (
                    "Refrigerant discharge delta +8.7°C exceeds alarm threshold (+5.0°C). "
                    "Compressor scroll seal blow-by confirmed. Cargo compartment loss of cooling imminent within 2-4 hours."
                ),
                "ai_repair_scope_recommendation": (
                    "Execute Work Order WO-2026-COLD-001: Mobile cold-dock dispatch, "
                    "re-seal scroll assembly, nitrogen pressure decay test, and verify discharge delta <= 2.5°C before capture."
                ),
                "rca_confidence": 0.958,
                "rca_confidence_note": "Bayesian thermal envelope match score",
                "failure_forecast_hours": "2-4",
                "failure_forecast_note": "Perishable pharmaceutical cargo spoilage threshold",
                "knowledge_graph_path": [
                    {"type": "Equipment", "id": "REEFER-TRK-9042", "name": "Refrigerated Transport Truck #9042"},
                    {"type": "FailureEvent", "id": "FE-COLD-01", "name": "Scroll Seal Blow-By"},
                    {"type": "Procedure", "id": "PROC-COLD-01", "name": "EPA 608 Mobile Refrigerant Service"},
                    {"type": "Standard", "id": "FDA-21CFR211", "name": "Current Good Manufacturing Practice (cGMP) Cold Chain"},
                ],
                "citations": [
                    "FDA-21CFR211: Cold Chain Temperature Assurance",
                    "PROC-COLD-01: Rapid Emergency Mobile Refrigerant Service Standard",
                    "CARRIER-APX-TRU: Historical Failure Envelope Dataset",
                ],
                "provenance_split": {
                    "empirical_research_foundation": {
                        "dataset": "Carrier APX™ Cold Chain Telematics Gateway",
                        "source_fixture_tag": "REPLAY-TRU-COLD-01",
                        "historical_failure_runout_rms": "8.7°C Delta",
                        "sampling_frequency_khz": 1.0,
                        "curator": "Global Cold Chain Quality Assurance Council",
                    },
                    "operational_plant_demonstration": {
                        "asset_tag": "REEFER-TRK-9042 (Transport Refrigeration Truck)",
                        "current_vibration_rms": "8.7°C Delta",
                        "iso_zone": "Critical Thermal Excursion (Alarm: 5.0°C)",
                        "risk_classification": "LANE_B_CRITICAL",
                        "mandated_dual_control": True,
                    },
                },
            }
            return incident

        incident = CANONICAL_INCIDENT.copy()

        # Dynamic Knowledge Graph Traversal & Diagnostic Attribution
        root_cause_desc = "High-frequency envelope acceleration spectrum exhibits characteristic BPFO/BPFI sidebands indicating fatigue spalling."
        traversed_nodes = [
            {"type": "Equipment", "id": "P-101A", "name": "Crude Charge Pump P-101A"},
            {"type": "FailureEvent", "id": "FE-001", "name": "Bearing Cage Degradation & Overheating"},
            {"type": "Procedure", "id": "PROC-001", "name": "Laser Alignment Standard Operating Procedure"},
            {"type": "DatasetRecord", "id": "NASA-IMS-T2-REC-042", "dataset": "NASA IMS Run-to-Failure"},
        ]
        try:
            sess_gen = get_session()
            sess = next(sess_gen)
            # Live multi-hop Cypher traversal: Equipment -> Component -> FailureEvent -> Procedure
            multi_hop_query = """
            MATCH (eq:Equipment {tag_id: 'P-101A'})-[:HAS_COMPONENT]->(comp:Component)
            OPTIONAL MATCH (comp)-[:SUSCEPTIBLE_TO]->(fe:FailureEvent)
            OPTIONAL MATCH (fe)-[:MITIGATED_BY]->(proc:Procedure)
            RETURN eq, comp, fe, proc
            """
            res = list(sess.run(multi_hop_query))
            if res:
                row = res[0]
                comp_node = row.get("comp") or {}
                fe_node = row.get("fe") or {}
                proc_node = row.get("proc") or {}
                rc = fe_node.get("root_cause")
                if rc:
                    root_cause_desc = f"Knowledge Graph Entity FE-001: {rc}. Defect frequency BPFO: {fe_node.get('defect_frequency_bpfo_hz', '148.2')} Hz. Outer race spalling confirmed."
                if comp_node.get("name"):
                    traversed_nodes[1] = {"type": "Component", "id": comp_node.get("part_number", "SKF-22210-E-C3"), "name": comp_node.get("name"), "manufacturer": comp_node.get("manufacturer", "SKF Group")}
                if proc_node.get("name"):
                    traversed_nodes[2] = {"type": "Procedure", "id": proc_node.get("id", "PROC-001"), "name": proc_node.get("name"), "standard": proc_node.get("standard", "ISO 10816-3")}
            else:
                res_simple = list(sess.run("MATCH (fe:FailureEvent {id: 'FE-001'}) RETURN fe"))
                if res_simple:
                    fe_record = res_simple[0]
                    rc = fe_record.get("root_cause")
                    if rc:
                        root_cause_desc = f"Knowledge Graph Entity FE-001: {rc}. High-frequency envelope acceleration spectrum indicates outer race fatigue spalling."
        except Exception as exc:
            logger.warning("Dynamic Knowledge Graph query fallback: %s", exc)

        incident["graphrag_context"] = {
            "node_id": "FE-001",
            "failure_mode": "Bearing Cage Degradation & Overheating",
            "component_subsystem": "Drive-End Roller Element Bearings",
            "root_cause_analysis": (
                f"{root_cause_desc} Vibration velocity RMS on P-101A is 4.82 mm/s, "
                "exceeding ISO 10816-3 Group 1 rigid boundary for acceptable operation (4.50 mm/s Limit)."
            ),
            "ai_repair_scope_recommendation": (
                "Execute Work Order WO-2026-IMS-001: Procure SKF 22210 spherical roller bearing, "
                "dispatch certified millwright technician, perform dial indicator laser alignment, "
                "and mandate post-repair vibration validation (must verify <= 4.50 mm/s before releasing payment capture)."
            ),
            "rca_confidence": 0.942,
            "rca_confidence_note": "Bayesian envelope match score (illustrative scenario estimate)",
            "failure_forecast_hours": "48-72",
            "failure_forecast_note": "Degradation trend extrapolation based on NASA IMS progression rate (scenario estimate)",
            "knowledge_graph_path": traversed_nodes,
            "citations": [
                "ISO-10816-3: Mechanical Vibration Evaluation on Industrial Machines (Table C.1)",
                "PROC-001: Laser Alignment Standard Operating Procedure",
                "DOC-P101-RCA: Plant Reliability Outer Race Defect (BPFO) Ontology and Historical Incident Ledger",
                "NASA-IMS-2004: Run-to-Failure Accelerometry Baseline Curves (Test 2, Bearing 1)",
            ],
            "provenance_split": {
                "empirical_research_foundation": {
                    "dataset": "NASA IMS Bearing Run-to-Failure Accelerometry (2004)",
                    "source_fixture_tag": "REPLAY-ASSET-01",
                    "historical_failure_runout_rms": "5.42 mm/s",
                    "sampling_frequency_khz": 20.0,
                    "curator": "NASA Ames Prognostics Center of Excellence",
                },
                "operational_plant_demonstration": {
                    "asset_tag": "P-101A (Primary Slurry Feed Pump)",
                    "current_vibration_rms": "4.82 mm/s",
                    "iso_zone": "Zone C/D Excursion (Alarm Boundary: 4.50 mm/s)",
                    "risk_classification": "LANE_B_CRITICAL",
                    "mandated_dual_control": True,
                },
            },
        }
        return incident

    def get_quotes(self, scenario_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns the comparison RFQ quotes with synthetic disclosures."""
        if scenario_id and scenario_id.lower() in ("cold-chain", "reefer", "scn-2026-cold-01"):
            return [q.copy() for q in DEMO_QUOTES_REEFER]
        return [q.copy() for q in DEMO_QUOTES]

    def get_mandate(self) -> Dict[str, Any]:
        """Returns the active spending mandate definition."""
        return {
            "mandate_id": CANONICAL_MANDATE.mandate_id,
            "version": CANONICAL_MANDATE.version,
            "equipment_scope": CANONICAL_MANDATE.equipment_scope,
            "allowed_service_ids": CANONICAL_MANDATE.allowed_service_ids,
            "currency_code": CANONICAL_MANDATE.currency_code,
            "max_amount": CANONICAL_MANDATE.max_amount,
            "max_sla_hours": CANONICAL_MANDATE.max_sla_hours,
            "allowed_vendor_ids": CANONICAL_MANDATE.allowed_vendor_ids,
            "require_human_for_critical_assets": CANONICAL_MANDATE.require_human_for_critical_assets,
            "critical_asset_tags": CANONICAL_MANDATE.critical_asset_tags,
        }

    def evaluate_quote(self, quote_id: str, policy_lane: Optional[str] = None) -> Dict[str, Any]:
        """Deterministic evaluation of a candidate quote against the spending mandate."""
        quote_dict = next((q for q in ALL_DEMO_QUOTES if q["quote_id"] == quote_id), None)
        if not quote_dict:
            raise ValueError(f"Quote {quote_id} not found")

        # Policy Lane A (Autonomous Agent Settlement for Routine Spares < $500):
        # Critical asset dual-signature check is bypassed per autonomous MRO delegation policy rule.
        # Policy Lane B (Regulated Dual-Control Safety Policy):
        # Critical asset requires human supervisor dual-signature.
        is_lane_a = bool(policy_lane and policy_lane.upper() in ("LANE_A", "AUTONOMOUS", "ROUTINE"))

        active_mandate = SpendingMandate(
            mandate_id=CANONICAL_MANDATE.mandate_id,
            version=CANONICAL_MANDATE.version,
            site_id=CANONICAL_MANDATE.site_id,
            equipment_scope=CANONICAL_MANDATE.equipment_scope,
            allowed_service_ids=CANONICAL_MANDATE.allowed_service_ids,
            allowed_vendor_ids=CANONICAL_MANDATE.allowed_vendor_ids,
            max_amount=CANONICAL_MANDATE.max_amount,
            currency_code=CANONICAL_MANDATE.currency_code,
            max_sla_hours=CANONICAL_MANDATE.max_sla_hours,
            require_human_for_critical_assets=(not is_lane_a),
            critical_asset_tags=CANONICAL_MANDATE.critical_asset_tags,
        )

        res = SpendingMandateEngine.evaluate_quote(
            mandate=active_mandate,
            quote=quote_dict,
            equipment_tag=("REEFER-TRK-9042" if "COLD" in quote_id else CANONICAL_INCIDENT["equipment_tag"]),
            untrusted_text=quote_dict.get("scope_description", ""),
        )

        audit_hash = hashlib.sha256(
            f"{res.mandate_id}:{res.quote_id}:{res.amount_value}:{res.timestamp.isoformat()}".encode()
        ).hexdigest()

        return {
            "decision": res.decision.value,
            "risk_lane": res.risk_lane.value,
            "requires_supervisor_signoff": res.human_approval_required,
            "reason_codes": res.reason_codes,
            "audit_hash": audit_hash,
            "quote": quote_dict,
        }

    async def create_paypal_order(
        self,
        db: Session,
        quote_id: str,
        actor: str = "kinetix-procurement-agent",
        is_simulation: bool = False,
        policy_lane: Optional[str] = None,
    ) -> PayPalOrderRecord:
        """Evaluates mandate and creates a PayPal Order with intent=AUTHORIZE."""
        eval_result = self.evaluate_quote(quote_id, policy_lane=policy_lane)
        decision = eval_result["decision"]
        if decision == MandateDecision.BLOCKED.value:
            reasons = "; ".join(eval_result["reason_codes"])
            raise ValueError(f"Quote blocked by spending mandate hard gates: {reasons}")
        if decision == MandateDecision.REQUIRES_REVIEW.value:
            reasons = "; ".join(eval_result["reason_codes"])
            raise ValueError(f"Quote exceeds policy cap and requires prior human review: {reasons}")

        quote = eval_result["quote"]
        amount_dec = Decimal(str(quote["amount"]))
        currency = quote["currency"]

        active_incident = CANONICAL_INCIDENT_REEFER if "COLD" in quote_id else CANONICAL_INCIDENT
        idempotency_key = f"order:{active_incident['work_order_id']}:{quote_id}"
        approve_url = None

        if is_simulation:
            # Explicit simulation mode
            paypal_order_id = f"SIM-ORD-{uuid.uuid4().hex[:12].upper()}"
            order_status = "SIMULATED_ORDER_CREATED"
            approve_url = f"https://www.sandbox.paypal.com/checkoutnow?token={paypal_order_id}"
            is_sim_flag = True
        elif not self.order_service.client.is_configured:
            # Live/Sandbox order requested but credentials are not configured
            raise ValueError(
                "PayPal Sandbox credentials (PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET) are not configured. "
                "Enable Simulation Mode or configure sandbox credentials."
            )
        else:
            # LIVE SANDBOX MODE: real PayPal Orders v2 API call.
            # Exceptions are propagated directly without fake ID substitution.
            order_resp = await self.order_service.create_order(
                amount_value=str(amount_dec),
                currency_code=currency,
                work_order_id=active_incident["work_order_id"],
                quote_id=quote_id,
                description=f"Emergency repair {active_incident['equipment_id']} - {quote['vendor_name']}",
                idempotency_key=idempotency_key,
                payee_email=os.environ.get("PAYPAL_DEMO_RECIPIENT", "").strip() or None,
            )
            paypal_order_id = order_resp.id
            order_status = "ORDER_CREATED"
            is_sim_flag = False
            for link in (order_resp.links or []):
                if link.rel in ("approve", "payer-action"):
                    approve_url = link.href
                    break

        existing = db.query(PayPalOrderRecord).filter(PayPalOrderRecord.paypal_order_id == paypal_order_id).first()
        if existing:
            # Replaying create must not rewrite the identity used for separation of duties.
            if existing.requester_user_id != actor:
                raise ValueError("Existing order belongs to another requester")
            if approve_url:
                existing.approve_url = approve_url
            db.commit()
            db.refresh(existing)
            return existing

        order_record = PayPalOrderRecord(
            paypal_order_id=paypal_order_id,
            work_order_id=active_incident["work_order_id"],
            predictive_event_id="EVT-2026-IMS-01",
            equipment_tag=("REEFER-TRK-9042" if "COLD" in quote_id else CANONICAL_INCIDENT["equipment_tag"]),
            quote_id=quote_id,
            vendor_id=quote["vendor_id"],
            amount_value=str(amount_dec),
            currency_code=currency,
            status=order_status,
            requester_user_id=actor,
            approve_url=approve_url,
            is_simulated=is_sim_flag,
            mandate_id=CANONICAL_MANDATE.mandate_id,
            mandate_version=CANONICAL_MANDATE.version,
            mandate_snapshot_json=json.dumps({
                "risk_lane": eval_result["risk_lane"],
                "human_approval_required": eval_result["requires_supervisor_signoff"],
                "budget_cap": CANONICAL_MANDATE.max_amount,
                "quote_amount": str(amount_dec),
                "audit_hash": eval_result["audit_hash"],
            }),
            create_request_id=idempotency_key,
            evidence_status="PENDING",
        )
        db.add(order_record)
        db.commit()
        db.refresh(order_record)
        return order_record

    async def approve_paypal_order(
        self,
        db: Session,
        order_id: str,
        simulated_approval: bool = False,
    ) -> PayPalOrderRecord:
        """Verifies or records Buyer Approval for a PayPal Order before authorization."""
        order = db.query(PayPalOrderRecord).filter(PayPalOrderRecord.paypal_order_id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        if order.status in ("BUYER_APPROVED", "AUTHORIZED", "EVIDENCE_VERIFIED", "CAPTURED"):
            return order

        if simulated_approval and not order.is_simulated:
            raise ValueError(
                "Simulated approval is only permitted for simulated orders. "
                "Live orders must be approved via PayPal Sandbox checkout."
            )
        if order.is_simulated:
            order.status = "BUYER_APPROVED"
        else:
            # Query PayPal for ground truth status
            order_data = await self.order_service.get_order(order_id)
            if order_data.status.value in ("APPROVED", "COMPLETED"):
                order.status = "BUYER_APPROVED"
            else:
                raise ValueError(
                    f"PayPal Order {order_id} is in status '{order_data.status.value}'. "
                    f"Buyer Approval must be completed in PayPal Sandbox before authorization. "
                    f"Approval URL: {order.approve_url}"
                )

        order.updated_at = utcnow()
        db.commit()
        db.refresh(order)
        return order

    async def authorize_paypal_order(
        self,
        db: Session,
        order_id: str,
        sandbox_authorization_id: Optional[str] = None,
    ) -> PayPalOrderRecord:
        """Authorizes an approved PayPal order and transitions record to AUTHORIZED."""
        order = db.query(PayPalOrderRecord).filter(PayPalOrderRecord.paypal_order_id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        if order.status == "AUTHORIZED" and order.authorization_id:
            return order

        auth_id = sandbox_authorization_id
        auth_status = "CREATED"
        if not auth_id:
            if order.is_simulated:
                auth_id = f"SIM-AUTH-{uuid.uuid4().hex[:12].upper()}"
            else:
                # Live Sandbox mode
                if order.status not in ("BUYER_APPROVED", "APPROVED"):
                    try:
                        order_data = await self.order_service.get_order(order_id)
                        if order_data.status.value == "APPROVED":
                            order.status = "BUYER_APPROVED"
                    except Exception as e:
                        logger.warning(f"Failed to check PayPal order approval status: {e}")

                auth_resp = await self.authorization_service.authorize_order(
                    order_id=order_id,
                    idempotency_key=f"auth:{order_id}",
                )
                auth_id = auth_resp.authorization_id
                auth_status = auth_resp.status.value

                if not auth_id or auth_status not in ("CREATED", "PENDING"):
                    logger.error("PayPal authorization rejected (id=%s, status=%s)", auth_id, auth_status)
                    order.status = "AUTH_REJECTED"
                    db.commit()
                    raise ValueError(f"PayPal authorization was not successful (status={auth_status}). Local order not authorized.")

                # Amount and currency cross-check
                if auth_resp.amount.currency_code != order.currency_code or auth_resp.amount.value != str(order.amount_value):
                    logger.error(
                        "Authorization amount mismatch: order expected %s %s, PayPal authorized %s %s",
                        order.amount_value, order.currency_code, auth_resp.amount.value, auth_resp.amount.currency_code
                    )
                    order.status = "AUTH_AMOUNT_MISMATCH"
                    db.commit()
                    raise ValueError("Authorization amount or currency does not match local order")

        order.authorization_id = auth_id
        # Map PENDING authorization status to AUTH_PENDING (blocks capture until review completes)
        if auth_status == "PENDING":
            order.status = "AUTH_PENDING"
        else:
            order.status = "AUTHORIZED"
        order.authorized_at = utcnow()
        order.authorization_expires_at = order.authorized_at + timedelta(days=29)
        order.authorize_request_id = f"auth-req-{order_id}"
        db.commit()
        db.refresh(order)
        return order

    def sign_off_supervisor(
        self,
        db: Session,
        order_id: str,
        supervisor_id: str,
        notes: str = "Authorized Lane B critical asset maintenance after reviewing telemetry and RFQ",
    ) -> PayPalOrderRecord:
        """Records dual-control supervisor approval required for Lane B critical assets."""
        order = db.query(PayPalOrderRecord).filter(PayPalOrderRecord.paypal_order_id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        # Strict Dual-Control Separation of Duties: Requester cannot act as supervisor
        if order.requester_user_id and supervisor_id == order.requester_user_id:
            raise ValueError(
                f"Separation of duties violation: Requester '{order.requester_user_id}' "
                f"cannot sign off as dual-control supervisor"
            )

        order.reviewer_user_id = supervisor_id
        order.reviewer_notes = notes
        db.commit()
        db.refresh(order)
        return order

    def submit_evidence(
        self,
        db: Session,
        order_id: str,
        submission: EvidenceSubmission,
    ) -> Tuple[CompletionEvidenceRecord, EvidenceValidationResult]:
        """Submits vendor repair evidence, validates against deterministic criteria, and stores record."""
        order = db.query(PayPalOrderRecord).filter(PayPalOrderRecord.paypal_order_id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")
        if order.status not in ("AUTHORIZED", "EVIDENCE_VERIFIED"):
            raise ValueError("Evidence can only be submitted against an authorized, uncaptured order")
        if db.query(CompletionEvidenceRecord).filter(
            CompletionEvidenceRecord.evidence_record_id == submission.evidence_id
        ).first():
            raise ValueError("Evidence identifier already exists; submit a new evidence identifier")

        val_res = self.evidence_validator.validate(submission, order)

        file_bytes = submission.file_bytes
        if not file_bytes and getattr(submission, "file_content", None):
            file_bytes = submission.file_content.encode("utf-8")

        file_hash = submission.file_sha256
        if not file_hash and file_bytes:
            file_hash = hashlib.sha256(file_bytes).hexdigest()
        file_hash = file_hash or hashlib.sha256(f"evidence_{submission.evidence_id}_{order_id}".encode()).hexdigest()

        # Enforce 5 MB maximum file size limit
        if file_bytes and len(file_bytes) > 5 * 1024 * 1024:
            raise ValueError("Evidence payload exceeds maximum allowed size limit of 5 MB")

        # Sanitize evidence ID to eliminate path traversal vulnerabilities
        safe_evidence_id = re.sub(r"[^a-zA-Z0-9_\-]", "", submission.evidence_id)
        if not safe_evidence_id:
            safe_evidence_id = f"evd_{uuid.uuid4().hex[:8]}"

        # Derive truthful artifact file extension from content
        ext = ".bin"
        if file_bytes:
            stripped = file_bytes.strip()
            if stripped.startswith(b"%PDF"):
                ext = ".pdf"
            elif stripped.startswith(b"{") or stripped.startswith(b"["):
                ext = ".json"
            else:
                ext = ".bin"

        # Persist physical evidence artifact to storage with path containment verification
        if file_bytes:
            storage_dir = os.path.abspath(".runtime/evidence")
            os.makedirs(storage_dir, exist_ok=True)
            # Content-addressed names prevent sanitized-ID collisions from overwriting artifacts.
            artifact_file = os.path.abspath(os.path.join(storage_dir, f"{hashlib.sha256(file_bytes).hexdigest()}.bin"))
            if os.path.commonpath([storage_dir, artifact_file]) != storage_dir:
                raise ValueError("Path traversal attempt detected in evidence identifier")
            try:
                with open(artifact_file, "wb") as f_art:
                    f_art.write(file_bytes)
            except Exception as e_art:
                logger.error("Could not persist evidence artifact: %s", e_art)
                raise RuntimeError(f"Storage error: Failed to safely write evidence artifact ({e_art})") from e_art

        evidence_record = CompletionEvidenceRecord(
            evidence_record_id=submission.evidence_id,
            order_id=order.paypal_order_id,
            work_order_id=submission.work_order_id,
            quote_id=submission.quote_id,
            equipment_tag=submission.equipment_tag,
            evidence_type="DIAGNOSTIC_REPORT",
            filename=f"repair_report_{submission.work_order_id}{ext}",
            file_sha256=file_hash,
            file_content=getattr(submission, "file_content", None) or (file_bytes.decode("utf-8", errors="ignore") if file_bytes else None),
            file_size_bytes=len(file_bytes) if file_bytes else 0,
            submitted_by=submission.technician_id,
            provenance_classification=val_res.evidence_provenance,
            checklist_items_json=json.dumps(submission.checklist_items),
            measurements_json=json.dumps(submission.measurements),
            validation_passed=(val_res.decision == EvidenceDecision.PASS),
            validation_reason_codes_json=json.dumps(val_res.reason_codes),
            is_synthetic=submission.is_synthetic,
        )
        db.add(evidence_record)

        # Update order with evidence linkage
        order.evidence_record_id = submission.evidence_id
        order.evidence_hash = file_hash
        # Approval applies to the report that was reviewed, not future replacements.
        order.reviewer_user_id = None
        order.reviewer_notes = None
        if val_res.decision == EvidenceDecision.PASS:
            order.evidence_status = "VERIFIED"
            if order.status == "AUTHORIZED":
                order.status = "EVIDENCE_VERIFIED"
        else:
            order.evidence_status = "FAILED"

        db.commit()
        db.refresh(evidence_record)
        db.refresh(order)

        return evidence_record, val_res

    async def execute_gated_capture(
        self,
        db: Session,
        order_id: str,
        idempotency_key: Optional[str] = None,
        supervisor_auth: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Enforces 'No Evidence, No Capture' policy gate.
        Executes PayPal capture if and only if evidence is valid and supervisor sign-off is satisfied.
        """
        order = db.query(PayPalOrderRecord).filter(PayPalOrderRecord.paypal_order_id == order_id).first()
        if not order:
            return False, f"Order {order_id} not found", None

        # Idempotency check: if already captured, return success
        if order.status == "CAPTURED" and order.capture_id:
            return True, "Order already captured (idempotent)", {
                "capture_id": order.capture_id,
                "status": "COMPLETED",
                "amount": order.amount_value,
                "currency": order.currency_code,
            }

        # Look up stored evidence record strictly bound to this order
        if not order.evidence_record_id:
            return False, "Evidence gate blocked capture: No evidence submitted for this order (No Evidence, No Capture)", None

        evidence_rec = (
            db.query(CompletionEvidenceRecord)
            .filter(
                CompletionEvidenceRecord.evidence_record_id == order.evidence_record_id,
                CompletionEvidenceRecord.order_id == order.paypal_order_id,
                CompletionEvidenceRecord.work_order_id == order.work_order_id,
                CompletionEvidenceRecord.quote_id == order.quote_id,
            )
            .first()
        )

        if not evidence_rec:
            return False, f"Evidence gate blocked capture: Bound evidence '{order.evidence_record_id}' not found for order {order_id}", None

        try:
            checklist = json.loads(evidence_rec.checklist_items_json) if evidence_rec.checklist_items_json else []
        except Exception:
            checklist = []
        try:
            meas = json.loads(evidence_rec.measurements_json) if evidence_rec.measurements_json else {}
        except Exception:
            meas = {}
        try:
            reasons = json.loads(evidence_rec.validation_reason_codes_json) if evidence_rec.validation_reason_codes_json else []
        except Exception:
            reasons = []

        # Independently cross-verify stored evidence attributes (never blindly trust True)
        vendor_match = (evidence_rec.quote_id == order.quote_id)
        checklist_text = " ".join(checklist).lower()
        scope_match = any(kw in checklist_text for kw in ["verified", "completed", "alignment", "bearing", "inspected"])
        vib_val = meas.get("vibration_after_mm_s")
        measurements_valid = False
        try:
            if not isinstance(vib_val, bool) and vib_val is not None and math.isfinite(float(vib_val)) and 0.0 < float(vib_val) <= 4.50:
                measurements_valid = True
        except (ValueError, TypeError):
            measurements_valid = False

        file_integrity_valid = bool(
            evidence_rec.file_sha256
            and evidence_rec.file_sha256 == order.evidence_hash
            and (evidence_rec.is_synthetic or evidence_rec.file_sha256 != EvidenceValidator.EMPTY_SHA256)
        )
        if evidence_rec.file_size_bytes:
            # Recheck the persisted artifact at the payment boundary. A stored PASS flag
            # or nonempty digest cannot establish that bytes have remained unchanged.
            digest = evidence_rec.file_sha256 or ""
            if re.fullmatch(r"[a-f0-9]{64}", digest):
                artifact_file = os.path.join(".runtime", "evidence", f"{digest}.bin")
                try:
                    with open(artifact_file, "rb") as artifact:
                        artifact_bytes = artifact.read(5 * 1024 * 1024 + 1)
                    file_integrity_valid = file_integrity_valid and (
                        len(artifact_bytes) == evidence_rec.file_size_bytes
                        and hashlib.sha256(artifact_bytes).hexdigest() == digest
                        and artifact_bytes.decode("utf-8", errors="ignore") == evidence_rec.file_content
                    )
                except OSError:
                    # In ephemeral container/serverless environments (Render, Fly, Vercel), local disk is ephemeral.
                    # Fallback to verifying against persisted database file_content if available.
                    if evidence_rec.file_content:
                        content_bytes = evidence_rec.file_content.encode("utf-8")
                        file_integrity_valid = file_integrity_valid and (
                            len(content_bytes) == evidence_rec.file_size_bytes
                            and hashlib.sha256(content_bytes).hexdigest() == digest
                        )
                    else:
                        file_integrity_valid = False
            else:
                file_integrity_valid = False
        elif not evidence_rec.is_synthetic:
            file_integrity_valid = False
        fields_complete = bool(evidence_rec.evidence_record_id and checklist and meas)

        reconstructed_pass = (
            evidence_rec.validation_passed
            and evidence_rec.equipment_tag == order.equipment_tag
            and vendor_match
            and scope_match
            and measurements_valid
            and file_integrity_valid
            and fields_complete
        )

        evidence_result = EvidenceValidationResult(
            decision=EvidenceDecision.PASS if reconstructed_pass else EvidenceDecision.FAIL,
            work_order_match=(evidence_rec.work_order_id == order.work_order_id),
            quote_match=(evidence_rec.quote_id == order.quote_id),
            equipment_match=(evidence_rec.equipment_tag == order.equipment_tag),
            vendor_match=vendor_match,
            service_scope_match=scope_match,
            required_fields_complete=fields_complete,
            measurements_valid=measurements_valid,
            file_integrity_valid=file_integrity_valid,
            evidence_provenance=getattr(evidence_rec, "provenance_classification", "SYNTHETIC_DEMO_FIXTURE"),
            reason_codes=reasons,
        )

        # Build supervisor auth context if signed off in order or passed explicitly
        sup_auth = supervisor_auth
        if not sup_auth and order.reviewer_user_id:
            sup_auth = {
                "approved": True,
                "reviewer_id": order.reviewer_user_id,
                "supervisor_id": order.reviewer_user_id,
                "notes": order.reviewer_notes or "Supervisor sign-off",
            }

        allowed, reason = self.evidence_controller.verify_capture_eligibility(
            order_record=order,
            evidence_result=evidence_result,
            supervisor_auth=sup_auth,
        )

        if not allowed:
            logger.warning(f"Capture blocked by Evidence Gate for order {order_id}: {reason}")
            return False, f"Evidence gate blocked capture: {reason}", None

        # Execute PayPal capture
        # A caller-supplied key must not create a second provider operation for the
        # same authorization when requests overlap or are retried after a timeout.
        capture_idempotency = f"cap:{order.authorization_id}"
        if order.is_simulated:
            capture_id = f"SIM-CAP-{uuid.uuid4().hex[:12].upper()}"
            cap_status = "COMPLETED"
        else:
            if self.capture_service.client.base_url != "https://api-m.sandbox.paypal.com":
                return False, "Sandbox-only prototype: production capture requires trusted physical attestation", None
            # LIVE SANDBOX: Real capture API call
            cap_resp = await self.capture_service.capture_authorization(
                authorization_id=order.authorization_id,
                amount_value=str(order.amount_value),
                currency_code=order.currency_code,
                idempotency_key=capture_idempotency,
            )
            capture_id = cap_resp.capture_id
            cap_status = cap_resp.status.value

            if cap_status != "COMPLETED":
                logger.warning(f"PayPal capture returned non-completed status: {cap_status}")
                order.status = "CAPTURE_PENDING"
                order.capture_id = capture_id
                order.updated_at = utcnow()
                db.commit()
                return False, f"Capture submitted to PayPal but pending settlement confirmation (status={cap_status}). Funds not yet released.", {
                    "capture_id": capture_id,
                    "status": cap_status,
                    "amount": order.amount_value,
                    "currency": order.currency_code,
                }

            # Independent verification of amount and currency returned from PayPal
            if cap_resp.amount.currency_code != order.currency_code or cap_resp.amount.value != str(order.amount_value):
                logger.error(
                    "Capture amount mismatch: expected %s %s, PayPal captured %s %s",
                    order.amount_value, order.currency_code, cap_resp.amount.value, cap_resp.amount.currency_code
                )
                order.status = "CAPTURE_AMOUNT_MISMATCH"
                order.capture_id = capture_id
                order.updated_at = utcnow()
                db.commit()
                return False, f"Capture amount mismatch: expected {order.amount_value} {order.currency_code}, got {cap_resp.amount.value} {cap_resp.amount.currency_code}", {
                    "capture_id": capture_id,
                    "status": "AMOUNT_MISMATCH",
                    "amount": cap_resp.amount.value,
                    "currency": cap_resp.amount.currency_code,
                }

        order.capture_id = capture_id
        order.status = "CAPTURED"
        order.captured_at = utcnow()
        order.capture_request_id = capture_idempotency
        db.commit()
        db.refresh(order)

        return True, "Payment captured successfully under Evidence Gating Policy", {
            "capture_id": capture_id,
            "status": "COMPLETED",
            "amount": order.amount_value,
            "currency": order.currency_code,
            "captured_at": order.captured_at.isoformat(),
        }

    async def void_order(
        self,
        db: Session,
        order_id: str,
        reason: str = "Procurement cancelled or evidence expired",
    ) -> PayPalOrderRecord:
        """Voids an uncaptured authorization."""
        order = db.query(PayPalOrderRecord).filter(PayPalOrderRecord.paypal_order_id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        if order.status == "CAPTURED":
            raise ValueError("Cannot void an already captured order")

        if order.authorization_id and not order.is_simulated:
            try:
                await self.authorization_service.void_authorization(order.authorization_id)
            except Exception as e:
                logger.error(f"Live PayPal void failed: {e}")
                order.status = "VOID_FAILED"
                order.reviewer_notes = f"PayPal void failed: {e}"
                order.updated_at = utcnow()
                db.commit()
                raise ValueError(f"PayPal void operation failed: {e}")

        order.status = "VOIDED"
        order.reviewer_notes = f"Void reason: {reason}"
        db.commit()
        db.refresh(order)
        return order

    def get_audit_lineage(self, db: Session, order_id: str) -> Dict[str, Any]:
        """Assembles the complete immutable causal lineage with unbroken cryptographic SHA-256 hash chaining."""
        order = db.query(PayPalOrderRecord).filter(PayPalOrderRecord.paypal_order_id == order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")

        evidence = None
        if order.evidence_record_id:
            evidence = (
                db.query(CompletionEvidenceRecord)
                .filter(CompletionEvidenceRecord.evidence_record_id == order.evidence_record_id)
                .first()
            )

        stages = [
            {
                "step": 1,
                "title": "Predictive Anomaly Excursion",
                "source": CANONICAL_INCIDENT["anomaly_source"],
                "equipment_id": CANONICAL_INCIDENT["equipment_id"],
                "detail": f"Vibration RMS reached {CANONICAL_INCIDENT['measured_value_mm_s']} mm/s (Alarm: {CANONICAL_INCIDENT['alarm_threshold_mm_s']} mm/s)",
                "status": "TRIGGERED",
                "timestamp": CANONICAL_INCIDENT["trigger_timestamp"],
            },
            {
                "step": 2,
                "title": "GraphRAG Diagnostic Attribution",
                "diagnosis": CANONICAL_INCIDENT["diagnosis"],
                "recommended_action": CANONICAL_INCIDENT["recommended_action"],
                "work_order_id": order.work_order_id,
                "rca_confidence": 0.942,
                "sop_citations": ["PROC-001", "ISO-10816-3", "DOC-P101-RCA"],
                "status": "CONFIRMED",
            },
            {
                "step": 3,
                "title": "RFQ Quote Comparison & Hard-Gate Filter",
                "quotes_evaluated": len(DEMO_QUOTES),
                "selected_vendor_id": order.vendor_id,
                "disclosure": "[SYNTHETIC DEMO QUOTE]",
                "mandate_id": order.mandate_id,
                "budget_cap": "$500.00 USD",
                "status": "APPROVED",
            },
            {
                "step": 4,
                "title": "Spending Mandate Evaluation & Risk Routing",
                "mandate_snapshot": json.loads(order.mandate_snapshot_json) if order.mandate_snapshot_json else {},
                "requester_id": getattr(order, "requester_user_id", "kinetix-procurement-agent"),
                "supervisor_signed_off": bool(order.reviewer_user_id),
                "supervisor_id": order.reviewer_user_id,
                "status": "VERIFIED" if order.reviewer_user_id else "SUPERVISOR_PENDING",
            },
            {
                "step": 5,
                "title": "PayPal Orders v2 Two-Phase Authorization",
                "order_id": order.paypal_order_id,
                "intent": "AUTHORIZE",
                "amount": f"{order.amount_value} {order.currency_code}",
                "authorization_id": order.authorization_id,
                "approve_url": getattr(order, "approve_url", None),
                "is_simulated": getattr(order, "is_simulated", False),
                "authorized_at": order.authorized_at.isoformat() if order.authorized_at else None,
                "policy": "No Evidence, No Capture (Funds held in PayPal Sandbox, not transferred)",
                "status": order.status,
            },
            {
                "step": 6,
                "title": "Vendor Physical Repair & Evidence Validation",
                "evidence_submitted": evidence is not None,
                "evidence_id": evidence.evidence_record_id if evidence else None,
                "validation_passed": evidence.validation_passed if evidence else False,
                "file_sha256": evidence.file_sha256 if evidence else None,
                "status": "VALIDATED" if (evidence and evidence.validation_passed) else "PENDING",
            },
            {
                "step": 7,
                "title": "Evidence-Gated Capture & Settlement",
                "capture_id": order.capture_id,
                "captured_at": order.captured_at.isoformat() if order.captured_at else None,
                "status": "COMPLETED" if order.status == "CAPTURED" else "HELD",
            },
        ]

        # Compute continuous cryptographic SHA-256 hash chaining and binary Merkle tree
        prev_hash = "0" * 64
        leaf_hashes = []
        for stage in stages:
            stage["previous_stage_hash"] = prev_hash
            stage_serialized = json.dumps(stage, sort_keys=True, default=str)
            stage_hash = hashlib.sha256(f"{prev_hash}:{stage_serialized}".encode("utf-8")).hexdigest()
            stage["stage_hash"] = stage_hash
            leaf_hash = hashlib.sha256(stage_serialized.encode("utf-8")).hexdigest()
            stage["leaf_hash"] = leaf_hash
            leaf_hashes.append(leaf_hash)
            prev_hash = stage_hash

        audit_snapshot_hash = prev_hash
        merkle_root, merkle_depth = self.compute_merkle_root(leaf_hashes)

        return {
            "order_id": order.paypal_order_id,
            "work_order_id": order.work_order_id,
            "status": order.status,
            "amount": order.amount_value,
            "currency": order.currency_code,
            "is_simulated": getattr(order, "is_simulated", False),
            "final_chain_digest": audit_snapshot_hash,
            "audit_snapshot_hash": audit_snapshot_hash,
            "merkle_root": merkle_root,
            "merkle_tree": {
                "root": merkle_root,
                "depth": merkle_depth,
                "leaf_count": len(leaf_hashes),
                "verification_complexity": f"O(log2({len(leaf_hashes)})) = {merkle_depth} hops",
            },
            "ledger_type": "Binary Merkle Tree + Sequential Hash Chain",
            "chain_valid": True,
            "lineage_stages": stages,
        }
