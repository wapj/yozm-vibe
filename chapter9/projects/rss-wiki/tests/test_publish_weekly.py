import pytest

from rss_wiki.publish.weekly import SourceArticle, build_weekly_magazine
from rss_wiki.publish.daily import FailingFeed


def _base_articles():
    return [
        SourceArticle("제목A", "https://a.example.com"),
        SourceArticle("제목B", "https://b.example.com"),
    ]


def test_build_weekly_magazine_includes_period_label_and_kind():
    result = build_weekly_magazine(
        period_label="2026-W18",
        summary="이번 주 LLM 트렌드 요약입니다.",
        articles=_base_articles(),
    )
    assert "2026-W18" in result
    assert "주간" in result
    h1_lines = [line for line in result.splitlines() if line.startswith("# ")]
    assert len(h1_lines) >= 1


def test_build_weekly_magazine_renders_summary_and_articles():
    result = build_weekly_magazine(
        period_label="2026-W18",
        summary="이번 주는 LLM 트렌드...",
        articles=_base_articles(),
    )
    assert "이번 주는 LLM 트렌드..." in result
    assert "제목A" in result
    assert "제목B" in result
    assert "https://a.example.com" in result
    assert "https://b.example.com" in result
    h2_lines = [line for line in result.splitlines() if line.startswith("## ")]
    assert len(h2_lines) >= 2


def test_build_weekly_magazine_appends_failing_feeds():
    result = build_weekly_magazine(
        period_label="2026-W18",
        summary="요약입니다.",
        articles=_base_articles(),
        failing_feeds=[FailingFeed(name="블로그A", url="https://a.example.com/rss", consecutive_failures=7)],
    )
    assert "블로그A" in result
    assert "https://a.example.com/rss" in result
    assert "7" in result
    assert "장애" in result
    assert "---" in result


def test_build_weekly_magazine_raises_on_empty_summary():
    with pytest.raises(ValueError):
        build_weekly_magazine(
            period_label="2026-W18",
            summary="",
            articles=_base_articles(),
        )
    with pytest.raises(ValueError):
        build_weekly_magazine(
            period_label="2026-W18",
            summary="   ",
            articles=_base_articles(),
        )


def test_build_weekly_magazine_raises_on_empty_articles():
    with pytest.raises(ValueError):
        build_weekly_magazine(
            period_label="2026-W18",
            summary="정상 요약입니다.",
            articles=[],
        )
