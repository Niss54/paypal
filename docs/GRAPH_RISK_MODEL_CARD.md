# GraphSAGE research module: model card

Reviewed against source on 2026-11-11. This optional module is **disabled by default** and is outside the core PayPal submission claim. The repository does not establish a deployed trained checkpoint or validated industrial failure prediction.

## Architecture supported by code

[`model.py`](../ml/graph_risk/model.py) implements two mean-aggregation layers in **NumPy**, with separate self and neighbor projections, ReLU in the first layer and sigmoid output in the second. `GraphSAGEConfig` defaults to seven input features and 32 hidden channels. The training smoke test explicitly uses 16 hidden channels. These are configurations, not evidence of a deployed model.

The previous PyTorch/PyG runtime description, 801-parameter count, measured 4.8 ms inference and 42.6 MB memory usage are withdrawn. The code uses NumPy; no supporting runtime benchmark artifact accompanies those measurements.

[`schemas.py`](../ml/graph_risk/schemas.py) defines the ordered input contract:

1. `vibration_rms_mm_s`
2. `vibration_peak_mm_s`
3. `vibration_crest_factor`
4. `vibration_kurtosis`
5. `bearing_temp_c`
6. `temp_rate_of_change_c_per_hr`
7. `frequency_dominant_hz`

Feature names and units do not prove values were measured by calibrated sensors or extracted from raw NASA recordings.

## Data and evaluation limits

The checked-in [industrial fixture](../ml/graph_risk/tests/fixtures/industrial_telemetry_fixture.json) contains seven representative observations named after NASA IMS Test 2. Its split contains four training nodes, two validation nodes and one test node. All four training labels are zero; validation and test labels are one. That split cannot establish useful generalization or a comparative industrial benchmark.

The metadata names NASA and a 24-hour horizon. It does not supply a reproducible raw-record-to-feature transformation, sensor calibration record or independent labels for every supplied feature. Treat it as a test fixture. Do not claim its temperatures, vibration values or P-101A identity are verified NASA measurements.

[`test_train.py`](../ml/graph_risk/tests/test_train.py) checks that training runs and writes a checkpoint. [Baseline tests](../ml/graph_risk/tests/test_baseline.py) use synthetic data. These check software behavior, not the former model comparison.

The previous accuracy table, including GraphSAGE validation PR-AUC 0.960 and its claimed advantage over Random Forest, is withdrawn. No reproducible evaluation artifact supporting that table was found in the inspected ML directory. No replacement accuracy number is asserted.

Future evaluation needs raw-data provenance, preprocessing/split manifests, multiple independent failure runs, both classes in evaluation partitions, a checkpoint digest, baseline results and calibration assessment.

## Inference and explanations

[`inference.py`](../ml/graph_risk/inference.py) reports disabled, untrained, incompatible-feature and inference-error states. Available predictions carry `calibrated: false` and `is_advisory: true`. A sigmoid output is an uncalibrated score, not a measured probability of failure.

[`explain.py`](../ml/graph_risk/explain.py) implements bounded predecessor attribution. This describes model sensitivity, not physical causation. The current backend service invokes inference without a graph argument, so hosted neighborhood attribution is not established by the explainer's existence.

## Deployment and use

[`graph_risk.py`](../backend/app/services/graph_risk.py) defaults `ENABLE_GRAPH_RISK_MODEL` to false and looks for a checkpoint. Enabling the flag alone does not train or validate a model.

Scores must not approve purchases, bypass payment gates, certify a repair or replace a safety instrument. No validated 24-hour prediction, ISO certification, memory guarantee or production readiness is claimed.

See the [claim matrix](CLAIM_EVIDENCE_MATRIX.md) and [current readiness report](HACKATHON_READINESS_REPORT.md).

