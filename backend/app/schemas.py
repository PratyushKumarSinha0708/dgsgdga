from pydantic import BaseModel


class Point(BaseModel):
    time: str
    target_time: str
    forecast: float | None
    actual: float | None
    publishTime: str
    horizon_hours: float


class LatestForecastResponse(BaseModel):
    delivery_date: str
    cutoff_utc: str
    cutoff_uk: str
    latest_publish_time: str | None
    earliest_publish_time: str | None
    points: list[Point]


class Metrics(BaseModel):
    n: int
    mae: float
    rmse: float
    bias: float
    p5: float
    p50: float
    p95: float
    abs_p90: float
    abs_p99: float


class SeriesPoint(BaseModel):
    time: str
    forecast: float | None
    actual: float | None
    publishTime: str


class HistBin(BaseModel):
    bin: int
    count: int


class AccuracyResponse(BaseModel):
    horizon_hours: float | None = None
    metrics: Metrics | None
    series: list[SeriesPoint]
    histogram: list[HistBin]


class HorizonRow(Metrics):
    horizon: int


class ByHorizonResponse(BaseModel):
    points: list[HorizonRow]
