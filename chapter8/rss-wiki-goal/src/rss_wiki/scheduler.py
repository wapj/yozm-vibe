"""APScheduler BackgroundScheduler 등록 — 매시 정각 수집."""

import asyncio
import logging
import sqlite3
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from rss_wiki.config import LLM_PARALLEL_CONCURRENCY, SCHEDULER_HOUR, SCHEDULER_MINUTE
from rss_wiki.pipeline.extractor import extract_content
from rss_wiki.pipeline.fetcher import fetch_new_entries
from rss_wiki.pipeline.rebuilder import rebuild_wiki
from rss_wiki.pipeline.summarizer import summarize_article

logger = logging.getLogger(__name__)

_fetch_lock = asyncio.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _log(conn: sqlite3.Connection, job_type: str, status: str,
         target_ref: str | None = None, error: str | None = None,
         started_at: str | None = None, attempt: int = 1) -> None:
    try:
        conn.execute(
            """INSERT INTO job_logs(job_type, target_ref, status, error_message,
               attempt_count, started_at, finished_at)
               VALUES (?,?,?,?,?,?,datetime('now'))""",
            (job_type, target_ref, status, error, attempt, started_at or _now()),
        )
        conn.commit()
    except Exception as exc:
        logger.error("job_log write failed: %s", exc)


async def run_fetch_cycle(conn: sqlite3.Connection) -> dict:
    """수집 사이클 1회 실행. 이미 실행 중이면 started=False 반환."""
    if _fetch_lock.locked():
        return {"started": False, "reason": "already_running"}

    async with _fetch_lock:
        return await _do_fetch_cycle(conn)


async def _process_entry(
    conn: sqlite3.Connection,
    feed_id: int,
    entry: dict,
    sem: asyncio.Semaphore,
) -> tuple[int | None, int | None]:
    """글 1건을 추출·요약·분류한다. (article_id, category_id) 반환. 실패 시 None."""
    url = entry["url"]
    title = entry["title"]
    started = _now()

    # 본문 추출
    async with sem:
        try:
            content = await extract_content(url, fallback=entry.get("raw_summary"))
            _log(conn, "extract", "ok", target_ref=url, started_at=started)
        except Exception as exc:
            _log(conn, "extract", "failed", target_ref=url, error=str(exc)[:300], started_at=started)
            content = entry.get("raw_summary") or ""

    # DB 저장
    try:
        conn.execute(
            """INSERT INTO articles(feed_id, url, title, author, published_at,
               raw_summary, extracted_content, status)
               VALUES (?,?,?,?,?,?,?,'ok')""",
            (feed_id, url, title, entry.get("author"), entry.get("published_at"),
             entry.get("raw_summary"), content),
        )
        conn.commit()
        article_id = conn.execute("SELECT id FROM articles WHERE url=?", (url,)).fetchone()["id"]
    except Exception as exc:
        logger.error("DB insert error (%s): %s", url, exc)
        return None, None

    # 요약·분류
    sum_started = _now()
    async with sem:
        result = await summarize_article(conn, article_id, title, url, content or title)

    if result is None:
        conn.execute("UPDATE articles SET status='failed' WHERE id=?", (article_id,))
        conn.commit()
        _log(conn, "summarize", "failed", target_ref=str(article_id),
             error="LLM summarize returned None", started_at=sum_started)
        return None, None

    _log(conn, "summarize", "ok", target_ref=str(article_id), started_at=sum_started)

    row = conn.execute("SELECT primary_category_id FROM articles WHERE id=?", (article_id,)).fetchone()
    cat_id = row["primary_category_id"] if row else None
    return article_id, cat_id


async def _do_fetch_cycle(conn: sqlite3.Connection) -> dict:
    cycle_started = _now()
    logger.info("Fetch cycle started")

    feed_rows = conn.execute("SELECT id, url FROM feeds WHERE is_active=1").fetchall()
    feeds = [{"id": r["id"], "url": r["url"]} for r in feed_rows]

    if not feeds:
        _log(conn, "fetch_feed", "ok", target_ref="(no active feeds)", started_at=cycle_started)
        return {"started": True, "feeds": 0, "new_articles": 0}

    existing_urls = {r["url"] for r in conn.execute("SELECT url FROM articles").fetchall()}

    # 피드 RSS 병렬 수집
    fetch_started = _now()
    new_by_feed = await fetch_new_entries(feeds, existing_urls)

    for feed in feeds:
        fid = feed["id"]
        entries = new_by_feed.get(fid, [])
        status = "ok" if fid in new_by_feed else "failed"
        _log(conn, "fetch_feed", status,
             target_ref=f"feed:{fid} new:{len(entries)}",
             started_at=fetch_started)

    # 모든 신규 항목 평탄화
    all_entries: list[tuple[int, dict]] = [
        (fid, entry)
        for fid, entries in new_by_feed.items()
        for entry in entries
    ]

    if not all_entries:
        for fid in new_by_feed:
            conn.execute(
                "UPDATE feeds SET last_fetched_at=datetime('now'), consecutive_failures=0 WHERE id=?",
                (fid,),
            )
        conn.commit()
        return {"started": True, "feeds": len(feeds), "new_articles": 0}

    # 글 처리 병렬화
    sem = asyncio.Semaphore(LLM_PARALLEL_CONCURRENCY)
    tasks = [
        asyncio.create_task(_process_entry(conn, fid, entry, sem))
        for fid, entry in all_entries
    ]
    results = await asyncio.gather(*tasks)

    affected_category_ids: set[int] = set()
    new_article_ids_by_category: dict[int, list[int]] = {}
    total_new = 0

    for article_id, cat_id in results:
        if article_id is None:
            continue
        total_new += 1
        if cat_id:
            affected_category_ids.add(cat_id)
            new_article_ids_by_category.setdefault(cat_id, []).append(article_id)

    # 피드 last_fetched_at 갱신
    for fid in new_by_feed:
        conn.execute(
            "UPDATE feeds SET last_fetched_at=datetime('now'), consecutive_failures=0 WHERE id=?",
            (fid,),
        )
    conn.commit()

    # 영향받은 카테고리 Wiki 재구성
    for cat_id in affected_category_ids:
        rebuild_started = _now()
        article_ids = new_article_ids_by_category.get(cat_id, [])
        ok = await rebuild_wiki(conn, cat_id, article_ids)
        _log(conn, "rebuild_wiki",
             "ok" if ok else "failed",
             target_ref=f"category:{cat_id}",
             error=None if ok else "rebuild_wiki returned False",
             started_at=rebuild_started)
        if not ok:
            logger.warning("Wiki rebuild failed for category %d", cat_id)

    logger.info("Fetch cycle done. new_articles=%d", total_new)
    return {"started": True, "feeds": len(feeds), "new_articles": total_new}


def create_scheduler(conn: sqlite3.Connection) -> BackgroundScheduler:
    scheduler = BackgroundScheduler()

    def _job():
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(run_fetch_cycle(conn))
        finally:
            loop.close()

    scheduler.add_job(
        _job,
        trigger="cron",
        hour=SCHEDULER_HOUR,
        minute=SCHEDULER_MINUTE,
        id="fetch_cycle",
        replace_existing=True,
    )
    return scheduler
