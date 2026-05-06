# Monorepo Aggregator Dashboard Design

## Goal

Convert this repository into a monorepo with two runnable applications:

- `apps/aggregator`: a Python/FastAPI service that manages keywords, ingests Apify task datasets through webhooks or manual sync endpoints, stores full post/comment data in SQLite, and exposes read APIs for visualization.
- `apps/dashboard`: a Next.js data visualization site that reads aggregator APIs and displays stored posts with field filters.
- `packages/shared`: shared API contract and database schema documentation.

## Architecture

The aggregator owns all SQLite access. The dashboard never reads SQLite directly; it calls HTTP APIs exposed by the aggregator. This keeps the dashboard independent from database file paths, migrations, and future database changes.

The monorepo root provides developer documentation and convenience commands. Each app owns its dependencies and runtime configuration:

- Aggregator dependencies are managed in `apps/aggregator`.
- Dashboard dependencies are managed in `apps/dashboard`.
- Shared contracts live in `packages/shared` and are manually maintained for the MVP.

## Aggregator

The aggregator is a FastAPI service with these responsibilities:

- Manage keywords through `GET /keywords` and `POST /keywords`.
- Ingest Apify task results through `POST /webhooks/apify/run-finished`, where Apify Schedules own the actual timer.
- Support manual dataset backfills through `POST /apify/datasets/{dataset_id}/sync`.
- Keep `POST /runs/search` as a local development/debug endpoint rather than the production scheduling path.
- Persist ingestion metadata, posts, and comments in SQLite.
- Expose `GET /posts` for dashboard reads, including filters by keyword, platform, date range, author, and free text.
- Provide `GET /health` for process checks.

The MVP uses Apify Tasks and Schedules as the production scheduling layer. The aggregator fetches dataset items by `defaultDatasetId` when a succeeded-run webhook arrives, then normalizes posts/comments into SQLite. Platform-specific actor IDs remain configurable only for the retained local debug search endpoint.

## Dashboard

The dashboard is a Next.js App Router application. The first screen is the actual data interface:

- Summary counts for posts, comments, platforms, and keywords.
- Filter controls for keyword, platform, date range, and search text.
- A posts table showing platform, keyword, author, content preview, engagement fields, comment count, URL, and collection time.
- Empty and error states for local development.

The dashboard reads the aggregator URL from `NEXT_PUBLIC_AGGREGATOR_API_URL`, defaulting to `http://localhost:8000`.

## Shared Contracts

`packages/shared` documents the contract between apps:

- `schemas/openapi.yaml`: HTTP API contract for the MVP endpoints.
- `schemas/database.md`: SQLite tables, key fields, and JSON payload policy.

Generated clients are out of scope for the first pass. The package exists now so generated types can be added later without moving contracts.

## Data Model

SQLite tables:

- `keywords`: keyword records, active state, timestamps.
- `ingestion_runs`: each Apify/manual/debug run, requested platforms, status, item counts, Apify run/task/dataset metadata, error message.
- `posts`: normalized searchable post rows plus `raw_json` for complete source data.
- `comments`: normalized comments linked to posts plus `raw_json` for complete source data.

Posts and comments use source IDs plus platform for uniqueness. The schema keeps normalized columns for filtering and display, while preserving full Apify payloads in JSON text columns for auditability and future extraction.

## Error Handling

- Aggregator returns structured HTTP errors for invalid keyword input and unknown resources.
- Ingestion runs are recorded even when provider calls fail.
- Provider errors are stored on `ingestion_runs.error_message`.
- Dashboard renders API failures as an inline error state instead of crashing the page.

## Testing

Aggregator tests cover database initialization, keyword CRUD, post filters, and dry-run ingestion. Dashboard tests cover API client URL construction and filter query serialization. Full end-to-end Apify calls are excluded from default tests because they require credentials and network access.

## Initial Scope

This implementation creates a working local MVP:

- Monorepo structure.
- FastAPI service with SQLite persistence.
- Dry-run/mock ingestion path.
- Apify webhook and dataset sync endpoints.
- Retained dry-run/debug ingestion path.
- Next.js dashboard with filters and table display.
- Shared schema documentation.

The exact Apify actor mapping for Threads, Instagram, Facebook, X, and TikTok remains configurable rather than hard-coded.
