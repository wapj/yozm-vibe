"""SQLite 연결 및 스키마 초기화."""

import sqlite3
from pathlib import Path

from rss_wiki.config import DB_PATH

_DDL = """
CREATE TABLE IF NOT EXISTS feeds (
  id                   INTEGER PRIMARY KEY AUTOINCREMENT,
  url                  TEXT NOT NULL UNIQUE,
  title                TEXT,
  is_active            INTEGER NOT NULL DEFAULT 1,
  last_fetched_at      TEXT,
  consecutive_failures INTEGER NOT NULL DEFAULT 0,
  created_at           TEXT NOT NULL DEFAULT (datetime('now'))
);

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
CREATE INDEX IF NOT EXISTS idx_articles_feed    ON articles(feed_id);
CREATE INDEX IF NOT EXISTS idx_articles_cat     ON articles(primary_category_id);
CREATE INDEX IF NOT EXISTS idx_articles_pub     ON articles(published_at DESC);

CREATE TABLE IF NOT EXISTS wiki_pages (
  id                         INTEGER PRIMARY KEY AUTOINCREMENT,
  category_id                INTEGER NOT NULL UNIQUE REFERENCES categories(id) ON DELETE CASCADE,
  content_markdown           TEXT NOT NULL DEFAULT '',
  last_rebuilt_at            TEXT,
  articles_count_at_rebuild  INTEGER NOT NULL DEFAULT 0,
  last_seen_at               TEXT,
  has_unread_updates         INTEGER NOT NULL DEFAULT 0
);

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


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: str = DB_PATH) -> sqlite3.Connection:
    conn = get_connection(db_path)
    conn.executescript(_DDL)
    conn.commit()
    return conn
