from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from rss_wiki.config import FeedConfig
from rss_wiki.ingest.fetcher import FeedEntry
from rss_wiki.storage.db import get_connection, init_db
from rss_wiki.storage.repo import insert_article, upsert_feed
from rss_wiki.cli import is_friday, is_last_friday_of_month, run_daily, run_weekly, run_monthly, run_web, main
import rss_wiki.cli


def _setup_db(tmp_path: Path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    conn = get_connection(db_path)
    return db_path, conn


def _fake_runner(prompt: str) -> str:
    if "JSON 스키마" in prompt:
        return json.dumps({"summary": "요약", "category": "AI", "tags": ["llm"]})
    if "주간(한 주)" in prompt:
        return "주간 통합 요약 단락"
    if "월간(한 달)" in prompt:
        return "월간 통합 요약 단락"
    return "AI 트렌드 단락"


# --- 트리거 판정 함수 테스트 ---

def test_is_friday_true_for_friday():
    assert is_friday(date(2026, 5, 1)) is True   # 금요일
    assert is_friday(date(2026, 5, 2)) is False   # 토요일
    assert is_friday(date(2026, 5, 4)) is False   # 월요일


def test_is_last_friday_of_month_true_for_last_friday():
    # 5월 마지막 금요일: 29+7=36 > 31 → True
    assert is_last_friday_of_month(date(2026, 5, 29)) is True


def test_is_last_friday_of_month_false_for_non_last_friday():
    # 5월 22일 금요일, 다음 금요일(29일)이 같은 5월에 있음 → False
    assert is_last_friday_of_month(date(2026, 5, 22)) is False


def test_is_last_friday_of_month_false_for_non_friday():
    # 5월 31일 일요일
    assert is_last_friday_of_month(date(2026, 5, 31)) is False


# --- run_daily 테스트 ---

def test_run_daily_invokes_pipeline_and_commits(tmp_path, monkeypatch):
    db_path, conn = _setup_db(tmp_path)
    output_dir = tmp_path / "output"
    feeds = [FeedConfig(name="TestFeed", url="https://example.com/rss")]

    fake_entry = FeedEntry(
        url="https://example.com/article/1",
        title="AI 글제목",
        published_at="2026-05-04",
        summary=None,
    )
    monkeypatch.setattr("rss_wiki.pipeline.ingest.fetch_feed", lambda url: [fake_entry])
    monkeypatch.setattr("rss_wiki.pipeline.ingest.extract_body", lambda entry: "본문 내용")

    try:
        result = run_daily(
            conn=conn,
            feeds=feeds,
            output_dir=output_dir,
            runner=_fake_runner,
            now=date(2026, 5, 4),  # 월요일, 트리거 미충족
        )
    finally:
        conn.close()

    assert result == 0
    assert (output_dir / "daily-2026-05-04.md").exists()
    assert not list(output_dir.glob("weekly-*.md"))
    assert not list(output_dir.glob("monthly-*.md"))

    # conn.commit() 검증: 새 connection으로 row 확인
    conn2 = get_connection(db_path)
    try:
        count = conn2.execute("SELECT COUNT(*) FROM magazines WHERE kind='daily'").fetchone()[0]
        assert count == 1
    finally:
        conn2.close()


def test_run_daily_triggers_weekly_on_friday(tmp_path, monkeypatch):
    db_path, conn = _setup_db(tmp_path)
    output_dir = tmp_path / "output"
    feeds = [FeedConfig(name="TestFeed", url="https://example.com/rss")]

    # 사전 INSERT: published_at="2026-05-01", summary 빈 문자열 (미분석)
    feed_id = upsert_feed(conn, "TestFeed", "https://example.com/rss")
    insert_article(
        conn,
        feed_id=feed_id,
        url="https://example.com/friday-article",
        url_hash="hash_friday_article",
        title="금요일 글",
        title_hash="th_friday_article",
        published_at="2026-05-01",
        content="금요일 본문",
        summary="",
    )

    # 새 항목 없음 (이미 DB에 있는 글 사용)
    monkeypatch.setattr("rss_wiki.pipeline.ingest.fetch_feed", lambda url: [])

    try:
        result = run_daily(
            conn=conn,
            feeds=feeds,
            output_dir=output_dir,
            runner=_fake_runner,
            now=date(2026, 5, 1),  # 금요일, 마지막 금요일 아님
        )
    finally:
        conn.close()

    assert result == 0
    assert (output_dir / "daily-2026-05-01.md").exists()
    assert (output_dir / "weekly-2026-W18.md").exists()
    assert not list(output_dir.glob("monthly-*.md"))

    conn2 = get_connection(db_path)
    try:
        rows = conn2.execute("SELECT kind FROM magazines ORDER BY id ASC").fetchall()
        assert len(rows) == 2
        kinds = {r["kind"] for r in rows}
        assert kinds == {"daily", "weekly"}
    finally:
        conn2.close()


def test_run_daily_triggers_monthly_on_last_friday(tmp_path, monkeypatch):
    db_path, conn = _setup_db(tmp_path)
    output_dir = tmp_path / "output"
    feeds = [FeedConfig(name="TestFeed", url="https://example.com/rss")]

    # 사전 INSERT: published_at="2026-05-15", summary 빈 문자열 (월간 범위에 포함)
    feed_id = upsert_feed(conn, "TestFeed", "https://example.com/rss")
    insert_article(
        conn,
        feed_id=feed_id,
        url="https://example.com/monthly-article",
        url_hash="hash_monthly_article",
        title="월간 테스트 글",
        title_hash="th_monthly_article",
        published_at="2026-05-15",
        content="월간 본문",
        summary="",
    )

    # 페처는 주간 범위[2026-05-23, 2026-05-29]에 속하는 글 1개 반환
    weekly_entry = FeedEntry(
        url="https://example.com/weekly-article",
        title="주간 테스트 글",
        published_at="2026-05-27",
        summary=None,
    )
    monkeypatch.setattr("rss_wiki.pipeline.ingest.fetch_feed", lambda url: [weekly_entry])
    monkeypatch.setattr("rss_wiki.pipeline.ingest.extract_body", lambda entry: "주간 본문")

    try:
        result = run_daily(
            conn=conn,
            feeds=feeds,
            output_dir=output_dir,
            runner=_fake_runner,
            now=date(2026, 5, 29),  # 5월 마지막 금요일
        )
    finally:
        conn.close()

    assert result == 0
    assert (output_dir / "daily-2026-05-29.md").exists()
    assert (output_dir / "weekly-2026-W22.md").exists()
    assert (output_dir / "monthly-2026-05.md").exists()

    conn2 = get_connection(db_path)
    try:
        count = conn2.execute("SELECT COUNT(*) FROM magazines").fetchone()[0]
        assert count == 3
        kinds = {r["kind"] for r in conn2.execute("SELECT kind FROM magazines").fetchall()}
        assert kinds == {"daily", "weekly", "monthly"}
    finally:
        conn2.close()


# --- run_weekly 테스트 ---

def test_run_weekly_bypasses_trigger(tmp_path):
    db_path, conn = _setup_db(tmp_path)
    output_dir = tmp_path / "output"

    # 주간 범위 [2026-04-28, 2026-05-04] 안에 article 1개
    feed_id = upsert_feed(conn, "TestFeed", "https://example.com/rss")
    insert_article(
        conn,
        feed_id=feed_id,
        url="https://example.com/weekly-bypass-article",
        url_hash="hash_weekly_bypass",
        title="주간 우회 테스트 글",
        title_hash="th_weekly_bypass",
        published_at="2026-05-04",
        content="본문",
        summary="기존 요약",
    )

    try:
        result = run_weekly(
            conn=conn,
            end_date="2026-05-04",
            output_dir=output_dir,
            runner=_fake_runner,
        )
    finally:
        conn.close()

    assert result == 0
    assert (output_dir / "weekly-2026-W19.md").exists()
    assert not list(output_dir.glob("daily-*.md"))

    conn2 = get_connection(db_path)
    try:
        count = conn2.execute("SELECT COUNT(*) FROM magazines WHERE kind='weekly'").fetchone()[0]
        assert count == 1
    finally:
        conn2.close()


# --- run_monthly 테스트 ---

def test_run_monthly_bypasses_trigger(tmp_path):
    db_path, conn = _setup_db(tmp_path)
    output_dir = tmp_path / "output"

    # 월간 범위 [2026-05-01, 2026-05-29] 안에 article 1개
    feed_id = upsert_feed(conn, "TestFeed", "https://example.com/rss")
    insert_article(
        conn,
        feed_id=feed_id,
        url="https://example.com/monthly-bypass-article",
        url_hash="hash_monthly_bypass",
        title="월간 우회 테스트 글",
        title_hash="th_monthly_bypass",
        published_at="2026-05-15",
        content="본문",
        summary="기존 요약",
    )

    try:
        result = run_monthly(
            conn=conn,
            end_date="2026-05-29",
            output_dir=output_dir,
            runner=_fake_runner,
        )
    finally:
        conn.close()

    assert result == 0
    assert (output_dir / "monthly-2026-05.md").exists()

    conn2 = get_connection(db_path)
    try:
        count = conn2.execute("SELECT COUNT(*) FROM magazines WHERE kind='monthly'").fetchone()[0]
        assert count == 1
    finally:
        conn2.close()


# --- main 디스패치 테스트 ---

def test_main_dispatches_daily_subcommand(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    feeds_toml = tmp_path / "feeds.toml"
    feeds_toml.write_text('[[feed]]\nurl = "https://example.com/rss"\nname = "Test"\n')
    output_dir = tmp_path / "output"

    monkeypatch.setattr(rss_wiki.cli, "run_daily", lambda **kw: 0)

    result = main([
        "--db", str(db_path),
        "--feeds", str(feeds_toml),
        "--output", str(output_dir),
        "daily",
    ])

    assert result == 0
    assert db_path.exists()


def test_main_dispatches_weekly_subcommand(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    feeds_toml = tmp_path / "feeds.toml"
    feeds_toml.write_text('[[feed]]\nurl = "https://example.com/rss"\nname = "Test"\n')
    output_dir = tmp_path / "output"

    captured: dict = {}

    def fake_run_weekly(**kw):
        captured.update(kw)
        return 0

    claude_call: dict = {}

    def fake_call_claude(prompt, *, timeout):
        claude_call["prompt"] = prompt
        claude_call["timeout"] = timeout
        return "ok"

    monkeypatch.setattr(rss_wiki.cli, "call_claude", fake_call_claude)
    monkeypatch.setattr(rss_wiki.cli, "run_weekly", fake_run_weekly)

    result = main([
        "--db", str(db_path),
        "--feeds", str(feeds_toml),
        "--output", str(output_dir),
        "weekly",
        "--end-date", "2026-05-04",
        "--llm-timeout", "180",
    ])

    assert result == 0
    assert db_path.exists()
    assert captured.get("end_date") == "2026-05-04"
    assert captured["runner"]("prompt") == "ok"
    assert claude_call == {"prompt": "prompt", "timeout": 180.0}


def test_main_daily_bootstraps_and_runs(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    feeds_toml = tmp_path / "feeds.toml"
    feeds_toml.write_text('[[feed]]\nurl = "https://example.com/rss"\nname = "Test"\n')
    output_dir = tmp_path / "output"

    def fake_run_daily(**kw):
        kw["conn"].commit()
        return 0

    monkeypatch.setattr(rss_wiki.cli, "run_daily", fake_run_daily)

    result = main([
        "--db", str(db_path),
        "--feeds", str(feeds_toml),
        "--output", str(output_dir),
        "daily",
    ])

    assert result == 0
    conn = get_connection(db_path)
    try:
        rows = conn.execute("SELECT * FROM feeds").fetchall()
        assert len(rows) >= 1
        assert rows[0]["url"] == "https://example.com/rss"
    finally:
        conn.close()


def test_main_dispatches_monthly_subcommand(tmp_path, monkeypatch):
    db_path = tmp_path / "db.sqlite"
    feeds_toml = tmp_path / "feeds.toml"
    feeds_toml.write_text('[[feed]]\nurl = "https://example.com/rss"\nname = "Test"\n')
    output_dir = tmp_path / "output"

    captured: dict = {}

    def fake_run_monthly(**kw):
        captured.update(kw)
        return 0

    monkeypatch.setattr(rss_wiki.cli, "run_monthly", fake_run_monthly)

    result = main([
        "--db", str(db_path),
        "--feeds", str(feeds_toml),
        "--output", str(output_dir),
        "monthly",
        "--end-date", "2026-05-29",
    ])

    assert result == 0
    assert db_path.exists()
    assert captured.get("end_date") == "2026-05-29"


# --- run_web / web 서브커맨드 테스트 ---

def test_run_web_invokes_uvicorn_with_create_app(tmp_path):
    from fastapi import FastAPI

    db_path = tmp_path / "x.db"
    init_db(db_path)

    captured: list[tuple] = []

    def fake(app, **kw):
        captured.append((app, kw))

    rc = run_web(db_path=db_path, host="127.0.0.1", port=8765, run_uvicorn=fake)

    assert rc == 0
    assert len(captured) == 1
    (app, kw) = captured[0]
    assert kw["host"] == "127.0.0.1"
    assert kw["port"] == 8765
    assert kw["log_level"] == "info"
    assert isinstance(app, FastAPI)


def test_run_web_passes_custom_host_port(tmp_path):
    from fastapi import FastAPI

    db_path = tmp_path / "x.db"
    init_db(db_path)

    captured: list[tuple] = []

    def fake(app, **kw):
        captured.append((app, kw))

    run_web(db_path=db_path, host="0.0.0.0", port=9000, run_uvicorn=fake)

    assert len(captured) == 1
    (app, kw) = captured[0]
    assert kw["host"] == "0.0.0.0"
    assert kw["port"] == 9000


def test_main_web_subcommand_routes_to_run_web(tmp_path, monkeypatch):
    db_path = tmp_path / "x.db"

    captured: list[tuple] = []

    def fake(app, **kw):
        captured.append((app, kw))

    monkeypatch.setattr(rss_wiki.cli, "_default_uvicorn_run", lambda: fake)

    rc = main(["--db", str(db_path), "web"])

    assert rc == 0
    assert len(captured) == 1
    assert captured[0][1]["host"] == "127.0.0.1"
    assert captured[0][1]["port"] == 8765


def test_main_web_subcommand_honors_host_port_args(tmp_path, monkeypatch):
    db_path = tmp_path / "x.db"

    captured: list[tuple] = []

    def fake(app, **kw):
        captured.append((app, kw))

    monkeypatch.setattr(rss_wiki.cli, "_default_uvicorn_run", lambda: fake)

    main(["--db", str(db_path), "web", "--host", "0.0.0.0", "--port", "9000"])

    assert len(captured) == 1
    assert captured[0][1]["host"] == "0.0.0.0"
    assert captured[0][1]["port"] == 9000
