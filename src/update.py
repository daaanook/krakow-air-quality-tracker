"""Day 6: daily update. Downloads only the days that are missing, for air quality and weather.

Run from the project folder (with the virtual environment on):
    python3 src/update.py

Writes a log to the console and to logs/update.log.
"""
import logging
import sqlite3
from datetime import date, datetime
from pathlib import Path

import extract
import transform
import weather
from load import DB_PATH, connect, load

log = logging.getLogger(__name__)

DEFAULT_DAYS = 7   # used when the table is empty
MAX_DAYS = 92      # the API gives at most 92 past days
LOG_FILE = Path("logs/update.log")


def days_to_fetch(conn, table, today=None):
    """How many past_days to request so that nothing is missing.

    Looks at the newest hour in the table. Empty table -> DEFAULT_DAYS.
    The newest day is downloaded again on purpose: it may have been incomplete.
    """
    today = today or date.today()
    try:
        latest = conn.execute(f"SELECT MAX(time) FROM {table}").fetchone()[0]
    except sqlite3.OperationalError:  # table does not exist yet
        latest = None
    if latest is None:
        return DEFAULT_DAYS
    latest_day = datetime.strptime(latest[:10], "%Y-%m-%d").date()
    return max(1, min((today - latest_day).days + 1, MAX_DAYS))


def update_dataset(name, conn, table, fetch, save_raw, transform_fn, load_fn):
    """One dataset: decide how many days, download, save the raw answer, clean, load."""
    days = days_to_fetch(conn, table)
    log.info("%s: requesting the last %d day(s)", name, days)
    payload = fetch(days)
    save_raw(payload)
    df = transform_fn(payload)
    new_rows = load_fn(conn, df)
    log.info("%s: %d row(s) after cleaning, %d new in the database", name, len(df), new_rows)
    return new_rows


def setup_logging():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(), logging.FileHandler(LOG_FILE, encoding="utf-8")],
    )


def main():
    setup_logging()
    conn = connect(DB_PATH)
    conn.execute(weather.SCHEMA)
    try:
        air = update_dataset("air quality", conn, "air_quality",
                             extract.fetch, extract.save_raw, transform.transform, load)
        wx = update_dataset("weather", conn, "weather",
                            weather.fetch, weather.save_raw, weather.transform_weather, weather.load_weather)
    finally:
        conn.close()
    print(f"New air quality rows: {air}")
    print(f"New weather rows: {wx}")


if __name__ == "__main__":
    main()
