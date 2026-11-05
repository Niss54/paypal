<div align="center">



<img src="./frontend/public/kr.png" alt="KinetixRAG Logo" width="130" style="margin-bottom: 10px;" />



# ⚡ KinetixRAG — PayPal AI Hackathon 2026 Judge Evaluation Guide



</div>



> **Project Identity:** KinetixRAG — Evidence-Gated Industrial Procurement  

> **Target Track:** Best Use of Agentic Commerce ($5,000 Special Prize) & Grand Prize  

> **Evaluation Duration:** 3 Minutes  

> **Signature Innovation:** **"No Evidence, No Capture"** via PayPal Orders v2 Two-Phase Settlement  

> **Interactive Live Route:** `/procurement` (`http://localhost:3000/procurement`)  

> **Automated Test Suite:** 100% pass rate: 394 automated tests passing across backend, auth, mandates, evidence gating, webhooks, and full project harness + 65 frontend tests passing with zero errors.



---



## 🏆 30-Second Elevator Pitch



In industrial manufacturing, AI agents that automatically purchase replacement services risk enterprise catastrophic spend if they pay vendors without verifying physical repairs. Traditional checkout systems either pay upfront or require slow human bureaucratic sign-offs that delay critical asset uptime.



**KinetixRAG** solves this with **Evidence-Gated Industrial Procurement** powered by **PayPal Orders v2**:

1. **IoT Telemetry & GraphRAG**: Real-world **NASA IMS Bearing Accelerometry** empirical baseline (`REPLAY-ASSET-01`, 5.42 mm/s RMS) informs the operational demonstration on synthetic asset `P-101A` (4.82 mm/s RMS, ISO 10816 Zone C/D threshold). The GraphRAG knowledge engine diagnoses inner-race defect risk and generates Work Order `WO-2026-IMS-001`.

2. **Deterministic Spending Mandate Engine**: Evaluates vendor RFQ quotes against strict hard-coded enterprise policies ($500 cap, non-positive amount blocking, SLA limits, USD currency check, approved vendor registry, Lane B dual-control supervisor routing).

3. **PayPal Orders v2 Authorization & Buyer Approval**: Creates an order with `intent: AUTHORIZE` via PayPal Sandbox (`api-m.sandbox.paypal.com`), confirms buyer approval via HATEOAS approval link, and executes an authorized hold (29-day authorization window with 3-day guaranteed honor period).

4. **"No Evidence, No Capture" Gating Engine (The Hero Moment)**: The AI agent and merchant are **strictly blocked (HTTP 403)** from capturing funds until the vendor submits verifiable physical completion evidence (post-repair vibration $\le$ 4.5 mm/s, SHA-256 report integrity digest) and an authorized supervisor signs off.

5. **Dual-Control Separation of Duties**: The system strictly enforces that the procurement requester cannot approve their own high-stakes payout (`order.requester_user_id != supervisor_id`, HTTP 403 on self-approval).

6. **Deterministic Capture & 7-Stage Continuous Cryptographic Audit**: Upon valid multi-check verification, the backend captures authorized funds (`POST /v2/payments/authorizations/{id}/capture`) and seals an unbroken SHA-256 cryptographic hash chain across all 7 stages from sensor anomaly to PayPal Capture ID.



---



## 🚀 3-Minute Fast-Track Walkthrough for Evaluators



### Step 1: Open the Evidence-Gated Procurement Console

Navigate to **`/procurement`** in the application UI (or run locally: `cd frontend && npm run dev` ➔ `http://localhost:3000/procurement`).

*(Tip: You can use the **1-Click Auto Demo** button in the header for an instant 10-second guided simulation walkthrough, or follow the step-by-step interactive mode below.)*



### Step 2: Screen 1 — Incident Intelligence (NASA IMS Telemetry)

- Inspect the live vibration anomaly for **Primary Slurry Pump P-101A** (Bearing 1: 4.82 mm/s RMS).

