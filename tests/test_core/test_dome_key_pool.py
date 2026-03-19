"""Tests for DomeKeyPool — round-robin rotation and rate-limit cooldown."""

import time
import pytest
from core.dome.key_pool import DomeKeyPool

pytestmark = pytest.mark.asyncio(loop_scope="session")


def test_requires_at_least_one_key():
    with pytest.raises(ValueError):
        DomeKeyPool([])


def test_round_robin_rotates():
    pool = DomeKeyPool(["a", "b", "c", "d"], ws_key_count=1)
    keys = [pool.next_key() for _ in range(6)]
    # REST keys are a, b, c (last 1 reserved for WS).
    assert keys[:3] == ["a", "b", "c"]
    assert keys[3:6] == ["a", "b", "c"]


def test_ws_keys_separate():
    pool = DomeKeyPool(["a", "b", "c", "d"], ws_key_count=2)
    ws1 = pool.next_ws_key()
    ws2 = pool.next_ws_key()
    assert ws1 in ("c", "d")
    assert ws2 in ("c", "d")
    assert ws1 != ws2


def test_cooldown_skips_key():
    pool = DomeKeyPool(["a", "b", "c"], ws_key_count=0, cooldown_seconds=60)
    # Get "a" then mark it as rate-limited.
    first = pool.next_key()
    assert first == "a"
    pool.report_rate_limit("a")
    # Next calls should skip "a".
    second = pool.next_key()
    assert second == "b"
    third = pool.next_key()
    assert third == "c"
    fourth = pool.next_key()
    assert fourth == "b"  # "a" still cooling down, wraps to "b"


def test_all_cooldown_returns_least_cooled():
    pool = DomeKeyPool(["x", "y"], ws_key_count=0, cooldown_seconds=60)
    pool.report_rate_limit("x")
    pool.report_rate_limit("y")
    # Both cooling — should still return one.
    key = pool.next_key()
    assert key in ("x", "y")


def test_key_counts():
    pool = DomeKeyPool(["a", "b", "c", "d", "e"], ws_key_count=2)
    assert pool.rest_key_count == 3
    assert pool.ws_key_count == 2
    assert pool.total_key_count == 5


def test_single_key_works():
    pool = DomeKeyPool(["only"], ws_key_count=0)
    assert pool.next_key() == "only"
    assert pool.next_key() == "only"
    assert pool.next_ws_key() == "only"
