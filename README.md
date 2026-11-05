<div align="center">

<img src="./frontend/public/kr.png" alt="KinetixRAG Logo" width="140" style="margin-bottom: 12px;" />

<pre align="center">
██╗  ██╗██╗███╗   ██╗███████╗████████╗██╗██╗  ██╗██████╗  █████╗  ██████╗ 
██║ ██╔╝██║████╗  ██║██╔════╝╚══██╔══╝██║╚██╗██╔╝██╔══██╗██╔══██╗██╔════╝ 
█████╔╝ ██║██╔██╗ ██║█████╗     ██║   ██║ ╚███╔╝ ██████╔╝███████║██║  ███╗
██╔═██╗ ██║██║╚██╗██║██╔══╝     ██║   ██║ ██╔██╗ ██╔══██╗██╔══██║██║   ██║
██║  ██╗██║██║ ╚████║███████╗   ██║   ██║██╔╝ ██╗██║  ██║██║  ██║╚██████╔╝
╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ 
</pre>

# KinetixRAG — PayPal AI Hackathon 2026
## Evidence-Gated Industrial Procurement & Autonomous Spending Mandates

<p align="center">
  <b>Grounded NASA IMS Bearing Telemetry • GraphRAG Diagnostic Engine • Deterministic Spending Mandates • "No Evidence, No Capture" PayPal Orders v2 Settlement</b>
</p>

<p align="center">
  <a href="#-paypal-ai-hackathon-2026-rubric-alignment"><img src="https://img.shields.io/badge/PayPal%20AI%20Hackathon-Agentic%20Commerce%20Track-003087?style=for-the-badge&logo=paypal&logoColor=white" alt="PayPal Track"/></a>
  <a href="#-verified-test-suite-396-passing-tests"><img src="https://img.shields.io/badge/Pytest-34%20PayPal%20%2F%20396%20Total-2ea44f?style=for-the-badge&logo=pytest&logoColor=white" alt="34 PayPal / 396 Total"/></a>
  <a href="./JUDGE_README.md"><img src="https://img.shields.io/badge/Judge%20Guide-3--Minute%20Fast--Track-FFC439?style=for-the-badge&logo=readme&logoColor=black" alt="Judge Guide"/></a>
  <a href="./LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="MIT License"/></a>
</p>

<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/rainbow.png" width="100%" alt="divider"/>

</div>

## 🏆 For Hackathon Judges & Evaluators (3-Minute Fast-Track)

> ⚡ **JUDGES START HERE**: Please read **[JUDGE_README.md](./JUDGE_README.md)** for our concise 3-minute executive evaluation guide and rubric alignment!
>
> 📌 **Direct Judge Quick Links**:
> - ⚡ **Fast-Track Judge Guide**: **[JUDGE_README.md](./JUDGE_README.md)** (3-Minute Read)
> - 📜 **Consolidated Master PRD & Engineering Blueprint**: **[`docs/KINETIXRAG_PAYPAL_HACKATHON_MASTER_PRD_V2.md`](./docs/KINETIXRAG_PAYPAL_HACKATHON_MASTER_PRD_V2.md)**
> - 🌐 **Interactive 4-Stage Procurement Experience**: `/procurement` (`http://localhost:3000/procurement`)
> - 🧪 **34 Automated PayPal & Secret Scan Tests**: `pytest tests/test_paypal_*.py tests/test_spending_mandate_v2.py tests/test_evidence_gating.py tests/test_secret_scan.py -v`

---

## 💡 The Real-World Industrial Challenge

In autonomous industrial facilities, AI agents are increasingly entrusted with monitoring rotating equipment and ordering spare parts or contracted maintenance. However, autonomous commerce introduces an existential risk: **agent spend leakage and contractor non-performance**. 

If an AI agent pays an equipment vendor upfront, or if settlement occurs before physical work is verified, facilities risk millions in unfulfilled repairs and catastrophic equipment breakdown. Traditional enterprise procurement solves this with slow bureaucratic sign-offs (2 to 4 weeks for purchase orders and invoice reconciliation), leading to extended plant downtime.

### 🛡️ The KinetixRAG Solution: "No Evidence, No Capture"

