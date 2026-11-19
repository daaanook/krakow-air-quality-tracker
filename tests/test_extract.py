"""Tests for src/extract.py. Run from the project folder:  python3 -m pytest"""
import json
import sys
from pathlib import Path
from unittest import mock

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import extract  # noqa: E402

FAKE_ANSWER = {
    "latitude": 50.0647,
    "longitude": 19.945,
    "hourly_units": {"time": "iso8601", "pm10": "μg/m³", "pm2_5": "μg/m³"},
    "hourly": {
        "time": ["2026-11-14T00:00", "2026-11-14T01:00"],
        "pm10": [30.1, 28.4],
        "pm2_5": [22.0, 20.5],
    },
}


def test_build_params_contains_location_and_pollutants():
    params = extract.build_params(past_days=3)
    assert params["past_days"] == 3
    assert params["latitude"] == extract.KRAKOW["latitude"]
    assert params["hourly"] == "pm10,pm2_5"


def test_fetch_returns_json_from_api():
    fake_response = mock.Mock()
    fake_response.json.return_value = FAKE_ANSWER
    with mock.patch.object(requests, "get", return_value=fake_response) as get:
        result = extract.fetch(past_days=2)
    assert result == FAKE_ANSWER
    assert get.call_args.kwargs["params"]["past_days"] == 2
    fake_response.raise_for_status.assert_called_once()


def test_save_raw_writes_valid_json(tmp_path):
    path = extract.save_raw(FAKE_ANSWER, raw_dir=tmp_path)
    assert path.exists()
    assert json.loads(path.read_text(encoding="utf-8")) == FAKE_ANSWER
