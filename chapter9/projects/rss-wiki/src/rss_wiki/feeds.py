"""피드 등록/삭제/목록의 순수 로직. 파일 I/O는 store.py가 담당한다."""

from __future__ import annotations

import datetime


class FeedValidationError(Exception):
    """피드 URL이 유효한 RSS/Atom으로 파싱되지 않거나 항목이 없음."""


class DuplicateFeedError(Exception):
    """동일 URL이 이미 등록되어 있음."""


class FeedNotFoundError(Exception):
    """URL 또는 이름에 해당하는 피드가 없음."""


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _default_validate(url: str) -> dict:
    import feedparser

    parsed = feedparser.parse(url)
    if not parsed.entries:
        raise FeedValidationError(f"피드를 파싱할 수 없거나 항목이 없습니다: {url}")
    return {"title": parsed.feed.get("title") if parsed.feed else None}


def add_feed(
    feeds: list[dict],
    url: str,
    validate=_default_validate,
    now=_now_iso,
) -> list[dict]:
    """유효성 검증을 통과한 피드를 feeds에 추가한 새 리스트를 반환한다."""
    if any(feed["url"] == url for feed in feeds):
        raise DuplicateFeedError(f"이미 등록된 피드입니다: {url}")

    result = validate(url)
    name = result.get("title") or url
    new_feed = {"name": name, "url": url, "added_at": now()}
    return [*feeds, new_feed]


def remove_feed(feeds: list[dict], target: str) -> list[dict]:
    """URL 또는 이름이 target과 일치하는 피드를 제거한 새 리스트를 반환한다."""
    remaining = [feed for feed in feeds if feed["url"] != target and feed["name"] != target]
    if len(remaining) == len(feeds):
        raise FeedNotFoundError(f"일치하는 피드가 없습니다: {target}")
    return remaining


def list_feeds(feeds: list[dict]) -> list[dict]:
    """등록된 피드 목록을 그대로 반환한다."""
    return feeds
