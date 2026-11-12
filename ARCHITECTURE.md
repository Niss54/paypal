# KinetixRAG Enterprise & Agentic Commerce Architecture

**PayPal AI Hackathon 2026 — Primary Track: Best Use of Agentic Commerce**

This document provides the complete, authoritative architectural specifications, Mermaid sequence diagrams, state machines, and data topologies for **KinetixRAG**.

---

## 📑 Architecture Navigation Index

| Section | Architecture Diagram | Focus Area |
| :--- | :--- | :--- |
| **Section 1** | [End-to-End System Architecture](#1-end-to-end-system-architecture) | Full ingestion-to-settlement pipeline |
| **Section 2** | [PayPal Payment Lifecycle Architecture](#2-paypal-payment-lifecycle-architecture) | Two-phase authorization hold & evidence gating |
| **Section 3** | [Multi-Source Predictive Telemetry Architecture](#3-multi-source-predictive-telemetry-architecture) | NASA IMS replay, mobile MEMS & sensor bridge |
| **Section 4** | [Hybrid GraphRAG Knowledge Architecture](#4-hybrid-graphrag-knowledge-architecture) | Neo4j multi-hop traversal & citation grounding |
| **Section 5** | [Dual-Control Evidence & Merkle Lineage Architecture](#5-dual-control-evidence--merkle-lineage-architecture) | SHA-256 digest verification & binary Merkle tree |
| **Section 6** | [ERP Clearing & External Ledger Architecture](#6-erp-clearing--external-ledger-architecture) | Google Sheets GL 2100 clearing & SAP/Maximo connectors |

---

## 1. End-to-End System Architecture

The following diagram illustrates the complete flow of data from empirical sensor signals through multi-agent diagnosis, policy enforcement, PayPal Sandbox payment gating, and external ledger synchronization.

```mermaid
flowchart TD
    subgraph SENSORS["1. Physical & Replay Telemetry Layer"]
        S1["NASA IMS Bearing Dataset<br/>(20 kHz Run-to-Failure Accelerometry)"]
        S2["Live Smartphone MEMS<br/>(3-Axis DeviceMotionEvent Bridge)"]
        S3["Industrial Harmonic Synthesizer<br/>(Rotor Unbalance & Load Simulation)"]
    end

    subgraph INGESTION["2. Telemetry Processing & Anomaly Detection"]
        TP1["Velocity RMS Extrapolator<br/>(ISO 10816 Severity Calculator)"]
        TP2{"Threshold Evaluator<br/>(Zone C Boundary: 4.50 mm/s)"}
        S1 --> TP1
        S2 --> TP1
        S3 --> TP1
        TP1 --> TP2
    end

    subgraph GRAPHRAG["3. Grounded Multi-Agent Knowledge Swarm"]
        NEO["Neo4j Knowledge Graph<br/>(Equipment ➔ Component ➔ Failure ➔ SOP)"]
        QDR["Qdrant Vector Store<br/>(Hybrid Dense + Sparse BM25 Search)"]
        RCA["RCA Diagnostic Specialist<br/>(Root Cause & Failure Horizon)"]
        CIT["Citation Resolver<br/>(ISO-10816-3, PROC-001, WO-1002)"]
        TP2 -- "Excursion (> 4.5 mm/s)" --> RCA
        RCA <--> NEO
        RCA <--> QDR
        RCA --> CIT
    end

    subgraph MANDATE["4. Deterministic Spending Mandate Engine"]
        RFQ["Vendor RFQ Evaluator<br/>(3 Candidate Supplier Quotes)"]
        POL{"Policy Validator<br/>(Cap: $500.00 USD | SLA <= 48h)"}
        CIT --> RFQ
        RFQ --> POL
    end

    subgraph PAYPAL["5. PayPal Orders v2 Two-Phase Settlement"]
        ORD["Create Order<br/>(intent: AUTHORIZE, $450.00 USD)"]
        APP["Buyer Approval<br/>(PayPal Sandbox Hosted Checkout)"]
        AUT["Payment Authorization<br/>(Funds Held in Sandbox)"]
        GATE{"Evidence Gate<br/>(HTTP 403 Early Capture Block)"}
        POL -- "Quote Q-2026-001 Approved" --> ORD
        ORD --> APP
        APP --> AUT
        AUT --> GATE
    end

    subgraph VERIFICATION["6. Evidence Validation & Dual-Control RBAC"]
        REP["Technician Report Upload<br/>(Vibration <= 4.5 mm/s & Checklist)"]
        HASH["Cryptographic SHA-256 Digest<br/>(Report Hash Verification)"]
        SUP{"Supervisor Sign-Off<br/>(Separation of Duties Check)"}
        REP --> HASH
        HASH --> SUP
        SUP -- "Approved (SUP-09)" --> GATE
    end

    subgraph SETTLEMENT["7. Capture Execution & Audit Sealing"]
        CAP["Execute PayPal Capture<br/>(POST /v2/checkout/orders/{id}/capture)"]
        MRK["Binary Merkle Tree Audit Sealer<br/>(O(log N) Cryptographic Root)"]
        ERP["ERP Ledger Synchronizer<br/>(Google Sheets GL 2100 Clearing)"]
        GATE -- "All Conditions Met" --> CAP
        CAP --> MRK
        CAP --> ERP
    end

    style SENSORS fill:#0f172a,stroke:#38bdf8,stroke-width:1px,color:#f8fafc
    style INGESTION fill:#1e1b4b,stroke:#818cf8,stroke-width:1px,color:#f8fafc
    style GRAPHRAG fill:#064e3b,stroke:#34d399,stroke-width:1px,color:#f8fafc
    style MANDATE fill:#451a03,stroke:#fbbf24,stroke-width:1px,color:#f8fafc
    style PAYPAL fill:#1e3a8a,stroke:#60a5fa,stroke-width:2px,color:#f8fafc
    style VERIFICATION fill:#701a75,stroke:#f472b6,stroke-width:1px,color:#f8fafc
    style SETTLEMENT fill:#14532d,stroke:#4ade80,stroke-width:2px,color:#f8fafc
```

---

## 2. PayPal Payment Lifecycle Architecture

The core financial safety mechanism of KinetixRAG is the **Two-Phase Authorization Hold with Evidence Gating**.

```mermaid
sequenceDiagram
    autonumber
    actor Tech as Field Technician
    actor Agent as Procurement Agent
    participant Backend as FastAPI Backend
    participant Mandate as Policy Engine
    participant PayPal as PayPal Orders v2 (Sandbox)
    actor Super as Supervisor (Dual Control)
    participant ERP as ERP Ledger (Google Sheets)

    Note over Agent,PayPal: Phase 1: Purchase Planning & Authorization Hold
    Agent->>Backend: Request Incident Quotes & Diagnosis
    Backend->>Mandate: Evaluate Quotes against $500.00 Policy Cap
    Mandate-->>Backend: Winner: Motion Industries ($450.00 USD, 24h SLA)
    Agent->>Backend: Initialize PayPal Order (intent: AUTHORIZE)
    Backend->>PayPal: POST /v2/checkout/orders (intent=AUTHORIZE, amount=$450)
    PayPal-->>Backend: Return Order ID (e.g., 816654817Y487441B)
    Agent->>PayPal: Redirect to Sandbox Buyer Checkout & Approve
    PayPal-->>Agent: Approval Hook (token / PayerID)
    Agent->>Backend: Authorize Order (POST /api/paypal/orders/{id}/authorize)
    Backend->>PayPal: POST /v2/checkout/orders/{id}/authorize
    PayPal-->>Backend: Authorization ID & Status = AUTHORIZED

    Note over Agent,Backend: Gate Verification: Early Capture Rejection
    Agent->>Backend: Attempt Premature Capture (POST /api/paypal/orders/{id}/capture)
    Backend->>Backend: Check Evidence Registry & Supervisor Sign-off
    Backend-->>Agent: HTTP 403 Forbidden (NO_EVIDENCE_NO_CAPTURE)
    Note over Backend: Early Capture Blocked! Funds remain in Authorization Hold.

    Note over Tech,Super: Phase 2: Evidence Submission & Dual-Control Approval
    Tech->>Backend: Submit Repair Report & Vibration Measurement (1.25 mm/s)
    Backend->>Backend: Validate SHA-256 Digest & ISO Threshold
    Backend->>Backend: Bind caller user_id to technician audit record
    Backend-->>Tech: Evidence Validated (EVD-2026-IMS-001)
    
    Agent->>Backend: Attempt Self-Approval
    Backend-->>Agent: HTTP 403 Forbidden (SEPARATION_OF_DUTIES_VIOLATION)
    
    Super->>Backend: Authenticate (Supervisor Role)
    Super->>Backend: Sign-off Work Order (POST /api/paypal/orders/{id}/sign-off)
    Backend-->>Super: Dual-Control Sign-off Recorded

    Note over Backend,ERP: Phase 3: Final Capture & Ledger Reconciliation
    Agent->>Backend: Request Capture (POST /api/paypal/orders/{id}/capture)
    Backend->>Backend: Verify Evidence Present & Supervisor Signed
    Backend->>PayPal: POST /v2/payments/authorizations/{auth_id}/capture
    PayPal-->>Backend: HTTP 201 Created (Capture ID: CAP-XXXXX, Status=COMPLETED)
    Backend->>Backend: Seal Binary Merkle Audit Tree
    Backend->>ERP: Sync to Google Sheets ERP Ledger (POST /exec, GL 2100)
    ERP-->>Backend: HTTP 200 OK (Row Appended)
    Backend-->>Agent: Settlement Finalized & Disbursed
```

---

## 3. Multi-Source Predictive Telemetry Architecture

KinetixRAG supports three distinct telemetry feeds while rigorously maintaining the boundary between real sensor data, simulated inputs, and historical reference benchmarks.

```mermaid
graph LR
    subgraph FEED1["Source 1: NASA IMS Benchmark Replay"]
        N1["Run-to-Failure Accelerometry<br/>(Test 2, Bearing 1)"] --> N2["20,000 Hz Sampling Extrapolator"]
        N2 --> N3["Progression Slider<br/>(Hour 0: Nominal ➔ Hour 164: Catastrophic 5.4 mm/s)"]
    end

    subgraph FEED2["Source 2: Live Smartphone MEMS Transmitter"]
        M1["Mobile Browser<br/>(window.DeviceMotionEvent)"] --> M2["3-Axis Inertial Packet<br/>(Ax, Ay, Az in m/s²)"]
        M2 --> M3["Calibrated RMS Velocity Index<br/>(Baseline 1.25 ➔ Vigorous Shake 10-25 mm/s)"]
        M3 --> M4["Neon Serverless PostgreSQL<br/>(Table: live_telemetry)"]
        M4 --> M5["Laptop Oscilloscope Cockpit<br/>(250ms Dual-Cloud Polling Bridge)"]
        M5 --> M6["Latching Trip Circuit<br/>(Holds Peak Alarm until User Clear)"]
    end

    subgraph FEED3["Source 3: Industrial Harmonic Synthesizer"]
        H1["1,780 RPM Motor Baseline"] --> H2["Rotor Unbalance Modulator (10-100%)"]
        H2 --> H3["1X / 2X / 4X Harmonic Waveform Generator"]
    end

    style FEED1 fill:#082f49,stroke:#0284c7,stroke-width:1px,color:#f8fafc
    style FEED2 fill:#022c22,stroke:#059669,stroke-width:1px,color:#f8fafc
    style FEED3 fill:#2e1065,stroke:#7c3aed,stroke-width:1px,color:#f8fafc
```

---

## 4. Hybrid GraphRAG Knowledge Architecture

The diagnostic intelligence is grounded in a multi-hop Neo4j knowledge graph linked with dense vector and sparse keyword retrieval.

```mermaid
graph TD
    subgraph GRAPH["Neo4j Knowledge Graph Entities & Relationships"]
        EQ["Equipment Entity<br/>tag_id: 'P-101A'<br/>name: 'Crude Charge Pump'"]
        COMP["Component Entity<br/>part_number: 'SKF-22210-E-C3'<br/>type: 'Spherical Roller Bearing'"]
        FE["FailureEvent Entity<br/>id: 'FE-001'<br/>mode: 'Outer Race Spalling'<br/>defect_freq: 148.2 Hz (BPFO)"]
        PROC["Procedure Entity<br/>id: 'PROC-001'<br/>name: 'Dial Indicator Alignment SOP'<br/>standard: 'ISO 10816-3'"]
        DATA["DatasetRecord Entity<br/>id: 'NASA-IMS-T2-REC-042'<br/>dataset: 'NASA IMS Run-to-Failure'"]

        EQ -- "HAS_COMPONENT" --> COMP
        COMP -- "SUSCEPTIBLE_TO" --> FE
        FE -- "MITIGATED_BY" --> PROC
        FE -- "EVIDENCED_BY" --> DATA
    end

    subgraph QUERY["Live Multi-Hop Cypher Traversal"]
        CYPHER["MATCH (eq:Equipment {tag_id: 'P-101A'})-[:HAS_COMPONENT]->(comp)<br/>OPTIONAL MATCH (comp)-[:SUSCEPTIBLE_TO]->(fe)<br/>OPTIONAL MATCH (fe)-[:MITIGATED_BY]->(proc)<br/>RETURN eq, comp, fe, proc"]
    end

    subgraph CITATIONS["Dynamic Attribution Output"]
        C1["ISO 10816-3 Table C.1 (Zone Boundary 4.50 mm/s)"]
        C2["PROC-001: Laser Alignment & Lubrication Standard"]
        C3["NASA IMS Run-to-Failure Benchmark (Test 2)"]
    end

    GRAPH --> CYPHER
    CYPHER --> CITATIONS

    style GRAPH fill:#1e1b4b,stroke:#6366f1,stroke-width:1px,color:#f8fafc
    style QUERY fill:#0f172a,stroke:#38bdf8,stroke-width:1px,color:#f8fafc
    style CITATIONS fill:#064e3b,stroke:#10b981,stroke-width:1px,color:#f8fafc
```

---

## 5. Dual-Control Evidence & Merkle Lineage Architecture

To guarantee non-repudiation and prevent premature payment release, the complete audit lineage is sealed into a binary Merkle tree.

```mermaid
graph BT
    subgraph LEAVES["Cryptographic Stage Hashes (SHA-256)"]
        H1["H1: Anomaly Telemetry<br/>SHA256(asset_tag + vibration + timestamp)"]
        H2["H2: Quote Evaluation<br/>SHA256(vendor_id + amount + mandate_pass)"]
        H3["H3: PayPal Authorization<br/>SHA256(order_id + auth_id + payer_id)"]
        H4["H4: Evidence Digest<br/>SHA256(report_bytes + post_repair_vibe)"]
        H5["H5: Supervisor Approval<br/>SHA256(supervisor_id + credential_hash)"]
        H6["H6: Final Capture<br/>SHA256(capture_id + gross_amount + status)"]
    end

    subgraph MERKLE["Binary Merkle Tree Construction (O(log N))"]
        N12["Node 12: SHA256(H1 + H2)"]
        N34["Node 34: SHA256(H3 + H4)"]
        N56["Node 56: SHA256(H5 + H6)"]
        N1234["Node 1234: SHA256(N12 + N34)"]
        ROOT["MERKLE ROOT HASH<br/>SHA256(N1234 + N56)"]

        H1 --> N12
        H2 --> N12
        H3 --> N34
        H4 --> N34
        H5 --> N56
        H6 --> N56
        N12 --> N1234
        N34 --> N1234
        N1234 --> ROOT
        N56 --> ROOT
    end

    style LEAVES fill:#1e293b,stroke:#64748b,stroke-width:1px,color:#f8fafc
    style MERKLE fill:#022c22,stroke:#10b981,stroke-width:2px,color:#f8fafc
```

---

## 6. ERP Clearing & External Ledger Architecture

Once the PayPal capture is confirmed, KinetixRAG synchronizes settlement details to the general ledger clearing account.

```mermaid
graph LR
    subgraph BACKEND["FastAPI Procurement Engine"]
        CAP["Confirmed PayPal Capture<br/>(ID: CAP-XXXXX, Amount: $450.00 USD)"]
    end

    subgraph SYNC["Dual-Safety Ledger Connector"]
        CHK{"Safety Check:<br/>1. Is capture COMPLETED?<br/>2. Is secret authenticated?"}
        CAP --> CHK
    end

    subgraph LEDGER["Live Google Sheets ERP Ledger"]
        URL["Google Apps Script Web App<br/>(script.google.com/macros/s/.../exec)"]
        SHEET["Spreadsheet: PayPal ERP Accounting Ledger<br/>Tab: 'ERP Ledger'<br/>Columns: GL Account (2100) | Order ID | Capture ID | Amount | Timestamp"]
        CHK -- "Valid" --> URL
        URL --> SHEET
    end

    style BACKEND fill:#1e3a8a,stroke:#3b82f6,stroke-width:1px,color:#f8fafc
    style SYNC fill:#451a03,stroke:#f59e0b,stroke-width:1px,color:#f8fafc
    style LEDGER fill:#064e3b,stroke:#10b981,stroke-width:1px,color:#f8fafc
```
