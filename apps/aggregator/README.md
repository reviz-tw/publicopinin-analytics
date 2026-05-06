# Public Opinin Aggregator

FastAPI service for keyword management, Apify dataset ingestion, SQLite persistence, and read APIs for the dashboard.

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
- `POST /runs/search` for local dry-run/debug ingestion
- `POST /apify/datasets/sync-recent`
- `POST /apify/datasets/{dataset_id}/sync`
- `POST /webhooks/apify/run-finished`
- `GET /posts`

When `APIFY_TOKEN` is not configured, `POST /runs/search` uses dry-run sample data so local development works without credentials. If `APIFY_TOKEN` and platform actor IDs are configured, `/runs/search` calls those actors directly and requires their input schemas to match the debug client payload.

## Apify Scheduling Flow

Production scheduling should live in Apify:

1. Create one Apify Actor Task per platform/search configuration.
2. Attach the tasks to an Apify Schedule.
3. Configure each task's succeeded-run webhook to call this service:

```text
POST https://YOUR_AGGREGATOR_HOST/webhooks/apify/run-finished?platform=threads&keyword=YOUR_KEYWORD
```

The webhook payload must include the Apify run resource with `defaultDatasetId`. The aggregator fetches dataset items, normalizes posts/comments, records an `ingestion_runs` row with Apify metadata, and stores posts/comments in SQLite.

For cron-style local syncing, fetch recent Apify datasets and ingest anything not already synced:

```bash
curl -s -X POST http://127.0.0.1:8000/apify/datasets/sync-recent \
  -H 'content-type: application/json' \
  -d '{"limit":20}'
```

For local debugging with a known dataset ID:

```bash
curl -s -X POST http://127.0.0.1:8000/apify/datasets/DATASET_ID/sync \
  -H 'content-type: application/json' \
  -d '{"platform":"threads","keyword":"國際特赦組織","apify_run_id":"RUN_ID"}'
```
