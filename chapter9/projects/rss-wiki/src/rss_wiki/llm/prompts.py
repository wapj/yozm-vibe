from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Mapping, Sequence


class PromptParseError(Exception):
    pass


@dataclass(frozen=True)
class ArticleAnalysis:
    summary: str
    category: str
    tags: tuple[str, ...]


def build_article_prompt(
    *,
    title: str,
    body: str,
    existing_categories: Sequence[str],
) -> str:
    if existing_categories:
        category_hint = (
            "기존 카테고리 목록:\n"
            + "\n".join(f"- {c}" for c in existing_categories)
            + "\n가능하면 위 목록에서 카테고리를 선택하고, 진짜 새로운 주제일 때만 새 카테고리를 만드세요."
        )
    else:
        category_hint = "아직 등록된 카테고리가 없습니다. 적절한 카테고리를 새로 만드세요."

    return f"""당신은 한국어 기술 매거진 편집자입니다. 아래 글을 분석하여 요약, 카테고리, 태그를 JSON으로 반환하세요.

제목: {title}

본문:
{body}

{category_hint}

응답 규칙:
- 요약(summary): 1~3줄 한국어 요약
- 카테고리(category): 글을 대표하는 단일 카테고리
- 태그(tags): 자유 형식, 최대 5개 권장

반드시 아래 JSON 스키마 형태의 단일 JSON 객체만 반환하세요. 설명이나 다른 텍스트 없이 JSON만 출력하세요.
{{"summary": "...", "category": "...", "tags": ["...", "..."]}}"""


def parse_article_response(text: str) -> ArticleAnalysis:
    text = text.strip()

    lines = text.splitlines()
    if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].strip() == "```":
        inner = lines[1:-1]
        text = "\n".join(inner)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise PromptParseError(f"JSON 디코딩 실패: {e}") from e

    if not isinstance(data, dict):
        raise PromptParseError(f"응답이 dict가 아닙니다: {type(data)}")

    for key in ("summary", "category", "tags"):
        if key not in data:
            raise PromptParseError(f"필수 키 누락: '{key}'")

    if not isinstance(data["summary"], str):
        raise PromptParseError(f"summary가 str이 아닙니다: {type(data['summary'])}")
    if not isinstance(data["category"], str):
        raise PromptParseError(f"category가 str이 아닙니다: {type(data['category'])}")
    if not isinstance(data["tags"], list):
        raise PromptParseError(f"tags가 list가 아닙니다: {type(data['tags'])}")

    summary = data["summary"].strip()
    category = data["category"].strip()
    tags = tuple(str(t).strip() for t in data["tags"] if str(t).strip())

    if not summary:
        raise PromptParseError("summary가 빈 문자열입니다")
    if not category:
        raise PromptParseError("category가 빈 문자열입니다")

    return ArticleAnalysis(summary=summary, category=category, tags=tags)


def build_trend_prompt(
    *,
    category: str,
    articles: Sequence[Mapping[str, str]],
) -> str:
    if not articles:
        raise ValueError("articles는 1개 이상이어야 합니다")

    article_list = "\n".join(
        f"- 제목: {a['title']}\n  요약: {a['summary']}" for a in articles
    )

    return f"""당신은 한국어 기술 매거진 편집자입니다. 아래 카테고리의 오늘 글들을 바탕으로 트렌드 요약을 작성하세요.

카테고리: {category}

오늘의 글 목록:
{article_list}

이 카테고리의 오늘 트렌드를 자연스러운 한국어 1단락으로 요약하세요.
응답 형식: 단락 1개. JSON·머리말·코드 펜스 사용 금지."""


def parse_trend_response(text: str) -> str:
    text = text.strip()

    lines = text.splitlines()
    if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].strip() == "```":
        text = "\n".join(lines[1:-1]).strip()

    if not text:
        raise PromptParseError("트렌드 응답이 빈 문자열입니다")

    return text


def _build_period_prompt(period_label: str, articles: Sequence[Mapping[str, str]]) -> str:
    if not articles:
        raise ValueError("articles는 1개 이상이어야 합니다")

    article_list = "\n".join(
        f"- 제목: {a['title']}\n  요약: {a['summary']}" for a in articles
    )

    return f"""당신은 한국어 기술 매거진 편집자입니다. 아래 {period_label} 동안의 글들을 통합하여 정리글을 작성하세요.

글 목록:
{article_list}

이 {period_label} 분량의 글을 통합 요약한 정리글을 작성하세요.
응답 형식: 자연어 본문. 단락 수 제한 없음. JSON·머리말·코드 펜스 사용 금지."""


def build_weekly_prompt(
    *,
    articles: Sequence[Mapping[str, str]],
) -> str:
    return _build_period_prompt("주간(한 주)", articles)


def build_monthly_prompt(
    *,
    articles: Sequence[Mapping[str, str]],
) -> str:
    return _build_period_prompt("월간(한 달)", articles)
