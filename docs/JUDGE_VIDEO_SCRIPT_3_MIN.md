# KinetixRAG: under-three-minute submission cut

Target final runtime: **2:40–2:50**, including title cards. The official challenge page asks for a public YouTube video under three minutes. The existing five-minute narration needs a shorter cut and factual corrections, even if its delivery is polished.

Record the behavior available in the deployed build. Use the narration below only when the corresponding action is visible and succeeds. Do not call Auto Demo, a fixed quote rationale, or a stored screenshot a live AI or PayPal result. Never expose passwords, client secrets or bearer tokens.

## 0:00–0:15 | Product and audience

**Screen:** pump repair procurement console.

“An AI can propose an emergency repair. But a company still needs a rule for when payment can be captured. KinetixRAG adds that control to industrial procurement: No Evidence, No Capture.”

## 0:15–0:35 | Show the actual AI contribution

**Screen:** `/investigate`. Ask a fresh maintenance question, show its answer and open a returned citation. Verify the configured model responds before recording.

“Here, the AI investigation assistant answers a maintenance question using retrieved evidence. I can inspect its citations. The operator reviews that recommendation. For this payment demonstration, we use a clearly labelled pump incident and synthetic supplier quotes.”

**Accuracy rule:** the investigation and seeded procurement scenario are distinct steps. Do not claim the model automatically generated the quote table or work-order identifiers. If this answer is a replay, label it as a replay and provide separate evidence of the real AI call.

## 0:35–0:55 | Deterministic purchase policy

**Screen:** `/procurement`, quote evaluation and policy result.

“This four-hundred-and-fifty-dollar quote meets the five-hundred-dollar limit and service deadline. The alternatives fail budget or timing checks. Those decisions run outside the language model. This critical asset also requires a separate supervisor's approval.”

## 0:55–1:20 | PayPal authorization

**Screen:** create order, buyer approval in PayPal Sandbox, authorize, returned identifiers.

“We create a PayPal Sandbox order, obtain buyer approval and authorize the payment. This is an authorization hold, not escrow. PayPal recommends capture within the first three-day honor period; later capture depends on its risk checks and funding availability.”

## 1:20–1:40 | Rejected early capture

**Screen:** attempt capture without completion evidence; hold the actual response on screen.

“Now I request capture before submitting repair evidence. The server rejects it with HTTP four-zero-three. The response identifies the evidence gate. The application has not called PayPal to capture this order.”

**Accuracy rule:** an authentication error is not evidence of this gate. Confirm the server response reason before recording.

## 1:40–2:15 | Submitted evidence and separate approval

**Screen:** upload report and measurement, inspect evidence result, demonstrate rejected self-approval, then separate supervisor approval.

“I submit a repair report and post-repair measurement. The server checks the order details, policy threshold and report digest. This verifies the submitted record, not the authenticity of a physical sensor. The requester cannot approve its own payout. A separately authenticated supervisor reviews and approves it.”

**Accuracy rule:** the Sandbox exercise does not prove that an actual pump was repaired. Keep synthetic fixtures and submitted-report provenance visible. Do not relabel a demo file as independently verified operational evidence.

## 2:15–2:45 | Capture and close

**Screen:** confirmed Sandbox capture response, mode, capture ID and audit snapshot.

“With those gates satisfied, the application requests capture from PayPal. Here is the Sandbox result and capture identifier. The audit links the order, evidence and approval using SHA-two-fifty-six hashes and a Merkle root. KinetixRAG demonstrates a controlled payment boundary for AI-assisted repair procurement: recommendations inform the purchase; policy, evidence and approval control capture.”

If the final result is simulated, replace “Sandbox result” with “simulated result” and do not present it as proof of PayPal capture. A provider-backed recording must include genuine buyer approval and authorization.

## Corrections required in the existing five-minute voiceover

| Existing claim | Required correction |
| --- | --- |
| “99 percent of projects”, “most submissions”, “solve this forever”, “brand new primitive” | Remove. No comparative study or uniqueness proof is supplied. |
| Funds locked in PayPal escrow; zero risk | Authorization hold with the honor-period and funding caveat above. |
| Continuous live 20 kHz telemetry on P-101A | Illustrative pump scenario; distinguish replay/reference data from a live sensor. |
| Inner-race diagnosis, automatic RFQ federation, Bayesian confidence | The pump fixture describes outer-race context. Quote rationales and confidence numbers are seeded; do not call them fresh inference. |
| Physical proof of ISO compliance | Submitted report and policy measurement checks. The threshold is scenario-specific, not a certification. |
| Immutable ledger with logarithmic construction | Hashes and Merkle root; root construction O(N), tree depth O(log N), no independent immutable anchor. |
| Simultaneous live SAP/Maximo posting | Remove unless separately demonstrated against real configured tenants. |
| Cold-chain telemetry proves biologics safe at -18°C | Remove. The current prototype does not establish this domain-specific physical or regulatory conclusion. |
| 526 tests, 100% pass rate, every call live | Use only current observed counts, clearly separate mocked tests from live Sandbox tests, and disclose skips. |
| Production-grade, four unbreakable layers | Hackathon prototype with tested controls and stated limitations. |

Leave GraphSAGE, Lightning, Nostr, ERP, macroeconomic statistics and the second scenario out of this cut. They consume time needed to show the core evidence and payment sequence.
