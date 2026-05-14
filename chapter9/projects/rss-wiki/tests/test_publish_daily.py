import pytest

from rss_wiki.publish.daily import (
    ArticleCard,
    CategorySection,
    FailingFeed,
    build_daily_magazine,
)


def _make_section(name: str, trend: str, articles=None) -> CategorySection:
    if articles is None:
        articles = [ArticleCard(title="기본 제목", url="https://example.com/x", summary="기본 요약")]
    return CategorySection(name=name, trend_summary=trend, articles=articles)


def test_build_daily_magazine_includes_date():
    result = build_daily_magazine(
        date="2026-05-05",
        sections=[_make_section("AI", "AI 트렌드")],
    )
    assert "2026-05-05" in result
    h1_lines = [l for l in result.splitlines() if l.startswith("# ")]
    assert len(h1_lines) >= 1


def test_build_daily_magazine_renders_sections_in_order():
    sections = [
        _make_section("AI", "트렌드A"),
        _make_section("Python", "트렌드B"),
    ]
    result = build_daily_magazine(date="2026-05-05", sections=sections)
    assert "AI" in result
    assert "Python" in result
    assert result.index("AI") < result.index("Python")
    h2_lines = [l for l in result.splitlines() if l.startswith("## ")]
    assert len(h2_lines) >= 2


def test_build_daily_magazine_renders_article_card():
    article = ArticleCard(
        title="제목",
        url="https://example.com/a",
        summary="요약본",
        tags=["ai", "python"],
    )
    section = CategorySection(name="테스트", trend_summary="트렌드", articles=[article])
    result = build_daily_magazine(date="2026-05-05", sections=[section])
    assert "제목" in result
    assert "https://example.com/a" in result
    assert "요약본" in result
    assert "#ai" in result
    assert "#python" in result


def test_build_daily_magazine_omits_empty_tag_line():
    article = ArticleCard(title="제목", url="https://example.com/b", summary="요약", tags=())
    section = CategorySection(name="테스트", trend_summary="트렌드", articles=[article])
    result = build_daily_magazine(date="2026-05-05", sections=[section])
    # 헤딩(# ## ###) 이외에 # 뒤에 비공백이 오는 패턴이 없어야 한다
    non_heading_hash = [
        l for l in result.splitlines()
        if "#" in l and not l.lstrip().startswith("#")
    ]
    assert non_heading_hash == [], f"태그 줄이 출력되었습니다: {non_heading_hash}"


def test_build_daily_magazine_appends_failing_feeds():
    section = _make_section("AI", "트렌드")
    feed = FailingFeed(name="블로그A", url="https://a.example.com/rss", consecutive_failures=7)
    result = build_daily_magazine(date="2026-05-05", sections=[section], failing_feeds=[feed])
    assert "블로그A" in result
    assert "https://a.example.com/rss" in result
    assert "7" in result
    assert "장애" in result
    assert "---" in result


def test_build_daily_magazine_omits_failing_feeds_when_empty():
    section = _make_section("AI", "트렌드")
    result = build_daily_magazine(date="2026-05-05", sections=[section], failing_feeds=())
    assert "장애 피드" not in result
    assert "---" not in result


def test_build_daily_magazine_raises_on_empty_sections():
    with pytest.raises(ValueError):
        build_daily_magazine(date="2026-05-05", sections=[])
