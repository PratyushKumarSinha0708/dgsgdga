import sys
from datetime import date, time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import processing as proc  # noqa: E402


def ts(s):
    return pd.Timestamp(s, tz="UTC")


def test_latest_before_cutoff_is_chosen():
    fc = pd.DataFrame({
        "publish_time": [ts("2026-01-09 06:00"), ts("2026-01-09 08:30"), ts("2026-01-09 10:00")],
        "start_time": [ts("2026-01-10 12:00")] * 3,
        "forecast": [100.0, 200.0, 999.0],  # 10:00 publish is after the cutoff
    })
    ac = pd.DataFrame({"start_time": [ts("2026-01-10 12:00")], "actual": [150.0]})
    res = proc.latest_forecast(fc, ac, date(2026, 1, 10), time(9, 0))
    assert res["points"][0]["forecast"] == 200.0
    assert "08:30" in res["latest_publish_time"]


def test_horizon_selection_and_metrics():
    fc = pd.DataFrame({
        "publish_time": [ts("2026-01-09 12:00"), ts("2026-01-10 10:00")],
        "start_time": [ts("2026-01-10 12:00")] * 2,
        "forecast": [100.0, 140.0],  # horizons 24h and 2h
    })
    ac = pd.DataFrame({"start_time": [ts("2026-01-10 12:00")], "actual": [150.0]})
    res = proc.accuracy(fc, ac, date(2026, 1, 10), date(2026, 1, 10), horizon_hours=24)
    assert res["metrics"]["bias"] == 50.0
    res = proc.accuracy(fc, ac, date(2026, 1, 10), date(2026, 1, 10), horizon_hours=1)
    assert res["metrics"]["bias"] == 10.0


def test_empty_when_nothing_before_cutoff():
    fc = pd.DataFrame({"publish_time": [ts("2026-01-09 12:00")],
                       "start_time": [ts("2026-01-10 12:00")], "forecast": [1.0]})
    ac = pd.DataFrame({"start_time": [ts("2026-01-10 12:00")], "actual": [1.0]})
    res = proc.latest_forecast(fc, ac, date(2026, 1, 10), time(9, 0))
    assert res["points"] == [] and res["latest_publish_time"] is None
