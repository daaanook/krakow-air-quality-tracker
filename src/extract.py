"""Day 2: download hourly air quality data for Krakow from the Open-Meteo Air Quality API.

Docs: https://open-meteo.com/en/docs/air-quality-api

Run from the project folder:
    python3 src/extract.py
    python3 src/extract.py --past-days 30
"""
import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

import requests

log = logging.getLogger(__name__)

URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
KRAKOW = {"latitude": 50.0647, "longitude": 19.9450}
POLLUTANTS = ["pm10", "pm2_5"]
RAW_DIR = Path("data/raw")


def build_params(past_days):
    """Query parameters for the API request."""
    return {
        **KRAKOW,
        "hourly": ",".join(POLLUTANTS),
        "past_days": past_days,
        "forecast_days": 1,
        "timezone": "Europe/Warsaw",
    }


def fetch(past_days=7, timeout=30):
    """Download the data and return it as a Python dictionary."""
    response = requests.get(URL, params=build_params(past_days), timeout=timeout)
    response.raise_for_status()  # stops with an error for 4xx / 5xx answers
    return response.json()


def save_raw(payload, raw_dir=RAW_DIR):
    """Save the unchanged API answer to data/raw/ so it can always be re-processed."""
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = raw_dir / f"krakow_air_quality_{stamp}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def main(argv=None):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Download Krakow air quality data")
    parser.add_argument("--past-days", type=int, default=7, help="how many past days to download")
    args = parser.parse_args(argv)

    payload = fetch(args.past_days)
    hourly = payload.get("hourly", {})
    log.info("Downloaded %d hourly rows", len(hourly.get("time", [])))
    log.info("Units: %s", payload.get("hourly_units"))
    path = save_raw(payload)
    log.info("Saved to %s", path)


if __name__ == "__main__":
    main()