- Observe the **ISO 10816-3 Zone C/D Alarm** and the grounded **GraphRAG diagnostic finding**.

- Notice the automatically drafted Work Order: `WO-2026-IMS-001` with required scope (`SCOPE-BRG-REPLACE-01`).



### Step 3: Screen 2 — RFQ & Deterministic Spending Mandate

- Review the 3 vendor comparison quotes (clearly disclosed as `[SYNTHETIC DEMO QUOTE]`).

- Click **"Evaluate Mandate"** on the winning bid (**Apex Rotating Equipment**, `$450.00 USD`).

- Verify the **Deterministic Spending Mandate Engine** pass/fail matrix:

  - Budget Limit Check ($450.00 $\le$ $500.00 Cap): **PASSED**

  - Currency Check (USD): **PASSED**

  - Vendor Registry Check: **PASSED**

  - SLA Limit Check ($\le$ 48h): **PASSED**

  - Risk Policy: **LANE B (CRITICAL ASSET)** — dual-control supervisor sign-off required prior to capture.



### Step 4: Screen 3 — PayPal Authorization & The Evidence Gate (Hero Demo)

- Click **"Create PayPal Order"**:

  - PayPal Orders v2 Sandbox creates Order ID with `intent: AUTHORIZE` and HATEOAS `approve_url`.

- Confirm **Buyer Approval**:

  - Either click **"Open Sandbox Checkout"** for the genuine PayPal sandbox experience or click **"Fast Simulated Approval"** for automated demonstration.

- Click **"Authorize Payment Hold"**:

  - PayPal backend executes `POST /v2/checkout/orders/{id}/authorize`.

  - Authorized payment hold is established (`AUTH-...`). Status: **`AUTHORIZED`** (29-day authorization window, 3-day guaranteed honor period).

- 🚨 **Test the Hero Gate ("No Evidence, No Capture")**:

  - Click **"Attempt Early Capture (Should Fail)"**.

  - **Observe HTTP 403 Forbidden**: `Capture rejected: No verified completion evidence on file (NO_EVIDENCE_NO_CAPTURE)`. Funds remain completely safe in the authorized hold.

- 📋 **Submit Vendor Completion Evidence**:

  - Vendor submits physical service report with post-repair vibration reading: `1.25 mm/s RMS` (Passes ISO limit $\le 4.5$ mm/s) + SHA-256 document checksum.

  - Evidence validation status: **`VERIFIED`**.

- ✍️ **Supervisor Dual-Control Sign-Off**:

  - Reliability Supervisor signs off (`SUP-CHIEF-09`).

  - Strict separation of duties verified: Requester cannot sign off as supervisor (HTTP 403 on self-approval).

- 💳 **Execute Gated Capture**:

  - Click **"Execute Gated PayPal Capture"**.

  - Capture succeeds via `POST /v2/payments/authorizations/{id}/capture`! Status: **`COMPLETED`** with real PayPal Capture ID.



### Step 5: Screen 4 — 7-Stage Cryptographically Chained Audit Ledger

- Inspect the complete unbroken causal chain linking:

  1. Sensor Anomaly (4.82 mm/s RMS)

  2. GraphRAG Knowledge Diagnosis

  3. Work Order `WO-2026-IMS-001`

  4. RFQ Winning Quote ($450.00 USD)

  5. Spending Mandate Decision (`ALLOWED_LANE_B`)

  6. PayPal Authorization (`AUTH-...`)

  7. Verified Completion Evidence + Dual-Control Sign-Off ➔ Final PayPal Capture ID.

- Each stage displays its continuous **`stage_hash`** cryptographically chained from the previous stage (`previous_stage_hash`), culminating in a verifiable **Hash-Chained Audit Snapshot Hash**.



---



## 🧪 Verified Automated Test Suite



Every architectural layer is backed by comprehensive, passing automated tests:



