from __future__ import annotations

import logging
import pytest

from rss_wiki.llm.client import LLMError
from rss_wiki.llm.prompts import PromptParseError
from rss_wiki.storage.db import get_connection, init_db
from rss_wiki.storage.repo import (
    get_article_by_url_hash,
    insert_article,
    upsert_category,
    upsert_feed,
)
from rss_wiki.pipeline.llm import AnalyzeResult, AnalyzeStats, analyze_articles


@pytest.fixture
def conn(tmp_path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    c = get_connection(db_path)
    yield c
    c.close()


def _make_feed(conn):
    return upsert_feed(conn, "TestFeed", "https://example.com/rss")


def _make_article(conn, feed_id, *, url_suffix="1", content="본문", summary=None):
    url = f"https://example.com/article/{url_suffix}"
    url_hash = f"hash_{url_suffix}"
    title = f"Article {url_suffix}"
    return insert_article(
        conn,
        feed_id=feed_id,
        url=url,
        url_hash=url_hash,
        title=title,
        title_hash=f"th_{url_suffix}",
        published_at="2026-05-05T00:00:00",
        content=content,
        summary=summary,
    )


def test_analyze_articles_returns_empty_for_empty_input(conn):
    calls = []
    runner = lambda p: calls.append(p) or '{"summary":"x","category":"A","tags":[]}'
    result = analyze_articles(conn=conn, article_ids=[], runner=runner)
    assert result == AnalyzeResult(
        stats=AnalyzeStats(0, 0, 0, 0, 0),
        trends={},
        analyzed_article_ids=(),
    )
    assert len(calls) == 0


def test_analyze_articles_persists_summary_category_tags(conn):
    feed_id = _make_feed(conn)
    article_id = _make_article(conn, feed_id, url_suffix="p1", content="본문", summary=None)

    runner = lambda p: '{"summary":"요약","category":"AI","tags":["llm","claude"]}'
    result = analyze_articles(conn=conn, article_ids=[article_id], runner=runner)

    # (e) stats
    assert result.stats.articles_analyzed == 1
    assert result.stats.articles_failed == 0

    # (a) summary updated
    row = get_article_by_url_hash(conn, "hash_p1")
    assert row["summary"] == "요약"

    # (b) category exists
    cat_count = conn.execute(
        "SELECT COUNT(*) FROM categories WHERE name = 'ai'"
    ).fetchone()[0]
    assert cat_count == 1

    # (c) tags exist
    tags = [r["name"] for r in conn.execute("SELECT name FROM tags").fetchall()]
    assert "llm" in tags
    assert "claude" in tags

    # (d) links exist
    ac = conn.execute(
        "SELECT COUNT(*) FROM article_categories WHERE article_id = ?", (article_id,)
    ).fetchone()[0]
    assert ac == 1

    at = conn.execute(
        "SELECT COUNT(*) FROM article_tags WHERE article_id = ?", (article_id,)
    ).fetchone()[0]
    assert at == 2


def test_analyze_articles_passes_existing_categories_to_prompt(conn):
    feed_id = _make_feed(conn)
    upsert_category(conn, "AI")
    article_id = _make_article(conn, feed_id, url_suffix="ec1")

    captured = []
    def runner(prompt):
        captured.append(prompt)
        return '{"summary":"요약","category":"AI","tags":[]}'

    analyze_articles(conn=conn, article_ids=[article_id], runner=runner)

    assert len(captured) >= 1
    first_prompt = captured[0]
    assert "기존 카테고리 목록:" in first_prompt
    assert "- ai" in first_prompt


def test_analyze_articles_groups_by_category_and_builds_trends(conn):
    feed_id = _make_feed(conn)
    id1 = _make_article(conn, feed_id, url_suffix="g1")
    id2 = _make_article(conn, feed_id, url_suffix="g2")
    id3 = _make_article(conn, feed_id, url_suffix="g3")

    article_responses = [
        '{"summary":"요약1","category":"AI","tags":[]}',
        '{"summary":"요약2","category":"AI","tags":[]}',
        '{"summary":"요약3","category":"DevOps","tags":[]}',
    ]
    trend_responses = [
        "AI 트렌드 요약 단락.",
        "DevOps 트렌드 요약 단락.",
    ]
    side_effects = article_responses + trend_responses
    idx = [0]

    def runner(prompt):
        val = side_effects[idx[0]]
        idx[0] += 1
        return val

    result = analyze_articles(conn=conn, article_ids=[id1, id2, id3], runner=runner)

    assert set(result.trends.keys()) == {"ai", "devops"}
    assert result.trends["ai"] == "AI 트렌드 요약 단락."
    assert result.trends["devops"] == "DevOps 트렌드 요약 단락."
    assert result.stats.categories_with_trend == 2
    assert len(result.analyzed_article_ids) == 3


def test_analyze_articles_isolates_article_llm_failure(conn, caplog):
    feed_id = _make_feed(conn)
    id1 = _make_article(conn, feed_id, url_suffix="f1")
    id2 = _make_article(conn, feed_id, url_suffix="f2")

    side_effects: list = [
        LLMError("boom"),
        '{"summary":"요약","category":"AI","tags":[]}',
        "AI 트렌드 단락.",
    ]
    idx = [0]

    def runner(prompt):
        val = side_effects[idx[0]]
        idx[0] += 1
        if isinstance(val, Exception):
            raise val
        return val

    with caplog.at_level(logging.WARNING):
        result = analyze_articles(conn=conn, article_ids=[id1, id2], runner=runner)

    assert result.stats.articles_analyzed == 1
    assert result.stats.articles_failed == 1
    assert len(result.analyzed_article_ids) == 1
    assert str(id1) in caplog.text


def test_analyze_articles_isolates_trend_failure(conn, caplog):
    feed_id = _make_feed(conn)
    article_id = _make_article(conn, feed_id, url_suffix="tf1")

    side_effects: list = [
        '{"summary":"요약","category":"AI","tags":[]}',
        PromptParseError("bad"),
    ]
    idx = [0]

    def runner(prompt):
        val = side_effects[idx[0]]
        idx[0] += 1
        if isinstance(val, Exception):
            raise val
        return val

    with caplog.at_level(logging.WARNING):
        result = analyze_articles(conn=conn, article_ids=[article_id], runner=runner)

    assert result.stats.articles_analyzed == 1
    assert result.stats.categories_with_trend == 0
    assert result.stats.trends_failed == 1
    assert result.trends == {}
    assert "ai" in caplog.text


def test_analyze_articles_skips_missing_ids(conn):
    calls = []
    runner = lambda p: calls.append(p) or '{"summary":"x","category":"A","tags":[]}'
    result = analyze_articles(conn=conn, article_ids=[9999], runner=runner)
    assert result.stats.articles_total == 0
    assert len(calls) == 0
