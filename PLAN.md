# 30-Day Plan: Krakow Air Quality Tracker

One small, real step per day (30-60 minutes) and one commit with a clear message. Rest days are built in so the streak does not break.
Rule: a commit is made only when something real changed (code, analysis, text, test). No empty commits.

**Data sources (free, no key needed; check the current documentation on Day 2):**
- Open-Meteo Air Quality API (PM2.5, PM10, NO2, etc.)
- Open-Meteo Weather API (temperature, wind, humidity)
- Optional later: the Polish national air monitoring data (GIOS), if its API is available

## Phase 1: Data collection (days 1-7)
| Day | Task | Example commit message |
|---|---|---|
| 1 | Create the repo, folders, README with the goal, commit this plan | `Start project: goal, structure, plan` |
| 2 | Read the API docs, write `src/extract.py` that downloads hourly PM2.5 and PM10 for Krakow and saves raw JSON | `Add air quality extract script` |
| 3 | `src/transform.py`: JSON to a pandas table, correct types, handle missing values | `Add transform to clean table` |
| 4 | `src/load.py`: SQLite table with a primary key (time, pollutant), repeatable load without duplicates | `Add SQLite loading` |
| 5 | Add weather data (temperature, wind, humidity) as a second table | `Add weather data` |
| 6 | Make collection incremental (only new hours), add logging and retries | `Add incremental load and logging` |
| 7 | First tests with pytest for transform and load, journal entry for week 1 | `Add tests, week 1 journal` |

## Phase 2: Exploration (days 8-14)
| Day | Task | Example commit message |
|---|---|---|
| 8 | Backfill as much history as the API allows | `Backfill historical data` |
| 9 | Data quality notebook: missing hours, outliers, units | `Add data quality checks` |
| 10 | PM2.5 by hour of day (chart) | `Add hourly pattern analysis` |
| 11 | PM2.5 by day of week and by month | `Add weekday and seasonal patterns` |
| 12 | Compare with the WHO guideline and the EU limit (look up the current values and cite the source in the README): share of days above the limits | `Add limit exceedance analysis` |
| 13 | Relationship with weather: wind and temperature vs PM2.5 | `Add weather correlation` |
| 14 | Clean the notebook, write the first findings in the README, journal entry for week 2 | `Add first findings` |

## Phase 3: Deeper analysis with SQL (days 15-21)
| Day | Task | Example commit message |
|---|---|---|
| 15 | SQL views: daily average and 7-day rolling average (window functions) | `Add SQL views with rolling average` |
| 16 | Ten worst days and the weather on those days | `Add worst days analysis` |
| 17 | Heating season vs the rest of the year, with a permutation test (as in the support tickets project) | `Add heating season comparison` |
| 18 | Heatmap: hour of day vs month | `Add hour-month heatmap` |
| 19 | Add a second city for comparison (for example Warsaw) | `Add second city` |
| 20 | Comparison chart and findings for the two cities | `Add city comparison` |
| 21 | Refactor the code, more tests, update the README, journal entry for week 3 | `Refactor and update docs` |

## Phase 4: Dashboard and forecast (days 22-28)
| Day | Task | Example commit message |
|---|---|---|
| 22 | Streamlit app skeleton that reads from SQLite | `Add Streamlit skeleton` |
| 23 | Dashboard: last 24 hours chart and key numbers | `Add last 24h view` |
| 24 | Dashboard: filters by date range and city | `Add filters` |
| 25 | Baseline forecast ("tomorrow equals today") and an error metric | `Add baseline forecast` |
| 26 | Simple model (linear regression or random forest) with weather features and a time-based train/test split | `Add forecast model` |
| 27 | Compare the model with the baseline, write honest conclusions (it may not win, and that is a valid result) | `Add model evaluation` |
| 28 | Automate daily data collection (cron on Mac or GitHub Actions), journal entry for week 4 | `Add scheduled collection` |

## Phase 5: Finish (days 29-30)
| Day | Task | Example commit message |
|---|---|---|
| 29 | README: screenshots of the dashboard, key findings with real numbers, limitations, how to run | `Write final README` |
| 30 | Final polish, tag release v1.0, add the project to the CV and the learning journal | `Release v1.0` |

## If a day is missed
Do not skip the task, move it to the next day. A finished project matters more than a perfect streak.

## Honesty notes for the README
- Describe what the data covers and where it comes from.
- Report the limits: model error, missing data, short history.
- Say how you worked on the project if asked at an interview, and be able to explain every part of the code.
