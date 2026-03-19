# tests/test_webhooks/test_dispatcher.py
"""Tests for webhook dispatcher: signing, delivery, failure counting."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, UTC
from api.auth.service import AuthService

pytestmark = pytest.mark.asyncio(loop_scope="session")


def test_sign_payload_deterministic():
    from api.webhooks.dispatcher import sign_payload
    sig1 = sign_payload("secret123", b'{"event": "test"}')
    sig2 = sign_payload("secret123", b'{"event": "test"}')
    assert sig1 == sig2
    assert sig1.startswith("sha256=")


def test_sign_payload_different_secrets():
    from api.webhooks.dispatcher import sign_payload
    sig1 = sign_payload("secret1", b'data')
    sig2 = sign_payload("secret2", b'data')
    assert sig1 != sig2


async def test_dispatch_event_sends_to_matching_webhooks(test_db_session):
    from api.webhooks.dispatcher import dispatch_event
    from api.webhooks.models import Webhook

    wh = Webhook(
        id="wh_dispatch_test_001",
        user_id="user_dispatch_001",
        url="https://example.com/hook",
        events=["order.filled"],
        secret="test_secret",
        status="active",
    )
    test_db_session.add(wh)
    await test_db_session.commit()

    with patch("api.webhooks.dispatcher._deliver", new_callable=AsyncMock, return_value=True) as mock_deliver:
        count = await dispatch_event(
            test_db_session,
            event_type="order.filled",
            data={"order_id": "ord_123"},
            user_id="user_dispatch_001",
        )

    assert count == 1
    mock_deliver.assert_called_once()
    call_args = mock_deliver.call_args
    assert b"order.filled" in call_args[0][1]  # body contains event type
    assert call_args[0][2].startswith("sha256=")  # signature


async def test_dispatch_event_skips_non_matching_events(test_db_session):
    from api.webhooks.dispatcher import dispatch_event

    with patch("api.webhooks.dispatcher._deliver", new_callable=AsyncMock) as mock_deliver:
        count = await dispatch_event(
            test_db_session,
            event_type="market.resolved",  # webhook only listens to order.filled
            data={},
            user_id="user_dispatch_001",
        )

    assert count == 0
    mock_deliver.assert_not_called()


async def test_dispatch_increments_failure_count(test_db_session):
    from api.webhooks.dispatcher import dispatch_event
    from api.webhooks.models import Webhook
    from sqlalchemy import select

    wh = Webhook(
        id="wh_fail_test_001",
        user_id="user_fail_001",
        url="https://example.com/failing",
        events=["order.cancelled"],
        secret="s",
        status="active",
        failure_count=0,
    )
    test_db_session.add(wh)
    await test_db_session.commit()

    with patch("api.webhooks.dispatcher._deliver", new_callable=AsyncMock, return_value=False):
        await dispatch_event(
            test_db_session,
            event_type="order.cancelled",
            data={},
            user_id="user_fail_001",
        )

    await test_db_session.refresh(wh)
    assert wh.failure_count == 1
    assert wh.status == "active"


async def test_dispatch_marks_failed_after_max_failures(test_db_session):
    from api.webhooks.dispatcher import dispatch_event
    from api.webhooks.models import Webhook

    wh = Webhook(
        id="wh_maxfail_001",
        user_id="user_maxfail_001",
        url="https://example.com/dead",
        events=["position.opened"],
        secret="s",
        status="active",
        failure_count=4,  # one more failure = max (5)
    )
    test_db_session.add(wh)
    await test_db_session.commit()

    with patch("api.webhooks.dispatcher._deliver", new_callable=AsyncMock, return_value=False):
        await dispatch_event(
            test_db_session,
            event_type="position.opened",
            data={},
            user_id="user_maxfail_001",
        )

    await test_db_session.refresh(wh)
    assert wh.failure_count == 5
    assert wh.status == "failed"
