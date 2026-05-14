from __future__ import annotations
import logging
import sqlite3
from collections.abc import Sequence
from datetime import date, timedelta
from pathlib import Path
from typing import Callable

from rss_wiki.llm.client import call_claude
from rss_wiki.llm.prompts import build_monthly_prompt, build_weekly_prompt, parse_trend_response
from rss_wiki.pipeline.llm import AnalyzeResult
from rss_wiki.publish.daily import (
    ArticleCard,
    CategorySection,
    FailingFeed,
    build_daily_magazine,
)
from rss_wiki.publish.indexes import IndexEntry, build_index
from rss_wiki.publish.monthly import build_monthly_magazine
from rss_wiki.publish.weekly import SourceArticle, build_weekly_magazine
from rss_wiki.storage.repo import (
    insert_magazine,
    link_magazine_article,
    list_articles_by_category,
    list_articles_by_ids,
    list_articles_by_tag,
    list_articles_published_between,
    list_categories,
    list_categories_for_article,
    list_failing_feeds,
    list_tags,
    list_tags_for_article,
)


def _iso_week_label(date_str: str) -> str:
    """YYYY-MM-DD → YYYY-Www (ISO 8601 주차)."""
    d = date.fromisoformat(date_str)
    iso_year, iso_week, _ = d.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def publish_daily(
    *,
    conn: sqlite3.Connection,
    result: AnalyzeResult,
    output_dir: Path,
    date: str,
    logger: logging.Logger | None = None,
) -> Path:
    _logger = logger or logging.getLogger(__name__)

    analyzed_ids = result.analyzed_article_ids
    if not analyzed_ids:
        raise ValueError("분석된 글이 없어 일간 매거진을 발행할 수 없습니다.")

    articles = list_articles_by_ids(conn, analyzed_ids)

    by_category: dict[str, list[ArticleCard]] = {}
    included_ids: list[int] = []

    for row in articles:
        cat_rows = list_categories_for_article(conn, row["id"])
        if not cat_rows:
            _logger.warning("article has no category, skipping: id=%s", row["id"])
            continue
        tag_names = tuple(r["name"] for r in list_tags_for_article(conn, row["id"]))
        card = ArticleCard(
            title=row["title"] or "",
            url=row["url"],
            summary=row["summary"] or "",
            tags=tag_names,
        )
        cat_names = [r["name"] for r in cat_rows]
        first_cat = cat_names[0]
        by_category.setdefault(first_cat, []).append(card)
        included_ids.append(row["id"])

    if not by_category:
        raise ValueError("분석된 글이 없어 일간 매거진을 발행할 수 없습니다.")

    sections: list[CategorySection] = []
    for cat_key, cards in by_category.items():
        trend_summary = result.trends.get(cat_key, "")
        sections.append(CategorySection(name=cat_key, trend_summary=trend_summary, articles=tuple(cards)))

    failing_rows = list_failing_feeds(conn)
    failing = tuple(
        FailingFeed(name=r["name"], url=r["url"], consecutive_failures=r["consecutive_failures"])
        for r in failing_rows
    )

    markdown = build_daily_magazine(date=date, sections=tuple(sections), failing_feeds=failing)

    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"daily-{date}.md"
    file_path.write_text(markdown, encoding="utf-8")

    magazine_id = insert_magazine(conn, kind="daily", published_at=date, file_path=str(file_path))

    for aid in included_ids:
        link_magazine_article(conn, magazine_id, aid)

    _logger.info(
        "daily magazine published: path=%s articles=%s sections=%s",
        file_path,
        len(included_ids),
        len(sections),
    )

    return file_path


