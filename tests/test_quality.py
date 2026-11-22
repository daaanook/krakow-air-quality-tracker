"""Tests for src/quality.py. Run from the project folder:  python3 -m pytest"""
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import quality  # noqa: E402


def frame(times, values, unit="x"):
    return pd.DataFrame({"time": pd.to_datetime(times), "value": values, "unit": unit})


def test_missing_hours_finds_gap():
    times = ["2026-11-01 00:00", "2026-11-01 01:00", "2026-11-01 04:00"]
    missing = quality.missing_hours(pd.to_datetime(times))
    assert [t.hour for t in missing] == [2, 3]


def test_missing_hours_none_when_complete_or_empty():
    assert quality.missing_hours(pd.to_datetime(["2026-11-01 00:00", "2026-11-01 01:00"])) == []
    assert quality.missing_hours([]) == []


def test_outliers_iqr_flags_extreme_value_only():
    values = pd.Series([10, 11, 12, 11, 10, 12, 11, 100])
    _, _, out = quality.outliers_iqr(values)
    assert out.tolist() == [100]


def test_check_variable_counts_future_hours_and_units():
    df = frame(["2026-11-01 00:00", "2026-11-01 01:00", "2026-11-03 00:00"], [1.0, 2.0, 3.0], unit="μg/m³")
    r = quality.check_variable(df, now=datetime(2026, 11, 2))
    assert r["rows"] == 3
    assert r["future_hours"] == 1
    assert r["units"] == ["μg/m³"]
    assert r["missing_hours"] == 46  # 1 Nov 02:00 ... 2 Nov 23:00 are absent


def test_overlap_of_counts_common_hours():
    air = frame(["2026-11-01 00:00", "2026-11-01 01:00"], [1, 2])
    wx = frame(["2026-11-01 01:00", "2026-11-01 02:00"], [1, 2])
    assert quality.overlap_of(air, wx)["hours"] == 1
    assert quality.overlap_of(air, frame(["2027-01-01 00:00"], [1])) is None
