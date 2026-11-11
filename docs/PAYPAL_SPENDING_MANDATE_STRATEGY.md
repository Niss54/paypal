# PayPal submission strategy: evidence-gated repair procurement

The product is AI-assisted industrial repair procurement whose application requests PayPal capture only after evidence validation and required supervisor approval. Keep the submission on this one workflow.

The competition has no prescribed tracks. Best Use of Agentic Commerce is an award category. The submission deadline is November 12, 2026, 12:00 PM Pacific Time, or November 13, 2026, 1:30 AM IST. Check the [official rules](https://paypalaihackathon.devpost.com/rules).

## What to demonstrate

1. Show a fresh AI investigation answer and inspect a citation. Describe the operator's review and handoff to the fixture-based payment demonstration accurately.
2. Evaluate the pump's $450 quote against its $500 scenario policy. Show alternative quote rejection reasons.
3. Create an AUTHORIZE order in PayPal Sandbox, complete buyer approval and authorize. Show actual order and authorization identifiers.
4. Attempt capture without evidence. Show an evidence-specific server rejection, not an authentication failure.
5. Upload a report and submitted measurement. Show validation and a separately authenticated supervisor's approval.
6. Capture through the application and show the actual Sandbox response, mode and audit snapshot.

The [video script](JUDGE_VIDEO_SCRIPT_3_MIN.md) targets 2:40–2:50. The original five-minute recording needs a shorter cut and factual corrections. The [challenge page](https://paypalaihackathon.devpost.com/) requires a public YouTube video under three minutes.

## Engineering distinction

The model proposes or explains. `SpendingMandateEngine` evaluates server-owned policy using decimal values. The orchestrator binds quote and order; the evidence controller checks completion evidence and required approval before requesting capture.

A finite prompt-pattern scanner is not a universal prompt-injection defense. The stronger boundary is that model prose cannot change the server-owned amount, policy or authenticated approval identity. Demonstrate the cases actually covered by current tests.

The application uses PayPal authorization and capture APIs. Creating an order is not itself authorization. This is an authorization hold, not escrow. Capture is most reliable during the first three-day honor period; later capture depends on risk and funding availability. [PayPal documentation](https://developer.paypal.com/payment-methods/auth-honor/)

## Corrections to the earlier strategy

- Competitor-behavior estimates, “first” or unique-product assertions and numerical winning probabilities had no comparative evidence.
- Certified vendors, FDA-backed science, protected biologics and a 3,111-times ROI were unsupported by deployment evidence.
- AG Grid, APIMatic and Channel3 usage must be demonstrated before claiming implemented sponsor integrations. A generic table or OpenAPI schema alone does not prove product use.
- Payload adapters do not prove live SAP/Maximo posting, tax compliance or external accounting reconciliation.
- Fixed test totals, sub-second payment latency and “zero unauthorized payments” exceeded the evidence.

Those claims are removed from the recommended pitch. GraphSAGE, Lightning, Nostr, ERP and cold chain remain separate or optional prototype work.

## Judge-facing evidence

Use the [claim matrix](CLAIM_EVIDENCE_MATRIX.md), [judge guide](../JUDGE_README.md) and [readiness report](HACKATHON_READINESS_REPORT.md). Preserve a Sandbox trace with order/authorization/capture IDs, the evidence rejection, accepted report digest and separate approval identity. Redact tokens and credentials.

Before submission, verify the public repository has final changes and a visible license, the hosted build matches the recording, the video is public and Devpost confirms entry. Local tests cannot establish these external states.

