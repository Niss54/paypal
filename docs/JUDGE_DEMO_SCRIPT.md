# KinetixRAG — Judge Demo Script (3–4 Minutes)

**Event:** PayPal AI Hackathon 2026  
**Category:** Best Use of Agentic Commerce ($5,000 Special Prize) & Grand Prize  
**Core Thesis:** *AI recommends. Policy controls. Evidence verifies. PayPal executes.*  
**Live UI Console:** [`/procurement`](http://localhost:3000/procurement)  
**Backend API:** FastAPI with PayPal Orders v2 REST API Integration  
**Target Duration:** 3 to 4 minutes  

---

## ⏱️ Minute-by-Minute Screen & Narration Walkthrough

### 🎬 Part 1: The Agentic Commerce Problem (0:00 – 0:30)
* **Screen:** Open the **Evidence-Gated Procurement Console** at `/procurement`. Point cursor to the top header showing the active persona bar, the PayPal Orders v2 badge, and the 3-step procurement progression bar.
* **Narration:**
  > "Judges, the greatest barrier to autonomous agentic commerce is trust. In industrial operations, giving an AI agent an unconstrained corporate card or payment wallet invites hallucinations, prompt injection, and premature release of funds before work is actually completed.
  > Today, we present **KinetixRAG** — the first **Evidence-Gated Autonomous Procurement System** built on **PayPal Orders v2**.
  > Our architecture enforces a strict division of responsibility:
  > **AI recommends. Policy controls. Evidence verifies. PayPal executes.**
  > Money never moves unconditionally. Capital is protected by a two-phase PayPal authorization hold and released only after physical sensor evidence confirms successful machine repair."

---

### 🔍 Part 2: AI Diagnosis & RFQ Ranking (0:30 – 1:00)
* **Screen:** Scroll to **Step 1: Incident & Quote Selection**. Highlight the **Asset Anomaly Card** (`P-101A`, 4.82 mm/s RMS vs 4.50 mm/s limit) and the **3 Evaluated Vendor Quotes**.
* **Narration:**
  > "Let's look at the operational trigger:
  > Sensor telemetry on Primary Slurry Pump **P-101A** detected a severe radial vibration excursion at 4.82 mm/s RMS, breaching the ISO 10816 Zone C operational threshold.
  > Our GraphRAG engine instantly traversed our plant ontology, correlating the vibration spectrogram with failure signature **FE-001** (Outer Race Fatigue Spalling) and procedure **PROC-001** with 94.2% scenario confidence.
  > The procurement agent automatically federated RFQs to three pre-approved suppliers. Notice the scoring: Vendor **VND-001 (Bearing Supply Co)** is selected at $450.00 USD with a 24-hour SLA."

---

### 🛡️ Part 3: Deterministic Spending Mandate (1:00 – 1:30)
* **Screen:** Point to the **Deterministic Spending Mandate Badge** and click into the Mandate Evaluation details.
* **Narration:**
  > "Notice who authorizes the transaction: **not the LLM**.
  > An AI model can hallucinate, but our **Deterministic Spending Mandate** evaluates hard mathematical gates:
  > 1. Amount ($450.00 USD) is within the automated cap ($500.00).
  > 2. Supplier is verified on the plant allowlist.
  > 3. Currency is validated as USD.
  > 4. Because P-101A is classified as a Critical Asset, the mandate assigns **Lane B Governance**, strictly requiring post-repair operational evidence and independent dual-control supervisor sign-off before settlement."

---

### 💳 Part 4: PayPal Authorization Hold (1:30 – 2:00)
* **Screen:** Click **`Create PayPal Order`** and **`Buyer Approve`** (or let the 1-Click Auto Demo execute).
* **Narration:**
  > "Now PayPal executes. 
  > Instead of paying upfront, KinetixRAG calls PayPal Orders v2 with `intent: AUTHORIZE`.
  > The plant finance authority approves via PayPal Sandbox, and our backend creates an authorized hold for $450.00 USD.
  > Under our Platform Merchant of Record model, capital is safely committed and held for up to 29 days without leaving escrow."

---

### 🚫 Part 5: The Hero Negative Gate Test (2:00 – 2:30)
* **Screen:** Highlight the red alert: **`Server Gate Policy Enforced: HTTP 403 Forbidden (NO_EVIDENCE_NO_CAPTURE)`**.
* **Narration:**
  > "Here is our core technical differentiator: **The Evidence Gate**.
  > What happens if an agent or vendor attempts early payment capture right now?
  > Watch: our backend immediately rejects premature capture with **HTTP 403 Forbidden**.
  > This is not a simulated UI mock — it is an authoritative server-side check.
  > The rule is absolute: **No Evidence, No Capture.** Funds cannot be captured while the asset remains in an unverified state."

---

### 🔬 Part 6: Physical Evidence & Dual-Control Sign-Off (2:30 – 3:15)
* **Screen:** Scroll to **Step 2: Evidence Gate & Settlement**. Show the **Evidence Submission** card with the uploaded vibration inspection certification, followed by the **Supervisor Sign-off**.
* **Narration:**
  > "Now, the certified millwright technician replaces the bearing and runs a post-repair test.
  > The technician submits an authentic test report artifact:
  > Post-repair vibration is measured at **1.25 mm/s RMS (ISO Zone A - Good)**.
  > Our server computes a cryptographic SHA-256 digest of the artifact and derives verified operational provenance.
  > Next, our separation-of-duties engine requires an independent **Plant Reliability Supervisor** to authenticate via Microsoft Entra ID / RBAC and sign off. Dual control is satisfied."

---

### 💰 Part 7: Verified Capture & Hash-Chained Audit Trail (3:15 – 4:00)
* **Screen:** Click **`Capture Authorized Funds`**. Display the green capture banner and the **7-Stage Cryptographic Causal Lineage**.
* **Narration:**
  > "With all policy gates unlocked, the backend invokes PayPal Capture:
  > PayPal confirms with a real capture ID and status **COMPLETED**.
  > Finally, look at our **7-Stage Hash-Chained Audit Snapshot**:
  > Every link in the chain — from initial telemetry anomaly, to GraphRAG diagnosis, mandate approval, PayPal authorization, SHA-256 evidence artifact, supervisor sign-off, to final settlement — is bound into an unbroken SHA-256 cryptographic chain.
  > If a single byte is tampered with, the audit chain breaks.
  > This is how enterprise agentic commerce must work: autonomous speed with institutional safeguards.
  > Thank you!"

---

## 📋 Judge Technical Q&A Reference

| Question | Defensible Answer | Code Reference |
| :--- | :--- | :--- |
| **What is your PayPal payment model?** | **Platform Merchant of Record (Option A)**. The plant facility authorizes payment to the Kinetix platform, which manages procurement and settlement upon verified evidence sign-off. | `backend/app/services/paypal/orders.py`, `frontend/app/procurement/page.tsx` |
| **Is the early capture test real?** | Yes. Calling `/paypal/orders/{order_id}/capture` without verified evidence returns HTTP 403 Forbidden with `NO_EVIDENCE_NO_CAPTURE`. | `backend/app/services/procurement/orchestrator.py` |
| **How is evidence integrity verified?** | The server computes a SHA-256 hash of the uploaded report content, verifies post-repair vibration <= 4.50 mm/s (ISO 10816 Zone A/B), and derives provenance server-side. | `backend/app/services/procurement/evidence.py` |
| **How is dual-control enforced?** | The supervisor user ID cannot match the order requester, and the caller must possess the `Supervisor` role verified via JWT / Entra ID. | `backend/app/services/procurement/orchestrator.py`, `backend/app/core/auth.py` |
| **What is the telemetry dataset?** | NASA IMS Bearing Run-to-Failure dataset is replayed on `REPLAY-ASSET-01` (5.42 mm/s RMS). Asset `P-101A` is a synthetic industrial demo asset (4.82 mm/s RMS) calibrated from ISO 10816 standards. | `docs/PUBLIC_DATASET_PROVENANCE.md` |
