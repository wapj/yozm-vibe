from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from rss_wiki.ingest.dedupe import normalize_url
from rss_wiki.storage import repo
from rss_wiki.web.app import get_db

router = APIRouter()


@router.get("/feeds", response_class=HTMLResponse)
def feeds_index(
    request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> HTMLResponse:
    feeds = repo.list_feeds(conn)
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request, "feeds.html", {"feeds": feeds, "active_nav": "feeds"}
    )


@router.get("/feeds/new", response_class=HTMLResponse)
def feed_new_form(request: Request) -> HTMLResponse:
    templates = request.app.state.templates
    return templates.TemplateResponse(request, "feed_new.html", {"active_nav": "feeds"})


@router.get("/feeds/{feed_id}/edit", response_class=HTMLResponse)
def feed_edit_form(
    feed_id: int,
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
) -> HTMLResponse:
    feed = repo.get_feed_by_id(conn, feed_id)
    if feed is None:
        raise HTTPException(status_code=404, detail="feed not found")
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request, "feed_edit.html", {"feed": feed, "active_nav": "feeds"}
    )


@router.post("/feeds")
def feeds_create(
    url: str = Form(...),
    name: str = Form(""),
    conn: sqlite3.Connection = Depends(get_db),
) -> RedirectResponse:
    if not url.strip():
        raise HTTPException(status_code=400, detail="url is required")
    normalized = normalize_url(url.strip())
    display_name = name.strip() or normalized
    repo.upsert_feed(conn, display_name, normalized)
    conn.commit()
    return RedirectResponse(url="/feeds?ok=created", status_code=303)


@router.post("/feeds/{feed_id}")
def feed_update(
    feed_id: int,
    name: str = Form(...),
    url: str = Form(""),
    enabled: str | None = Form(None),
    conn: sqlite3.Connection = Depends(get_db),
) -> RedirectResponse:
    feed = repo.get_feed_by_id(conn, feed_id)
    if feed is None:
        raise HTTPException(status_code=404, detail="feed not found")
    url_arg: str | None = None
    if url.strip():
        normalized = normalize_url(url.strip())
        if normalized != feed["url"]:
            url_arg = normalized
    try:
        repo.update_feed(conn, feed_id, name=name.strip(), url=url_arg)
        repo.set_feed_enabled(conn, feed_id, bool(enabled))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        return RedirectResponse(
            url=f"/feeds/{feed_id}/edit?error=duplicate",
            status_code=303,
        )
    return RedirectResponse(url="/feeds?ok=updated", status_code=303)


@router.post("/feeds/{feed_id}/delete")
def feed_delete(
    feed_id: int,
    conn: sqlite3.Connection = Depends(get_db),
) -> RedirectResponse:
    feed = repo.get_feed_by_id(conn, feed_id)
    if feed is None:
        raise HTTPException(status_code=404, detail="feed not found")
    repo.delete_feed(conn, feed_id)
    conn.commit()
    return RedirectResponse(url="/feeds", status_code=303)


@router.post("/feeds/{feed_id}/toggle")
def feed_toggle(
    feed_id: int,
    conn: sqlite3.Connection = Depends(get_db),
) -> RedirectResponse:
    feed = repo.get_feed_by_id(conn, feed_id)
    if feed is None:
        raise HTTPException(status_code=404, detail="feed not found")
    repo.set_feed_enabled(conn, feed_id, not bool(feed["enabled"]))
    conn.commit()
    return RedirectResponse(url="/feeds", status_code=303)


@router.post("/feeds/{feed_id}/reset")
def feed_reset(
    feed_id: int,
    conn: sqlite3.Connection = Depends(get_db),
) -> RedirectResponse:
    feed = repo.get_feed_by_id(conn, feed_id)
    if feed is None:
        raise HTTPException(status_code=404, detail="feed not found")
    repo.reset_feed_failures(conn, feed_id)
    conn.commit()
    return RedirectResponse(url="/feeds", status_code=303)
