#!/usr/bin/env python3
"""
Pre-submission Secret and Credential Scanner for KinetixRAG.
Verifies SEC-01 and Task 9.1:
- Scans tracked and non-ignored new files for likely exposed credentials.
- This heuristic scan does not prove credentials were never published in history.
"""

import os
import re
import sys
import subprocess

PATTERNS = {
    "Hardcoded Ledger Secret": re.compile(r"(?:ERP_SYNC_SECRET\s*=\s*[^\s\"']{8,}|DEFAULT_SECRET\s*=\s*[\"'][^\"']{8,}[\"'])"),
    "Google API Key": re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
    "GitHub Token": re.compile(r"(?:ghp_[0-9A-Za-z]{36}|github_pat_[0-9A-Za-z_]{82})"),
    "Groq API Key": re.compile(r"gsk_[0-9A-Za-z]{48}"),
    "OpenAI API Key": re.compile(r"sk-[a-zA-Z0-9]{48}"),
    "Private Key Block": re.compile(r"-----BEGIN (?:RSA|OPENSSH|EC|DSA) PRIVATE KEY-----"),
    "Hardcoded Admin Key Assignment": re.compile(r"(?i)(?:ADMIN_KEY|INVOICE_KEY|PRIVATE_KEY)\s*=\s*['\"][a-f0-9]{32,}['\"]"),
}

DOCUMENTED_PASSWORD = re.compile(
    r"(?i)\b(?:sandbox\s+)?(?:account\s+|test\s+)?(?:password|passcode|credential)"
    r"\s*(?:\*{1,2}|__)?\s*[:|](?!=)\s*(?:\*{1,2}|__)?\s*[`\"']?([^`\"'\s|<>\(\):,;]+)"
)

EXPOSED_CREDENTIAL_KEYWORDS = re.compile(
    r"(?i)(?:btn-pwd|copy\s+pass|copyToClipboard\([^)]*pwd\)|a\+\)n46B6)"
)

EXCLUDE_DIRS = {
    ".git",
    ".agents",
    ".cursor",
    ".vscode",
    "node_modules",
    ".venv",
    "__pycache__",
    ".next",
    ".pytest_cache",
    "artifacts",
}

EXCLUDE_FILES = {
    "package-lock.json",
    ".env.example",
    ".env.machine-money.example",
    "secret_scan.py",
}

def scan_repository(root_dir=None):
    findings = []
    root_dir = os.path.abspath(root_dir or os.path.join(os.path.dirname(__file__), ".."))

    print(f"Scanning tracked and non-ignored new files at: {root_dir}")

    # 1. Get all git-tracked files (with unzipped archive fallback)
    try:
        git_tracked = subprocess.check_output(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            cwd=root_dir, text=True, stderr=subprocess.DEVNULL
        ).split("\0")
        git_tracked = list(dict.fromkeys(path for path in git_tracked if path))
    except Exception:
        git_tracked = []

    if not git_tracked:
        has_git_dir = os.path.exists(os.path.join(root_dir, ".git"))
        print("Note: git ls-files returned 0 files (e.g. unzipped submission archive). Scanning filesystem tree directly...")
        for dirpath, dirnames, filenames in os.walk(root_dir):
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS and not d.startswith(".")]
            for fn in filenames:
                # If in a dev repo with .git, do not treat local untracked .env as committed
                if has_git_dir and fn == ".env":
                    continue
                rel = os.path.relpath(os.path.join(dirpath, fn), root_dir).replace("\\", "/")
                git_tracked.append(rel)

    # Verify .env is NOT tracked
    for f in git_tracked:
        basename = os.path.basename(f)
        if (basename == ".env" or basename.startswith(".env.")) and not basename.endswith(".example"):
            findings.append({
                "type": "TRACKED_ENV_FILE",
                "file": f,
                "line": 0,
                "content": "Environment credential file is tracked or included in submission"
            })

    # Verify .gitignore contains .env
    gitignore_path = os.path.join(root_dir, ".gitignore")
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            gitignore_content = f.read()
            if ".env" not in gitignore_content:
                findings.append({
                    "type": "GITIGNORE_MISSING_ENV",
                    "file": ".gitignore",
                    "line": 0,
                    "content": ".env is missing from .gitignore!"
                })

    # 2. Scan content of all git-tracked files
    scanned_files = 0
    for relpath in git_tracked:
        if any(part in EXCLUDE_DIRS for part in relpath.replace("\\", "/").split("/")):
            continue
        if os.path.basename(relpath) in EXCLUDE_FILES:
            continue

        filepath = os.path.join(root_dir, relpath)
        if not os.path.isfile(filepath):
            continue

        scanned_files += 1
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line_idx, line in enumerate(f, 1):
                    for label, pattern in PATTERNS.items():
                        match = pattern.search(line)
                        if match:
                            findings.append({
                                "type": label,
                                "file": relpath,
                                "line": line_idx,
                                "content": "Credential-like value detected (redacted)",
                            })
                    if relpath.lower().endswith((".md", ".txt", ".ts", ".tsx", ".js", ".jsx", ".py", ".json", ".html")):
                        if "test" not in relpath.lower() and "fixture" not in relpath.lower():
                            documented = DOCUMENTED_PASSWORD.search(line)
                            if documented:
                                value = documented.group(1).strip().lower()
                                placeholders = {
                                    "example", "placeholder", "redacted", "unset", "none", "n/a", "***", "[redacted]",
                                    "string", "str", "required", "true", "false", "null", "undefined", "type",
                                    "demo_agent_password", "demo_supervisor_password", "demo_buyer_password",
                                    "demo_tech_password", "demo_finance_password", "demo_auditor_password",
                                    "demo_operator_password", "demo_payment_password", "private", "configured",
                                    "operator-configured", "password", "hash", "digest", "salt", "optional[str]",
                                    "field", "secret", "str]=field", "pass"
                                }
                                if value and value not in placeholders and not value.startswith(("your_", "${", "env.", "process.env", "os.environ", "get(", "optional")):
                                    findings.append({
                                        "type": "Documented Password",
                                        "file": relpath,
                                        "line": line_idx,
                                        "content": "Password-like value published in repository file",
                                    })
                            kw_match = EXPOSED_CREDENTIAL_KEYWORDS.search(line)
                            if kw_match:
                                findings.append({
                                    "type": "Exposed Credential UI Handler",
                                    "file": relpath,
                                    "line": line_idx,
                                    "content": "Credential copy handler detected in source code",
                                })
        except Exception:
            pass

    print(f"Scanned {scanned_files} repository files.")
    return findings

if __name__ == "__main__":
    findings = scan_repository()
    if findings:
        print(f"\n[ALERT] Found {len(findings)} potential secret(s):")
        for finding in findings:
            print(f" - [{finding['type']}] {finding['file']}:{finding['line']}: {finding['content']}")
        sys.exit(1)
    else:
        print("\n[PASS] No credential patterns found in scanned working files. Git history and credential rotation are NOT verified.")
        sys.exit(0)
