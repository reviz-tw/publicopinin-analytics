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
    row = connection.execute("SELECT * FROM keywords WHERE value = ?", (normalized,)).fetchone()
    return row_to_dict(row)


def list_keywords(connection: sqlite3.Connection, active_only: bool = True) -> list[dict[str, Any]]:
    sql = "SELECT * FROM keywords"
    if active_only:
        sql += " WHERE is_active = 1"
    sql += " ORDER BY value"
    return [row_to_dict(row) for row in connection.execute(sql).fetchall()]


def active_keyword_values(connection: sqlite3.Connection) -> list[str]:
    rows = connection.execute("SELECT value FROM keywords WHERE is_active = 1 ORDER BY value").fetchall()
    return [row["value"] for row in rows]


def create_run(connection: sqlite3.Connection, keywords: list[str], platforms: list[str]) -> int:
    cursor = connection.execute(
        """
        INSERT INTO ingestion_runs (status, requested_keywords, requested_platforms, source)
        VALUES ('running', ?, ?, 'debug')
        """,
        (json.dumps(keywords), json.dumps(platforms)),
    )
    connection.commit()
    return int(cursor.lastrowid)


def create_apify_run(
    connection: sqlite3.Connection,
    keyword: str,
    platform: str,
    dataset_id: str,
    apify_run_id: str | None = None,
    apify_actor_id: str | None = None,
    apify_actor_task_id: str | None = None,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO ingestion_runs (
            status, requested_keywords, requested_platforms, source,
            apify_run_id, apify_actor_id, apify_actor_task_id, apify_dataset_id
        )
        VALUES ('running', ?, ?, 'apify', ?, ?, ?, ?)
        """,
        (
            json.dumps([keyword]),
            json.dumps([platform]),
            apify_run_id,
            apify_actor_id,
            apify_actor_task_id,
            dataset_id,
        ),
    )
    connection.commit()
    return int(cursor.lastrowid)


def dataset_was_synced(connection: sqlite3.Connection, dataset_id: str) -> bool:
    row = connection.execute(
        """
        SELECT 1
        FROM ingestion_runs
        WHERE source = 'apify' AND apify_dataset_id = ? AND status = 'succeeded'
        LIMIT 1
        """,
        (dataset_id,),
    ).fetchone()
    return row is not None


def finish_run(
    connection: sqlite3.Connection,
    run_id: int,
    status: str,
    posts_count: int,
    comments_count: int,
    error_message: str | None = None,
) -> dict[str, Any]:
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


def list_posts(
    connection: sqlite3.Connection,
    keyword: str | None = None,
    platform: str | None = None,
    author: str | None = None,
    q: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[int, list[dict[str, Any]]]:
    clauses = []
    params: list[Any] = []
    if keyword:
        clauses.append("keyword = ?")
        params.append(keyword)
    if platform:
        clauses.append("platform = ?")
        params.append(platform)
    if author:
        clauses.append("(author_name LIKE ? OR author_handle LIKE ?)")
        pattern = f"%{author}%"
        params.extend([pattern, pattern])
    if q:
        clauses.append("(content LIKE ? OR author_name LIKE ? OR author_handle LIKE ?)")
        pattern = f"%{q}%"
        params.extend([pattern, pattern, pattern])
    if date_from:
        clauses.append("collected_at >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("collected_at <= ?")
        params.append(date_to)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    total = connection.execute(f"SELECT COUNT(*) AS count FROM posts {where}", params).fetchone()["count"]
    rows = connection.execute(
        f"""
        SELECT id, platform, source_id, keyword, author_name, author_handle, content, url,
               published_at, like_count, comment_count, share_count, collected_at
        FROM posts
        {where}
        ORDER BY collected_at DESC, id DESC
        LIMIT ? OFFSET ?
        """,
        [*params, limit, offset],
    ).fetchall()
    return int(total), [row_to_dict(row) for row in rows]
