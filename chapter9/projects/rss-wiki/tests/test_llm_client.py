import subprocess
import pytest
from rss_wiki.llm.client import DEFAULT_TIMEOUT, call_claude, LLMError, LLMTimeoutError


def _make_runner(returncode=0, stdout="", stderr=""):
    def runner(args, stdin_text, timeout):
        return subprocess.CompletedProcess(
            args=args, returncode=returncode, stdout=stdout, stderr=stderr
        )
    return runner


def _make_raising_runner(exc):
    def runner(args, stdin_text, timeout):
        raise exc
    return runner


def test_call_claude_returns_stripped_stdout():
    stub = _make_runner(returncode=0, stdout="hello world\n", stderr="")
    result = call_claude("ping", runner=stub)
    assert result == "hello world"


def test_call_claude_uses_extended_default_timeout():
    captured: dict[str, float] = {}

    def runner(args, stdin_text, timeout):
        captured["timeout"] = timeout
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="ok", stderr="")

    result = call_claude("ping", runner=runner)

    assert result == "ok"
    assert captured["timeout"] == DEFAULT_TIMEOUT
    assert DEFAULT_TIMEOUT > 60.0


def test_call_claude_raises_llm_error_on_nonzero_exit():
    stub = _make_runner(returncode=2, stdout="", stderr="boom")
    with pytest.raises(LLMError) as exc_info:
        call_claude("ping", runner=stub)
    assert "boom" in str(exc_info.value)


def test_call_claude_raises_timeout_error():
    exc = subprocess.TimeoutExpired(cmd=["claude", "-p", "ping"], timeout=0.1)
    stub = _make_raising_runner(exc)
    with pytest.raises(LLMTimeoutError) as exc_info:
        call_claude("ping", timeout=0.1, runner=stub)
    assert isinstance(exc_info.value, LLMError)


def test_call_claude_raises_llm_error_on_empty_output():
    stub = _make_runner(returncode=0, stdout="   \n", stderr="")
    with pytest.raises(LLMError) as exc_info:
        call_claude("ping", runner=stub)
    assert "empty" in str(exc_info.value)
