# KinetixRAG: technical questions and honest answers

## What is the product?

An industrial repair procurement prototype. AI helps investigate a fault, policy checks a proposed purchase, and the application requests PayPal capture only after evidence validation and required supervisor approval. The primary demonstration uses one pump repair.

## Why use PayPal?

The implementation uses the Orders v2 `AUTHORIZE` intent, buyer approval, authorization, delayed capture and void operations. This allows the application to withhold its capture request while evidence and approval are missing. An authorization is not escrow. PayPal recommends capture in the first 3-day honor period within the authorization's 29-day window; later capture depends on risk and funding availability. [Official documentation](https://developer.paypal.com/payment-methods/auth-honor/)

## Does the AI actually generate the procurement screen?

The repository has an AI investigation workflow in `agents/`, `retrieval/` and `/investigate`. The procurement cockpit uses a seeded incident, work order, quote narratives, rankings and confidence values, with optional graph lookup for pump context. Those values are not proof of a fresh model call. Demonstrate a fresh investigation answer with citations separately and disclose the handoff into the seeded payment scenario. The current prototype does not establish a fully autonomous incident-to-supplier procurement agent.

## Are the sensors and suppliers real?

The displayed pump and repair values are fixtures. The repository includes NASA IMS reference/replay material, but the procurement incident is not a live sensor stream from that dataset or an operating customer plant. Quotes are synthetic. A vendor name in a fixture does not imply a commercial partnership, certification or live quote API.

## Does a hash prove the repair happened?

No. A SHA-256 digest binds submitted bytes and can detect a mismatch against those bytes. The validator also checks order identifiers, scope, measurement and approval. It does not authenticate independent sensor hardware or establish the truth of a technician's report. Independent signed measurement acquisition and a trustworthy verifier are additional work before industrial deployment.

## What does the HTTP 403 prove?

A correctly authenticated capture request without qualifying evidence is rejected by the application. Verify the returned reason is the evidence gate. An authentication failure with the same HTTP status does not demonstrate that control. This does not block an operator who uses merchant credentials to call PayPal outside the application.

## Is supervisor approval independent?

The server checks roles and rejects approval by the order requester. The hosted deployment still needs separately controlled identities and credentials. Showing two personas operated by the same presenter demonstrates the code path, not an organization's real separation of duties.

## Are Sandbox and simulation the same?

No. A provider-backed Sandbox request reaches PayPal's test environment. Simulation returns local demonstration identifiers and does not establish a PayPal authorization or capture. Buyer approval and a confirmed authorization are required before a real Sandbox capture. Auto Demo, synthetic evidence and simulated approvals must be labelled in recordings.

## Where does the money go?

The Sandbox transaction uses the configured PayPal merchant account. A supplier quote label does not prove vendor onboarding, marketplace eligibility or production disbursement routing. The prototype does not claim approved merchant-of-record or multi-party production operations.

## Is the audit immutable?

No. The code computes stage hashes and a binary Merkle root for the audit snapshot. Changes can be detected by comparing against a previously trusted root. Someone controlling the database and root storage could rewrite both. Root construction is O(N); binary-tree depth is O(log N). A root alone does not implement an independently verified inclusion-proof protocol or a blockchain.

## Is GraphSAGE deployed and trained?

The repository contains a NumPy research implementation and tests. The service defaults to `ENABLE_GRAPH_RISK_MODEL=false`; enabling it without a compatible checkpoint does not produce a trained model. The current submission excludes it from the core pitch. Previously listed accuracy, latency and memory figures are not supported by a reproducible deployed-model evaluation in this review. See the [model card](docs/GRAPH_RISK_MODEL_CARD.md).

## Do SAP and Maximo receive real ledger entries?

Connector code exists, including simulated operation when external configuration is absent. No live enterprise tenant posting is established by a simulated connector response or an in-memory balanced ledger. Do not narrate these as live integrations without external acknowledgments from the configured tenant.

## Does the cold-chain scenario prove generalization?

It demonstrates an additional fixture. It does not establish live carrier telematics, biologic cargo safety, a real refrigeration repair or a validated temperature-based capture rule. It is excluded from the primary pitch while the pump scenario is evaluated.

## Do all automated tests reach PayPal?

No. Most tests use mocks or local data so failure cases are reproducible. Dedicated live Sandbox tests are credential- and network-dependent, and some cover only OAuth or order creation. Report pass, failure and skip counts from an actual run and identify the commands. See the [test snapshot](docs/CURRENT_TEST_SNAPSHOT.md).

## Is the code production-ready?

It is a substantial prototype with payment controls, tests and deployment configuration. Production readiness needs independent evidence provenance, operational identity management, recovery and reconciliation validation, production-provider onboarding, and observed deployment behavior. Neither a test count nor a polished video establishes these.

## What could lower the judging score?

The weakest point is the handoff from live AI investigation to a seeded procurement scenario. A judge may see two adjacent capabilities rather than a completed agentic workflow. Missing live Sandbox capture proof, inaccessible demo credentials, slow startup, unsupported claims, and a video over three minutes can also hurt. The strongest presentation shows the actual AI contribution, a server-side blocked capture, a valid separate approval and a truthfully labelled final result.

## What are the submission requirements?

The current [official challenge page](https://paypalaihackathon.devpost.com/) lists no prescribed tracks and includes a Best Use of Agentic Commerce prize. It asks for a functioning demo or complete run instructions, public open-source code with a license, AI-tool disclosure and a public YouTube demo under three minutes. Verify the final Devpost entry, repository visibility and video yourself; the presence of local files proves none of those publication states.
