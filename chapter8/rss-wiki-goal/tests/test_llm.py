"""pipeline/llm.py JSON 파싱 폴백 체인 테스트 (subprocess mock)."""

import pytest
from unittest.mock import AsyncMock, patch

from rss_wiki.pipeline.llm import _try_parse, call_llm_json


# ── _try_parse 단위 테스트 ────────────────────────────────────────────────────

def test_try_parse_valid_json():
    result = _try_parse('{"key": "value"}')
    assert result == {"key": "value"}


def test_try_parse_with_fence():
    result = _try_parse('```json\n{"key": "value"}\n```')
    assert result == {"key": "value"}


def test_try_parse_with_fence_no_lang():
    result = _try_parse('```\n{"key": "value"}\n```')
    assert result == {"key": "value"}


def test_try_parse_embedded_json():
    result = _try_parse('Here is the result: {"key": "value"} done.')
    assert result == {"key": "value"}


def test_try_parse_invalid_returns_none():
    result = _try_parse("not json at all")
    assert result is None


# ── call_llm_json 통합 테스트 (subprocess mock) ───────────────────────────────

@pytest.mark.asyncio
async def test_call_llm_json_success():
    mock_raw = '{"summary": "요약", "category_name": "AI", "is_new_category": false, "language_detected": "ko"}'
    with patch("rss_wiki.pipeline.llm._run_claude", new=AsyncMock(return_value=mock_raw)):
        result = await call_llm_json("test prompt")
    assert result is not None
    assert result["summary"] == "요약"
    assert result["category_name"] == "AI"


@pytest.mark.asyncio
async def test_call_llm_json_fence_fallback():
    mock_raw = '```json\n{"summary": "요약", "category_name": "LLM"}\n```'
    with patch("rss_wiki.pipeline.llm._run_claude", new=AsyncMock(return_value=mock_raw)):
        result = await call_llm_json("test prompt")
    assert result is not None
    assert result["category_name"] == "LLM"


@pytest.mark.asyncio
async def test_call_llm_json_retry_on_bad_json():
    good_json = '{"summary": "ok", "category_name": "test"}'
    call_count = 0

    async def mock_run(prompt, timeout=120):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return "bad json response"
        return good_json

    with patch("rss_wiki.pipeline.llm._run_claude", side_effect=mock_run):
        result = await call_llm_json("test")
    assert result is not None
    assert call_count == 2  # 1차 실패 후 재호출


@pytest.mark.asyncio
async def test_call_llm_json_all_fail_returns_none():
    async def always_bad(prompt, timeout=120):
        return "not json"

    with patch("rss_wiki.pipeline.llm._run_claude", side_effect=always_bad):
        result = await call_llm_json("test")
    assert result is None
