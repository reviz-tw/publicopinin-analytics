from fastapi.testclient import TestClient

from public_opinin_aggregator.config import Settings
from public_opinin_aggregator.db import connect, initialize_database
from public_opinin_aggregator.main import create_app


class FailingSearchClient:
    async def search(self, keyword, platform):
        raise RuntimeError(
            "Client error '400 Bad Request' for url "
            "'https://api.apify.com/v2/acts/example/run-sync-get-dataset-items?token=secret-token'"
        )


class FakeDatasetClient:
    def __init__(self):
        self.dataset_ids: list[str] = []
        self.recent_limit: int | None = None

    async def list_recent_datasets(self, limit: int):
        self.recent_limit = limit
        return [
            {"id": "dataset-threads", "actId": "actor-threads", "actRunId": "run-threads"},
            {"id": "dataset-existing", "actId": "actor-existing", "actRunId": "run-existing"},
        ]

    async def get_dataset_items(self, dataset_id: str):
        self.dataset_ids.append(dataset_id)
        if dataset_id == "dataset-threads":
            return [
                {
                    "id": "post-threads",
                    "text": "A candidate result that needs local filtering",
                    "url": "https://www.threads.com/t/abc123",
                    "authorName": "Threads Author",
                }
            ]
        return [
            {
                "id": "post-1",
                "text": "Dataset item about 國際特赦組織",
                "url": "https://example.com/post-1",
                "authorName": "Dataset Author",
                "authorHandle": "@dataset_author",
                "likesCount": 7,
                "commentsCount": 1,
                "sharesCount": 2,
                "comments": [
                    {
                        "id": "comment-1",
                        "text": "Dataset comment",
                        "authorName": "Comment Author",
                        "authorHandle": "@comment_author",
                        "likesCount": 3,
                    }
                ],
            }
        ]


def isolated_settings(database_url: str) -> Settings:
    return Settings(
        database_url=database_url,
        apify_token=None,
        apify_actor_threads=None,
        apify_actor_instagram=None,
        apify_actor_facebook=None,
        apify_actor_x=None,
        apify_actor_tiktok=None,
    )


def test_health_endpoint(tmp_path):
    db_url = f"sqlite:///{tmp_path / 'test.db'}"
    app = create_app(isolated_settings(db_url))

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
    app = create_app(isolated_settings(f"sqlite:///{tmp_path / 'test.db'}"))

    with TestClient(app) as client:
        created = client.post("/keywords", json={"value": "election"}).json()
        listed = client.get("/keywords").json()

    assert created["value"] == "election"
    assert created["is_active"] is True
    assert listed["items"][0]["value"] == "election"


def test_search_run_persists_dry_run_posts_and_comments(tmp_path):
    db_path = tmp_path / "test.db"
    app = create_app(isolated_settings(f"sqlite:///{db_path}"))

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
    app = create_app(isolated_settings(f"sqlite:///{tmp_path / 'test.db'}"))

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


def test_posts_endpoint_supports_limit_and_offset_pagination(tmp_path):
    app = create_app(isolated_settings(f"sqlite:///{tmp_path / 'test.db'}"))

    with TestClient(app) as client:
        for keyword in ("alpha", "beta", "gamma"):
            client.post("/runs/search", json={"keywords": [keyword], "platforms": ["threads"]})
        first_page = client.get("/posts", params={"limit": 2, "offset": 0}).json()
        second_page = client.get("/posts", params={"limit": 2, "offset": 2}).json()

    assert first_page["total"] == 3
    assert len(first_page["items"]) == 2
    assert len(second_page["items"]) == 1
    first_page_ids = {item["id"] for item in first_page["items"]}
    second_page_ids = {item["id"] for item in second_page["items"]}
    assert first_page_ids.isdisjoint(second_page_ids)


