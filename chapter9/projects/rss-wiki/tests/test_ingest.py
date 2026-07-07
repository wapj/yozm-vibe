import pytest

from rss_wiki import ingest

FEED = {"name": "예제 피드", "url": "https://example.com/rss", "added_at": "2026-07-07T00:00:00Z"}


def _entry(**overrides):
    entry = {
        "id": None,
        "title": "제목",
        "link": "https://example.com/article",
        "published": "2026-07-07T00:00:00Z",
        "description": "요약",
    }
    entry.update(overrides)
    return entry


def _fake_parse(entries, bozo=0):
    def parse(url):
        return {"bozo": bozo, "entries": entries}

    return parse


def test_first_ingest_limits_to_latest_n_in_feed_order():
    entries = [
        _entry(id="guid-1", link="https://example.com/1"),
        _entry(id="guid-2", link="https://example.com/2"),
        _entry(id="guid-3", link="https://example.com/3"),
    ]

    result = ingest.select_new_articles(FEED, {"processed": {}}, limit=2, parse=_fake_parse(entries))

    assert [a["id"] for a in result] == ["guid-1", "guid-2"]


def test_skips_already_processed_by_guid_and_by_url():
    entries = [
        _entry(id="guid-1", link="https://example.com/1"),
        _entry(id=None, link="https://example.com/2"),
        _entry(id="guid-3", link="https://example.com/3"),
    ]
    state = {
        "processed": {
            "guid-1": {"processed_at": "2026-07-06T00:00:00Z", "status": "ok"},
            "https://example.com/2": {"processed_at": "2026-07-06T00:00:00Z", "status": "ok"},
        }
    }

    result = ingest.select_new_articles(FEED, state, limit=10, parse=_fake_parse(entries))

    assert [a["id"] for a in result] == ["guid-3"]


def test_uses_link_as_id_when_guid_missing():
    entries = [_entry(id=None, link="https://example.com/no-guid")]

    result = ingest.select_new_articles(FEED, {"processed": {}}, limit=10, parse=_fake_parse(entries))

    assert result[0]["id"] == "https://example.com/no-guid"


def test_returns_all_unprocessed_when_not_first_ingest():
    entries = [
        _entry(id="guid-1", link="https://example.com/1"),
        _entry(id="guid-2", link="https://example.com/2"),
        _entry(id="guid-3", link="https://example.com/3"),
    ]
    state = {"processed": {"guid-1": {"processed_at": "2026-07-06T00:00:00Z", "status": "ok"}}}

    result = ingest.select_new_articles(FEED, state, limit=1, parse=_fake_parse(entries))

    assert [a["id"] for a in result] == ["guid-2", "guid-3"]


def test_raises_feed_parse_error_when_bozo_and_no_entries():
    with pytest.raises(ingest.FeedParseError):
        ingest.select_new_articles(FEED, {"processed": {}}, limit=10, parse=_fake_parse([], bozo=1))


def test_article_contains_all_meta_keys():
    entries = [_entry(id="guid-1", link="https://example.com/1")]

    result = ingest.select_new_articles(FEED, {"processed": {}}, limit=10, parse=_fake_parse(entries))

    assert set(result[0].keys()) == {"id", "title", "link", "published", "description", "content"}


def test_description_falls_back_to_summary_when_missing():
    entries = [_entry(id="guid-1", link="https://example.com/1")]
    del entries[0]["description"]
    entries[0]["summary"] = "요약 대체 텍스트"

    result = ingest.select_new_articles(FEED, {"processed": {}}, limit=10, parse=_fake_parse(entries))

    assert result[0]["description"] == "요약 대체 텍스트"


def test_content_field_maps_from_entry_content():
    entries = [_entry(id="guid-1", link="https://example.com/1", content="본문 전체 텍스트")]

    result = ingest.select_new_articles(FEED, {"processed": {}}, limit=10, parse=_fake_parse(entries))

    assert result[0]["content"] == "본문 전체 텍스트"
