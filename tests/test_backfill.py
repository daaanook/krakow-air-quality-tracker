"""Tests for src/backfill.py. Run from the project folder:  python3 -m pytest"""
import sys
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import backfill  # noqa: E402
import extract  # noqa: E402
import load  # noqa: E402
import weather  # noqa: E402

AIR = {
    "hourly_units": {"time": "iso8601", "pm10": "μg/m³", "pm2_5": "μg/m³"},
    "hourly": {"time": ["2026-09-01T00:00", "2026-09-01T01:00"], "pm10": [10.0, 11.0], "pm2_5": [5.0, 6.0]},
}
WEATHER = {
    "hourly_units": {"time": "iso8601", "temperature_2m": "°C", "relative_humidity_2m": "%", "wind_speed_10m": "km/h"},
    "hourly": {"time": ["2026-09-01T00:00"], "temperature_2m": [14.0],
               "relative_humidity_2m": [70], "wind_speed_10m": [8.0]},
}


def run(conn):
    with mock.patch.object(extract, "fetch", return_value=AIR) as air_fetch, \
         mock.patch.object(extract, "save_raw"), \
         mock.patch.object(weather, "fetch", return_value=WEATHER) as wx_fetch, \
         mock.patch.object(weather, "save_raw"):
        result = backfill.backfill(conn)
    return result, air_fetch, wx_fetch


def test_backfill_asks_for_the_maximum_number_of_days_and_loads_both_tables():
    conn = load.connect(":memory:")
    (air, wx), air_fetch, wx_fetch = run(conn)
    air_fetch.assert_called_once_with(92)
    wx_fetch.assert_called_once_with(92)
    assert (air, wx) == (4, 3)


def test_backfill_twice_creates_no_duplicates():
    conn = load.connect(":memory:")
    run(conn)
    (air, wx), _, _ = run(conn)
    assert (air, wx) == (0, 0)
