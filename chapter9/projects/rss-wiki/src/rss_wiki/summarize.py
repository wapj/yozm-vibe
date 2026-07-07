"""claude CLI 서브프로세스를 호출해 한국어 요약을 생성하는 순수 로직."""

from __future__ import annotations

import asyncio
import subprocess


class SummarizeError(Exception):
    """claude CLI 미설치 또는 비0 종료로 요약을 생성하지 못함. 호출자는 이 글을 건너뛴다."""


def _build_prompt(body: str) -> str:
    return (
        "다음 글을 한국어로 요약해 주세요. 원문의 언어와 무관하게 반드시 한국어로 "
        "작성하고, 요약문 3~5줄과 핵심 포인트 불릿 목록을 포함해 주세요.\n\n"
        f"{body}"
    )


def _default_run(prompt: str) -> str:
    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def summarize_article(article: dict, body: str, *, feed_name: str, run=_default_run) -> dict:
    """article과 본문(body)을 입력받아 한국어 요약과 메타데이터를 반환한다(PRD 4.3).

    feed_name은 article dict에 담기지 않으므로(ingest._to_article) 별도 인자로 받아
    반환 메타에 포함한다. claude 미설치(FileNotFoundError)나 비0 종료
    (subprocess.CalledProcessError)는 SummarizeError로 감싸 올린다.
    """
    prompt = _build_prompt(body)
    try:
        summary = run(prompt)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise SummarizeError(f"claude 요약 생성에 실패했습니다: {exc}") from exc

    return {
        "summary": summary,
        "title": article.get("title"),
        "link": article.get("link"),
        "published": article.get("published"),
        "feed_name": feed_name,
    }


async def _default_run_async(prompt: str) -> str:
    process = await asyncio.create_subprocess_exec(
        "claude",
        "-p",
        prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode != 0:
        raise subprocess.CalledProcessError(
            process.returncode, "claude", output=stdout, stderr=stderr
        )
    return stdout.decode()


async def summarize_article_async(
    article: dict, body: str, *, feed_name: str, run=_default_run_async
) -> dict:
    """summarize_article의 asyncio판. 반환 계약(5키)은 동일하며, 병렬 오케스트레이션의
    단위 실행 함수로 쓰인다(M7 T17에서 세마포어와 함께 배선).
    """
    prompt = _build_prompt(body)
    try:
        summary = await run(prompt)
    except (FileNotFoundError, subprocess.CalledProcessError) as exc:
        raise SummarizeError(f"claude 요약 생성에 실패했습니다: {exc}") from exc

    return {
        "summary": summary,
        "title": article.get("title"),
        "link": article.get("link"),
        "published": article.get("published"),
        "feed_name": feed_name,
    }
