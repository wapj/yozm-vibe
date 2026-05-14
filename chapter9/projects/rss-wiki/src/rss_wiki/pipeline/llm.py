from __future__ import annotations
import logging
import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Callable

from rss_wiki.llm.client import LLMError, call_claude
from rss_wiki.llm.prompts import (
    ArticleAnalysis,
    PromptParseError,
    build_article_prompt,
    build_trend_prompt,
    parse_article_response,
    parse_trend_response,
)
from rss_wiki.storage.repo import (
    link_article_category,
    link_article_tag,
    list_articles_by_ids,
    list_categories,
    update_article_summary,
    upsert_category,
    upsert_tag,
)

Runner = Callable[..., str]


@dataclass(frozen=True)
class AnalyzeStats:
    articles_total: int
    articles_analyzed: int
    articles_failed: int
    categories_with_trend: int
    trends_failed: int


@dataclass(frozen=True)
class AnalyzeResult:
    stats: AnalyzeStats
    trends: dict[str, str]
    analyzed_article_ids: tuple[int, ...]


def analyze_articles(
    *,
    conn: sqlite3.Connection,
    article_ids: Sequence[int],
    runner: Runner | None = None,
    logger: logging.Logger | None = None,
) -> AnalyzeResult:
    _logger = logger or logging.getLogger(__name__)

    if runner is not None:
        _runner = runner
    else:
        _runner = call_claude

    if not article_ids:
        return AnalyzeResult(
            stats=AnalyzeStats(0, 0, 0, 0, 0),
            trends={},
            analyzed_article_ids=(),
        )

    articles = list_articles_by_ids(conn, article_ids)
    articles_total = len(articles)

    existing_categories = [row["name"] for row in list_categories(conn)]

    by_category: dict[str, list[dict[str, str]]] = {}
    analyzed_ids: list[int] = []
    articles_analyzed = 0
    articles_failed = 0

    for row in articles:
        try:
            prompt = build_article_prompt(
                title=row["title"] or "",
                body=row["content"] or "",
                existing_categories=existing_categories,
            )
            text = _runner(prompt)
            analysis: ArticleAnalysis = parse_article_response(text)
            update_article_summary(conn, article_id=row["id"], summary=analysis.summary)
            category_id = upsert_category(conn, analysis.category)
            link_article_category(conn, row["id"], category_id)
            for tag in analysis.tags:
                tag_id = upsert_tag(conn, tag)
                link_article_tag(conn, row["id"], tag_id)
            cat_key = analysis.category.strip().lower()
            by_category.setdefault(cat_key, []).append(
                {"title": row["title"] or "", "summary": analysis.summary}
            )
            analyzed_ids.append(row["id"])
            articles_analyzed += 1
        except (LLMError, PromptParseError) as exc:
            _logger.warning("article analyze failed: id=%s reason=%s", row["id"], exc)
            articles_failed += 1

    trends: dict[str, str] = {}
    categories_with_trend = 0
    trends_failed = 0

    for cat_key, items in by_category.items():
        try:
            prompt = build_trend_prompt(category=cat_key, articles=items)
            text = _runner(prompt)
            trends[cat_key] = parse_trend_response(text)
            categories_with_trend += 1
        except (LLMError, PromptParseError) as exc:
            _logger.warning("trend analyze failed: category=%s reason=%s", cat_key, exc)
            trends_failed += 1

    return AnalyzeResult(
        stats=AnalyzeStats(
            articles_total=articles_total,
            articles_analyzed=articles_analyzed,
            articles_failed=articles_failed,
            categories_with_trend=categories_with_trend,
            trends_failed=trends_failed,
        ),
        trends=trends,
        analyzed_article_ids=tuple(sorted(analyzed_ids)),
    )
