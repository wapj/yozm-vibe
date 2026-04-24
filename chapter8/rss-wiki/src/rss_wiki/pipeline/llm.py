"""Claude CLI `-p` subprocess 래퍼 (PRD §7.2).

subprocess 레벨 에러는 지수 백오프로, JSON 파싱 실패는 폴백 체인으로 처리한다.
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from rss_wiki.config import (
    LLM_BACKOFF_SECONDS,
    LLM_MAX_ATTEMPTS,
    LLM_SUBPROCESS_TIMEOUT_SECONDS,
)


CLAUDE_CLI_ARGS: tuple[str, ...] = ("claude", "-p", "--output-format", "text")

_RATE_LIMIT_PATTERN = re.compile(
    r"rate[\s_-]?limit|too many requests|\b429\b",
    re.IGNORECASE,
)

_CODE_FENCE_PATTERN = re.compile(
    r"^\s*```(?:json)?\s*\n?(?P<body>[\s\S]*?)\n?\s*```\s*$",
    re.IGNORECASE,
)
_JSON_OBJECT_PATTERN = re.compile(r"\{[\s\S]*\}")

RETRY_INSTRUCTION = (
    "\n\n이전 응답이 JSON이 아니었다. JSON만 출력하라."
)


class LLMError(Exception):
    """모든 재시도를 소진한 후의 subprocess 레벨 실패."""


class LLMJSONParseError(Exception):
    """JSON 파싱 폴백 체인이 모두 실패한 경우."""


class _RetryableLLMError(Exception):
    """내부 전용: timeout / non-zero exit / rate-limit."""


@dataclass(slots=True)
class LLMResult:
    stdout: str
    attempts: int


SubprocessFactory = Callable[..., Awaitable[asyncio.subprocess.Process]]
SleepFn = Callable[[float], Awaitable[None]]


async def call_claude_cli(
    prompt: str,
    *,
    timeout_seconds: float = LLM_SUBPROCESS_TIMEOUT_SECONDS,
    max_attempts: int = LLM_MAX_ATTEMPTS,
    backoff_seconds: tuple[int, ...] = LLM_BACKOFF_SECONDS,
    sleep: SleepFn = asyncio.sleep,
    create_subprocess: SubprocessFactory = asyncio.create_subprocess_exec,
) -> LLMResult:
    """`claude -p --output-format text` 를 stdin으로 호출한다.

    재시도 대상: subprocess timeout, non-zero exit, stderr의 rate-limit 단서.
    반환: 성공한 호출의 raw stdout. JSON 파싱은 호출자가 수행한다.
    """
    last_error: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return await _invoke(
                prompt,
                timeout_seconds=timeout_seconds,
                create_subprocess=create_subprocess,
                attempt_number=attempt + 1,
            )
        except _RetryableLLMError as exc:
            last_error = exc
            if attempt >= max_attempts - 1:
                break
            delay = backoff_seconds[min(attempt, len(backoff_seconds) - 1)]
            await sleep(delay)
    raise LLMError(
        f"claude CLI failed after {max_attempts} attempts: {last_error}"
    )


async def _invoke(
    prompt: str,
    *,
    timeout_seconds: float,
    create_subprocess: SubprocessFactory,
    attempt_number: int,
) -> LLMResult:
    proc = await create_subprocess(
        *CLAUDE_CLI_ARGS,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout_b, stderr_b = await asyncio.wait_for(
            proc.communicate(prompt.encode("utf-8")),
            timeout=timeout_seconds,
        )
    except asyncio.TimeoutError as exc:
        await _terminate(proc)
        raise _RetryableLLMError(
            f"claude CLI timeout after {timeout_seconds}s"
        ) from exc

    stdout = stdout_b.decode("utf-8", errors="replace")
    stderr = stderr_b.decode("utf-8", errors="replace")

    if proc.returncode != 0:
        raise _RetryableLLMError(
            f"claude CLI exited with code {proc.returncode}: {stderr.strip()}"
        )
    if _RATE_LIMIT_PATTERN.search(stderr):
        raise _RetryableLLMError(f"rate limit detected in stderr: {stderr.strip()}")

    return LLMResult(stdout=stdout, attempts=attempt_number)


async def _terminate(proc: asyncio.subprocess.Process) -> None:
    try:
        proc.kill()
    except ProcessLookupError:
        return
    try:
        await proc.wait()
    except Exception:
        pass


def parse_json_with_fallbacks(raw: str) -> Any:
    """§7.2 JSON 파싱 폴백 체인 1~3단계.

    1. strip 후 json.loads
    2. ```json ... ``` 코드펜스 제거 후 json.loads
    3. 정규식 r'\\{[\\s\\S]*\\}' 로 첫 JSON-like 블록 추출 후 json.loads

    모두 실패하면 LLMJSONParseError 를 raise 한다.
    """
    stripped = raw.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    fence = _CODE_FENCE_PATTERN.match(stripped)
    if fence is not None:
        body = fence.group("body").strip()
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            pass

    match = _JSON_OBJECT_PATTERN.search(stripped)
    if match is not None:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise LLMJSONParseError(
        f"could not parse JSON from LLM output (len={len(raw)})"
    )


async def call_claude_cli_json(
    prompt: str,
    *,
    timeout_seconds: float = LLM_SUBPROCESS_TIMEOUT_SECONDS,
    max_attempts: int = LLM_MAX_ATTEMPTS,
    backoff_seconds: tuple[int, ...] = LLM_BACKOFF_SECONDS,
    sleep: SleepFn = asyncio.sleep,
    create_subprocess: SubprocessFactory = asyncio.create_subprocess_exec,
) -> Any:
    """claude CLI 호출 → JSON 파싱 폴백 체인.

    1. `call_claude_cli` 로 호출 → 파싱 시도
    2. 파싱 실패 시 프롬프트 뒤에 `RETRY_INSTRUCTION` 을 덧붙여 1회 재호출 → 재파싱
    3. 여전히 실패면 `LLMJSONParseError` 를 raise (호출자가 job_logs 기록/skip 처리)
    """
    first = await call_claude_cli(
        prompt,
        timeout_seconds=timeout_seconds,
        max_attempts=max_attempts,
        backoff_seconds=backoff_seconds,
        sleep=sleep,
        create_subprocess=create_subprocess,
    )
    try:
        return parse_json_with_fallbacks(first.stdout)
    except LLMJSONParseError:
        pass

    retry = await call_claude_cli(
        prompt + RETRY_INSTRUCTION,
        timeout_seconds=timeout_seconds,
        max_attempts=max_attempts,
        backoff_seconds=backoff_seconds,
        sleep=sleep,
        create_subprocess=create_subprocess,
    )
    return parse_json_with_fallbacks(retry.stdout)
