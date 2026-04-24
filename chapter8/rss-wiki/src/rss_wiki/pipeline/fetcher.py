"""RSS 피드 fetch 래퍼 (PRD §7.1).

- `feedparser.parse` 를 스레드 풀로 offload 해 async 로 호출.
- 피드별 최대 5 병렬 (`asyncio.Semaphore`), 개별 30s 타임아웃.
- 한 피드의 실패가 사이클 전체를 무너뜨리지 않도록 `FetchError` 로 래핑.
- 신규 URL 판별은 `filter_new_entries` 로 수행 (호출자가 기존 URL 집합을 주입).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Iterable, Sequence

import feedparser

from rss_wiki.config import FEED_FETCH_CONCURRENCY, FEED_FETCH_TIMEOUT_SECONDS


@dataclass(slots=True)
class FeedEntry:
    url: str
    title: str
    author: str | None = None
    published_at: str | None = None
    raw_summary: str | None = None


@dataclass(slots=True)
class FetchResult:
    url: str
    title: str | None
    entries: list[FeedEntry]


@dataclass(slots=True)
class FetchError:
    url: str
    error: str


ParseAwaitable = Callable[[str], Awaitable[Any]]


async def _default_parse(url: str) -> Any:
    return await asyncio.to_thread(feedparser.parse, url)


async def fetch_feed(
    url: str,
    *,
    timeout_seconds: float = FEED_FETCH_TIMEOUT_SECONDS,
    parse: ParseAwaitable = _default_parse,
) -> FetchResult:
    """단일 피드 URL 을 가져와 entries 로 정규화한다.

    타임아웃 초과 시 `asyncio.TimeoutError` 를 raise (상위에서 잡아 job_logs 기록).
    """
    parsed = await asyncio.wait_for(parse(url), timeout=timeout_seconds)
    entries: list[FeedEntry] = []
    for raw_entry in getattr(parsed, "entries", []) or []:
        entry_url = _pick(raw_entry, "link") or _pick(raw_entry, "id")
        if not entry_url:
            continue
        title = (_pick(raw_entry, "title") or "").strip() or entry_url
        entries.append(
            FeedEntry(
                url=entry_url,
                title=title,
                author=_pick(raw_entry, "author"),
                published_at=_pick(raw_entry, "published")
                or _pick(raw_entry, "updated"),
                raw_summary=_pick(raw_entry, "summary"),
            )
        )
    return FetchResult(url=url, title=_feed_title(parsed), entries=entries)


async def fetch_feeds(
    urls: Sequence[str],
    *,
    concurrency: int = FEED_FETCH_CONCURRENCY,
    timeout_seconds: float = FEED_FETCH_TIMEOUT_SECONDS,
    parse: ParseAwaitable = _default_parse,
) -> list[FetchResult | FetchError]:
    """여러 피드를 세마포어로 병렬 수집한다. 결과는 입력 순서를 유지한다."""
    sem = asyncio.Semaphore(concurrency)

    async def worker(url: str) -> FetchResult | FetchError:
        async with sem:
            try:
                return await fetch_feed(
                    url, timeout_seconds=timeout_seconds, parse=parse
                )
            except asyncio.TimeoutError:
                return FetchError(url=url, error=f"timeout after {timeout_seconds}s")
            except Exception as exc:
                return FetchError(url=url, error=f"{type(exc).__name__}: {exc}")

    return list(await asyncio.gather(*(worker(u) for u in urls)))


def filter_new_entries(
    entries: Iterable[FeedEntry],
    existing_urls: Iterable[str],
) -> list[FeedEntry]:
    """`articles` 에 이미 존재하는 URL 과 배치 내 중복을 제거한 신규 항목."""
    known = set(existing_urls)
    seen: set[str] = set()
    result: list[FeedEntry] = []
    for entry in entries:
        if entry.url in known or entry.url in seen:
            continue
        seen.add(entry.url)
        result.append(entry)
    return result


def _pick(raw_entry: Any, key: str) -> Any:
    if hasattr(raw_entry, "get"):
        return raw_entry.get(key)
    return getattr(raw_entry, key, None)


def _feed_title(parsed: Any) -> str | None:
    feed_info = getattr(parsed, "feed", None)
    if feed_info is None:
        return None
    return _pick(feed_info, "title")
