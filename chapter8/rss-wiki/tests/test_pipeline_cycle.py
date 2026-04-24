"""pipeline.cycle — 전체 수집 사이클 (PRD §7.1)."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Sequence

import pytest

from rss_wiki import db
from rss_wiki.pipeline import cycle
from rss_wiki.pipeline.extractor import ExtractionResult
from rss_wiki.pipeline.fetcher import FeedEntry, FetchError, FetchResult
from rss_wiki.pipeline.rebuilder import RebuildOutcome
from rss_wiki.pipeline.summarizer import SummarizeOutcome


@pytest.fixture
def conn(tmp_path: Path):
    connection = db.get_connection(tmp_path / "test.db")
    db.init_schema(connection)
    try:
        yield connection
    finally:
        connection.close()


def _insert_feed(
    conn: sqlite3.Connection,
    url: str,
    *,
    is_active: int = 1,
    title: str | None = None,
) -> int:
    cursor = conn.execute(
        "INSERT INTO feeds (url, title, is_active) VALUES (?, ?, ?)",
        (url, title, is_active),
    )
    conn.commit()
    return int(cursor.lastrowid)


def _entry(url: str, title: str = "t") -> FeedEntry:
    return FeedEntry(
        url=url,
        title=title,
        author=None,
        published_at="2026-04-25T00:00:00Z",
        raw_summary=f"raw:{title}",
    )


# -----------------------------------------------------------------------------
# Fake helpers
# -----------------------------------------------------------------------------


def _fake_fetch_feeds(
    outcomes_by_url: dict[str, FetchResult | FetchError],
):
    async def fn(urls: Sequence[str]) -> list[FetchResult | FetchError]:
        fn.calls.append(list(urls))
        return [outcomes_by_url[u] for u in urls]

    fn.calls = []  # type: ignore[attr-defined]
    return fn


def _fake_extract(text: str = "본문", source: str = "trafilatura"):
    async def fn(url: str, *, raw_summary: str | None = None) -> ExtractionResult:
        fn.calls.append({"url": url, "raw_summary": raw_summary})
        return ExtractionResult(text=text, source=source)  # type: ignore[arg-type]

    fn.calls = []  # type: ignore[attr-defined]
    return fn


def _fake_summarize(
    *,
    category_by_url: dict[str, str] | None = None,
    fail_urls: set[str] | None = None,
):
    """Summarize fake: URL → 카테고리 이름을 지정해 실제 DB INSERT 를 수행한다.

    fail_urls 에 속한 URL 은 status='failed' 로 저장한다.
    """
    category_by_url = category_by_url or {}
    fail_urls = fail_urls or set()

    async def fn(
        conn: sqlite3.Connection,
        *,
        feed_id: int,
        entry: FeedEntry,
        extraction: ExtractionResult,
        detected_language: str = "",
    ) -> SummarizeOutcome:
        fn.calls.append(entry.url)
        if entry.url in fail_urls:
            cursor = conn.execute(
                """
                INSERT INTO articles (feed_id, url, title, status)
                VALUES (?, ?, ?, 'failed')
                """,
                (feed_id, entry.url, entry.title),
            )
            conn.commit()
            return SummarizeOutcome(
                article_id=int(cursor.lastrowid),
                status="failed",
                category_id=None,
                error="boom",
            )

        name = category_by_url.get(entry.url, "기본")
        row = conn.execute(
            "SELECT id FROM categories WHERE name=?", (name,)
        ).fetchone()
        if row is None:
            cid = int(
                conn.execute(
                    "INSERT INTO categories (name) VALUES (?)", (name,)
                ).lastrowid
            )
        else:
            cid = int(row["id"])

        cursor = conn.execute(
            """
            INSERT INTO articles (
                feed_id, url, title, llm_summary, primary_category_id, status
            ) VALUES (?, ?, ?, ?, ?, 'ok')
            """,
            (feed_id, entry.url, entry.title, "요약", cid),
        )
        conn.commit()
        return SummarizeOutcome(
            article_id=int(cursor.lastrowid),
            status="ok",
            category_id=cid,
        )

    fn.calls = []  # type: ignore[attr-defined]
    return fn


def _fake_rebuild(*, fail_category_ids: set[int] | None = None):
    fail_category_ids = fail_category_ids or set()

    async def fn(
        conn: sqlite3.Connection,
        *,
        category_id: int,
        new_article_ids: Sequence[int] | None = None,
    ) -> RebuildOutcome:
        fn.calls.append(
            {
                "category_id": category_id,
                "new_article_ids": list(new_article_ids or []),
            }
        )
        if category_id in fail_category_ids:
            return RebuildOutcome(
                category_id=category_id,
                status="failed",
                content_markdown=None,
                is_initial=False,
                used_existing_context_size=0,
                articles_count=0,
                error="llm down",
            )
        return RebuildOutcome(
            category_id=category_id,
            status="ok",
            content_markdown="# md",
            is_initial=True,
            used_existing_context_size=0,
            articles_count=len(new_article_ids or []),
        )

    fn.calls = []  # type: ignore[attr-defined]
    return fn


# -----------------------------------------------------------------------------
# 빈 상태 / 비활성 필터링
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_cycle_returns_zero_when_no_active_feeds(conn: sqlite3.Connection):
    fetch_fn = _fake_fetch_feeds({})
    extract_fn = _fake_extract()
    summarize_fn = _fake_summarize()
    rebuild_fn = _fake_rebuild()

    result = await cycle.run_cycle(
        conn,
        fetch_feeds=fetch_fn,
        extract=extract_fn,
        summarize=summarize_fn,
        rebuild=rebuild_fn,
    )

    assert result.feeds_attempted == 0
    assert result.new_articles == 0
    assert fetch_fn.calls == []


@pytest.mark.asyncio
async def test_run_cycle_skips_inactive_feeds(conn: sqlite3.Connection):
    _insert_feed(conn, "https://a/rss", is_active=0)
    active_id = _insert_feed(conn, "https://b/rss", is_active=1)

    fetch_fn = _fake_fetch_feeds(
        {
            "https://b/rss": FetchResult(
                url="https://b/rss",
                title="B",
                entries=[_entry("https://b/a1", "A1")],
            ),
        }
    )
    extract_fn = _fake_extract()
    summarize_fn = _fake_summarize(category_by_url={"https://b/a1": "AI"})
    rebuild_fn = _fake_rebuild()

    result = await cycle.run_cycle(
        conn,
        fetch_feeds=fetch_fn,
        extract=extract_fn,
        summarize=summarize_fn,
        rebuild=rebuild_fn,
    )

    assert result.feeds_attempted == 1
    assert fetch_fn.calls == [["https://b/rss"]]
    row = conn.execute(
        "SELECT feed_id FROM articles WHERE url=?", ("https://b/a1",)
    ).fetchone()
    assert row["feed_id"] == active_id


# -----------------------------------------------------------------------------
# 행복 경로
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_cycle_happy_path_fetches_summarizes_and_rebuilds(
    conn: sqlite3.Connection,
):
    feed_id = _insert_feed(conn, "https://a/rss")

    fetch_fn = _fake_fetch_feeds(
        {
            "https://a/rss": FetchResult(
                url="https://a/rss",
                title="A",
                entries=[
                    _entry("https://a/1", "첫 번째"),
                    _entry("https://a/2", "두 번째"),
                ],
            )
        }
    )
    extract_fn = _fake_extract()
    summarize_fn = _fake_summarize(
        category_by_url={
            "https://a/1": "AI",
            "https://a/2": "AI",
        }
    )
    rebuild_fn = _fake_rebuild()

    result = await cycle.run_cycle(
        conn,
        fetch_feeds=fetch_fn,
        extract=extract_fn,
        summarize=summarize_fn,
        rebuild=rebuild_fn,
    )

    assert result.feeds_succeeded == 1
    assert result.new_articles == 2
    assert result.ok_articles == 2
    assert result.failed_articles == 0
    # 같은 카테고리는 한 번만 rebuild.
    assert len(rebuild_fn.calls) == 1
    assert len(result.rebuilt_category_ids) == 1
    assert result.rebuild_failed_category_ids == []
    # extract 는 새 엔트리 수만큼 호출.
    assert len(extract_fn.calls) == 2
    # last_fetched_at 기록.
    fetched = conn.execute(
        "SELECT last_fetched_at, consecutive_failures FROM feeds WHERE id=?",
        (feed_id,),
    ).fetchone()
    assert fetched["last_fetched_at"] is not None
    assert fetched["consecutive_failures"] == 0


@pytest.mark.asyncio
async def test_run_cycle_rebuilds_each_affected_category_once(
    conn: sqlite3.Connection,
):
    _insert_feed(conn, "https://a/rss")

    fetch_fn = _fake_fetch_feeds(
        {
            "https://a/rss": FetchResult(
                url="https://a/rss",
                title="A",
                entries=[
                    _entry("https://a/1", "x1"),
                    _entry("https://a/2", "x2"),
                    _entry("https://a/3", "x3"),
                ],
            )
        }
    )
    summarize_fn = _fake_summarize(
        category_by_url={
            "https://a/1": "AI",
            "https://a/2": "데이터",
            "https://a/3": "AI",
        }
    )
    rebuild_fn = _fake_rebuild()

    result = await cycle.run_cycle(
        conn,
        fetch_feeds=fetch_fn,
        extract=_fake_extract(),
        summarize=summarize_fn,
        rebuild=rebuild_fn,
    )

    # 서로 다른 카테고리 2개 → rebuild 2회.
    assert len(rebuild_fn.calls) == 2
    ai_call = next(c for c in rebuild_fn.calls if len(c["new_article_ids"]) == 2)
    data_call = next(c for c in rebuild_fn.calls if len(c["new_article_ids"]) == 1)
    assert ai_call["category_id"] != data_call["category_id"]
    assert set(result.rebuilt_category_ids) == {
        ai_call["category_id"],
        data_call["category_id"],
    }


# -----------------------------------------------------------------------------
# 중복 URL 제외
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_cycle_filters_already_stored_urls(conn: sqlite3.Connection):
    feed_id = _insert_feed(conn, "https://a/rss")
    conn.execute(
        "INSERT INTO articles (feed_id, url, title, status) VALUES (?, ?, ?, 'ok')",
        (feed_id, "https://a/old", "old"),
    )
    conn.commit()

    fetch_fn = _fake_fetch_feeds(
        {
            "https://a/rss": FetchResult(
                url="https://a/rss",
                title="A",
                entries=[
                    _entry("https://a/old", "old"),  # 이미 있음
                    _entry("https://a/new", "new"),
                ],
            )
        }
    )
    summarize_fn = _fake_summarize(category_by_url={"https://a/new": "AI"})
    rebuild_fn = _fake_rebuild()

    result = await cycle.run_cycle(
        conn,
        fetch_feeds=fetch_fn,
        extract=_fake_extract(),
        summarize=summarize_fn,
        rebuild=rebuild_fn,
    )

    assert result.new_articles == 1
    assert summarize_fn.calls == ["https://a/new"]


# -----------------------------------------------------------------------------
# Fetch 실패 처리
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_cycle_records_fetch_error_and_continues(conn: sqlite3.Connection):
    bad_id = _insert_feed(conn, "https://bad/rss")
    good_id = _insert_feed(conn, "https://good/rss")

    fetch_fn = _fake_fetch_feeds(
        {
            "https://bad/rss": FetchError(
                url="https://bad/rss", error="timeout after 30s"
            ),
            "https://good/rss": FetchResult(
                url="https://good/rss",
                title="G",
                entries=[_entry("https://good/1", "g1")],
            ),
        }
    )
    summarize_fn = _fake_summarize(category_by_url={"https://good/1": "AI"})
    rebuild_fn = _fake_rebuild()

    result = await cycle.run_cycle(
        conn,
        fetch_feeds=fetch_fn,
        extract=_fake_extract(),
        summarize=summarize_fn,
        rebuild=rebuild_fn,
    )

    assert result.feeds_attempted == 2
    assert result.feeds_failed == 1
    assert result.feeds_succeeded == 1
    assert result.new_articles == 1

    # job_logs 기록 확인.
    log = conn.execute(
        "SELECT job_type, target_ref, status, error_message FROM job_logs "
        "WHERE job_type='fetch_feed'"
    ).fetchone()
    assert log is not None
    assert log["target_ref"] == str(bad_id)
    assert log["status"] == "failed"
    assert "timeout" in log["error_message"]

    bad_row = conn.execute(
        "SELECT consecutive_failures FROM feeds WHERE id=?", (bad_id,)
    ).fetchone()
    assert bad_row["consecutive_failures"] == 1
    good_row = conn.execute(
        "SELECT consecutive_failures, last_fetched_at FROM feeds WHERE id=?",
        (good_id,),
    ).fetchone()
    assert good_row["consecutive_failures"] == 0
    assert good_row["last_fetched_at"] is not None


# -----------------------------------------------------------------------------
# Summarize 실패 경로
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_cycle_logs_summarize_failure_and_skips_rebuild(
    conn: sqlite3.Connection,
):
    _insert_feed(conn, "https://a/rss")

    fetch_fn = _fake_fetch_feeds(
        {
            "https://a/rss": FetchResult(
                url="https://a/rss",
                title="A",
                entries=[
                    _entry("https://a/1", "ok"),
                    _entry("https://a/2", "fail"),
                ],
            )
        }
    )
    summarize_fn = _fake_summarize(
        category_by_url={"https://a/1": "AI"},
        fail_urls={"https://a/2"},
    )
    rebuild_fn = _fake_rebuild()

    result = await cycle.run_cycle(
        conn,
        fetch_feeds=fetch_fn,
        extract=_fake_extract(),
        summarize=summarize_fn,
        rebuild=rebuild_fn,
    )

    assert result.ok_articles == 1
    assert result.failed_articles == 1
    # 실패 글의 카테고리는 affected 에 포함되지 않음 → rebuild 는 1회만.
    assert len(rebuild_fn.calls) == 1

    log = conn.execute(
        "SELECT error_message FROM job_logs WHERE job_type='summarize'"
    ).fetchone()
    assert log is not None
    assert "boom" in log["error_message"]


# -----------------------------------------------------------------------------
# Rebuild 실패 경로
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_cycle_logs_rebuild_failure(conn: sqlite3.Connection):
    _insert_feed(conn, "https://a/rss")

    fetch_fn = _fake_fetch_feeds(
        {
            "https://a/rss": FetchResult(
                url="https://a/rss",
                title="A",
                entries=[_entry("https://a/1", "x")],
            )
        }
    )
    summarize_fn = _fake_summarize(category_by_url={"https://a/1": "AI"})

    # rebuild 는 생성된 카테고리 id 에 대해 실패하도록 동적으로 구성.
    async def rebuild_fn(
        conn: sqlite3.Connection,
        *,
        category_id: int,
        new_article_ids: Sequence[int] | None = None,
    ) -> RebuildOutcome:
        return RebuildOutcome(
            category_id=category_id,
            status="failed",
            content_markdown=None,
            is_initial=True,
            used_existing_context_size=0,
            articles_count=0,
            error="llm down",
        )

    result = await cycle.run_cycle(
        conn,
        fetch_feeds=fetch_fn,
        extract=_fake_extract(),
        summarize=summarize_fn,
        rebuild=rebuild_fn,
    )

    assert result.rebuilt_category_ids == []
    assert len(result.rebuild_failed_category_ids) == 1

    log = conn.execute(
        "SELECT status, error_message FROM job_logs WHERE job_type='rebuild_wiki'"
    ).fetchone()
    assert log is not None
    assert log["status"] == "failed"
    assert "llm down" in log["error_message"]


# -----------------------------------------------------------------------------
# 기본 의존 주입 (주입 파라미터 없이 호출해도 준비된 기본 함수가 연결되어 있음)
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_cycle_uses_defaults_without_injection(conn: sqlite3.Connection):
    # 활성 피드가 없으면 외부 호출 자체가 일어나지 않으므로 기본 구현으로도 안전하게 실행된다.
    result = await cycle.run_cycle(conn)
    assert result.feeds_attempted == 0
    assert result.new_articles == 0
