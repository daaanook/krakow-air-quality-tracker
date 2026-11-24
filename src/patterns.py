"""Day 11: PM2.5 by day of the week and by month (charts + tables).

Run from the project folder (with the virtual environment on):
    python3 src/patterns.py

Works with daily means of COMPLETE days only (24 hourly values), so a half-finished day
(today) does not distort the result.
"""
import calendar
import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from hourly import read_pollutant  # noqa: E402
from load import DB_PATH  # noqa: E402

WEEKDAY_IMAGE = Path("images/pm25_by_weekday.png")
MONTH_IMAGE = Path("images/pm25_by_month.png")
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def daily_means(df):
    """One row per COMPLETE day (24 values): date and mean value."""
    day = df["time"].dt.normalize()
    grouped = df.groupby(day)["value"].agg(mean="mean", n="count")
    complete = grouped[grouped["n"] == 24]
    out = complete[["mean"]].rename(columns={"mean": "value"})
    out.index.name = "date"
    return out


def by_weekday(daily):
    """Mean of daily means for each day of the week, and the number of days behind it."""
    g = daily.groupby(daily.index.day_of_week)["value"].agg(mean="mean", median="median", days="count")
    return g.reindex(range(7)).rename(index=dict(enumerate(WEEKDAYS)))


def by_month(daily):
    """Mean of daily means for each month. `days` and `of` show how complete the month is."""
    periods = daily.index.to_period("M")
    g = daily.groupby(periods)["value"].agg(mean="mean", median="median", days="count")
    g["of"] = [calendar.monthrange(p.year, p.month)[1] for p in g.index]
    g.index = [f"{p.year}-{p.month:02d}" for p in g.index]
    return g


def _style(ax, title, ylabel):
    ax.set_title(title, loc="left")
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)


def plot_bars(table, path, title, labels=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    labels = labels or list(table.index)
    ax.bar(labels, table["mean"], color="#2a6f97")
    for x, v in zip(labels, table["mean"]):
        if pd.notna(v):
            ax.text(x, v, f"{v:.1f}", ha="center", va="bottom", fontsize=9)
    _style(ax, title, "PM2.5, μg/m³ (mean of daily means)")
    fig.text(0.01, 0.01, "Source: CAMS model via Open-Meteo (model output, not sensor measurements)",
             fontsize=8, color="#666666")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main():
    conn = sqlite3.connect(DB_PATH)
    df = read_pollutant(conn)
    conn.close()
    daily = daily_means(df)
    if daily.empty:
        print("No complete days. Run  python3 src/update.py  first.")
        return
    wd, mo = by_weekday(daily), by_month(daily)

    print(f"{len(daily)} complete days ({daily.index.min():%Y-%m-%d} to {daily.index.max():%Y-%m-%d})\n")
    print("PM2.5 by day of the week:")
    print(wd.round(1).to_string(), "\n")
    print("PM2.5 by month (days = days with data, of = days in the month):")
    print(mo.round(1).to_string(), "\n")

    plot_bars(wd, WEEKDAY_IMAGE, f"Krakow: PM2.5 by day of the week ({len(daily)} days)")
    month_labels = [f"{m}\n({int(r['days'])}/{int(r['of'])} days)" for m, r in mo.iterrows()]
    plot_bars(mo, MONTH_IMAGE, "Krakow: PM2.5 by month", labels=month_labels)
    print(f"Charts saved to {WEEKDAY_IMAGE} and {MONTH_IMAGE}")


if __name__ == "__main__":
    main()
