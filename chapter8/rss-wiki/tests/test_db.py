"""db.get_connection / init_schema (feeds, categories) 검증."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from rss_wiki import db


@pytest.fixture
def conn(tmp_path: Path):
    connection = db.get_connection(tmp_path / "test.db")
    db.init_schema(connection)
    try:
        yield connection
    finally:
        connection.close()


def test_get_connection_returns_sqlite_row_connection(tmp_path: Path):
    connection = db.get_connection(tmp_path / "x.db")
    try:
        assert isinstance(connection, sqlite3.Connection)
        assert connection.row_factory is sqlite3.Row
        fk = connection.execute("PRAGMA foreign_keys").fetchone()[0]
        assert fk == 1
    finally:
        connection.close()


def test_get_connection_creates_parent_directory(tmp_path: Path):
    nested = tmp_path / "a" / "b" / "c.db"
    connection = db.get_connection(nested)
    try:
        assert nested.parent.is_dir()
    finally:
        connection.close()


def test_get_connection_uses_default_db_path(monkeypatch, tmp_path: Path):
    target = tmp_path / "default.db"
    monkeypatch.setattr(db.config, "DB_PATH", target)
    connection = db.get_connection()
    try:
        connection.execute("CREATE TABLE smoke (a INTEGER)")
        connection.commit()
    finally:
        connection.close()
    assert target.exists()


def test_init_schema_creates_feeds_with_expected_columns(conn: sqlite3.Connection):
    table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='feeds'"
    ).fetchone()
    assert table is not None
    cols = {row["name"] for row in conn.execute("PRAGMA table_info(feeds)")}
    assert cols == {
        "id",
        "url",
        "title",
        "is_active",
        "last_fetched_at",
        "consecutive_failures",
        "created_at",
    }


def test_init_schema_creates_categories_with_expected_columns(conn: sqlite3.Connection):
    table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='categories'"
    ).fetchone()
    assert table is not None
    cols = {row["name"] for row in conn.execute("PRAGMA table_info(categories)")}
    assert cols == {
        "id",
        "name",
        "parent_id",
        "description",
        "is_user_edited",
        "merged_into_id",
        "created_at",
    }


def test_categories_parent_index_exists(conn: sqlite3.Connection):
    idx = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_categories_parent'"
    ).fetchone()
    assert idx is not None


def test_init_schema_is_idempotent(conn: sqlite3.Connection):
    db.init_schema(conn)
    db.init_schema(conn)
    table_count = conn.execute(
        "SELECT count(*) FROM sqlite_master "
        "WHERE type='table' AND name IN ('feeds', 'categories')"
    ).fetchone()[0]
    assert table_count == 2


def test_feeds_url_unique_constraint(conn: sqlite3.Connection):
    conn.execute("INSERT INTO feeds (url) VALUES (?)", ("https://example.com/rss",))
    conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO feeds (url) VALUES (?)", ("https://example.com/rss",))


def test_feeds_default_values(conn: sqlite3.Connection):
    conn.execute("INSERT INTO feeds (url) VALUES (?)", ("https://example.com/rss",))
    conn.commit()
    row = conn.execute(
        "SELECT is_active, consecutive_failures, created_at FROM feeds"
    ).fetchone()
    assert row["is_active"] == 1
    assert row["consecutive_failures"] == 0
    assert row["created_at"] is not None


def test_categories_name_unique_constraint(conn: sqlite3.Connection):
    conn.execute("INSERT INTO categories (name) VALUES ('AI')")
    conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO categories (name) VALUES ('AI')")


def test_categories_parent_id_references_self(conn: sqlite3.Connection):
    cur = conn.execute("INSERT INTO categories (name) VALUES ('Root')")
    root_id = cur.lastrowid
    conn.execute(
        "INSERT INTO categories (name, parent_id) VALUES ('Child', ?)", (root_id,)
    )
    conn.commit()
    child = conn.execute(
        "SELECT parent_id FROM categories WHERE name='Child'"
    ).fetchone()
    assert child["parent_id"] == root_id


def test_categories_parent_id_set_null_on_delete(conn: sqlite3.Connection):
    cur = conn.execute("INSERT INTO categories (name) VALUES ('Root')")
    root_id = cur.lastrowid
    conn.execute(
        "INSERT INTO categories (name, parent_id) VALUES ('Child', ?)", (root_id,)
    )
    conn.commit()
    conn.execute("DELETE FROM categories WHERE id=?", (root_id,))
    conn.commit()
    child = conn.execute(
        "SELECT parent_id FROM categories WHERE name='Child'"
    ).fetchone()
    assert child["parent_id"] is None


def _insert_feed(conn: sqlite3.Connection, url: str = "https://example.com/rss") -> int:
    cur = conn.execute("INSERT INTO feeds (url) VALUES (?)", (url,))
    conn.commit()
    return cur.lastrowid


def test_init_schema_creates_articles_with_expected_columns(conn: sqlite3.Connection):
    table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='articles'"
    ).fetchone()
    assert table is not None
    cols = {row["name"] for row in conn.execute("PRAGMA table_info(articles)")}
    assert cols == {
        "id",
        "feed_id",
        "url",
        "title",
        "author",
        "published_at",
        "raw_summary",
        "extracted_content",
        "llm_summary",
        "primary_category_id",
        "language",
        "status",
        "fetched_at",
    }


def test_articles_indexes_exist(conn: sqlite3.Connection):
    names = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )
    }
    assert {"idx_articles_feed", "idx_articles_cat", "idx_articles_pub"} <= names


def test_articles_url_unique_constraint(conn: sqlite3.Connection):
    feed_id = _insert_feed(conn)
    conn.execute(
        "INSERT INTO articles (feed_id, url, title) VALUES (?, ?, ?)",
        (feed_id, "https://example.com/a", "A"),
    )
    conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO articles (feed_id, url, title) VALUES (?, ?, ?)",
            (feed_id, "https://example.com/a", "A-dup"),
        )


def test_articles_default_status_and_fetched_at(conn: sqlite3.Connection):
    feed_id = _insert_feed(conn)
    conn.execute(
        "INSERT INTO articles (feed_id, url, title) VALUES (?, ?, ?)",
        (feed_id, "https://example.com/a", "A"),
    )
    conn.commit()
    row = conn.execute("SELECT status, fetched_at FROM articles").fetchone()
    assert row["status"] == "ok"
    assert row["fetched_at"] is not None


def test_articles_feed_cascade_delete(conn: sqlite3.Connection):
    feed_id = _insert_feed(conn)
    conn.execute(
        "INSERT INTO articles (feed_id, url, title) VALUES (?, ?, ?)",
        (feed_id, "https://example.com/a", "A"),
    )
    conn.commit()
    conn.execute("DELETE FROM feeds WHERE id=?", (feed_id,))
    conn.commit()
    count = conn.execute("SELECT count(*) FROM articles").fetchone()[0]
    assert count == 0


def test_articles_category_set_null_on_delete(conn: sqlite3.Connection):
    feed_id = _insert_feed(conn)
    cur = conn.execute("INSERT INTO categories (name) VALUES ('AI')")
    cat_id = cur.lastrowid
    conn.execute(
        "INSERT INTO articles (feed_id, url, title, primary_category_id) "
        "VALUES (?, ?, ?, ?)",
        (feed_id, "https://example.com/a", "A", cat_id),
    )
    conn.commit()
    conn.execute("DELETE FROM categories WHERE id=?", (cat_id,))
    conn.commit()
    row = conn.execute(
        "SELECT primary_category_id FROM articles WHERE url='https://example.com/a'"
    ).fetchone()
    assert row["primary_category_id"] is None


def test_articles_fts_virtual_table_exists(conn: sqlite3.Connection):
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='articles_fts'"
    ).fetchone()
    assert row is not None


def test_articles_fts_insert_trigger_indexes_new_row(conn: sqlite3.Connection):
    feed_id = _insert_feed(conn)
    conn.execute(
        "INSERT INTO articles (feed_id, url, title, llm_summary, extracted_content) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            feed_id,
            "https://example.com/a",
            "LLM 에이전트 소개",
            "에이전트에 대한 짧은 요약",
            "본문에는 agent 라는 단어가 포함되어 있습니다",
        ),
    )
    conn.commit()
    hits = conn.execute(
        "SELECT rowid FROM articles_fts WHERE articles_fts MATCH ?",
        ("에이전트",),
    ).fetchall()
    assert len(hits) == 1


def test_articles_fts_update_trigger_reindexes(conn: sqlite3.Connection):
    feed_id = _insert_feed(conn)
    conn.execute(
        "INSERT INTO articles (feed_id, url, title) VALUES (?, ?, ?)",
        (feed_id, "https://example.com/a", "원래 제목"),
    )
    conn.commit()
    conn.execute(
        "UPDATE articles SET title=? WHERE url=?",
        ("수정된 제목", "https://example.com/a"),
    )
    conn.commit()
    old_hits = conn.execute(
        "SELECT rowid FROM articles_fts WHERE articles_fts MATCH ?", ("원래",)
    ).fetchall()
    new_hits = conn.execute(
        "SELECT rowid FROM articles_fts WHERE articles_fts MATCH ?", ("수정된",)
    ).fetchall()
    assert old_hits == []
    assert len(new_hits) == 1


def test_init_schema_creates_wiki_pages_with_expected_columns(conn: sqlite3.Connection):
    table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='wiki_pages'"
    ).fetchone()
    assert table is not None
    cols = {row["name"] for row in conn.execute("PRAGMA table_info(wiki_pages)")}
    assert cols == {
        "id",
        "category_id",
        "content_markdown",
        "last_rebuilt_at",
        "articles_count_at_rebuild",
        "last_seen_at",
        "has_unread_updates",
    }


def test_wiki_pages_category_id_unique(conn: sqlite3.Connection):
    cur = conn.execute("INSERT INTO categories (name) VALUES ('AI')")
    cat_id = cur.lastrowid
    conn.execute("INSERT INTO wiki_pages (category_id) VALUES (?)", (cat_id,))
    conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO wiki_pages (category_id) VALUES (?)", (cat_id,))


def test_wiki_pages_defaults(conn: sqlite3.Connection):
    cur = conn.execute("INSERT INTO categories (name) VALUES ('AI')")
    cat_id = cur.lastrowid
    conn.execute("INSERT INTO wiki_pages (category_id) VALUES (?)", (cat_id,))
    conn.commit()
    row = conn.execute(
        "SELECT content_markdown, articles_count_at_rebuild, has_unread_updates "
        "FROM wiki_pages WHERE category_id=?",
        (cat_id,),
    ).fetchone()
    assert row["content_markdown"] == ""
    assert row["articles_count_at_rebuild"] == 0
    assert row["has_unread_updates"] == 0


def test_wiki_pages_cascade_delete_on_category(conn: sqlite3.Connection):
    cur = conn.execute("INSERT INTO categories (name) VALUES ('AI')")
    cat_id = cur.lastrowid
    conn.execute("INSERT INTO wiki_pages (category_id) VALUES (?)", (cat_id,))
    conn.commit()
    conn.execute("DELETE FROM categories WHERE id=?", (cat_id,))
    conn.commit()
    count = conn.execute("SELECT count(*) FROM wiki_pages").fetchone()[0]
    assert count == 0


def test_init_schema_creates_job_logs_with_expected_columns(conn: sqlite3.Connection):
    table = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='job_logs'"
    ).fetchone()
    assert table is not None
    cols = {row["name"] for row in conn.execute("PRAGMA table_info(job_logs)")}
    assert cols == {
        "id",
        "job_type",
        "target_ref",
        "status",
        "error_message",
        "attempt_count",
        "started_at",
        "finished_at",
    }


def test_job_logs_started_index_exists(conn: sqlite3.Connection):
    idx = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_joblogs_started'"
    ).fetchone()
    assert idx is not None


def test_job_logs_default_attempt_count(conn: sqlite3.Connection):
    conn.execute(
        "INSERT INTO job_logs (job_type, status, started_at) VALUES (?, ?, ?)",
        ("fetch_feed", "ok", "2026-04-25T00:00:00Z"),
    )
    conn.commit()
    row = conn.execute("SELECT attempt_count FROM job_logs").fetchone()
    assert row["attempt_count"] == 1


def test_job_logs_requires_job_type_and_status(conn: sqlite3.Connection):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO job_logs (status, started_at) VALUES (?, ?)",
            ("ok", "2026-04-25T00:00:00Z"),
        )
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO job_logs (job_type, started_at) VALUES (?, ?)",
            ("fetch_feed", "2026-04-25T00:00:00Z"),
        )
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO job_logs (job_type, status) VALUES (?, ?)",
            ("fetch_feed", "ok"),
        )


def test_articles_fts_delete_trigger_removes_row(conn: sqlite3.Connection):
    feed_id = _insert_feed(conn)
    conn.execute(
        "INSERT INTO articles (feed_id, url, title) VALUES (?, ?, ?)",
        (feed_id, "https://example.com/a", "삭제대상"),
    )
    conn.commit()
    conn.execute("DELETE FROM articles WHERE url='https://example.com/a'")
    conn.commit()
    hits = conn.execute(
        "SELECT rowid FROM articles_fts WHERE articles_fts MATCH ?", ("삭제대상",)
    ).fetchall()
    assert hits == []
