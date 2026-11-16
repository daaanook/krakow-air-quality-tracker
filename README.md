# Krakow Air Quality Tracker

Work in progress (started November 2026). A Python project that collects air quality and weather data for Krakow, stores it in a SQL database, analyses patterns (time of day, season, weather) and shows the results in a dashboard.

**Tools:** Python (requests, pandas, matplotlib, Streamlit, scikit-learn), SQL (SQLite), pytest

See [PLAN.md](PLAN.md) for the 30-day plan. Findings and how to run will be added as the project grows.

## Data

Source: [Open-Meteo Air Quality API](https://open-meteo.com/en/docs/air-quality-api).

- **What the numbers are:** model output from the CAMS European air quality forecast
  (Copernicus), not measurements from sensors on the ground. Resolution is about 11 km,
  hourly.
- **Pollutants:** PM10 and PM2.5, in μg/m³.
- **Location:** Krakow (latitude 50.0647, longitude 19.9450).
- **Time zone:** Europe/Warsaw.
- **Limit of one request:** the API returns up to 92 past days (`past_days`).

Attribution: CAMS European air quality forecasts, ENSEMBLE data, via Open-Meteo.
The API is free for non-commercial use; this is a portfolio project.
