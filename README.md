<div align="center">

<img src="./frontend/public/kr.png" alt="KinetixRAG Logo" width="160" style="margin-bottom: 14px; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.35);" />

# KinetixRAG
### Evidence-Gated Autonomous Industrial Commerce & Deterministic Spending Mandates
**PayPal AI Hackathon 2026**

<p align="center">
  <b>Predictive IoT Telemetry • Hybrid GraphRAG Diagnostic Swarm • Deterministic Spending Mandates • "No Evidence, No Capture" PayPal Orders v2 Settlement</b>
</p>

<p align="center">
  <a href="https://paypalaihackathon.devpost.com/"><img src="https://img.shields.io/badge/PayPal%20AI%20Hackathon-2026-003087?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal AI Hackathon 2026"/></a>
  <a href="#-paypal-orders-v2-two-phase-settlement"><img src="https://img.shields.io/badge/PayPal%20Orders%20v2-2--Phase%20Auth%20%26%20Capture-00457C?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal Orders v2"/></a>
  <a href="https://paypal-pink.vercel.app"><img src="https://img.shields.io/badge/Vercel-Live%20Frontend%20Console-000000?style=for-the-badge&logo=vercel&logoColor=white" alt="Vercel Live"/></a>
  <a href="https://paypal-y2jk.onrender.com/docs"><img src="https://img.shields.io/badge/Render-Hosted%20FastAPI%20Backend-46E3B7?style=for-the-badge&logo=render&logoColor=black" alt="Render Backend"/></a>
  <a href="./JUDGE_README.md"><img src="https://img.shields.io/badge/Judge%20Guide-3--Minute%20Fast--Track-FFC439?style=for-the-badge&logo=readme&logoColor=black" alt="Judge Guide"/></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-16.2.11%20Turbopack-000000?style=flat-square&logo=next.js&logoColor=white" alt="Next.js 16"/>
  <img src="https://img.shields.io/badge/FastAPI-0.115%20Python%203.12-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/TypeScript-5.x%20Strict-3178C6?style=flat-square&logo=typescript&logoColor=white" alt="TypeScript"/>
  <img src="https://img.shields.io/badge/Neo4j-GraphRAG%20Knowledge%20Graph-45818E?style=flat-square&logo=neo4j&logoColor=white" alt="Neo4j"/>
  <img src="https://img.shields.io/badge/Neon-Serverless%20Postgres-00E599?style=flat-square&logo=postgresql&logoColor=black" alt="Neon Postgres"/>
  <img src="https://img.shields.io/badge/Frontend%20Vitest-82%20Passing%20(19%20Suites)-FCC72B?style=flat-square&logo=vitest&logoColor=black" alt="82 Frontend Vitest"/>
  <img src="https://img.shields.io/badge/Core%20Pytest-68%20Passing%20(100%25)-2ea44f?style=flat-square&logo=pytest&logoColor=white" alt="68 Core Pytest"/>
  <img src="https://img.shields.io/badge/Audit%20Ledger-Binary%20Merkle%20Tree%20O(log%20N)-8A2BE2?style=flat-square" alt="Merkle Tree"/>
  <img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="MIT License"/>
</p>

</div>

---

## 📑 Table of Contents

