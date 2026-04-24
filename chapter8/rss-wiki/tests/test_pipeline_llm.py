"""pipeline.llm — claude CLI subprocess + 지수 백오프 (PRD §7.2)."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from rss_wiki.pipeline import llm


class _FakeProcess:
    """asyncio.subprocess.Process 의 최소 대역.

    timeout=True: communicate 가 영원히 블록되어 wait_for 가 취소하도록.
    """

    def __init__(
        self,
        *,
        returncode: int = 0,
        stdout: bytes = b"",
        stderr: bytes = b"",
        timeout: bool = False,
    ) -> None:
        self.returncode = returncode
        self._stdout = stdout
        self._stderr = stderr
        self._timeout = timeout
        self.stdin_received: bytes | None = None
        self.killed: bool = False

    async def communicate(self, input: bytes | None = None) -> tuple[bytes, bytes]:
        self.stdin_received = input
        if self._timeout:
            await asyncio.sleep(10_000)  # wait_for 가 취소할 때까지 대기
        return self._stdout, self._stderr

    def kill(self) -> None:
        self.killed = True

    async def wait(self) -> int:
        return self.returncode


def _factory(procs: list[_FakeProcess]):
    iterator = iter(procs)

    async def create(*args: Any, **kwargs: Any) -> _FakeProcess:
        create.calls.append({"args": args, "kwargs": kwargs})
        return next(iterator)

    create.calls = []  # type: ignore[attr-defined]
    return create


def _sleep_recorder() -> tuple[list[float], Any]:
    sleeps: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    return sleeps, fake_sleep


@pytest.mark.asyncio
async def test_success_on_first_attempt_passes_prompt_via_stdin():
    proc = _FakeProcess(returncode=0, stdout=b'{"ok":true}\n', stderr=b"")
    factory = _factory([proc])
    sleeps, sleeper = _sleep_recorder()

    result = await llm.call_claude_cli(
        "hello", create_subprocess=factory, sleep=sleeper
    )

    assert result.stdout == '{"ok":true}\n'
    assert result.attempts == 1
    assert sleeps == []  # 성공하면 백오프 대기 없음
    assert proc.stdin_received == b"hello"


@pytest.mark.asyncio
async def test_invokes_claude_p_with_text_output_format():
    factory = _factory([_FakeProcess(returncode=0, stdout=b"ok")])
    _, sleeper = _sleep_recorder()

    await llm.call_claude_cli("x", create_subprocess=factory, sleep=sleeper)

    call = factory.calls[0]  # type: ignore[attr-defined]
    assert call["args"] == ("claude", "-p", "--output-format", "text")
    assert call["kwargs"]["stdin"] is asyncio.subprocess.PIPE
    assert call["kwargs"]["stdout"] is asyncio.subprocess.PIPE
    assert call["kwargs"]["stderr"] is asyncio.subprocess.PIPE


@pytest.mark.asyncio
async def test_retries_on_non_zero_exit_and_succeeds():
    procs = [
        _FakeProcess(returncode=1, stderr=b"boom"),
        _FakeProcess(returncode=0, stdout=b"ok"),
    ]
    sleeps, sleeper = _sleep_recorder()

    result = await llm.call_claude_cli(
        "p", create_subprocess=_factory(procs), sleep=sleeper
    )

    assert result.stdout == "ok"
    assert result.attempts == 2
    assert sleeps == [2]  # 첫 실패 후 backoff[0]=2s 대기


@pytest.mark.asyncio
async def test_retries_on_timeout_kills_process_and_succeeds():
    procs = [
        _FakeProcess(timeout=True),
        _FakeProcess(returncode=0, stdout=b"ok"),
    ]
    sleeps, sleeper = _sleep_recorder()

    result = await llm.call_claude_cli(
        "p",
        create_subprocess=_factory(procs),
        sleep=sleeper,
        timeout_seconds=0.01,
    )

    assert result.stdout == "ok"
    assert result.attempts == 2
    assert procs[0].killed is True
    assert sleeps == [2]


@pytest.mark.asyncio
async def test_retries_on_rate_limit_in_stderr():
    procs = [
        _FakeProcess(returncode=0, stdout=b"partial", stderr=b"Error: Rate limit exceeded (429)"),
        _FakeProcess(returncode=0, stdout=b"ok"),
    ]
    sleeps, sleeper = _sleep_recorder()

    result = await llm.call_claude_cli(
        "p", create_subprocess=_factory(procs), sleep=sleeper
    )

    assert result.stdout == "ok"
    assert result.attempts == 2


@pytest.mark.asyncio
async def test_exhausts_three_attempts_then_raises_llm_error():
    procs = [
        _FakeProcess(returncode=1, stderr=b"e1"),
        _FakeProcess(returncode=1, stderr=b"e2"),
        _FakeProcess(returncode=1, stderr=b"e3"),
    ]
    sleeps, sleeper = _sleep_recorder()

    with pytest.raises(llm.LLMError) as excinfo:
        await llm.call_claude_cli(
            "p", create_subprocess=_factory(procs), sleep=sleeper
        )

    assert "3 attempts" in str(excinfo.value)
    # 3회 시도 → 실패 사이 대기 2회 (2s, 4s). 마지막 실패 후에는 대기 없음.
    assert sleeps == [2, 4]


@pytest.mark.asyncio
async def test_uses_full_backoff_sequence_2_4_8():
    procs = [_FakeProcess(returncode=1, stderr=b"x") for _ in range(4)]
    sleeps, sleeper = _sleep_recorder()

    with pytest.raises(llm.LLMError):
        await llm.call_claude_cli(
            "p",
            create_subprocess=_factory(procs),
            sleep=sleeper,
            max_attempts=4,
            backoff_seconds=(2, 4, 8),
        )

    assert sleeps == [2, 4, 8]


def test_defaults_come_from_config_constants():
    """PRD §14: 120s 타임아웃, 최대 3회, 2/4/8s 백오프가 기본값이어야 한다."""
    from rss_wiki import config

    kwdefaults = llm.call_claude_cli.__kwdefaults__
    assert kwdefaults is not None
    assert kwdefaults["timeout_seconds"] == config.LLM_SUBPROCESS_TIMEOUT_SECONDS == 120
    assert kwdefaults["max_attempts"] == config.LLM_MAX_ATTEMPTS == 3
    assert kwdefaults["backoff_seconds"] == config.LLM_BACKOFF_SECONDS == (2, 4, 8)


# -----------------------------------------------------------------------------
# JSON 파싱 폴백 체인 (PRD §7.2)
# -----------------------------------------------------------------------------


def test_parse_json_step1_direct_strip():
    """1단계: strip 후 json.loads 로 바로 파싱."""
    raw = '  {"summary":"ok","is_new_category":false}\n'
    assert llm.parse_json_with_fallbacks(raw) == {
        "summary": "ok",
        "is_new_category": False,
    }


def test_parse_json_step2_strips_json_code_fence():
    """2단계: ```json ... ``` 코드펜스 제거 후 파싱."""
    raw = '```json\n{"a": 1, "b": [2, 3]}\n```\n'
    assert llm.parse_json_with_fallbacks(raw) == {"a": 1, "b": [2, 3]}


def test_parse_json_step2_strips_plain_code_fence():
    """2단계: 언어 태그 없는 ``` 코드펜스도 허용."""
    raw = '```\n{"a": 1}\n```'
    assert llm.parse_json_with_fallbacks(raw) == {"a": 1}


def test_parse_json_step3_extracts_first_json_object():
    """3단계: 앞뒤 설명문이 섞여 있으면 정규식으로 첫 JSON 객체 추출."""
    raw = '여기 응답입니다:\n{"summary": "hi", "ok": true}\n끝.'
    assert llm.parse_json_with_fallbacks(raw) == {"summary": "hi", "ok": True}


def test_parse_json_raises_when_all_fallbacks_fail():
    """JSON-like 블록조차 없으면 LLMJSONParseError."""
    with pytest.raises(llm.LLMJSONParseError):
        llm.parse_json_with_fallbacks("그냥 평문입니다")


def test_parse_json_raises_on_empty_output():
    with pytest.raises(llm.LLMJSONParseError):
        llm.parse_json_with_fallbacks("")


# -----------------------------------------------------------------------------
# call_claude_cli_json: 파싱 실패 시 프롬프트 덧붙여 1회 재호출 (PRD §7.2 4단계)
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_call_claude_cli_json_returns_parsed_on_first_try():
    factory = _factory([_FakeProcess(returncode=0, stdout=b'{"k": 1}')])
    _, sleeper = _sleep_recorder()

    data = await llm.call_claude_cli_json(
        "prompt", create_subprocess=factory, sleep=sleeper
    )

    assert data == {"k": 1}
    assert len(factory.calls) == 1  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_call_claude_cli_json_retries_once_with_appended_instruction():
    """첫 응답이 파싱 불가 → 프롬프트에 재시도 지시문을 붙여 1회만 재호출."""
    procs = [
        _FakeProcess(
            returncode=0,
            stdout="죄송합니다, JSON이 아닙니다.".encode("utf-8"),
        ),
        _FakeProcess(returncode=0, stdout=b'{"k": 2}'),
    ]
    factory = _factory(procs)
    _, sleeper = _sleep_recorder()

    data = await llm.call_claude_cli_json(
        "base prompt", create_subprocess=factory, sleep=sleeper
    )

    assert data == {"k": 2}
    # 정확히 2번 호출, 2번째는 RETRY_INSTRUCTION 이 붙은 프롬프트.
    assert len(factory.calls) == 2  # type: ignore[attr-defined]
    assert procs[0].stdin_received == b"base prompt"
    assert procs[1].stdin_received == (
        "base prompt" + llm.RETRY_INSTRUCTION
    ).encode("utf-8")


@pytest.mark.asyncio
async def test_call_claude_cli_json_raises_when_retry_also_unparseable():
    """재호출 응답도 파싱 실패 → LLMJSONParseError."""
    procs = [
        _FakeProcess(returncode=0, stdout=b"not json"),
        _FakeProcess(returncode=0, stdout=b"still not json"),
    ]
    factory = _factory(procs)
    _, sleeper = _sleep_recorder()

    with pytest.raises(llm.LLMJSONParseError):
        await llm.call_claude_cli_json(
            "p", create_subprocess=factory, sleep=sleeper
        )

    # 재호출은 딱 1회만 — 3회 이상 루프 금지.
    assert len(factory.calls) == 2  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_call_claude_cli_json_does_not_retry_on_fence_or_embedded_json():
    """코드펜스/임베디드 JSON 은 폴백 체인 내에서 처리 → 재호출 없음."""
    procs = [_FakeProcess(returncode=0, stdout=b"```json\n{\"a\": 3}\n```")]
    factory = _factory(procs)
    _, sleeper = _sleep_recorder()

    data = await llm.call_claude_cli_json(
        "p", create_subprocess=factory, sleep=sleeper
    )

    assert data == {"a": 3}
    assert len(factory.calls) == 1  # type: ignore[attr-defined]
