"""Day 12: share of days with daily mean PM2.5 / PM10 above the WHO guideline and the EU limit values.

Run from the project folder (with the virtual environment on):
    python3 src/limits.py

Thresholds (24-hour means, μg/m³) - see the "Sources" section of the README:
    PM2.5: WHO guideline 2021 = 15;  EU Directive 2024/2881 (from 2030) = 25.
           The current EU Directive 2008/50/EC has no daily limit for PM2.5.
    PM10:  WHO guideline 2021 = 45;  EU Directive 2008/50/EC = 50;  EU Directive 2024/2881 (from 2030) = 45.
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

IMAGE_PATH = Path("images/days_above_limits.png")
REPORT_PATH = Path("reports/limit_exceedance.md")

# (pollutant, threshold name, value in μg/m³)
THRESHOLDS = [
    ("pm2_5", "WHO guideline 2021 (24 h)", 15),
    ("pm2_5", "EU limit from 2030 (24 h)", 25),
    ("pm10", "WHO guideline 2021 (24 h)", 45),
    ("pm10", "EU limit today (24 h)", 50),
    ("pm10", "EU limit from 2030 (24 h)", 45),
]


def days_above(daily, threshold):
    """Number of days whose daily mean is strictly above the threshold, and the share of all days."""
    total = len(daily)
    above = int((daily["value"] > threshold).sum())
    return above, total, (above / total * 100 if total else float("nan"))


def exceedance_table(daily_by_pollutant):
    """One row per threshold: pollutant, threshold, days above, days in total, share in percent."""
    rows = []
    for pollutant, name, value in THRESHOLDS:
        daily = daily_by_pollutant.get(pollutant)
        if daily is None or daily.empty:
            continue
        above, total, share = days_above(daily, value)
        rows.append({"pollutant": pollutant, "threshold": name, "value": value,
                     "days_above": above, "days": total, "share": share})
    return pd.DataFrame(rows)


def to_markdown(table, first, last):
    lines = ["# Days above the limits", "",
             f"Daily means of complete days, {first:%Y-%m-%d} to {last:%Y-%m-%d}.", "",
             "| Pollutant | Threshold | Value, μg/m³ | Days above | Days in total | Share of days |",
             "|---|---|---|---|---|---|"]
    for r in table.itertuples():
        lines.append(f"| {r.pollutant} | {r.threshold} | {r.value} | {r.days_above} | {r.days} | {r.share:.0f} % |")
    lines += ["", "This is a comparison of model values with thresholds, not a legal assessment of compliance: "
              "the EU limits allow a number of exceedance days per year and are checked at monitoring stations.", ""]
    return "\n".join(lines)


def plot_table(table, path=IMAGE_PATH):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    labels = [f"{r.pollutant.upper().replace('_', '.')}\n{r.threshold}\n> {r.value} μg/m³" for r in table.itertuples()]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(range(len(table)), table["share"], color="#2a6f97")
    for i, v in enumerate(table["share"]):
        ax.text(i, v, f"{v:.0f} %", ha="center", va="bottom", fontsize=10)
    ax.set_xticks(range(len(table)))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylabel("Share of days above the threshold, %")
    ax.set_ylim(0, 105)
    ax.set_title("Krakow: share of days above WHO and EU thresholds", loc="left")
    ax.grid(axis="y", alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.01, "Source: CAMS model via Open-Meteo (model output, not sensor measurements)",
             fontsize=8, color="#666666")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main():
    conn = sqlite3.connect(DB_PATH)
    daily = {p: daily_means(read_pollutant(conn, p)) for p in ("pm2_5", "pm10")}
    conn.close()
    table = exceedance_table(daily)
    if table.empty:
        print("No complete days. Run  python3 src/update.py  first.")
        return
    first = min(d.index.min() for d in daily.values() if not d.empty)
    last = max(d.index.max() for d in daily.values() if not d.empty)
    report = to_markdown(table, first, last)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    plot_table(table)
    print(report)
    print(f"Saved to {REPORT_PATH} and {IMAGE_PATH}")


if __name__ == "__main__":
    main()
