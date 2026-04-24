"""SQLite 연결 팩토리와 스키마 생성 (PRD §6)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from . import config


_SCHEMA_FEEDS = """
CREATE TABLE IF NOT EXISTS feeds (
  id                   INTEGER PRIMARY KEY AUTOINCREMENT,
  url                  TEXT NOT NULL UNIQUE,
  title                TEXT,
  is_active            INTEGER NOT NULL DEFAULT 1,
  last_fetched_at      TEXT,
  consecutive_failures INTEGER NOT NULL DEFAULT 0,
  created_at           TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

_SCHEMA_CATEGORIES = """
CREATE TABLE IF NOT EXISTS categories (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  name            TEXT NOT NULL UNIQUE,
  parent_id       INTEGER REFERENCES categories(id) ON DELETE SET NULL,
  description     TEXT,
  is_user_edited  INTEGER NOT NULL DEFAULT 0,
  merged_into_id  INTEGER REFERENCES categories(id) ON DELETE SET NULL,
  created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_id);
"""

_SCHEMA_ARTICLES = """
CREATE TABLE IF NOT EXISTS articles (
  id                  INTEGER PRIMARY KEY AUTOINCREMENT,
  feed_id             INTEGER NOT NULL REFERENCES feeds(id) ON DELETE CASCADE,
  url                 TEXT NOT NULL UNIQUE,
  title               TEXT NOT NULL,
  author              TEXT,
  published_at        TEXT,
  raw_summary         TEXT,
  extracted_content   TEXT,
  llm_summary         TEXT,
  primary_category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
  language            TEXT,
  status              TEXT NOT NULL DEFAULT 'ok',
  fetched_at          TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_articles_feed ON articles(feed_id);
CREATE INDEX IF NOT EXISTS idx_articles_cat  ON articles(primary_category_id);
CREATE INDEX IF NOT EXISTS idx_articles_pub  ON articles(published_at DESC);
"""

_SCHEMA_WIKI_PAGES = """
CREATE TABLE IF NOT EXISTS wiki_pages (
  id                         INTEGER PRIMARY KEY AUTOINCREMENT,
  category_id                INTEGER NOT NULL UNIQUE REFERENCES categories(id) ON DELETE CASCADE,
  content_markdown           TEXT NOT NULL DEFAULT '',
  last_rebuilt_at            TEXT,
  articles_count_at_rebuild  INTEGER NOT NULL DEFAULT 0,
  last_seen_at               TEXT,
  has_unread_updates         INTEGER NOT NULL DEFAULT 0
);
"""

_SCHEMA_JOB_LOGS = """
CREATE TABLE IF NOT EXISTS job_logs (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  job_type       TEXT NOT NULL,
  target_ref     TEXT,
  status         TEXT NOT NULL,
  error_message  TEXT,
  attempt_count  INTEGER NOT NULL DEFAULT 1,
  started_at     TEXT NOT NULL,
  finished_at    TEXT
);
CREATE INDEX IF NOT EXISTS idx_joblogs_started ON job_logs(started_at DESC);
"""

_SCHEMA_ARTICLES_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
  title, llm_summary, extracted_content,
  content='articles', content_rowid='id',
  tokenize='unicode61'
);

CREATE TRIGGER IF NOT EXISTS articles_ai AFTER INSERT ON articles BEGIN
  INSERT INTO articles_fts(rowid, title, llm_summary, extracted_content)
  VALUES (new.id, new.title, new.llm_summary, new.extracted_content);
END;
CREATE TRIGGER IF NOT EXISTS articles_ad AFTER DELETE ON articles BEGIN
  INSERT INTO articles_fts(articles_fts, rowid, title, llm_summary, extracted_content)
  VALUES ('delete', old.id, old.title, old.llm_summary, old.extracted_content);
END;
CREATE TRIGGER IF NOT EXISTS articles_au AFTER UPDATE ON articles BEGIN
  INSERT INTO articles_fts(articles_fts, rowid, title, llm_summary, extracted_content)
  VALUES ('delete', old.id, old.title, old.llm_summary, old.extracted_content);
  INSERT INTO articles_fts(rowid, title, llm_summary, extracted_content)
  VALUES (new.id, new.title, new.llm_summary, new.extracted_content);
END;
"""


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """SQLite 연결을 생성한다.

    - 부모 디렉토리가 없으면 만든다.
    - `row_factory=sqlite3.Row` 로 컬럼명 접근을 허용한다.
    - 외래키 제약을 활성화한다.
    """
    path = db_path if db_path is not None else config.DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """현재까지 정의된 모든 테이블/인덱스를 생성한다 (idempotent)."""
    conn.executescript(
        _SCHEMA_FEEDS
        + _SCHEMA_CATEGORIES
        + _SCHEMA_ARTICLES
        + _SCHEMA_WIKI_PAGES
        + _SCHEMA_JOB_LOGS
        + _SCHEMA_ARTICLES_FTS
    )
    conn.commit()
