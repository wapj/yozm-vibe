import pytest

from rss_wiki import feeds


def _fake_validate_ok(url):
    return {"title": "예제 피드"}


def _fake_validate_no_entries(url):
    raise feeds.FeedValidationError(f"항목이 없습니다: {url}")


def _fake_now():
    return "2026-07-07T00:00:00Z"


def test_add_feed_registers_with_validated_title():
    result = feeds.add_feed(
        [],
        "https://example.com/rss",
        validate=_fake_validate_ok,
        now=_fake_now,
    )

    assert result == [
        {"name": "예제 피드", "url": "https://example.com/rss", "added_at": "2026-07-07T00:00:00Z"}
    ]


def test_add_feed_falls_back_to_url_when_title_missing():
    result = feeds.add_feed(
        [],
        "https://example.com/rss",
        validate=lambda url: {"title": None},
        now=_fake_now,
    )

    assert result[0]["name"] == "https://example.com/rss"


def test_add_feed_rejects_feed_without_entries():
    with pytest.raises(feeds.FeedValidationError):
        feeds.add_feed([], "https://example.com/empty", validate=_fake_validate_no_entries, now=_fake_now)


def test_add_feed_rejects_duplicate_url():
    existing = [{"name": "예제 피드", "url": "https://example.com/rss", "added_at": "2026-07-07T00:00:00Z"}]

    with pytest.raises(feeds.DuplicateFeedError):
        feeds.add_feed(existing, "https://example.com/rss", validate=_fake_validate_ok, now=_fake_now)


def test_remove_feed_by_url():
    existing = [{"name": "예제 피드", "url": "https://example.com/rss", "added_at": "2026-07-07T00:00:00Z"}]

    result = feeds.remove_feed(existing, "https://example.com/rss")

    assert result == []


def test_remove_feed_by_name():
    existing = [{"name": "예제 피드", "url": "https://example.com/rss", "added_at": "2026-07-07T00:00:00Z"}]

    result = feeds.remove_feed(existing, "예제 피드")

    assert result == []


def test_remove_feed_raises_when_not_found():
    with pytest.raises(feeds.FeedNotFoundError):
        feeds.remove_feed([], "https://missing.example")


def test_list_feeds_returns_registered_feeds():
    existing = [{"name": "예제 피드", "url": "https://example.com/rss", "added_at": "2026-07-07T00:00:00Z"}]

    assert feeds.list_feeds(existing) == existing
