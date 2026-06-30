"""feedparser 래퍼 — 피드 수집 및 신규 URL 판별."""

import asyncio
import logging
from typing import Any

import feedparser

from rss_wiki.config import FEED_FETCH_CONCURRENCY, FEED_FETCH_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


async def fetch_feed(url: str, timeout: int = FEED_FETCH_TIMEOUT_SECONDS) -> list[dict[str, Any]]:
    """피드 URL에서 항목 목록을 반환한다. 실패 시 빈 리스트."""
    loop = asyncio.get_event_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(None, feedparser.parse, url),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        logger.warning("Feed fetch timeout: %s", url)
        return []
    except Exception as exc:
        logger.error("Feed fetch error (%s): %s", url, exc)
        return []

    if result.bozo and not result.entries:
        logger.warning("Bozo feed (possibly invalid): %s", url)

    return [
        {
            "url": e.get("link", ""),
            "title": e.get("title", "(제목 없음)"),
            "author": e.get("author"),
            "published_at": e.get("published"),
            "raw_summary": e.get("summary"),
        }
        for e in result.entries
        if e.get("link")
    ]


async def fetch_new_entries(
    feeds: list[dict[str, Any]],
    existing_urls: set[str],
    semaphore: asyncio.Semaphore | None = None,
) -> dict[int, list[dict[str, Any]]]:
    """feeds 목록에서 existing_urls에 없는 신규 항목만 반환한다.

    Returns:
        {feed_id: [entry, ...]}
    """
    if semaphore is None:
        semaphore = asyncio.Semaphore(FEED_FETCH_CONCURRENCY)

    async def _fetch_one(feed: dict[str, Any]) -> tuple[int, list[dict[str, Any]]]:
        async with semaphore:
            entries = await fetch_feed(feed["url"])
            new = [e for e in entries if e["url"] and e["url"] not in existing_urls]
            return feed["id"], new

    tasks = [asyncio.create_task(_fetch_one(f)) for f in feeds]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    out: dict[int, list[dict[str, Any]]] = {}
    for r in results:
        if isinstance(r, Exception):
            logger.error("Unexpected fetch error: %s", r)
            continue
        feed_id, entries = r
        out[feed_id] = entries
    return out
