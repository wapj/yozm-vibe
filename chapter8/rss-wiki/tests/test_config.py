"""PRD §14 운영 상수가 config 모듈에 정확히 반영되어 있는지 검증."""

from __future__ import annotations

from pathlib import Path

from rss_wiki import config


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_paths_anchored_to_project_root() -> None:
    assert config.PROJECT_ROOT == PROJECT_ROOT
    assert config.DATA_DIR == PROJECT_ROOT / "data"
    assert config.LOGS_DIR == PROJECT_ROOT / "data" / "logs"
    assert config.DB_PATH == PROJECT_ROOT / "data" / "rss-wiki.db"
    assert config.LOG_PATH == PROJECT_ROOT / "data" / "logs" / "rss-wiki.log"


def test_scheduler_cron_every_hour_on_the_hour() -> None:
    assert config.SCHEDULER_CRON_HOUR == "*"
    assert config.SCHEDULER_CRON_MINUTE == 0


def test_fetch_and_extractor_timeouts() -> None:
    assert config.FEED_FETCH_CONCURRENCY == 5
    assert config.FEED_FETCH_TIMEOUT_SECONDS == 30
    assert config.EXTRACTOR_TIMEOUT_SECONDS == 20


def test_llm_subprocess_and_backoff() -> None:
    assert config.LLM_SUBPROCESS_TIMEOUT_SECONDS == 120
    assert config.LLM_MAX_ATTEMPTS == 3
    assert config.LLM_BACKOFF_SECONDS == (2, 4, 8)


def test_wiki_rebuild_budgets() -> None:
    assert config.WIKI_REBUILD_INPUT_CHAR_LIMIT == 100_000
    assert config.WIKI_INITIAL_BUILD_RECENT_ARTICLES == 20
    assert config.WIKI_INCREMENTAL_EXISTING_CONTEXT == 10
    assert config.WIKI_EXISTING_CONTEXT_FALLBACKS == (10, 5, 3, 0)


def test_category_tree_depth_is_two() -> None:
    assert config.CATEGORY_MAX_DEPTH == 2


def test_local_binding() -> None:
    assert config.HOST == "127.0.0.1"
    assert config.PORT == 8000


def test_llm_output_language_is_korean() -> None:
    assert config.LLM_OUTPUT_LANGUAGE == "ko"


def test_job_log_list_limit() -> None:
    assert config.JOB_LOG_LIST_LIMIT == 200
