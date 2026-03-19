# tests/test_data/test_weather_parser.py
import pytest
from datetime import date


def test_parse_event_slug_standard():
    from data_pipeline.weather_collector import parse_event_slug
    city, d = parse_event_slug("highest-temperature-in-tokyo-on-march-19-2026")
    assert city == "tokyo"
    assert d == date(2026, 3, 19)


def test_parse_event_slug_multi_word_city():
    from data_pipeline.weather_collector import parse_event_slug
    city, d = parse_event_slug("highest-temperature-in-tel-aviv-on-march-16-2026")
    assert city == "tel-aviv"
    assert d == date(2026, 3, 16)


def test_parse_event_slug_invalid():
    from data_pipeline.weather_collector import parse_event_slug
    with pytest.raises(ValueError):
        parse_event_slug("warriors-vs-celtics")


def test_known_cities_has_entries():
    from data_pipeline.weather_collector import KNOWN_CITIES
    assert "tokyo" in KNOWN_CITIES
    assert "nyc" in KNOWN_CITIES
    assert len(KNOWN_CITIES) >= 15


def test_known_cities_structure():
    from data_pipeline.weather_collector import KNOWN_CITIES
    for city, info in KNOWN_CITIES.items():
        assert "lat" in info
        assert "lon" in info
        assert "tz" in info
        assert "unit" in info
        assert -90 <= info["lat"] <= 90
        assert -180 <= info["lon"] <= 180
        assert info["unit"] in ("celsius", "fahrenheit")


def test_compute_ensemble_probs_celsius():
    from data_pipeline.weather_collector import compute_ensemble_probs
    # 51 members: 17 round to 18, 17 round to 19, 17 round to 20
    members = [18.3] * 17 + [19.1] * 17 + [20.4] * 17
    bins = ["13°C or below", "18°C", "19°C", "20°C", "23°C or higher"]
    probs = compute_ensemble_probs(members, bins, "celsius")
    assert probs["18°C"] == pytest.approx(17 / 51, abs=0.001)
    assert probs["19°C"] == pytest.approx(17 / 51, abs=0.001)
    assert probs["20°C"] == pytest.approx(17 / 51, abs=0.001)
    assert probs["13°C or below"] == 0.0
    assert probs["23°C or higher"] == 0.0


def test_compute_ensemble_probs_boundary():
    from data_pipeline.weather_collector import compute_ensemble_probs
    # All 51 at 12.2 -> round to 12, which is <= 13, so "13°C or below"
    members = [12.2] * 51
    bins = ["13°C or below", "14°C", "15°C", "23°C or higher"]
    probs = compute_ensemble_probs(members, bins, "celsius")
    assert probs["13°C or below"] == pytest.approx(1.0)
    assert probs["14°C"] == 0.0


def test_compute_ensemble_probs_empty():
    from data_pipeline.weather_collector import compute_ensemble_probs
    probs = compute_ensemble_probs([], ["18°C"], "celsius")
    assert probs["18°C"] == 0.0


def test_compute_ensemble_probs_fahrenheit():
    from data_pipeline.weather_collector import compute_ensemble_probs
    members = [65.0] * 51
    bins = ["60°F or below", "65°F", "70°F or higher"]
    probs = compute_ensemble_probs(members, bins, "fahrenheit")
    assert probs["65°F"] == pytest.approx(1.0)


def test_compute_weather_bias_neutral():
    from data_pipeline.weather_collector import compute_weather_bias
    direction, bps = compute_weather_bias(0.25, 0.27)
    assert direction == "NEUTRAL"
    assert bps == 200


def test_compute_weather_bias_forecast_higher():
    from data_pipeline.weather_collector import compute_weather_bias
    direction, bps = compute_weather_bias(0.35, 0.20)
    assert direction == "FORECAST_HIGHER"
    # int(0.15 * 10000) = 1499 due to float truncation
    assert bps == 1499


def test_compute_weather_bias_market_higher():
    from data_pipeline.weather_collector import compute_weather_bias
    direction, bps = compute_weather_bias(0.10, 0.25)
    assert direction == "MARKET_HIGHER"
    assert bps == 1500
