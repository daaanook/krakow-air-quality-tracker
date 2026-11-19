"""Tests for src/http_utils.py and src/update.py. Run from the project folder:  python3 -m pytest"""
import sys
from datetime import date
from pathlib import Path
from unittest import mock

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import http_utils  # noqa: E402
import load  # noqa: E402
import update  # noqa: E402


def answer(status=200, data=None):
    r = mock.Mock(status_code=status)
    r.json.return_value = data or {"ok": True}
    if status >= 400:
        r.raise_for_status.side_effect = requests.HTTPError(f"{status}", response=r)
    return r


def test_retry_after_connection_error_then_success():
    sleeps = []
    with mock.patch.object(requests, "get", side_effect=[requests.ConnectionError("down"), answer()]) as get:
        result = http_utils.get_json("http://x", {}, sleep=sleeps.append)
    assert result == {"ok": True}
    assert get.call_count == 2
    assert sleeps == [2]


def test_server_error_is_retried_and_gives_up_after_all_attempts():
    with mock.patch.object(requests, "get", return_value=answer(503)) as get:
        with pytest.raises(requests.HTTPError):
            http_utils.get_json("http://x", {}, attempts=3, sleep=lambda s: None)
    assert get.call_count == 3


def test_client_error_is_not_retried():
    with mock.patch.object(requests, "get", return_value=answer(400)) as get:
        with pytest.raises(requests.HTTPError):
            http_utils.get_json("http://x", {}, sleep=lambda s: None)
    assert get.call_count == 1


def test_days_to_fetch_empty_table_uses_default():
    conn = load.connect(":memory:")
    assert update.days_to_fetch(conn, "air_quality", today=date(2026, 11, 19)) == update.DEFAULT_DAYS


def test_days_to_fetch_missing_table_uses_default():
    conn = load.connect(":memory:")
    assert update.days_to_fetch(conn, "no_such_table", today=date(2026, 11, 19)) == update.DEFAULT_DAYS


def test_days_to_fetch_counts_missing_days():
    conn = load.connect(":memory:")
    conn.execute("INSERT INTO air_quality VALUES ('2026-11-17 23:00:00','pm10',10,'x','t')")
    assert update.days_to_fetch(conn, "air_quality", today=date(2026, 11, 19)) == 3
    assert update.days_to_fetch(conn, "air_quality", today=date(2026, 11, 17)) == 1


def test_days_to_fetch_is_limited_to_api_maximum():
    conn = load.connect(":memory:")
    conn.execute("INSERT INTO air_quality VALUES ('2026-01-01 00:00:00','pm10',10,'x','t')")
    assert update.days_to_fetch(conn, "air_quality", today=date(2026, 11, 19)) == update.MAX_DAYS
