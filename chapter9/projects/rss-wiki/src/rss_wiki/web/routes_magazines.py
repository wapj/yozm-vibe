from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse

from rss_wiki.storage import repo
from rss_wiki.web.app import get_db
from rss_wiki.web.markdown import render_markdown

router = APIRouter()


def _magazine_items(rows: list[sqlite3.Row]) -> list[dict]:
    items: list[dict] = []
    for r in rows:
        items.append(
            {
                "title": f"{r['kind']} {r['published_at']}",
                "subtitle": r["file_path"],
                "href": f"/magazines/{r['id']}",
            }
        )
    return items


@router.get("/", response_class=HTMLResponse)
def index(request: Request, conn: sqlite3.Connection = Depends(get_db)) -> HTMLResponse:
    rows = repo.list_magazines(conn)
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "list.html",
        {"heading": "최근 매거진", "items": _magazine_items(rows), "active_nav": "magazines"},
    )


@router.get("/magazines", response_class=HTMLResponse)
def magazines_list(request: Request, conn: sqlite3.Connection = Depends(get_db)) -> HTMLResponse:
    rows = repo.list_magazines(conn)
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "list.html",
        {"heading": "매거진 인덱스", "items": _magazine_items(rows), "active_nav": "magazines"},
    )


@router.get("/magazines/{magazine_id}", response_class=HTMLResponse)
def magazine_detail(
    magazine_id: int,
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
) -> HTMLResponse:
    row = repo.get_magazine_by_id(conn, magazine_id)
    if row is None:
        raise HTTPException(status_code=404, detail="magazine not found")
    path = Path(row["file_path"])
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail="magazine file missing") from e
    html = render_markdown(text)
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "magazine.html",
        {
            "title": f"{row['kind']} {row['published_at']}",
            "magazine_html": html,
            "active_nav": "magazines",
        },
    )


def _category_items(rows: list[sqlite3.Row]) -> list[dict]:
    return [
        {"title": r["name"], "href": f"/categories/{r['name']}"}
        for r in rows
    ]


def _tag_items(rows: list[sqlite3.Row]) -> list[dict]:
    return [
        {"title": r["name"], "href": f"/tags/{r['name']}"}
        for r in rows
    ]


def _article_items(rows: list[sqlite3.Row]) -> list[dict]:
    items: list[dict] = []
    for r in rows:
        items.append(
            {
                "title": r["title"] or r["url"],
                "href": r["url"],
                "subtitle": r["published_at"] or "",
            }
        )
    return items


@router.get("/categories", response_class=HTMLResponse)
def categories_index(
    request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> HTMLResponse:
    rows = repo.list_categories(conn)
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "list.html",
        {"heading": "카테고리", "items": _category_items(rows), "active_nav": "categories"},
    )


@router.get("/categories/{name}", response_class=HTMLResponse)
def category_articles(
    name: str,
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
) -> HTMLResponse:
    category = repo.get_category_by_name(conn, name)
    if category is None:
        raise HTTPException(status_code=404, detail="category not found")
    rows = repo.list_articles_by_category(conn, category["id"])
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "list.html",
        {
            "heading": f"카테고리: {category['name']}",
            "items": _article_items(rows),
            "active_nav": "categories",
        },
    )


@router.get("/tags", response_class=HTMLResponse)
def tags_index(
    request: Request, conn: sqlite3.Connection = Depends(get_db)
) -> HTMLResponse:
    rows = repo.list_tags(conn)
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "list.html",
        {"heading": "태그", "items": _tag_items(rows), "active_nav": "tags"},
    )


@router.get("/tags/{name}", response_class=HTMLResponse)
def tag_articles(
    name: str,
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
) -> HTMLResponse:
    tag = repo.get_tag_by_name(conn, name)
    if tag is None:
        raise HTTPException(status_code=404, detail="tag not found")
    rows = repo.list_articles_by_tag(conn, tag["id"])
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request,
        "list.html",
        {
            "heading": f"태그: {tag['name']}",
            "items": _article_items(rows),
            "active_nav": "tags",
        },
    )
