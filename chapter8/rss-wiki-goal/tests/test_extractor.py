"""pipeline/extractor.py 테스트."""

import pytest
from unittest.mock import patch

from rss_wiki.pipeline.extractor import extract_content


@pytest.mark.asyncio
async def test_extract_content_success():
    with (
        patch("rss_wiki.pipeline.extractor.trafilatura.fetch_url", return_value="<html>본문</html>"),
        patch("rss_wiki.pipeline.extractor.trafilatura.extract", return_value="추출된 본문"),
    ):
        result = await extract_content("https://example.com/1")
    assert result == "추출된 본문"


@pytest.mark.asyncio
async def test_extract_content_fallback_on_none():
    with (
        patch("rss_wiki.pipeline.extractor.trafilatura.fetch_url", return_value=None),
    ):
        result = await extract_content("https://example.com/1", fallback="RSS 요약")
    assert result == "RSS 요약"


@pytest.mark.asyncio
async def test_extract_content_fallback_on_empty_extract():
    with (
        patch("rss_wiki.pipeline.extractor.trafilatura.fetch_url", return_value="<html></html>"),
        patch("rss_wiki.pipeline.extractor.trafilatura.extract", return_value=None),
    ):
        result = await extract_content("https://example.com/1", fallback="RSS 요약")
    assert result == "RSS 요약"


@pytest.mark.asyncio
async def test_extract_content_empty_when_no_fallback():
    with (
        patch("rss_wiki.pipeline.extractor.trafilatura.fetch_url", return_value=None),
    ):
        result = await extract_content("https://example.com/1")
    assert result == ""
