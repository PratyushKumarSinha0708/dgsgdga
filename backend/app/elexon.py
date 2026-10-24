import time
from datetime import date, datetime, timedelta, timezone

import httpx
import pandas as pd

from .config import BASE_URL


def _get(client: httpx.Client, path: str, params: dict, retries: int = 4) -> list[dict]:
    for attempt in range(retries):
        try:
            r = client.get(f"{BASE_URL}{path}", params=params, timeout=60)
            r.raise_for_status()
            data = r.json()
            return data if isinstance(data, list) else data.get("data", [])
        except (httpx.HTTPError, ValueError):
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)
    return []


def _chunks(start: date, end: date, days: int):
    cur = start
    while cur <= end:
        nxt = min(cur + timedelta(days=days - 1), end)
        yield cur, nxt
        cur = nxt + timedelta(days=1)


def fetch_actuals(start: date, end: date) -> pd.DataFrame:
    rows: list[dict] = []
    with httpx.Client() as client:
        for a, b in _chunks(start, end, 7):
            rows += _get(client, "/datasets/FUELHH/stream", {
                "settlementDateFrom": a.isoformat(),
                "settlementDateTo": b.isoformat(),
                "fuelType": "WIND",
            })
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["start_time", "actual"])
    df = df[df["fuelType"] == "WIND"].copy()
    df["start_time"] = pd.to_datetime(df["startTime"], utc=True)
    df["actual"] = pd.to_numeric(df["generation"], errors="coerce")
    if "publishTime" in df:
        df = df.sort_values("publishTime")
    return (df.drop_duplicates("start_time", keep="last")[["start_time", "actual"]]
              .sort_values("start_time").reset_index(drop=True))


def fetch_forecasts(pub_from: date, pub_to: date) -> pd.DataFrame:
    rows: list[dict] = []
    with httpx.Client() as client:
        for a, b in _chunks(pub_from, pub_to, 3):
            start_dt = datetime(a.year, a.month, a.day, tzinfo=timezone.utc)
            end_dt = datetime(b.year, b.month, b.day, tzinfo=timezone.utc) + timedelta(days=1)
            rows += _get(client, "/datasets/WINDFOR/stream", {
                "publishDateTimeFrom": start_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "publishDateTimeTo": end_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            })
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["publish_time", "start_time", "forecast"])
    df["publish_time"] = pd.to_datetime(df["publishTime"], utc=True)
    df["start_time"] = pd.to_datetime(df["startTime"], utc=True)
    df["forecast"] = pd.to_numeric(df["generation"], errors="coerce")
    df = df.dropna(subset=["forecast"])
    return (df.drop_duplicates(["publish_time", "start_time"], keep="last")
              [["publish_time", "start_time", "forecast"]]
              .sort_values(["start_time", "publish_time"]).reset_index(drop=True))
