"""Tests for Binary Merkle Tree Cryptographic Audit Ledger (FIX 3).
Verifies logarithmic verification depth, deterministic root generation, and tamper detection.
"""
import hashlib
import pytest
from backend.app.services.procurement.orchestrator import ProcurementOrchestrator


def test_merkle_root_empty_leaves():
    root, depth = ProcurementOrchestrator.compute_merkle_root([])
    assert root == "0" * 64
    assert depth == 0


def test_merkle_root_single_leaf():
    leaf = hashlib.sha256(b"stage-1").hexdigest()
    root, depth = ProcurementOrchestrator.compute_merkle_root([leaf])
    assert root == leaf
    assert depth == 1


def test_merkle_root_power_of_two_leaves():
    leaves = [hashlib.sha256(f"stage-{i}".encode()).hexdigest() for i in range(4)]
    root, depth = ProcurementOrchestrator.compute_merkle_root(leaves)
    assert len(root) == 64
    assert depth == 2  # log2(4) = 2


def test_merkle_root_odd_leaves_handling():
    # 7 stages (exact count of our causal audit ledger)
    leaves = [hashlib.sha256(f"stage-{i}".encode()).hexdigest() for i in range(7)]
    root, depth = ProcurementOrchestrator.compute_merkle_root(leaves)
    assert len(root) == 64
    assert depth == 3  # ceil(log2(7)) = 3


def test_merkle_root_tamper_detection():
    leaves = [hashlib.sha256(f"stage-{i}".encode()).hexdigest() for i in range(7)]
    original_root, _ = ProcurementOrchestrator.compute_merkle_root(leaves)

    # Tamper with stage 3
    tampered_leaves = list(leaves)
    tampered_leaves[3] = hashlib.sha256(b"tampered-stage-3").hexdigest()
    tampered_root, _ = ProcurementOrchestrator.compute_merkle_root(tampered_leaves)

    assert original_root != tampered_root, "Tampering with any stage must invalidate the Merkle root!"


def test_merkle_root_deterministic():
    leaves = [hashlib.sha256(f"stage-{i}".encode()).hexdigest() for i in range(7)]
    root1, depth1 = ProcurementOrchestrator.compute_merkle_root(leaves)
    root2, depth2 = ProcurementOrchestrator.compute_merkle_root(leaves)
    assert root1 == root2
    assert depth1 == depth2


def test_merkle_inclusion_proof_verification():
    leaves = [hashlib.sha256(f"stage-{i}".encode()).hexdigest() for i in range(7)]
    root, depth = ProcurementOrchestrator.compute_merkle_root(leaves)

    # Generate and verify proof for each leaf
    for i, leaf in enumerate(leaves):
        proof = ProcurementOrchestrator.generate_merkle_proof(leaves, i)
        assert len(proof) == depth
        is_valid = ProcurementOrchestrator.verify_merkle_proof(leaf, proof, root)
        assert is_valid is True

    # Tampered leaf must fail verification
    proof_0 = ProcurementOrchestrator.generate_merkle_proof(leaves, 0)
    fake_leaf = hashlib.sha256(b"fake-stage-0").hexdigest()
    assert ProcurementOrchestrator.verify_merkle_proof(fake_leaf, proof_0, root) is False


def test_merkle_cve_2012_2459_duplicate_leaf_mitigation():
    """Verify that [A, B, C] and [A, B, C, C] do NOT produce the same Merkle root."""
    hA = hashlib.sha256(b"leaf-A").hexdigest()
    hB = hashlib.sha256(b"leaf-B").hexdigest()
    hC = hashlib.sha256(b"leaf-C").hexdigest()

    root_3, _ = ProcurementOrchestrator.compute_merkle_root([hA, hB, hC])
    root_4_dup, _ = ProcurementOrchestrator.compute_merkle_root([hA, hB, hC, hC])

    assert root_3 != root_4_dup, "CVE-2012-2459 duplicate leaf collision must be prevented by domain-separated odd padding!"
