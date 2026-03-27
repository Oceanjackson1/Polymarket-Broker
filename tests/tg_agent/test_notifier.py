import pytest
from unittest.mock import AsyncMock
from tg_agent.notifier import TelegramNotifier


@pytest.mark.asyncio
async def test_notify_order_filled():
    mock_bot = AsyncMock()
    notifier = TelegramNotifier(bot=mock_bot)

    await notifier.notify(
        chat_id=12345,
        event="order.filled",
        data={"order_id": "o1", "side": "BUY", "price": 0.65, "size": 100},
    )

    mock_bot.send_message.assert_called_once()
    call_args = mock_bot.send_message.call_args
    assert call_args.kwargs["chat_id"] == 12345
    assert "filled" in call_args.kwargs["text"].lower()


@pytest.mark.asyncio
async def test_notify_unknown_event():
    mock_bot = AsyncMock()
    notifier = TelegramNotifier(bot=mock_bot)

    await notifier.notify(chat_id=12345, event="custom.event", data={"foo": "bar"})
    mock_bot.send_message.assert_called_once()
