"""Tests for src/weather.py. Run from the project folder:  python3 -m pytest"""
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import load  # noqa: E402
import weather  # noqa: E402

PAYLOAD = {
    "hourly_units": {"time": "iso8601", "temperature_2m": "°C",
                     "relative_humidity_2m": "%", "wind_speed_10m": "km/h"},
    "hourly": {
        "time": ["2026-11-14T00:00", "2026-11-14T01:00", "2026-11-14T02:00"],
        "temperature_2m": [-3.5, 2.0, None],          # negative temperature is valid; one missing
        "relative_humidity_2m": [80, 150, 75],        # 150 % is impossible
        "wind_speed_10m": [5.0, 7.2, 3.1],
    },
}


def test_build_params_contains_variables_and_location():
    params = weather.build_params(past_days=5)
    assert params["past_days"] == 5
    assert params["hourly"] == "temperature_2m,relative_humidity_2m,wind_speed_10m"
    assert params["latitude"] == weather.KRAKOW["latitude"]


def test_fetch_uses_api_and_returns_json():
    fake = mock.Mock()
    fake.json.return_value = PAYLOAD
    with mock.patch.object(weather.requests, "get", return_value=fake) as get:
        assert weather.fetch(past_days=2) == PAYLOAD
    assert get.call_args.kwargs["params"]["past_days"] == 2
    fake.raise_for_status.assert_called_once()


def test_negative_temperature_is_kept_but_impossible_humidity_is_removed():
    df = weather.transform_weather(PAYLOAD)
    temps = df[df["variable"] == "temperature_2m"]["value"].tolist()
    assert -3.5 in temps                      # negative temperature stays
    assert len(temps) == 2                    # the missing value is dropped
    humidity = df[df["variable"] == "relative_humidity_2m"]["value"].tolist()
    assert 150 not in humidity and len(humidity) == 2


def test_loading_twice_creates_no_duplicates():
    conn = load.connect(":memory:")
    df = weather.transform_weather(PAYLOAD)
    first = weather.load_weather(conn, df)
    assert first == len(df)
    assert weather.load_weather(conn, df) == 0


def test_empty_payload_loads_nothing():
    conn = load.connect(":memory:")
    assert weather.load_weather(conn, weather.transform_weather({})) == 0
