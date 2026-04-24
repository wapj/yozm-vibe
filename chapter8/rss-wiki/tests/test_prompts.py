"""prompts/*.txt — PRD §15 템플릿이 존재하고 Jinja2로 렌더되는지 검증."""

from __future__ import annotations

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined

import rss_wiki

PROMPTS_DIR = Path(rss_wiki.__file__).parent / "prompts"


@pytest.fixture
def env() -> Environment:
    return Environment(
        loader=FileSystemLoader(PROMPTS_DIR),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )


# --- 파일 존재 -----------------------------------------------------------


def test_prompt_files_exist():
    assert (PROMPTS_DIR / "article_summarize.txt").is_file()
    assert (PROMPTS_DIR / "wiki_rebuild.txt").is_file()


# --- article_summarize.txt ----------------------------------------------


def test_article_summarize_renders_with_existing_categories(env: Environment):
    rendered = env.get_template("article_summarize.txt").render(
        existing_categories=[
            {"name": "AI", "description": "인공지능"},
            {"name": "데이터 엔지니어링", "description": None},
        ],
        title="LLM 에이전트 설계",
        url="https://example.com/post/1",
        detected_language="ko",
        content="본문 내용입니다.",
    )
    assert "당신은 한국어 기술 큐레이터입니다." in rendered
    assert "- AI: 인공지능" in rendered
    assert "- 데이터 엔지니어링" in rendered
    # description이 없는 카테고리는 콜론이 붙지 않아야 함
    assert "- 데이터 엔지니어링: " not in rendered
    assert "제목: LLM 에이전트 설계" in rendered
    assert "원문 URL: https://example.com/post/1" in rendered
    assert "언어: ko" in rendered
    assert "본문 내용입니다." in rendered
    # JSON 강제 문구
    assert "응답은 반드시 유효한 JSON 객체 하나만 출력하세요." in rendered
    # 스키마 키들이 그대로 노출되어야 함
    assert '"summary"' in rendered
    assert '"category_name"' in rendered
    assert '"is_new_category"' in rendered
    assert '"language_detected"' in rendered


def test_article_summarize_renders_with_empty_categories(env: Environment):
    rendered = env.get_template("article_summarize.txt").render(
        existing_categories=[],
        title="첫 글",
        url="https://example.com/p/0",
        detected_language="en",
        content="hello",
    )
    assert "[기존 카테고리 목록]" in rendered
    assert "제목: 첫 글" in rendered
    assert "언어: en" in rendered


# --- wiki_rebuild.txt ----------------------------------------------------


def test_wiki_rebuild_renders_incremental(env: Environment):
    rendered = env.get_template("wiki_rebuild.txt").render(
        category_name="AI",
        previous_wiki_markdown="# AI\n\n## 한줄 요약\n기존 요약",
        new_articles=[
            {
                "title": "새 글",
                "url": "https://example.com/new",
                "published_at": "2026-04-25",
                "llm_summary": "한 줄 요약 글.",
            }
        ],
        existing_recent_articles=[
            {
                "title": "예전 글",
                "published_at": "2026-04-20",
                "one_line": "예전 글 한줄",
            }
        ],
    )
    assert "카테고리명: AI" in rendered
    assert "# AI\n\n## 한줄 요약\n기존 요약" in rendered
    assert "- 제목: 새 글" in rendered
    assert "URL: https://example.com/new" in rendered
    assert "발행일: 2026-04-25" in rendered
    assert "요약: 한 줄 요약 글." in rendered
    assert "- 예전 글 (2026-04-20) — 예전 글 한줄" in rendered
    # 출력 구조 헤더가 프롬프트에 명시되어 있어야 함
    assert "## 한줄 요약" in rendered
    assert "## 핵심 내용" in rendered
    assert "## 최근 동향" in rendered
    assert "## 참고한 글" in rendered


def test_wiki_rebuild_renders_initial_build_with_empty_previous(env: Environment):
    rendered = env.get_template("wiki_rebuild.txt").render(
        category_name="데이터 엔지니어링",
        previous_wiki_markdown="",
        new_articles=[],
        existing_recent_articles=[],
    )
    # 빈 문자열이면 폴백 문구가 들어가야 함
    assert "(없음 — 최초 생성)" in rendered
    assert "카테고리명: 데이터 엔지니어링" in rendered
