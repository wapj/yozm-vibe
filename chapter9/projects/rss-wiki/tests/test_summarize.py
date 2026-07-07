import asyncio
import subprocess

import pytest

from rss_wiki import summarize

ARTICLE = {
    "id": "guid-1",
    "title": "원문 제목",
    "link": "https://example.com/article",
    "published": "2026-07-07T00:00:00Z",
    "description": "RSS 요약 본문",
    "content": None,
}
BODY = "원문 본문 텍스트입니다."


def test_summarize_article_returns_summary_and_meta():
    result = summarize.summarize_article(
        ARTICLE, BODY, feed_name="예제 피드", run=lambda prompt: "요약 텍스트"
    )

    assert result == {
        "summary": "요약 텍스트",
        "title": "원문 제목",
        "link": "https://example.com/article",
        "published": "2026-07-07T00:00:00Z",
        "feed_name": "예제 피드",
    }


def test_summarize_article_prompt_includes_body_and_korean_instruction():
    captured = {}

    def _run(prompt):
        captured["prompt"] = prompt
        return "요약 텍스트"

    summarize.summarize_article(ARTICLE, BODY, feed_name="예제 피드", run=_run)

    assert BODY in captured["prompt"]
    assert "한국어" in captured["prompt"]


def test_summarize_article_raises_when_claude_not_installed():
    def _run(prompt):
        raise FileNotFoundError("claude: command not found")

    with pytest.raises(summarize.SummarizeError):
        summarize.summarize_article(ARTICLE, BODY, feed_name="예제 피드", run=_run)


def test_summarize_article_raises_when_claude_exits_nonzero():
    def _run(prompt):
        raise subprocess.CalledProcessError(1, "claude")

    with pytest.raises(summarize.SummarizeError):
        summarize.summarize_article(ARTICLE, BODY, feed_name="예제 피드", run=_run)


def test_summarize_article_async_returns_summary_and_meta():
    async def _run(prompt):
        return "요약 텍스트"

    result = asyncio.run(
        summarize.summarize_article_async(
            ARTICLE, BODY, feed_name="예제 피드", run=_run
        )
    )

    assert result == {
        "summary": "요약 텍스트",
        "title": "원문 제목",
        "link": "https://example.com/article",
        "published": "2026-07-07T00:00:00Z",
        "feed_name": "예제 피드",
    }


def test_summarize_article_async_raises_when_claude_not_installed():
    async def _run(prompt):
        raise FileNotFoundError("claude: command not found")

    with pytest.raises(summarize.SummarizeError):
        asyncio.run(
            summarize.summarize_article_async(
                ARTICLE, BODY, feed_name="예제 피드", run=_run
            )
        )


def test_summarize_article_async_raises_when_claude_exits_nonzero():
    async def _run(prompt):
        raise subprocess.CalledProcessError(1, "claude")

    with pytest.raises(summarize.SummarizeError):
        asyncio.run(
            summarize.summarize_article_async(
                ARTICLE, BODY, feed_name="예제 피드", run=_run
            )
        )


class _FakeAsyncProcess:
    def __init__(self, returncode, stdout=b"", stderr=b""):
        self.returncode = returncode
        self._stdout = stdout
        self._stderr = stderr

    async def communicate(self):
        return self._stdout, self._stderr


def test_default_run_async_raises_called_process_error_on_nonzero_exit(monkeypatch):
    async def fake_create_subprocess_exec(*args, **kwargs):
        return _FakeAsyncProcess(returncode=1, stdout=b"", stderr=b"failure reason")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    with pytest.raises(subprocess.CalledProcessError) as exc_info:
        asyncio.run(summarize._default_run_async("프롬프트"))

    assert exc_info.value.returncode == 1


def test_default_run_async_returns_decoded_stdout_on_success(monkeypatch):
    async def fake_create_subprocess_exec(*args, **kwargs):
        return _FakeAsyncProcess(returncode=0, stdout="요약 결과 텍스트".encode())

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    result = asyncio.run(summarize._default_run_async("프롬프트"))

    assert result == "요약 결과 텍스트"
