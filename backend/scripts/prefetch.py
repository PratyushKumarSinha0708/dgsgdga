"""Run once: python -m scripts.prefetch   (then commit backend/data/*.csv)"""
from app import config, elexon

config.DATA_DIR.mkdir(exist_ok=True)
fc = elexon.fetch_forecasts(config.FORECAST_PUBLISH_FROM, config.FORECAST_PUBLISH_TO)
ac = elexon.fetch_actuals(config.ACTUALS_FROM, config.ACTUALS_TO)
fc.to_csv(config.DATA_DIR / "forecasts.csv", index=False)
ac.to_csv(config.DATA_DIR / "actuals.csv", index=False)
print(f"forecasts: {len(fc):,} rows | actuals: {len(ac):,} rows")
print(fc.head(), ac.head(), sep="\n")
