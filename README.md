# Wind Forecast Desk

Web app for a UK energy utility's day-ahead buying desk. It uses national GB wind data from Elexon only:

1. **Latest forecast at decision time:** for a delivery day D, shows the most recent wind forecast published at or before a configurable cutoff (default 09:00 UK time on D-1).
2. **Forecast accuracy:** quantifies forecast error (MAE, RMSE, bias, percentiles, error vs horizon) so a buffer can be sized.

Scope: purchase decisions made in **January 2026**, so delivery days 2 Jan to 1 Feb 2026.

**Data:** Elexon Insights API. `WINDFOR` (forecasts: `publishTime`, `startTime`, `generation`) and `FUELHH` filtered to `fuelType = WIND` (actuals, half-hourly).

## AI disclosure
This project was built with assistance from **Claude (Anthropic)** for planning, code generation and documentation. All code was reviewed and run by the author. *(Edit this line to describe your own usage.)*

## Run locally
```bash
# 1. Backend
cd backend
pip install -r requirements.txt
python -m scripts.prefetch        # downloads Jan 2026 data to backend/data/*.csv
pytest
uvicorn app.main:app --reload     # http://localhost:8000/docs

# 2. Frontend (new terminal)
cd frontend
npm install
npm run dev                       # http://localhost:5173 (proxies /api to :8000)
```

## Run with Docker
```bash
cd backend && python -m scripts.prefetch && cd ..   # so the snapshot is baked into the image
docker compose up --build                           # http://localhost:8080
```
If `backend/data/*.csv` is missing, the backend fetches live from Elexon on first request.

## Deploy to Vercel (two projects, same repo)
1. Commit `backend/data/*.csv`.
2. Project 1: Root Directory `backend`. Note its URL.
3. Put that URL into `frontend/vercel.json` (`YOUR-BACKEND`).
4. Project 2: Root Directory `frontend` (framework: Vite).

## Design decisions
- **Time:** everything is UTC internally. UK local time is used only to define the delivery day, the cutoff, and display labels. UK day bounds use `Europe/London`, so 23h/25h DST days are handled (none in January).
- **Latest forecast:** among forecasts with `publishTime <= cutoff` and `startTime` in the delivery day, take the latest `publishTime` per `startTime`.
- **Horizon** = `startTime - publishTime`. For horizon h, use the latest forecast published at least h hours before the target time.
- **Granularity:** forecast step is detected from data. If hourly, the 30-min actuals are averaged to hourly so the comparison is like for like.
- **Error** = actual - forecast. Negative = wind below forecast = buyer must purchase more. Report MAE, RMSE, bias, P5/P50/P95, absolute P90/P99. Percentiles matter more than MAE for sizing a safety margin because the cost is asymmetric.
- **Data snapshot:** serverless has no persistent disk, so January data is prefetched and committed. This also makes the demo independent of Elexon uptime.
- **Duplicates / missing:** duplicate (publish, start) rows are dropped; rows without actuals are excluded from metrics.

## Limitations / next steps
- National wind only; no demand, solar, or price data.
- Static snapshot, no scheduled refresh.
- The cutoff is a single configurable time; real gate closure may differ by market.
- Next: probabilistic error bands conditional on wind level and hour of day, solar and demand, scheduled data refresh.

## Layout
```
backend/   FastAPI app (app/), tests/, scripts/prefetch.py, Dockerfile, vercel.json, api/index.py
frontend/  Vite + React (plain JS) + Recharts, Dockerfile (nginx), vercel.json
docker-compose.yml
```


## AI disclosure
Claude (Anthropic) and ChatGPT (OpenAI) were used as assistants for ideas and boilerplate; I wrote, tested and adapted the final code myself.