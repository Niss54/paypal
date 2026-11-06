"""Unit tests for sliding window rate limiter."""
import pytest
import time
from backend.app.core.rate_limit import SlidingWindowRateLimiter


def test_sliding_window_allows_under_limit():
    limiter = SlidingWindowRateLimiter(requests_per_minute=5, window_seconds=1.0)
    for _ in range(5):
        assert limiter.check("test-ip-1") is True


def test_sliding_window_blocks_over_limit():
    limiter = SlidingWindowRateLimiter(requests_per_minute=3, window_seconds=1.0)
    assert limiter.check("test-ip-2") is True
    assert limiter.check("test-ip-2") is True
    assert limiter.check("test-ip-2") is True
    # 4th request must be blocked
    assert limiter.check("test-ip-2") is False


def test_sliding_window_resets_after_window_expires():
    limiter = SlidingWindowRateLimiter(requests_per_minute=2, window_seconds=0.2)
    assert limiter.check("test-ip-3") is True
    assert limiter.check("test-ip-3") is True
    assert limiter.check("test-ip-3") is False
    # Wait for window to expire
    time.sleep(0.25)
    assert limiter.check("test-ip-3") is True


def test_sliding_window_isolates_different_keys():
    limiter = SlidingWindowRateLimiter(requests_per_minute=2, window_seconds=1.0)
    assert limiter.check("ip-A") is True
    assert limiter.check("ip-A") is True
    assert limiter.check("ip-A") is False
    # ip-B should still be allowed
    assert limiter.check("ip-B") is True
