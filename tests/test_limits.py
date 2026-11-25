"""Tests for src/limits.py. Run from the project folder:  python3 -m pytest"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import limits  # noqa: E402


def daily(values):
    idx = pd.date_range("2026-11-01", periods=len(values), freq="D", name="date")
    return pd.DataFrame({"value": values}, index=idx)


def test_days_above_is_strictly_above():
    above, total, share = limits.days_above(daily([10, 15, 16, 30]), 15)
    assert (above, total, share) == (2, 4, 50.0)  # exactly 15 is NOT above 15


def test_days_above_empty():
    above, total, share = limits.days_above(daily([]), 15)
    assert (above, total) == (0, 0) and pd.isna(share)


def test_table_has_one_row_per_threshold_with_data():
    table = limits.exceedance_table({"pm2_5": daily([10, 20, 30]), "pm10": daily([40, 60])})
    assert len(table) == len(limits.THRESHOLDS)
    who = table[(table["pollutant"] == "pm2_5") & (table["value"] == 15)].iloc[0]
    assert who["days_above"] == 2 and who["days"] == 3


def test_table_skips_pollutant_without_data():
    table = limits.exceedance_table({"pm2_5": daily([10, 20])})
    assert set(table["pollutant"]) == {"pm2_5"}


def test_thresholds_match_documented_values():
    values = {(p, n): v for p, n, v in limits.THRESHOLDS}
    assert values[("pm2_5", "WHO guideline 2021 (24 h)")] == 15
    assert values[("pm2_5", "EU limit from 2030 (24 h)")] == 25
    assert values[("pm10", "EU limit today (24 h)")] == 50


def test_plot_writes_image(tmp_path):
    table = limits.exceedance_table({"pm2_5": daily([10, 20, 30]), "pm10": daily([40, 60])})
    path = limits.plot_table(table, tmp_path / "x.png")
    assert path.exists() and path.stat().st_size > 1000
