"""models.py 테스트."""

from rss_wiki.models import (
    Article,
    ArticleContext,
    Category,
    Feed,
    JobLog,
    LLMSummaryResult,
    NewArticleForWiki,
    WikiPage,
)


def test_feed_defaults():
    f = Feed(id=None, url="https://example.com/feed")
    assert f.is_active is True
    assert f.consecutive_failures == 0
    assert f.title is None


def test_category_defaults():
    c = Category(id=None, name="AI")
    assert c.parent_id is None
    assert c.is_user_edited is False
    assert c.merged_into_id is None


def test_article_defaults():
    a = Article(id=None, feed_id=1, url="https://example.com/1", title="Test")
    assert a.status == "ok"
    assert a.primary_category_id is None


def test_wiki_page_defaults():
    wp = WikiPage(id=None, category_id=1)
    assert wp.content_markdown == ""
    assert wp.has_unread_updates is False


def test_llm_summary_result():
    r = LLMSummaryResult(summary="요약", category_name="AI", is_new_category=True, language_detected="ko")
    assert r.summary == "요약"
    assert r.is_new_category is True


def test_article_context():
    ac = ArticleContext(title="제목", published_at="2024-01-01", one_line="한 줄 요약")
    assert ac.one_line == "한 줄 요약"


def test_new_article_for_wiki():
    na = NewArticleForWiki(title="제목", url="https://example.com", llm_summary="요약", published_at="2024-01-01")
    assert na.url == "https://example.com"