1. [⚡ 60-Second Fast-Track for Hackathon Judges](#-60-second-fast-track-for-hackathon-judges)
2. [🚨 Why KinetixRAG Exists: The Reality in Numbers](#-why-kinetixrag-exists-the-reality-in-numbers)
3. [👥 Who Faces This Problem?](#-who-faces-this-problem)
4. [🔄 Before vs. After: Architectural Paradigm Shift](#-before-vs-after-architectural-paradigm-shift)
5. [⚙️ Core Technical Capabilities](#-core-technical-capabilities)
6. [🏛️ System Architecture & Deep Blueprints Navigation](#-system-architecture--deep-blueprints-navigation)
7. [🛡️ Security, Authorization & Privacy Architecture](#-security-authorization--privacy-architecture)
8. [📋 Detailed Execution Sequence](#-detailed-execution-sequence)
9. [📸 Live Platform Screenshots](#-live-platform-screenshots)
10. [🧪 Comprehensive Test Suite & Terminal Verification](#-comprehensive-test-suite--terminal-verification)
    * [💻 Live Terminal Test Execution Proof (16/16 Passed)](#-live-terminal-test-execution-proof-1616-passed)
    * [📊 Observed Verification Metrics Table](#observed-verification-metrics-100-deterministic-pass-rate)
    * [⚡ 60-Second Terminal Commands for Judges](#-60-second-terminal-verification-suite-for-judges)
11. [🚀 Quickstart & Local Setup](#-quickstart--local-setup)
12. [🛠️ Production Tech Stack](#-production-tech-stack)
13. [📄 Truth in Engineering & Academic Disclosures](#-truth-in-engineering--academic-disclosures)
14. [📜 License & Author](#-license--author)

---

## ⚡ 60-Second Fast-Track for Hackathon Judges

> 💡 **THE CORE INNOVATION**: Most AI agent hackathon entries build a chatbot that calls `paypal.create_order()` and immediately captures corporate funds upon receiving supplier text. In heavy industry, energy, and mission-critical supply chains, **un-gated AI spending is unacceptable and dangerous.**
>
> **KinetixRAG** introduces an enterprise agentic commerce primitive: **"No Evidence, No Capture"**, powered by **PayPal Orders v2 Two-Phase Settlement (`intent: AUTHORIZE` + evidence-gated delayed capture)**:
>
> 1. **Predictive Anomaly**: Real-time vibration exceeds ISO 10816 Zone C limits ($> 4.50\text{ mm/s}$ RMS), triggering autonomous quote evaluation.
> 2. **Grounded GraphRAG**: Neo4j multi-hop traversal retrieves OEM part numbers (`SKF-22210-E-C3`) and Standard Operating Procedures (`PROC-001`).
> 3. **Deterministic Spending Mandate**: The winning quote ($450.00 USD) complies with a strict $500.00 policy cap and 24h SLA.
> 4. **PayPal Authorization Hold**: Buyer approves order in PayPal Sandbox. Funds are authorized (`intent: AUTHORIZE`).
> 5. **Evidence Gate**: Any premature capture attempt is rejected with **HTTP 403 Forbidden (`NO_EVIDENCE_NO_CAPTURE`)**.
> 6. **Dual-Control Settlement**: Capture unlocks **only** after post-repair measurement ($\le 4.50\text{ mm/s}$), SHA-256 report verification, and separate supervisor sign-off are verified.
> 7. **Merkle Sealing & ERP Clearing**: An $O(\log N)$ binary Merkle tree seals the audit chain, and confirmed capture syncs to Google Sheets GL 2100 clearing.

### 📌 Live Cloud Links for Evaluators
* 🌐 **Live Web Application**: [https://paypal-pink.vercel.app](https://paypal-pink.vercel.app)
* 🛒 **Live Procurement Console**: [https://paypal-pink.vercel.app/procurement](https://paypal-pink.vercel.app/procurement)
* 📡 **Live Vibration Sensor Cockpit**: [https://paypal-pink.vercel.app/predictive-watch](https://paypal-pink.vercel.app/predictive-watch)
* 📲 **Live Mobile Sensor Transmitter**: [https://paypal-pink.vercel.app/sensor](https://paypal-pink.vercel.app/sensor)
* 📚 **Interactive FastAPI Swagger Docs**: [https://paypal-y2jk.onrender.com/docs](https://paypal-y2jk.onrender.com/docs)
* 🎬 **3-Minute Video Presentation Script**: [`docs/JUDGE_VIDEO_SCRIPT_3_MIN.md`](./docs/JUDGE_VIDEO_SCRIPT_3_MIN.md)

---

## 🚨 Why KinetixRAG Exists: The Reality in Numbers

Large language models are increasingly granted corporate card access and autonomous procurement authority. But when applied to mission-critical infrastructure, unconstrained autonomous spending exposes enterprises to massive financial and operational hazards:

<div align="center">

### 1. Global Industrial Outage Benchmark: Siemens Senseye ($1.5 Trillion / Year)
<img src="./docs/screenshots/evidence/siemens_downtime_cost.png" alt="Siemens Senseye Downtime Report" width="850" style="border: 1px solid #334155; border-radius: 8px; margin: 10px 0;" />
<p align="center">
  <b>Siemens Senseye Machine Health Benchmark:</b> Unplanned downtime costs Fortune Global 500 industrial leaders over <b>$1.5 Trillion annually</b> (11% of corporate turnover), with hourly failure costs scaling from $39,000 in FMCG to over <b>$2,000,000+ per hour</b> in automotive manufacturing.<br/>
  🔗 <a href="https://blog.siemens.com/2023/04/the-true-cost-of-downtime/" target="_blank"><b>Verify Official Report: Siemens True Cost of Downtime ($1.5T Benchmark)</b></a>
</p>

### 2. The Real Hourly Cost of Factory Downtime ($260,000 / Hour)
<img src="./docs/screenshots/evidence/reliable_downtime_hourly.png" alt="Reliable Magazine Downtime Hourly Benchmark" width="850" style="border: 1px solid #334155; border-radius: 8px; margin: 10px 0;" />
<p align="center">
  <b>Aberdeen Research & Reliable Plant Analysis:</b> Downtime across manufacturing sectors averages <b>$260,000 per hour</b> and climbs past <b>$2.3 Million per hour</b> for automotive assembly lines—representing immediate lost production, idle crews, and emergency replacement premiums.<br/>
  🔗 <a href="https://reliamag.com/topics/articles/cost-unplanned-downtime-manufacturing" target="_blank"><b>Verify Report: Reliable Magazine — The True Cost of Unplanned Downtime in Manufacturing</b></a>
</p>

### 3. Financial Liability & Risk of Autonomous AI Agents (JPMorgan Warning)
<img src="./docs/screenshots/evidence/jamie_dimon_ai_agent_risk.png" alt="Jamie Dimon Banking Dive AI Agent Risk" width="850" style="border: 1px solid #334155; border-radius: 8px; margin: 10px 0;" />
<p align="center">
  <b>Banking Dive & Financial Leadership Warning:</b> Autonomous AI agents cannot be granted unconstrained disbursement authority without human-in-the-loop boundaries and cryptographic lineage. JPMorgan CEO Jamie Dimon warns of an immediate <i>'liability transfer'</i> when external AI agents access banking and payment systems.<br/>
  🔗 <a href="https://www.bankingdive.com/news/jpmorgan-dimon-ai-agents-bank-customers-liability-transfer/832870/" target="_blank"><b>Verify Article: Banking Dive — Dimon Warns of 'Liability Transfer' With AI</b></a>
</p>

### 4. Critical Supply Chain Spoilage & Vaccine Loss ($35 Billion / Year)
<img src="./docs/screenshots/evidence/freightwaves_cold_chain_spoilage.png" alt="FreightWaves Cold Chain Breakdown Report" width="850" style="border: 1px solid #334155; border-radius: 8px; margin: 10px 0;" />
<p align="center">
  <b>FreightWaves & WHO Supply Chain Report:</b> Over <b>$35 Billion</b> in pharmaceutical products and nearly <b>25% of all global vaccines</b> are degraded before reaching destination due to transit temperature excursions and delayed refrigeration repairs.<br/>
  🔗 <a href="https://www.freightwaves.com/news/35-billion-saved-the-digital-shift-in-pharma-logistics" target="_blank"><b>Verify Report: FreightWaves — The Digital Shift in Pharma Cold Chain Logistics</b></a> | <a href="https://www.freightwaves.com/news/temperature-incursions-into-cold-storage-containers-cause-massive-food-waste" target="_blank">Cold Storage Temperature Incursions Study</a>
</p>

</div>

### The Failure of Conventional Agentic Commerce
1. **Hallucinated Spending**: LLMs optimize for persuasive responses, not mathematical budget constraints. Without deterministic policy engines, agents exceed budgets and select unvetted vendors.
2. **Pre-Payment Contractor Fraud**: When an AI executes single-phase capture upfront, dishonest suppliers receive disbursement before performing repairs or verifying equipment operation.
3. **Audit Trail Blind Spots**: Enterprise compliance mandates non-repudiation. When an AI orders repairs, auditors demand verifiable cryptographic proof tying the physical sensor anomaly to the final payment capture ID.

---

## 👥 Who Faces This Problem?

| Stakeholder Persona | The Daily Pain Point | How KinetixRAG Solves It |
| :--- | :--- | :--- |
| **Plant Reliability Engineers** | Trapped in reactive firefighting; manual vibration analysis takes hours while critical pumps degrade toward catastrophic seizure. | Automated ISO 10816 anomaly evaluation and multi-hop Neo4j GraphRAG attribution identify root cause and draft emergency work orders in seconds. |
| **Corporate Procurement Directors** | Terrified of rogue agent spending, budget overruns, and payments disbursed for unverified contractor work. | Hard-coded spending policy caps ($500.00 USD), allowlisted vendor checks, and **HTTP 403 capture gating** block payment until physical completion is proven. |
| **Enterprise AI Developers** | Lack a secure financial primitive to grant AI agents economic autonomy without exposing the enterprise to unlimited liability. | PayPal Orders v2 two-phase authorization holds funds securely for up to 29 days without capturing, creating a risk-free agentic procurement lifecycle. |

---

## 🔄 Before vs. After: Architectural Paradigm Shift

| Evaluation Dimension | Conventional AI Chatbot Procurement | KinetixRAG Evidence-Gated Agentic Commerce |
| :--- | :--- | :--- |
| **Payment Flow** | Single-Phase immediate card capture on order creation. | **Two-Phase Settlement**: `intent: AUTHORIZE` hold first; delayed capture only after verified work. |
| **Capture Control** | LLM decides when to disburse funds based on chat prompt. | **Deterministic Evidence Gate**: Server rejects capture with **HTTP 403** until evidence is validated. |
| **Budget Enforcement** | Soft system prompts ("Please don't spend over $500"). | **Hard Invariant Engine**: Code-level decimal math validates budget caps, SLAs, and allowlists. |
| **Diagnostic Grounding** | Unanchored LLM hallucination of maintenance steps. | **Neo4j Multi-Hop GraphRAG**: Formal entity traversal linking assets, defect frequencies, and SOPs. |
| **Work Verification** | Self-reported contractor confirmation text. | **Cryptographic Report Validation**: SHA-256 digest check + sensor verification + supervisor dual control. |
| **Separation of Duties** | Single user or agent initiates and authorizes payment. | **Strict RBAC Separation**: Requester cannot approve own order; supervisor authentication required. |
| **Audit Trail** | Ephemeral application logs prone to database mutation. | **Binary Merkle Tree ($O(\log N)$)**: Tamper-evident root hashes every stage from sensor to capture ID. |
| **Ledger Reconciliation**| Manual accounting entry after invoice receipt. | **Live ERP Synchronization**: Instant post to Google Sheets GL 2100 clearing upon capture confirmation. |

---

## ⚙️ Core Technical Capabilities

### 1. Deterministic Spending Mandate Engine
* **Policy Invariants**: Fixed $500.00 USD transaction cap, maximum 48-hour SLA response window, and allowlisted vendor validation.
* **Separation from LLM**: Policy rules are evaluated using deterministic server-side logic in Python/Pydantic, guaranteeing that model hallucinations cannot bypass corporate spending thresholds.

### 2. PayPal Orders v2 Two-Phase Settlement
* **Authorization Hold**: Orders are created with `intent: AUTHORIZE`. Buyer approves in PayPal Sandbox; funds are authorized and held securely for up to 29 days without transferring.
* **No Evidence, No Capture**: The backend intercepts any capture call. If valid completion evidence or supervisor approval is missing, the server responds with `HTTP 403 Forbidden` (`NO_EVIDENCE_NO_CAPTURE`).
* **Capture Execution**: Once all gates pass, `POST /v2/payments/authorizations/{auth_id}/capture` executes the final charge.

### 3. Multi-Source Predictive Telemetry Cockpit
* **NASA IMS Bearing Benchmark**: Replays empirical 20 kHz accelerometry from the NASA Prognostics Center of Excellence run-to-failure experiments (164-hour progression).
* **Live Smartphone MEMS Transmitter**: Connects real smartphone accelerometers (`window.DeviceMotionEvent`) via a live Neon Cloud bridge. When the phone is shaken, vibration RMS spikes, latches an ISO 10816 Zone C alarm, and displays an autonomous procurement draft.
* **Harmonic Synthesizer**: Interactive rotor unbalance and RPM tuning generating real-time 3-axis oscilloscope waveforms.

### 4. Hybrid GraphRAG Multi-Hop Knowledge Traversal
* **Knowledge Graph Schema**: Neo4j graph modeling Equipment (`P-101A`), Components (`SKF-22210-E-C3`), Failure Modes (`FE-001 Outer Race Spalling`), and SOPs (`PROC-001 Laser Alignment`).
* **Live Attribution**: Dynamically resolves ISO 10816-3 severity tables and matches the exact OEM replacement part number directly to candidate supplier RFQs.

### 5. Cryptographic Merkle Audit Lineage
* **Tamper-Evident Hashing**: Generates SHA-256 digests for each stage: Telemetry Anomaly $\rightarrow$ RFQ Quote $\rightarrow$ PayPal Authorization ID $\rightarrow$ Evidence Digest $\rightarrow$ Supervisor Signature $\rightarrow$ Final Capture ID.
* **Binary Merkle Tree**: Constructs a binary tree with $O(\log N)$ depth, sealing the root hash for regulatory audit defense.

---

## 🏛️ System Architecture & Deep Blueprints Navigation

### High-Level Architectural Flow

```mermaid
flowchart TD
    subgraph S1["📡 1. PHYSICAL IOT & SENSORS"]
        NASA["NASA IMS Bearing Dataset<br/>20 kHz Empirical Replay"]
        MEMS["Mobile Device MEMS Sensor<br/>HTML5 DeviceMotionEvent"]
        ISO["ISO 10816 Severity Trip<br/>Zone C/D > 4.50 mm/s RMS"]
        NASA --> ISO
        MEMS --> ISO
    end

    subgraph S2["🧠 2. KNOWLEDGE & AI ORCHESTRATION"]
        GraphRAG["Neo4j Hybrid GraphRAG<br/>36 Nodes • OEM Specs • SOPs"]
        LLM["Llama 3.3 70B & Gemini 2.0<br/>Root-Cause & Quote Reasoning"]
        Mandate["Spending Mandate Engine<br/>Deterministic $500 Cap • 24h SLA"]
        ISO --> GraphRAG
        GraphRAG --> LLM
        LLM --> Mandate
    end

    subgraph S3["💳 3. PAYPAL TWO-PHASE ESCROW"]
        Hold["PayPal Orders v2 Two-Phase Hold<br/>intent: AUTHORIZE • $450 Held in Escrow"]
        EarlyTrap{"Premature Capture Attempt?"}
        Reject["⛔ HTTP 403 Forbidden<br/>NO_EVIDENCE_NO_CAPTURE"]
        Mandate --> Hold
        Hold --> EarlyTrap
        EarlyTrap -- "No Evidence / Rogue AI" --> Reject
    end

    subgraph S4["🛡️ 4. DUAL-CONTROL EVIDENCE GATE"]
        Tech["Technician Post-Repair Evidence<br/>Vibration Dropped to Zone A < 2.30 mm/s"]
        Supervisor["Dual-Control Supervisor Sign-Off<br/>Independent Human-in-the-Loop"]
        Merkle["Binary Merkle Tree Audit Root<br/>O(log N) Cryptographic Lineage"]
        Tech --> Supervisor
        Supervisor --> Merkle
    end

    subgraph S5["🏛️ 5. SETTLED CAPTURE & ERP CLEARING"]
        Capture["PayPal Capture Settled<br/>POST /v2/payments/authorizations/{id}/capture"]
        Sheets["Live Google Sheets ERP Ledger<br/>GL 2100-PAYPAL-CLEARING Entry"]
        ERP["SAP S/4HANA & IBM Maximo<br/>PM01 & OSLC Work Order Closure"]
        Merkle --> Capture
        EarlyTrap -- "Verified Physical Evidence" --> Capture
        Capture --> Sheets
        Capture --> ERP
    end

    classDef physical fill:#091e3a,stroke:#38bdf8,stroke-width:2px,color:#f8fafc;
    classDef intelligence fill:#1e1035,stroke:#c084fc,stroke-width:2px,color:#f8fafc;
    classDef escrow fill:#002244,stroke:#0070ba,stroke-width:2px,color:#f8fafc;
    classDef verification fill:#3b0712,stroke:#f43f5e,stroke-width:2px,color:#f8fafc;
    classDef settlement fill:#062817,stroke:#22c55e,stroke-width:2px,color:#f8fafc;

    class NASA,MEMS,ISO physical;
    class GraphRAG,LLM,Mandate intelligence;
    class Hold,EarlyTrap,Reject escrow;
    class Tech,Supervisor,Merkle verification;
    class Capture,Sheets,ERP settlement;
```

### Deep Architecture Blueprints Index
Detailed architectural specifications, Mermaid sequence diagrams, state machines, and data topologies are maintained in **[`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md)**:

| Deep Blueprint Topic | Target Specification Link in `docs/ARCHITECTURE.md` | Primary Focus |
| :--- | :--- | :--- |
| **End-to-End System Architecture** | [`docs/ARCHITECTURE.md#1-end-to-end-system-architecture`](./docs/ARCHITECTURE.md#1-end-to-end-system-architecture) | Ingestion-to-settlement pipeline and subsystem interactions |
| **PayPal Payment Lifecycle** | [`docs/ARCHITECTURE.md#2-paypal-payment-lifecycle-architecture`](./docs/ARCHITECTURE.md#2-paypal-payment-lifecycle-architecture) | Sequence diagram of 2-phase authorization hold & evidence gating |
| **Multi-Source Telemetry Pipeline** | [`docs/ARCHITECTURE.md#3-multi-source-predictive-telemetry-architecture`](./docs/ARCHITECTURE.md#3-multi-source-predictive-telemetry-architecture) | NASA IMS replay, mobile MEMS transmitter, and latching alarms |
| **Hybrid GraphRAG Traversal** | [`docs/ARCHITECTURE.md#4-hybrid-graphrag-knowledge-architecture`](./docs/ARCHITECTURE.md#4-hybrid-graphrag-knowledge-architecture) | Cypher query paths, component attribution, and regulatory citations |
| **Evidence Gate & Merkle Lineage** | [`docs/ARCHITECTURE.md#5-dual-control-evidence--merkle-lineage-architecture`](./docs/ARCHITECTURE.md#5-dual-control-evidence--merkle-lineage-architecture) | SHA-256 leaf hashing and binary Merkle tree root calculation |
| **ERP Clearing & External Ledgers** | [`docs/ARCHITECTURE.md#6-erp-clearing--external-ledger-architecture`](./docs/ARCHITECTURE.md#6-erp-clearing--external-ledger-architecture) | Google Sheets GL 2100 clearing and enterprise connector safeguards |

---

## 🛡️ Security, Authorization & Privacy Architecture

KinetixRAG implements defense-in-depth principles across authentication, payment lifecycle, and audit persistence:

1. **Strict 4-Tier Role-Based Access Control (RBAC)**:
   * `PlantOperator`: Monitors telemetry and views equipment status.
   * `ProcurementAgent`: Evaluates RFQs and initiates PayPal authorization holds.
   * `Supervisor`: Required for critical asset dual-control approval (`LANE_B`).
   * `VendorTechnician`: Submits field repair reports and post-repair measurements.
2. **Separation of Duties Invariant**:
   * The authenticated user who created or authorized an order **cannot** approve their own work order. Attempted self-approval returns `HTTP 403 Forbidden` (`SEPARATION_OF_DUTIES_VIOLATION`).
3. **Caller-Bound Technician Identity**:
   * In `backend/app/api/paypal.py`, `submission.technician_id` is automatically bound to the caller's verified `current_user.user_id`. Any client-supplied technician identifier is overwritten, preventing audit trail spoofing.
4. **Webhook Signature Verification**:
   * Production PayPal webhooks verify cryptographic signatures against registered webhook IDs (`PAYPAL_WEBHOOK_ID`). Unverified simulation payloads cannot mutate order state.
5. **Secret Leak Prevention**:
   * Automated pre-commit scans (`tests/test_secret_scan.py`) verify that zero live private keys, JWT secrets, or high-entropy tokens exist in repository source files.
6. **Detailed Threat Model**:
   * Complete STRIDE security analysis is documented in **[`docs/THREAT_MODEL_STRIDE.md`](./docs/THREAT_MODEL_STRIDE.md)**.

---

## 📋 Detailed Execution Sequence

```mermaid
stateDiagram-v2
    [*] --> TelemetryExcursion: Vibration > 4.50 mm/s (ISO 10816 Zone C)
    TelemetryExcursion --> GraphRAGDiagnosis: Traversed Neo4j Knowledge Graph
    GraphRAGDiagnosis --> MandateEvaluation: Evaluate Supplier Quotes against $500 Cap
    MandateEvaluation --> PayPalOrderCreated: POST /v2/checkout/orders (intent=AUTHORIZE)
    PayPalOrderCreated --> BuyerApproved: Buyer Approves in PayPal Sandbox
    BuyerApproved --> PaymentAuthorized: POST /v2/checkout/orders/{id}/authorize
    
    state EvidenceGate {
        PaymentAuthorized --> PrematureCaptureRejected: Attempt Capture (No Evidence)
        PrematureCaptureRejected --> PaymentAuthorized: HTTP 403 Forbidden (Blocked)
        PaymentAuthorized --> EvidenceSubmitted: Upload Report & Measurement (<= 4.5 mm/s)
        EvidenceSubmitted --> SupervisorApproved: Separately Authenticated Supervisor Approves
    }
    
    SupervisorApproved --> CaptureExecuted: POST /v2/payments/authorizations/{id}/capture
    CaptureExecuted --> MerkleSealed: Calculate Binary Merkle Tree Root
    MerkleSealed --> ERPSynchronized: Post to Google Sheets GL 2100 Ledger
    ERPSynchronized --> [*]
```

1. **Telemetry Anomaly**: Equipment `P-101A` vibration velocity RMS exceeds $4.50\text{ mm/s}$ limit (NASA IMS replay or live smartphone shake).
2. **GraphRAG Investigation**: Multi-agent swarm traverses Neo4j entities, identifying outer race spalling (BPFO: 148.2 Hz) and retrieving SOP `PROC-001`.
3. **RFQ Quote Evaluation**: Policy engine evaluates candidate supplier quotes. Motion Industries (`Q-2026-001`, $450.00 USD, 24h SLA) satisfies the $500.00 mandate cap.
4. **PayPal Order Creation**: System creates PayPal Orders v2 record with `intent: AUTHORIZE`.
5. **Buyer Approval**: Requester logs into PayPal Sandbox buyer checkout and grants authorization.
6. **Authorization Hold**: Order is authorized via `/api/paypal/orders/{id}/authorize`. Funds are reserved in Sandbox.
7. **Early Capture Rejection**: Premature capture call without completion evidence is blocked with `HTTP 403 Forbidden`.
8. **Evidence Submission**: Technician uploads service report and verifies post-repair vibration ($1.25\text{ mm/s}$). System binds cryptographic SHA-256 digest.
9. **Supervisor Dual-Control**: Authenticated supervisor signs off on Work Order `WO-2026-IMS-001`.
10. **Capture & Merkle Sealing**: Capture executes against PayPal Sandbox. Binary Merkle tree root seals the audit lineage, and details sync to Google Sheets ERP clearing.

---

## 📸 Live Platform Screenshots

<div align="center">

### 1. Command Center & Operational Cockpit
<img src="./docs/screenshots/platform/01_homepage_command_center.png" alt="Command Center & Operational Cockpit" width="900" style="border: 1px solid #334155; border-radius: 8px; margin: 12px 0;" />
<p align="center"><i>Operational Command Center showing real-time fleet health, ISO 10816 excursion alerts, and active PayPal agentic commerce status.</i></p>

### 2. Multi-Source Vibration Cockpit (Live MEMS & NASA IMS Replay)
<img src="./docs/screenshots/platform/06_predictive_watch_graphsage.png" alt="Predictive Watch Cockpit" width="900" style="border: 1px solid #334155; border-radius: 8px; margin: 12px 0;" />
<p align="center"><i>3-Axis oscilloscope displaying empirical 20 kHz NASA IMS run-to-failure vibration signals and live smartphone MEMS transmitter telemetry.</i></p>

### 3. PayPal Procurement Console & Spending Mandates
<img src="./docs/screenshots/platform/02_procurement_console_initial.png" alt="Procurement Console Initial State" width="900" style="border: 1px solid #334155; border-radius: 8px; margin: 12px 0;" />
<p align="center"><i>Deterministic Spending Mandate evaluation: Motion Industries ($450.00) selected against $500.00 cap with live GraphRAG procedural citations.</i></p>

### 4. PayPal Sandbox Authorization & Buyer Approval
<img src="./docs/screenshots/platform/03_paypal_authorization_gate.png" alt="PayPal Authorization Hold" width="900" style="border: 1px solid #334155; border-radius: 8px; margin: 12px 0;" />
<p align="center"><i>Phase 1 complete: PayPal Sandbox order authorized with 29-day authorization hold before contractor dispatch.</i></p>

### 5. HTTP 403 Early Capture Blocked (Evidence Gate Demonstration)
<img src="./docs/screenshots/platform/05_http_403_early_capture_blocked.png" alt="HTTP 403 Early Capture Blocked" width="900" style="border: 2px solid #ef4444; border-radius: 8px; margin: 12px 0;" />
<p align="center"><i>Deterministic safety boundary: Backend blocks premature capture with HTTP 403 Forbidden when completion evidence is missing.</i></p>

### 6. Settled Capture & Cryptographic Merkle Lineage
<img src="./docs/screenshots/platform/04_settled_receipt_merkle_lineage.png" alt="Settled Receipt & Merkle Lineage" width="900" style="border: 1px solid #10b981; border-radius: 8px; margin: 12px 0;" />
<p align="center"><i>Phase 3 finalized: Confirmed PayPal capture ID, binary Merkle tree audit root, and Google Sheets GL 2100 accounting sync.</i></p>

### 7. Hybrid GraphRAG Multi-Hop Investigation & Citations
<img src="./docs/screenshots/platform/07_graphrag_investigation.png" alt="GraphRAG Investigation & Citations" width="900" style="border: 1px solid #a855f7; border-radius: 8px; margin: 12px 0;" />
<p align="center"><i>Multi-agent GraphRAG reasoning traversing Neo4j asset-component-procedure graphs with verifiable OEM manual citations.</i></p>

### 8. Programmatic Spending Mandates & Enterprise Governance
<img src="./docs/screenshots/platform/08_spending_mandates_policy.png" alt="Spending Mandates & Policy Configuration" width="900" style="border: 1px solid #38bdf8; border-radius: 8px; margin: 12px 0;" />
<p align="center"><i>Deterministic spending mandate policy controls: $500 hard cap, USD currency gate, allowlisted vendors, and Lane B dual-control isolation.</i></p>

</div>

---

## 🧪 Comprehensive Test Suite & Terminal Verification

### 💻 Live Terminal Test Execution Proof (16/16 Passed)

<div align="center">
  <img src="./docs/screenshots/terminal_verification.png" alt="Live Terminal Verification: 16 Tests Passed in 8.58s" width="900" style="border: 1px solid #38bdf8; border-radius: 8px; margin: 12px 0; box-shadow: 0 4px 20px rgba(0,0,0,0.4);" />
  <p align="center">
    <b>Live Terminal Proof:</b> <code>py -3.12 -m pytest tests/test_secret_scan.py tests/test_spending_mandate_v2.py -v</code><br/>
    <i>Exhaustive verification of Pre-submission Secret Scanning (8/8) and Deterministic Spending Mandate Policy Gates (8/8) executing with 100% pass rate in 8.58 seconds.</i>
  </p>
</div>

#### What This Terminal Proof Mathematically Verifies:
1. **Zero Secret Leaks (`test_secret_scan.py` — 8 Passed)**:
   - Scans all git-tracked repository files for private keys, high-entropy tokens, and passwords.
   - Verifies `.env` and secret files are completely untracked and strictly git-ignored.
   - Ensures no production PayPal credentials or secret keys can ever leak to public version control.
2. **Deterministic Spending Mandates (`test_spending_mandate_v2.py` — 8 Passed)**:
   - **Lane A ($500 Cap)**: Proves autonomous approval functions strictly under $500 with compliant 24h SLA.
   - **Lane B Escalation**: Proves mission-critical assets automatically escalate to dual-control supervisor sign-off.
   - **Security Invariants**: Verifies immediate programmatic rejection of nonpositive amounts, unapproved vendors, currency mismatches, and prompt injection attacks targeting procurement reasoning.

---

### Observed Verification Metrics (100% Deterministic Pass Rate)

| Test Layer | Test Runner | Files | Tests | Result | Verification Scope |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Frontend UI & Components** | **Vitest 4.x** | 19 | **82** | **PASS ✅** | Persona switcher, evidence drawers, QR decode, stepper, safety boundaries |
| **Targeted Backend Security** | **Pytest 9.x** | 7 | **40** | **PASS ✅** | Auth RBAC, separation of duties, header spoofing prevention, ledger export |
| **PayPal Provider Hardening** | **Pytest 9.x** | 1 | **11** | **PASS ✅** | Neutralized legacy adapter, invoice rejection, zero fake receipts |
| **Webhook Identity Hardening** | **Pytest 9.x** | 1 | **9** | **PASS ✅** | Signature verification, caller identity binding, simulation isolation |
| **Secret Leak Scanner** | **Pytest 9.x** | 1 | **8** | **PASS ✅** | Zero high-entropy keys, private tokens, or credential leaks in repo |
| **Production Build** | **Turbopack** | 17 routes | — | **PASS ✅** | Zero TypeScript errors, clean static page generation across all routes |
| **TOTAL VERIFIED CHECKS** | | | **150+** | **100% PASS** | **Zero failures, zero regressions, 100% deterministic test execution** |

---

### ⚡ 60-Second Terminal Verification Suite for Judges

Run these verified commands inside your terminal to test the core security, payment, and evidence boundaries in under 60 seconds:

```bash
# 1. Verify Zero Secret Leaks & Spending Mandates Policy Engine (16 Passing Tests in 8.5s)
py -3.12 -m pytest tests/test_secret_scan.py tests/test_spending_mandate_v2.py -v

# 2. Verify PayPal Provider Hardening (Rejects legacy fake settlement defect)
py -3.12 -m pytest tests/test_paypal_provider.py -v

# 3. Verify Webhook Hardening & Technician Identity Binding
py -3.12 -m pytest tests/test_paypal_webhook_hardening.py -v

# 4. Verify RBAC, Separation of Duties & Ledger Export Safety
py -3.12 -m pytest tests/backend/test_auth.py tests/backend/test_auth_elevation_hardening.py tests/test_ledger_export_hardening.py -v

# 5. Verify Frontend Component & Evidence Gate Test Suite (82 Passing Vitest Specs)
npm --prefix frontend test -- --run
```
> *Note for Windows evaluators: If multiple Python versions are installed, run using `py -3.12` as shown above to target Python 3.12.*

---

## 🚀 Quickstart & Local Setup

### Prerequisites
* **Python 3.11 or 3.12**
* **Node.js 20+ & npm**
* Active PayPal Sandbox Developer Account ([developer.paypal.com](https://developer.paypal.com))

---

### Step 1: Clone Repository & Configure Environment

```bash
git clone https://github.com/Niss54/paypal.git
cd paypal

# Create and activate Python virtual environment
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt
```

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Configure your PayPal Sandbox API credentials in `.env`:
```env
PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=your_paypal_sandbox_client_id
PAYPAL_CLIENT_SECRET=your_paypal_sandbox_client_secret
PAYPAL_WEBHOOK_ID=your_optional_webhook_id
```

---

### Step 2: Launch FastAPI Backend Server

```bash
python -m uvicorn backend.app.main:app --port 8000 --reload
```
* **Local Backend API**: `http://localhost:8000`
* **Interactive Swagger Documentation**: `http://localhost:8000/docs`

---

### Step 3: Launch Next.js Frontend Console

```bash
# In a separate terminal
cd frontend
npm install
npm run dev
```
* **Local Web Application**: `http://localhost:3000`
* **Procurement Settlement Cockpit**: `http://localhost:3000/procurement`
* **Predictive Sensor Cockpit**: `http://localhost:3000/predictive-watch`

---

## 🛠️ Production Tech Stack

| Layer | Technology | Version | Architectural Rationale |
| :--- | :--- | :--- | :--- |
| **Payment Gateway** | **PayPal Orders v2 REST API** | v2 (Sandbox) | Two-phase authorization hold (`intent: AUTHORIZE`) enabling up to 29-day funds reservation prior to physical repair validation. |
| **Frontend Framework** | **Next.js** | **16.2.11** | Turbopack App Router, React 19 Server Components, zero hydration drift, responsive dark-mode cockpit. |
| **Styling & UI Components**| **Tailwind CSS + shadcn/ui** | v3.4 / Radix UI | Accessible enterprise theme matching SCADA / industrial plant control consoles. |
| **Backend Framework** | **FastAPI** | **0.115.8** | High-performance async Python ASGI framework, strict Pydantic v2 schemas, typed dependency injection. |
| **Cloud Database** | **Neon Serverless Postgres** | PostgreSQL 16 | Serverless connection pooling, HTTP-based query execution, and live mobile telemetry streaming. |
| **Knowledge Graph** | **Neo4j Enterprise** | 5.x / Cypher | Knowledge graph storing equipment topologies, component BOMs, failure modes, and SOPs. |
| **Vector Database** | **Qdrant** | 1.x / REST | High-performance vector embeddings for hybrid dense-sparse RRF retrieval of maintenance procedures. |
| **Cryptographic Ledger** | **Binary Merkle Tree** | Custom SHA-256 | $O(\log_2 N)$ logarithmic tree depth providing mathematical proof of audit lineage. |
| **Testing Harness** | **Pytest + Vitest** | 9.x / 4.x | 68 core backend tests + 82 frontend component tests with 100% deterministic execution. |

---

## 📄 Truth in Engineering & Academic Disclosures

To preserve absolute academic, professional, and engineering integrity:

| Data Element | Type | Provenance / Source | Disclosure Boundary |
| :--- | :---: | :--- | :--- |
| **Vibration Telemetry (Replay)** | **Empirical Benchmark** | NASA IMS Bearing Run-to-Failure Accelerometry (University of Cincinnati IMS / NASA Prognostics Center of Excellence). | Real physical run-to-failure accelerometry sampled at 20 kHz from historical test rigs. |
| **Mobile Sensor Telemetry** | **Live Physical MEMS** | Smartphone 3-axis accelerometer (`window.DeviceMotionEvent`). | Measures linear acceleration ($m/s^2$) translated to a calibrated anomaly index. Not an ISO-certified industrial transducer. |
| **Asset Diagnostics** | **Empirical Standard** | ISO 10816-3 Mechanical Vibration Severity Standards + Neo4j GraphRAG. | Grounded in standard engineering failure thresholds ($4.50\text{ mm/s}$ limit). |
| **Vendor RFQ Quotes** | **Synthetic Fixture** | 3 candidate vendor quotes created for demonstration. | Labeled in UI and API with `[SYNTHETIC DEMO QUOTE]`. |
| **Vendor Service Report** | **Synthetic Fixture** | Service report fixture demonstrating post-repair re-inspection. | Labeled `[SYNTHETIC DEMO REPORT]`. |
| **PayPal API Calls** | **Live Sandbox** | PayPal Orders v2 REST API running against official PayPal Sandbox (`api-m.sandbox.paypal.com`). | Real PayPal OAuth2 client credentials, order creation, authorization, and capture execution. |

---

## 📜 License & Author

This project is licensed under the **MIT License** — see the [LICENSE](./LICENSE) file for details.  

**Lead Architect & Developer**: Nishant Maurya ([@Niss54](https://github.com/Niss54))  
**Competition**: PayPal AI Hackathon 2026 (Devpost)  
**Submission Date**: November 12, 2026 (12th Nov 2026)  
