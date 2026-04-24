"""엔드투엔드 스모크: `uv run uvicorn rss_wiki.main:app` 기동 + 로그 검증.

PRD §14.2 실행 명령이 실제로 살아 있는지, uvicorn 표준 기동 로그가 찍히는지,
GET / 가 200 을 돌려주는지까지 하나의 서브프로세스 수명 안에서 확인한다.
"""

from __future__ import annotations

import shutil
import socket
import subprocess
import time
from pathlib import Path

import httpx
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BOOT_TIMEOUT_SECONDS = 60.0


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_http_ready(url: str, timeout: float) -> httpx.Response:
    deadline = time.monotonic() + timeout
    last_exc: Exception | None = None
    while time.monotonic() < deadline:
        try:
            return httpx.get(url, timeout=2.0)
        except httpx.TransportError as exc:
            last_exc = exc
            time.sleep(0.25)
    raise AssertionError(
        f"uvicorn 서버가 {timeout}s 안에 응답하지 않았다: {last_exc!r}"
    )


@pytest.mark.skipif(shutil.which("uv") is None, reason="uv CLI 필요")
def test_uvicorn_boot_logs_startup_complete() -> None:
    port = _find_free_port()
    proc = subprocess.Popen(
        [
            "uv",
            "run",
            "uvicorn",
            "rss_wiki.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--no-access-log",
        ],
        cwd=str(PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        resp = _wait_http_ready(
            f"http://127.0.0.1:{port}/", timeout=BOOT_TIMEOUT_SECONDS
        )
        assert resp.status_code == 200
        assert "RSS Wiki" in resp.text
    finally:
        proc.terminate()
        try:
            output, _ = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            output, _ = proc.communicate(timeout=5)

    assert "Application startup complete" in output, (
        f"uvicorn 기동 완료 로그가 없다. 전체 출력:\n{output}"
    )
    assert f"127.0.0.1:{port}" in output, (
        f"기동 바인딩 로그({port})가 없다. 전체 출력:\n{output}"
    )
