"""FastAPI 앱 팩토리 + 글 열람·피드 관리·수집 실행 라우트 배선(T22·T24·T27·T28).

목록(`GET /`)·피드별(`GET /feeds/{slug}`)·날짜별(`GET /daily/{date}`)·개별 글
(`GET /articles/{filename}`) 라우트가 `state.json` 표시 메타와 `wiki/articles/`
마크다운을 T21 순수 함수(`web.render`)에 주입해 Jinja2 템플릿으로 렌더한다.
`GET /feeds-admin`·`POST /feeds-admin/add`·`POST /feeds-admin/remove`는
`feeds.py`의 검증·CRUD 로직과 `store.py`의 `feeds.json` 읽기/쓰기를 재사용해
CLI와 동일한 진실 소스를 공유한다(T24). `GET /fetch`는 트리거 버튼·진행 상황
영역을 담은 화면을 렌더하고(T28), `POST /fetch`·`GET /fetch/progress`는
CLI `fetch`(T13·T18)와 동일한 `pipeline.run_fetch_async` 경로를 백그라운드
태스크로 구동하고, `web/progress.py`의 `ProgressTracker`로 진행 상황·중복 실행
차단을 관리한다(T27). 백그라운드 태스크는 `background_tasks` 집합에 참조를
보관하고 완료 시 `add_done_callback`으로 제거해 실행 중 GC되지 않게 한다
(REVIEW T27 메모 1). `state_path`/`wiki_dir`/`feeds_path`는 `store.py`의 주입
패턴과 동일하게 기본값을 `config.py`에서 가져오되 테스트가 격리된 임시 경로를
주입할 수 있게 한다.
"""

from __future__ import annotations

import asyncio
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from rss_wiki import config, pipeline, store, wiki
from rss_wiki import feeds as feeds_logic
from rss_wiki.web import progress, render

WEB_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"


def _claude_available() -> bool:
    return shutil.which("claude") is not None


def _load_display_metas(state_path: Path) -> list[dict]:
    state = store.load_state(state_path)
    return [entry["meta"] for entry in state.get("processed", {}).values() if entry.get("meta")]


async def _form_value(request: Request, key: str) -> str:
    """`application/x-www-form-urlencoded` 본문에서 필드값을 읽는다.

    `python-multipart` 의존성 없이 단일 필드 폼을 처리하기 위해 원시 본문을
    직접 파싱한다(자체 결정: 되돌리기 쉬움).
    """
    body = (await request.body()).decode("utf-8")
    return parse_qs(body).get(key, [""])[0].strip()


