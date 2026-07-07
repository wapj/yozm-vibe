"""원문 HTML fetch와 본문 추출의 순수 로직. 실패 시 RSS 본문으로 대체한다."""

from __future__ import annotations

DEFAULT_TIMEOUT = 10.0


class ArticleExtractionError(Exception):
    """원문 추출과 RSS 대체 본문 모두 확보하지 못함. 호출자는 이 글을 건너뛴다."""


def _default_fetch(url: str) -> str:
    import httpx

    response = httpx.get(url, timeout=DEFAULT_TIMEOUT, follow_redirects=True)
    response.raise_for_status()
    return response.text


def _default_extract(html: str) -> str | None:
    import trafilatura

    return trafilatura.extract(html)


def extract_body(article: dict, *, fetch=_default_fetch, extract=_default_extract) -> dict:
    """원문 링크의 HTML에서 본문을 추출하고, 실패하면 RSS 본문으로 대체한다(PRD 4.2).

    반환값의 "source"는 본문 출처를 나타낸다: 원문 fetch·추출이 성공하면
    "original", 실패해 RSS description/content로 대체하면 "rss".
    fetch의 타임아웃·상태 코드 실패는 fetch 함수 내부에서 예외로 표현된다고
    가정하고 여기서 잡아 RSS 대체 경로로 전환한다.
    """
    try:
        html = fetch(article["link"])
        body = extract(html)
    except Exception:
        body = None

    if body:
        return {"body": body, "source": "original"}

    fallback = article.get("description") or article.get("content")
    if fallback:
        return {"body": fallback, "source": "rss"}

    raise ArticleExtractionError(f"본문을 확보할 수 없습니다: {article.get('link')}")
