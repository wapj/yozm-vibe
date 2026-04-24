"""카테고리별 위키 페이지 재구성 (PRD §7.1 step 6, §8.2).

- previous_wiki_markdown + 이번 배치의 new_articles + 기존 최근 글을 입력으로
  Claude CLI (`-p --output-format text`) 에 보내 순수 Markdown 을 돌려받는다.
- 입력 총 길이가 100,000자를 넘으면 `existing_recent_articles` 를 축소한다.
  - 증분: (10 → 5 → 3 → 0)
  - 최초 빌드: (20 → 10 → 5 → 3 → 0) — previous 가 빈 문자열일 때
- 성공 시 `wiki_pages` 를 upsert 하고 `has_unread_updates=1` 로 표시한다.
  `last_seen_at` 은 건드리지 않는다 (사용자 방문 시점만 갱신).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Sequence

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from rss_wiki.config import (
    PROMPTS_DIR,
    WIKI_EXISTING_CONTEXT_FALLBACKS,
    WIKI_INCREMENTAL_EXISTING_CONTEXT,
    WIKI_INITIAL_BUILD_RECENT_ARTICLES,
    WIKI_REBUILD_INPUT_CHAR_LIMIT,
)
from rss_wiki.pipeline.llm import LLMError, call_claude_cli


ClaudeTextFn = Callable[[str], Awaitable[str]]


@dataclass(slots=True)
class RebuildOutcome:
    category_id: int
    status: str  # 'ok' | 'failed' | 'skipped'
    content_markdown: str | None
    is_initial: bool
    used_existing_context_size: int
    articles_count: int
    error: str | None = None


def _build_env() -> Environment:
    return Environment(
        loader=FileSystemLoader(PROMPTS_DIR),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )


_ENV = _build_env()


def _fallback_sizes(is_initial: bool) -> tuple[int, ...]:
    if is_initial:
        # 최초 빌드는 20부터 시작해 동일 사다리로 축소.
        extras = tuple(
            s for s in WIKI_EXISTING_CONTEXT_FALLBACKS
            if s < WIKI_INITIAL_BUILD_RECENT_ARTICLES
        )
        return (WIKI_INITIAL_BUILD_RECENT_ARTICLES, *extras)
    base = WIKI_EXISTING_CONTEXT_FALLBACKS
    if base and base[0] == WIKI_INCREMENTAL_EXISTING_CONTEXT:
        return base
    return (WIKI_INCREMENTAL_EXISTING_CONTEXT, *base)


def _one_line(summary: str | None) -> str:
    if not summary:
        return ""
    for line in summary.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _load_category_name(conn: sqlite3.Connection, category_id: int) -> str | None:
    row = conn.execute(
        "SELECT name FROM categories WHERE id = ?", (category_id,)
    ).fetchone()
    return None if row is None else str(row["name"])


def _load_previous_markdown(conn: sqlite3.Connection, category_id: int) -> str:
    row = conn.execute(
        "SELECT content_markdown FROM wiki_pages WHERE category_id = ?",
        (category_id,),
    ).fetchone()
    if row is None:
        return ""
    return str(row["content_markdown"] or "")


def _load_new_articles(
    conn: sqlite3.Connection,
    category_id: int,
    new_article_ids: Sequence[int],
) -> list[dict[str, Any]]:
    if not new_article_ids:
        return []
    placeholders = ",".join("?" for _ in new_article_ids)
    rows = conn.execute(
        f"""
        SELECT id, title, url, published_at, llm_summary
        FROM articles
        WHERE id IN ({placeholders})
          AND primary_category_id = ?
          AND status = 'ok'
        ORDER BY COALESCE(published_at, '') DESC, id DESC
        """,
        (*new_article_ids, category_id),
    ).fetchall()
    return [
        {
            "id": int(r["id"]),
            "title": r["title"],
            "url": r["url"],
            "published_at": r["published_at"],
            "llm_summary": r["llm_summary"],
        }
        for r in rows
    ]


def _load_existing_recent(
    conn: sqlite3.Connection,
    category_id: int,
    exclude_ids: Sequence[int],
    limit: int,
) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    if exclude_ids:
        placeholders = ",".join("?" for _ in exclude_ids)
        where_exclude = f"AND id NOT IN ({placeholders})"
        params: tuple[Any, ...] = (category_id, *exclude_ids, limit)
    else:
        where_exclude = ""
        params = (category_id, limit)
    rows = conn.execute(
        f"""
        SELECT id, title, published_at, llm_summary
        FROM articles
        WHERE primary_category_id = ?
          AND status = 'ok'
          {where_exclude}
        ORDER BY COALESCE(published_at, '') DESC, id DESC
        LIMIT ?
        """,
        params,
    ).fetchall()
    return [
        {
            "id": int(r["id"]),
            "title": r["title"],
            "published_at": r["published_at"],
            "one_line": _one_line(r["llm_summary"]),
        }
        for r in rows
    ]


def render_wiki_prompt(
    *,
    category_name: str,
    previous_wiki_markdown: str,
    new_articles: list[dict[str, Any]],
    existing_recent_articles: list[dict[str, Any]],
    env: Environment | None = None,
) -> str:
    template = (env or _ENV).get_template("wiki_rebuild.txt")
    return template.render(
        category_name=category_name,
        previous_wiki_markdown=previous_wiki_markdown,
        new_articles=new_articles,
        existing_recent_articles=existing_recent_articles,
    )


def pick_prompt_within_budget(
    *,
    category_name: str,
    previous_wiki_markdown: str,
    new_articles: list[dict[str, Any]],
    existing_recent_articles: list[dict[str, Any]],
    fallback_sizes: Sequence[int],
    char_limit: int = WIKI_REBUILD_INPUT_CHAR_LIMIT,
    env: Environment | None = None,
) -> tuple[str, int]:
    """가장 큰 `size` 부터 시도하며 `char_limit` 을 넘지 않는 프롬프트를 고른다.

    모든 크기가 한도를 넘으면 가장 작은 크기(보통 0)의 프롬프트를 반환한다.
    """
    rendered: str = ""
    chosen_size = fallback_sizes[-1]
    for size in fallback_sizes:
        truncated = existing_recent_articles[:size]
        rendered = render_wiki_prompt(
            category_name=category_name,
            previous_wiki_markdown=previous_wiki_markdown,
            new_articles=new_articles,
            existing_recent_articles=truncated,
            env=env,
        )
        chosen_size = size
        if len(rendered) <= char_limit:
            return rendered, size
    return rendered, chosen_size


def upsert_wiki_page(
    conn: sqlite3.Connection,
    *,
    category_id: int,
    content_markdown: str,
    articles_count: int,
) -> None:
    """wiki_pages 에 새로 INSERT 하거나 content 를 UPDATE. last_seen_at 은 보존."""
    row = conn.execute(
        "SELECT id FROM wiki_pages WHERE category_id = ?", (category_id,)
    ).fetchone()
    if row is None:
        conn.execute(
            """
            INSERT INTO wiki_pages (
                category_id, content_markdown, last_rebuilt_at,
                articles_count_at_rebuild, has_unread_updates
            ) VALUES (?, ?, datetime('now'), ?, 1)
            """,
            (category_id, content_markdown, articles_count),
        )
    else:
        conn.execute(
            """
            UPDATE wiki_pages
               SET content_markdown = ?,
                   last_rebuilt_at = datetime('now'),
                   articles_count_at_rebuild = ?,
                   has_unread_updates = 1
             WHERE category_id = ?
            """,
            (content_markdown, articles_count, category_id),
        )


def _count_category_articles(conn: sqlite3.Connection, category_id: int) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM articles "
        "WHERE primary_category_id = ? AND status = 'ok'",
        (category_id,),
    ).fetchone()
    return int(row["n"]) if row is not None else 0


async def rebuild_wiki_page(
    conn: sqlite3.Connection,
    *,
    category_id: int,
    new_article_ids: Sequence[int] | None = None,
    call_llm: ClaudeTextFn | None = None,
) -> RebuildOutcome:
    """한 카테고리의 위키 페이지를 재구성한다.

    - previous 가 빈 문자열이면 '최초 빌드' 로 간주하고 existing_recent 크기를 20부터 시작.
    - 총 입력 길이가 `WIKI_REBUILD_INPUT_CHAR_LIMIT` 을 넘으면 existing_recent 를 단계적으로 축소.
    - 해당 카테고리에 ok 상태 글이 하나도 없으면 `status='skipped'` 로 조기 반환 (LLM 미호출).
    """
    ids = list(new_article_ids or [])
    name = _load_category_name(conn, category_id)
    if name is None:
        return RebuildOutcome(
            category_id=category_id,
            status="failed",
            content_markdown=None,
            is_initial=False,
            used_existing_context_size=0,
            articles_count=0,
            error=f"category {category_id} not found",
        )

    previous = _load_previous_markdown(conn, category_id)
    is_initial = previous == ""

    new_articles = _load_new_articles(conn, category_id, ids)
    # existing_recent 에서는 새 글을 제외해 중복 노출을 막는다.
    existing_ids = [a["id"] for a in new_articles] if new_articles else list(ids)
    sizes = _fallback_sizes(is_initial)
    max_size = sizes[0]
    existing_recent = _load_existing_recent(
        conn, category_id, exclude_ids=existing_ids, limit=max_size
    )

    if not new_articles and not existing_recent:
        return RebuildOutcome(
            category_id=category_id,
            status="skipped",
            content_markdown=None,
            is_initial=is_initial,
            used_existing_context_size=0,
            articles_count=0,
            error="no articles for category",
        )

    prompt, used_size = pick_prompt_within_budget(
        category_name=name,
        previous_wiki_markdown=previous,
        new_articles=new_articles,
        existing_recent_articles=existing_recent,
        fallback_sizes=sizes,
        char_limit=WIKI_REBUILD_INPUT_CHAR_LIMIT,
    )

    llm = call_llm or _default_text_llm
    try:
        markdown = await llm(prompt)
    except LLMError as exc:
        return RebuildOutcome(
            category_id=category_id,
            status="failed",
            content_markdown=None,
            is_initial=is_initial,
            used_existing_context_size=used_size,
            articles_count=0,
            error=f"{type(exc).__name__}: {exc}",
        )

    content = (markdown or "").strip()
    if not content:
        return RebuildOutcome(
            category_id=category_id,
            status="failed",
            content_markdown=None,
            is_initial=is_initial,
            used_existing_context_size=used_size,
            articles_count=0,
            error="empty LLM output",
        )

    articles_count = _count_category_articles(conn, category_id)
    upsert_wiki_page(
        conn,
        category_id=category_id,
        content_markdown=content,
        articles_count=articles_count,
    )
    conn.commit()

    return RebuildOutcome(
        category_id=category_id,
        status="ok",
        content_markdown=content,
        is_initial=is_initial,
        used_existing_context_size=used_size,
        articles_count=articles_count,
    )


async def _default_text_llm(prompt: str) -> str:
    result = await call_claude_cli(prompt)
    return result.stdout