def create_app(
    *,
    state_path: Path = config.STATE_PATH,
    wiki_dir: Path = config.WIKI_DIR,
    feeds_path: Path = config.FEEDS_PATH,
    validate=feeds_logic._default_validate,
    run_fetch_async=pipeline.run_fetch_async,
    claude_available=_claude_available,
    fetch_limit: int = 10,
    fetch_concurrency: int = 4,
) -> FastAPI:
    app = FastAPI(title="rss-wiki")
    templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    articles_dir = wiki_dir / "articles"
    tracker = progress.ProgressTracker()
    background_tasks: set[asyncio.Task] = set()

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request) -> HTMLResponse:
        viewmodel = render.build_list_viewmodel(_load_display_metas(state_path))
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "title": "rss-wiki",
                "articles": viewmodel["latest"],
                "by_feed": viewmodel["by_feed"],
                "by_date": viewmodel["by_date"],
            },
        )

    @app.get("/feeds/{slug}", response_class=HTMLResponse)
    def feed_detail(request: Request, slug: str) -> HTMLResponse:
        viewmodel = render.build_list_viewmodel(_load_display_metas(state_path))
        group = next((g for g in viewmodel["by_feed"] if g["slug"] == slug), None)
        feed_name = group["feed_name"] if group else slug
        articles = group["articles"] if group else []
        return templates.TemplateResponse(
            request,
            "feed.html",
            {"title": f"{feed_name} - rss-wiki", "feed_name": feed_name, "articles": articles},
        )

    @app.get("/daily/{date}", response_class=HTMLResponse)
    def daily_detail(request: Request, date: str) -> HTMLResponse:
        viewmodel = render.build_list_viewmodel(_load_display_metas(state_path))
        group = next((g for g in viewmodel["by_date"] if g["date"] == date), None)
        articles = group["articles"] if group else []
        return templates.TemplateResponse(
            request,
            "daily.html",
            {"title": f"{date} - rss-wiki", "date": date, "articles": articles},
        )

    @app.get("/articles/{filename}", response_class=HTMLResponse)
    def article_detail(request: Request, filename: str) -> HTMLResponse:
        article_path = articles_dir / filename
        resolved = article_path.resolve()
        is_within_articles_dir = resolved.is_relative_to(articles_dir.resolve())
        if not is_within_articles_dir or not resolved.is_file():
            return templates.TemplateResponse(
                request,
                "404.html",
                {"title": "글을 찾을 수 없습니다 - rss-wiki"},
                status_code=404,
            )

        meta = next(
            (m for m in _load_display_metas(state_path) if m.get("filename") == filename),
            {},
        )
        article_html = render.render_article_html(resolved.read_text(encoding="utf-8"))
        return templates.TemplateResponse(
            request,
            "article.html",
            {
                "title": f"{meta.get('title', filename)} - rss-wiki",
                "article_html": article_html,
                "meta": meta,
            },
        )

    def _render_feeds_admin(request: Request, *, error: str | None = None, status_code: int = 200) -> HTMLResponse:
        current = store.load_feeds(feeds_path)
        return templates.TemplateResponse(
            request,
            "feeds_admin.html",
            {"title": "피드 관리 - rss-wiki", "feeds": current, "error": error},
            status_code=status_code,
        )

    @app.get("/feeds-admin", response_class=HTMLResponse)
    def feeds_admin(request: Request) -> HTMLResponse:
        return _render_feeds_admin(request)

    @app.post("/feeds-admin/add", response_class=HTMLResponse)
    async def feeds_admin_add(request: Request):
        url = await _form_value(request, "url")
        current = store.load_feeds(feeds_path)
        try:
            updated = feeds_logic.add_feed(current, url, validate=validate)
        except (feeds_logic.DuplicateFeedError, feeds_logic.FeedValidationError) as e:
            return _render_feeds_admin(request, error=str(e), status_code=400)
        store.save_feeds(updated, feeds_path)
        return RedirectResponse("/feeds-admin", status_code=303)

    @app.post("/feeds-admin/remove", response_class=HTMLResponse)
    async def feeds_admin_remove(request: Request):
        target = await _form_value(request, "target")
        current = store.load_feeds(feeds_path)
        try:
            updated = feeds_logic.remove_feed(current, target)
        except feeds_logic.FeedNotFoundError as e:
            return _render_feeds_admin(request, error=str(e), status_code=400)
        store.save_feeds(updated, feeds_path)
        return RedirectResponse("/feeds-admin", status_code=303)

    async def _run_fetch_in_background() -> None:
        """트리거가 백그라운드 태스크로 구동하는 실제 수집 실행.

        CLI `fetch`(T13·T18)와 동일한 순서(프리플라이트 → `run_fetch_async` →
        누적 인덱스 쓰기 → state 저장 → 리포트)를 따르되, stdout 출력·종료 코드
        대신 트래커 `finish`/`fail`로 결과를 알린다.
        """
        if not claude_available():
            await tracker.fail(
                "claude CLI를 찾을 수 없습니다. Claude Code CLI를 설치한 뒤 다시 시도하세요."
            )
            return

        try:
            current_feeds = store.load_feeds(feeds_path)
            state = store.load_state(state_path)
            now = datetime.now(timezone.utc).isoformat()
            collected_date = now[:10]

            async def _on_progress(event: dict) -> None:
                await tracker.handle_event(event)

            result = await run_fetch_async(
                current_feeds,
                state,
                limit=fetch_limit,
                now=now,
                collected_date=collected_date,
                concurrency=fetch_concurrency,
                on_progress=_on_progress,
            )

            new_state = result["state"]
            all_meta = [
                record["meta"]
                for record in new_state.get("processed", {}).values()
                if "meta" in record
            ]
            wiki.write_wiki(result["batch"], wiki_dir=wiki_dir, all_meta=all_meta)
            store.save_state(new_state, state_path)
            await tracker.finish(result["report"])
        except Exception as exc:  # noqa: BLE001 - 백그라운드 태스크 결과를 트래커로만 전달
            await tracker.fail(str(exc))

    @app.get("/fetch", response_class=HTMLResponse)
    def fetch_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request,
            "fetch.html",
            {"title": "수집 실행 - rss-wiki"},
        )

    @app.post("/fetch")
    async def trigger_fetch():
        try:
            await tracker.begin()
        except progress.AlreadyRunningError as e:
            raise HTTPException(status_code=409, detail=str(e))

        task = asyncio.create_task(_run_fetch_in_background())
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)
        return await tracker.snapshot()

    @app.get("/fetch/progress")
    async def fetch_progress():
        return await tracker.snapshot()

    return app
