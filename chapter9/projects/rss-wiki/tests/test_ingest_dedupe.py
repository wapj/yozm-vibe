import re
import urllib.parse

from rss_wiki.ingest.dedupe import normalize_url, title_hash, url_hash


def test_normalize_url_strips_utm_params():
    url = "https://example.com/post?utm_source=feed&utm_medium=email&id=42"
    result = normalize_url(url)
    parsed = urllib.parse.urlsplit(result)
    keys = [k for k, _ in urllib.parse.parse_qsl(parsed.query)]
    assert not any(k.startswith("utm_") for k in keys)
    assert "id" in keys


def test_normalize_url_strips_known_tracking_params():
    url = "https://example.com/post?fbclid=abc&gclid=xyz&page=1"
    result = normalize_url(url)
    parsed = urllib.parse.urlsplit(result)
    keys = [k for k, _ in urllib.parse.parse_qsl(parsed.query)]
    assert "fbclid" not in keys
    assert "gclid" not in keys
    assert "page" in keys


def test_normalize_url_lowercases_scheme_and_host_and_drops_fragment():
    url = "HTTPS://Example.COM/Path?a=1#section-2"
    result = normalize_url(url)
    parsed = urllib.parse.urlsplit(result)
    assert parsed.scheme == "https"
    assert parsed.netloc == "example.com"
    assert parsed.fragment == ""
    assert parsed.path == "/Path"


def test_normalize_url_sorts_query_keys():
    url1 = "https://example.com/x?b=2&a=1"
    url2 = "https://example.com/x?a=1&b=2"
    assert normalize_url(url1) == normalize_url(url2)


def test_url_hash_equal_for_tracking_variants():
    base = "https://example.com/article"
    with_utm = "https://example.com/article?utm_source=feed"
    h1 = url_hash(base)
    h2 = url_hash(with_utm)
    assert h1 == h2
    assert len(h1) == 64
    assert re.fullmatch(r"[0-9a-f]{64}", h1)


def test_title_hash_normalizes_whitespace_and_case():
    h1 = title_hash("  Hello World  ")
    h2 = title_hash("hello world")
    assert h1 == h2
    assert len(h1) == 64
    assert re.fullmatch(r"[0-9a-f]{64}", h1)