def test_search_run_redacts_provider_tokens_from_error_message(tmp_path):
    app = create_app(isolated_settings(f"sqlite:///{tmp_path / 'test.db'}"))

    with TestClient(app) as client:
        client.app.state.search_client = FailingSearchClient()
        response = client.post(
            "/runs/search",
            json={"keywords": ["policy"], "platforms": ["threads"]},
        )

    payload = response.json()
    assert payload["status"] == "failed"
    assert "secret-token" not in payload["error_message"]
    assert "token=<redacted>" in payload["error_message"]


def test_manual_dataset_sync_persists_posts_comments_and_run_metadata(tmp_path):
    app = create_app(isolated_settings(f"sqlite:///{tmp_path / 'test.db'}"))
    dataset_client = FakeDatasetClient()

    with TestClient(app) as client:
        client.app.state.dataset_client = dataset_client
        run = client.post(
            "/apify/datasets/dataset-123/sync",
            json={
                "platform": "threads",
                "keyword": "國際特赦組織",
                "apify_run_id": "run-123",
                "apify_actor_id": "actor-123",
                "apify_actor_task_id": "task-123",
            },
        ).json()
        posts = client.get("/posts", params={"keyword": "國際特赦組織", "platform": "threads"}).json()

    assert dataset_client.dataset_ids == ["dataset-123"]
    assert run["status"] == "succeeded"
    assert run["source"] == "apify"
    assert run["apify_dataset_id"] == "dataset-123"
    assert run["apify_run_id"] == "run-123"
    assert run["posts_count"] == 1
    assert run["comments_count"] == 1
    assert posts["total"] == 1
    assert posts["items"][0]["content"] == "Dataset item about 國際特赦組織"


def test_apify_webhook_run_finished_syncs_default_dataset(tmp_path):
    app = create_app(isolated_settings(f"sqlite:///{tmp_path / 'test.db'}"))
    dataset_client = FakeDatasetClient()

    with TestClient(app) as client:
        client.app.state.dataset_client = dataset_client
        response = client.post(
            "/webhooks/apify/run-finished",
            params={"platform": "threads", "keyword": "國際特赦組織"},
            json={
                "eventType": "ACTOR.RUN.SUCCEEDED",
                "resource": {
                    "id": "run-from-webhook",
                    "status": "SUCCEEDED",
                    "actId": "actor-from-webhook",
                    "actorTaskId": "task-from-webhook",
                    "defaultDatasetId": "dataset-from-webhook",
                },
            },
        )

    payload = response.json()
    assert response.status_code == 200
    assert dataset_client.dataset_ids == ["dataset-from-webhook"]
    assert payload["status"] == "succeeded"
    assert payload["apify_run_id"] == "run-from-webhook"
    assert payload["apify_dataset_id"] == "dataset-from-webhook"


def test_sync_recent_datasets_infers_platform_and_skips_existing_dataset(tmp_path):
    db_path = tmp_path / "test.db"
    app = create_app(isolated_settings(f"sqlite:///{db_path}"))
    dataset_client = FakeDatasetClient()
    connection = connect(f"sqlite:///{db_path}")
    initialize_database(connection)
    connection.execute(
        """
        INSERT INTO ingestion_runs (
            status, requested_keywords, requested_platforms, source, apify_dataset_id,
            posts_count, comments_count, finished_at
        )
        VALUES ('succeeded', '["unknown"]', '["unknown"]', 'apify', 'dataset-existing', 0, 0, CURRENT_TIMESTAMP)
        """
    )
    connection.commit()

    with TestClient(app) as client:
        client.app.state.dataset_client = dataset_client
        response = client.post("/apify/datasets/sync-recent", json={"limit": 2})
        posts = client.get("/posts", params={"platform": "threads", "keyword": "unknown"}).json()

    payload = response.json()
    assert response.status_code == 200
    assert dataset_client.recent_limit == 2
    assert dataset_client.dataset_ids == ["dataset-threads"]
    assert payload["synced"] == 1
    assert payload["skipped"] == 1
    assert payload["runs"][0]["apify_dataset_id"] == "dataset-threads"
    assert posts["total"] == 1
    assert posts["items"][0]["platform"] == "threads"
    assert posts["items"][0]["keyword"] == "unknown"
