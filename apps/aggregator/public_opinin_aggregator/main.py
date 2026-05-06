from contextlib import asynccontextmanager
import re

from fastapi import FastAPI, Query, Request

from . import repository
from .apify_client import ApifySearchClient
from .config import Settings, get_settings
from .db import connect, initialize_database
from .models import KeywordCreate, KeywordList, KeywordRead, PostList, SearchRunCreate, SearchRunRead


def redact_secret_values(message: str) -> str:
    return re.sub(r"token=[^'&\s]+", "token=<redacted>", message)


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
            row = repository.finish_run(
                connection,
                run_id,
                "failed",
                posts_count,
                comments_count,
                redact_secret_values(str(exc)),
            )
        return SearchRunRead(**row)

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
