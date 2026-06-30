"""FastAPI 라우터 — PRD §9 전체 엔드포인트."""

import asyncio
import logging
import sqlite3
from pathlib import Path
from typing import Annotated

import markdown as md
from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from markupsafe import Markup

logger = logging.getLogger(__name__)

router = APIRouter()

_TEMPLATE_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))


def _markdown_filter(text: str) -> Markup:
    if not text:
        return Markup("")
    return Markup(md.markdown(text, extensions=["nl2br", "fenced_code", "tables"]))


templates.env.filters["markdown"] = _markdown_filter


def get_db(request: Request) -> sqlite3.Connection:
    return request.app.state.db


DB = Annotated[sqlite3.Connection, Depends(get_db)]


# ── 카테고리 목록 (홈) ────────────────────────────────────────────────────────

@router.get("/", response_class=HTMLResponse)
async def index(request: Request, db: DB):
    rows = db.execute(
        """SELECT c.id, c.name, c.parent_id, wp.has_unread_updates
           FROM categories c
           LEFT JOIN wiki_pages wp ON wp.category_id=c.id
           WHERE c.parent_id IS NULL AND c.merged_into_id IS NULL
           ORDER BY wp.has_unread_updates DESC, c.name"""
    ).fetchall()
    return templates.TemplateResponse(request, "index.html", {"categories": rows})


# ── 카테고리 관리 (정적 경로 — {cat_id} 이전에 등록) ──────────────────────────

@router.get("/categories/manage", response_class=HTMLResponse)
async def category_manage(request: Request, db: DB):
    categories = db.execute(
        "SELECT c.*, p.name as parent_name FROM categories c LEFT JOIN categories p ON c.parent_id=p.id ORDER BY c.name"
    ).fetchall()
    return templates.TemplateResponse(request, "category_manage.html", {"categories": categories})


# ── 카테고리 위키 페이지 ──────────────────────────────────────────────────────

@router.get("/categories/{cat_id}", response_class=HTMLResponse)
async def category_detail(request: Request, cat_id: int, db: DB):
    cat = db.execute("SELECT * FROM categories WHERE id=?", (cat_id,)).fetchone()
    if cat is None:
        raise HTTPException(404, "Category not found")

    wp = db.execute("SELECT * FROM wiki_pages WHERE category_id=?", (cat_id,)).fetchone()
    articles = db.execute(
        "SELECT title, url, published_at, llm_summary FROM articles WHERE primary_category_id=? ORDER BY published_at DESC",
        (cat_id,),
    ).fetchall()

    db.execute(
        "UPDATE wiki_pages SET has_unread_updates=0, last_seen_at=datetime('now') WHERE category_id=?",
        (cat_id,),
    )
    db.commit()

    children = db.execute(
        "SELECT id, name FROM categories WHERE parent_id=? AND merged_into_id IS NULL",
        (cat_id,),
    ).fetchall()

    return templates.TemplateResponse(
        request,
        "category_detail.html",
        {"category": cat, "wiki_page": wp, "articles": articles, "children": children},
    )


@router.post("/categories/{cat_id}/rename")
async def category_rename(cat_id: int, name: Annotated[str, Form()], db: DB):
    if not name.strip():
        raise HTTPException(400, "Name required")
    db.execute("UPDATE categories SET name=?, is_user_edited=1 WHERE id=?", (name.strip(), cat_id))
    db.commit()
    return RedirectResponse("/categories/manage", status_code=303)


@router.post("/categories/{cat_id}/merge")
async def category_merge(request: Request, cat_id: int, db: DB):
    form = await request.form()
    target_id = int(form.get("target_id", 0))
    if not target_id or target_id == cat_id:
        raise HTTPException(400, "Invalid target_id")

    # 글 이동
    db.execute("UPDATE articles SET primary_category_id=? WHERE primary_category_id=?", (target_id, cat_id))
    # 소스 카테고리 병합 표시
    db.execute("UPDATE categories SET merged_into_id=? WHERE id=?", (target_id, cat_id))
    # 소스 위키 삭제
    db.execute("DELETE FROM wiki_pages WHERE category_id=?", (cat_id,))
    db.commit()

    # 타겟 위키 재구성 (비동기 백그라운드)
    from rss_wiki.pipeline.rebuilder import rebuild_wiki
    asyncio.create_task(rebuild_wiki(db, target_id, []))

    return RedirectResponse("/categories/manage", status_code=303)