```bash

# 1. Backend PayPal Integration, Evidence Gating & Security Tests (34 passed)

pytest tests/test_paypal_provider.py \

       tests/test_evidence_gating.py \

       tests/test_spending_mandate_v2.py \

       tests/test_paypal_api_endpoints.py \

       tests/test_secret_scan.py -v



# 2. Live PayPal Sandbox API Tests against api-m.sandbox.paypal.com (2 passed)

pytest tests/test_paypal_sandbox_live.py -v



# 3. Frontend Vitest Suite (17 test files, 65 tests passed)

cd frontend && npm test -- --run



# 4. TypeScript Type Safety Check (Zero compilation errors)

cd frontend && npx tsc --noEmit

```



---



---



## 🏛️ Enterprise Payment Architecture & Option A Settlement Routing



In mission-critical industrial plants, contractor disbursements follow an **Option A Merchant of Record Architecture**:

1. **Merchant of Record**: The industrial facility operator acts as the authorized merchant of record establishing the payment hold via PayPal Orders v2 (`intent: AUTHORIZE`).

2. **Authorized Hold & Payee Routing**: PayPal securely holds the authorized capital for up to 29 days (3-day honor window). The architecture supports multi-party routing (`payee: { email_address: vendor_paypal_email }`).

3. **No Evidence, No Capture**: Funds are never captured until post-repair vibration telemetry is cryptographically verified ($\le$ 4.5 mm/s RMS) and an authorized supervisor signs off under dual-control separation of duties.

4. **Disbursement**: Upon valid multi-point physical verification, `POST /v2/payments/authorizations/{id}/capture` executes, completing the authorized payment under Platform Merchant-of-Record settlement.



---



## 🔬 Dataset Provenance & Engineering Standards



- **Research Telemetry Baseline**: NASA IMS Run-to-Failure 2004 bearing accelerometry (`REPLAY-ASSET-01`, 5.42 mm/s baseline RMS) from University of Cincinnati Center for Intelligent Maintenance Systems.

- **Demonstration Plant Asset**: Primary Slurry Pump `P-101A` operating at 4.82 mm/s RMS vibration velocity, exceeding ISO 10816-3 Zone C/D threshold (4.50 mm/s limit).

- **Model-Estimated Diagnostic Confidence**: The 94.2% inner-race defect diagnosis is a model-estimated confidence derived from high-frequency spectral envelope feature analysis citing `ISO-10816-3 Table C.1`, `PROC-001`, `DOC-P101-RCA`, and `NASA-IMS-2004`.

- **Truthful Audit Ledger**: Unbroken causal lineage is cryptographically secured via a **Continuous Hash-Chained Audit Snapshot** (not a public distributed blockchain or Merkle tree).



## 🏛️ Architectural Integrity & Rubric Alignment



| Rubric Criterion | Implementation & Evidence |

| :--- | :--- |

| **Technological Implementation** | Full PayPal Orders v2 REST client (`api-m.sandbox.paypal.com`) with async single-flight token manager, 60s expiration buffer, idempotency headers (`PayPal-Request-Id`), typed exceptions, two-phase authorize/capture lifecycle, and webhook signature verification (`/v1/notifications/verify-webhook-signature`). Zero fake ID fallbacks in live mode. |

| **Design & User Experience** | Intuitive 4-stage operator workflow (`/procurement`) with interactive live test bench demonstrating both blocked attempts and successful gated settlements with zero UI flicker, single-line sidebar navigation, and responsive audit ledger. |

| **Potential Impact** | Eliminates autonomous agent spend leakage and supplier non-performance by enforcing the invariant: **"No Evidence, No Capture"** for mission-critical industrial assets. |

| **Innovation & Creativity** | Repurposes PayPal's two-phase `AUTHORIZE` + delayed capture pattern as an empirical evidence-gated safety barrier for autonomous agentic commerce, backed by continuous SHA-256 hash chaining. |

| **Truthful Disclosure** | Real empirical dataset: **NASA IMS Bearing Accelerometry**; vendor quotes clearly disclosed as `[SYNTHETIC DEMO QUOTE]`; simulation mode cleanly demarcated with `is_simulated` flags and badges. |