def publish_weekly(
    *,
    conn: sqlite3.Connection,
    end_date: str,
    output_dir: Path,
    runner: Callable[[str], str] | None = None,
    logger: logging.Logger | None = None,
) -> Path | None:
    _logger = logger or logging.getLogger(__name__)
    _runner = runner if runner is not None else call_claude
    start_date = (date.fromisoformat(end_date) - timedelta(days=6)).isoformat()
    articles = list_articles_published_between(conn, start_date=start_date, end_date=end_date)
    if not articles:
        _logger.warning(
            "weekly publish skipped (no articles): start=%s end=%s", start_date, end_date
        )
        return None
    items = [{"title": r["title"] or "", "summary": r["summary"] or ""} for r in articles]
    prompt = build_weekly_prompt(articles=items)
    text = _runner(prompt)
    summary_text = parse_trend_response(text)
    source_articles = tuple(SourceArticle(title=r["title"] or "", url=r["url"]) for r in articles)
    failing_rows = list_failing_feeds(conn)
    failing = tuple(
        FailingFeed(name=r["name"], url=r["url"], consecutive_failures=r["consecutive_failures"])
        for r in failing_rows
    )
    period_label = _iso_week_label(end_date)
    markdown = build_weekly_magazine(
        period_label=period_label,
        summary=summary_text,
        articles=source_articles,
        failing_feeds=failing,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"weekly-{period_label}.md"
    file_path.write_text(markdown, encoding="utf-8")
    magazine_id = insert_magazine(conn, kind="weekly", published_at=end_date, file_path=str(file_path))
    for r in articles:
        link_magazine_article(conn, magazine_id, r["id"])
    _logger.info("weekly magazine published: path=%s articles=%s", file_path, len(articles))
    return file_path


def publish_monthly(
    *,
    conn: sqlite3.Connection,
    end_date: str,
    output_dir: Path,
    runner: Callable[[str], str] | None = None,
    logger: logging.Logger | None = None,
) -> Path | None:
    _logger = logger or logging.getLogger(__name__)
    _runner = runner if runner is not None else call_claude
    start_date = date.fromisoformat(end_date).replace(day=1).isoformat()
    articles = list_articles_published_between(conn, start_date=start_date, end_date=end_date)
    if not articles:
        _logger.warning(
            "monthly publish skipped (no articles): start=%s end=%s", start_date, end_date
        )
        return None
    items = [{"title": r["title"] or "", "summary": r["summary"] or ""} for r in articles]
    prompt = build_monthly_prompt(articles=items)
    text = _runner(prompt)
    summary_text = parse_trend_response(text)
    source_articles = tuple(SourceArticle(title=r["title"] or "", url=r["url"]) for r in articles)
    failing_rows = list_failing_feeds(conn)
    failing = tuple(
        FailingFeed(name=r["name"], url=r["url"], consecutive_failures=r["consecutive_failures"])
        for r in failing_rows
    )
    period_label = end_date[:7]
    markdown = build_monthly_magazine(
        period_label=period_label,
        summary=summary_text,
        articles=source_articles,
        failing_feeds=failing,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"monthly-{period_label}.md"
    file_path.write_text(markdown, encoding="utf-8")
    magazine_id = insert_magazine(conn, kind="monthly", published_at=end_date, file_path=str(file_path))
    for r in articles:
        link_magazine_article(conn, magazine_id, r["id"])
    _logger.info("monthly magazine published: path=%s articles=%s", file_path, len(articles))
    return file_path


def publish_indexes(
    *,
    conn: sqlite3.Connection,
    output_dir: Path,
    logger: logging.Logger | None = None,
) -> list[Path]:
    _logger = logger or logging.getLogger(__name__)
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    categories = list_categories(conn)
    for row in categories:
        article_rows = list_articles_by_category(conn, row["id"])
        if not article_rows:
            _logger.warning("category index skipped (no articles): name=%s", row["name"])
            continue
        entries = tuple(
            IndexEntry(
                title=r["title"] or "",
                url=r["url"],
                summary=r["summary"] or "",
                published_date=r["published_at"] or "",
            )
            for r in article_rows
        )
        markdown = build_index(kind="category", name=row["name"], entries=entries)
        safe_name = row["name"].replace("/", "-")
        file_path = output_dir / f"index-category-{safe_name}.md"
        file_path.write_text(markdown, encoding="utf-8")
        written.append(file_path)

    tags = list_tags(conn)
    for row in tags:
        article_rows = list_articles_by_tag(conn, row["id"])
        if not article_rows:
            _logger.warning("tag index skipped (no articles): name=%s", row["name"])
            continue
        entries = tuple(
            IndexEntry(
                title=r["title"] or "",
                url=r["url"],
                summary=r["summary"] or "",
                published_date=r["published_at"] or "",
            )
            for r in article_rows
        )
        markdown = build_index(kind="tag", name=row["name"], entries=entries)
        safe_name = row["name"].replace("/", "-")
        file_path = output_dir / f"index-tag-{safe_name}.md"
        file_path.write_text(markdown, encoding="utf-8")
        written.append(file_path)

    _logger.info("indexes published: count=%s", len(written))
    return written
