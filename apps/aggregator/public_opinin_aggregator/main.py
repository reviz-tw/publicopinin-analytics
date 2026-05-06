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
