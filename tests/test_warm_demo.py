from unittest.mock import MagicMock

import pytest

from scripts import warm_demo as warm


@pytest.fixture
def clock(monkeypatch):
    now = [0.0]
    monkeypatch.setattr(warm.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(warm.time, "sleep", lambda seconds: now.__setitem__(0, now[0] + seconds))
    return now


def test_cold_start_recovers_with_read_only_health_probes(monkeypatch, clock):
    fetch = MagicMock(side_effect=[TimeoutError(), {"status": "alive"}, {"ready": True}])
    monkeypatch.setattr(warm, "_get_json", fetch)
    result = warm.warm_demo("https://demo.example", 15, 3, 2)
    assert result["ready"] is True
    assert result["attempts"] == 2
    assert result["elapsed_seconds"] == 2
    assert all(call.args[0].endswith(("/api/health/live", "/api/health/ready")) for call in fetch.call_args_list)


def test_http_success_without_readiness_does_not_pass(monkeypatch, clock):
    monkeypatch.setattr(warm, "_get_json", lambda url, timeout: {"status": "alive", "ready": False})
    result = warm.warm_demo("https://demo.example", 5, 2, 2)
    assert result["ready"] is False
    assert result["attempts"] == 3
    assert result["elapsed_seconds"] == 5


def test_timeout_is_clamped_to_remaining_budget(monkeypatch, clock):
    timeouts = []
    def fetch(url, timeout):
        timeouts.append(timeout)
        clock[0] += timeout
        raise TimeoutError()
    monkeypatch.setattr(warm, "_get_json", fetch)
    result = warm.warm_demo("https://demo.example", 3, 10, 2)
    assert timeouts == [3]
    assert result["ready"] is False
    assert result["elapsed_seconds"] == 3


@pytest.mark.parametrize("url", ["file:///secret", "https://user:secret@demo.example", "https://demo.example/?token=secret"])
def test_rejects_non_http_or_credential_urls(url):
    with pytest.raises(ValueError):
        warm.warm_demo(url)


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf")])
def test_rejects_unbounded_or_invalid_timeouts(value):
    with pytest.raises(ValueError):
        warm.warm_demo("https://demo.example", timeout_seconds=value)
