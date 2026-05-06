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
