"""Day 13: how does PM2.5 relate to temperature, wind and humidity? (daily means)

Run from the project folder (with the virtual environment on):
    python3 src/weather_corr.py

Uses complete days (24 values) that exist in BOTH tables, so the period starts where the weather data starts.
Saves images/pm25_vs_weather.png and reports/weather_correlation.md.
"""
import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from hourly import read_pollutant  # noqa: E402
from load import DB_PATH  # noqa: E402
from patterns import daily_means  # noqa: E402

IMAGE_PATH = Path("images/pm25_vs_weather.png")
REPORT_PATH = Path("reports/weather_correlation.md")
VARIABLES = {
    "temperature_2m": "Temperature, °C",
    "wind_speed_10m": "Wind speed, km/h",
    "relative_humidity_2m": "Relative humidity, %",
}
WIND_BINS = [0, 5, 10, float("inf")]
WIND_LABELS = ["calm (< 5 km/h)", "light (5-10 km/h)", "windy (> 10 km/h)"]


def read_weather_daily(conn, variable):
    """Daily means of one weather variable (complete days only)."""
    df = pd.read_sql_query("SELECT time, value FROM weather WHERE variable = ? ORDER BY time", conn, params=(variable,))
    df["time"] = pd.to_datetime(df["time"])
    return daily_means(df)


def build_dataset(pm25_daily, weather_daily):
    """One row per day with PM2.5 and every weather variable. Only days present in all of them."""
    data = pm25_daily.rename(columns={"value": "pm2_5"})
    for variable, daily in weather_daily.items():
        data = data.join(daily.rename(columns={"value": variable}), how="inner")
    return data


def correlations(data):
    """Spearman rank correlation of PM2.5 with each weather variable.

    Spearman is used because it does not assume a straight-line relationship and is less
    sensitive to a few extreme days than the ordinary (Pearson) correlation.
    """
    weather_cols = [c for c in data.columns if c != "pm2_5"]
    pm_rank = data["pm2_5"].rank()  # Spearman = ordinary correlation of the ranks (no extra libraries needed)
    return data[weather_cols].apply(lambda col: col.rank().corr(pm_rank)).rename("spearman")


def pm25_by_wind(data):
    """Mean and median PM2.5 for calm, light and windy days."""
    groups = pd.cut(data["wind_speed_10m"], bins=WIND_BINS, labels=WIND_LABELS, right=False)
    return data.groupby(groups, observed=False)["pm2_5"].agg(mean="mean", median="median", days="count")


def plot_scatter(data, path=IMAGE_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), sharey=True)
    for ax, (variable, label) in zip(axes, VARIABLES.items()):
        ax.scatter(data[variable], data["pm2_5"], s=16, color="#2a6f97", alpha=0.7)
        ax.set_xlabel(label)
        ax.grid(alpha=0.3)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("PM2.5 daily mean, μg/m³")
    fig.suptitle(f"Krakow: PM2.5 and weather, one point per day ({len(data)} days)", x=0.01, ha="left")
    fig.text(0.01, 0.01, "Source: CAMS model and Open-Meteo weather (model output)", fontsize=8, color="#666666")
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def to_markdown(data, corr, wind):
    lines = ["# PM2.5 and weather", "",
             f"{len(data)} complete days, {data.index.min():%Y-%m-%d} to {data.index.max():%Y-%m-%d} (daily means).", "",
             "## Spearman correlation with PM2.5", "", "| Variable | Correlation |", "|---|---|"]
    for variable, value in corr.items():
        lines.append(f"| {VARIABLES[variable]} | {value:+.2f} |")
    lines += ["", "## PM2.5 by wind speed", "", "| Wind | Mean PM2.5 | Median PM2.5 | Days |", "|---|---|---|---|"]
    for name, r in wind.iterrows():
        if r["days"] == 0:
            lines.append(f"| {name} | - | - | 0 |")  # no such days in the data
        else:
            lines.append(f"| {name} | {r['mean']:.1f} | {r['median']:.1f} | {int(r['days'])} |")
    lines += ["", "Correlation is not causation. Over autumn the temperature falls while many other things change "
              "(heating, day length), so a relationship with temperature may partly reflect the season.", ""]
    return "\n".join(lines)


def main():
    conn = sqlite3.connect(DB_PATH)
    pm25 = daily_means(read_pollutant(conn, "pm2_5"))
    weather_daily = {v: read_weather_daily(conn, v) for v in VARIABLES}
    conn.close()
    data = build_dataset(pm25, weather_daily)
    if len(data) < 10:
        print(f"Only {len(data)} days with both air quality and weather. Run  python3 src/backfill.py  first.")
        return
    corr, wind = correlations(data), pm25_by_wind(data)
    report = to_markdown(data, corr, wind)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    plot_scatter(data)
    print(report)
    print(f"Saved to {REPORT_PATH} and {IMAGE_PATH}")


if __name__ == "__main__":
    main()
