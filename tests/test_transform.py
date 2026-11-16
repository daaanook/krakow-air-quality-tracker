"""Tests for src/transform.py. Run from the project folder:  python3 -m pytest"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pandas as pd  # noqa: E402
import transform  # noqa: E402

PAYLOAD = {
    "hourly_units": {"time": "iso8601", "pm10": "μg/m³", "pm2_5": "μg/m³"},
    "hourly": {
        "time": ["2026-11-14T00:00", "2026-11-14T01:00", "2026-11-14T02:00"],
        "pm10": [30.1, None, 28.4],      # one missing value
        "pm2_5": [22.0, 20.5, -5.0],     # one impossible negative value
    },
}


def test_to_dataframe_has_one_row_per_hour_per_pollutant():
    df = transform.to_dataframe(PAYLOAD)
    assert list(df.columns) == transform.COLUMNS
    assert len(df) == 6
    assert set(df["pollutant"]) == {"pm10", "pm2_5"}
    assert (df["unit"] == "μg/m³").all()


def test_clean_removes_missing_and_negative_values():
    df = transform.transform(PAYLOAD)
    assert len(df) == 4                      # 6 rows - 1 missing - 1 negative
    assert df["value"].ge(0).all()
    assert pd.api.types.is_datetime64_any_dtype(df["time"])


def test_clean_removes_duplicates_keeping_last():
    payload = {
        "hourly_units": {"pm10": "μg/m³"},
        "hourly": {"time": ["2026-11-14T00:00", "2026-11-14T00:00"], "pm10": [10.0, 12.0]},
    }
    df = transform.transform(payload)
    assert len(df) == 1
    assert df.loc[0, "value"] == 12.0


def test_empty_payload_gives_empty_table():
    df = transform.transform({})
    assert df.empty
    assert list(df.columns) == transform.COLUMNS
