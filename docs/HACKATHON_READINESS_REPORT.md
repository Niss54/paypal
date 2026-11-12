# Engineering readiness evidence

Reviewed 12 November 2026. This report covers the local working tree. A successful hosted health request does not establish that these local changes are deployed. Submission publication and the planned 2–3 minute video are separate delivery steps, not software defects.

## Changes

- Disabled the legacy Lightning-to-PayPal invoice adapter. It previously ignored the invoice amount, invented preimages and could report unknown payments as settled. The supported procurement flow uses Orders v2.
- Bound the report audit submitter to the authenticated caller. Client-supplied technician identifiers no longer impersonate the submitting account.
- Retained signature verification for Sandbox webhooks; simulation events remain unverified and cannot mutate real order state. Anonymous role headers and requester/supervisor identity overrides are restricted outside tests.
- Removed the client-side Lane A capture path for the critical pump. The guided simulation stops for separate supervisor approval. The self-approval test uses requester credentials rather than a forged identifier.
- Required an actual capture identifier and COMPLETED provider status before showing capture success or exporting it. No generated capture identifier substitutes for a missing receipt.
- Added the existing AI investigation and source inspection components to the procurement screen. This calls the existing chat API with the current session token. The quote table is still a disclosed fixture, not live supplier discovery.
- Removed the button that generated a repair report with fixed measurements and falsely labelled it non-synthetic. Sandbox checkout requires an uploaded report; generated reports remain simulation evidence.
- Removed source-code defaults for the Sheets URL, sync secret and spreadsheet. Removed automatic export from capture and SAP requests. Explicit exports require reviewer privileges and a stored, non-simulated completed capture; amount, currency and capture ID come from the database.
- Ledger acknowledgements now fail closed: missing/false success, malformed responses and non-finite amounts cannot produce a successful export result.
- Added the missing Maximo sync API route and protected ERP mutations with reviewer roles. Adapter responses retain their simulation/live configuration mode.
- Corrected landing-page guarantees, physical sensor proof, settlement, ERP and authorization language. Removed the misleading guaranteed-honor-period wording and unsupported supplier-disbursement claim.
- Added ledger-secret scanning and regression coverage. Exposed account credentials still need rotation at their external services; source deletion cannot revoke them.

## Observed verification

| Check | Observed result | Scope |
|---|---|---|
| Frontend Vitest | 82 passed, 19 files | Component/helper tests; not a live checkout |
| Next.js production build | Passed, including TypeScript and generated routes | Build before final text/report-shortcut removal; final rebuild tracked below |
| Focused earlier auth/webhook/capture suite | 33 passed | Local tests with provider responses mocked where applicable |
| Final affected backend checks | 52 passed | Auth, legacy provider, webhook identity, ledger export, ERP and secret scanning; two test-key-length warnings were isolated for follow-up |
| Optional GraphSAGE software tests | 45 passed | Model implementation tests, not predictive accuracy evidence |
| Live PayPal Sandbox test files | 6 passed | OAuth, order creation/retrieval and API behavior; no completed buyer-approved capture |
| Preflight | 4 PASS, 1 UNVERIFIED, 0 FAIL | Real Sandbox OAuth and Neo4j read; local policy/Merkle checks; ERP not externally verified |
| Hosted warm-up | Ready after 129.42 seconds, 12 attempts | Liveness and readiness only |
| Hosted access | Requester token, profile, incident and quotes HTTP 200; unauthenticated supervisor HTTP 401 | Existing hosted deployment |
| Secret scanner | 518 working files scanned, no pattern matches in initial run | Does not inspect credential revocation or prove history is clean |

The full backend run initially exceeded the wrapper's 300-second timeout. A diagnostic run exposed two authentication tests whose explicit test signing secret was shadowed by the operator's local JWT_SECRET. The test fixture now isolates that key. Final suite outcomes are recorded after completion; do not reuse the obsolete 526-test/100%-pass narration.

## Boundaries to preserve in the demonstration

1. An uploaded hash is report integrity, not independent sensor attestation. The prototype blocks production-money capture. Do not claim installed industrial hardware or ISO certification.
2. The Sandbox merchant receives the capture. A separate supplier payout is not established by this workflow.
3. GraphSAGE remains optional and disabled by default; accuracy and deployed-model claims are withdrawn. Its software tests do not validate industrial predictive accuracy.
4. SAP/Maximo/Sheets acknowledgements are not independently reconciled general-ledger postings. They are outside the core pitch.
5. Customer savings, pilot deployments and universal security guarantees have not been established. Do not invent them to strengthen the presentation.

## External release work

- Rotate the previously exposed PayPal Sandbox account password and Sheets sync secret in their owning services. Do not paste credentials into chats, source or README.
- Deploy the reviewed local changes and supply the private demo supervisor credential through the intended judging access channel.
- Complete a buyer-approved Sandbox authorize/capture rehearsal using a truthfully labelled submitted report. Record the returned order, authorization and capture identifiers without exposing tokens.
- Use the existing warm-up script before recording or live review; the observed cold start was over two minutes.

Use [the recording script](JUDGE_VIDEO_SCRIPT_3_MIN.md), [claim matrix](CLAIM_EVIDENCE_MATRIX.md) and [judge guide](../JUDGE_README.md) for a consistent account of what is demonstrated.
