# tests/test_analysis/test_parse_json.py
"""Test AI response JSON parsing."""
import pytest


def test_parse_plain_json():
    from api.analysis.router import _parse_ai_json
    result = _parse_ai_json('{"probability": 0.72}')
    assert result["probability"] == 0.72


def test_parse_markdown_json():
    from api.analysis.router import _parse_ai_json
    result = _parse_ai_json('```json\n{"probability": 0.72}\n```')
    assert result["probability"] == 0.72


def test_parse_json_array():
    from api.analysis.router import _parse_ai_json
    result = _parse_ai_json('[{"id": 1}, {"id": 2}]')
    assert len(result) == 2


def test_parse_invalid_json():
    from api.analysis.router import _parse_ai_json
    with pytest.raises(Exception):
        _parse_ai_json('not json at all')
