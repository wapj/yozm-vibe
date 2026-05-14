from __future__ import annotations
import logging
import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Callable

from rss_wiki.config import FeedConfig
from rss_wiki.ingest.fetcher import FeedEntry, FetchError, fetch_feed
from rss_wiki.ingest.extractor import extract_body
from rss_wiki.ingest.dedupe import url_hash, title_hash
from rss_wiki.storage.repo import (
    get_article_by_url_hash,
    get_article_by_title_hash,
    insert_article,
    record_feed_failure,
    record_feed_success,
    upsert_feed,
)


def process_entry(
    *,
    conn: sqlite3.Connection,
    feed_id: int,
    entry: FeedEntry,
    extractor: Callable[[FeedEntry], str | None] | None = None,
    logger: logging.Logger | None = None,
) -> int | None:
    _logger = logger or logging.getLogger(__name__)
    _extractor = extractor if extractor is not None else extract_body

    body = _extractor(entry)
    if body is None:
        _logger.warning("extract failed: url=%s", entry.url)
        return None

    uh = url_hash(entry.url)
    if get_article_by_url_hash(conn, uh) is not None:
        return None

    th: str | None = None
    if entry.title is not None:
        th = title_hash(entry.title)
        if get_article_by_title_hash(conn, th) is not None:
            return None

    return insert_article(
        conn,
        feed_id=feed_id,
        url=entry.url,
        url_hash=uh,
        title=entry.title,
        title_hash=th,
        published_at=entry.published_at,
        content=body,
        summary=entry.summary,
    )


@dataclass(frozen=True)
class IngestStats:
    feeds_total: int
    feeds_success: int
    feeds_failed: int
    articles_inserted: int
    articles_skipped: int


def run_daily_ingest(
    *,
    conn: sqlite3.Connection,
    feeds: Sequence[FeedConfig],
    fetcher: Callable[[str], list[FeedEntry]] | None = None,
    extractor: Callable[[FeedEntry], str | None] | None = None,
    logger: logging.Logger | None = None,
) -> IngestStats:
    _logger = logger or logging.getLogger(__name__)
    _fetcher = fetcher if fetcher is not None else fetch_feed

    feeds_success = 0
    feeds_failed = 0
    articles_inserted = 0
    articles_skipped = 0

    for cfg in feeds:
        feed_id = upsert_feed(conn, cfg.name, cfg.url)
        try:
            entries = _fetcher(cfg.url)
        except FetchError as exc:
            _logger.warning("fetch failed: url=%s reason=%s", cfg.url, exc)
            record_feed_failure(conn, feed_id)
            feeds_failed += 1
            continue

        record_feed_success(conn, feed_id)
        feeds_success += 1

        for entry in entries:
            result = process_entry(
                conn=conn,
                feed_id=feed_id,
                entry=entry,
                extractor=extractor,
                logger=_logger,
            )
            if result is None:
                articles_skipped += 1
            else:
                articles_inserted += 1

    return IngestStats(
        feeds_total=len(feeds),
        feeds_success=feeds_success,
        feeds_failed=feeds_failed,
        articles_inserted=articles_inserted,
        articles_skipped=articles_skipped,
    )
