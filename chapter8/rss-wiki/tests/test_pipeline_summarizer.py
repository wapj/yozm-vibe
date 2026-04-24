"""pipeline.summarizer — 개별 글 요약/분류 + articles INSERT + 카테고리 upsert (PRD §7.1 step 4)."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pytest

from rss_wiki import db
from rss_wiki.pipeline import summarizer
from rss_wiki.pipeline.extractor import ExtractionResult
from rss_wiki.pipeline.fetcher import FeedEntry
from rss_wiki.pipeline.llm import LLMError, LLMJSONParseError


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


def _entry(url: str = "https://example.com/a", title: str = "제목") -> FeedEntry:
    return FeedEntry(
        url=url,
        title=title,
        author="저자",
        published_at="2026-04-25T00:00:00Z",
        raw_summary="원문 요약",
    )


def _trafilatura_extraction(text: str = "본문 전문") -> ExtractionResult:
    return ExtractionResult(text=text, source="trafilatura")


def _fallback_extraction(text: str = "원문 요약") -> ExtractionResult:
    return ExtractionResult(text=text, source="fallback")


def _llm_returning(payload: Any):
    async def fn(prompt: str) -> Any:
        fn.calls.append(prompt)
        return payload

    fn.calls = []  # type: ignore[attr-defined]
    return fn


def _llm_raising(exc: BaseException):
    async def fn(prompt: str) -> Any:
        fn.calls.append(prompt)
        raise exc

    fn.calls = []  # type: ignore[attr-defined]
    return fn


# -----------------------------------------------------------------------------
# upsert_category
# -----------------------------------------------------------------------------


def test_upsert_category_inserts_new_when_missing(conn: sqlite3.Connection):
    cid = summarizer.upsert_category(conn, "AI")
    assert cid > 0
    row = conn.execute("SELECT name FROM categories WHERE id=?", (cid,)).fetchone()
    assert row["name"] == "AI"


def test_upsert_category_returns_existing_id_when_present(conn: sqlite3.Connection):
    first = summarizer.upsert_category(conn, "AI")
    second = summarizer.upsert_category(conn, "AI")
    assert first == second
    count = conn.execute("SELECT COUNT(*) AS n FROM categories").fetchone()["n"]
    assert count == 1


# -----------------------------------------------------------------------------
# list_existing_categories
# -----------------------------------------------------------------------------


def test_list_existing_categories_excludes_merged(conn: sqlite3.Connection):
    target = summarizer.upsert_category(conn, "AI")
    merged = summarizer.upsert_category(conn, "인공지능")
    conn.execute(
        "UPDATE categories SET merged_into_id=? WHERE id=?", (target, merged)
    )
    conn.commit()

    names = [c["name"] for c in summarizer.list_existing_categories(conn)]
    assert names == ["AI"]


def test_list_existing_categories_returns_name_and_description(
    conn: sqlite3.Connection,
):
    conn.execute(
        "INSERT INTO categories (name, description) VALUES (?, ?)",
        ("LLM", "대형언어모델"),
    )
    conn.commit()
    cats = summarizer.list_existing_categories(conn)
    assert cats == [{"id": cats[0]["id"], "name": "LLM", "description": "대형언어모델"}]


# -----------------------------------------------------------------------------
# render_article_prompt
# -----------------------------------------------------------------------------


def test_render_article_prompt_embeds_categories_and_content():
    prompt = summarizer.render_article_prompt(
        existing_categories=[{"name": "AI", "description": None}],
        title="t",
        url="u",
        detected_language="ko",
        content="본문",
    )
    assert "- AI" in prompt
    assert "제목: t" in prompt
    assert "원문 URL: u" in prompt
    assert "언어: ko" in prompt
    assert "본문" in prompt
    assert "응답은 반드시 유효한 JSON" in prompt


# -----------------------------------------------------------------------------
# summarize_article — 성공 경로
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_summarize_article_inserts_ok_and_upserts_new_category(
    conn: sqlite3.Connection, feed_id: int
):
    llm = _llm_returning(
        {
            "summary": "한국어 3-5문장 요약",
            "category_name": "LLM 에이전트",
            "is_new_category": True,
            "language_detected": "ko",
        }
    )

    outcome = await summarizer.summarize_article(
        conn,
        feed_id=feed_id,
        entry=_entry(),
        extraction=_trafilatura_extraction("본문 전문입니다."),
        detected_language="ko",
        call_llm=llm,
    )

    assert outcome.status == "ok"
    assert outcome.error is None
    assert outcome.category_id is not None

    row = conn.execute(
        "SELECT * FROM articles WHERE id=?", (outcome.article_id,)
    ).fetchone()
    assert row["status"] == "ok"
    assert row["llm_summary"] == "한국어 3-5문장 요약"
    assert row["primary_category_id"] == outcome.category_id
    assert row["language"] == "ko"
    assert row["extracted_content"] == "본문 전문입니다."
    assert row["raw_summary"] == "원문 요약"
    assert row["feed_id"] == feed_id
    assert row["title"] == "제목"
    assert row["url"] == "https://example.com/a"

    cat = conn.execute(
        "SELECT name FROM categories WHERE id=?", (outcome.category_id,)
    ).fetchone()
    assert cat["name"] == "LLM 에이전트"

    assert len(llm.calls) == 1
    assert "제목: 제목" in llm.calls[0]


@pytest.mark.asyncio
async def test_summarize_article_reuses_existing_category(
    conn: sqlite3.Connection, feed_id: int
):
    existing = summarizer.upsert_category(conn, "AI")
    conn.commit()

    llm = _llm_returning(
        {
            "summary": "요약",
            "category_name": "AI",
            "is_new_category": False,
            "language_detected": "ko",
        }
    )

    outcome = await summarizer.summarize_article(
        conn,
        feed_id=feed_id,
        entry=_entry(url="https://example.com/b"),
        extraction=_trafilatura_extraction(),
        call_llm=llm,
    )

    assert outcome.category_id == existing
    count = conn.execute("SELECT COUNT(*) AS n FROM categories").fetchone()["n"]
    assert count == 1


@pytest.mark.asyncio
async def test_summarize_article_sets_extracted_content_null_on_fallback(
    conn: sqlite3.Connection, feed_id: int
):
    llm = _llm_returning(
        {"summary": "요약", "category_name": "AI", "language_detected": "ko"}
    )

    outcome = await summarizer.summarize_article(
        conn,
        feed_id=feed_id,
        entry=_entry(),
        extraction=_fallback_extraction("RSS 요약만 있는 경우"),
        call_llm=llm,
    )

    assert outcome.status == "ok"
    row = conn.execute(
        "SELECT extracted_content, raw_summary FROM articles WHERE id=?",
        (outcome.article_id,),
    ).fetchone()
    # trafilatura 추출이 아니면 extracted_content 는 NULL — FTS 에도 본문은 들어가지 않음.
    assert row["extracted_content"] is None
    assert row["raw_summary"] == "원문 요약"


@pytest.mark.asyncio
async def test_summarize_article_commits_changes(
    conn: sqlite3.Connection, feed_id: int, tmp_path: Path
):
    llm = _llm_returning({"summary": "s", "category_name": "AI"})
    outcome = await summarizer.summarize_article(
        conn,
        feed_id=feed_id,
        entry=_entry(),
        extraction=_trafilatura_extraction(),
        call_llm=llm,
    )
    # 별도 connection 에서 읽어도 보여야 함 → commit 된 상태.
    other = db.get_connection(tmp_path / "test.db")
    try:
        row = other.execute(
            "SELECT id FROM articles WHERE id=?", (outcome.article_id,)
        ).fetchone()
        assert row is not None
    finally:
        other.close()


# -----------------------------------------------------------------------------
# summarize_article — 실패 경로 (status='failed')
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_summarize_article_inserts_failed_on_llm_error(
    conn: sqlite3.Connection, feed_id: int
):
    llm = _llm_raising(LLMError("subprocess died"))

    outcome = await summarizer.summarize_article(
        conn,
        feed_id=feed_id,
        entry=_entry(),
        extraction=_trafilatura_extraction(),
        call_llm=llm,
    )

    assert outcome.status == "failed"
    assert outcome.category_id is None
    assert "subprocess died" in (outcome.error or "")

    row = conn.execute(
        "SELECT status, llm_summary, primary_category_id FROM articles WHERE id=?",
        (outcome.article_id,),
    ).fetchone()
    assert row["status"] == "failed"
    assert row["llm_summary"] is None
    assert row["primary_category_id"] is None


@pytest.mark.asyncio
async def test_summarize_article_inserts_failed_on_json_parse_error(
    conn: sqlite3.Connection, feed_id: int
):
    llm = _llm_raising(LLMJSONParseError("could not parse"))

    outcome = await summarizer.summarize_article(
        conn,
        feed_id=feed_id,
        entry=_entry(),
        extraction=_trafilatura_extraction(),
        call_llm=llm,
    )

    assert outcome.status == "failed"
    row = conn.execute(
        "SELECT status FROM articles WHERE id=?", (outcome.article_id,)
    ).fetchone()
    assert row["status"] == "failed"


@pytest.mark.asyncio
async def test_summarize_article_failed_when_response_missing_summary(
    conn: sqlite3.Connection, feed_id: int
):
    llm = _llm_returning({"category_name": "AI"})  # summary 누락

    outcome = await summarizer.summarize_article(
        conn,
        feed_id=feed_id,
        entry=_entry(),
        extraction=_trafilatura_extraction(),
        call_llm=llm,
    )

    assert outcome.status == "failed"
    assert "summary" in (outcome.error or "")
    cnt = conn.execute("SELECT COUNT(*) AS n FROM categories").fetchone()["n"]
    assert cnt == 0  # 실패 시 카테고리 생성되지 않아야 함


@pytest.mark.asyncio
async def test_summarize_article_failed_when_response_missing_category(
    conn: sqlite3.Connection, feed_id: int
):
    llm = _llm_returning({"summary": "요약"})

    outcome = await summarizer.summarize_article(
        conn,
        feed_id=feed_id,
        entry=_entry(),
        extraction=_trafilatura_extraction(),
        call_llm=llm,
    )

    assert outcome.status == "failed"


@pytest.mark.asyncio
async def test_summarize_article_failed_when_content_is_empty(
    conn: sqlite3.Connection, feed_id: int
):
    llm = _llm_returning({"summary": "s", "category_name": "AI"})

    outcome = await summarizer.summarize_article(
        conn,
        feed_id=feed_id,
        entry=_entry(),
        extraction=ExtractionResult(text=None, source="none"),
        call_llm=llm,
    )

    assert outcome.status == "failed"
    assert "empty content" in (outcome.error or "")
    assert llm.calls == []  # 본문이 없으면 LLM 호출 자체를 생략


@pytest.mark.asyncio
async def test_summarize_article_rejects_whitespace_only_category_name(
    conn: sqlite3.Connection, feed_id: int
):
    llm = _llm_returning({"summary": "요약", "category_name": "   "})

    outcome = await summarizer.summarize_article(
        conn,
        feed_id=feed_id,
        entry=_entry(),
        extraction=_trafilatura_extraction(),
        call_llm=llm,
    )

    assert outcome.status == "failed"


# -----------------------------------------------------------------------------
# 프롬프트 주입 검증
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_summarize_article_injects_existing_categories_into_prompt(
    conn: sqlite3.Connection, feed_id: int
):
    summarizer.upsert_category(conn, "AI")
    summarizer.upsert_category(conn, "데이터 엔지니어링")
    conn.commit()

    llm = _llm_returning({"summary": "s", "category_name": "AI"})
    await summarizer.summarize_article(
        conn,
        feed_id=feed_id,
        entry=_entry(),
        extraction=_trafilatura_extraction("본문"),
        detected_language="ko",
        call_llm=llm,
    )

    prompt = llm.calls[0]
    assert "- AI" in prompt
    assert "- 데이터 엔지니어링" in prompt
    assert "본문" in prompt
