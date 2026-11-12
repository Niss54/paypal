# KinetixRAG

**Evidence-gated authorization and capture for industrial repair procurement.**

An AI assistant helps investigate a machine fault. Deterministic policy checks the repair purchase. The application requests PayPal capture only after submitted completion evidence passes validation and a separate supervisor approves the critical-asset order.

The product rule is **No Evidence, No Capture**. This repository is a hackathon prototype, with explicit simulation and PayPal Sandbox paths.

[Hosted procurement demo](https://paypal-pink.vercel.app/procurement) · [AI investigation](https://paypal-pink.vercel.app/investigate) · [API documentation](https://paypal-y2jk.onrender.com/docs) · [Judge guide](JUDGE_README.md) · [MIT license](LICENSE)

## What to evaluate

1. Investigate a maintenance question using the AI/RAG workflow and inspect its returned citations.
2. Open the pump repair scenario in `/procurement`. Its incident and three supplier quotes are demonstration fixtures. The $450 quote satisfies the $500 policy cap; alternative quotes exercise budget and service-time rejection.
3. Create a PayPal Sandbox order with `intent: AUTHORIZE`, complete buyer approval, and authorize the order.
4. Attempt capture before evidence is present. The application rejects the request with HTTP 403.
5. Submit completion evidence and obtain approval from an authenticated supervisor distinct from the requester.
6. Request capture and inspect the returned payment identifiers and audit snapshot. A simulated result must remain labelled simulated.

**PayPal semantics:** creating an order does not itself place a hold. Buyer approval and authorization precede capture. An authorization can remain valid for up to 29 days; PayPal recommends capture in the initial 3-day honor period. Later capture depends on risk checks and funding availability. This is an authorization hold, not escrow or a guarantee of payment. [PayPal authorization documentation](https://developer.paypal.com/payment-methods/auth-honor/)

## What is implemented, and what is demonstrated

| Component | Current scope |
| --- | --- |
| AI investigation | LLM and retrieval implementation in `agents/`, `retrieval/`, and `/investigate`. A live answer requires configured providers and supporting data. Show a fresh answer to establish live AI use. |
| Procurement scenario | Seeded pump incident, work-order identity, quote rankings and narrative. Optional Neo4j traversal enriches context. This screen alone does not prove a fresh model diagnosis or autonomous supplier discovery. |
| Spending policy | Server-side amount, currency, supplier, service-time and critical-asset checks using decimal amounts. LLM text cannot change these checks. |
| PayPal | REST client for OAuth, order creation, authorization, capture, void and webhooks. Provider-backed Sandbox results require valid credentials and buyer approval. Auto Demo is a simulation. |
| Evidence | Validates submitted identifiers, maintenance checklist, measurement and report digest. A hash binds submitted bytes; it does not establish that a sensor is authentic or that a physical repair occurred. |
| Supervisor approval | Server-side role and separation-of-duties checks. Use separate configured identities when testing the Sandbox flow. |
| Audit | SHA-256 stage hashes and a binary Merkle root summarize an audit snapshot. This is tamper-evident relative to a trusted saved root, not immutable storage or external timestamping. Building the root is O(N); tree depth is O(log N). |
| GraphSAGE | Optional advisory research module, disabled by default. No trained deployed checkpoint or validated predictive-accuracy claim is required for this demo. |
| SAP, Maximo and cold chain | Additional prototype code and fixtures. They are outside the core submission demonstration; no live enterprise posting, supplier partnership or validated cold-chain deployment is claimed. |

The pump values of 4.82 mm/s before repair, 1.25 mm/s after repair, and a 4.50 mm/s policy limit are illustrative scenario values. They are not live measurements or universal ISO acceptance limits. NASA IMS reference material and replay fixtures must not be presented as a live installation on pump P-101A. See the [claim evidence matrix](docs/CLAIM_EVIDENCE_MATRIX.md).

## Run locally

Use Python 3.11 or 3.12 and a Node.js version supported by the installed Next.js package, at least Node.js 20.9. The dependency lockfile is in `frontend/`.

```bash
git clone https://github.com/Niss54/paypal.git
cd paypal
python -m venv .venv
# Activate .venv using your shell's activation command.
python -m pip install -r requirements-dev.txt
```

Copy `.env.example` to `.env`. For local simulation, keep `DEMO_STANDALONE=true`. Set a unique `JWT_SECRET`, enable `DEMO_AUTH_ENABLED=true`, and supply distinct private `DEMO_AGENT_PASSWORD`, `DEMO_SUPERVISOR_PASSWORD`, `DEMO_BUYER_PASSWORD` and `DEMO_TECH_PASSWORD` values for the personas you will use. Do not publish those values. Keep local credentials separate from hosted credentials. Production requires deliberate authentication and secret configuration.

For provider-backed testing, configure your own `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET`, and use `PAYPAL_API_BASE_URL=https://api-m.sandbox.paypal.com`. Use a separate Sandbox buyer account to approve checkout. `PAYPAL_WEBHOOK_ID` is needed to verify registered webhook delivery. Keep all testing in Sandbox.

```bash
python -m uvicorn backend.app.main:app --env-file .env --host 127.0.0.1 --port 8000 --reload
```

In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend/.env.local` before starting the frontend if it is configured for a hosted backend. Open [local procurement](http://localhost:3000/procurement) and [local API docs](http://localhost:8000/docs).

For live AI investigation, configure the model provider used by `agents/llm.py`, including `GROQ_API_KEY` for the Groq path. Full graph/vector retrieval also needs Neo4j, Qdrant and indexed source material. Follow [deployment and service configuration](docs/DEPLOYMENT.md). Standalone fixtures are useful for exploring controls, but are not proof of a live external AI or database call.

## Verify

```bash
python -m pytest tests
python -m pytest ml/graph_risk/tests
python scripts/secret_scan.py
python scripts/verify_sandbox.py
```

```bash
npm --prefix frontend test
npm --prefix frontend run build
```

See [current test evidence](docs/CURRENT_TEST_SNAPSHOT.md) for observed results and limitations. Unit tests, simulated lifecycle tests and live Sandbox tests are different evidence. A passing OAuth/order-creation test does not establish a completed buyer-approved authorization and capture. Credential-dependent tests can skip; skipped tests are not passes.

Before recording or judging, request the hosted backend's `/api/health/live`, then `/api/health/ready`, and wait for the dependencies needed by the selected flow. A liveness response alone is not payment readiness. Run preflight and inspect every failure or simulation label. Never describe its output as an unconditional all-green guarantee.

## Hackathon submission

The [official challenge page](https://paypalaihackathon.devpost.com/) lists no prescribed tracks. Best Use of Agentic Commerce is a prize category. The listed deadline is **12 November 2026, 12:00 PST**, equivalent to **13 November 2026, 01:30 IST**. Recheck the official page before submitting.

The submission needs a functional demo or complete run instructions, a public open-source repository with a visible license, identification of the AI tools used, and a publicly visible YouTube demo **under three minutes**. Repository source alone does not prove that the Devpost submission or video has been published.

Use the [under-three-minute recording script](docs/JUDGE_VIDEO_SCRIPT_3_MIN.md) for the planned 2–3 minute video. Keep the pump incident, fresh AI answer with sources, authorization, rejected early capture, evidence, supervisor approval and final result in that cut. AI investigation is also available inside the procurement screen.

## Security and limitations

If a Sandbox password was previously published, remove it from the current files and rotate it in the PayPal account. A clean scan cannot revoke a leaked password or remove it from Git history. Do not distribute privileged demo passwords in the README.

The legacy Lightning-to-PayPal invoice adapter is disabled: satoshi invoices do not define a safe USD repair payment. Use the Orders v2 procurement path. Optional ledger exports use stored completed capture values, require reviewer privileges, and never automatically turn a simulation into a financial posting. Configure the Sheets connector privately and rotate its previously exposed sync secret before enabling it.

This prototype has not demonstrated independent sensor attestation, real industrial deployment, externally anchored immutable logs, calibrated failure prediction, live SAP/Maximo settlement, or measured savings for customers. Direct use of merchant credentials outside this application is outside its capture gate. These are deployment and product-development boundaries, not features proven by the demo.

Licensed under the [MIT License](LICENSE). Third-party attribution is in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
