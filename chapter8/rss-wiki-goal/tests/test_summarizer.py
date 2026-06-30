"""pipeline/summarizer.py 테스트."""

import pytest
from unittest.mock import AsyncMock, patch

from rss_wiki.pipeline.summarizer import summarize_article


@pytest.fixture
def db_with_feed(db):
    db.execute("INSERT INTO feeds(url) VALUES ('https://example.com/feed')")
    db.commit()
    db.execute(
        "INSERT INTO articles(feed_id, url, title) VALUES (1, 'https://example.com/1', '테스트 글')"
    )
    db.commit()
    return db


@pytest.mark.asyncio
async def test_summarize_article_success(db_with_feed):
    mock_result = {
        "summary": "한국어 요약 내용입니다.",
        "category_name": "AI",
        "is_new_category": True,
        "language_detected": "ko",
    }
    with patch("rss_wiki.pipeline.summarizer.call_llm_json", new=AsyncMock(return_value=mock_result)):
        result = await summarize_article(
            db_with_feed,
            article_id=1,
            title="테스트 글",
            url="https://example.com/1",
            content="본문 내용",
        )

    assert result is not None
    assert result.summary == "한국어 요약 내용입니다."
    assert result.category_name == "AI"
    assert result.is_new_category is True

    # DB에 카테고리 생성 및 글 업데이트 확인
    cat = db_with_feed.execute("SELECT * FROM categories WHERE name='AI'").fetchone()
    assert cat is not None
    article = db_with_feed.execute("SELECT * FROM articles WHERE id=1").fetchone()
    assert article["llm_summary"] == "한국어 요약 내용입니다."
    assert article["primary_category_id"] == cat["id"]


@pytest.mark.asyncio
async def test_summarize_article_llm_fail(db_with_feed):
    with patch("rss_wiki.pipeline.summarizer.call_llm_json", new=AsyncMock(return_value=None)):
        result = await summarize_article(
            db_with_feed, 1, "제목", "https://example.com/1", "본문"
        )
    assert result is None


@pytest.mark.asyncio
async def test_summarize_reuses_existing_category(db_with_feed):
    db_with_feed.execute("INSERT INTO categories(name) VALUES ('AI')")
    db_with_feed.commit()

    mock_result = {
        "summary": "요약",
        "category_name": "AI",
        "is_new_category": False,
        "language_detected": "ko",
    }
    with patch("rss_wiki.pipeline.summarizer.call_llm_json", new=AsyncMock(return_value=mock_result)):
        await summarize_article(db_with_feed, 1, "제목", "https://example.com/1", "본문")

    # 카테고리가 중복 생성되지 않아야 함
    count = db_with_feed.execute("SELECT COUNT(*) as c FROM categories WHERE name='AI'").fetchone()["c"]
    assert count == 1
