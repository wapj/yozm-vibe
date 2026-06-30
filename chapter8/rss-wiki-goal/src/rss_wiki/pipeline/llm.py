"""Claude CLI -p 모드 subprocess 래퍼. JSON 파싱 폴백 체인 + 지수 백오프."""

import asyncio
import json
import logging
import re
from typing import Any

from rss_wiki.config import (
    LLM_BACKOFF_DELAYS,
    LLM_BACKOFF_MAX_RETRIES,
    LLM_SUBPROCESS_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)

_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.MULTILINE)
_JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}")


async def _run_claude(prompt: str, timeout: int = LLM_SUBPROCESS_TIMEOUT_SECONDS) -> str:
    """claude -p를 실행하고 stdout을 반환한다."""
    proc = await asyncio.create_subprocess_exec(
        "claude", "-p", "--output-format", "text",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=prompt.encode()),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        proc.kill()
        raise

    if proc.returncode != 0:
        err = stderr.decode(errors="replace")
        raise RuntimeError(f"claude exited {proc.returncode}: {err[:200]}")

    return stdout.decode(errors="replace").strip()


def _try_parse(text: str) -> dict[str, Any] | None:
    """JSON 파싱 폴백 체인 1-3단계."""
    # 1단계
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2단계: 코드펜스 제거
    m = _FENCE_RE.search(text)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass

    # 3단계: 정규식으로 첫 JSON 블록
    m2 = _JSON_BLOCK_RE.search(text)
    if m2:
        try:
            return json.loads(m2.group())
        except json.JSONDecodeError:
            pass

    return None


async def call_llm_json(
    prompt: str,
    timeout: int = LLM_SUBPROCESS_TIMEOUT_SECONDS,
) -> dict[str, Any] | None:
    """LLM을 호출하고 JSON dict를 반환한다. 모든 시도 실패 시 None."""
    # 지수 백오프 (네트워크/프로세스 에러)
    last_exc: Exception | None = None
    for attempt in range(LLM_BACKOFF_MAX_RETRIES):
        try:
            raw = await _run_claude(prompt, timeout)
            break
        except Exception as exc:
            last_exc = exc
            if attempt < LLM_BACKOFF_MAX_RETRIES - 1:
                delay = LLM_BACKOFF_DELAYS[attempt]
                logger.warning("LLM call failed (attempt %d), retry in %ds: %s", attempt + 1, delay, exc)
                await asyncio.sleep(delay)
    else:
        logger.error("LLM call failed after %d retries: %s", LLM_BACKOFF_MAX_RETRIES, last_exc)
        return None

    result = _try_parse(raw)
    if result is not None:
        return result

    # 4단계: 재호출 (JSON만 달라는 메시지 추가)
    retry_prompt = prompt + "\n\n이전 응답이 유효한 JSON이 아니었습니다. JSON 객체 하나만 출력하세요."
    try:
        raw2 = await _run_claude(retry_prompt, timeout)
        result2 = _try_parse(raw2)
        if result2 is not None:
            return result2
    except Exception as exc:
        logger.error("LLM JSON retry call failed: %s", exc)

    # 5단계: 포기
    logger.error("LLM JSON parsing failed for all attempts. Raw output: %s", raw[:200])
    return None


async def call_llm_text(
    prompt: str,
    timeout: int = LLM_SUBPROCESS_TIMEOUT_SECONDS,
) -> str | None:
    """LLM을 호출하고 원문 텍스트를 반환한다. wiki_rebuild 전용."""
    last_exc: Exception | None = None
    for attempt in range(LLM_BACKOFF_MAX_RETRIES):
        try:
            return await _run_claude(prompt, timeout)
        except Exception as exc:
            last_exc = exc
            if attempt < LLM_BACKOFF_MAX_RETRIES - 1:
                delay = LLM_BACKOFF_DELAYS[attempt]
                logger.warning("LLM text call failed (attempt %d), retry in %ds: %s", attempt + 1, delay, exc)
                await asyncio.sleep(delay)
    logger.error("LLM text call failed after retries: %s", last_exc)
    return None
