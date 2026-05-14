import httpx

from rss_wiki.ingest.extractor import ExtractError, extract_body
from rss_wiki.ingest.fetcher import FeedEntry

LONG_ARTICLE_HTML = """<!DOCTYPE html>
<html>
<head><title>Test Article</title></head>
<body>
<article>
<h1>Test Article Title</h1>
<p>This is the first paragraph of the article body with enough text to be extracted by trafilatura properly.</p>
<p>This is the second paragraph providing additional content so that the extraction algorithm can recognize this as meaningful article content.</p>
<p>The third paragraph continues the discussion and provides more context to ensure trafilatura identifies this block as the main article body.</p>
<p>Fourth paragraph with even more substantial content to ensure the article extractor works correctly and returns the expected text.</p>
<p>Fifth paragraph: key-body-text-marker here for verification in the test assertion.</p>
</article>
</body>
</html>""".encode("utf-8")


def make_transport(content: bytes, status_code: int = 200):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, content=content)

    return httpx.MockTransport(handler)


def test_extract_body_trafilatura_success_returns_extracted_text():
    transport = make_transport(LONG_ARTICLE_HTML, status_code=200)
    client = httpx.Client(transport=transport)
    entry = FeedEntry(url="https://example.com/article", title="Test", published_at=None, summary=None)

    result = extract_body(entry, client=client)

    assert result is not None
    assert "key-body-text-marker" in result


def test_extract_body_trafilatura_returns_none_falls_back_to_summary(monkeypatch):
    monkeypatch.setattr("rss_wiki.ingest.extractor.trafilatura.extract", lambda *a, **kw: None)
    transport = make_transport(b"<html><body><p>some html</p></body></html>", status_code=200)
    client = httpx.Client(transport=transport)
    entry = FeedEntry(url="https://example.com/article", title="Test", published_at=None, summary="요약 폴백")

    result = extract_body(entry, client=client)

    assert result == "요약 폴백"


def test_extract_body_http_error_falls_back_to_summary():
    transport = make_transport(b"Internal Server Error", status_code=500)
    client = httpx.Client(transport=transport)
    entry = FeedEntry(url="https://example.com/article", title="Test", published_at=None, summary="요약 폴백")

    result = extract_body(entry, client=client)

    assert result == "요약 폴백"


def test_extract_body_both_fail_returns_none():
    transport = make_transport(b"Internal Server Error", status_code=500)
    client = httpx.Client(transport=transport)
    entry = FeedEntry(url="https://example.com/article", title="Test", published_at=None, summary=None)

    result = extract_body(entry, client=client)

    assert result is None
