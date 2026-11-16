"""Day 3: turn the raw API JSON into a clean table (one row per hour per pollutant).

Run from the project folder:
    python3 src/transform.py
"""
import json
import logging
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)

RAW_DIR = Path("data/raw")
COLUMNS = ["time", "pollutant", "value", "unit"]


def to_dataframe(payload):
    """Flatten one API answer into a table with columns: time, pollutant, value, unit.

    The API returns parallel lists, for example
        hourly = {"time": [...], "pm10": [...], "pm2_5": [...]}
    and a dictionary hourly_units with the unit of every column.
    """
    hourly = payload.get("hourly", {})
    units = payload.get("hourly_units", {})
    times = hourly.get("time", [])

    frames = []
    for name, values in hourly.items():
        if name == "time":
            continue
        frames.append(pd.DataFrame({
            "time": times,
            "pollutant": name,
            "value": values,
            "unit": units.get(name),
        }))
    if not frames:
        return pd.DataFrame(columns=COLUMNS)
    return pd.concat(frames, ignore_index=True)


def clean(df):
    """Fix types, remove missing and impossible values, remove duplicates."""
    if df.empty:
        return df
    df = df.copy()
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    before = len(df)
    missing = int(df["value"].isna().sum())
    df = df.dropna(subset=["time", "value"])   # no time or no measurement
    df = df[df["value"] >= 0]                   # a concentration cannot be negative
    df = df.drop_duplicates(subset=["time", "pollutant"], keep="last")
    log.info("Rows: %d before, %d after cleaning (%d had no value)", before, len(df), missing)

    return df.sort_values(["pollutant", "time"]).reset_index(drop=True)


def transform(payload):
    return clean(to_dataframe(payload))


def load_raw_files(raw_dir=RAW_DIR):
    """Read all saved raw files, oldest first (so newer files win when rows repeat)."""
    paths = sorted(Path(raw_dir).glob("*.json"))
    return [json.loads(p.read_text(encoding="utf-8")) for p in paths]


def transform_all(raw_dir=RAW_DIR):
    """Transform all raw files into one table."""
    frames = [to_dataframe(p) for p in load_raw_files(raw_dir)]
    if not frames:
        return pd.DataFrame(columns=COLUMNS)
    return clean(pd.concat(frames, ignore_index=True))


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    df = transform_all()
    if df.empty:
        print("No data found. Run  python3 src/extract.py  first.")
        return
    print(df.head(5).to_string(index=False))
    print()
    print(df.dtypes.to_string())
    print()
    print("Time range:", df["time"].min(), "to", df["time"].max())
    print(df.groupby("pollutant")["value"].describe().round(1).to_string())


if __name__ == "__main__":
    main()
