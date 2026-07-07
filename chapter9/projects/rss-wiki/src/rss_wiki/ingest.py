"""피드 파싱과 새 글 판별의 순수 로직. state.json 로드/저장은 store.py가 담당한다."""

from __future__ import annotations


class FeedParseError(Exception):
    """피드를 파싱할 수 없음(feedparser bozo 등). 호출자는 이 피드를 건너뛴다."""


def _default_parse(url: str):
    import feedparser

    return feedparser.parse(url)


def _entry_id(entry: dict) -> str:
    """항목의 GUID가 있으면 그것을, 없으면 링크 URL을 식별자로 채택한다(PRD 5절)."""
    guid = entry.get("id") or entry.get("guid")
    return guid if guid else entry.get("link", "")


def _to_article(entry: dict) -> dict:
    return {
        "id": _entry_id(entry),
        "title": entry.get("title"),
        "link": entry.get("link"),
        "published": entry.get("published"),
        "description": entry.get("description") or entry.get("summary"),
        "content": entry.get("content"),
    }


def select_new_articles(
    feed: dict,
    state: dict,
    *,
    limit: int,
    parse=_default_parse,
) -> list[dict]:
    """단일 피드에서 처리 대상 새 글 목록을 반환한다.

    피드의 어떤 항목도 state["processed"]에 없으면 첫 수집으로 보고
    (피드가 최신 글을 앞에 두는 통상적인 순서를 그대로 따라) 최신 limit개까지만
    반환한다. 첫 수집이 아니면 아직 처리되지 않은 글을 전부 반환한다.
    """
    parsed = parse(feed["url"])
    entries = parsed.get("entries", [])
    if parsed.get("bozo") and not entries:
        raise FeedParseError(f"피드를 파싱할 수 없습니다: {feed['url']}")

    processed = state.get("processed", {})
    is_first_ingest = not any(_entry_id(entry) in processed for entry in entries)

    new_articles = [
        _to_article(entry) for entry in entries if _entry_id(entry) not in processed
    ]

    if is_first_ingest:
        return new_articles[:limit]
    return new_articles
