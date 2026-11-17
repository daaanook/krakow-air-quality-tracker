"""Day 4: load the clean table into a SQLite database. Running it twice creates no duplicates.

Run from the project folder:
    python3 src/load.py
"""
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from transform import transform_all

log = logging.getLogger(__name__)

DB_PATH = Path("data/air_quality.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS air_quality (
    time      TEXT NOT NULL,      -- local time of the hour, 'YYYY-MM-DD HH:MM:SS'
    pollutant TEXT NOT NULL,      -- 'pm10' or 'pm2_5'
    value     REAL NOT NULL,      -- concentration
    unit      TEXT,               -- for example 'μg/m³'
    loaded_at TEXT NOT NULL,      -- when this row was written
    PRIMARY KEY (time, pollutant) -- one value per hour and pollutant
);
"""


def connect(db_path=DB_PATH):
    """Open the database; create the folder and the table if they do not exist."""
    if str(db_path) != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(SCHEMA)
    conn.commit()
    return conn


def load(conn, df):
    """Write the rows. A row with the same (time, pollutant) replaces the old one.

    Returns the number of NEW rows added to the table.
    """
    if df.empty:
        return 0
    before = conn.execute("SELECT COUNT(*) FROM air_quality").fetchone()[0]
    loaded_at = datetime.now().isoformat(timespec="seconds")
    rows = [
        (t.strftime("%Y-%m-%d %H:%M:%S"), pollutant, float(value), unit, loaded_at)
        for t, pollutant, value, unit in df[["time", "pollutant", "value", "unit"]].itertuples(index=False)
    ]
    with conn:  # one transaction: everything is saved, or nothing
        conn.executemany(
            "INSERT OR REPLACE INTO air_quality (time, pollutant, value, unit, loaded_at) "
            "VALUES (?, ?, ?, ?, ?)",
            rows,
        )
    after = conn.execute("SELECT COUNT(*) FROM air_quality").fetchone()[0]
    return after - before


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    df = transform_all()
    if df.empty:
        print("No data found. Run  python3 src/extract.py  first.")
        return
    conn = connect()
    new_rows = load(conn, df)
    total = conn.execute("SELECT COUNT(*) FROM air_quality").fetchone()[0]
    print(f"New rows added: {new_rows}")
    print(f"Rows in the database: {total}")
    print()
    print("Check with SQL:")
    for row in conn.execute(
        "SELECT pollutant, COUNT(*), ROUND(AVG(value), 1), MIN(time), MAX(time) "
        "FROM air_quality GROUP BY pollutant"
    ):
        print("  ", row)
    conn.close()


if __name__ == "__main__":
    main()
