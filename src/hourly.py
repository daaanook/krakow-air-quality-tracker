"""Day 10: average PM2.5 by hour of the day (chart + table).

Run from the project folder (with the virtual environment on):
    python3 src/hourly.py

Saves the chart to images/pm25_by_hour.png and prints the average for each hour.
"""
import sqlite3
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # draw to a file, no window needed
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from load import DB_PATH  # noqa: E402

IMAGE_PATH = Path("images/pm25_by_hour.png")


def read_pollutant(conn, pollutant="pm2_5", now=None):
    """Hourly values of one pollutant. Hours that have not happened yet (forecast) are left out."""
    now = now or datetime.now()
    df = pd.read_sql_query(
        "SELECT time, value FROM air_quality WHERE pollutant = ? ORDER BY time", conn, params=(pollutant,)
    )
    df["time"] = pd.to_datetime(df["time"])
    return df[df["time"] <= now].reset_index(drop=True)


def hourly_profile(df):
    """Mean, median and number of values for each hour of the day (0-23)."""
    grouped = df.groupby(df["time"].dt.hour)["value"]
    profile = grouped.agg(mean="mean", median="median", n="count")
    profile.index.name = "hour"
    return profile


def plot_profile(profile, path=IMAGE_PATH, days=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(profile.index, profile["mean"], marker="o", color="#2a6f97", label="Mean")
    ax.plot(profile.index, profile["median"], marker="", linestyle="--", color="#8a8f98", label="Median")
    ax.set_xticks(range(0, 24, 2))
    ax.set_xlabel("Hour of the day (local time, Europe/Warsaw)")
    ax.set_ylabel("PM2.5, μg/m³")
    subtitle = f" ({days} days)" if days else ""
    ax.set_title(f"Krakow: PM2.5 by hour of the day{subtitle}", loc="left")
    ax.grid(axis="y", alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False)
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
    if df.empty:
        print("No PM2.5 data. Run  python3 src/update.py  first.")
        return
    profile = hourly_profile(df)
    days = df["time"].dt.normalize().nunique()
    path = plot_profile(profile, days=days)

    print(f"PM2.5 by hour of the day, {days} days of data ({df['time'].min():%Y-%m-%d} to {df['time'].max():%Y-%m-%d})")
    print(profile.round(1).to_string())
    print()
    best, worst = profile["mean"].idxmin(), profile["mean"].idxmax()
    print(f"Lowest average: hour {best}:00 = {profile.loc[best, 'mean']:.1f} μg/m³")
    print(f"Highest average: hour {worst}:00 = {profile.loc[worst, 'mean']:.1f} μg/m³")
    print(f"Chart saved to {path}")


if __name__ == "__main__":
    main()
