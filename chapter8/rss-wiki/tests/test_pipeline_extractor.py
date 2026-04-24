"""pipeline.extractor — trafilatura 래퍼 + 20s 타임아웃 + RSS summary fallback (PRD §7.1)."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from rss_wiki.pipeline import extractor


def _async_value(value: Any):
    async def f(*args: Any, **kwargs: Any) -> Any:
        return value

    return f


def _async_raise(exc: BaseException):
    async def f(*args: Any, **kwargs: Any) -> Any:
        raise exc

    return f


@pytest.mark.asyncio
async def test_extract_article_returns_trafilatura_result_on_success():
    result = await extractor.extract_article(
        "https://x/a",
        raw_summary="summary",
        fetch=_async_value("<html>...</html>"),
        extract=_async_value("  본문입니다  "),
    )

    assert result.source == "trafilatura"
    assert result.text == "본문입니다"


@pytest.mark.asyncio
async def test_extract_article_passes_fetched_html_and_url_to_extract():
    captured: dict[str, Any] = {}

    async def fetch(url: str) -> str:
        captured["fetch_url"] = url
        return "<html>body</html>"

    async def extract(html: str, url: str) -> str:
        captured["extract_html"] = html
        captured["extract_url"] = url
        return "body"

    await extractor.extract_article(
        "https://x/a", raw_summary=None, fetch=fetch, extract=extract
    )

    assert captured == {
        "fetch_url": "https://x/a",
        "extract_html": "<html>body</html>",
        "extract_url": "https://x/a",
    }


@pytest.mark.asyncio
async def test_extract_article_falls_back_when_extract_returns_none():
    result = await extractor.extract_article(
        "https://x/a",
        raw_summary="요약입니다",
        fetch=_async_value("<html>"),
        extract=_async_value(None),
    )

    assert result.source == "fallback"
    assert result.text == "요약입니다"


@pytest.mark.asyncio
async def test_extract_article_falls_back_when_extract_returns_whitespace():
    result = await extractor.extract_article(
        "https://x/a",
        raw_summary="요약",
        fetch=_async_value("<html>"),
        extract=_async_value("   \n  "),
    )

    assert result.source == "fallback"
    assert result.text == "요약"


@pytest.mark.asyncio
async def test_extract_article_falls_back_when_fetch_returns_none():
    calls: list[tuple[str, str]] = []

    async def extract(html: str, url: str) -> str:
        calls.append((html, url))
        return "should-not-be-used"

    result = await extractor.extract_article(
        "https://x/a",
        raw_summary="summary",
        fetch=_async_value(None),
        extract=extract,
    )

    assert result.source == "fallback"
    assert result.text == "summary"
    assert calls == []  # extract 은 호출되지 않는다


@pytest.mark.asyncio
async def test_extract_article_falls_back_on_fetch_exception():
    result = await extractor.extract_article(
        "https://x/a",
        raw_summary="summary",
        fetch=_async_raise(RuntimeError("net down")),
        extract=_async_value("ignored"),
    )

    assert result.source == "fallback"
    assert result.text == "summary"


@pytest.mark.asyncio
async def test_extract_article_falls_back_on_extract_exception():
    result = await extractor.extract_article(
        "https://x/a",
        raw_summary="summary",
        fetch=_async_value("<html>"),
        extract=_async_raise(RuntimeError("parse err")),
    )

    assert result.source == "fallback"
    assert result.text == "summary"


@pytest.mark.asyncio
async def test_extract_article_times_out_and_falls_back():
    async def slow_fetch(url: str) -> str:
        await asyncio.sleep(5)
        return "<html>"

    result = await extractor.extract_article(
        "https://x/a",
        raw_summary="summary",
        timeout_seconds=0.01,
        fetch=slow_fetch,
        extract=_async_value("body"),
    )

    assert result.source == "fallback"
    assert result.text == "summary"


@pytest.mark.asyncio
async def test_extract_article_returns_none_when_no_fallback_available():
    result = await extractor.extract_article(
        "https://x/a",
        raw_summary=None,
        fetch=_async_value(None),
        extract=_async_value(None),
    )

    assert result.source == "none"
    assert result.text is None


@pytest.mark.asyncio
async def test_extract_article_treats_whitespace_only_raw_summary_as_absent():
    result = await extractor.extract_article(
        "https://x/a",
        raw_summary="   \n  ",
        fetch=_async_value(None),
        extract=_async_value(None),
    )

    assert result.source == "none"
    assert result.text is None


@pytest.mark.asyncio
async def test_extract_article_strips_extracted_text():
    result = await extractor.extract_article(
        "https://x/a",
        raw_summary=None,
        fetch=_async_value("<html>"),
        extract=_async_value("\n  본문  \n"),
    )

    assert result.source == "trafilatura"
    assert result.text == "본문"


def test_default_timeout_comes_from_config():
    from rss_wiki import config

    defaults = extractor.extract_article.__kwdefaults__
    assert defaults is not None
    assert (
        defaults["timeout_seconds"] == config.EXTRACTOR_TIMEOUT_SECONDS == 20
    )
