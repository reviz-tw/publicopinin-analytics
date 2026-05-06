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
