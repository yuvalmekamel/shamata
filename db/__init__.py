import sqlite3
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fetcher import Article

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS articles (
    guid        TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    url         TEXT NOT NULL,
    summary     TEXT,
    published_at TEXT,
    source      TEXT NOT NULL,
    fetched_at  TEXT NOT NULL,
    score       REAL,
    feedback    TEXT            -- 'liked' | 'disliked' | NULL
)
"""


def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    """Create the database and tables if they don't exist."""
    with get_connection(db_path) as conn:
        conn.execute(CREATE_TABLE_SQL)


def save_articles(articles: list["Article"], db_path: str) -> tuple[int, int]:
    """
    Insert articles into the DB, skipping any whose guid already exists.
    Returns (new_count, duplicate_count).
    """
    fetched_at = datetime.now(timezone.utc).isoformat()
    new_count = 0

    with get_connection(db_path) as conn:
        for article in articles:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO articles
                    (guid, title, url, summary, published_at, source, fetched_at, score, feedback)
                VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL)
                """,
                (
                    article.guid,
                    article.title,
                    article.url,
                    article.summary,
                    article.published_at.isoformat() if article.published_at else None,
                    article.source,
                    fetched_at,
                ),
            )
            new_count += cursor.rowcount

    duplicate_count = len(articles) - new_count
    return new_count, duplicate_count


def get_unscored_articles(db_path: str) -> list[dict]:
    """Return all articles that have no score yet, newest first."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM articles WHERE score IS NULL ORDER BY published_at DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_recent_articles(db_path: str, hours: int = 24, min_score: float = 0.0) -> list[dict]:
    """Return scored articles from the last N hours, ordered by score descending."""
    with get_connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT * FROM articles
            WHERE fetched_at >= datetime('now', ?)
              AND score IS NOT NULL
              AND score >= ?
            ORDER BY score DESC
            """,
            (f"-{hours} hours", min_score),
        ).fetchall()
    return [dict(row) for row in rows]
