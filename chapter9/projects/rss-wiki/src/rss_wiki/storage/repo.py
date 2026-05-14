import sqlite3
from collections.abc import Sequence


def upsert_feed(conn: sqlite3.Connection, name: str, url: str) -> int:
    conn.execute(
        "INSERT OR IGNORE INTO feeds (name, url) VALUES (?, ?)",
        (name, url),
    )
    row = conn.execute("SELECT id FROM feeds WHERE url = ?", (url,)).fetchone()
    return row["id"]


def get_feed_by_url(conn: sqlite3.Connection, url: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM feeds WHERE url = ?", (url,)).fetchone()


def insert_article(
    conn: sqlite3.Connection,
    *,
    feed_id: int,
    url: str,
    url_hash: str,
    title: str | None,
    title_hash: str | None,
    published_at: str | None,
    content: str | None,
    summary: str | None,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO articles
            (feed_id, url, url_hash, title, title_hash, published_at, content, summary)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (feed_id, url, url_hash, title, title_hash, published_at, content, summary),
    )
    return cursor.lastrowid


def get_article_by_url_hash(
    conn: sqlite3.Connection, url_hash: str
) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM articles WHERE url_hash = ?", (url_hash,)
    ).fetchone()


def get_article_by_title_hash(
    conn: sqlite3.Connection, title_hash: str
) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM articles WHERE title_hash = ?", (title_hash,)
    ).fetchone()


def upsert_category(conn: sqlite3.Connection, name: str) -> int:
    normalized = name.strip().lower()
    conn.execute(
        "INSERT OR IGNORE INTO categories (name) VALUES (?)",
        (normalized,),
    )
    row = conn.execute(
        "SELECT id FROM categories WHERE name = ?", (normalized,)
    ).fetchone()
    return row["id"]


def upsert_tag(conn: sqlite3.Connection, name: str) -> int:
    normalized = name.strip().lower()
    conn.execute(
        "INSERT OR IGNORE INTO tags (name) VALUES (?)",
        (normalized,),
    )
    row = conn.execute(
        "SELECT id FROM tags WHERE name = ?", (normalized,)
    ).fetchone()
    return row["id"]


def link_article_category(
    conn: sqlite3.Connection, article_id: int, category_id: int
) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO article_categories (article_id, category_id) VALUES (?, ?)",
        (article_id, category_id),
    )


def link_article_tag(
    conn: sqlite3.Connection, article_id: int, tag_id: int
) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO article_tags (article_id, tag_id) VALUES (?, ?)",
        (article_id, tag_id),
    )


def insert_magazine(
    conn: sqlite3.Connection,
    *,
    kind: str,
    published_at: str,
    file_path: str,
) -> int:
    cursor = conn.execute(
        "INSERT INTO magazines (kind, published_at, file_path) VALUES (?, ?, ?)",
        (kind, published_at, file_path),
    )
    return cursor.lastrowid


def link_magazine_article(
    conn: sqlite3.Connection, magazine_id: int, article_id: int
) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO magazine_articles (magazine_id, article_id) VALUES (?, ?)",
        (magazine_id, article_id),
    )


def record_feed_success(conn: sqlite3.Connection, feed_id: int) -> None:
    conn.execute(
        "UPDATE feeds SET consecutive_failures = 0, last_success_at = datetime('now') WHERE id = ?",
        (feed_id,),
    )


def record_feed_failure(conn: sqlite3.Connection, feed_id: int) -> None:
    conn.execute(
        "UPDATE feeds SET consecutive_failures = consecutive_failures + 1 WHERE id = ?",
        (feed_id,),
    )


def list_failing_feeds(conn: sqlite3.Connection, *, threshold: int = 5) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            "SELECT * FROM feeds WHERE consecutive_failures >= ? ORDER BY consecutive_failures DESC, name ASC",
            (threshold,),
        ).fetchall()
    )


def list_categories(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return list(
        conn.execute("SELECT id, name FROM categories ORDER BY name ASC").fetchall()
    )


def list_articles_by_ids(
    conn: sqlite3.Connection, article_ids: Sequence[int]
) -> list[sqlite3.Row]:
    if not article_ids:
        return []
    placeholders = ",".join("?" * len(article_ids))
    rows = conn.execute(
        f"SELECT * FROM articles WHERE id IN ({placeholders}) ORDER BY id ASC",
        tuple(article_ids),
    ).fetchall()
    return list(rows)


def update_article_summary(
    conn: sqlite3.Connection, *, article_id: int, summary: str
) -> None:
    conn.execute(
        "UPDATE articles SET summary = ? WHERE id = ?",
        (summary, article_id),
    )


def list_categories_for_article(
    conn: sqlite3.Connection, article_id: int
) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            """
            SELECT c.id, c.name
            FROM categories c
            JOIN article_categories ac ON ac.category_id = c.id
            WHERE ac.article_id = ?
            ORDER BY c.name ASC
            """,
            (article_id,),
        ).fetchall()
    )


