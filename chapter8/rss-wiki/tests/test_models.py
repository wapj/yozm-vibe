"""models.py — Pydantic 모델이 PRD §6 스키마와 맞는지 검증."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from pydantic import ValidationError

from rss_wiki import db
from rss_wiki.models import Article, Category, Feed, JobLog, WikiPage


@pytest.fixture
def conn(tmp_path: Path):
    connection = db.get_connection(tmp_path / "models.db")
    db.init_schema(connection)
    try:
        yield connection
    finally:
        connection.close()


# --- Feed ----------------------------------------------------------------


def test_feed_defaults_match_schema_defaults():
    feed = Feed(id=1, url="https://example.com/rss", created_at="2026-04-25 00:00:00")
    assert feed.title is None
    assert feed.is_active is True
    assert feed.last_fetched_at is None
    assert feed.consecutive_failures == 0


def test_feed_builds_from_sqlite_row_with_int_bool(conn: sqlite3.Connection):
    conn.execute(
        "INSERT INTO feeds (url, title, is_active) VALUES (?, ?, 0)",
        ("https://example.com/a", "A"),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM feeds WHERE url='https://example.com/a'").fetchone()
    feed = Feed.model_validate(dict(row))
    assert feed.url == "https://example.com/a"
    assert feed.title == "A"
    assert feed.is_active is False
    assert feed.consecutive_failures == 0
    assert feed.created_at  # DEFAULT datetime('now')


# --- Category ------------------------------------------------------------


def test_category_defaults():
    cat = Category(id=3, name="AI", created_at="2026-04-25 00:00:00")
    assert cat.parent_id is None
    assert cat.description is None
    assert cat.is_user_edited is False
    assert cat.merged_into_id is None


def test_category_from_row(conn: sqlite3.Connection):
    conn.execute(
        "INSERT INTO categories (name, description, is_user_edited) VALUES (?, ?, 1)",
        ("AI", "인공지능"),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM categories WHERE name='AI'").fetchone()
    cat = Category.model_validate(dict(row))
    assert cat.name == "AI"
    assert cat.description == "인공지능"
    assert cat.is_user_edited is True


# --- Article -------------------------------------------------------------


def test_article_defaults_and_status_literal():
    art = Article(
        id=1,
        feed_id=2,
        url="https://example.com/p/1",
        title="제목",
        fetched_at="2026-04-25 00:00:00",
    )
    assert art.status == "ok"
    assert art.author is None
    assert art.primary_category_id is None


def test_article_rejects_invalid_status():
    with pytest.raises(ValidationError):
        Article(
            id=1,
            feed_id=2,
            url="https://example.com/p/1",
            title="제목",
            status="pending",  # type: ignore[arg-type]
            fetched_at="2026-04-25 00:00:00",
        )


def test_article_from_row_roundtrip(conn: sqlite3.Connection):
    conn.execute("INSERT INTO feeds (url) VALUES ('https://f.example/rss')")
    feed_id = conn.execute("SELECT id FROM feeds").fetchone()["id"]
    conn.execute(
        """
        INSERT INTO articles (feed_id, url, title, status, language)
        VALUES (?, ?, ?, 'failed', 'ko')
        """,
        (feed_id, "https://example.com/x", "테스트"),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM articles").fetchone()
    art = Article.model_validate(dict(row))
    assert art.feed_id == feed_id
    assert art.title == "테스트"
    assert art.status == "failed"
    assert art.language == "ko"


# --- WikiPage ------------------------------------------------------------


def test_wiki_page_defaults():
    page = WikiPage(id=1, category_id=2)
    assert page.content_markdown == ""
    assert page.articles_count_at_rebuild == 0
    assert page.has_unread_updates is False
    assert page.last_rebuilt_at is None
    assert page.last_seen_at is None


def test_wiki_page_from_row(conn: sqlite3.Connection):
    conn.execute("INSERT INTO categories (name) VALUES ('AI')")
    cat_id = conn.execute("SELECT id FROM categories").fetchone()["id"]
    conn.execute(
        """
        INSERT INTO wiki_pages
          (category_id, content_markdown, articles_count_at_rebuild, has_unread_updates)
        VALUES (?, ?, ?, 1)
        """,
        (cat_id, "# AI\n", 5),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM wiki_pages").fetchone()
    page = WikiPage.model_validate(dict(row))
    assert page.category_id == cat_id
    assert page.content_markdown == "# AI\n"
    assert page.articles_count_at_rebuild == 5
    assert page.has_unread_updates is True


# --- JobLog --------------------------------------------------------------


def test_job_log_defaults_and_literal():
    log = JobLog(
        id=1,
        job_type="summarize",
        status="ok",
        started_at="2026-04-25 00:00:00",
    )
    assert log.attempt_count == 1
    assert log.error_message is None
    assert log.target_ref is None
    assert log.finished_at is None


def test_job_log_rejects_invalid_job_type():
    with pytest.raises(ValidationError):
        JobLog(
            id=1,
            job_type="bogus",  # type: ignore[arg-type]
            status="ok",
            started_at="2026-04-25 00:00:00",
        )


def test_job_log_rejects_invalid_status():
    with pytest.raises(ValidationError):
        JobLog(
            id=1,
            job_type="extract",
            status="retry",  # type: ignore[arg-type]
            started_at="2026-04-25 00:00:00",
        )


def test_job_log_attempt_count_must_be_positive():
    with pytest.raises(ValidationError):
        JobLog(
            id=1,
            job_type="extract",
            status="ok",
            attempt_count=0,
            started_at="2026-04-25 00:00:00",
        )


def test_job_log_from_row(conn: sqlite3.Connection):
    conn.execute(
        """
        INSERT INTO job_logs (job_type, target_ref, status, started_at, finished_at, attempt_count)
        VALUES ('fetch_feed', 'feed:1', 'failed', '2026-04-25 00:00:00', '2026-04-25 00:00:01', 3)
        """
    )
    conn.commit()
    row = conn.execute("SELECT * FROM job_logs").fetchone()
    log = JobLog.model_validate(dict(row))
    assert log.job_type == "fetch_feed"
    assert log.target_ref == "feed:1"
    assert log.status == "failed"
    assert log.attempt_count == 3
    assert log.finished_at == "2026-04-25 00:00:01"
