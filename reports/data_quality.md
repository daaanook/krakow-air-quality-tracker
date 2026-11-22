# Data quality report

Created: 2026-11-22 22:41

## Table `air_quality`

| Variable | Rows | First hour | Last hour | Missing hours | Unit | Min | Mean | Max | Outliers (IQR rule) | Hours in the future |
|---|---|---|---|---|---|---|---|---|---|---|
| pm10 | 2232 | 2026-08-21 00:00 | 2026-11-21 23:00 | 0 | μg/m³ | 3.4 | 28.1 | 166.6 | 144 | 0 |
| pm2_5 | 2232 | 2026-08-21 00:00 | 2026-11-21 23:00 | 0 | μg/m³ | 2.6 | 22.8 | 132.9 | 135 | 0 |

## Table `weather`

| Variable | Rows | First hour | Last hour | Missing hours | Unit | Min | Mean | Max | Outliers (IQR rule) | Hours in the future |
|---|---|---|---|---|---|---|---|---|---|---|
| relative_humidity_2m | 1751 | 2026-09-10 01:00 | 2026-11-21 23:00 | 0 | % | 24.0 | 76.7 | 100.0 | 13 | 0 |
| temperature_2m | 1751 | 2026-09-10 01:00 | 2026-11-21 23:00 | 0 | °C | -2.7 | 10.2 | 24.4 | 11 | 0 |
| wind_speed_10m | 1751 | 2026-09-10 01:00 | 2026-11-21 23:00 | 0 | km/h | 0.0 | 7.8 | 24.1 | 41 | 0 |

## Overlap of air quality and weather

Hours present in both tables: 1751 (from 2026-09-10 to 2026-11-21).

## How to read this

- *Missing hours*: hours absent between the first and the last hour of that variable.
- *Outliers (IQR rule)*: values more than 1.5 x IQR outside the quartiles. They are **flagged, not removed**: high PM values during smog episodes are real events, not errors.
- *Hours in the future*: the API also returns the rest of today, which is a model forecast and gets replaced by the next update.
