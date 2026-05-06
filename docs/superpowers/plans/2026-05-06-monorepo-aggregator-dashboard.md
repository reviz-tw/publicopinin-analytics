# Monorepo Aggregator Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable monorepo with a FastAPI social-search aggregator backed by SQLite, a Next.js dashboard that reads aggregator APIs, and shared contract documentation.

**Architecture:** The aggregator owns all SQLite access and exposes HTTP APIs for both ingestion and reads. The dashboard is a separate Next.js app that calls those APIs and never opens the database file directly. Shared contracts live under `packages/shared` so generated clients can be added later without changing app boundaries.

**Tech Stack:** Python 3.11+, FastAPI, SQLite, pytest, httpx, Next.js App Router, TypeScript, CSS modules/plain CSS, Node.js 20+.

---

## File Structure

- Create `README.md`: root monorepo overview, local setup, app commands, environment variables.
- Create `apps/aggregator/README.md`: aggregator-specific setup and endpoint examples.
- Create `apps/aggregator/pyproject.toml`: Python package metadata and dependencies.
- Create `apps/aggregator/.env.example`: aggregator runtime configuration.
- Create `apps/aggregator/public_opinin_aggregator/__init__.py`: package marker.
- Create `apps/aggregator/public_opinin_aggregator/config.py`: environment-backed settings.
- Create `apps/aggregator/public_opinin_aggregator/db.py`: SQLite connection, migrations, row helpers.
- Create `apps/aggregator/public_opinin_aggregator/models.py`: Pydantic request/response models.
- Create `apps/aggregator/public_opinin_aggregator/repository.py`: keyword, run, post, and comment database operations.
- Create `apps/aggregator/public_opinin_aggregator/apify_client.py`: Apify adapter and dry-run provider.
- Create `apps/aggregator/public_opinin_aggregator/main.py`: FastAPI app and routes.
- Create `apps/aggregator/tests/test_api.py`: API and persistence tests.
- Create `apps/dashboard/README.md`: dashboard-specific setup.
- Create `apps/dashboard/package.json`: dashboard scripts and dependencies.
- Create `apps/dashboard/next.config.js`: Next.js config.
- Create `apps/dashboard/tsconfig.json`: TypeScript config.
- Create `apps/dashboard/.env.example`: dashboard runtime configuration.
- Create `apps/dashboard/app/globals.css`: global UI styles.
- Create `apps/dashboard/app/layout.tsx`: root layout.
- Create `apps/dashboard/app/page.tsx`: dashboard page.
- Create `apps/dashboard/lib/api.ts`: aggregator API client.
- Create `apps/dashboard/lib/types.ts`: dashboard-facing API types.
- Create `packages/shared/README.md`: contract package overview.
- Create `packages/shared/schemas/openapi.yaml`: MVP API contract.
- Create `packages/shared/schemas/database.md`: SQLite schema and field semantics.

---

### Task 1: Root Monorepo Documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace the root README with monorepo setup documentation**

````markdown
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
````

- [ ] **Step 2: Verify the README renders enough setup detail**

Run: `sed -n '1,220p' README.md`

Expected: The output names all three monorepo areas and includes local commands for both apps.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: describe monorepo setup"
```

---

### Task 2: Aggregator Project Skeleton

**Files:**
- Create: `apps/aggregator/README.md`
- Create: `apps/aggregator/pyproject.toml`
- Create: `apps/aggregator/.env.example`
- Create: `apps/aggregator/public_opinin_aggregator/__init__.py`

- [ ] **Step 1: Create the aggregator README**

````markdown
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
````

- [ ] **Step 2: Create `pyproject.toml`**

```toml
[project]
name = "public-opinin-aggregator"
version = "0.1.0"
description = "FastAPI social search aggregator for publicopinin analytics"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115.0",
  "uvicorn[standard]>=0.30.0",
  "pydantic-settings>=2.4.0",
  "httpx>=0.27.0",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3.0",
  "pytest-asyncio>=0.24.0",
]

[build-system]
requires = ["setuptools>=72.0"]
build-backend = "setuptools.build_meta"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 3: Create `.env.example`**

```dotenv
DATABASE_URL=sqlite:///./data/public_opinin.db
APIFY_TOKEN=
APIFY_ACTOR_THREADS=
APIFY_ACTOR_INSTAGRAM=
APIFY_ACTOR_FACEBOOK=
APIFY_ACTOR_X=
APIFY_ACTOR_TIKTOK=
```

- [ ] **Step 4: Create the package marker**

```python
"""Public Opinin Aggregator package."""
```

- [ ] **Step 5: Run metadata validation**

Run: `python3 -c 'import pathlib, tomllib; tomllib.loads(pathlib.Path("apps/aggregator/pyproject.toml").read_text())'`

Expected: exits with code 0.

- [ ] **Step 6: Commit**

