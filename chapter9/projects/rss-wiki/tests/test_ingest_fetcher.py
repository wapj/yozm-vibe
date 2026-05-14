import httpx
import pytest

from rss_wiki.ingest.fetcher import FeedEntry, FetchError, fetch_feed

RSS_TWO_ITEMS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <link>https://example.com</link>
    <item>
      <title>Article One</title>
      <link>https://example.com/article-1</link>
      <pubDate>Mon, 05 May 2026 10:00:00 +0000</pubDate>
      <description>Summary one</description>
    </item>
    <item>
      <title>Article Two</title>
      <link>https://example.com/article-2</link>
      <pubDate>Mon, 05 May 2026 11:00:00 +0000</pubDate>
      <description>Summary two</description>
    </item>
  </channel>
</rss>"""

RSS_EMPTY = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Empty Feed</title>
    <link>https://example.com</link>
  </channel>
</rss>"""


def make_mock_transport(content: bytes, status_code: int = 200):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, content=content)

    return httpx.MockTransport(handler)


def test_fetch_feed_normal_returns_entries():
    transport = make_mock_transport(RSS_TWO_ITEMS)
    client = httpx.Client(transport=transport)
    entries = fetch_feed("https://example.com/feed.rss", client=client)

    assert len(entries) == 2
    assert isinstance(entries[0], FeedEntry)

    assert entries[0].url == "https://example.com/article-1"
    assert entries[0].title == "Article One"
    assert entries[0].published_at == "Mon, 05 May 2026 10:00:00 +0000"
    assert entries[0].summary == "Summary one"

    assert entries[1].url == "https://example.com/article-2"
    assert entries[1].title == "Article Two"
    assert entries[1].published_at == "Mon, 05 May 2026 11:00:00 +0000"
    assert entries[1].summary == "Summary two"


def test_fetch_feed_empty_returns_empty_list():
    transport = make_mock_transport(RSS_EMPTY)
    client = httpx.Client(transport=transport)
    entries = fetch_feed("https://example.com/feed.rss", client=client)
    assert entries == []


def test_fetch_feed_http_error_raises_fetch_error():
    transport = make_mock_transport(b"Internal Server Error", status_code=500)
    client = httpx.Client(transport=transport)
    with pytest.raises(FetchError) as ei:
        fetch_feed("https://example.com/feed.rss", client=client)
    assert isinstance(ei.value.__cause__, httpx.HTTPStatusError)
    assert "https://example.com/feed.rss" in str(ei.value)


def test_fetch_feed_network_error_raises_fetch_error():
    def error_handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    transport = httpx.MockTransport(error_handler)
    client = httpx.Client(transport=transport)
    with pytest.raises(FetchError) as ei:
        fetch_feed("https://example.com/feed.rss", client=client)
    assert isinstance(ei.value.__cause__, httpx.ConnectError)
