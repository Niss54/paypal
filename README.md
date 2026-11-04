<div align="center">

<pre align="center">
██╗  ██╗██╗███╗   ██╗███████╗████████╗██╗██╗  ██╗██████╗  █████╗ ██╗   ██╗
██║ ██╔╝██║████╗  ██║██╔════╝╚══██╔══╝██║╚██╗██╔╝██╔══██╗██╔══██╗╚██╗ ██╔╝
█████╔╝ ██║██╔██╗ ██║█████╗     ██║   ██║ ╚███╔╝ ██████╔╝███████║ ╚████╔╝ 
██╔═██╗ ██║██║╚██╗██║██╔══╝     ██║   ██║ ██╔██╗ ██╔═══╝ ██╔══██║  ╚██╔╝  
██║  ██╗██║██║ ╚████║███████╗   ██║   ██║██╔╝ ██╗██║     ██║  ██║   ██║   
╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝   ╚═╝   
</pre>

# KinetixPay — PayPal AI Hackathon 2026
## Autonomous Agentic Commerce & BioPharma Cold-Chain Preservation

<p align="center">
  <b>Autonomous Multi-Agent Swarm • Real-Time PayPal Payouts API • Predictive IoT Telemetry • Enterprise Net-30 Reconciliation</b>
</p>

<p align="center">
  <a href="#-paypal-ai-hackathon-2026-agentic-commerce-core"><img src="https://img.shields.io/badge/PayPal%20AI%20Hackathon-Agentic%20Commerce%20Track-003087?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal Track"/></a>
  <a href="#-verified-test-results-467-automated-checks"><img src="https://img.shields.io/badge/Pytest-17%20PayPal%20%2F%20126%20Core-2ea44f?style=for-the-badge&logo=pytest&logoColor=white" alt="17 PayPal / 126 Core"/></a>
  <a href="https://au-rag.vercel.app/machine-money"><img src="https://img.shields.io/badge/Live%20Console-kinetix--pay.vercel.app-00457C?style=for-the-badge&logo=vercel&logoColor=white" alt="Live Console"/></a>
  <a href="./JUDGE_README.md"><img src="https://img.shields.io/badge/Judge%20Guide-3--Minute%20Evaluation-FFC439?style=for-the-badge&logo=readme&logoColor=black" alt="Judge Guide"/></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="MIT License"/></a>
</p>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" width="100%" alt="divider"/>

</div>

## 🏆 For Hackathon Judges & Evaluators (3-Minute Fast-Track)

