"""운영 상수 (PRD §14)."""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent

DATA_DIR: Path = PROJECT_ROOT / "data"
LOGS_DIR: Path = DATA_DIR / "logs"
DB_PATH: Path = DATA_DIR / "rss-wiki.db"
LOG_PATH: Path = LOGS_DIR / "rss-wiki.log"

PACKAGE_DIR: Path = Path(__file__).resolve().parent
PROMPTS_DIR: Path = PACKAGE_DIR / "prompts"
TEMPLATES_DIR: Path = PACKAGE_DIR / "web" / "templates"

SCHEDULER_CRON_HOUR: str = "*"
SCHEDULER_CRON_MINUTE: int = 0

FEED_FETCH_CONCURRENCY: int = 5
FEED_FETCH_TIMEOUT_SECONDS: int = 30
EXTRACTOR_TIMEOUT_SECONDS: int = 20
LLM_SUBPROCESS_TIMEOUT_SECONDS: int = 120

LLM_MAX_ATTEMPTS: int = 3
LLM_BACKOFF_SECONDS: tuple[int, ...] = (2, 4, 8)

WIKI_REBUILD_INPUT_CHAR_LIMIT: int = 100_000
WIKI_INITIAL_BUILD_RECENT_ARTICLES: int = 20
WIKI_INCREMENTAL_EXISTING_CONTEXT: int = 10
WIKI_EXISTING_CONTEXT_FALLBACKS: tuple[int, ...] = (10, 5, 3, 0)

CATEGORY_MAX_DEPTH: int = 2

HOST: str = "127.0.0.1"
PORT: int = 8000

LLM_OUTPUT_LANGUAGE: str = "ko"
JOB_LOG_LIST_LIMIT: int = 200
