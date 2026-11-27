"""Tests for src/weather_corr.py. Run from the project folder:  python3 -m pytest"""
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import weather_corr as wc  # noqa: E402


def daily(values, start="2026-11-01"):
    idx = pd.date_range(start, periods=len(values), freq="D", name="date")
    return pd.DataFrame({"value": values}, index=idx)


def dataset(pm, temp, wind, hum=None):
    hum = hum or list(range(len(pm)))
    return wc.build_dataset(daily(pm), {"temperature_2m": daily(temp), "wind_speed_10m": daily(wind),
                                        "relative_humidity_2m": daily(hum)})


def test_build_dataset_keeps_only_common_days():
    data = wc.build_dataset(daily([1, 2, 3, 4]), {"wind_speed_10m": daily([5, 6], start="2026-11-03")})
    assert list(data.index.day) == [3, 4]


def test_correlation_signs():
    pm = [10, 20, 30, 40, 50]
    data = dataset(pm, temp=[5, 4, 3, 2, 1], wind=[1, 2, 3, 4, 5])
    corr = wc.correlations(data)
    assert corr["temperature_2m"] == pytest.approx(-1.0)
    assert corr["wind_speed_10m"] == pytest.approx(1.0)


def test_pm25_by_wind_groups_days():
    data = dataset(pm=[50, 40, 20, 10], temp=[0] * 4, wind=[2, 4, 8, 15])
    table = wc.pm25_by_wind(data)
    assert table.loc["calm (< 5 km/h)", "days"] == 2
    assert table.loc["calm (< 5 km/h)", "mean"] == 45.0
    assert table.loc["windy (> 10 km/h)", "mean"] == 10.0


def test_plot_writes_image(tmp_path):
    data = dataset(pm=[10, 20, 30, 40], temp=[1, 2, 3, 4], wind=[5, 6, 7, 8])
    path = wc.plot_scatter(data, tmp_path / "x.png")
    assert path.exists() and path.stat().st_size > 1000
