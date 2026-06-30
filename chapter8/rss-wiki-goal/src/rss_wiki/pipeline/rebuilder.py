"""위키 페이지 재구성 — WIKI_REBUILD_PROMPT 적용, 증분 전략."""

import logging
import sqlite3
from pathlib import Path

from rss_wiki.config import (
    WIKI_INCREMENTAL_CONTEXT_COUNT,
    WIKI_INITIAL_BUILD_ARTICLE_COUNT,
    WIKI_INPUT_MAX_CHARS,
)
from rss_wiki.models import ArticleContext, NewArticleForWiki
from rss_wiki.pipeline.llm import call_llm_text

logger = logging.getLogger(__name__)

_PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "wiki_rebuild.txt"


def _load_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _render_new_articles(articles: list[NewArticleForWiki]) -> str:
    lines = []
    for a in articles:
        lines.append(f"- 제목: {a.title}\n  URL: {a.url}\n  발행일: {a.published_at or ''}\n  요약: {a.llm_summary or ''}")
    return "\n".join(lines)


def _render_existing_articles(articles: list[ArticleContext]) -> str:
    return "\n".join(
        f"- {a.title} ({a.published_at or ''}) — {a.one_line}"
        for a in articles
    )


def _render_prompt(
    template: str,
    category_name: str,
    previous_wiki_markdown: str,
    new_articles: list[NewArticleForWiki],
    existing_recent_articles: list[ArticleContext],
) -> str:
    new_section = _render_new_articles(new_articles)
    existing_section = _render_existing_articles(existing_recent_articles)

    return (
        template
        .replace("{{ category_name }}", category_name)
        .replace("{{ previous_wiki_markdown or \"(없음 — 최초 생성)\" }}", previous_wiki_markdown or "(없음 — 최초 생성)")
        .replace(
            "{% for a in new_articles %}\n- 제목: {{ a.title }}\n  URL: {{ a.url }}\n  발행일: {{ a.published_at }}\n  요약: {{ a.llm_summary }}\n{% endfor %}",
            new_section,
        )
        .replace(
            "{% for a in existing_recent_articles %}\n- {{ a.title }} ({{ a.published_at }}) — {{ a.one_line }}\n{% endfor %}",
            existing_section,
        )
        .replace("# {{ category_name }}", f"# {category_name}")
    )


def _get_new_articles(conn: sqlite3.Connection, category_id: int, since_article_ids: list[int]) -> list[NewArticleForWiki]:
    if not since_article_ids:
        return []
    placeholders = ",".join("?" * len(since_article_ids))
    rows = conn.execute(
        f"SELECT title, url, llm_summary, published_at FROM articles "
        f"WHERE id IN ({placeholders}) AND primary_category_id=? ORDER BY published_at DESC",
        (*since_article_ids, category_id),
    ).fetchall()
    return [NewArticleForWiki(title=r["title"], url=r["url"], llm_summary=r["llm_summary"], published_at=r["published_at"]) for r in rows]


def _get_existing_context(conn: sqlite3.Connection, category_id: int, limit: int, exclude_ids: list[int]) -> list[ArticleContext]:
    excludes = f"AND id NOT IN ({','.join('?' * len(exclude_ids))})" if exclude_ids else ""
    rows = conn.execute(
        f"SELECT title, published_at, llm_summary FROM articles "
        f"WHERE primary_category_id=? {excludes} ORDER BY published_at DESC LIMIT ?",
        (category_id, *exclude_ids, limit),
    ).fetchall()
    return [ArticleContext(title=r["title"], published_at=r["published_at"], one_line=(r["llm_summary"] or "")[:80]) for r in rows]


def _apply_token_budget(
    new_articles: list[NewArticleForWiki],
    existing_articles: list[ArticleContext],
    previous_wiki: str,
) -> list[ArticleContext]:
    """입력 길이가 WIKI_INPUT_MAX_CHARS 초과 시 existing_articles 축소."""
    new_text = _render_new_articles(new_articles)
    existing_text = _render_existing_articles(existing_articles)
    total = len(previous_wiki) + len(new_text) + len(existing_text)
    if total <= WIKI_INPUT_MAX_CHARS:
        return existing_articles

    for limit in (5, 3, 0):
        truncated = existing_articles[:limit]
        existing_text = _render_existing_articles(truncated)
        total = len(previous_wiki) + len(new_text) + len(existing_text)
        if total <= WIKI_INPUT_MAX_CHARS:
            return truncated
    return []


async def rebuild_wiki(
    conn: sqlite3.Connection,
    category_id: int,
    new_article_ids: list[int],
) -> bool:
    """카테고리 위키 페이지를 재구성한다. 성공 시 True."""
    # 카테고리명 조회
    cat_row = conn.execute("SELECT name FROM categories WHERE id=?", (category_id,)).fetchone()
    if cat_row is None:
        logger.error("Category %d not found", category_id)
        return False
    category_name = cat_row["name"]

    # 기존 위키 내용
    wp_row = conn.execute("SELECT content_markdown FROM wiki_pages WHERE category_id=?", (category_id,)).fetchone()
    previous_wiki = wp_row["content_markdown"] if wp_row else ""

    # 신규 글
    new_articles = _get_new_articles(conn, category_id, new_article_ids)

    # 기존 컨텍스트 글
    is_initial = not previous_wiki
    context_limit = WIKI_INITIAL_BUILD_ARTICLE_COUNT if is_initial else WIKI_INCREMENTAL_CONTEXT_COUNT
    existing_articles = _get_existing_context(conn, category_id, context_limit, new_article_ids)

    # 토큰 예산 가드
    existing_articles = _apply_token_budget(new_articles, existing_articles, previous_wiki)

    # 프롬프트 렌더링 및 LLM 호출
    template = _load_prompt()
    prompt = _render_prompt(template, category_name, previous_wiki, new_articles, existing_articles)
    markdown = await call_llm_text(prompt)
    if markdown is None:
        return False

    # wiki_pages upsert
    article_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM articles WHERE primary_category_id=?", (category_id,)
    ).fetchone()["cnt"]

    conn.execute(
        """INSERT INTO wiki_pages(category_id, content_markdown, last_rebuilt_at, articles_count_at_rebuild, has_unread_updates)
           VALUES (?, ?, datetime('now'), ?, 1)
           ON CONFLICT(category_id) DO UPDATE SET
             content_markdown=excluded.content_markdown,
             last_rebuilt_at=excluded.last_rebuilt_at,
             articles_count_at_rebuild=excluded.articles_count_at_rebuild,
             has_unread_updates=1
        """,
        (category_id, markdown, article_count),
    )
    conn.commit()
    return True
