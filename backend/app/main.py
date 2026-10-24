import datetime as dt
from functools import lru_cache

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import config, elexon, processing as proc
from .schemas import AccuracyResponse, ByHorizonResponse, LatestForecastResponse

app = FastAPI(title="Wind Forecast Desk API", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])


@lru_cache(maxsize=1)
def get_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Use the committed snapshot if present; otherwise fetch live (and try to save)."""
    fc_path, ac_path = config.DATA_DIR / "forecasts.csv", config.DATA_DIR / "actuals.csv"
    if fc_path.exists() and ac_path.exists():
        fc, ac = pd.read_csv(fc_path), pd.read_csv(ac_path)
        fc["publish_time"] = pd.to_datetime(fc["publish_time"], utc=True)
        fc["start_time"] = pd.to_datetime(fc["start_time"], utc=True)
        ac["start_time"] = pd.to_datetime(ac["start_time"], utc=True)
        return fc, ac

    fc = elexon.fetch_forecasts(config.FORECAST_PUBLISH_FROM, config.FORECAST_PUBLISH_TO)
    ac = elexon.fetch_actuals(config.ACTUALS_FROM, config.ACTUALS_TO)
    try:
        config.DATA_DIR.mkdir(exist_ok=True)
        fc.to_csv(fc_path, index=False)
        ac.to_csv(ac_path, index=False)
    except OSError:
        pass  # read-only filesystem (serverless); in-memory cache still works
    return fc, ac


def _parse_cutoff(s: str) -> dt.time:
    try:
        return dt.time.fromisoformat(s)
    except ValueError:
        raise HTTPException(400, "cutoff must be HH:MM, e.g. 09:00")


def _check_range(start: dt.date, end: dt.date):
    if start > end:
        raise HTTPException(400, "start must be on or before end")
    if start < config.MIN_DELIVERY_DATE or end > config.MAX_DELIVERY_DATE:
        raise HTTPException(
            400, f"Dates must be within {config.MIN_DELIVERY_DATE} and {config.MAX_DELIVERY_DATE}"
        )
    if (end - start).days > config.MAX_RANGE_DAYS:
        raise HTTPException(400, "Date range too large")


def _load():
    try:
        return get_data()
    except Exception as e:  # upstream failure
        raise HTTPException(502, f"Could not load Elexon data: {e}")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/meta")
def meta():
    return {
        "min_date": config.MIN_DELIVERY_DATE.isoformat(),
        "max_date": config.MAX_DELIVERY_DATE.isoformat(),
        "default_cutoff": config.DEFAULT_CUTOFF,
    }


@app.get("/api/forecast/latest", response_model=LatestForecastResponse)
def forecast_latest(delivery: dt.date = Query(alias="date"), cutoff: str = config.DEFAULT_CUTOFF):
    _check_range(delivery, delivery)
    fc, ac = _load()
    return proc.latest_forecast(fc, ac, delivery, _parse_cutoff(cutoff))


@app.get("/api/accuracy", response_model=AccuracyResponse)
def accuracy(start: dt.date, end: dt.date, horizon_hours: float = Query(24, ge=0.5, le=48)):
    _check_range(start, end)
    fc, ac = _load()
    return proc.accuracy(fc, ac, start, end, horizon_hours)


@app.get("/api/accuracy/by-horizon", response_model=ByHorizonResponse)
def accuracy_by_horizon(start: dt.date, end: dt.date):
    _check_range(start, end)
    fc, ac = _load()
    return proc.accuracy_by_horizon(fc, ac, start, end)
