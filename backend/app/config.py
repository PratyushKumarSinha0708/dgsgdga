from datetime import date
from pathlib import Path

BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Decisions are made on D-1 and must fall in January 2026,
# so delivery days run from 2 Jan to 1 Feb 2026.
MIN_DELIVERY_DATE = date(2026, 1, 2)
MAX_DELIVERY_DATE = date(2026, 2, 1)

FORECAST_PUBLISH_FROM = date(2026, 1, 1)
FORECAST_PUBLISH_TO = date(2026, 2, 1)
ACTUALS_FROM = date(2026, 1, 2)
ACTUALS_TO = date(2026, 2, 2)

DEFAULT_CUTOFF = "09:00"  # UK time on D-1, configurable per request
MAX_RANGE_DAYS = 40
