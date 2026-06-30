"""pipeline/rebuilder.py 테스트."""

import pytest
from unittest.mock import AsyncMock, patch

from rss_wiki.pipeline.rebuilder import _apply_token_budget, rebuild_wiki
from rss_wiki.models import ArticleContext, NewArticleForWiki


# ── _apply_token_budget 단위 테스트 ──────────────────────────────────────────

def make_articles(n):
    return [ArticleContext(title=f"제목{i}", published_at="2024-01-01", one_line="한 줄") for i in range(n)]

def make_new(n):
    return [NewArticleForWiki(title=f"신규{i}", url=f"https://example.com/{i}", llm_summary="요약", published_at="2024-01-01") for i in range(n)]


def test_apply_token_budget_no_truncation():
    new = make_new(2)
    existing = make_articles(3)
    result = _apply_token_budget(new, existing, "previous")
    assert len(result) == 3


def test_apply_token_budget_truncates_on_overflow():
    # 매우 긴 previous_wiki로 오버플로우 유도
    new = make_new(1)
    existing = make_articles(10)
    very_long_previous = "x" * 99_900
    result = _apply_token_budget(new, existing, very_long_previous)
    # 5 또는 3 또는 0으로 줄어들어야 함
    assert len(result) <= 5


# ── rebuild_wiki 통합 테스트 ─────────────────────────────────────────────────

@pytest.fixture
def db_with_category_and_articles(db):
    db.execute("INSERT INTO feeds(url) VALUES ('https://example.com/feed')")
    db.commit()
    db.execute("INSERT INTO categories(name) VALUES ('AI')")
    db.commit()
    cat_id = db.execute("SELECT id FROM categories WHERE name='AI'").fetchone()["id"]

    for i in range(3):
        db.execute(
            """INSERT INTO articles(feed_id, url, title, llm_summary, primary_category_id, published_at)
               VALUES (1, ?, ?, ?, ?, '2024-01-0{}')""".format(i + 1),
            (f"https://example.com/{i}", f"제목{i}", f"요약{i}", cat_id),
        )
    db.commit()
    return db, cat_id


@pytest.mark.asyncio
async def test_rebuild_wiki_creates_page(db_with_category_and_articles):
    db, cat_id = db_with_category_and_articles
    article_ids = [r["id"] for r in db.execute("SELECT id FROM articles").fetchall()]
    mock_markdown = "# AI\n\n## 한줄 요약\nAI 관련 내용입니다.\n\n## 핵심 내용\n내용 상세.\n"

    with patch("rss_wiki.pipeline.rebuilder.call_llm_text", new=AsyncMock(return_value=mock_markdown)):
        ok = await rebuild_wiki(db, cat_id, article_ids)

    assert ok is True
    wp = db.execute("SELECT * FROM wiki_pages WHERE category_id=?", (cat_id,)).fetchone()
    assert wp is not None
    assert wp["content_markdown"] == mock_markdown
    assert wp["has_unread_updates"] == 1


@pytest.mark.asyncio
async def test_rebuild_wiki_llm_failure_returns_false(db_with_category_and_articles):
    db, cat_id = db_with_category_and_articles
    with patch("rss_wiki.pipeline.rebuilder.call_llm_text", new=AsyncMock(return_value=None)):
        ok = await rebuild_wiki(db, cat_id, [])
    assert ok is False


@pytest.mark.asyncio
async def test_rebuild_wiki_unknown_category_returns_false(db):
    with patch("rss_wiki.pipeline.rebuilder.call_llm_text", new=AsyncMock(return_value="# Test")):
        ok = await rebuild_wiki(db, 9999, [])
    assert ok is False
