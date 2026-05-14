import pytest

from rss_wiki.llm.prompts import (
    ArticleAnalysis,
    PromptParseError,
    build_article_prompt,
    build_monthly_prompt,
    build_trend_prompt,
    build_weekly_prompt,
    parse_article_response,
    parse_trend_response,
)


def test_build_article_prompt_includes_title_body_and_existing_categories():
    result = build_article_prompt(
        title="제목",
        body="본문 내용",
        existing_categories=["AI", "데브옵스"],
    )
    assert "제목" in result
    assert "본문 내용" in result
    assert "AI" in result
    assert "데브옵스" in result
    assert "json" in result.lower()


def test_build_article_prompt_handles_empty_existing_categories():
    result = build_article_prompt(title="제목", body="본문", existing_categories=[])
    assert isinstance(result, str)
    assert "없" in result


def test_parse_article_response_returns_analysis():
    text = '{"summary": "한 줄 요약", "category": "AI", "tags": ["LLM", "Claude"]}'
    result = parse_article_response(text)
    assert result == ArticleAnalysis(summary="한 줄 요약", category="AI", tags=("LLM", "Claude"))


def test_parse_article_response_strips_code_fence():
    text = '```json\n{"summary": "s", "category": "c", "tags": []}\n```'
    result = parse_article_response(text)
    assert result == ArticleAnalysis(summary="s", category="c", tags=())


def test_parse_article_response_raises_on_invalid_json():
    with pytest.raises(PromptParseError):
        parse_article_response("not a json")


def test_parse_article_response_raises_on_missing_keys():
    with pytest.raises(PromptParseError):
        parse_article_response('{"summary": "s"}')


def test_parse_article_response_raises_on_empty_summary():
    with pytest.raises(PromptParseError):
        parse_article_response('{"summary": "  ", "category": "AI", "tags": []}')


def test_parse_article_response_raises_on_empty_category():
    with pytest.raises(PromptParseError):
        parse_article_response('{"summary": "ok", "category": "", "tags": []}')


def test_build_trend_prompt_includes_category_and_articles():
    result = build_trend_prompt(
        category="AI",
        articles=[
            {"title": "글1", "summary": "요1"},
            {"title": "글2", "summary": "요2"},
        ],
    )
    assert "AI" in result
    assert "글1" in result
    assert "글2" in result
    assert "요1" in result
    assert "요2" in result


def test_build_trend_prompt_raises_on_empty_articles():
    with pytest.raises(ValueError):
        build_trend_prompt(category="AI", articles=[])


def test_parse_trend_response_returns_paragraph():
    result = parse_trend_response("오늘은 LLM 관련 발표가 활발했다.")
    assert result == "오늘은 LLM 관련 발표가 활발했다."


def test_parse_trend_response_strips_code_fence():
    result = parse_trend_response("```\n트렌드 요약\n```")
    assert result == "트렌드 요약"


def test_parse_trend_response_raises_on_empty():
    with pytest.raises(PromptParseError):
        parse_trend_response("")
    with pytest.raises(PromptParseError):
        parse_trend_response("   ")


def test_build_weekly_prompt_includes_articles():
    result = build_weekly_prompt(
        articles=[{"title": "글1", "summary": "요1"}, {"title": "글2", "summary": "요2"}]
    )
    assert "글1" in result
    assert "글2" in result
    assert "요1" in result
    assert "요2" in result


def test_build_weekly_prompt_raises_on_empty():
    with pytest.raises(ValueError):
        build_weekly_prompt(articles=[])


def test_build_monthly_prompt_includes_articles():
    result = build_monthly_prompt(
        articles=[{"title": "글1", "summary": "요1"}, {"title": "글2", "summary": "요2"}]
    )
    assert "글1" in result
    assert "글2" in result
    assert "요1" in result
    assert "요2" in result


def test_build_monthly_prompt_raises_on_empty():
    with pytest.raises(ValueError):
        build_monthly_prompt(articles=[])


def test_weekly_and_monthly_prompts_distinguishable():
    articles = [{"title": "글1", "summary": "요1"}, {"title": "글2", "summary": "요2"}]
    weekly = build_weekly_prompt(articles=articles)
    monthly = build_monthly_prompt(articles=articles)
    assert weekly != monthly
    assert any(k in weekly for k in ["주간", "한 주", "이번 주"])
    assert any(k in monthly for k in ["월간", "한 달", "이번 달"])
