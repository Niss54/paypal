"""Warm a hosted API with bounded GET requests before recording or judging.

Readiness confirms only the API's own readiness response. It does not verify a
PayPal capture, live AI inference, physical sensors or other third-party systems.
"""
import argparse
import json
import math
import sys
import time
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


def _get_json(url: str, timeout: float) -> dict:
    request = Request(url, headers={"User-Agent": "KinetixRAG-DemoWarmup/1.0"})
    with urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError("Endpoint did not return HTTP 200")
        body = response.read(65537)
        if len(body) > 65536:
            raise ValueError("Unexpectedly large health response")
        data = json.loads(body)
        if not isinstance(data, dict):
            raise ValueError("Health response must be a JSON object")
        return data


def warm_demo(base_url: str, deadline_seconds: float = 180, timeout_seconds: float = 10,
              interval_seconds: float = 5) -> dict:
    parsed = urlsplit(base_url)
    if (parsed.scheme not in ("http", "https") or not parsed.hostname
            or parsed.username or parsed.password or parsed.query or parsed.fragment):
        raise ValueError("Supply a plain HTTP(S) API base URL without credentials or query parameters")
    for value in (deadline_seconds, timeout_seconds, interval_seconds):
        if not math.isfinite(value) or value <= 0:
            raise ValueError("Deadline, timeout and interval must be finite positive seconds")
    start = time.monotonic()
    deadline = start + deadline_seconds
    attempts = 0
    last_error = None
    live = ready = False
    while time.monotonic() < deadline:
        attempts += 1
        live = ready = False
        try:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            live_data = _get_json(f"{base_url.rstrip('/')}/api/health/live", min(timeout_seconds, remaining))
            live = live_data.get("status") == "alive"
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            ready_data = _get_json(f"{base_url.rstrip('/')}/api/health/ready", min(timeout_seconds, remaining))
            ready = ready_data.get("ready") is True
            if live and ready:
                break
            last_error = "Health response did not confirm both alive and ready"
        except Exception as exc:
            last_error = type(exc).__name__
        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(interval_seconds, remaining))
    return {
        "target_url": base_url,
        "ready": live and ready,
        "attempts": attempts,
        "elapsed_seconds": round(time.monotonic() - start, 2),
        "liveness_confirmed": live,
        "readiness_confirmed": ready,
        "last_error": None if live and ready else last_error,
        "scope": "Hosted API health responses only; no checkout, capture, AI or external integration verified",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="https://paypal-y2jk.onrender.com")
    parser.add_argument("--deadline", type=float, default=180)
    parser.add_argument("--timeout", type=float, default=10)
    parser.add_argument("--interval", type=float, default=5)
    args = parser.parse_args()
    try:
        report = warm_demo(args.url, args.deadline, args.timeout, args.interval)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["ready"] else 1)
