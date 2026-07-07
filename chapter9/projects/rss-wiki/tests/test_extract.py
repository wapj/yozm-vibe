import pytest

from rss_wiki import extract

ARTICLE = {
    "id": "guid-1",
    "title": "제목",
    "link": "https://example.com/article",
    "published": "2026-07-07T00:00:00Z",
    "description": "RSS 요약 본문",
    "content": "RSS 전체 본문",
}


def test_extract_body_uses_original_on_success():
    result = extract.extract_body(
        ARTICLE,
        fetch=lambda url: "<html>원문 HTML</html>",
        extract=lambda html: "원문에서 추출한 본문",
    )

    assert result == {"body": "원문에서 추출한 본문", "source": "original"}


def test_extract_body_falls_back_to_rss_description_when_fetch_fails():
    def _raise_fetch(url):
        raise ConnectionError("네트워크 오류")

    result = extract.extract_body(
        ARTICLE,
        fetch=_raise_fetch,
        extract=lambda html: "사용되지 않음",
    )

    assert result == {"body": "RSS 요약 본문", "source": "rss"}


def test_extract_body_falls_back_to_rss_when_extract_returns_empty():
    result = extract.extract_body(
        ARTICLE,
        fetch=lambda url: "<html>본문 없는 페이지</html>",
        extract=lambda html: "",
    )

    assert result == {"body": "RSS 요약 본문", "source": "rss"}


def test_extract_body_raises_when_no_rss_body_available():
    article = {**ARTICLE, "description": None, "content": None}

    with pytest.raises(extract.ArticleExtractionError):
        extract.extract_body(
            article,
            fetch=lambda url: "<html></html>",
            extract=lambda html: "",
        )


def test_extract_body_falls_back_to_content_when_description_missing():
    article = {**ARTICLE, "description": None}

    def _raise_fetch(url):
        raise TimeoutError("타임아웃")

    result = extract.extract_body(article, fetch=_raise_fetch, extract=lambda html: "사용되지 않음")

    assert result == {"body": "RSS 전체 본문", "source": "rss"}
