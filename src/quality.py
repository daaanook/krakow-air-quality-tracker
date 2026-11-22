"""Day 9: data quality report for the database: missing hours, outliers, units, future hours.

Run from the project folder (with the virtual environment on):
    python3 src/quality.py

Prints the report and saves it to reports/data_quality.md.
"""
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

from load import DB_PATH

REPORT_PATH = Path("reports/data_quality.md")
TABLES = {"air_quality": "pollutant", "weather": "variable"}


def read_table(conn, table, name_col):
    df = pd.read_sql_query(f"SELECT time, {name_col} AS name, value, unit FROM {table}", conn)
    df["time"] = pd.to_datetime(df["time"])
    return df


def missing_hours(times):
    """Hours that are absent between the first and the last hour. Returns a sorted list of Timestamps."""
    times = pd.Series(sorted(set(times)))
    if times.empty:
        return []
    full = pd.date_range(times.iloc[0], times.iloc[-1], freq="h")
    return list(full.difference(pd.DatetimeIndex(times)))


def outliers_iqr(values):
    """Values outside 1.5 x IQR from the quartiles (the usual box-plot rule). Returns (low, high, outliers)."""
    q1, q3 = values.quantile(0.25), values.quantile(0.75)
    iqr = q3 - q1
    low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return low, high, values[(values < low) | (values > high)]


def check_variable(df, now=None):
    """All checks for one variable (one pollutant or one weather variable). Returns a dict."""
    now = now or datetime.now()
    missing = missing_hours(df["time"])
    low, high, out = outliers_iqr(df["value"])
    return {
        "rows": len(df),
        "first": df["time"].min(),
        "last": df["time"].max(),
        "missing_hours": len(missing),
        "units": sorted(df["unit"].dropna().unique()),
        "min": df["value"].min(),
        "mean": df["value"].mean(),
        "max": df["value"].max(),
        "iqr_low": low,
        "iqr_high": high,
        "outliers": len(out),
        "future_hours": int((df["time"] > now).sum()),
    }


def build_report(results, overlap=None):
    lines = ["# Data quality report", "", f"Created: {datetime.now():%Y-%m-%d %H:%M}", ""]
    for table, per_name in results.items():
        lines += [f"## Table `{table}`", "",
                  "| Variable | Rows | First hour | Last hour | Missing hours | Unit | Min | Mean | Max | Outliers (IQR rule) | Hours in the future |",
                  "|---|---|---|---|---|---|---|---|---|---|---|"]
        for name, r in per_name.items():
            lines.append(
                f"| {name} | {r['rows']} | {r['first']:%Y-%m-%d %H:%M} | {r['last']:%Y-%m-%d %H:%M} | "
                f"{r['missing_hours']} | {', '.join(r['units'])} | {r['min']:.1f} | {r['mean']:.1f} | "
                f"{r['max']:.1f} | {r['outliers']} | {r['future_hours']} |")
        lines.append("")
    if overlap:
        lines += ["## Overlap of air quality and weather", "",
                  f"Hours present in both tables: {overlap['hours']} "
                  f"(from {overlap['first']:%Y-%m-%d} to {overlap['last']:%Y-%m-%d}).", ""]
    lines += ["## How to read this", "",
              "- *Missing hours*: hours absent between the first and the last hour of that variable.",
              "- *Outliers (IQR rule)*: values more than 1.5 x IQR outside the quartiles. They are **flagged, not removed**: "
              "high PM values during smog episodes are real events, not errors.",
              "- *Hours in the future*: the API also returns the rest of today, which is a model forecast "
              "and gets replaced by the next update.", ""]
    return "\n".join(lines)


def overlap_of(air, wx):
    both = sorted(set(air["time"]) & set(wx["time"]))
    if not both:
        return None
    return {"hours": len(both), "first": both[0], "last": both[-1]}


def main():
    conn = sqlite3.connect(DB_PATH)
    results, frames = {}, {}
    for table, col in TABLES.items():
        df = read_table(conn, table, col)
        frames[table] = df
        results[table] = {name: check_variable(g) for name, g in df.groupby("name")} if not df.empty else {}
    conn.close()
    report = build_report(results, overlap_of(frames["air_quality"], frames["weather"]))
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(report)
    print(f"Saved to {REPORT_PATH}")


if __name__ == "__main__":
    main()
