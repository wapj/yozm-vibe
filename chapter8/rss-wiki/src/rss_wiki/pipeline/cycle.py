"""전체 수집 사이클 (PRD §7.1).

- 활성 피드 목록을 fetch_feeds 로 병렬 수집 → 피드별 FetchError 는 job_logs 기록
- 각 피드의 엔트리를 filter_new_entries 로 신규만 선별 (articles.url UNIQUE + 배치 내 중복 제거)
- 각 신규 엔트리에 대해 extractor → summarizer 를 순차 호출 (LLM 직렬화)
- ok 상태로 저장된 글의 카테고리를 affected 로 수집
- 사이클 끝에 카테고리당 1회만 rebuild_wiki_page 를 호출

외부 의존(subprocess, network) 은 주입 가능한 fetch_feeds/extract/summarize/rebuild 로
받아 테스트에서는 fake 로 대체한다.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Protocol, Sequence

from rss_wiki.pipeline.extractor import ExtractionResult, extract_article
from rss_wiki.pipeline.fetcher import (
    FeedEntry,
    FetchError,
    FetchResult,
    fetch_feeds as _default_fetch_feeds,
    filter_new_entries,
)
from rss_wiki.pipeline.rebuilder import RebuildOutcome, rebuild_wiki_page
from rss_wiki.pipeline.summarizer import SummarizeOutcome, summarize_article


FetchFeedsFn = Callable[
    [Sequence[str]], Awaitable[list[FetchResult | FetchError]]
]


class ExtractFn(Protocol):
    async def __call__(
        self, url: str, *, raw_summary: str | None = None
    ) -> ExtractionResult: ...


class SummarizeFn(Protocol):
    async def __call__(
        self,
        conn: sqlite3.Connection,
        *,
        feed_id: int,
        entry: FeedEntry,
        extraction: ExtractionResult,
        detected_language: str = "",
    ) -> SummarizeOutcome: ...


class RebuildFn(Protocol):
    async def __call__(
        self,
        conn: sqlite3.Connection,
        *,
        category_id: int,
        new_article_ids: Sequence[int] | None = None,
    ) -> RebuildOutcome: ...


@dataclass(slots=True)
class CycleResult:
    feeds_attempted: int = 0
    feeds_succeeded: int = 0
    feeds_failed: int = 0
    new_articles: int = 0
    ok_articles: int = 0
    failed_articles: int = 0
    affected_category_ids: list[int] = field(default_factory=list)
    rebuilt_category_ids: list[int] = field(default_factory=list)
    rebuild_failed_category_ids: list[int] = field(default_factory=list)


async def run_cycle(
    conn: sqlite3.Connection,
    *,
    fetch_feeds: FetchFeedsFn = _default_fetch_feeds,
    extract: ExtractFn = extract_article,
    summarize: SummarizeFn = summarize_article,
    rebuild: RebuildFn = rebuild_wiki_page,
) -> CycleResult:
    """한 사이클 실행. 외부 의존은 모두 키워드 인자로 주입 가능."""
    result = CycleResult()

    active = _active_feeds(conn)
    result.feeds_attempted = len(active)
    if not active:
        return result

    urls = [url for _, url in active]
    url_to_id = {url: fid for fid, url in active}

    fetch_outcomes = await fetch_feeds(urls)

    existing_urls = _existing_article_urls(conn)
    entries_with_feed: list[tuple[int, FeedEntry]] = []

    for outcome in fetch_outcomes:
        if isinstance(outcome, FetchError):
            result.feeds_failed += 1
            fid = url_to_id.get(outcome.url)
            if fid is not None:
                _mark_feed_failed(conn, fid)
                _log_job(
                    conn,
                    job_type="fetch_feed",
                    target_ref=fid,
                    status="failed",
                    error_message=outcome.error,
                )
            continue

        result.feeds_succeeded += 1
        fid = url_to_id.get(outcome.url)
        if fid is None:
            continue
        _mark_feed_fetched(conn, fid, title=outcome.title)

        new_entries = filter_new_entries(outcome.entries, existing_urls)
        # 다음 피드에서 같은 URL 이 또 등장하면 중복 처리되지 않도록 즉시 기존 집합에 추가.
        existing_urls.update(e.url for e in new_entries)
        for entry in new_entries:
            entries_with_feed.append((fid, entry))

    result.new_articles = len(entries_with_feed)

    per_category_new_articles: dict[int, list[int]] = {}

    for feed_id, entry in entries_with_feed:
        extraction = await extract(entry.url, raw_summary=entry.raw_summary)
        outcome = await summarize(
            conn,
            feed_id=feed_id,
            entry=entry,
            extraction=extraction,
        )
        if outcome.status == "ok":
            result.ok_articles += 1
            if outcome.category_id is not None:
                per_category_new_articles.setdefault(
                    outcome.category_id, []
                ).append(outcome.article_id)
        else:
            result.failed_articles += 1
            _log_job(
                conn,
                job_type="summarize",
                target_ref=outcome.article_id,
                status="failed",
                error_message=outcome.error,
            )

    result.affected_category_ids = sorted(per_category_new_articles.keys())

    for category_id in result.affected_category_ids:
        article_ids = per_category_new_articles[category_id]
        rebuild_outcome = await rebuild(
            conn,
            category_id=category_id,
            new_article_ids=article_ids,
        )
        if rebuild_outcome.status == "ok":
            result.rebuilt_category_ids.append(category_id)
        else:
            result.rebuild_failed_category_ids.append(category_id)
            _log_job(
                conn,
                job_type="rebuild_wiki",
                target_ref=category_id,
                status=rebuild_outcome.status,
                error_message=rebuild_outcome.error,
            )

    return result


def _active_feeds(conn: sqlite3.Connection) -> list[tuple[int, str]]:
    rows = conn.execute(
        "SELECT id, url FROM feeds WHERE is_active = 1 ORDER BY id"
    ).fetchall()
    return [(int(r["id"]), str(r["url"])) for r in rows]


def _existing_article_urls(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT url FROM articles").fetchall()
    return {str(r["url"]) for r in rows}


def _mark_feed_fetched(
    conn: sqlite3.Connection, feed_id: int, *, title: str | None
) -> None:
    if title:
        conn.execute(
            """
            UPDATE feeds
               SET last_fetched_at = datetime('now'),
                   consecutive_failures = 0,
                   title = COALESCE(title, ?)
             WHERE id = ?
            """,
            (title, feed_id),
        )
    else:
        conn.execute(
            """
            UPDATE feeds
               SET last_fetched_at = datetime('now'),
                   consecutive_failures = 0
             WHERE id = ?
            """,
            (feed_id,),
        )
    conn.commit()


def _mark_feed_failed(conn: sqlite3.Connection, feed_id: int) -> None:
    conn.execute(
        "UPDATE feeds SET consecutive_failures = consecutive_failures + 1 "
        "WHERE id = ?",
        (feed_id,),
    )
    conn.commit()


def _log_job(
    conn: sqlite3.Connection,
    *,
    job_type: str,
    target_ref: Any,
    status: str,
    error_message: str | None,
    attempt_count: int = 1,
) -> None:
    conn.execute(
        """
        INSERT INTO job_logs (
            job_type, target_ref, status, error_message, attempt_count,
            started_at, finished_at
        ) VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """,
        (
            job_type,
            None if target_ref is None else str(target_ref),
            status,
            error_message,
            attempt_count,
        ),
    )
    conn.commit()
