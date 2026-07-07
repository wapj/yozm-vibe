import asyncio
import shutil
from datetime import datetime, timezone

import typer
import uvicorn

from rss_wiki import feeds as feeds_logic
from rss_wiki import pipeline
from rss_wiki import store
from rss_wiki import wiki
from rss_wiki.web.app import create_app

app = typer.Typer(
    name="rss-wiki",
    help="RSS 피드를 LLM으로 요약해 마크다운 위키로 정리하는 CLI 도구",
    no_args_is_help=True,
)


def _load_feeds_or_exit() -> list[dict]:
    try:
        return store.load_feeds()
    except store.StoreError as e:
        typer.echo(f"오류: {e}", err=True)
        raise typer.Exit(code=1)


def _load_state_or_exit() -> dict:
    try:
        return store.load_state()
    except store.StoreError as e:
        typer.echo(f"오류: {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def add(url: str) -> None:
    """피드를 등록합니다."""
    current = _load_feeds_or_exit()

    try:
        updated = feeds_logic.add_feed(current, url)
    except (feeds_logic.DuplicateFeedError, feeds_logic.FeedValidationError) as e:
        typer.echo(f"오류: {e}", err=True)
        raise typer.Exit(code=1)

    store.save_feeds(updated)
    added = updated[-1]
    typer.echo(f"등록됨: {added['name']} ({added['url']})")


@app.command()
def remove(target: str) -> None:
    """URL 또는 이름으로 피드를 삭제합니다."""
    current = _load_feeds_or_exit()

    try:
        updated = feeds_logic.remove_feed(current, target)
    except feeds_logic.FeedNotFoundError as e:
        typer.echo(f"오류: {e}", err=True)
        raise typer.Exit(code=1)

    store.save_feeds(updated)
    typer.echo(f"삭제됨: {target}")


@app.command(name="list")
def list_feeds() -> None:
    """등록된 피드 목록을 출력합니다."""
    current = _load_feeds_or_exit()
    items = feeds_logic.list_feeds(current)

    if not items:
        typer.echo("등록된 피드가 없습니다.")
        return

    for feed in items:
        typer.echo(f"- {feed['name']}  {feed['url']}  (등록: {feed['added_at']})")


def _claude_available() -> bool:
    return shutil.which("claude") is not None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _echo_report(report: dict) -> None:
    feeds_report = report["feeds"]
    articles_report = report["articles"]
    typer.echo(
        f"피드: 성공 {feeds_report['succeeded']}건 / 실패 {feeds_report['failed']}건"
    )
    for failure in feeds_report["failures"]:
        typer.echo(f"  - 피드 실패: {failure['feed']} ({failure['reason']})")
    typer.echo(
        f"글: 성공 {articles_report['succeeded']}건 / 실패 {articles_report['failed']}건"
    )
    for failure in articles_report["failures"]:
        typer.echo(f"  - 글 실패: {failure['feed']} / {failure['article_id']} ({failure['reason']})")


@app.command()
def fetch(
    limit: int = typer.Option(10, "--limit", help="최초 수집 시 가져올 글 개수"),
    concurrency: int = typer.Option(4, "--concurrency", help="글 요약 동시 실행 개수"),
) -> None:
    """전체 피드에서 새 글을 수집하고 위키를 갱신합니다."""
    if not _claude_available():
        typer.echo(
            "오류: claude CLI를 찾을 수 없습니다. Claude Code CLI를 설치한 뒤 다시 시도하세요.",
            err=True,
        )
        raise typer.Exit(code=1)

    current_feeds = _load_feeds_or_exit()
    state = _load_state_or_exit()

    now = _now_iso()
    collected_date = now[:10]

    result = asyncio.run(
        pipeline.run_fetch_async(
            current_feeds,
            state,
            limit=limit,
            now=now,
            collected_date=collected_date,
            concurrency=concurrency,
        )
    )

    new_state = result["state"]
    all_meta = [
        record["meta"] for record in new_state.get("processed", {}).values() if "meta" in record
    ]
    wiki.write_wiki(result["batch"], all_meta=all_meta)
    store.save_state(new_state)

    _echo_report(result["report"])

    articles_succeeded = result["report"]["articles"]["succeeded"]
    total_failed = result["report"]["feeds"]["failed"] + result["report"]["articles"]["failed"]
    if total_failed > 0 and articles_succeeded == 0:
        raise typer.Exit(code=1)


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", "--host", help="바인딩할 호스트(로컬 전용)"),
    port: int = typer.Option(8000, "--port", help="바인딩할 포트"),
) -> None:
    """로컬 웹 UI 서버를 실행합니다."""
    uvicorn.run(create_app(), host=host, port=port)
