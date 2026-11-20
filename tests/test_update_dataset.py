"""End-to-end test of one update run with a fake API. Run from the project folder:  python3 -m pytest"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import load  # noqa: E402
import transform  # noqa: E402
import update  # noqa: E402

PAYLOAD = {
    "hourly_units": {"time": "iso8601", "pm10": "μg/m³", "pm2_5": "μg/m³"},
    "hourly": {
        "time": ["2026-11-14T00:00", "2026-11-14T01:00"],
        "pm10": [30.0, 28.0],
        "pm2_5": [22.0, None],  # one missing value
    },
}


def run_once(conn, requested):
    def fake_fetch(days):
        requested.append(days)
        return PAYLOAD

    return update.update_dataset(
        "air quality", conn, "air_quality",
        fake_fetch, lambda payload: None, transform.transform, load.load,
    )


def test_first_run_loads_rows_and_asks_for_default_days():
    conn = load.connect(":memory:")
    requested = []
    assert run_once(conn, requested) == 3  # 4 values, 1 missing is dropped
    assert requested == [update.DEFAULT_DAYS]


def test_second_run_adds_nothing_and_asks_for_fewer_days():
    conn = load.connect(":memory:")
    requested = []
    run_once(conn, requested)
    assert run_once(conn, requested) == 0
    assert requested[1] <= update.MAX_DAYS
    assert conn.execute("SELECT COUNT(*) FROM air_quality").fetchone()[0] == 3