def list_tags_for_article(
    conn: sqlite3.Connection, article_id: int
) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            """
            SELECT t.id, t.name
            FROM tags t
            JOIN article_tags at ON at.tag_id = t.id
            WHERE at.article_id = ?
            ORDER BY t.name ASC
            """,
            (article_id,),
        ).fetchall()
    )


def list_tags(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return list(
        conn.execute("SELECT id, name FROM tags ORDER BY name ASC").fetchall()
    )


def list_articles_by_category(
    conn: sqlite3.Connection, category_id: int
) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            """
            SELECT a.*
            FROM articles a
            JOIN article_categories ac ON ac.article_id = a.id
            WHERE ac.category_id = ?
            ORDER BY a.published_at DESC NULLS LAST, a.id DESC
            """,
            (category_id,),
        ).fetchall()
    )


def list_articles_by_tag(
    conn: sqlite3.Connection, tag_id: int
) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            """
            SELECT a.*
            FROM articles a
            JOIN article_tags at ON at.article_id = a.id
            WHERE at.tag_id = ?
            ORDER BY a.published_at DESC NULLS LAST, a.id DESC
            """,
            (tag_id,),
        ).fetchall()
    )


def list_unanalyzed_article_ids(conn: sqlite3.Connection) -> list[int]:
    """summary가 NULL이거나 빈 문자열인 글의 id 목록을 반환(생성 순=id ASC)."""
    cur = conn.execute(
        "SELECT id FROM articles WHERE summary IS NULL OR summary = '' ORDER BY id ASC"
    )
    return [r["id"] for r in cur.fetchall()]


def list_feeds(conn: sqlite3.Connection, *, enabled_only: bool = False) -> list[sqlite3.Row]:
    if enabled_only:
        return list(conn.execute("SELECT * FROM feeds WHERE enabled = 1 ORDER BY id ASC").fetchall())
    return list(conn.execute("SELECT * FROM feeds ORDER BY id ASC").fetchall())


def update_feed(
    conn: sqlite3.Connection,
    feed_id: int,
    *,
    name: str,
    url: str | None = None,
) -> None:
    if url is None:
        conn.execute(
            "UPDATE feeds SET name = ?, updated_at = datetime('now') WHERE id = ?",
            (name, feed_id),
        )
    else:
        conn.execute(
            "UPDATE feeds SET name = ?, url = ?, updated_at = datetime('now') WHERE id = ?",
            (name, url, feed_id),
        )


def set_feed_enabled(conn: sqlite3.Connection, feed_id: int, enabled: bool) -> None:
    conn.execute(
        "UPDATE feeds SET enabled = ?, updated_at = datetime('now') WHERE id = ?",
        (int(enabled), feed_id),
    )


def reset_feed_failures(conn: sqlite3.Connection, feed_id: int) -> None:
    conn.execute(
        "UPDATE feeds SET consecutive_failures = 0, updated_at = datetime('now') WHERE id = ?",
        (feed_id,),
    )


def delete_feed(conn: sqlite3.Connection, feed_id: int) -> None:
    conn.execute(
        """
        UPDATE articles
        SET feed_url_snapshot = (SELECT url FROM feeds WHERE id = ?),
            feed_name_snapshot = (SELECT name FROM feeds WHERE id = ?)
        WHERE feed_id = ?
        """,
        (feed_id, feed_id, feed_id),
    )
    conn.execute("UPDATE articles SET feed_id = NULL WHERE feed_id = ?", (feed_id,))
    conn.execute("DELETE FROM feeds WHERE id = ?", (feed_id,))


def list_articles_published_between(
    conn: sqlite3.Connection, *, start_date: str, end_date: str
) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            """
            SELECT * FROM articles
            WHERE published_at IS NOT NULL
              AND published_at >= ?
              AND published_at <= ?
            ORDER BY published_at ASC, id ASC
            """,
            (start_date, end_date),
        ).fetchall()
    )


def list_magazines(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            "SELECT id, kind, published_at, file_path FROM magazines "
            "ORDER BY published_at DESC, id DESC"
        ).fetchall()
    )


def get_magazine_by_id(
    conn: sqlite3.Connection, magazine_id: int
) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM magazines WHERE id = ?", (magazine_id,)
    ).fetchone()


def get_category_by_name(
    conn: sqlite3.Connection, name: str
) -> sqlite3.Row | None:
    normalized = name.strip().lower()
    return conn.execute(
        "SELECT id, name FROM categories WHERE name = ?", (normalized,)
    ).fetchone()


def get_tag_by_name(
    conn: sqlite3.Connection, name: str
) -> sqlite3.Row | None:
    normalized = name.strip().lower()
    return conn.execute(
        "SELECT id, name FROM tags WHERE name = ?", (normalized,)
    ).fetchone()


def get_feed_by_id(
    conn: sqlite3.Connection, feed_id: int
) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM feeds WHERE id = ?", (feed_id,)
    ).fetchone()
