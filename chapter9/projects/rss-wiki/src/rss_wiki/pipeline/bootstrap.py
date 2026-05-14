from __future__ import annotations

import sqlite3
from pathlib import Path

from rss_wiki.config import load_feeds
from rss_wiki.storage.repo import upsert_feed


def bootstrap_feeds_from_toml(conn: sqlite3.Connection, path: str | Path) -> int:
    """feeds.toml의 모든 피드를 upsert. 반환: 처리된 피드 수."""
    feeds = load_feeds(path)
    for cfg in feeds:
        upsert_feed(conn, cfg.name, cfg.url)
    return len(feeds)
