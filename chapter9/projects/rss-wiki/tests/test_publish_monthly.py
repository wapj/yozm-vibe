import pytest

from rss_wiki.publish.monthly import build_monthly_magazine
from rss_wiki.publish.weekly import SourceArticle


def _base_articles():
    return [
        SourceArticle("제목A", "https://a.example.com"),
        SourceArticle("제목B", "https://b.example.com"),
    ]


def test_build_monthly_magazine_includes_period_label_and_kind():
    result = build_monthly_magazine(
        period_label="2026-05",
        summary="이번 달 LLM 트렌드 요약입니다.",
        articles=_base_articles(),
    )
    assert "2026-05" in result
    assert "월간" in result
    assert "주간" not in result


def test_build_monthly_magazine_renders_summary_and_articles():
    result = build_monthly_magazine(
        period_label="2026-05",
        summary="이번 달은 AI 기술이 발전했습니다.",
        articles=_base_articles(),
    )
    assert "이번 달은 AI 기술이 발전했습니다." in result
    assert "제목A" in result
    assert "제목B" in result
    assert "https://a.example.com" in result
    assert "https://b.example.com" in result


def test_build_monthly_magazine_raises_on_empty_summary():
    with pytest.raises(ValueError):
        build_monthly_magazine(
            period_label="2026-05",
            summary="",
            articles=_base_articles(),
        )
