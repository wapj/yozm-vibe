"""trafilatura 본문 추출 래퍼."""

import asyncio
import logging

import trafilatura

from rss_wiki.config import EXTRACTOR_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


def _extract_sync(url: str) -> str | None:
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            return None
        text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        return text
    except Exception as exc:
        logger.error("Extraction error (%s): %s", url, exc)
        return None


async def extract_content(
    url: str,
    fallback: str | None = None,
    timeout: int = EXTRACTOR_TIMEOUT_SECONDS,
) -> str:
    """URL에서 본문을 추출한다. 실패 시 fallback(raw_summary)을 반환한다."""
    loop = asyncio.get_event_loop()
    try:
        text = await asyncio.wait_for(
            loop.run_in_executor(None, _extract_sync, url),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        logger.warning("Extraction timeout: %s", url)
        text = None
    except Exception as exc:
        logger.error("Extraction unexpected error (%s): %s", url, exc)
        text = None

    if text:
        return text

    if fallback:
        logger.info("Falling back to RSS summary for: %s", url)
        return fallback

    return ""