```bash
git add apps/aggregator/README.md apps/aggregator/pyproject.toml apps/aggregator/.env.example apps/aggregator/public_opinin_aggregator/__init__.py
git commit -m "chore: scaffold aggregator app"
```

---

### Task 3: Aggregator Settings and Database

**Files:**
- Create: `apps/aggregator/public_opinin_aggregator/config.py`
- Create: `apps/aggregator/public_opinin_aggregator/db.py`
- Create: `apps/aggregator/tests/test_api.py`

- [ ] **Step 1: Write failing tests for database initialization**

```python
from fastapi.testclient import TestClient

from public_opinin_aggregator.config import Settings
from public_opinin_aggregator.db import connect, initialize_database
from public_opinin_aggregator.main import create_app


def test_health_endpoint(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'test.db'}"
    app = create_app(Settings(database_url=db_url))

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_initialize_database_creates_tables(tmp_path):
    db_path = tmp_path / "test.db"
    connection = connect(f"sqlite:///{db_path}")
    initialize_database(connection)

    tables = {
        row["name"]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }

    assert {"keywords", "ingestion_runs", "posts", "comments"}.issubset(tables)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd apps/aggregator && pytest -q`

Expected: FAIL because `config.py`, `db.py`, and `main.py` do not exist yet.

- [ ] **Step 3: Implement settings**

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/public_opinin.db"
    apify_token: str | None = None
    apify_actor_threads: str | None = None
    apify_actor_instagram: str | None = None
    apify_actor_facebook: str | None = None
    apify_actor_x: str | None = None
    apify_actor_tiktok: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
    )

    @property
    def apify_actors(self) -> dict[str, str]:
        return {
            platform: actor
            for platform, actor in {
                "threads": self.apify_actor_threads,
                "instagram": self.apify_actor_instagram,
                "facebook": self.apify_actor_facebook,
                "x": self.apify_actor_x,
                "tiktok": self.apify_actor_tiktok,
            }.items()
            if actor
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 4: Implement SQLite connection and migrations**

```python
from pathlib import Path
import sqlite3


def sqlite_path(database_url: str) -> str:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("Only sqlite:/// database URLs are supported")
    return database_url.removeprefix(prefix)


def connect(database_url: str) -> sqlite3.Connection:
    path = sqlite_path(database_url)
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            value TEXT NOT NULL UNIQUE,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS ingestion_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL,
            requested_keywords TEXT NOT NULL,
            requested_platforms TEXT NOT NULL,
            posts_count INTEGER NOT NULL DEFAULT 0,
            comments_count INTEGER NOT NULL DEFAULT 0,
            error_message TEXT,
            started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            finished_at TEXT
        );

        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform TEXT NOT NULL,
            source_id TEXT NOT NULL,
            keyword TEXT NOT NULL,
            author_name TEXT,
            author_handle TEXT,
            content TEXT,
            url TEXT,
            published_at TEXT,
            like_count INTEGER,
            comment_count INTEGER,
            share_count INTEGER,
            raw_json TEXT NOT NULL,
            collected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(platform, source_id)
        );

        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
            platform TEXT NOT NULL,
            source_id TEXT NOT NULL,
            author_name TEXT,
            author_handle TEXT,
            content TEXT,
            published_at TEXT,
            like_count INTEGER,
            raw_json TEXT NOT NULL,
            collected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(platform, source_id)
        );

        CREATE INDEX IF NOT EXISTS idx_posts_keyword ON posts(keyword);
        CREATE INDEX IF NOT EXISTS idx_posts_platform ON posts(platform);
        CREATE INDEX IF NOT EXISTS idx_posts_published_at ON posts(published_at);
        """
    )
    connection.commit()
```

- [ ] **Step 5: Add temporary FastAPI factory so tests can pass**

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .config import Settings, get_settings
from .db import connect, initialize_database


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        connection = connect(app_settings.database_url)
        initialize_database(connection)
        app.state.db = connection
        yield
        connection.close()

    app = FastAPI(title="Public Opinin Aggregator", lifespan=lifespan)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 6: Run tests**

Run: `cd apps/aggregator && pytest -q`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add apps/aggregator/public_opinin_aggregator/config.py apps/aggregator/public_opinin_aggregator/db.py apps/aggregator/public_opinin_aggregator/main.py apps/aggregator/tests/test_api.py
git commit -m "feat: add aggregator database foundation"
```

---

### Task 4: Keyword and Post Repository

**Files:**
- Create: `apps/aggregator/public_opinin_aggregator/models.py`
- Create: `apps/aggregator/public_opinin_aggregator/repository.py`
- Modify: `apps/aggregator/tests/test_api.py`

- [ ] **Step 1: Add failing tests for keyword and post filtering behavior**

```python
def test_create_and_list_keywords(tmp_path):
    app = create_app(Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}"))

    with TestClient(app) as client:
        created = client.post("/keywords", json={"value": "election"}).json()
        listed = client.get("/keywords").json()

    assert created["value"] == "election"
    assert created["is_active"] is True
    assert listed["items"][0]["value"] == "election"


def test_posts_endpoint_filters_by_keyword_and_platform(tmp_path):
    app = create_app(Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}"))

    with TestClient(app) as client:
        run = client.post("/runs/search", json={"keywords": ["policy"], "platforms": ["threads"]}).json()
        client.post("/runs/search", json={"keywords": ["sports"], "platforms": ["x"]})
        response = client.get("/posts", params={"keyword": "policy", "platform": "threads"})

    assert run["comments_count"] == 1
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["keyword"] == "policy"
    assert payload["items"][0]["platform"] == "threads"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd apps/aggregator && pytest -q`

Expected: FAIL because keyword, post, and run routes are not implemented.

- [ ] **Step 3: Implement Pydantic models**

```python
from pydantic import BaseModel, Field


class KeywordCreate(BaseModel):
    value: str = Field(min_length=1, max_length=200)


class KeywordRead(BaseModel):
    id: int
    value: str
    is_active: bool
    created_at: str
    updated_at: str


class KeywordList(BaseModel):
    items: list[KeywordRead]


class SearchRunCreate(BaseModel):
    keywords: list[str] | None = None
    platforms: list[str] = Field(default_factory=lambda: ["threads", "instagram", "facebook", "x", "tiktok"])


class SearchRunRead(BaseModel):
    id: int
    status: str
    requested_keywords: list[str]
    requested_platforms: list[str]
    posts_count: int
    comments_count: int
    error_message: str | None
    started_at: str
    finished_at: str | None


class PostRead(BaseModel):
    id: int
    platform: str
    source_id: str
    keyword: str
    author_name: str | None
    author_handle: str | None
    content: str | None
    url: str | None
    published_at: str | None
    like_count: int | None
    comment_count: int | None
    share_count: int | None
    collected_at: str


class PostList(BaseModel):
    total: int
    items: list[PostRead]
```

- [ ] **Step 4: Implement repository operations**

```python
import json
import sqlite3
from typing import Any


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def create_keyword(connection: sqlite3.Connection, value: str) -> dict[str, Any]:
    normalized = value.strip()
    connection.execute(
        """
        INSERT INTO keywords (value, updated_at)
        VALUES (?, CURRENT_TIMESTAMP)
        ON CONFLICT(value) DO UPDATE SET is_active = 1, updated_at = CURRENT_TIMESTAMP
        """,
        (normalized,),
    )
    connection.commit()
    return row_to_dict(
        connection.execute("SELECT * FROM keywords WHERE value = ?", (normalized,)).fetchone()
    )


def list_keywords(connection: sqlite3.Connection, active_only: bool = True) -> list[dict[str, Any]]:
    sql = "SELECT * FROM keywords"
    params: tuple[Any, ...] = ()
    if active_only:
        sql += " WHERE is_active = 1"
    sql += " ORDER BY value"
    return [row_to_dict(row) for row in connection.execute(sql, params).fetchall()]


def active_keyword_values(connection: sqlite3.Connection) -> list[str]:
    return [row["value"] for row in connection.execute("SELECT value FROM keywords WHERE is_active = 1 ORDER BY value")]


def create_run(connection: sqlite3.Connection, keywords: list[str], platforms: list[str]) -> int:
    cursor = connection.execute(
        """
        INSERT INTO ingestion_runs (status, requested_keywords, requested_platforms)
        VALUES ('running', ?, ?)
        """,
        (json.dumps(keywords), json.dumps(platforms)),
    )
    connection.commit()
    return int(cursor.lastrowid)


def finish_run(connection: sqlite3.Connection, run_id: int, status: str, posts_count: int, comments_count: int, error_message: str | None = None) -> dict[str, Any]:
    connection.execute(
        """
        UPDATE ingestion_runs
        SET status = ?, posts_count = ?, comments_count = ?, error_message = ?, finished_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (status, posts_count, comments_count, error_message, run_id),
    )
    connection.commit()
    row = row_to_dict(connection.execute("SELECT * FROM ingestion_runs WHERE id = ?", (run_id,)).fetchone())
    row["requested_keywords"] = json.loads(row["requested_keywords"])
    row["requested_platforms"] = json.loads(row["requested_platforms"])
    return row


def upsert_post(connection: sqlite3.Connection, post: dict[str, Any]) -> int:
    connection.execute(
        """
        INSERT INTO posts (
            platform, source_id, keyword, author_name, author_handle, content, url,
            published_at, like_count, comment_count, share_count, raw_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(platform, source_id) DO UPDATE SET
            keyword = excluded.keyword,
            author_name = excluded.author_name,
            author_handle = excluded.author_handle,
            content = excluded.content,
            url = excluded.url,
            published_at = excluded.published_at,
            like_count = excluded.like_count,
            comment_count = excluded.comment_count,
            share_count = excluded.share_count,
            raw_json = excluded.raw_json,
            collected_at = CURRENT_TIMESTAMP
        """,
        (
            post["platform"],
            post["source_id"],
            post["keyword"],
            post.get("author_name"),
            post.get("author_handle"),
            post.get("content"),
            post.get("url"),
            post.get("published_at"),
            post.get("like_count"),
            post.get("comment_count"),
            post.get("share_count"),
            json.dumps(post.get("raw_json", post)),
        ),
    )
    connection.commit()
    row = connection.execute(
        "SELECT id FROM posts WHERE platform = ? AND source_id = ?",
        (post["platform"], post["source_id"]),
    ).fetchone()
    return int(row["id"])


def upsert_comment(connection: sqlite3.Connection, post_id: int, comment: dict[str, Any]) -> int:
    connection.execute(
        """
        INSERT INTO comments (
            post_id, platform, source_id, author_name, author_handle,
            content, published_at, like_count, raw_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(platform, source_id) DO UPDATE SET
            post_id = excluded.post_id,
            author_name = excluded.author_name,
            author_handle = excluded.author_handle,
            content = excluded.content,
            published_at = excluded.published_at,
            like_count = excluded.like_count,
            raw_json = excluded.raw_json,
            collected_at = CURRENT_TIMESTAMP
        """,
        (
            post_id,
            comment["platform"],
            comment["source_id"],
            comment.get("author_name"),
            comment.get("author_handle"),
            comment.get("content"),
            comment.get("published_at"),
            comment.get("like_count"),
            json.dumps(comment.get("raw_json", comment)),
        ),
    )
    connection.commit()
    row = connection.execute(
        "SELECT id FROM comments WHERE platform = ? AND source_id = ?",
        (comment["platform"], comment["source_id"]),
    ).fetchone()
    return int(row["id"])


def list_posts(connection: sqlite3.Connection, keyword: str | None = None, platform: str | None = None, q: str | None = None, limit: int = 100) -> tuple[int, list[dict[str, Any]]]:
    clauses = []
    params: list[Any] = []
    if keyword:
        clauses.append("keyword = ?")
        params.append(keyword)
    if platform:
        clauses.append("platform = ?")
        params.append(platform)
    if q:
        clauses.append("(content LIKE ? OR author_name LIKE ? OR author_handle LIKE ?)")
        pattern = f"%{q}%"
        params.extend([pattern, pattern, pattern])

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    total = connection.execute(f"SELECT COUNT(*) AS count FROM posts {where}", params).fetchone()["count"]
    rows = connection.execute(
        f"SELECT id, platform, source_id, keyword, author_name, author_handle, content, url, published_at, like_count, comment_count, share_count, collected_at FROM posts {where} ORDER BY collected_at DESC LIMIT ?",
        [*params, limit],
    ).fetchall()
    return int(total), [row_to_dict(row) for row in rows]
```

- [ ] **Step 5: Run tests**

Run: `cd apps/aggregator && pytest -q`

Expected: still FAIL because API routes and provider are not wired.

- [ ] **Step 6: Commit**

```bash
git add apps/aggregator/public_opinin_aggregator/models.py apps/aggregator/public_opinin_aggregator/repository.py apps/aggregator/tests/test_api.py
git commit -m "feat: add aggregator repository models"
```

---

### Task 5: Dry-Run Apify Adapter and Aggregator Routes

**Files:**
- Create: `apps/aggregator/public_opinin_aggregator/apify_client.py`
- Modify: `apps/aggregator/public_opinin_aggregator/main.py`
- Modify: `apps/aggregator/tests/test_api.py`

- [ ] **Step 1: Implement the provider adapter**

```python
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote_plus

import httpx


@dataclass(frozen=True)
class SearchResult:
    posts: list[dict[str, Any]]
    comments: list[dict[str, Any]]


class ApifySearchClient:
    def __init__(self, token: str | None, actors: dict[str, str]):
        self.token = token
        self.actors = actors

    async def search(self, keyword: str, platform: str) -> SearchResult:
        if not self.token or platform not in self.actors:
            return self._dry_run_result(keyword, platform)

        actor_id = self.actors[platform]
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"https://api.apify.com/v2/acts/{quote_plus(actor_id)}/run-sync-get-dataset-items",
                params={"token": self.token},
                json={"search": keyword, "keyword": keyword, "query": keyword},
            )
            response.raise_for_status()
            items = response.json()

        posts = [self._normalize_item(item, keyword, platform, index) for index, item in enumerate(items)]
        comments = []
        for post, item in zip(posts, items, strict=False):
            for comment_index, comment in enumerate(item.get("comments") or []):
                comments.append(self._normalize_comment(comment, post["source_id"], platform, comment_index))
        return SearchResult(posts=posts, comments=comments)

    def _dry_run_result(self, keyword: str, platform: str) -> SearchResult:
        source_id = f"dry-run-{platform}-{keyword}".replace(" ", "-").lower()
        post = {
            "platform": platform,
            "source_id": source_id,
            "keyword": keyword,
            "author_name": "Dry Run Author",
            "author_handle": f"@{platform}_sample",
            "content": f"Sample {platform} post for keyword: {keyword}",
            "url": f"https://example.com/{platform}/{source_id}",
            "published_at": None,
            "like_count": 0,
            "comment_count": 0,
            "share_count": 0,
            "raw_json": {"dry_run": True, "keyword": keyword, "platform": platform},
        }
        comment = {
            "platform": platform,
            "post_source_id": source_id,
            "source_id": f"{source_id}-comment-1",
            "author_name": "Dry Run Commenter",
            "author_handle": f"@{platform}_commenter",
            "content": f"Sample comment for keyword: {keyword}",
            "published_at": None,
            "like_count": 0,
            "raw_json": {"dry_run": True, "keyword": keyword, "platform": platform, "parent_source_id": source_id},
        }
        return SearchResult(posts=[post], comments=[comment])

    def _normalize_item(self, item: dict[str, Any], keyword: str, platform: str, index: int) -> dict[str, Any]:
        source_id = str(item.get("id") or item.get("postId") or item.get("url") or f"{keyword}-{index}")
        author = item.get("author") if isinstance(item.get("author"), dict) else {}
        return {
            "platform": platform,
            "source_id": source_id,
            "keyword": keyword,
            "author_name": item.get("authorName") or author.get("name") or item.get("username"),
            "author_handle": item.get("authorHandle") or author.get("username") or item.get("handle"),
            "content": item.get("text") or item.get("caption") or item.get("content"),
            "url": item.get("url"),
            "published_at": item.get("timestamp") or item.get("publishedAt") or item.get("createdAt"),
            "like_count": item.get("likesCount") or item.get("likeCount"),
            "comment_count": item.get("commentsCount") or item.get("commentCount"),
            "share_count": item.get("sharesCount") or item.get("shareCount"),
            "raw_json": item,
        }

    def _normalize_comment(self, item: dict[str, Any], post_source_id: str, platform: str, index: int) -> dict[str, Any]:
        source_id = str(item.get("id") or item.get("commentId") or f"{post_source_id}-comment-{index}")
        author = item.get("author") if isinstance(item.get("author"), dict) else {}
        return {
            "platform": platform,
            "post_source_id": post_source_id,
            "source_id": source_id,
            "author_name": item.get("authorName") or author.get("name") or item.get("username"),
            "author_handle": item.get("authorHandle") or author.get("username") or item.get("handle"),
            "content": item.get("text") or item.get("content"),
            "published_at": item.get("timestamp") or item.get("publishedAt") or item.get("createdAt"),
            "like_count": item.get("likesCount") or item.get("likeCount"),
            "raw_json": item,
        }
```

- [ ] **Step 2: Wire routes in `main.py`**

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query, Request

from .apify_client import ApifySearchClient
from .config import Settings, get_settings
from .db import connect, initialize_database
from .models import KeywordCreate, KeywordList, KeywordRead, PostList, SearchRunCreate, SearchRunRead
from . import repository


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        connection = connect(app_settings.database_url)
        initialize_database(connection)
        app.state.db = connection
        app.state.search_client = ApifySearchClient(app_settings.apify_token, app_settings.apify_actors)
        yield
        connection.close()

    app = FastAPI(title="Public Opinin Aggregator", lifespan=lifespan)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/keywords", response_model=KeywordList)
    def get_keywords(request: Request) -> KeywordList:
        rows = repository.list_keywords(request.app.state.db)
        return KeywordList(items=[KeywordRead(**{**row, "is_active": bool(row["is_active"])}) for row in rows])

    @app.post("/keywords", response_model=KeywordRead)
    def post_keyword(payload: KeywordCreate, request: Request) -> KeywordRead:
        row = repository.create_keyword(request.app.state.db, payload.value)
        return KeywordRead(**{**row, "is_active": bool(row["is_active"])})

    @app.post("/runs/search", response_model=SearchRunRead)
    async def run_search(payload: SearchRunCreate, request: Request) -> SearchRunRead:
        connection = request.app.state.db
        keywords = payload.keywords or repository.active_keyword_values(connection)
        run_id = repository.create_run(connection, keywords, payload.platforms)
        posts_count = 0
        comments_count = 0
        try:
            for keyword in keywords:
                for platform in payload.platforms:
                    result = await request.app.state.search_client.search(keyword, platform)
                    for post in result.posts:
                        post_id = repository.upsert_post(connection, post)
                        posts_count += 1
                        for comment in result.comments:
                            if comment.get("post_source_id") == post["source_id"]:
                                repository.upsert_comment(connection, post_id, comment)
                                comments_count += 1
            row = repository.finish_run(connection, run_id, "succeeded", posts_count, comments_count)
        except Exception as exc:
            row = repository.finish_run(connection, run_id, "failed", posts_count, comments_count, str(exc))
        return SearchRunRead(**row)

    @app.get("/posts", response_model=PostList)
    def get_posts(
        request: Request,
        keyword: str | None = None,
        platform: str | None = None,
        q: str | None = None,
        limit: int = Query(default=100, ge=1, le=500),
    ) -> PostList:
        total, rows = repository.list_posts(request.app.state.db, keyword=keyword, platform=platform, q=q, limit=limit)
        return PostList(total=total, items=rows)

    return app


app = create_app()
```

- [ ] **Step 3: Run tests**

Run: `cd apps/aggregator && pytest -q`

Expected: PASS.

- [ ] **Step 4: Manually smoke test the service**

Run: `cd apps/aggregator && uvicorn public_opinin_aggregator.main:app --port 8000`

In another terminal run:

```bash
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/keywords -H 'content-type: application/json' -d '{"value":"policy"}'
curl -s -X POST http://localhost:8000/runs/search -H 'content-type: application/json' -d '{"keywords":["policy"],"platforms":["threads"]}'
curl -s 'http://localhost:8000/posts?keyword=policy&platform=threads'
```

Expected: health returns `{"status":"ok"}` and posts returns one dry-run item; the run response reports one persisted comment.

- [ ] **Step 5: Commit**

```bash
git add apps/aggregator/public_opinin_aggregator/apify_client.py apps/aggregator/public_opinin_aggregator/main.py apps/aggregator/tests/test_api.py
git commit -m "feat: expose aggregator api routes"
```

---

### Task 6: Dashboard Skeleton and API Client

**Files:**
- Create: `apps/dashboard/README.md`
- Create: `apps/dashboard/package.json`
- Create: `apps/dashboard/next.config.js`
- Create: `apps/dashboard/tsconfig.json`
- Create: `apps/dashboard/.env.example`
- Create: `apps/dashboard/lib/types.ts`
- Create: `apps/dashboard/lib/api.ts`

- [ ] **Step 1: Create dashboard project metadata**

```json
{
  "name": "public-opinin-dashboard",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "lint": "next lint",
    "typecheck": "tsc --noEmit"
  },
  "dependencies": {
    "next": "^15.0.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@types/node": "^22.0.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "typescript": "^5.6.0"
  }
}
```

- [ ] **Step 2: Create Next and TypeScript configs**

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {};

module.exports = nextConfig;
```

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": false,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }]
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
```

- [ ] **Step 3: Create dashboard README and env example**

````markdown
# Public Opinin Dashboard

Next.js dashboard for visualizing posts collected by the aggregator.

## Setup

```bash
npm install
cp .env.example .env.local
npm run dev
```
````

```dotenv
NEXT_PUBLIC_AGGREGATOR_API_URL=http://localhost:8000
```

- [ ] **Step 4: Create API types**

```typescript
export type Post = {
  id: number;
  platform: string;
  source_id: string;
  keyword: string;
  author_name: string | null;
  author_handle: string | null;
  content: string | null;
  url: string | null;
  published_at: string | null;
  like_count: number | null;
  comment_count: number | null;
  share_count: number | null;
  collected_at: string;
};

export type PostList = {
  total: number;
  items: Post[];
};

export type PostFilters = {
  keyword?: string;
  platform?: string;
  q?: string;
};
```

- [ ] **Step 5: Create API client**

```typescript
import type { PostFilters, PostList } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_AGGREGATOR_API_URL ?? "http://localhost:8000";

export function buildPostsUrl(filters: PostFilters): string {
  const url = new URL("/posts", API_BASE_URL);

  Object.entries(filters).forEach(([key, value]) => {
    if (value) {
      url.searchParams.set(key, value);
    }
  });

  return url.toString();
}

export async function fetchPosts(filters: PostFilters): Promise<PostList> {
  const response = await fetch(buildPostsUrl(filters), { cache: "no-store" });

  if (!response.ok) {
    throw new Error(`Aggregator request failed: ${response.status}`);
  }

  return response.json();
}
```

- [ ] **Step 6: Run typecheck**

Run: `cd apps/dashboard && npm install && npm run typecheck`

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add apps/dashboard/README.md apps/dashboard/package.json apps/dashboard/next.config.js apps/dashboard/tsconfig.json apps/dashboard/.env.example apps/dashboard/lib/types.ts apps/dashboard/lib/api.ts
git commit -m "chore: scaffold dashboard app"
```

---

### Task 7: Dashboard Page and Styles

**Files:**
- Create: `apps/dashboard/app/layout.tsx`
- Create: `apps/dashboard/app/page.tsx`
- Create: `apps/dashboard/app/globals.css`

- [ ] **Step 1: Create root layout**

```tsx
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Public Opinin Analytics",
  description: "Public opinion analytics dashboard",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

- [ ] **Step 2: Create the dashboard page**

```tsx
import { fetchPosts } from "../lib/api";

type PageProps = {
  searchParams?: Promise<{
    keyword?: string;
    platform?: string;
    q?: string;
  }>;
};

export default async function DashboardPage({ searchParams }: PageProps) {
  const filters = (await searchParams) ?? {};
  let data;
  let error: string | null = null;

  try {
    data = await fetchPosts(filters);
  } catch (err) {
    error = err instanceof Error ? err.message : "Unable to load aggregator data";
    data = { total: 0, items: [] };
  }

  const platforms = new Set(data.items.map((item) => item.platform));
  const keywords = new Set(data.items.map((item) => item.keyword));
  const commentTotal = data.items.reduce((sum, item) => sum + (item.comment_count ?? 0), 0);

  return (
    <main className="page">
      <header className="header">
        <div>
          <p className="eyebrow">Public Opinin Analytics</p>
          <h1>Collected social posts</h1>
        </div>
      </header>

      <section className="stats" aria-label="Summary">
        <div><span>{data.total}</span><p>Posts</p></div>
        <div><span>{commentTotal}</span><p>Comments</p></div>
        <div><span>{platforms.size}</span><p>Platforms</p></div>
        <div><span>{keywords.size}</span><p>Keywords</p></div>
      </section>

      <form className="filters">
        <input name="keyword" placeholder="Keyword" defaultValue={filters.keyword ?? ""} />
        <select name="platform" defaultValue={filters.platform ?? ""}>
          <option value="">All platforms</option>
          <option value="threads">Threads</option>
          <option value="instagram">Instagram</option>
          <option value="facebook">Facebook</option>
          <option value="x">X</option>
          <option value="tiktok">TikTok</option>
        </select>
        <input name="q" placeholder="Search text or author" defaultValue={filters.q ?? ""} />
        <button type="submit">Apply</button>
      </form>

      {error ? <p className="error">{error}</p> : null}

      <section className="tableWrap">
        <table>
          <thead>
            <tr>
              <th>Platform</th>
              <th>Keyword</th>
              <th>Author</th>
              <th>Content</th>
              <th>Engagement</th>
              <th>Collected</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((post) => (
              <tr key={`${post.platform}-${post.source_id}`}>
                <td>{post.platform}</td>
                <td>{post.keyword}</td>
                <td>{post.author_handle ?? post.author_name ?? "-"}</td>
                <td>
                  {post.url ? <a href={post.url}>{post.content ?? post.url}</a> : post.content ?? "-"}
                </td>
                <td>{post.like_count ?? 0} likes / {post.comment_count ?? 0} comments / {post.share_count ?? 0} shares</td>
                <td>{post.collected_at}</td>
              </tr>
            ))}
            {data.items.length === 0 ? (
              <tr>
                <td colSpan={6} className="empty">No posts match the current filters.</td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </section>
    </main>
  );
}
```

- [ ] **Step 3: Create CSS**

```css
:root {
  color: #16181d;
  background: #f6f7f9;
  font-family: Arial, Helvetica, sans-serif;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
}

a {
  color: #1267b1;
}

.page {
  width: min(1180px, calc(100% - 32px));
  margin: 0 auto;
  padding: 40px 0;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: end;
  margin-bottom: 24px;
}

.eyebrow {
  margin: 0 0 8px;
  color: #647084;
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
}

h1 {
  margin: 0;
  font-size: 34px;
}

.stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 18px;
}

.stats div,
.filters,
.tableWrap {
  border: 1px solid #dce1e8;
  background: #ffffff;
  border-radius: 8px;
}

.stats div {
  padding: 16px;
}

.stats span {
  display: block;
  font-size: 28px;
  font-weight: 700;
}

.stats p {
  margin: 4px 0 0;
  color: #647084;
}

.filters {
  display: grid;
  grid-template-columns: 1fr 180px 1.4fr auto;
  gap: 10px;
  padding: 12px;
  margin-bottom: 18px;
}

input,
select,
button {
  min-height: 40px;
  border: 1px solid #c9d1dc;
  border-radius: 6px;
  padding: 0 12px;
  font: inherit;
}

button {
  background: #1f2937;
  color: white;
  cursor: pointer;
}

.error {
  border: 1px solid #f0b8b8;
  background: #fff1f1;
  color: #9b1c1c;
  border-radius: 8px;
  padding: 12px;
}

.tableWrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  padding: 12px;
  border-bottom: 1px solid #edf0f4;
  text-align: left;
  vertical-align: top;
  font-size: 14px;
}

th {
  color: #647084;
  font-size: 12px;
  text-transform: uppercase;
}

.empty {
  text-align: center;
  color: #647084;
}

@media (max-width: 760px) {
  .stats,
  .filters {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 4: Run dashboard validation**

Run: `cd apps/dashboard && npm run typecheck && npm run build`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add apps/dashboard/app/layout.tsx apps/dashboard/app/page.tsx apps/dashboard/app/globals.css
git commit -m "feat: add dashboard posts view"
```

---

### Task 8: Shared Contracts

**Files:**
- Create: `packages/shared/README.md`
- Create: `packages/shared/schemas/openapi.yaml`
- Create: `packages/shared/schemas/database.md`

- [ ] **Step 1: Create shared package README**

```markdown
# Shared Contracts

API and database contracts shared by the aggregator and dashboard.

The MVP keeps these contracts as source-controlled documentation. Generated clients and schema packages can be added here later.
```

- [ ] **Step 2: Create OpenAPI contract**

```yaml
openapi: 3.1.0
info:
  title: Public Opinin Aggregator API
  version: 0.1.0
paths:
  /health:
    get:
      responses:
        "200":
          description: Service health
  /keywords:
    get:
      responses:
        "200":
          description: Active keywords
    post:
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [value]
              properties:
                value:
                  type: string
      responses:
        "200":
          description: Created or reactivated keyword
  /runs/search:
    post:
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                keywords:
                  type: array
                  items:
                    type: string
                platforms:
                  type: array
                  items:
                    type: string
      responses:
        "200":
          description: Ingestion run result
  /posts:
    get:
      parameters:
        - name: keyword
          in: query
          schema:
            type: string
        - name: platform
          in: query
          schema:
            type: string
        - name: q
          in: query
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            default: 100
      responses:
        "200":
          description: Filtered posts
```

- [ ] **Step 3: Create database contract**

```markdown
# Database Schema

The aggregator owns SQLite access. Dashboard code must use HTTP APIs instead of reading this database directly.

## `keywords`

- `id`: integer primary key.
- `value`: unique keyword text.
- `is_active`: `1` for active scheduler keywords, `0` for disabled keywords.
- `created_at`, `updated_at`: SQLite timestamps.

## `ingestion_runs`

- `id`: integer primary key.
- `status`: `running`, `succeeded`, or `failed`.
- `requested_keywords`: JSON array of keyword strings.
- `requested_platforms`: JSON array of platform strings.
- `posts_count`, `comments_count`: persisted item counts.
- `error_message`: provider or processing failure text.
- `started_at`, `finished_at`: run timestamps.

## `posts`

- `platform`: `threads`, `instagram`, `facebook`, `x`, or `tiktok`.
- `source_id`: source platform or Apify item ID.
- `keyword`: keyword that produced the item.
- `author_name`, `author_handle`, `content`, `url`, `published_at`: normalized display fields.
- `like_count`, `comment_count`, `share_count`: normalized engagement fields.
- `raw_json`: complete source payload serialized as JSON text.
- `collected_at`: ingestion timestamp.

## `comments`

- `post_id`: foreign key to `posts.id`.
- `platform`, `source_id`: unique source identity.
- `author_name`, `author_handle`, `content`, `published_at`, `like_count`: normalized display fields.
- `raw_json`: complete source payload serialized as JSON text.
- `collected_at`: ingestion timestamp.
```

- [ ] **Step 4: Verify docs exist**

Run: `rg --files packages/shared`

Expected: lists all three shared contract files.

- [ ] **Step 5: Commit**

```bash
git add packages/shared/README.md packages/shared/schemas/openapi.yaml packages/shared/schemas/database.md
git commit -m "docs: add shared api contracts"
```

---

### Task 9: End-to-End Local Verification

**Files:**
- Modify only files needed for defects found by the commands below.

- [ ] **Step 1: Run aggregator tests**

Run: `cd apps/aggregator && pytest -q`

Expected: PASS.

- [ ] **Step 2: Start aggregator**

Run: `cd apps/aggregator && uvicorn public_opinin_aggregator.main:app --port 8000`

Expected: service stays running at `http://localhost:8000`.

- [ ] **Step 3: Seed dry-run data**

Run:

```bash
curl -s -X POST http://localhost:8000/keywords -H 'content-type: application/json' -d '{"value":"policy"}'
curl -s -X POST http://localhost:8000/runs/search -H 'content-type: application/json' -d '{"keywords":["policy"],"platforms":["threads","x"]}'
curl -s 'http://localhost:8000/posts?keyword=policy'
```

Expected: posts response contains two dry-run items.

- [ ] **Step 4: Run dashboard checks**

Run: `cd apps/dashboard && npm run typecheck && npm run build`

Expected: PASS.

- [ ] **Step 5: Start dashboard**

Run: `cd apps/dashboard && npm run dev`

Expected: dashboard runs at `http://localhost:3000` and displays the seeded posts.

- [ ] **Step 6: Commit final fixes if any**

```bash
git add apps packages README.md
git commit -m "fix: complete local monorepo verification"
```

Skip this commit if no verification fixes were needed.

---

## Self-Review

- Spec coverage: The plan covers monorepo structure, FastAPI aggregator endpoints, scheduler-triggerable ingestion, Apify adapter boundary, SQLite persistence, dashboard API reads, filters, and shared contracts.
- Placeholder scan: No task uses unspecified implementation placeholders. Platform actor mapping is intentionally environment-configured because actor IDs are not known yet.
- Type consistency: Pydantic and TypeScript API field names match the planned `/posts` response contract.
