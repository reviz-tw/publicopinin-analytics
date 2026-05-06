# publicopinin-analytics

Monorepo for public opinion collection and analytics.

## Apps

- `apps/aggregator`: FastAPI service that manages keywords, triggers Apify-backed ingestion, stores posts/comments in SQLite, and exposes dashboard APIs.
- `apps/dashboard`: Next.js dashboard that visualizes records exposed by the aggregator API.
- `packages/shared`: API and database contracts shared between apps.

## Local Development

### Aggregator

```bash
cd apps/aggregator
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn public_opinin_aggregator.main:app --reload
```

The API runs at `http://localhost:8000`.

### Dashboard

```bash
cd apps/dashboard
npm install
cp .env.example .env.local
npm run dev
```

The dashboard runs at `http://localhost:3000`.

## Environment

Aggregator:

- `DATABASE_URL`: SQLite URL, defaults to `sqlite:///./data/public_opinin.db`.
- `APIFY_TOKEN`: optional Apify token. If omitted, ingestion runs in dry-run mode.
- `APIFY_ACTOR_THREADS`, `APIFY_ACTOR_INSTAGRAM`, `APIFY_ACTOR_FACEBOOK`, `APIFY_ACTOR_X`, `APIFY_ACTOR_TIKTOK`: optional actor IDs per platform.

Dashboard:

- `NEXT_PUBLIC_AGGREGATOR_API_URL`: aggregator API base URL, defaults to `http://localhost:8000`.
