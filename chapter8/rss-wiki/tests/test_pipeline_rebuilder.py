"""pipeline.rebuilder — 카테고리별 위키 페이지 재구성 (PRD §7.1 step 6, §8.2)."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pytest

from rss_wiki import db
from rss_wiki.pipeline import rebuilder
from rss_wiki.pipeline.llm import LLMError


@pytest.fixture
def conn(tmp_path: Path):
    connection = db.get_connection(tmp_path / "test.db")
    db.init_schema(connection)
    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture
def feed_id(conn: sqlite3.Connection) -> int:
    cursor = conn.execute(
        "INSERT INTO feeds (url, title) VALUES (?, ?)",
        ("https://example.com/rss", "Example"),
    )
    conn.commit()
    return int(cursor.lastrowid)


def _insert_category(conn: sqlite3.Connection, name: str) -> int:
    cursor = conn.execute(
        "INSERT INTO categories (name) VALUES (?)", (name,)
    )
    conn.commit()
    return int(cursor.lastrowid)


def _insert_article(
    conn: sqlite3.Connection,
    *,
    feed_id: int,
    category_id: int,
    url: str,
    title: str,
    published_at: str,
    llm_summary: str = "요약",
    status: str = "ok",
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO articles (
            feed_id, url, title, published_at, llm_summary,
            primary_category_id, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (feed_id, url, title, published_at, llm_summary, category_id, status),
    )
    conn.commit()
    return int(cursor.lastrowid)


def _llm_returning(markdown: str):
    async def fn(prompt: str) -> str:
        fn.calls.append(prompt)
        return markdown

    fn.calls = []  # type: ignore[attr-defined]
    return fn


def _llm_raising(exc: BaseException):
    async def fn(prompt: str) -> str:
        fn.calls.append(prompt)
        raise exc

    fn.calls = []  # type: ignore[attr-defined]
    return fn


# -----------------------------------------------------------------------------
# 유틸: _one_line, _fallback_sizes
# -----------------------------------------------------------------------------


def test_one_line_returns_first_non_empty_line():
    assert rebuilder._one_line("첫 줄\n둘째 줄") == "첫 줄"
    assert rebuilder._one_line("\n\n  실제 내용\n뒷 줄") == "실제 내용"
    assert rebuilder._one_line("") == ""
    assert rebuilder._one_line(None) == ""


def test_fallback_sizes_incremental_starts_at_ten():
    sizes = rebuilder._fallback_sizes(is_initial=False)
    assert sizes[0] == 10
    assert sizes[-1] == 0
    # 엄격히 감소
    assert list(sizes) == sorted(sizes, reverse=True)


def test_fallback_sizes_initial_starts_at_twenty_then_falls():
    sizes = rebuilder._fallback_sizes(is_initial=True)
    assert sizes[0] == 20
    assert sizes[-1] == 0
    assert list(sizes) == sorted(sizes, reverse=True)
    # 10,5,3,0 이 포함되어야 함
    for s in (10, 5, 3, 0):
        assert s in sizes


# -----------------------------------------------------------------------------
# render_wiki_prompt
# -----------------------------------------------------------------------------


def test_render_wiki_prompt_embeds_new_and_existing_articles():
    prompt = rebuilder.render_wiki_prompt(
        category_name="AI",
        previous_wiki_markdown="# AI\n기존",
        new_articles=[
            {
                "title": "새 글",
                "url": "https://example.com/a",
                "published_at": "2026-04-25",
                "llm_summary": "한 줄 요약.",
            }
        ],
        existing_recent_articles=[
            {
                "title": "예전 글",
                "published_at": "2026-04-01",
                "one_line": "예전 요약",
            }
        ],
    )
    assert "카테고리명: AI" in prompt
    assert "# AI\n기존" in prompt
    assert "제목: 새 글" in prompt
    assert "URL: https://example.com/a" in prompt
    assert "- 예전 글 (2026-04-01) — 예전 요약" in prompt


# -----------------------------------------------------------------------------
# pick_prompt_within_budget
# -----------------------------------------------------------------------------


def test_pick_prompt_uses_largest_size_when_within_budget():
    existing = [
        {"title": f"글{i}", "published_at": "2026-04-01", "one_line": "x"}
        for i in range(20)
    ]
    prompt, size = rebuilder.pick_prompt_within_budget(
        category_name="AI",
        previous_wiki_markdown="",
        new_articles=[],
        existing_recent_articles=existing,
        fallback_sizes=(10, 5, 3, 0),
        char_limit=100_000,
    )
    assert size == 10
    # 10개 만 들어갔는지 확인
    assert prompt.count("- 글") == 10


def test_pick_prompt_shrinks_when_over_budget():
    # 아주 긴 본문을 넣어 한도를 초과시킴
    long_line = "가" * 2_000
    existing = [
        {"title": f"글{i}", "published_at": "2026-04-01", "one_line": long_line}
        for i in range(20)
    ]
    prompt, size = rebuilder.pick_prompt_within_budget(
        category_name="AI",
        previous_wiki_markdown="",
        new_articles=[],
        existing_recent_articles=existing,
        fallback_sizes=(10, 5, 3, 0),
        char_limit=10_000,
    )
    # 10 개면 10 * 2000 = 20000자 → 초과. 5, 3 도 초과할 수 있음. 0 까지 내려가야 함.
    assert size in (5, 3, 0)
    if size == 0:
        assert long_line not in prompt


def test_pick_prompt_returns_smallest_size_when_all_exceed_budget():
    long_line = "가" * 50_000
    existing = [
        {"title": f"글{i}", "published_at": "2026-04-01", "one_line": long_line}
        for i in range(3)
    ]
    prompt, size = rebuilder.pick_prompt_within_budget(
        category_name="AI",
        previous_wiki_markdown="",
        new_articles=[],
        existing_recent_articles=existing,
        fallback_sizes=(3, 0),
        char_limit=100,
    )
    # 3 > 100자, 0도 카테고리명 등으로 100자 초과 가능. 마지막 크기(0)로 반환.
    assert size == 0


# -----------------------------------------------------------------------------
# upsert_wiki_page
# -----------------------------------------------------------------------------


def test_upsert_wiki_page_inserts_new_row(conn: sqlite3.Connection):
    cid = _insert_category(conn, "AI")
    rebuilder.upsert_wiki_page(
        conn, category_id=cid, content_markdown="# AI", articles_count=3
    )
    conn.commit()

    row = conn.execute(
        "SELECT content_markdown, articles_count_at_rebuild, has_unread_updates, "
        "last_rebuilt_at, last_seen_at FROM wiki_pages WHERE category_id=?",
        (cid,),
    ).fetchone()
    assert row["content_markdown"] == "# AI"
    assert row["articles_count_at_rebuild"] == 3
    assert row["has_unread_updates"] == 1
    assert row["last_rebuilt_at"] is not None
    assert row["last_seen_at"] is None


def test_upsert_wiki_page_updates_existing_and_preserves_last_seen_at(
    conn: sqlite3.Connection,
):
    cid = _insert_category(conn, "AI")
    # 먼저 페이지 생성 + 사용자 방문(last_seen_at 설정) 시뮬레이션
    conn.execute(
        """
        INSERT INTO wiki_pages (
            category_id, content_markdown, last_rebuilt_at,
            articles_count_at_rebuild, last_seen_at, has_unread_updates
        ) VALUES (?, '# 이전', datetime('now'), 1, '2026-04-20T00:00:00Z', 0)
        """,
        (cid,),
    )
    conn.commit()

    rebuilder.upsert_wiki_page(
        conn, category_id=cid, content_markdown="# 새 내용", articles_count=5
    )
    conn.commit()

    row = conn.execute(
        "SELECT content_markdown, articles_count_at_rebuild, has_unread_updates, "
        "last_seen_at FROM wiki_pages WHERE category_id=?",
        (cid,),
    ).fetchone()
    assert row["content_markdown"] == "# 새 내용"
    assert row["articles_count_at_rebuild"] == 5
    # 재구성했으니 다시 unread
    assert row["has_unread_updates"] == 1
    # 사용자 방문 기록은 유지되어야 함
    assert row["last_seen_at"] == "2026-04-20T00:00:00Z"


# -----------------------------------------------------------------------------
# rebuild_wiki_page — 성공 경로
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rebuild_wiki_page_initial_build_uses_up_to_20_articles(
    conn: sqlite3.Connection, feed_id: int
):
    cid = _insert_category(conn, "AI")
    ids = []
    # 25개를 넣으면 existing_recent 는 최대 20 만 가져와야 함 (초기 빌드)
    for i in range(25):
        aid = _insert_article(
            conn,
            feed_id=feed_id,
            category_id=cid,
            url=f"https://example.com/{i}",
            title=f"글{i}",
            published_at=f"2026-04-{(i % 28) + 1:02d}",
        )
        ids.append(aid)

    llm = _llm_returning("# AI\n\n## 한줄 요약\n요약")
    outcome = await rebuilder.rebuild_wiki_page(
        conn, category_id=cid, new_article_ids=[], call_llm=llm
    )

    assert outcome.status == "ok"
    assert outcome.is_initial is True
    assert outcome.used_existing_context_size == 20
    prompt = llm.calls[0]
    # existing_recent 에서 각 줄이 "- 글N (" 로 시작 → 20줄
    matches = prompt.count("- 글")
    assert matches == 20


@pytest.mark.asyncio
async def test_rebuild_wiki_page_incremental_build_uses_up_to_10_existing(
    conn: sqlite3.Connection, feed_id: int
):
    cid = _insert_category(conn, "AI")
    # 기존 페이지가 있어야 incremental
    conn.execute(
        "INSERT INTO wiki_pages (category_id, content_markdown, last_rebuilt_at) "
        "VALUES (?, '# AI\n기존', datetime('now'))",
        (cid,),
    )
    conn.commit()

    # 15개의 기존 글 + 1개의 새 글
    for i in range(15):
        _insert_article(
            conn,
            feed_id=feed_id,
            category_id=cid,
            url=f"https://example.com/old/{i}",
            title=f"기존{i}",
            published_at=f"2026-03-{(i % 28) + 1:02d}",
        )
    new_id = _insert_article(
        conn,
        feed_id=feed_id,
        category_id=cid,
        url="https://example.com/new/1",
        title="새 글",
        published_at="2026-04-25",
    )

    llm = _llm_returning("# AI\n내용")
    outcome = await rebuilder.rebuild_wiki_page(
        conn, category_id=cid, new_article_ids=[new_id], call_llm=llm
    )

    assert outcome.status == "ok"
    assert outcome.is_initial is False
    assert outcome.used_existing_context_size == 10

    prompt = llm.calls[0]
    assert "제목: 새 글" in prompt
    # existing_recent 는 최대 10개
    assert prompt.count("- 기존") == 10
    # 이전 위키 내용이 프롬프트에 포함
    assert "# AI\n기존" in prompt


@pytest.mark.asyncio
async def test_rebuild_wiki_page_writes_to_wiki_pages_and_commits(
    conn: sqlite3.Connection, feed_id: int, tmp_path: Path
):
    cid = _insert_category(conn, "AI")
    _insert_article(
        conn,
        feed_id=feed_id,
        category_id=cid,
        url="https://example.com/1",
        title="t",
        published_at="2026-04-25",
    )

    llm = _llm_returning("# AI\n\n## 한줄 요약\n요약")
    outcome = await rebuilder.rebuild_wiki_page(
        conn, category_id=cid, call_llm=llm
    )
    assert outcome.status == "ok"

    # 별도 커넥션에서도 보여야 함 → commit 완료
    other = db.get_connection(tmp_path / "test.db")
    try:
        row = other.execute(
            "SELECT content_markdown, has_unread_updates, articles_count_at_rebuild "
            "FROM wiki_pages WHERE category_id=?",
            (cid,),
        ).fetchone()
        assert row is not None
        assert row["content_markdown"] == "# AI\n\n## 한줄 요약\n요약"
        assert row["has_unread_updates"] == 1
        assert row["articles_count_at_rebuild"] == 1
    finally:
        other.close()


@pytest.mark.asyncio
async def test_rebuild_wiki_page_strips_trailing_whitespace_in_markdown(
    conn: sqlite3.Connection, feed_id: int
):
    cid = _insert_category(conn, "AI")
    _insert_article(
        conn,
        feed_id=feed_id,
        category_id=cid,
        url="https://example.com/1",
        title="t",
        published_at="2026-04-25",
    )

    llm = _llm_returning("\n\n# AI 내용\n\n")
    outcome = await rebuilder.rebuild_wiki_page(
        conn, category_id=cid, call_llm=llm
    )
    assert outcome.status == "ok"
    assert outcome.content_markdown == "# AI 내용"


# -----------------------------------------------------------------------------
# rebuild_wiki_page — 100k 자 가드
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rebuild_wiki_page_respects_char_limit_shrinking_existing(
    conn: sqlite3.Connection, feed_id: int, monkeypatch
):
    cid = _insert_category(conn, "AI")
    # 이전 위키가 있어 incremental 로 들어감.
    conn.execute(
        "INSERT INTO wiki_pages (category_id, content_markdown, last_rebuilt_at) "
        "VALUES (?, '# AI', datetime('now'))",
        (cid,),
    )
    conn.commit()

    long_summary = "가" * 5_000
    for i in range(10):
        _insert_article(
            conn,
            feed_id=feed_id,
            category_id=cid,
            url=f"https://example.com/old/{i}",
            title=f"기존{i}",
            published_at=f"2026-03-{(i % 28) + 1:02d}",
            llm_summary=long_summary,
        )
    new_id = _insert_article(
        conn,
        feed_id=feed_id,
        category_id=cid,
        url="https://example.com/new/1",
        title="새",
        published_at="2026-04-25",
    )

    # 한도를 낮춰서 10 → 더 작은 크기로 내려가게 강제
    monkeypatch.setattr(rebuilder, "WIKI_REBUILD_INPUT_CHAR_LIMIT", 8_000)

    llm = _llm_returning("# AI\n내용")
    outcome = await rebuilder.rebuild_wiki_page(
        conn, category_id=cid, new_article_ids=[new_id], call_llm=llm
    )
    assert outcome.status == "ok"
    assert outcome.used_existing_context_size in (5, 3, 0)
    # 새 글은 반드시 포함
    assert "제목: 새" in llm.calls[0]


# -----------------------------------------------------------------------------
# rebuild_wiki_page — 실패 / 스킵
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rebuild_wiki_page_returns_failed_on_llm_error(
    conn: sqlite3.Connection, feed_id: int
):
    cid = _insert_category(conn, "AI")
    _insert_article(
        conn,
        feed_id=feed_id,
        category_id=cid,
        url="https://example.com/1",
        title="t",
        published_at="2026-04-25",
    )
    llm = _llm_raising(LLMError("subprocess died"))
    outcome = await rebuilder.rebuild_wiki_page(
        conn, category_id=cid, call_llm=llm
    )
    assert outcome.status == "failed"
    assert "subprocess died" in (outcome.error or "")
    # 실패 시 wiki_pages 에 커밋되면 안 됨
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM wiki_pages WHERE category_id=?", (cid,)
    ).fetchone()
    assert row["n"] == 0


@pytest.mark.asyncio
async def test_rebuild_wiki_page_returns_failed_on_empty_llm_output(
    conn: sqlite3.Connection, feed_id: int
):
    cid = _insert_category(conn, "AI")
    _insert_article(
        conn,
        feed_id=feed_id,
        category_id=cid,
        url="https://example.com/1",
        title="t",
        published_at="2026-04-25",
    )
    llm = _llm_returning("   \n\n  ")
    outcome = await rebuilder.rebuild_wiki_page(
        conn, category_id=cid, call_llm=llm
    )
    assert outcome.status == "failed"
    assert "empty" in (outcome.error or "").lower()


@pytest.mark.asyncio
async def test_rebuild_wiki_page_skips_when_no_articles(
    conn: sqlite3.Connection,
):
    cid = _insert_category(conn, "AI")
    llm = _llm_returning("# 아무거나")
    outcome = await rebuilder.rebuild_wiki_page(
        conn, category_id=cid, call_llm=llm
    )
    assert outcome.status == "skipped"
    assert llm.calls == []
    # 페이지가 새로 생성되면 안 됨
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM wiki_pages WHERE category_id=?", (cid,)
    ).fetchone()
    assert row["n"] == 0


@pytest.mark.asyncio
async def test_rebuild_wiki_page_returns_failed_when_category_missing(
    conn: sqlite3.Connection,
):
    llm = _llm_returning("# nope")
    outcome = await rebuilder.rebuild_wiki_page(
        conn, category_id=9999, call_llm=llm
    )
    assert outcome.status == "failed"
    assert "not found" in (outcome.error or "")
    assert llm.calls == []


@pytest.mark.asyncio
async def test_rebuild_wiki_page_excludes_failed_articles_from_context(
    conn: sqlite3.Connection, feed_id: int
):
    cid = _insert_category(conn, "AI")
    _insert_article(
        conn,
        feed_id=feed_id,
        category_id=cid,
        url="https://example.com/ok",
        title="정상",
        published_at="2026-04-25",
    )
    _insert_article(
        conn,
        feed_id=feed_id,
        category_id=cid,
        url="https://example.com/bad",
        title="실패",
        published_at="2026-04-26",
        llm_summary=None,
        status="failed",
    )

    llm = _llm_returning("# AI")
    outcome = await rebuilder.rebuild_wiki_page(
        conn, category_id=cid, call_llm=llm
    )
    assert outcome.status == "ok"
    prompt = llm.calls[0]
    assert "정상" in prompt
    assert "실패" not in prompt
    # articles_count 는 ok 만 카운트
    assert outcome.articles_count == 1


@pytest.mark.asyncio
async def test_rebuild_wiki_page_does_not_duplicate_new_in_existing(
    conn: sqlite3.Connection, feed_id: int
):
    cid = _insert_category(conn, "AI")
    # 이전 위키 있음 → incremental
    conn.execute(
        "INSERT INTO wiki_pages (category_id, content_markdown, last_rebuilt_at) "
        "VALUES (?, '# AI 이전', datetime('now'))",
        (cid,),
    )
    conn.commit()

    new_id = _insert_article(
        conn,
        feed_id=feed_id,
        category_id=cid,
        url="https://example.com/new",
        title="유일한 새 글",
        published_at="2026-04-25",
    )

    llm = _llm_returning("# AI")
    await rebuilder.rebuild_wiki_page(
        conn, category_id=cid, new_article_ids=[new_id], call_llm=llm
    )

    prompt = llm.calls[0]
    # "유일한 새 글" 문자열이 new_articles 섹션에만 1회 등장 (existing_recent 에 중복 금지)
    assert prompt.count("유일한 새 글") == 1
