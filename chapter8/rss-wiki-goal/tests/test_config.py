"""config.py 상수 테스트."""

from rss_wiki import config


def test_scheduler_constants():
    assert config.SCHEDULER_HOUR == "*"
    assert config.SCHEDULER_MINUTE == 0


def test_timeout_constants():
    assert config.FEED_FETCH_TIMEOUT_SECONDS == 30
    assert config.EXTRACTOR_TIMEOUT_SECONDS == 20
    assert config.LLM_SUBPROCESS_TIMEOUT_SECONDS == 120


def test_concurrency():
    assert config.FEED_FETCH_CONCURRENCY == 5


def test_backoff():
    assert config.LLM_BACKOFF_MAX_RETRIES == 3
    assert config.LLM_BACKOFF_DELAYS == (2, 4, 8)


def test_wiki_constants():
    assert config.WIKI_INPUT_MAX_CHARS == 100_000
    assert config.WIKI_INITIAL_BUILD_ARTICLE_COUNT == 20
    assert config.WIKI_INCREMENTAL_CONTEXT_COUNT == 10


def test_paths():
    assert "rss-wiki.db" in config.DB_PATH
    assert "rss-wiki.log" in config.LOG_FILE_PATH


def test_server():
    assert config.BIND_HOST == "127.0.0.1"
    assert config.BIND_PORT == 8000
