import pytest
from api.agent.tg_auth import validate_init_data, parse_init_data


def test_parse_init_data():
    raw = "user=%7B%22id%22%3A12345%7D&auth_date=1234567890&hash=abc"
    parsed = parse_init_data(raw)
    assert "user" in parsed
    assert "auth_date" in parsed
    assert "hash" in parsed


def test_validate_init_data_rejects_tampered():
    result = validate_init_data(
        init_data="user=test&auth_date=123&hash=fakehash",
        bot_token="test_token",
    )
    assert result is None


def test_validate_init_data_rejects_expired():
    result = validate_init_data(
        init_data="user=%7B%22id%22%3A1%7D&auth_date=1000000000&hash=abc",
        bot_token="test_token",
        max_age_seconds=60,
    )
    assert result is None
