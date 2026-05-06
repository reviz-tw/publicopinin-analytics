from contextlib import asynccontextmanager
import re

from fastapi import FastAPI, HTTPException, Query, Request

from . import repository
from .apify_client import ApifyDatasetClient, ApifySearchClient, SearchResult, normalize_dataset_items
from .config import Settings, get_settings
from .db import connect, initialize_database
from .models import ApifyDatasetSyncCreate, KeywordCreate, KeywordList, KeywordRead, PostList, SearchRunCreate, SearchRunRead


def redact_secret_values(message: str) -> str:
    return re.sub(r"token=[^'&\s]+", "token=<redacted>", message)


def extract_apify_resource(payload: dict) -> dict:
    resource = payload.get("resource")
    if isinstance(resource, dict):
        return resource
    return payload


def persist_search_result(connection, run_id: int, result: SearchResult) -> tuple[int, int, dict]:
    posts_count = 0
    comments_count = 0
    for post in result.posts:
        post_id = repository.upsert_post(connection, post)
        posts_count += 1
        for comment in result.comments:
            if comment.get("post_source_id") == post["source_id"]:
                repository.upsert_comment(connection, post_id, comment)
                comments_count += 1
    row = repository.finish_run(connection, run_id, "succeeded", posts_count, comments_count)
    return posts_count, comments_count, row


async def sync_apify_dataset(
    request: Request,
    dataset_id: str,
    platform: str,
    keyword: str,
    apify_run_id: str | None = None,
    apify_actor_id: str | None = None,
    apify_actor_task_id: str | None = None,
) -> SearchRunRead:
    connection = request.app.state.db
    run_id = repository.create_apify_run(
        connection,
        keyword=keyword,
        platform=platform,
        dataset_id=dataset_id,
        apify_run_id=apify_run_id,
        apify_actor_id=apify_actor_id,
        apify_actor_task_id=apify_actor_task_id,
    )
    try:
        items = await request.app.state.dataset_client.get_dataset_items(dataset_id)
        result = normalize_dataset_items(items, keyword=keyword, platform=platform)
        _, _, row = persist_search_result(connection, run_id, result)
    except Exception as exc:
        row = repository.finish_run(
            connection,
            run_id,
            "failed",
            0,
            0,
            redact_secret_values(str(exc)),
        )
    return SearchRunRead(**row)


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        connection = connect(app_settings.database_url)
        initialize_database(connection)
        app.state.db = connection
        app.state.search_client = ApifySearchClient(app_settings.apify_token, app_settings.apify_actors)
        app.state.dataset_client = ApifyDatasetClient(app_settings.apify_token)
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
            row = repository.finish_run(
                connection,
                run_id,
                "failed",
                posts_count,
                comments_count,
                redact_secret_values(str(exc)),
            )
        return SearchRunRead(**row)

    @app.post("/apify/datasets/{dataset_id}/sync", response_model=SearchRunRead)
    async def sync_dataset(dataset_id: str, payload: ApifyDatasetSyncCreate, request: Request) -> SearchRunRead:
        return await sync_apify_dataset(
            request,
            dataset_id=dataset_id,
            platform=payload.platform,
            keyword=payload.keyword,
            apify_run_id=payload.apify_run_id,
            apify_actor_id=payload.apify_actor_id,
            apify_actor_task_id=payload.apify_actor_task_id,
        )

    @app.post("/webhooks/apify/run-finished", response_model=SearchRunRead)
    async def apify_run_finished_webhook(
        request: Request,
        platform: str,
        keyword: str,
    ) -> SearchRunRead:
        payload = await request.json()
        resource = extract_apify_resource(payload)
        dataset_id = resource.get("defaultDatasetId") or resource.get("default_dataset_id")
        if not dataset_id:
            raise HTTPException(status_code=400, detail="Apify webhook payload is missing defaultDatasetId")

        status = str(resource.get("status") or payload.get("eventType") or "").lower()
        if "succeeded" not in status and "success" not in status:
            raise HTTPException(status_code=202, detail=f"Ignored Apify run status: {status or 'unknown'}")

        return await sync_apify_dataset(
            request,
            dataset_id=dataset_id,
            platform=platform,
            keyword=keyword,
            apify_run_id=resource.get("id"),
            apify_actor_id=resource.get("actId") or resource.get("actorId"),
            apify_actor_task_id=resource.get("actorTaskId"),
        )

    @app.get("/posts", response_model=PostList)
    def get_posts(
        request: Request,
        keyword: str | None = None,
        platform: str | None = None,
        author: str | None = None,
        q: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = Query(default=100, ge=1, le=500),
    ) -> PostList:
        total, rows = repository.list_posts(
            request.app.state.db,
            keyword=keyword,
            platform=platform,
            author=author,
            q=q,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )
        return PostList(total=total, items=rows)

    return app


app = create_app()