**KinetixRAG** pioneers **Evidence-Gated Industrial Procurement** by combining:
1. **Physical Grounding**: Real vibration telemetry from the **NASA IMS Bearing Run-to-Failure dataset** (4.82 mm/s RMS, ISO 10816 Zone C/D).
2. **GraphRAG Diagnosis**: Grounded knowledge retrieval identifies inner-race bearing degradation on Primary Slurry Pump `P-101A` and drafts Work Order `WO-2026-IMS-001`.
3. **Deterministic Spending Mandate Engine**: Evaluates vendor bids against non-negotiable server-side constraints (strict $500 cap, non-positive amount blocking, SLA limits, USD currency gate, vendor allowlist, Lane B dual-control supervisor routing).
4. **PayPal Orders v2 Two-Phase Settlement & Buyer Approval**: Creates an order with `intent: AUTHORIZE` via PayPal Sandbox (`api-m.sandbox.paypal.com`), confirms buyer approval via HATEOAS approval link, and executes an authorized hold (29-day authorization window with 3-day guaranteed honor period).
5. **Evidence Gating Engine ("No Evidence, No Capture")**: **Strictly blocks funds capture (HTTP 403)** until the contractor submits verifiable completion evidence (post-repair vibration measurement $\le$ 4.5 mm/s, SHA-256 document checksum) and a designated reliability supervisor signs off.
6. **Dual-Control Separation of Duties**: Strictly enforces that the procurement requester cannot approve their own payment (`order.requester_user_id != supervisor_id`, HTTP 403 on self-approval).
7. **Deterministic Capture & Continuous Cryptographic Audit**: Captures authorized funds via PayPal API `POST /v2/payments/authorizations/{id}/capture` and seals an unbroken continuous SHA-256 hash chain and Merkle root from initial sensor telemetry to final PayPal Capture ID.

---

## 📐 System Architecture

```mermaid
flowchart TD
    subgraph TELEMETRY["1. Empirical Telemetry & Diagnosis"]
        IOT["IoT Accelerometry Sensor<br/>(NASA IMS Bearing 1: 4.82 mm/s RMS)"] -->|ISO 10816 Zone C/D Alert| DIAG["GraphRAG Knowledge Engine"]
        DIAG -->|Diagnosis: Inner Race Bearing Wear| WO["Work Order WO-2026-IMS-001<br/>(Scope: SCOPE-BRG-REPLACE-01)"]
    end

    subgraph PROCUREMENT["2. Procurement & Spending Mandate Engine"]
        WO --> RFQ["Multi-Vendor RFQ Comparison<br/>[Synthetic Demo Quotes]"]
        RFQ -->|Apex Rotating: $450.00 USD| MANDATE["Deterministic Spending Mandate"]
        MANDATE -->|Checks: $500 Cap, Currency, Registry| LANE{"Risk Lane Classification"}
        LANE -->|Asset: Critical| LANE_B["Lane B: Dual-Control Required"]
    end

    subgraph PAYPAL["3. PayPal Two-Phase Settlement & Evidence Gate"]
        LANE_B -->|POST /v2/checkout/orders (intent: AUTHORIZE)| ORD_AUTH["PayPal Orders v2 Authorization<br/>(29-Day Authorized Escrow Hold)"]
        ORD_AUTH --> EARLY_CAP{"Attempt Early Capture?"}
        EARLY_CAP -->|No Evidence on File| BLOCKED["❌ HTTP 403 Forbidden<br/>(NO_EVIDENCE_NO_CAPTURE)"]
        
        VENDOR["Vendor Service Execution"] -->|Post-Repair Vibration: 2.15 mm/s<br/>SHA-256 Report Checksum| EVIDENCE["Evidence Validator"]
        EVIDENCE -->|Valid Multi-Check| SUP_AUTH["Lane B Supervisor Sign-Off<br/>(Plant Reliability Lead MFA)"]
        
        SUP_AUTH --> GATED_CAP["POST /v2/payments/authorizations/{id}/capture"]
        GATED_CAP --> SETTLED["✅ PayPal Capture Confirmed<br/>(Status: COMPLETED)"]
    end

    subgraph AUDIT["4. Cryptographic Causal Ledger"]
        SETTLED --> LEDGER["7-Stage Causal Audit Lineage<br/>Sensor ➔ GraphRAG ➔ WO ➔ Quote ➔ Mandate ➔ Auth ➔ Capture"]
    end
```

---

## 🖥️ Interactive 4-Stage Procurement Experience (`/procurement`)

The frontend application provides a dedicated 4-stage operator cockpit accessible at `/procurement`:

1. **Screen 1: Incident Intelligence & Physical Grounding**
   - Live NASA IMS bearing vibration accelerometry graph displaying the 4.82 mm/s RMS spike on Primary Slurry Pump `P-101A`.
   - ISO 10816-3 Zone C/D critical alarm banner.
   - Grounded GraphRAG diagnostic finding and automatically drafted work order `WO-2026-IMS-001`.

2. **Screen 2: RFQ Bidding & Spending Mandate Engine**
   - 3 vendor comparison bids clearly labeled `[SYNTHETIC DEMO QUOTE]`.
   - Real-time policy evaluation against enterprise mandate rules ($500.00 cap, USD currency gate, vendor allowlist).
   - Dynamic risk classification routing to **Lane B (Critical Asset)**.

