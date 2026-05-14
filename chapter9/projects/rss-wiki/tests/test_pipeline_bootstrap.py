from __future__ import annotations

from pathlib import Path

import pytest

from rss_wiki.storage.db import get_connection, init_db
from rss_wiki.storage.repo import list_feeds
from rss_wiki.pipeline.bootstrap import bootstrap_feeds_from_toml


def _make_db(tmp_path: Path):
    db_path = tmp_path / "test.db"
    init_db(db_path)
    conn = get_connection(db_path)
    return conn


def _write_toml(tmp_path: Path, feeds: list[tuple[str, str]]) -> Path:
    lines = []
    for name, url in feeds:
        lines.append(f'[[feed]]\nname = "{name}"\nurl = "{url}"\n')
    toml_path = tmp_path / "feeds.toml"
    toml_path.write_text("\n".join(lines), encoding="utf-8")
    return toml_path


def test_bootstrap_inserts_all_feeds(tmp_path):
    conn = _make_db(tmp_path)
    toml_path = _write_toml(tmp_path, [
        ("Feed A", "https://example.com/a.rss"),
        ("Feed B", "https://example.com/b.rss"),
    ])
    try:
        bootstrap_feeds_from_toml(conn, toml_path)
        conn.commit()
        rows = list_feeds(conn)
        assert len(rows) == 2
        urls = {r["url"] for r in rows}
        names = {r["name"] for r in rows}
        assert urls == {"https://example.com/a.rss", "https://example.com/b.rss"}
        assert names == {"Feed A", "Feed B"}
    finally:
        conn.close()


def test_bootstrap_idempotent(tmp_path):
    conn = _make_db(tmp_path)
    toml_path = _write_toml(tmp_path, [
        ("Feed A", "https://example.com/a.rss"),
        ("Feed B", "https://example.com/b.rss"),
    ])
    try:
        bootstrap_feeds_from_toml(conn, toml_path)
        bootstrap_feeds_from_toml(conn, toml_path)
        conn.commit()
        rows = list_feeds(conn)
        assert len(rows) == 2
    finally:
        conn.close()


def test_bootstrap_returns_count(tmp_path):
    conn = _make_db(tmp_path)
    toml_path = _write_toml(tmp_path, [
        ("Feed A", "https://example.com/a.rss"),
        ("Feed B", "https://example.com/b.rss"),
    ])
    try:
        count = bootstrap_feeds_from_toml(conn, toml_path)
        assert count == 2
    finally:
        conn.close()


def test_bootstrap_preserves_existing_state(tmp_path):
    conn = _make_db(tmp_path)
    url = "https://example.com/a.rss"
    # 미리 enabled=0, name="legacy" 로 삽입
    conn.execute(
        "INSERT INTO feeds (name, url, enabled) VALUES (?, ?, 0)",
        ("legacy", url),
    )
    conn.commit()

    toml_path = _write_toml(tmp_path, [("Feed A", url)])
    try:
        bootstrap_feeds_from_toml(conn, toml_path)
        conn.commit()
        rows = list_feeds(conn)
        assert len(rows) == 1
        row = rows[0]
        assert row["enabled"] == 0
        assert row["name"] == "legacy"
    finally:
        conn.close()
