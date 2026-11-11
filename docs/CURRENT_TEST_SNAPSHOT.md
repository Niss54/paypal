# Test evidence: superseded snapshot

The previous snapshot is withdrawn as **current submission evidence**. It mixed historical transcripts, build-route counts and claims about live services. Its “392 automated checks,” “57 tests passing,” and “100% clean / zero secrets” labels must not be quoted as the current state.

Fresh observed commands, counts, skips and limitations are recorded in [HACKATHON_READINESS_REPORT.md](HACKATHON_READINESS_REPORT.md). Earlier prose does not prove the final working tree passes.

## Collecting a fresh snapshot

```bash
python -m pytest tests -q
python -m pytest ml/graph_risk/tests -q
python scripts/secret_scan.py
npm --prefix frontend test
npm --prefix frontend run build
```

Root pytest configuration collects `tests/`, not `ml/graph_risk/tests/`. Record them separately. Some tests use mocks; live Sandbox tests require configured credentials and network access and may skip. A provider order-creation test is not a complete buyer-approval, authorization and capture test.

For each run, preserve revision or working-tree state, command, exit code, pass/skip/failure counts and environment mode. State which external services were actually contacted. Building twelve routes is one build check, not twelve payment tests.

A clean credential scan means only that its patterns found no matches in scanned working files. It does not prove a password was never exposed in git history. Removal and rotation are separate actions.

The [claim matrix](CLAIM_EVIDENCE_MATRIX.md) defines what each evidence type supports.