3. **Screen 3: PayPal Authorization & The Evidence Gate (Hero Demo)**
   - PayPal Orders v2 Sandbox authorization creation (`ORD-SANDBOX-...`, `AUTH-SANDBOX-...`).
   - **Interactive Negative Test**: Evaluators can click *"Attempt Early Capture"* to observe the deterministic **HTTP 403 Block** (`NO_EVIDENCE_NO_CAPTURE`).
   - Vendor completion report upload with vibration re-inspection check ($\le$ 4.5 mm/s) and SHA-256 integrity digest.
   - Dual-control supervisor sign-off gate.
   - Successful gated capture execution yielding real PayPal Capture ID.

4. **Screen 4: 7-Stage Causal Audit Ledger**
   - Cryptographically linked chronological timeline proving complete lineage from raw sensor anomaly to settled PayPal transaction.

---

## 🔬 Truth in Engineering & Data Provenance

To maintain absolute academic and engineering integrity:

| Data Element | Type | Provenance / Source | Disclosure |
| :--- | :---: | :--- | :--- |
| **Vibration Telemetry** | **Empirical** | NASA IMS Bearing Run-to-Failure Dataset (University of Cincinnati IMS / NASA Prognostics Center of Excellence). | Real physical run-to-failure accelerometry sampled at 20 kHz. |
| **Asset Diagnostics** | **Empirical** | ISO 10816-3 Industrial Vibration Evaluation Standards + GraphRAG graph embeddings. | Grounded in industrial engineering failure standards. |
| **Vendor RFQ Quotes** | **Synthetic** | 3 candidate vendor bids generated for evaluation. | Clearly marked in the UI and API with `[SYNTHETIC DEMO QUOTE]`. |
| **Vendor Service Report** | **Synthetic** | Service report fixture demonstrating post-repair re-inspection. | Labeled `[SYNTHETIC DEMO REPORT]`. |
| **PayPal API Calls** | **Live Sandbox** | PayPal Orders v2 REST API running against the official PayPal Sandbox environment. | Real PayPal OAuth2 client credentials, order creation, authorization, and capture. |

---

## 🧪 Verified Test Suite (396 Passing Tests)

KinetixRAG enforces comprehensive automated test verification across both backend and frontend:

```bash
# 1. Run PayPal Orders v2, DB Models, Mandates, Evidence Gating, and Webhooks
pytest tests/test_paypal_orders_v2.py \
       tests/test_paypal_db_models.py \
       tests/test_spending_mandate_v2.py \
       tests/test_evidence_gating.py \
       tests/test_paypal_webhooks.py \
       tests/test_paypal_api_endpoints.py \
       tests/test_secret_scan.py -v

# 2. Run Frontend Vitest Component Suite (17 test files, 65 tests)
cd frontend && npm test -- --run

# 3. Run Full Backend Pytest Suite
pytest -v
```

### Test Suite Breakdown

| Layer | Files | Verified Tests | Status |
| :--- | :--- | :---: | :---: |
| **PayPal Orders v2 Client** | `tests/test_paypal_orders_v2.py` | 6 tests | **100% PASS ✅** |
| **PayPal DB State Machine** | `tests/test_paypal_db_models.py` | 3 tests | **100% PASS ✅** |
| **Spending Mandate Engine** | `tests/test_spending_mandate_v2.py` | 6 tests | **100% PASS ✅** |
| **Evidence Gating Engine** | `tests/test_evidence_gating.py` | 6 tests | **100% PASS ✅** |
| **Cryptographic Webhooks** | `tests/test_paypal_webhooks.py` | 6 tests | **100% PASS ✅** |
| **Procurement API Endpoints**| `tests/test_paypal_api_endpoints.py`| 5 tests | **100% PASS ✅** |
| **Pre-Submission Secret Scan**| `tests/test_secret_scan.py` | 2 tests | **100% PASS ✅** |
| **Frontend UI & Components** | Vitest (`frontend/`) | 65 tests | **100% PASS ✅** |
| **Full Project Harness** | Backend Core, Retrieval, Agents, ML | **396 tests** | **100% PASS ✅** |

---

## 🚀 Quickstart (Run Locally)

### Prerequisites
* Python 3.11 or 3.12
* Node.js 18+ & npm

### Step 1: Clone Repository & Configure Environment
```bash
git clone https://github.com/Niss54/KinetixRAG.git
cd KinetixRAG
cp .env.example .env
```

### Step 2: Configure PayPal Sandbox Credentials in `.env`
```env
PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=your_paypal_sandbox_client_id
PAYPAL_CLIENT_SECRET=your_paypal_sandbox_client_secret
PAYPAL_WEBHOOK_ID=your_optional_webhook_id
```

### Step 3: Launch FastAPI Backend
```bash
python -m pip install -r requirements.txt
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
* Backend Swagger documentation is accessible at [`http://localhost:8000/docs`](http://localhost:8000/docs).

### Step 4: Launch Next.js Frontend
```bash
cd frontend
npm install
npm run dev
```
* Open [`http://localhost:3000/procurement`](http://localhost:3000/procurement) to experience the live Evidence-Gated Procurement workflow.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](./LICENSE) file for details.  
Copyright (c) 2026 Niss54.
