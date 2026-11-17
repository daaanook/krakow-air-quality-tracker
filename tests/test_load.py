"""Tests for src/load.py. Run from the project folder:  python3 -m pytest"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import load  # noqa: E402
import transform  # noqa: E402

PAYLOAD = {
    "hourly_units": {"time": "iso8601", "pm10": "μg/m³", "pm2_5": "μg/m³"},
    "hourly": {
        "time": ["2026-11-14T00:00", "2026-11-14T01:00"],
        "pm10": [30.1, 28.4],
        "pm2_5": [22.0, 20.5],
    },
}


def count(conn):
    return conn.execute("SELECT COUNT(*) FROM air_quality").fetchone()[0]


def test_load_adds_all_rows():
    conn = load.connect(":memory:")
    assert load.load(conn, transform.transform(PAYLOAD)) == 4
    assert count(conn) == 4


def test_loading_twice_creates_no_duplicates():
    conn = load.connect(":memory:")
    df = transform.transform(PAYLOAD)
    load.load(conn, df)
    assert load.load(conn, df) == 0   # nothing new
    assert count(conn) == 4


def test_new_value_replaces_old_value_for_same_hour():
    conn = load.connect(":memory:")
    load.load(conn, transform.transform(PAYLOAD))
    changed = {**PAYLOAD, "hourly": {**PAYLOAD["hourly"], "pm10": [99.9, 28.4]}}
    load.load(conn, transform.transform(changed))
    value = conn.execute(
        "SELECT value FROM air_quality WHERE pollutant='pm10' AND time='2026-11-14 00:00:00'"
    ).fetchone()[0]
    assert value == 99.9
    assert count(conn) == 4


def test_empty_table_loads_nothing():
    conn = load.connect(":memory:")
    assert load.load(conn, transform.transform({})) == 0
