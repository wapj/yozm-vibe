import logging
import pytest

from rss_wiki.storage.db import get_connection, init_db
from rss_wiki.storage.repo import (
    upsert_feed,
    get_article_by_url_hash,
    insert_article,
    get_feed_by_url,
    record_feed_failure,
)
from rss_wiki.ingest.fetcher import FeedEntry, FetchError
from rss_wiki.ingest.dedupe import url_hash as compute_url_hash, title_hash as compute_title_hash
from rss_wiki.config import FeedConfig
from rss_wiki.pipeline.ingest import process_entry, run_daily_ingest, IngestStats


@pytest.fixture
def conn(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    c = get_connection(db_path)
    yield c
    c.close()


@pytest.fixture
def feed_id(conn):
    return upsert_feed(conn, "Test Feed", "https://test.example.com/rss")


def make_entry(
    url="https://example.com/article",
    title="Test Title",
    published_at="2026-05-05T00:00:00",
    summary="Test summary",
) -> FeedEntry:
    return FeedEntry(url=url, title=title, published_at=published_at, summary=summary)


def test_process_entry_inserts_new_article(conn, feed_id):
    entry = make_entry()
    result = process_entry(
        conn=conn,
        feed_id=feed_id,
        entry=entry,
        extractor=lambda e: "본문",
    )
    assert isinstance(result, int)
    row = get_article_by_url_hash(conn, compute_url_hash(entry.url))
    assert row is not None


def test_process_entry_returns_none_when_extract_fails(conn, feed_id):
    entry = make_entry()
    result = process_entry(
        conn=conn,
        feed_id=feed_id,
        entry=entry,
        extractor=lambda e: None,
    )
    assert result is None
    count = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    assert count == 0


def test_process_entry_logs_warning_when_extract_fails(conn, feed_id, caplog):
    entry = make_entry(url="https://example.com/specific-article")
    with caplog.at_level(logging.WARNING, logger="rss_wiki.pipeline.ingest"):
        process_entry(
            conn=conn,
            feed_id=feed_id,
            entry=entry,
            extractor=lambda e: None,
        )
    assert any(entry.url in msg for msg in caplog.messages)


def test_process_entry_skips_when_url_hash_duplicate(conn, feed_id):
    entry = make_entry()
    insert_article(
        conn,
        feed_id=feed_id,
        url=entry.url,
        url_hash=compute_url_hash(entry.url),
        title="Different title",
        title_hash=None,
        published_at=None,
        content="existing content",
        summary=None,
    )
    result = process_entry(
        conn=conn,
        feed_id=feed_id,
        entry=entry,
        extractor=lambda e: "본문",
    )
    assert result is None
    count = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    assert count == 1


def test_process_entry_skips_when_title_hash_duplicate(conn, feed_id):
    same_title = "Same Title"
    insert_article(
        conn,
        feed_id=feed_id,
        url="https://example.com/other",
        url_hash=compute_url_hash("https://example.com/other"),
        title=same_title,
        title_hash=compute_title_hash(same_title),
        published_at=None,
        content="existing content",
        summary=None,
    )
    entry = make_entry(url="https://example.com/new", title=same_title)
    result = process_entry(
        conn=conn,
        feed_id=feed_id,
        entry=entry,
        extractor=lambda e: "본문",
    )
    assert result is None
    count = conn.execute("SELECT COUNT(*) FROM articles").fetchone()[0]
    assert count == 1


def test_process_entry_inserts_when_title_is_none(conn, feed_id):
    entry = FeedEntry(
        url="https://example.com/no-title",
        title=None,
        published_at="2026-05-05T00:00:00",
        summary="Some summary",
    )
    result = process_entry(
        conn=conn,
        feed_id=feed_id,
        entry=entry,
        extractor=lambda e: "본문",
    )
    assert isinstance(result, int)
    row = get_article_by_url_hash(conn, compute_url_hash(entry.url))
    assert row is not None
    assert row["title_hash"] is None


# --- run_daily_ingest tests ---


def test_run_daily_ingest_processes_all_feeds(conn):
    feed1 = FeedConfig(name="Feed1", url="https://feed1.example.com/rss")
    feed2 = FeedConfig(name="Feed2", url="https://feed2.example.com/rss")
    entry1 = make_entry(url="https://example.com/article1", title="Title 1")
    entry2 = make_entry(url="https://example.com/article2", title="Title 2")

    def fetcher(url):
        return [entry1] if url == feed1.url else [entry2]

    stats = run_daily_ingest(
        conn=conn,
        feeds=[feed1, feed2],
        fetcher=fetcher,
        extractor=lambda e: "본문",
    )
    assert stats == IngestStats(
        feeds_total=2, feeds_success=2, feeds_failed=0,
        articles_inserted=2, articles_skipped=0,
    )


def test_run_daily_ingest_isolates_feed_fetch_error(conn):
    feed1 = FeedConfig(name="Feed1", url="https://feed1.example.com/rss")
    feed2 = FeedConfig(name="Feed2", url="https://feed2.example.com/rss")
    entry2 = make_entry(url="https://example.com/article2", title="Title 2")

    def fetcher(url):
        if url == feed1.url:
            raise FetchError("connection error")
        return [entry2]

    stats = run_daily_ingest(
        conn=conn,
        feeds=[feed1, feed2],
        fetcher=fetcher,
        extractor=lambda e: "본문",
    )
    assert stats.feeds_success == 1
    assert stats.feeds_failed == 1
    assert stats.articles_inserted == 1


def test_run_daily_ingest_records_failure_on_fetch_error(conn):
    feed = FeedConfig(name="Feed1", url="https://feed1.example.com/rss")

    def fetcher(url):
        raise FetchError("boom")

    run_daily_ingest(conn=conn, feeds=[feed], fetcher=fetcher)
    row = get_feed_by_url(conn, feed.url)
    assert row["consecutive_failures"] == 1


def test_run_daily_ingest_records_success_on_fetch_success(conn):
    feed = FeedConfig(name="Feed1", url="https://feed1.example.com/rss")
    feed_id = upsert_feed(conn, feed.name, feed.url)
    for _ in range(3):
        record_feed_failure(conn, feed_id)

    entry = make_entry()
    run_daily_ingest(
        conn=conn,
        feeds=[feed],
        fetcher=lambda url: [entry],
        extractor=lambda e: "본문",
    )
    row = get_feed_by_url(conn, feed.url)
    assert row["consecutive_failures"] == 0
    assert row["last_success_at"] is not None


def test_run_daily_ingest_counts_skipped_articles(conn):
    feed = FeedConfig(name="Feed1", url="https://feed1.example.com/rss")
    shared_url = "https://example.com/a2"
    entry1 = make_entry(url="https://example.com/a1", title="Title 1")
    entry2 = make_entry(url=shared_url, title="Title 2")
    entry3 = make_entry(url=shared_url, title="Title 3")

    def extractor(e):
        return None if e.url == "https://example.com/a1" else "본문"

    stats = run_daily_ingest(
        conn=conn,
        feeds=[feed],
        fetcher=lambda url: [entry1, entry2, entry3],
        extractor=extractor,
    )
    assert stats.articles_skipped == 2
    assert stats.articles_inserted == 1


def test_run_daily_ingest_logs_warning_on_feed_failure(conn, caplog):
    feed = FeedConfig(name="Feed1", url="https://feed1.example.com/rss")

    def fetcher(url):
        raise FetchError("boom")

    with caplog.at_level(logging.WARNING, logger="rss_wiki.pipeline.ingest"):
        run_daily_ingest(conn=conn, feeds=[feed], fetcher=fetcher)
    assert any(feed.url in msg for msg in caplog.messages)
