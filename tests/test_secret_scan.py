"""
Unit test for Pre-submission Secret and Credential Scanning (Task 9.1 / SEC-01 / SEC-02 / SEC-06).
Ensures no secrets, API keys, or private keys are committed into git-tracked files.
"""

import os
import subprocess
import pytest
from scripts.secret_scan import DOCUMENTED_PASSWORD, scan_repository


def test_documented_password_pattern_detects_public_passwords():
    assert DOCUMENTED_PASSWORD.search("Sandbox Password: `unsafe-demo-password`")
    assert DOCUMENTED_PASSWORD.search("**Password**: `unsafe-demo-password`")
    assert DOCUMENTED_PASSWORD.search("| Password | `unsafe-demo-password` |")
    assert not DOCUMENTED_PASSWORD.search("PAYPAL_CLIENT_SECRET=your_paypal_sandbox_client_secret_here")


def test_scanner_detects_markdown_password_without_revealing_value(tmp_path, monkeypatch):
    exposed = "must-never-appear-in-findings"
    (tmp_path / "README.md").write_text(f"**Password**: `{exposed}`\n", encoding="utf-8")
    monkeypatch.setattr(subprocess, "check_output", lambda *args, **kwargs: "README.md\0")
    findings = scan_repository(tmp_path)
    assert len(findings) == 1
    assert findings[0]["type"] == "Documented Password"
    assert exposed not in repr(findings)


def test_word_example_cannot_hide_a_real_documented_password(tmp_path, monkeypatch):
    (tmp_path / "README.md").write_text("Password: `example-but-actually-active`", encoding="utf-8")
    monkeypatch.setattr(subprocess, "check_output", lambda *args, **kwargs: "README.md\0")
    assert scan_repository(tmp_path)[0]["type"] == "Documented Password"


def test_scanner_includes_new_nonignored_files_and_redacts_api_keys(tmp_path, monkeypatch):
    fake_key = "ghp_" + "Z" * 36
    (tmp_path / "new.txt").write_text(fake_key, encoding="utf-8")
    def git_files(command, **kwargs):
        assert "--others" in command and "--exclude-standard" in command
        return "new.txt\0"
    monkeypatch.setattr(subprocess, "check_output", git_files)
    findings = scan_repository(tmp_path)
    assert findings[0]["type"] == "GitHub Token"
    assert fake_key not in repr(findings)


def test_scanner_flags_tracked_environment_variants(tmp_path, monkeypatch):
    monkeypatch.setattr(subprocess, "check_output", lambda *args, **kwargs: ".env.production\0.env.example\0")
    findings = scan_repository(tmp_path)
    assert [finding["file"] for finding in findings] == [".env.production"]

def test_no_exposed_secrets_in_git_tracked_files():
    """Verify that zero exposed production secrets or credentials exist in git-tracked files."""
    findings = scan_repository()
    assert findings == [], f"Found exposed credentials in git-tracked files: {findings}"

def test_env_files_are_untracked_and_gitignored():
    """Verify .env is gitignored and not in git index."""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    # Check .gitignore exists and contains .env
    gitignore_path = os.path.join(root_dir, ".gitignore")
    assert os.path.exists(gitignore_path), ".gitignore missing!"
    with open(gitignore_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert ".env" in content, ".env must be explicitly ignored in .gitignore!"

    # Check git ls-files does not list .env
    try:
        git_tracked = subprocess.check_output(
            ["git", "ls-files"], cwd=root_dir, text=True
        ).splitlines()
    except (subprocess.CalledProcessError, FileNotFoundError):
        pytest.skip("Git index unavailable in source archive")
    assert ".env" not in git_tracked, "CRITICAL: .env is tracked in git index!"