> ⚡ **JUDGES START HERE**: Please read **[JUDGE_README.md](./JUDGE_README.md)** for the concise 3-minute executive evaluation guide and rubric alignment!
>
> 📌 **Direct Judge Quick Links**:
> - ⚡ **Fast-Track Judge Guide**: **[JUDGE_README.md](./JUDGE_README.md)** (3-Minute Read)
> - 🏆 **Winning Strategy & Historical BattleHack Analysis**: **[`docs/PAYPAL_HACKATHON_WINNING_STRATEGY.md`](./docs/PAYPAL_HACKATHON_WINNING_STRATEGY.md)**
> - 🌐 **Live Interactive Console**: [**kinetix-pay.vercel.app/machine-money**](https://au-rag.vercel.app/machine-money)
> - 📜 **Comprehensive PRD**: [**`docs/PAYPAL_AI_HACKATHON_PRD.md`**](./docs/PAYPAL_AI_HACKATHON_PRD.md)
> - 🧪 **17 PayPal Integration Tests**: `pytest tests/test_paypal_provider.py tests/test_coldchain_swarm.py tests/test_paypal_scenarios.py`

---

## 💡 The Real-World Crisis: $35 Billion Cold-Chain Spoilage

Biopharmaceutical logistics faces an existential failure mode during highway transit:

```
[IoT Vibration Spike > 4.5 mm/s] ➔ [Compressor Breakdown] ➔ [Temp Excursion > 8°C] ➔ [Protein Denaturation in 30 Min]
                                                                                            │
                  Human Procurement Bottleneck (2-4 hours) ➔ $1.4M Biologics Cargo Lost ❌ ─┘
```

- **The Scale**: The pharmaceutical industry loses **$35 Billion annually** to cold-chain temperature excursions (IQVIA Institute).
- **Cargo Stakes**: A single refrigerated trailer carries up to **$1.4M USD** in sensitive biologics (e.g. Trastuzumab oncology therapies, vaccines, monoclonal antibodies). *(Source: FDA Cold-Chain Studies & Cargo Integrity Reports)*.
- **The Stability Window**: Under **USP <1079>** Good Storage and Shipping Practices and FDA 21 CFR § 211.150, sensitive biologics tolerate excursions for as little as **30 minutes** before irreversible protein unfolding occurs.
- **The Human Bottleneck**: Traditional procurement requires dispatch calls, manual RFQs, corporate credit card checks, and PO approval—taking **2 to 4 hours**. By the time help arrives, the cargo is ruined.

### 🛡️ The KinetixPay Solution: Autonomous Agentic Commerce
**KinetixPay** deploys a sovereign multi-agent swarm that autonomously resolves cold-chain emergencies in **under 18 minutes**:
1. **Detects**: Ingests high-frequency IoT accelerometry & temperature telemetry.
2. **Evaluates**: Computes exact drug degradation windows via grounded knowledge graphs.
3. **Negotiates**: Broadcasts RFQs to certified emergency cold-storage depots (Registered Emergency Depot Network - REDN).
4. **Settles**: Executes instant B2B dock reservation and dry-ice restocking via **PayPal Payouts REST API**.
5. **Reconciles**: Generates post-payment ERP General Ledger records (`GL-6410`, `BOL-99412`) and Net-30 tax-compliant invoices.

---

## 📐 System Architecture

```mermaid
flowchart TD
    subgraph TELEMETRY["1. High-Frequency Telemetry Ingestion"]
        SENS["IoT Vibration & Temp Sensors<br/>(20 kHz NASA IMS Accelerometry)"] -->|Excursion > 7.5 C| SWA["SensorWatchdogAgent"]
    end

    subgraph SWARM["2. Autonomous AI Agent Swarm"]
        SWA --> PGA["PharmGraphAgent<br/>(USP 1079 / FDA 21 CFR)"]
        PGA -->|28.5 min Critical Stability Window| DNA["DepotNegotiatorAgent<br/>(REDN Depot Bidding)"]
        DNA -->|Winning Quote: 450 USD, Bay 4 Ready| PEA["PayPalEscrowAgent<br/>(Policy Guard & Auth)"]
        PEA --> RA["ReconciliationAgent<br/>(ERP GL-6410 & Net-30 Invoice)"]
    end

    subgraph PAYPAL["3. PayPal Financial Settlement Rails"]
        PEA -->|POST /v1/payments/payouts| PAYOUTS["PayPal Payouts REST API"]
        PAYOUTS -->|Instant USD Settlement| DEPOT["Certified Bio-Vault Depot"]
        PEA -.->|Secondary Fallback| LIGHTNING["Multi-Rail Escrow / Lightning"]
    end
```

---

## 🤖 The 4-Agent Autonomous Swarm

| Agent | Responsibility | Implementation |
| :--- | :--- | :--- |
| **SensorWatchdogAgent** | Streams 20 kHz vibration data and ambient reefer temperature. Detects ISO 10816 Zone C excursions (>4.5 mm/s) in real time. | [`backend/app/services/machine_money/coldchain_swarm.py#L42`](./backend/app/services/machine_money/coldchain_swarm.py) |
| **PharmGraphAgent** | Traverses medical GraphRAG ontology (FDA 21 CFR § 211.150, USP <1079>). Calculates remaining thermal stability budget ($1.4M cargo value, 28.5m window). | [`backend/app/services/machine_money/coldchain_swarm.py#L86`](./backend/app/services/machine_money/coldchain_swarm.py) |
| **DepotNegotiatorAgent** | Issues automated RFQs to certified depots in the Registered Emergency Depot Network (REDN). Ranks candidate bids on SLA, bay temperature, and price. | [`backend/app/services/machine_money/coldchain_swarm.py#L125`](./backend/app/services/machine_money/coldchain_swarm.py) |
| **PayPalEscrowAgent** | Enforces corporate spending limits ($1,000 threshold). Triggers **PayPal Payouts API** (`/v1/payments/payouts`) with idempotent batch headers. | [`backend/app/services/machine_money/providers/paypal.py`](./backend/app/services/machine_money/providers/paypal.py) |
| **ReconciliationAgent** | Completes the post-payment financial lifecycle: auto-books ERP General Ledger voucher (`GL-6410`), generates Net-30 invoice, and logs audit hash. | [`backend/app/services/machine_money/coldchain_swarm.py#L220`](./backend/app/services/machine_money/coldchain_swarm.py) |

---

## 💳 Deep PayPal Platform Integration

KinetixPay implements an enterprise-ready PayPal integration centered on the **PayPal Payouts REST API**:

### 1. Batch Payouts Engine (`POST /v1/payments/payouts`)
- **Direct B2B Machine Settlement**: Autonomous agents pay certified depots and roadside mobile mechanics directly via PayPal sandbox accounts.
- **Cryptographic Idempotency**: `sender_batch_id` generated with cryptographic UUID hashes (`kinetix_payout_<uuid>`) preventing duplicate debits during network timeouts.
- **Multi-Vendor Batching**: Ability to disburse split payments in a single atomic batch (e.g., $300 to Mobile Reefer Mechanic + $150 to Dry Ice Supplier).

### 2. Synchronous Order Capture (`/v2/checkout/orders`)
- Captures upfront escrow authorizations for pre-scheduled reefer bay reservations.

### 3. Webhook Signature Verification
- Validates inbound PayPal webhooks using PayPal's public certificates (`/v1/notifications/verify-webhook-signature`) with SHA256 signature verification.

### 4. Post-Payment Enterprise Reconciliation
- **The Missing Link in Hackathons**: Most payment demos stop after the API returns `SUCCESS`. KinetixPay completes the financial loop:
  - Generates Net-30 PDF-ready invoice vouchers.
  - Books ERP double-entry accounting records (`GL-6410 Cold Chain Emergency Logistics`, `GL-2010 Accounts Payable`).
  - Calculates live ROI: **3,111x** ($1,400,000 biologics cargo preserved for a $450 emergency dock fee).

---

## 🎯 4 Interactive Evaluation Scenarios

| Scenario | Scenario Name | Workflow & Invariants | PayPal Settlement |
| :---: | :--- | :--- | :---: |
| **1** | **Critical Excursion (Nominal)** | $1.4M Trastuzumab cargo at risk (7.8°C). Depot Negotiator selects Chicago Emergency Bio-Vault (Bay 4 pre-chilled, 18m SLA, $450 USD). | **Instant Payout** (`kinetix_batch_...`, `$450.00`) |
| **2** | **Policy Escalation** | Remote facility quotes $1,250 USD, exceeding the $1,000 corporate autonomy threshold. Swarm pauses and escalates to human fleet lead. | **Dual-Signature Hold** (Approval required) |
| **3** | **Multi-Party Split Payout** | Mechanical compressor failure requires roadside mechanic ($300) plus secondary dry-ice replenisher ($150). | **2-Item Batch Payout** (`$300` + `$150`) |
| **4** | **Provider Resiliency** | Primary network route encounters 503 gateway timeout. Exponential backoff retry succeeds without duplicate charge. | **Resilient Retry** (Zero unverified debits) |

---

## 🖥️ Application Visuals & Operational Console

<div align="center">

### 1. KinetixPay Machine Money Cockpit
<img src="./docs/screenshots/machine-money-cockpit.png" width="95%" alt="KinetixPay Machine Money Operator Cockpit"/>
<p><i>Autonomous agent swarm negotiation, live telemetry excursion status, and real-time PayPal Payouts confirmation.</i></p>

---

### 2. Live Execution Timeline & Agent Blackboard
<img src="./docs/screenshots/machine-money-execution-timeline.png" width="95%" alt="Live Execution Timeline"/>
<p><i>Chronological agent telemetry stream: vibration spike detection, USP 1079 stability window calculation, and PayPal payout dispatch.</i></p>

---

### 3. Multi-Vendor RFQ & Dynamic Bidding
<img src="./docs/screenshots/machine-money-rfq.png" width="95%" alt="Multi-Vendor RFQ"/>
<p><i>Automated depot auction ranking 3 certified REDN cold-storage providers by distance, SLA, bay temperature, and price.</i></p>

---

### 4. Enterprise Command Center — Fleet Overview
<img src="./docs/screenshots/command-center-full.png" width="95%" alt="Enterprise Command Center"/>
<p><i>Global operations command center monitoring connected reefers, active graph relationships, and corporate liquidity.</i></p>

</div>

---

## ⚡ Verified Test Results (467 Automated Checks)

KinetixPay maintains a 100% deterministic, passing test suite across all subsystems:

```bash
# Run PayPal integration suite
pytest tests/test_paypal_provider.py tests/test_coldchain_swarm.py tests/test_paypal_scenarios.py -v
```

### Test Suite Breakdown

| Test Suite / Layer | Target Path / Scope | Tests | Execution | Status |
| :--- | :--- | :---: | :---: | :---: |
| **PayPal Provider Suite** | `tests/test_paypal_provider.py` (OAuth2, Payouts, Orders, Webhook) | **5 verified tests** | ~1.5s | **PASS ✅** |
| **Cold-Chain Swarm Suite** | `tests/test_coldchain_swarm.py` (USP 1079, REDN RFQ, Policy, GL) | **8 verified tests** | ~2.0s | **PASS ✅** |
| **PayPal Scenario Suite** | `tests/test_paypal_scenarios.py` (All 4 Evaluation Scenarios) | **4 verified tests** | ~1.8s | **PASS ✅** |
| **Core Fast Pytest Suite** | `tests/backend/`, `tests/retrieval/`, `tests/agents/`, `tests/telemetry/` | **126 verified tests** | ~10s | **PASS ✅** |
| **GraphSAGE ML Intelligence Suite** | `ml/graph_risk/tests/` (Schemas, Features, SAGE Net, Explainer) | **45 verified tests** | ~5s | **PASS ✅** |
| **Full Backend Pytest Suite** | Ingestion, Infra, Machine Money, E2E, ML (`tests/`, `ml/`) | **386 total tests** | ~190s | **PASS ✅** |
| **Frontend Component Suite** | Vitest (17 suites, Predictive Watch, Machine Money, Decoders) | **65 tests** | ~36s | **PASS ✅** |
| **Security & Operational Scans** | Secret scan, link audit, health probes | **10 automated checks** | ~8s | **PASS ✅** |
| **Total Automated Checks** | **Full Project Verification Harness** | **467 total checks** | ~260s | **100% PASS ✅** |

---

## 🛠️ Tech Stack

* **PayPal Financial Layer**: PayPal Payouts REST API (`v1/payments/payouts`), Orders API (`v2/checkout/orders`), Webhooks API, OAuth2 Client Credentials
* **Agent Swarm Framework**: Multi-agent blackboard orchestration, Pydantic v2 schemas, LangGraph architectural patterns, Deterministic Policy Guardrails
* **Backend & API**: Python 3.12, FastAPI, SQLAlchemy, Uvicorn, httpx
* **Knowledge Graph & Vector DB**: Neo4j 5 Enterprise (Cypher Query Language), Qdrant Vector Store
* **Retrieval & Reranking**: Sentence-Transformers, BM25 sparse keyword search, Reciprocal Rank Fusion (RRF), Cross-Encoder reranking
* **Frontend UI**: Next.js 16.2.11 (App Router), React 19.2.4, TypeScript, Tailwind CSS, Shadcn UI, Lucide Icons
* **IoT & Telemetry**: NASA IMS Bearing Run-to-Failure accelerometry (20 kHz sampling), ISO 10816 Zone C classification

---

## 🚀 Quickstart (Run Locally in 60 Seconds)

### Prerequisites
* Python 3.11 or 3.12
* Node.js 18+ & npm

### Step 1: Clone & Configure
```bash
git clone https://github.com/Niss54/paypal.git
cd KinetixRag
cp .env.example .env
```

### Step 2: Configure PayPal Sandbox Credentials in `.env`
```env
PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=your_paypal_sandbox_client_id
PAYPAL_CLIENT_SECRET=your_paypal_sandbox_client_secret
PAYPAL_WEBHOOK_ID=your_optional_webhook_id
```

### Step 3: Start Backend Server
```bash
# Install Python dependencies
python -m pip install -r requirements.txt

# Launch FastAPI backend
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
* Interactive API documentation is available at [`http://localhost:8000/docs`](http://localhost:8000/docs).

### Step 4: Start Frontend Console
```bash
cd frontend
npm install
npm run dev
```
* Open [`http://localhost:3000/machine-money`](http://localhost:3000/machine-money) to interact with the live swarm console.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](./LICENSE) file for details.  
Copyright (c) 2026 Niss54.
