# tests/test_core/test_base_collector.py
"""Tests for BaseCollector run loop."""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from data_pipeline.base import BaseCollector

pytestmark = pytest.mark.asyncio(loop_scope="session")


class FakeCollector(BaseCollector):
    name = "fake"
    interval_seconds = 0  # no delay for tests

    def __init__(self):
        self.collect_count = 0
        self.teardown_called = False

    async def collect(self, db):
        self.collect_count += 1
        if self.collect_count >= 3:
            raise asyncio.CancelledError()

    async def teardown(self):
        self.teardown_called = True


class FailingCollector(BaseCollector):
    name = "failing"
    interval_seconds = 0

    def __init__(self):
        self.collect_count = 0

    async def collect(self, db):
        self.collect_count += 1
        if self.collect_count == 1:
            raise ValueError("Simulated failure")
        if self.collect_count >= 3:
            raise asyncio.CancelledError()


async def test_base_collector_runs_multiple_cycles():
    collector = FakeCollector()
    mock_factory = MagicMock()
    mock_session = AsyncMock()
    mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

    with pytest.raises(asyncio.CancelledError):
        await collector.run(mock_factory)

    assert collector.collect_count == 3
    assert collector.teardown_called is True


async def test_base_collector_continues_after_error():
    collector = FailingCollector()
    mock_factory = MagicMock()
    mock_session = AsyncMock()
    mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_session)
    mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

    with pytest.raises(asyncio.CancelledError):
        await collector.run(mock_factory)

    # Should have continued past the error in cycle 1
    assert collector.collect_count == 3


async def test_base_collector_not_implemented():
    collector = BaseCollector()
    with pytest.raises(NotImplementedError):
        await collector.collect(AsyncMock())
