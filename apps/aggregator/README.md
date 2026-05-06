# Public Opinin Aggregator

FastAPI service for keyword management, scheduler-triggered social search ingestion, SQLite persistence, and read APIs for the dashboard.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn public_opinin_aggregator.main:app --reload
```

## Useful Endpoints

- `GET /health`
- `GET /keywords`
- `POST /keywords`
- `POST /runs/search`
- `GET /posts`

When `APIFY_TOKEN` is not configured, `POST /runs/search` uses dry-run sample data so local development works without credentials.
