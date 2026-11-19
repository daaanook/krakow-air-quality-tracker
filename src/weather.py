"""Day 5: download hourly weather for Krakow and store it in a second SQLite table.

Variables: temperature (2 m above ground), relative humidity, wind speed (10 m).
Docs: https://open-meteo.com/en/docs

Run from the project folder (with the virtual environment on):
    python3 src/weather.py                  # last 7 days
    python3 src/weather.py --past-days 11   # more days, up to 92
"""
import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
from http_utils import get_json
from load import DB_PATH, connect
from transform import to_dataframe

log = logging.getLogger(__name__)

URL = "https://api.open-meteo.com/v1/forecast"
KRAKOW = {"latitude": 50.0647, "longitude": 19.9450}
VARIABLES = ["temperature_2m", "relative_humidity_2m", "wind_speed_10m"]
RAW_DIR = Path("data/raw/weather")

# Physically possible ranges. Note: temperature CAN be negative, so it must not be
# cleaned with the "no negative values" rule that is used for pollutant concentrations.
LIMITS = {
    "temperature_2m": (-60, 60),
    "relative_humidity_2m": (0, 100),
    "wind_speed_10m": (0, 400),
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS weather (
    time      TEXT NOT NULL,      -- local time of the hour, 'YYYY-MM-DD HH:MM:SS'
    variable  TEXT NOT NULL,      -- 'temperature_2m', 'relative_humidity_2m', 'wind_speed_10m'
    value     REAL NOT NULL,
    unit      TEXT,
    loaded_at TEXT NOT NULL,
    PRIMARY KEY (time, variable)
);
"""


def build_params(past_days):
    return {
        **KRAKOW,
        "hourly": ",".join(VARIABLES),
        "past_days": past_days,
        "forecast_days": 1,
        "timezone": "Europe/Warsaw",
    }


def fetch(past_days=7, timeout=30):
    return get_json(URL, build_params(past_days), timeout=timeout)


def save_raw(payload, raw_dir=RAW_DIR):
    """Keep the unchanged API answer (in its own folder, so it is not mixed with air quality files)."""
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = raw_dir / f"krakow_weather_{stamp}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def clean_weather(df):
    """Fix types, drop missing and impossible values, drop duplicates."""
    if df.empty:
        return df
    df = df.rename(columns={"pollutant": "variable"}).copy()
    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["time", "value"])

    low = df["variable"].map(lambda v: LIMITS.get(v, (float("-inf"), float("inf")))[0])
    high = df["variable"].map(lambda v: LIMITS.get(v, (float("-inf"), float("inf")))[1])
    before = len(df)
    df = df[(df["value"] >= low) & (df["value"] <= high)]
    if len(df) < before:
        log.warning("Removed %d value(s) outside the possible range", before - len(df))

    df = df.drop_duplicates(subset=["time", "variable"], keep="last")
    return df.sort_values(["variable", "time"]).reset_index(drop=True)


def transform_weather(payload):
    return clean_weather(to_dataframe(payload))


def load_weather(conn, df):
    """Write rows to the weather table. Returns the number of NEW rows."""
    conn.execute(SCHEMA)
    if df.empty:
        return 0
    before = conn.execute("SELECT COUNT(*) FROM weather").fetchone()[0]
    loaded_at = datetime.now().isoformat(timespec="seconds")
    rows = [
        (t.strftime("%Y-%m-%d %H:%M:%S"), variable, float(value), unit, loaded_at)
        for t, variable, value, unit in df[["time", "variable", "value", "unit"]].itertuples(index=False)
    ]
    with conn:
        conn.executemany(
            "INSERT OR REPLACE INTO weather (time, variable, value, unit, loaded_at) "
            "VALUES (?, ?, ?, ?, ?)",
            rows,
        )
    after = conn.execute("SELECT COUNT(*) FROM weather").fetchone()[0]
    return after - before


def main(argv=None):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Download Krakow weather data")
    parser.add_argument("--past-days", type=int, default=7)
    args = parser.parse_args(argv)

    payload = fetch(args.past_days)
    log.info("Downloaded %d hourly rows", len(payload.get("hourly", {}).get("time", [])))
    log.info("Saved raw file: %s", save_raw(payload))

    df = transform_weather(payload)
    conn = connect(DB_PATH)
    new_rows = load_weather(conn, df)
    print(f"New weather rows added: {new_rows}")
    print()
    print("Check with SQL:")
    for row in conn.execute(
        "SELECT variable, COUNT(*), ROUND(MIN(value), 1), ROUND(AVG(value), 1), ROUND(MAX(value), 1), unit "
        "FROM weather GROUP BY variable"
    ):
        print("  ", row)
    conn.close()


if __name__ == "__main__":
    main()
