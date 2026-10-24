"""
All business logic. UTC internally; UK time only for defining the delivery day,
the cutoff, and display labels.

Sign convention: error = actual - forecast
  positive -> wind higher than forecast (under-forecast)
  negative -> wind lower than forecast (over-forecast; the risky direction for a
              buyer, who must then buy the shortfall)
"""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

UK = ZoneInfo("Europe/London")


def uk_day_bounds_utc(d: date) -> tuple[pd.Timestamp, pd.Timestamp]:
    """[00:00, 24:00) of a UK local day in UTC (handles 23h/25h DST days)."""
    lo = datetime.combine(d, time(0, 0), tzinfo=UK)
    hi = datetime.combine(d + timedelta(days=1), time(0, 0), tzinfo=UK)
    return pd.Timestamp(lo).tz_convert("UTC"), pd.Timestamp(hi).tz_convert("UTC")


def decision_cutoff_utc(delivery: date, cutoff: time) -> pd.Timestamp:
    """Cutoff = <cutoff> UK time on the day BEFORE delivery."""
    c = datetime.combine(delivery - timedelta(days=1), cutoff, tzinfo=UK)
    return pd.Timestamp(c).tz_convert("UTC")


def _uk(ts: pd.Timestamp) -> pd.Timestamp:
    return ts.tz_convert("Europe/London")


def _clean(x):
    return None if x is None or pd.isna(x) else float(x)


def forecast_step_minutes(fc: pd.DataFrame) -> int:
    starts = fc["start_time"].drop_duplicates().sort_values()
    if len(starts) < 2:
        return 60
    return int(starts.diff().dropna().median().total_seconds() // 60) or 60


def actuals_on_forecast_grid(ac: pd.DataFrame, step_min: int) -> pd.Series:
    """Actuals are 30-min. If forecasts are hourly, average the two half-hours."""
    s = ac.set_index("start_time")["actual"].sort_index()
    return s.resample("1h").mean() if step_min >= 60 else s



def latest_forecast(fc, ac, delivery: date, cutoff: time) -> dict:
    lo, hi = uk_day_bounds_utc(delivery)
    cut = decision_cutoff_utc(delivery, cutoff)

    f = fc[(fc.start_time >= lo) & (fc.start_time < hi) & (fc.publish_time <= cut)]
    f = (f.sort_values(["start_time", "publish_time"])
          .drop_duplicates("start_time", keep="last"))

    base = {
        "delivery_date": delivery.isoformat(),
        "cutoff_utc": cut.isoformat(),
        "cutoff_uk": _uk(cut).isoformat(),
        "latest_publish_time": None,
        "earliest_publish_time": None,
        "points": [],
    }
    if f.empty:
        return base

    act = actuals_on_forecast_grid(ac, forecast_step_minutes(fc))
    points = []
    for r in f.itertuples():
        a = act.get(r.start_time, np.nan)
        points.append({
            "time": _uk(r.start_time).strftime("%H:%M"),
            "target_time": _uk(r.start_time).isoformat(),
            "forecast": _clean(r.forecast),
            "actual": _clean(a),
            "publishTime": _uk(r.publish_time).isoformat(),
            "horizon_hours": round((r.start_time - r.publish_time).total_seconds() / 3600, 2),
        })
    base["points"] = points
    base["latest_publish_time"] = _uk(f.publish_time.max()).isoformat()
    base["earliest_publish_time"] = _uk(f.publish_time.min()).isoformat()
    return base



def _with_horizon(fc: pd.DataFrame) -> pd.DataFrame:
    out = fc.copy()
    out["horizon"] = (out.start_time - out.publish_time).dt.total_seconds() / 3600
    return out


def _pick_at_horizon(fc_h: pd.DataFrame, h: float) -> pd.DataFrame:
    """For every target time: latest forecast published at least h hours earlier."""
    f = fc_h[fc_h.horizon >= h]
    return (f.sort_values(["start_time", "publish_time"])
             .drop_duplicates("start_time", keep="last"))


def _joined(fc_h, ac, start: date, end: date, h: float) -> pd.DataFrame:
    lo, _ = uk_day_bounds_utc(start)
    _, hi = uk_day_bounds_utc(end)
    f = _pick_at_horizon(fc_h[(fc_h.start_time >= lo) & (fc_h.start_time < hi)], h)
    act = actuals_on_forecast_grid(ac, forecast_step_minutes(fc_h)).rename("actual")
    df = f.merge(act, left_on="start_time", right_index=True, how="inner").dropna(subset=["actual"])
    df["error"] = df["actual"] - df["forecast"]
    return df


def error_metrics(err: pd.Series) -> dict | None:
    if err.empty:
        return None
    a = err.abs()
    return {
        "n": int(len(err)),
        "mae": float(a.mean()),
        "rmse": float(np.sqrt((err ** 2).mean())),
        "bias": float(err.mean()),
        "p5": float(np.percentile(err, 5)),
        "p50": float(np.percentile(err, 50)),
        "p95": float(np.percentile(err, 95)),
        "abs_p90": float(np.percentile(a, 90)),
        "abs_p99": float(np.percentile(a, 99)),
    }


def accuracy(fc, ac, start: date, end: date, horizon_hours: float, bins: int = 20) -> dict:
    df = _joined(_with_horizon(fc), ac, start, end, horizon_hours)
    metrics = error_metrics(df["error"])
    if metrics is None:
        return {"horizon_hours": horizon_hours, "metrics": None, "series": [], "histogram": []}

    counts, edges = np.histogram(df["error"], bins=bins)
    histogram = [
        {"bin": int(round((edges[i] + edges[i + 1]) / 2)), "count": int(c)}
        for i, c in enumerate(counts)
    ]
    df = df.sort_values("start_time")
    series = [
        {"time": _uk(r.start_time).strftime("%d %b %H:%M"),
         "forecast": _clean(r.forecast), "actual": _clean(r.actual),
         "publishTime": _uk(r.publish_time).isoformat()}
        for r in df.itertuples()
    ]
    return {"horizon_hours": horizon_hours, "metrics": metrics,
            "series": series, "histogram": histogram}


def accuracy_by_horizon(fc, ac, start: date, end: date, max_h: int = 48) -> dict:
    fc_h = _with_horizon(fc)
    rows = []
    for h in range(1, max_h + 1):
        m = error_metrics(_joined(fc_h, ac, start, end, h)["error"])
        if m:
            rows.append({"horizon": h, **m})
    return {"points": rows}
