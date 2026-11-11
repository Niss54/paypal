# GraphSAGE implementation review and evidence corrections

Reviewed on 2026-11-11. This replaces the previous “100% complete and verified” audit. It records source inspection, not a new benchmark or hosted deployment certification.

## What the source supports

| Component | Source | Supported statement |
| --- | --- | --- |
| Feature contract | `ml/graph_risk/schemas.py`, `features.py` | Seven named features and extraction/validation utilities. |
| Graph construction | `ml/graph_risk/graph_builder.py` | Orders observations and rejects edges from later to earlier timestamps. This alone does not prove leakage-free experimental design. |
| Model | `ml/graph_risk/model.py` | Two NumPy mean-aggregation layers, default hidden width 32, checkpoint serialization. |
| Training | `ml/graph_risk/train.py` | Training loop with class weighting and validation-driven stopping. |
| Fixture | `ml/graph_risk/tests/fixtures/industrial_telemetry_fixture.json` | Seven representative rows and a four/two/one split, not an established industrial benchmark. |
| Inference | `ml/graph_risk/inference.py` | Explicit unavailable states and uncalibrated advisory scores. |
| Service | `backend/app/services/graph_risk.py` | Disabled by default; accepts a checkpoint. The prediction service currently passes no graph. |
| Explanations | `ml/graph_risk/explain.py` | Model attribution code exists; hosted graph attribution needs separate evidence. |

## Withdrawn claims

The previous audit asserted 451 checks at 100% pass rate, GraphSAGE validation PR-AUC 0.960, ROC-AUC 0.975, F1 0.933, a four-point advantage over Random Forest, 4.8 ms latency, 42.6 MB memory growth and a deployment memory guarantee. Those claims are **withdrawn as submission evidence**.

The inspected ML directory contains implementation and tests but no report reproducing those benchmarks. The fixture's training partition contains only negative labels; validation and test contain only positive labels. It cannot support the reported accuracy comparison. The training smoke test checks execution and checkpoint creation, not those metrics.

The former phase table named historical commits and aggregate counts. It did not establish a deployed checkpoint, calibrated predictions or a fresh suite result. Current observed results belong in the [readiness report](HACKATHON_READINESS_REPORT.md).

## Reproducible checks

Run optional ML tests separately from default root collection:

```bash
python -m pytest ml/graph_risk/tests -q
python -m pytest tests/backend/test_graph_risk_api.py tests/test_e2e_graph_risk.py -q
```

Record command, revision, environment, passes, skips and failures. Passing tests establishes covered software behavior only. Accuracy claims also need a dataset manifest, checkpoint digest, exact evaluation command and generated results.

Keep this module out of the core pitch. Demonstrate configured AI investigation and the PayPal evidence/approval boundary instead. See the corrected [model card](GRAPH_RISK_MODEL_CARD.md).

