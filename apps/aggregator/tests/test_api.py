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


def test_create_and_list_keywords(tmp_path):
    app = create_app(Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}"))

    with TestClient(app) as client:
        created = client.post("/keywords", json={"value": "election"}).json()
        listed = client.get("/keywords").json()

    assert created["value"] == "election"
    assert created["is_active"] is True
    assert listed["items"][0]["value"] == "election"


def test_search_run_persists_dry_run_posts_and_comments(tmp_path):
    db_path = tmp_path / "test.db"
    app = create_app(Settings(database_url=f"sqlite:///{db_path}"))

    with TestClient(app) as client:
        run = client.post(
            "/runs/search",
            json={"keywords": ["policy"], "platforms": ["threads"]},
        ).json()
        posts = client.get(
            "/posts",
            params={"keyword": "policy", "platform": "threads"},
        ).json()

    assert run["status"] == "succeeded"
    assert run["posts_count"] == 1
    assert run["comments_count"] == 1
    assert posts["total"] == 1
    assert posts["items"][0]["keyword"] == "policy"
    assert posts["items"][0]["platform"] == "threads"

    connection = connect(f"sqlite:///{db_path}")
    comments_count = connection.execute("SELECT COUNT(*) AS count FROM comments").fetchone()["count"]
    assert comments_count == 1


def test_posts_endpoint_filters_by_text_author_and_date(tmp_path):
    app = create_app(Settings(database_url=f"sqlite:///{tmp_path / 'test.db'}"))

    with TestClient(app) as client:
        client.post("/runs/search", json={"keywords": ["policy"], "platforms": ["threads"]})
        client.post("/runs/search", json={"keywords": ["sports"], "platforms": ["x"]})
        matched = client.get(
            "/posts",
            params={
                "q": "policy",
                "author": "Dry Run",
                "date_from": "2000-01-01T00:00:00",
                "date_to": "2999-01-01T00:00:00",
            },
        ).json()
        unmatched = client.get("/posts", params={"q": "does-not-exist"}).json()

    assert matched["total"] == 1
    assert matched["items"][0]["keyword"] == "policy"
    assert unmatched["total"] == 0