@router.post("/categories/{cat_id}/parent")
async def category_set_parent(request: Request, cat_id: int, db: DB):
    form = await request.form()
    parent_id_raw = form.get("parent_id", "")
    parent_id = int(parent_id_raw) if parent_id_raw else None
    db.execute("UPDATE categories SET parent_id=? WHERE id=?", (parent_id, cat_id))
    db.commit()
    return RedirectResponse("/categories/manage", status_code=303)


# ── 피드 관리 ─────────────────────────────────────────────────────────────────

@router.get("/feeds", response_class=HTMLResponse)
async def feeds_list(request: Request, db: DB):
    feeds = db.execute("SELECT * FROM feeds ORDER BY created_at DESC").fetchall()
    return templates.TemplateResponse(request, "feeds.html", {"feeds": feeds})


@router.post("/feeds/add")
async def feeds_add(url: Annotated[str, Form()], db: DB):
    url = url.strip()
    if not url:
        raise HTTPException(400, "URL required")
    try:
        db.execute("INSERT INTO feeds(url) VALUES (?)", (url,))
        db.commit()
    except Exception:
        raise HTTPException(409, "Feed already exists")
    return RedirectResponse("/feeds", status_code=303)


@router.post("/feeds/{feed_id}/toggle")
async def feeds_toggle(feed_id: int, db: DB):
    db.execute("UPDATE feeds SET is_active = 1 - is_active WHERE id=?", (feed_id,))
    db.commit()
    return RedirectResponse("/feeds", status_code=303)


@router.post("/feeds/{feed_id}/delete")
async def feeds_delete(feed_id: int, db: DB):
    db.execute("DELETE FROM feeds WHERE id=?", (feed_id,))
    db.commit()
    return RedirectResponse("/feeds", status_code=303)


# ── 검색 ──────────────────────────────────────────────────────────────────────

@router.get("/search", response_class=HTMLResponse)
async def search(request: Request, q: str = "", db: DB = None):
    results = []
    if q.strip():
        rows = db.execute(
            """SELECT a.id, a.title, a.url, a.published_at, a.llm_summary
               FROM articles_fts f
               JOIN articles a ON a.id=f.rowid
               WHERE articles_fts MATCH ?
               ORDER BY rank LIMIT 50""",
            (q,),
        ).fetchall()
        results = list(rows)
    return templates.TemplateResponse(request, "search.html", {"q": q, "results": results})


# ── 로그 ──────────────────────────────────────────────────────────────────────

@router.get("/logs", response_class=HTMLResponse)
async def logs(request: Request, db: DB):
    rows = db.execute(
        "SELECT * FROM job_logs ORDER BY started_at DESC LIMIT 200"
    ).fetchall()
    return templates.TemplateResponse(request, "logs.html", {"logs": rows})


# ── API ───────────────────────────────────────────────────────────────────────

@router.post("/api/fetch")
async def api_fetch(request: Request, background_tasks: BackgroundTasks, db: DB):
    """수동 수집 트리거.

    수집은 백그라운드에서 실행되며 즉시 /logs로 리다이렉트한다.
    브라우저를 닫아도 서버 내부에서 계속 실행된다.
    이미 실행 중이면 409를 반환한다.
    """
    from rss_wiki.scheduler import _fetch_lock, run_fetch_cycle

    if _fetch_lock.locked():
        raise HTTPException(409, "Fetch already running")

    async def _bg():
        try:
            await run_fetch_cycle(db)
        except Exception as exc:
            logger.error("Background fetch error: %s", exc)

    background_tasks.add_task(_bg)
    return RedirectResponse("/logs", status_code=303)
