"""본문 추출 래퍼 (PRD §7.1, §14).

- `trafilatura.fetch_url` 로 HTML 을 받고 `trafilatura.extract` 로 본문 텍스트 추출.
- 전체 과정(fetch + extract)에 20s 타임아웃 (`asyncio.wait_for`).
- 실패하거나 빈 결과면 RSS `raw_summary` 로 fallback.
- fallback 도 비어 있으면 `source="none"`, `text=None`.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Awaitable, Callable, Literal

import trafilatura

from rss_wiki.config import EXTRACTOR_TIMEOUT_SECONDS


FetchFn = Callable[[str], Awaitable[str | None]]
ExtractFn = Callable[[str, str], Awaitable[str | None]]


async def _default_fetch(url: str) -> str | None:
    return await asyncio.to_thread(trafilatura.fetch_url, url)


async def _default_extract(html: str, url: str) -> str | None:
    return await asyncio.to_thread(trafilatura.extract, html, url=url)


@dataclass(slots=True)
class ExtractionResult:
    text: str | None
    source: Literal["trafilatura", "fallback", "none"]


async def extract_article(
    url: str,
    *,
    raw_summary: str | None = None,
    timeout_seconds: float = EXTRACTOR_TIMEOUT_SECONDS,
    fetch: FetchFn = _default_fetch,
    extract: ExtractFn = _default_extract,
) -> ExtractionResult:
    """URL 에서 본문을 추출한다. 실패하면 `raw_summary` 로 fallback.

    fetch/extract 가 예외를 던지거나 None·빈 문자열을 돌려주거나,
    전체가 `timeout_seconds` 를 초과하면 모두 fallback 으로 흡수된다.
    """
    try:
        text = await asyncio.wait_for(
            _run_trafilatura(url, fetch=fetch, extract=extract),
            timeout=timeout_seconds,
        )
    except Exception:
        text = None

    if text and text.strip():
        return ExtractionResult(text=text.strip(), source="trafilatura")

    fallback = (raw_summary or "").strip()
    if fallback:
        return ExtractionResult(text=fallback, source="fallback")
    return ExtractionResult(text=None, source="none")


async def _run_trafilatura(
    url: str,
    *,
    fetch: FetchFn,
    extract: ExtractFn,
) -> str | None:
    html = await fetch(url)
    if not html:
        return None
    return await extract(html, url)
