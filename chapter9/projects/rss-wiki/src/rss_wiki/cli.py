from __future__ import annotations

import argparse
import calendar
import logging
import sqlite3
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Callable

from rss_wiki.config import FeedConfig
from rss_wiki.llm.client import DEFAULT_TIMEOUT, call_claude
from rss_wiki.storage.db import get_connection, init_db
from rss_wiki.storage.repo import list_feeds, list_unanalyzed_article_ids
from rss_wiki.pipeline.bootstrap import bootstrap_feeds_from_toml
from rss_wiki.pipeline.ingest import run_daily_ingest
from rss_wiki.pipeline.llm import analyze_articles
from rss_wiki.pipeline.publish import publish_daily, publish_indexes, publish_weekly, publish_monthly


def _default_uvicorn_run() -> Callable[..., None]:
    try:
        import uvicorn
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "web command requires uvicorn. Install project dependencies with `pip install -e .` or `uv sync`."
        ) from exc
    return uvicorn.run


def _create_web_app(db_path: Path):
    try:
        from rss_wiki.web.app import create_app
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "web command requires FastAPI web dependencies. Install project dependencies with `pip install -e .` or `uv sync`."
        ) from exc
    return create_app(db_path)


def _positive_float(value: str) -> float:
    parsed = float(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than 0")
    return parsed


def _add_llm_timeout_arg(
    parser: argparse.ArgumentParser,
    *,
    default: float | str = argparse.SUPPRESS,
) -> None:
    parser.add_argument(
        "--llm-timeout",
        type=_positive_float,
        default=default,
        help=f"Claude CLI 호출 타임아웃(초, 기본={DEFAULT_TIMEOUT:g})",
    )


def is_friday(d: date) -> bool:
    return d.weekday() == 4


def is_last_friday_of_month(d: date) -> bool:
    if d.weekday() != 4:
        return False
    last_day = calendar.monthrange(d.year, d.month)[1]
    return d.day + 7 > last_day


def run_daily(
    *,
    conn: sqlite3.Connection,
    feeds: Sequence[FeedConfig],
    output_dir: Path,
    runner: Callable[[str], str] | None = None,
    now: date | None = None,
    logger: logging.Logger | None = None,
) -> int:
    _logger = logger or logging.getLogger(__name__)
    _now = now or date.today()
    _today_iso = _now.isoformat()

    stats = run_daily_ingest(conn=conn, feeds=feeds, logger=_logger)
    _logger.info("ingest stats: %s", stats)

    article_ids = list_unanalyzed_article_ids(conn)
    result = analyze_articles(conn=conn, article_ids=article_ids, runner=runner, logger=_logger)
    _logger.info("analyze stats: %s", result.stats)

    if result.analyzed_article_ids:
        publish_daily(conn=conn, result=result, output_dir=output_dir, date=_today_iso, logger=_logger)
    else:
        _logger.warning("daily publish skipped (no analyzed articles)")

    publish_indexes(conn=conn, output_dir=output_dir, logger=_logger)

    if is_friday(_now):
        publish_weekly(conn=conn, end_date=_today_iso, output_dir=output_dir, runner=runner, logger=_logger)

    if is_last_friday_of_month(_now):
        publish_monthly(conn=conn, end_date=_today_iso, output_dir=output_dir, runner=runner, logger=_logger)

    conn.commit()
    return 0


def run_weekly(
    *,
    conn: sqlite3.Connection,
    end_date: str,
    output_dir: Path,
    runner: Callable[[str], str] | None = None,
    logger: logging.Logger | None = None,
) -> int:
    _logger = logger or logging.getLogger(__name__)
    publish_weekly(conn=conn, end_date=end_date, output_dir=output_dir, runner=runner, logger=_logger)
    conn.commit()
    return 0


def run_monthly(
    *,
    conn: sqlite3.Connection,
    end_date: str,
    output_dir: Path,
    runner: Callable[[str], str] | None = None,
    logger: logging.Logger | None = None,
) -> int:
    _logger = logger or logging.getLogger(__name__)
    publish_monthly(conn=conn, end_date=end_date, output_dir=output_dir, runner=runner, logger=_logger)
    conn.commit()
    return 0


def run_web(
    *,
    db_path: Path,
    host: str,
    port: int,
    run_uvicorn: Callable[..., None] | None = None,
    create_web_app: Callable[[Path], object] | None = None,
    logger: logging.Logger | None = None,
) -> int:
    _logger = logger or logging.getLogger(__name__)
    _logger.info("starting web server on %s:%d (db=%s)", host, port, db_path)
    runner = run_uvicorn or _default_uvicorn_run()
    app_factory = create_web_app or _create_web_app
    runner(app_factory(db_path), host=host, port=port, log_level="info")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rss-wiki")
    parser.add_argument("--db", default="data/rss-wiki.db", help="SQLite 경로")
    parser.add_argument("--feeds", default="feeds.toml", help="피드 설정 파일")
    parser.add_argument("--output", default="output", help="마크다운 출력 디렉터리")
    _add_llm_timeout_arg(parser, default=DEFAULT_TIMEOUT)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_daily = sub.add_parser("daily", help="일간 파이프라인")
    _add_llm_timeout_arg(p_daily)
    p_weekly = sub.add_parser("weekly", help="주간 매거진(트리거 우회)")
    p_weekly.add_argument("--end-date", default=None, help="ISO 날짜(기본=오늘)")
    _add_llm_timeout_arg(p_weekly)
    p_monthly = sub.add_parser("monthly", help="월간 매거진(트리거 우회)")
    p_monthly.add_argument("--end-date", default=None, help="ISO 날짜(기본=오늘)")
    _add_llm_timeout_arg(p_monthly)
    p_web = sub.add_parser("web", help="로컬 웹 인터페이스 실행")
    p_web.add_argument("--host", default="127.0.0.1", help="바인딩 호스트")
    p_web.add_argument("--port", type=int, default=8765, help="바인딩 포트")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger = logging.getLogger("rss_wiki.cli")

    db_path = Path(args.db)
    if not db_path.parent.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        if args.cmd == "daily":
            bootstrap_feeds_from_toml(conn, args.feeds)
            rows = list_feeds(conn, enabled_only=True)
            feeds = [FeedConfig(name=r["name"], url=r["url"]) for r in rows]
            return run_daily(
                conn=conn,
                feeds=feeds,
                output_dir=Path(args.output),
                runner=lambda prompt: call_claude(prompt, timeout=args.llm_timeout),
                logger=logger,
            )
        elif args.cmd == "weekly":
            end_date = args.end_date or date.today().isoformat()
            return run_weekly(
                conn=conn,
                end_date=end_date,
                output_dir=Path(args.output),
                runner=lambda prompt: call_claude(prompt, timeout=args.llm_timeout),
                logger=logger,
            )
        elif args.cmd == "monthly":
            end_date = args.end_date or date.today().isoformat()
            return run_monthly(
                conn=conn,
                end_date=end_date,
                output_dir=Path(args.output),
                runner=lambda prompt: call_claude(prompt, timeout=args.llm_timeout),
                logger=logger,
            )
        elif args.cmd == "web":
            return run_web(db_path=db_path, host=args.host, port=args.port, logger=logger)
        return 2  # 도달 불가(argparse required=True)
    except (RuntimeError, ValueError) as exc:
        logger.error("command failed: %s", exc)
        return 1
    finally:
        conn.close()
