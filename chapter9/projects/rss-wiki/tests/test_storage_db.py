import sqlite3
import pytest
from rss_wiki.storage.db import get_connection, init_db


def test_init_db_creates_all_tables(tmp_path):
    db_file = tmp_path / "test.db"
    init_db(db_file)
    conn = get_connection(db_file)
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    conn.close()
    table_names = {row["name"] for row in rows}
    expected = {
        "feeds", "articles", "categories", "tags",
        "article_categories", "article_tags", "magazines", "magazine_articles",
    }
    assert expected.issubset(table_names)


def test_init_db_is_idempotent(tmp_path):
    db_file = tmp_path / "test.db"
    init_db(db_file)
    init_db(db_file)  # second call must not raise


def test_get_connection_foreign_keys_enabled(tmp_path):
    db_file = tmp_path / "test.db"
    init_db(db_file)
    conn = get_connection(db_file)
    row = conn.execute("PRAGMA foreign_keys").fetchone()
    conn.close()
    assert row[0] == 1


def test_magazines_kind_check_constraint(tmp_path):
    db_file = tmp_path / "test.db"
    init_db(db_file)
    conn = get_connection(db_file)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO magazines (kind, published_at, file_path) VALUES (?, ?, ?)",
            ("invalid", "2026-01-01", "/tmp/test.md"),
        )
        conn.commit()
    conn.close()
