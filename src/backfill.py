"""Day 8: download as much history as the API allows (92 past days) for air quality and weather.

Run once from the project folder (with the virtual environment on):
    python3 src/backfill.py

Safe to repeat: rows that are already in the database are replaced, not duplicated.
"""
import logging

import extract
import transform
import weather
from load import DB_PATH, connect, load
from update import MAX_DAYS, setup_logging, update_dataset

log = logging.getLogger(__name__)

SUMMARY_SQL = (
    "SELECT {col}, COUNT(*), MIN(time), MAX(time) FROM {table} GROUP BY {col}"
)


def backfill(conn, days=MAX_DAYS):
    """Download `days` past days for both datasets. Returns (new air quality rows, new weather rows)."""
    conn.execute(weather.SCHEMA)
    air = update_dataset("air quality", conn, "air_quality",
                         extract.fetch, extract.save_raw, transform.transform, load, days=days)
    wx = update_dataset("weather", conn, "weather",
                        weather.fetch, weather.save_raw, weather.transform_weather,
                        weather.load_weather, days=days)
    return air, wx


def main():
    setup_logging()
    conn = connect(DB_PATH)
    try:
        air, wx = backfill(conn)
        print(f"New air quality rows: {air}")
        print(f"New weather rows: {wx}")
        print()
        print("What the database holds now (name, rows, first hour, last hour):")
        for table, col in (("air_quality", "pollutant"), ("weather", "variable")):
            for row in conn.execute(SUMMARY_SQL.format(col=col, table=table)):
                print("  ", row)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
