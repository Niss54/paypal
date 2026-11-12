# KinetixRAG: Hackathon Judge & Demonstration Runbook

This guide contains everything required to safely run, demonstrate, and verify the KinetixRAG platform for the PayPal AI Hackathon evaluation.

---

## 1. System Requirements & Prerequisites

- **Python:** Python 3.12 (use `py -3.12` on Windows).
- **Node.js:** Node v18+ (Node v20+ recommended).
- **Package Managers:** `pip`, `npm`.
- **Environment File:** `.env` copied from `.env.example`.

---

## 2. Safe Pre-Flight Audit & Verification

Before starting services or recording demonstrations, run the automated pre-flight audit scripts:

```powershell
# Step 1: Verify Zero Leaked Credentials in Repository
py -3.12 scripts/secret_scan.py
# Expected: [PASS] No credential patterns found in scanned working files.

# Step 2: Run Full Pre-Flight Sandbox Verification
py -3.12 scripts/verify_sandbox.py
# Expected: PREFLIGHT OVERALL STATUS: PASS (4/5 PASS, 1 SIMULATED)

# Step 3: Verify Backend Test Health
py -3.12 -m pytest tests/test_paypal_api_endpoints.py tests/test_evidence_gating.py
# Expected: 20 passed
```

---

## 3. Local Startup Commands

### Terminal 1: Backend Server (FastAPI)
```powershell
# Set Python path and launch Uvicorn
$env:PYTHONPATH = "."
py -3.12 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Health Check:* Open `http://127.0.0.1:8000/health` (Expect: `{"status": "healthy", "version": "0.1.0"}`).

### Terminal 2: Frontend Client (Next.js)
```powershell
cd frontend
npm run dev
```
*Access UI:* Open `http://localhost:3000` in Google Chrome or any modern browser.

---

## 4. Primary Hackathon Demonstration Flow (3-Minute Script)

The core product promise is **"No Evidence, No Capture"** (Funds are held in PayPal Sandbox and never captured until physical repair evidence is mathematically verified and approved).

### Step 1: Telemetry Anomaly & Incident Investigation
1. Navigate to `/predictive-watch` or `/investigate`.
2. Inspect the NASA IMS bearing vibration anomaly:
   - Asset: `P-101A` (Primary Slurry Feed Pump).
   - Sensor reading: **4.82 mm/s RMS** (exceeds ISO-10816-3 Zone C alarm threshold of 4.50 mm/s).
   - GraphRAG diagnostic attribution identifies outer-race defect (BPFO) with 94.2% confidence.

### Step 2: RFQ Evaluation & Deterministic Spending Mandate
1. Navigate to `/procurement`.
2. Inspect the 3 synthetic quotes:
   - **Motion Industries (Q-2026-001):** **$450.00 USD**, 24h SLA -> **ALLOWED** (complies with $500 cap).
   - **Applied Industrial (Q-2026-002):** $680.00 USD -> **BLOCKED / REQUIRES REVIEW** (exceeds $500 cap).
   - **Grainger Spares (Q-2026-003):** $420.00 USD, 72h SLA -> **BLOCKED** (SLA exceeds 48h emergency window).
3. Select **Quote Q-2026-001** ($450.00).

### Step 3: PayPal Order Creation & Two-Phase Authorization Hold
1. Click **"Create PayPal Order (intent: AUTHORIZE)"**.
   - Note: In simulation mode (`is_simulation=True`) or live sandbox (`is_simulation=False`), order is created with `intent: AUTHORIZE`.
2. Complete Buyer Approval (click Sandbox link, use the PayPal checkout popup, or use "Confirm Buyer Approval"):
   - When the PayPal Sandbox login modal opens, use the official test buyer account:
     - **Buyer Email:** `sb-h9ysd53750459@personal.example.com`
     - **Buyer Credentials:** Refer to local `.env` (`PAYPAL_BUYER_PASSWORD`) or Hackathon Devpost private note
     - **Test Card:** VISA `4311193954877121` (Exp: `02/2031`, CVV: `123`)
     - **Sandbox Balance:** USD 50,000 available
3. Click **"Authorize Payment Hold"**.
   - Observe status transitions to `AUTHORIZED`.
   - Authorization ID is generated (e.g. `AUTH-SANDBOX-xxxxx`).
   - Notice that funds are placed on a 29-day authorization hold (3-day honor window)—**funds have NOT been transferred**.

### Step 4: The Core Security Gate: Attempt Premature Capture (MUST FAIL)
1. Before submitting evidence, click **"Attempt Early Capture (Should Fail with HTTP 403)"**.
2. **Observe Server Rejection:**
   - Server returns **HTTP 403 Forbidden**.
   - Error code: `EvidenceGateBlocked`.
   - Message: `"No Evidence, No Capture: Funds remain held in PayPal Sandbox"`.
   - Demonstrates that AI or unverified requests cannot prematurely capture funds.

### Step 5: Contractor Evidence Submission & Integrity Verification
1. Under Evidence Submission, upload or submit the completion report:
   - Post-repair vibration reading: **1.25 mm/s RMS** (Restored to ISO-10816 Zone A "Good" condition).
   - SHA-256 binary hash computed deterministically.
   - Checklist validated (bearing replacement + laser alignment).
2. Click **"Submit Completion Evidence"**.
   - Status updates to `EVIDENCE_VERIFIED`.

### Step 6: Dual-Control Supervisor Sign-Off (Separation of Duties)
1. Notice the active user persona.
2. If testing self-approval with the requester persona, observe the system rejects self-approval.
3. Switch to or authenticate as supervisor (`SUP-CHIEF-09`).
4. Click **"Supervisor Sign-Off"**.
   - Both physical evidence and managerial authorization are now complete.

### Step 7: Gated Capture Execution & Cryptographic Audit Lineage
1. Click **"Execute Gated PayPal Capture ($450.00)"**.
2. Capture succeeds with HTTP 200:
   - Order status transitions to `CAPTURED`.
   - Capture ID is persisted.
3. Inspect the **7-Stage Cryptographic Audit Lineage**:
   - Continuous SHA-256 hash chaining links anomaly -> diagnosis -> RFQ -> mandate -> authorization -> evidence -> capture.
   - Merkle root with depth $O(\log_2 N)$ provides tamper detection.
   - Individual inclusion proofs verifiable in $O(\log N)$ time.

---

## 5. Offline / Backup Demonstration Mode

If the PayPal Sandbox API or remote network is unavailable during a live presentation:

1. Toggle the **"Simulation Mode"** switch in the top-right header of `/procurement`.
2. The entire 7-step lifecycle executes locally with identical deterministic policy gates, SHA-256 evidence validation, separation-of-duties checks, and Merkle audit tracking.
3. The UI clearly displays `[SIMULATED]` badges to ensure total transparency.

---

## 6. Demo State Reset Procedure

To cleanly reset demo state for a new recording:

```powershell
# Quick reset: Restart backend or call warm-demo script
py -3.12 scripts/warm_demo.py
```
Or simply refresh the `/procurement` page in the browser to initialize a fresh session.
