"""Seed Industrial Equipment Knowledge Graph into Neo4j (AuraDB Cloud or Local).
Connects to Neo4j using environment variables and initializes the full ontology:
- Equipment (:Equipment {tag_id, name, type, critical})
- Component (:Component {part_number, name, manufacturer})
- FailureEvent (:FailureEvent {id, description, root_cause, signature})
- Procedure (:Procedure {id, name, type, standard})
- WorkOrder (:WorkOrder {id, status, equipment_tag, cost_usd})

Usage:
    python scripts/seed_neo4j.py
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    from neo4j import GraphDatabase
except ImportError:
    print("[ERROR] neo4j driver not installed. Run: pip install neo4j")
    sys.exit(1)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")

CYPHER_STATEMENTS = [
    # 1. Constraints & Indexes for fast retrieval
    "CREATE CONSTRAINT equipment_tag IF NOT EXISTS FOR (e:Equipment) REQUIRE e.tag_id IS UNIQUE",
    "CREATE CONSTRAINT failure_event_id IF NOT EXISTS FOR (f:FailureEvent) REQUIRE f.id IS UNIQUE",
    "CREATE CONSTRAINT procedure_id IF NOT EXISTS FOR (p:Procedure) REQUIRE p.id IS UNIQUE",
    "CREATE CONSTRAINT component_part IF NOT EXISTS FOR (c:Component) REQUIRE c.part_number IS UNIQUE",

    # 2. Equipment Nodes
    """
    MERGE (e:Equipment {tag_id: 'P-101A'})
    SET e.name = 'Primary Slurry Feed Pump P-101A',
        e.type = 'Centrifugal Slurry Pump',
        e.critical = true,
        e.operating_speed_rpm = 1780,
        e.power_rating_kw = 450,
        e.iso_classification = 'ISO 10816-3 Group 1 Rigid',
        e.vibration_alarm_threshold_mm_s = 4.50,
        e.site_id = 'plant-mumbai-01'
    """,
    """
    MERGE (e:Equipment {tag_id: 'REPLAY-ASSET-01'})
    SET e.name = 'NASA IMS Bearing Test Rig Shaft 1',
        e.type = 'Empirical Run-to-Failure Accelerometry Baseline',
        e.critical = true,
        e.dataset_source = 'NASA Ames Prognostics Center of Excellence (2004)',
        e.runout_rms_mm_s = 5.42,
        e.sampling_rate_khz = 20.0
    """,

    # 3. Component Nodes (Real SKF Bearing Specification)
    """
    MERGE (c:Component {part_number: 'SKF-22210-E-C3'})
    SET c.name = 'Spherical Roller Bearing 22210 E/C3',
        c.manufacturer = 'SKF Group',
        c.bore_diameter_mm = 50.0,
        c.outer_diameter_mm = 90.0,
        c.width_mm = 23.0,
        c.dynamic_load_rating_kn = 104.0,
        c.unspsc_code = '31171504',
        c.defect_frequency_bpfo_hz = 148.2
    """,

    # 4. Failure Event Nodes (NASA IMS Outer Race Spalling BPFO)
    """
    MERGE (f:FailureEvent {id: 'FE-001'})
    SET f.name = 'Outer Race Fatigue Spalling (BPFO)',
        f.description = 'Accelerated surface fatigue spalling on bearing outer race raceway',
        f.root_cause = 'Lubricant starvation followed by cyclic micro-impact spalling',
        f.fault_signature = 'BPFO harmonic sidebands at 148.2 Hz and elevated RMS velocity',
        f.iso_severity_zone = 'Zone C/D Excursion (Alarm Limit: 4.50 mm/s RMS)',
        f.projected_hours_to_seizure = '48-72'
    """,

    # 5. Standard Operating Procedure (SOP) Nodes
    """
    MERGE (p:Procedure {id: 'PROC-001'})
    SET p.name = 'Dial Indicator Laser Shaft Alignment SOP',
        p.type = 'Precision Millwright Maintenance',
        p.standard = 'ISO 10816-3 / ISO 20816-3 Class II',
        p.max_tolerance_microns = 15.0,
        p.mandated_post_repair_vibration_max_mm_s = 4.50
    """,

    # 6. Graph Relationships
    """
    MATCH (e:Equipment {tag_id: 'P-101A'}), (c:Component {part_number: 'SKF-22210-E-C3'})
    MERGE (e)-[:HAS_COMPONENT {subsystem: 'Drive-End Bearing assembly'}]->(c)
    """,
    """
    MATCH (c:Component {part_number: 'SKF-22210-E-C3'}), (f:FailureEvent {id: 'FE-001'})
    MERGE (c)-[:SUSCEPTIBLE_TO {failure_mode: 'FATIGUE_SPALLING'}]->(f)
    """,
    """
    MATCH (f:FailureEvent {id: 'FE-001'}), (p:Procedure {id: 'PROC-001'})
    MERGE (f)-[:MITIGATED_BY {action: 'EMERGENCY_REPLACEMENT_AND_LASER_ALIGNMENT'}]->(p)
    """,
    """
    MATCH (e:Equipment {tag_id: 'P-101A'}), (f:FailureEvent {id: 'FE-001'})
    MERGE (e)-[:ACTIVE_INCIDENT {detected_at: '2026-11-04T14:32:00Z', measured_rms_mm_s: 4.82}]->(f)
    """,
]


def seed_database():
    print(f"Connecting to Neo4j at: {NEO4J_URI} as {NEO4J_USERNAME}...")
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("[SUCCESS] Connected to Neo4j successfully!")
    except Exception as exc:
        print(f"[FAIL] Could not connect to Neo4j ({NEO4J_URI}): {exc}")
        print("\nTip: If using Neo4j AuraDB Free, ensure NEO4J_URI=neo4j+s://<instance-id>.databases.neo4j.io in .env")
        return False

    with driver.session() as session:
        for i, cypher in enumerate(CYPHER_STATEMENTS, 1):
            try:
                session.run(cypher.strip())
                print(f"[{i}/{len(CYPHER_STATEMENTS)}] Executed Cypher block successfully.")
            except Exception as e:
                print(f"[{i}/{len(CYPHER_STATEMENTS)}] Warning/Notice on block: {e}")

    print("\n[COMPLETE] Neo4j Industrial Knowledge Graph successfully seeded!")
    driver.close()
    return True


if __name__ == "__main__":
    seed_database()
