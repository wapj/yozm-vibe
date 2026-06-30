"""pipeline/fetcher.py 테스트."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from rss_wiki.pipeline.fetcher import fetch_feed, fetch_new_entries


@pytest.mark.asyncio
async def test_fetch_feed_returns_entries():
    mock_result = MagicMock()
    mock_result.bozo = False
    mock_result.entries = [
        MagicMock(
            link="https://example.com/1",
            title="제목1",
            author="작성자",
            published="2024-01-01",
            summary="요약",
        )
    ]
    mock_result.entries[0].get = lambda k, d=None: {
        "link": "https://example.com/1",
        "title": "제목1",
        "author": "작성자",
        "published": "2024-01-01",
        "summary": "요약",
    }.get(k, d)

    with patch("rss_wiki.pipeline.fetcher.feedparser.parse", return_value=mock_result):
        entries = await fetch_feed("https://example.com/feed")

    assert len(entries) == 1
    assert entries[0]["url"] == "https://example.com/1"
    assert entries[0]["title"] == "제목1"


@pytest.mark.asyncio
async def test_fetch_feed_timeout_returns_empty():
    import asyncio
    with patch(
        "rss_wiki.pipeline.fetcher.feedparser.parse",
        side_effect=asyncio.TimeoutError,
    ):
        entries = await fetch_feed("https://example.com/feed", timeout=0.001)
    assert entries == []


@pytest.mark.asyncio
async def test_fetch_new_entries_filters_existing():
    mock_result = MagicMock()
    mock_result.bozo = False
    mock_result.entries = [
        MagicMock(**{"get.side_effect": lambda k, d=None: {"link": f"https://example.com/{i}", "title": f"제목{i}"}.get(k, d)})
        for i in range(3)
    ]
    # entries[i].get(...) 동작 수정
    for i, entry in enumerate(mock_result.entries):
        url = f"https://example.com/{i}"
        entry.get = lambda k, d=None, u=url, t=f"제목{i}": {"link": u, "title": t, "author": None, "published": None, "summary": None}.get(k, d)

    existing_urls = {"https://example.com/0", "https://example.com/1"}

    with patch("rss_wiki.pipeline.fetcher.feedparser.parse", return_value=mock_result):
        result = await fetch_new_entries(
            [{"id": 1, "url": "https://example.com/feed"}],
            existing_urls,
        )

    assert 1 in result
    # https://example.com/2 만 신규
    new_urls = [e["url"] for e in result[1]]
    assert "https://example.com/2" in new_urls
    assert "https://example.com/0" not in new_urls
