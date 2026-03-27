import pytest

def test_bind_command_parse_with_key():
    text = "/bind pk_abc123def456"
    parts = text.split(maxsplit=1)
    assert parts[0] == "/bind"
    assert parts[1] == "pk_abc123def456"

def test_bind_command_parse_no_key():
    text = "/bind"
    parts = text.split(maxsplit=1)
    assert len(parts) == 1
