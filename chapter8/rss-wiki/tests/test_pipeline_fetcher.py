"""pipeline.fetcher — feedparser async 래퍼 + Semaphore + 신규 URL 판별 (PRD §7.1)."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from rss_wiki.pipeline import fetcher


class _FakeParsed:
    """feedparser 결과의 최소 대역 — entries 리스트 + feed dict."""

    def __init__(self, entries: list[dict[str, Any]], feed_title: str | None = None) -> None:
        self.entries = entries
        self.feed = {"title": feed_title} if feed_title is not None else {}


def _make_parse(
    mapping: dict[str, _FakeParsed] | None = None,
    *,
    default: _FakeParsed | None = None,
):
    mapping = mapping or {}

    async def parse(url: str) -> _FakeParsed:
        parse.calls.append(url)  # type: ignore[attr-defined]
        if url in mapping:
            return mapping[url]
        if default is not None:
            return default
        raise KeyError(url)

    parse.calls = []  # type: ignore[attr-defined]
    return parse


# -----------------------------------------------------------------------------
# fetch_feed
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_feed_normalizes_entries_with_all_fields():
    parsed = _FakeParsed(
        entries=[
            {
                "link": "https://example.com/a",
                "title": "  A  ",
                "author": "alice",
                "published": "2026-04-24T00:00:00Z",
                "summary": "raw A",
            }
        ],
        feed_title="Example Blog",
    )
    parse = _make_parse({"https://example.com/rss": parsed})

    result = await fetcher.fetch_feed("https://example.com/rss", parse=parse)

    assert result.url == "https://example.com/rss"
    assert result.title == "Example Blog"
    assert len(result.entries) == 1
    entry = result.entries[0]
    assert entry.url == "https://example.com/a"
    assert entry.title == "A"  # title 은 strip
    assert entry.author == "alice"
    assert entry.published_at == "2026-04-24T00:00:00Z"
    assert entry.raw_summary == "raw A"


@pytest.mark.asyncio
async def test_fetch_feed_falls_back_from_published_to_updated():
    parsed = _FakeParsed(
        entries=[
            {
                "link": "https://example.com/b",
                "title": "B",
                "updated": "2026-04-23T10:00:00Z",
            }
        ]
    )
    parse = _make_parse(default=parsed)

    result = await fetcher.fetch_feed("x", parse=parse)

    assert result.entries[0].published_at == "2026-04-23T10:00:00Z"


@pytest.mark.asyncio
async def test_fetch_feed_skips_entries_without_link_or_id():
    parsed = _FakeParsed(
        entries=[
            {"title": "no link"},  # skip
            {"id": "https://example.com/fallback", "title": "by id"},  # keep
            {"link": "https://example.com/ok", "title": "ok"},  # keep
        ]
    )
    parse = _make_parse(default=parsed)

    result = await fetcher.fetch_feed("x", parse=parse)

    urls = [e.url for e in result.entries]
    assert urls == ["https://example.com/fallback", "https://example.com/ok"]


@pytest.mark.asyncio
async def test_fetch_feed_uses_url_as_title_when_missing():
    parsed = _FakeParsed(
        entries=[{"link": "https://example.com/a", "title": "   "}]
    )
    parse = _make_parse(default=parsed)

    result = await fetcher.fetch_feed("x", parse=parse)

    assert result.entries[0].title == "https://example.com/a"


@pytest.mark.asyncio
async def test_fetch_feed_times_out_after_configured_seconds():
    async def slow_parse(url: str) -> _FakeParsed:
        await asyncio.sleep(5)
        return _FakeParsed(entries=[])

    with pytest.raises(asyncio.TimeoutError):
        await fetcher.fetch_feed("x", timeout_seconds=0.01, parse=slow_parse)


@pytest.mark.asyncio
async def test_fetch_feed_handles_missing_feed_metadata():
    parsed = _FakeParsed(entries=[])
    parse = _make_parse(default=parsed)

    result = await fetcher.fetch_feed("x", parse=parse)

    assert result.title is None
    assert result.entries == []


# -----------------------------------------------------------------------------
# fetch_feeds (Semaphore, 병렬, 실패 격리)
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_feeds_returns_results_in_input_order():
    mapping = {
        f"u{i}": _FakeParsed(
            entries=[{"link": f"https://example.com/{i}", "title": f"T{i}"}]
        )
        for i in range(3)
    }
    parse = _make_parse(mapping)

    results = await fetcher.fetch_feeds(["u0", "u1", "u2"], parse=parse)

    assert [r.url for r in results] == ["u0", "u1", "u2"]
    assert all(isinstance(r, fetcher.FetchResult) for r in results)


@pytest.mark.asyncio
async def test_fetch_feeds_honors_semaphore_concurrency():
    in_flight = 0
    max_in_flight = 0

    async def parse(url: str) -> _FakeParsed:
        nonlocal in_flight, max_in_flight
        in_flight += 1
        max_in_flight = max(max_in_flight, in_flight)
        try:
            await asyncio.sleep(0.02)
            return _FakeParsed(entries=[])
        finally:
            in_flight -= 1

    await fetcher.fetch_feeds(
        [f"u{i}" for i in range(6)], concurrency=2, parse=parse
    )

    assert max_in_flight == 2


@pytest.mark.asyncio
async def test_fetch_feeds_wraps_exceptions_as_fetch_error():
    async def parse(url: str) -> _FakeParsed:
        if url == "bad":
            raise RuntimeError("boom")
        return _FakeParsed(entries=[])

    results = await fetcher.fetch_feeds(["good", "bad"], parse=parse)

    assert isinstance(results[0], fetcher.FetchResult)
    err = results[1]
    assert isinstance(err, fetcher.FetchError)
    assert err.url == "bad"
    assert "RuntimeError" in err.error and "boom" in err.error


@pytest.mark.asyncio
async def test_fetch_feeds_wraps_timeout_as_fetch_error():
    async def slow(url: str) -> _FakeParsed:
        await asyncio.sleep(1)
        return _FakeParsed(entries=[])

    results = await fetcher.fetch_feeds(
        ["slow"], timeout_seconds=0.01, parse=slow
    )

    err = results[0]
    assert isinstance(err, fetcher.FetchError)
    assert "timeout" in err.error.lower()


# -----------------------------------------------------------------------------
# filter_new_entries
# -----------------------------------------------------------------------------


def test_filter_new_entries_excludes_existing_urls():
    entries = [
        fetcher.FeedEntry(url="https://example.com/a", title="A"),
        fetcher.FeedEntry(url="https://example.com/b", title="B"),
        fetcher.FeedEntry(url="https://example.com/c", title="C"),
    ]

    result = fetcher.filter_new_entries(
        entries, existing_urls={"https://example.com/b"}
    )

    assert [e.url for e in result] == ["https://example.com/a", "https://example.com/c"]


def test_filter_new_entries_deduplicates_within_batch():
    e1 = fetcher.FeedEntry(url="https://x/1", title="1")
    e2 = fetcher.FeedEntry(url="https://x/1", title="1 dup")
    e3 = fetcher.FeedEntry(url="https://x/2", title="2")

    result = fetcher.filter_new_entries([e1, e2, e3], existing_urls=set())

    assert [e.title for e in result] == ["1", "2"]


def test_filter_new_entries_preserves_input_order():
    entries = [
        fetcher.FeedEntry(url=f"https://x/{i}", title=str(i)) for i in (3, 1, 4, 1, 5)
    ]

    result = fetcher.filter_new_entries(entries, existing_urls=set())

    assert [e.title for e in result] == ["3", "1", "4", "5"]


def test_filter_new_entries_accepts_any_iterable_of_known_urls():
    entries = [fetcher.FeedEntry(url="https://x/1", title="1")]

    result = fetcher.filter_new_entries(entries, existing_urls=["https://x/1"])

    assert result == []


# -----------------------------------------------------------------------------
# 기본값은 PRD §14 운영 상수에서 온다.
# -----------------------------------------------------------------------------


def test_defaults_come_from_config_constants():
    from rss_wiki import config

    feed_defaults = fetcher.fetch_feed.__kwdefaults__
    feeds_defaults = fetcher.fetch_feeds.__kwdefaults__

    assert feed_defaults is not None
    assert feeds_defaults is not None
    assert (
        feed_defaults["timeout_seconds"]
        == config.FEED_FETCH_TIMEOUT_SECONDS
        == 30
    )
    assert (
        feeds_defaults["timeout_seconds"]
        == config.FEED_FETCH_TIMEOUT_SECONDS
        == 30
    )
    assert (
        feeds_defaults["concurrency"] == config.FEED_FETCH_CONCURRENCY == 5
    )
