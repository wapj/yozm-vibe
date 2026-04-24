"""개별 글 요약·분류 (PRD §7.1 step 4, §7.2).

- 기존 카테고리 목록을 프롬프트에 주입해 Claude CLI 로 요약/카테고리 제안을 받는다.
- 응답의 `category_name` 을 `categories` 테이블에 upsert 하고 `articles` 에 INSERT.
- LLM / JSON 파싱이 최종 실패하면 URL 중복 재수집을 막기 위해 status='failed' 레코드를 삽입.
- extracted_content 는 trafilatura 본문 성공 시에만 저장 (fallback/none 은 NULL).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from rss_wiki.config import PROMPTS_DIR
from rss_wiki.pipeline.extractor import ExtractionResult
from rss_wiki.pipeline.fetcher import FeedEntry
from rss_wiki.pipeline.llm import (
    LLMError,
    LLMJSONParseError,
    call_claude_cli_json,
)


ClaudeJSONFn = Callable[[str], Awaitable[Any]]


@dataclass(slots=True)
class SummarizeOutcome:
    article_id: int
    status: str  # 'ok' | 'failed'
    category_id: int | None
    error: str | None = None


def _build_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(PROMPTS_DIR),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )


_ENV = _build_env()


def render_article_prompt(
    *,
    existing_categories: list[dict[str, Any]],
    title: str,
    url: str,
    detected_language: str,
    content: str,
    env: Environment | None = None,
) -> str:
    template = (env or _ENV).get_template("article_summarize.txt")
    return template.render(
        existing_categories=existing_categories,
        title=title,
        url=url,
        detected_language=detected_language,
        content=content,
    )


def list_existing_categories(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """병합되지 않은 카테고리만 프롬프트 후보로 노출한다."""
    rows = conn.execute(
        "SELECT id, name, description FROM categories "
        "WHERE merged_into_id IS NULL ORDER BY id"
    ).fetchall()
    return [
        {"id": r["id"], "name": r["name"], "description": r["description"]}
        for r in rows
    ]


def upsert_category(conn: sqlite3.Connection, name: str) -> int:
    """카테고리 이름으로 upsert. 이미 존재하면 기존 id, 없으면 새로 INSERT."""
    row = conn.execute(
        "SELECT id FROM categories WHERE name = ?", (name,)
    ).fetchone()
    if row is not None:
        return int(row["id"])
    cursor = conn.execute(
        "INSERT INTO categories (name) VALUES (?)", (name,)
    )
    return int(cursor.lastrowid)


async def summarize_article(
    conn: sqlite3.Connection,
    *,
    feed_id: int,
    entry: FeedEntry,
    extraction: ExtractionResult,
    detected_language: str = "",
    call_llm: ClaudeJSONFn | None = None,
) -> SummarizeOutcome:
    """단일 글을 LLM 으로 요약·분류하고 articles 에 저장한다."""
    llm = call_llm or _default_llm_call
    extracted_text = (
        extraction.text if extraction.source == "trafilatura" else None
    )

    content = (extraction.text or "").strip()
    if not content:
        return _insert_failed(
            conn,
            feed_id=feed_id,
            entry=entry,
            extracted_content=extracted_text,
            language=detected_language or None,
            error="empty content",
        )

    prompt = render_article_prompt(
        existing_categories=list_existing_categories(conn),
        title=entry.title,
        url=entry.url,
        detected_language=detected_language or "",
        content=content,
    )

    try:
        response = await llm(prompt)
    except (LLMError, LLMJSONParseError) as exc:
        return _insert_failed(
            conn,
            feed_id=feed_id,
            entry=entry,
            extracted_content=extracted_text,
            language=detected_language or None,
            error=f"{type(exc).__name__}: {exc}",
        )

    summary = _coerce_str(response.get("summary") if isinstance(response, dict) else None)
    category_name = _coerce_str(
        response.get("category_name") if isinstance(response, dict) else None
    )
    language = (
        _coerce_str(response.get("language_detected"))
        if isinstance(response, dict)
        else None
    ) or (detected_language or None)

    if not summary or not category_name:
        return _insert_failed(
            conn,
            feed_id=feed_id,
            entry=entry,
            extracted_content=extracted_text,
            language=language,
            error="missing summary or category_name",
        )

    category_id = upsert_category(conn, category_name)
    article_id = _insert_article(
        conn,
        feed_id=feed_id,
        entry=entry,
        extracted_content=extracted_text,
        llm_summary=summary,
        primary_category_id=category_id,
        language=language,
        status="ok",
    )
    conn.commit()
    return SummarizeOutcome(
        article_id=article_id, status="ok", category_id=category_id
    )


def _insert_failed(
    conn: sqlite3.Connection,
    *,
    feed_id: int,
    entry: FeedEntry,
    extracted_content: str | None,
    language: str | None,
    error: str,
) -> SummarizeOutcome:
    article_id = _insert_article(
        conn,
        feed_id=feed_id,
        entry=entry,
        extracted_content=extracted_content,
        llm_summary=None,
        primary_category_id=None,
        language=language,
        status="failed",
    )
    conn.commit()
    return SummarizeOutcome(
        article_id=article_id,
        status="failed",
        category_id=None,
        error=error,
    )


def _insert_article(
    conn: sqlite3.Connection,
    *,
    feed_id: int,
    entry: FeedEntry,
    extracted_content: str | None,
    llm_summary: str | None,
    primary_category_id: int | None,
    language: str | None,
    status: str,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO articles (
            feed_id, url, title, author, published_at, raw_summary,
            extracted_content, llm_summary, primary_category_id, language, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            feed_id,
            entry.url,
            entry.title,
            entry.author,
            entry.published_at,
            entry.raw_summary,
            extracted_content,
            llm_summary,
            primary_category_id,
            language,
            status,
        ),
    )
    return int(cursor.lastrowid)


def _coerce_str(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


async def _default_llm_call(prompt: str) -> Any:
    return await call_claude_cli_json(prompt)
