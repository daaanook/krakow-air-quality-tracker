"""Tests for src/hourly.py. Run from the project folder:  python3 -m pytest"""
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import hourly  # noqa: E402
import load  # noqa: E402


def make_db():
    conn = load.connect(":memory:")
    rows = [
        ("2026-11-01 08:00:00", "pm2_5", 10.0), ("2026-11-02 08:00:00", "pm2_5", 30.0),
        ("2026-11-01 20:00:00", "pm2_5", 50.0), ("2026-11-02 20:00:00", "pm2_5", 70.0),
        ("2026-11-01 08:00:00", "pm10", 999.0),          # other pollutant: must be ignored
        ("2026-11-30 12:00:00", "pm2_5", 500.0),         # in the future: must be ignored
    ]
    conn.executemany("INSERT INTO air_quality VALUES (?, ?, ?, 'x', 't')", rows)
    return conn


def test_future_hours_and_other_pollutants_are_left_out():
    df = hourly.read_pollutant(make_db(), now=datetime(2026, 11, 5))
    assert len(df) == 4


def test_hourly_profile_means_and_counts():
    df = hourly.read_pollutant(make_db(), now=datetime(2026, 11, 5))
    profile = hourly.hourly_profile(df)
    assert profile.loc[8, "mean"] == 20.0
    assert profile.loc[20, "mean"] == 60.0
    assert profile.loc[8, "n"] == 2
    assert list(profile.index) == [8, 20]


def test_plot_writes_image(tmp_path):
    df = hourly.read_pollutant(make_db(), now=datetime(2026, 11, 5))
    path = hourly.plot_profile(hourly.hourly_profile(df), path=tmp_path / "chart.png", days=2)
    assert path.exists() and path.stat().st_size > 1000
