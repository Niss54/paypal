# KinetixRAG: judge evaluation guide

**Product:** evidence-gated industrial repair procurement using PayPal authorization and capture.

**One sentence:** AI assists the repair investigation; deterministic policy and a separate supervisor control when the application requests PayPal capture.

[Procurement demo](https://paypal-pink.vercel.app/procurement) · [AI investigation](https://paypal-pink.vercel.app/investigate) · [API docs](https://paypal-y2jk.onrender.com/docs) · [Local setup](README.md#run-locally)

## Before evaluation

The backend may need time to start. Check `/api/health/live`, then `/api/health/ready`; review the returned dependency states. The preflight command is `python scripts/verify_sandbox.py`. Its simulation checks and provider-backed checks must be interpreted separately.

Use your own PayPal Sandbox buyer account. Separate requester and supervisor identities must be configured privately for the approval demonstration. The repository does not provide privileged login passwords. Auto Demo is a guided simulation and is not proof that PayPal captured a payment.

## Three-minute path

| Time | Action | What it establishes |
| --- | --- | --- |
| 0:00–0:25 | In `/investigate`, ask a pump maintenance question and show the returned answer with citations. | A fresh model response and evidence, if the provider is configured. A stored response or fixture must be labelled accordingly. |
| 0:25–0:50 | Open `/procurement`, identify the seeded pump incident, and compare the three synthetic quotes. Evaluate the $450 quote against the $500 cap. | Policy checks and a critical-asset approval requirement. The fixture is not a newly generated diagnosis or live vendor bid. |
| 0:50–1:20 | Create a Sandbox order, complete buyer approval, then authorize it. | A PayPal order and authorization. Show returned identifiers, without credentials. |
| 1:20–1:40 | Attempt capture before submitting evidence. | HTTP 403 from the server. Confirm the rejection is the evidence gate, not an unrelated login or connectivity error. |
| 1:40–2:20 | Submit the report and measurement. Attempt self-approval, then use the separate supervisor identity. | Evidence validation and separation of duties. The report is submitted evidence; the application does not attest a physical sensor. |
| 2:20–2:45 | Request gated capture and inspect its status, capture ID and audit snapshot. | Provider-backed Sandbox capture only if the response is non-simulated and PayPal confirms it. Otherwise describe a simulation. |

Do not show an edited or simulated successful result as a live provider call. If checkout takes longer, rehearse it or label time compression while retaining the important steps.

## Exact interpretation of the result

- PayPal authorization is a hold, not escrow. Creating the order does not create the hold. The first three days are the recommended honor period, and later capture depends on PayPal risk checks and funding availability. [PayPal documentation](https://developer.paypal.com/payment-methods/auth-honor/)
- The control applies to captures through this application. It does not prevent an operator with merchant credentials from calling PayPal independently.
- The pump scenario, supplier quotes, scores and failure forecast are demonstration inputs. The procurement screen can retrieve graph context but does not itself prove new LLM reasoning.
- A report digest checks the bytes received. It cannot establish that a technician told the truth or that a sensor is independently authenticated.
- The audit has a hash chain and a binary Merkle root. A trusted previously saved root can reveal changes. No external append-only anchoring is demonstrated.
- GraphSAGE is optional and disabled by default. SAP, Maximo and cold chain are outside this demonstration. No trained hosted GraphSAGE or real ERP posting is claimed.

## Reproduce the controls

```bash
python -m pytest tests/test_spending_mandate_v2.py tests/test_evidence_gating.py tests/test_paypal_api_endpoints.py tests/test_adversarial_judge_scenarios.py tests/backend/test_auth_elevation_hardening.py
python -m pytest tests/test_paypal_sandbox_live.py tests/test_paypal_sandbox_e2e_lifecycle.py
python scripts/secret_scan.py
npm --prefix frontend test
npm --prefix frontend run build
```

The live Sandbox files require valid credentials and network access. Read their individual test names: order creation and retrieval are not evidence of completed capture. Current observed results belong in [CURRENT_TEST_SNAPSHOT.md](docs/CURRENT_TEST_SNAPSHOT.md), not permanent pass-count badges.

For code mappings and remaining limitations, read the [claim evidence matrix](docs/CLAIM_EVIDENCE_MATRIX.md) and [technical FAQ](JUDGE_DEFENSE_AND_FAQ.md).
