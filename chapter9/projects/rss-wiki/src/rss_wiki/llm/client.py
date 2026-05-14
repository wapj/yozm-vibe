from __future__ import annotations

import subprocess
from typing import Callable

DEFAULT_TIMEOUT: float = 300.0


class LLMError(Exception):
    pass


class LLMTimeoutError(LLMError):
    pass


def _default_runner(
    args: list[str], stdin_text: str, timeout: float
) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def call_claude(
    prompt: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
    runner: Callable[[list[str], str, float], subprocess.CompletedProcess] | None = None,
) -> str:
    _runner = runner if runner is not None else _default_runner
    args = ["claude", "-p", prompt]
    try:
        result = _runner(args, "", timeout)
    except subprocess.TimeoutExpired as e:
        raise LLMTimeoutError(f"claude CLI timed out after {timeout}s") from e
    except FileNotFoundError as e:
        raise LLMError("claude CLI binary not found on PATH") from e

    if result.returncode != 0:
        stderr_truncated = (result.stderr or "")[-500:]
        raise LLMError(f"claude CLI failed with exit {result.returncode}: {stderr_truncated}")

    output = result.stdout.strip()
    if not output:
        raise LLMError("claude CLI returned empty output")

    return output
