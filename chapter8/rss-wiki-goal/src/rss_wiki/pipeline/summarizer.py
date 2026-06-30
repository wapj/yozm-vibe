"""개별 글 요약·분류 — ARTICLE_SUMMARIZE_PROMPT 적용."""

import logging
import sqlite3
from pathlib import Path

from rss_wiki.models import LLMSummaryResult
from rss_wiki.pipeline.llm import call_llm_json

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "article_summarize.txt"


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _render_prompt(
    template: str,
    title: str,
    url: str,
    detected_language: str,
    content: str,
    existing_categories: list[dict],
) -> str:
    cat_lines = "\n".join(
        f"- {c['name']}" + (f": {c['description']}" if c.get("description") else "")
        for c in existing_categories
    )
    return (
        template
        .replace("{% for c in existing_categories %}- {{ c.name }}{% if c.description %}: {{ c.description }}{% endif %}\n{% endfor %}", cat_lines + "\n")
        .replace("{{ title }}", title)
        .replace("{{ url }}", url)
        .replace("{{ detected_language }}", detected_language)
        .replace("{{ content }}", content)
    )


def _get_existing_categories(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT name, description FROM categories WHERE merged_into_id IS NULL ORDER BY name"
    ).fetchall()
    return [{"name": r["name"], "description": r["description"]} for r in rows]


def _upsert_category(conn: sqlite3.Connection, name: str) -> int:
    conn.execute(
        "INSERT OR IGNORE INTO categories(name) VALUES (?)", (name,)
    )
    row = conn.execute("SELECT id FROM categories WHERE name=?", (name,)).fetchone()
    return row["id"]


async def summarize_article(
    conn: sqlite3.Connection,
    article_id: int,
    title: str,
    url: str,
    content: str,
    detected_language: str = "ko",
) -> LLMSummaryResult | None:
    """글을 요약하고 카테고리를 분류한다. 실패 시 None."""
    template = _load_prompt()
    categories = _get_existing_categories(conn)
    prompt = _render_prompt(template, title, url, detected_language, content, categories)

    result = await call_llm_json(prompt)
    if result is None:
        return None

    summary = result.get("summary", "")
    category_name = result.get("category_name", "기타")
    is_new = bool(result.get("is_new_category", False))
    lang = result.get("language_detected", detected_language)

    if not category_name:
        category_name = "기타"

    category_id = _upsert_category(conn, category_name)

    conn.execute(
        "UPDATE articles SET llm_summary=?, primary_category_id=?, language=? WHERE id=?",
        (summary, category_id, lang, article_id),
    )
    conn.commit()

    return LLMSummaryResult(
        summary=summary,
        category_name=category_name,
        is_new_category=is_new,
        language_detected=lang,
    )
