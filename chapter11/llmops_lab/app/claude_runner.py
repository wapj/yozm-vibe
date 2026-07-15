# app/claude_runner.py
import subprocess
import json
import os
import time
from dataclasses import dataclass


@dataclass
class ClaudeResult:
    answer: str
    raw_payload: dict
    duration_ms: float
    cost_usd: float
    model: str


def run_claude(prompt: str) -> ClaudeResult:
    bin_path = os.getenv("CLAUDE_BIN", "claude")
    model = os.getenv("CLAUDE_MODEL", "sonnet")
    timeout = int(os.getenv("CLAUDE_TIMEOUT_SECONDS", "120"))

    started = time.time()
    result = subprocess.run(
        [bin_path, "-p", prompt, "--model", model, "--output-format", "json"],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    duration_ms = (time.time() - started) * 1000

    if result.returncode != 0:
        raise RuntimeError(f"claude failed: {result.stderr}")

    payload = json.loads(result.stdout)
    return ClaudeResult(
        answer=payload.get("result", ""),
        raw_payload=payload,
        duration_ms=duration_ms,
        cost_usd=payload.get("total_cost_usd", 0.0),
        model=model,
    )
