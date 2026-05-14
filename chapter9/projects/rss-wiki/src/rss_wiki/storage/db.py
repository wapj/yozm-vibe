import sqlite3
from pathlib import Path


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    db_path = Path(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def _migrate_feeds_table(conn: sqlite3.Connection) -> None:
    existing_cols = {
        row["name"]: row for row in conn.execute("PRAGMA table_info(feeds)").fetchall()
    }
    required_cols = {"enabled", "last_fetched_at", "updated_at"}
    if required_cols.issubset(existing_cols):
        return

    enabled_expr = "enabled" if "enabled" in existing_cols else "1"
    last_fetched_expr = (
        "last_fetched_at" if "last_fetched_at" in existing_cols else "NULL"
    )
    updated_expr = "updated_at" if "updated_at" in existing_cols else "datetime('now')"

    foreign_keys_enabled = conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    conn.execute("PRAGMA foreign_keys = OFF")
    try:
        conn.execute("""
            CREATE TABLE feeds_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL UNIQUE,
                consecutive_failures INTEGER NOT NULL DEFAULT 0,
                last_success_at TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                enabled INTEGER NOT NULL DEFAULT 1,
                last_fetched_at TEXT,
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute(
            f"""
            INSERT INTO feeds_new (
                id, name, url, consecutive_failures, last_success_at, created_at,
                enabled, last_fetched_at, updated_at
            )
            SELECT
                id, name, url, consecutive_failures, last_success_at, created_at,
                {enabled_expr}, {last_fetched_expr}, {updated_expr}
            FROM feeds
            """
        )
        conn.execute("DROP TABLE feeds")
        conn.execute("ALTER TABLE feeds_new RENAME TO feeds")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if foreign_keys_enabled:
            conn.execute("PRAGMA foreign_keys = ON")


def init_db(db_path: str | Path) -> None:
    db_path = Path(db_path)
    if not db_path.parent.exists():
        raise FileNotFoundError(
            f"Parent directory does not exist: {db_path.parent}"
        )
    schema_path = Path(__file__).parent / "schema.sql"
    try:
        schema_sql = schema_path.read_text(encoding="utf-8")
    except OSError as e:
        raise FileNotFoundError(f"Cannot read schema file {schema_path}: {e}") from e
    conn = get_connection(db_path)
    try:
        conn.executescript(schema_sql)
        _migrate_feeds_table(conn)

        # articles migration: step 1 — recreate if feed_id is NOT NULL
        articles_info = conn.execute("PRAGMA table_info(articles)").fetchall()
        feed_id_col = next((row for row in articles_info if row["name"] == "feed_id"), None)
        if feed_id_col and feed_id_col["notnull"] == 1:
            conn.execute("PRAGMA foreign_keys = OFF")
            conn.executescript("""
                CREATE TABLE articles_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feed_id INTEGER REFERENCES feeds(id),
                    url TEXT NOT NULL,
                    url_hash TEXT NOT NULL UNIQUE,
                    title TEXT,
                    title_hash TEXT,
                    published_at TEXT,
                    content TEXT,
                    summary TEXT,
                    feed_url_snapshot TEXT,
                    feed_name_snapshot TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                INSERT INTO articles_new (id, feed_id, url, url_hash, title, title_hash, published_at, content, summary, created_at)
                    SELECT id, feed_id, url, url_hash, title, title_hash, published_at, content, summary, created_at FROM articles;
                DROP TABLE articles;
                ALTER TABLE articles_new RENAME TO articles;
                CREATE INDEX IF NOT EXISTS idx_articles_url_hash ON articles(url_hash);
                CREATE INDEX IF NOT EXISTS idx_articles_title_hash ON articles(title_hash);
            """)
            conn.execute("PRAGMA foreign_keys = ON")

        # articles migration: step 2 — add snapshot columns if missing (idempotent)
        articles_cols = {row["name"] for row in conn.execute("PRAGMA table_info(articles)").fetchall()}
        for col_name, col_def in [
            ("feed_url_snapshot", "TEXT"),
            ("feed_name_snapshot", "TEXT"),
        ]:
            if col_name not in articles_cols:
                conn.execute(f"ALTER TABLE articles ADD COLUMN {col_name} {col_def}")

        conn.commit()
    finally:
        conn.close()
