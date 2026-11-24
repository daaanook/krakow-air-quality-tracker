"""Tests for src/patterns.py. Run from the project folder:  python3 -m pytest"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import patterns  # noqa: E402


def hours(day, value, count=24):
    t = pd.date_range(day, periods=count, freq="h")
    return pd.DataFrame({"time": t, "value": float(value)})


def test_incomplete_day_is_dropped():
    df = pd.concat([hours("2026-11-02", 10), hours("2026-11-03", 99, count=10)])
    daily = patterns.daily_means(df)
    assert list(daily["value"]) == [10.0]


def test_by_weekday_uses_daily_means():
    # 2026-11-02 is a Monday, 2026-11-09 is the next Monday, 2026-11-03 is a Tuesday
    df = pd.concat([hours("2026-11-02", 10), hours("2026-11-09", 30), hours("2026-11-03", 50)])
    table = patterns.by_weekday(patterns.daily_means(df))
    assert table.loc["Mon", "mean"] == 20.0 and table.loc["Mon", "days"] == 2
    assert table.loc["Tue", "mean"] == 50.0
    assert pd.isna(table.loc["Sun", "mean"])  # no data for Sunday: stays empty, not zero


def test_by_month_shows_how_complete_the_month_is():
    df = pd.concat([hours("2026-10-31", 10), hours("2026-11-01", 20), hours("2026-11-02", 40)])
    table = patterns.by_month(patterns.daily_means(df))
    assert table.loc["2026-10", "days"] == 1 and table.loc["2026-10", "of"] == 31
    assert table.loc["2026-11", "mean"] == 30.0 and table.loc["2026-11", "of"] == 30


def test_plot_bars_writes_image(tmp_path):
    df = pd.concat([hours("2026-11-02", 10), hours("2026-11-03", 50)])
    table = patterns.by_weekday(patterns.daily_means(df))
    path = patterns.plot_bars(table, tmp_path / "x.png", "title")
    assert path.exists() and path.stat().st_size > 1000
