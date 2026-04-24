"""Feed/카테고리 관련 라우트 (PRD §9).

- GET /feeds : 현재 등록된 피드 목록 + 추가/삭제/비활성화 폼 (HTML).
- POST /feeds/add : URL 추가. 기존과 중복되면 409.
- POST /feeds/{id}/toggle : `is_active` 토글.
- POST /feeds/{id}/delete : 피드 삭제 (articles CASCADE).
- GET / : 최상위 카테고리 목록. `has_unread_updates=true` 상단 정렬.
- GET /categories/{id} : 주제 위키 페이지 (Markdown → HTML) + 원문 글 목록.
  방문 시 `wiki_pages.has_unread_updates=0`, `last_seen_at=datetime('now')`.
- GET /search?q=... : FTS5 MATCH 로 articles.title/llm_summary/extracted_content 검색.

템플릿(`feeds.html` 등)은 후속 태스크에서 추가되므로, 지금은 존재할 경우에만 사용하고
없으면 인라인 HTML로 최소 렌더링한다. 라우트 행동(상태 코드, DB 갱신)은 동일하다.
"""

from __future__ import annotations

import html
import re
import sqlite3
from typing import AsyncIterator

import markdown as markdown_lib
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from rss_wiki import config
from rss_wiki.scheduler import FetchBusyError, run_fetch_cycle


router = APIRouter()


async def get_conn(request: Request) -> AsyncIterator[sqlite3.Connection]:
    """요청마다 DB 연결을 열고 닫는 의존성.

    비동기 제너레이터로 둬서 연결 생성/소비가 같은 이벤트 루프 스레드에서 이뤄지게 한다.
    (동기 제너레이터를 쓰면 FastAPI 가 스레드풀에서 실행해 sqlite3 스레드 체크에 걸림)
    """
    conn = request.app.state.connection_factory()
    try:
        yield conn
    finally:
        conn.close()


def _templates_searchpaths(request: Request) -> list[str]:
    """Jinja2Templates 내부 FileSystemLoader 의 searchpath 목록을 가져온다.

    FastAPI 최신 버전에서 `Jinja2Templates` 가 `.directory` 속성을 외부로 노출하지
    않으므로, 실제 로더의 searchpath 를 읽어 템플릿 파일 존재 여부를 확인한다.
    """
    templates = getattr(request.app.state, "templates", None)
    if templates is None:
        return []
    env = getattr(templates, "env", None)
    loader = getattr(env, "loader", None) if env is not None else None
    paths = getattr(loader, "searchpath", None)
    if not paths:
        return []
    return [str(p) for p in paths]


def _template_exists(request: Request, name: str) -> bool:
    from pathlib import Path

    for base in _templates_searchpaths(request):
        if (Path(base) / name).exists():
            return True
    return False


def _render_feeds_html(request: Request, feeds: list[dict]) -> HTMLResponse:
    templates = getattr(request.app.state, "templates", None)
    if templates is not None and _template_exists(request, "feeds.html"):
        return templates.TemplateResponse(
            request=request,
            name="feeds.html",
            context={"feeds": feeds},
        )

    rows_html = "".join(
        (
            "<li data-feed-id=\"{id}\">{url} ({status})</li>".format(
                id=f["id"],
                url=html.escape(f["url"]),
                status="활성" if f["is_active"] else "비활성",
            )
        )
        for f in feeds
    )
    body = (
        "<!doctype html><html><body>"
        "<h1>Feeds</h1>"
        "<form action=\"/feeds/add\" method=\"post\">"
        "<input type=\"url\" name=\"url\" required>"
        "<button type=\"submit\">추가</button>"
        "</form>"
        f"<ul>{rows_html}</ul>"
        "</body></html>"
    )
    return HTMLResponse(body)


@router.get("/feeds", response_class=HTMLResponse)
async def list_feeds(
    request: Request,
    conn: sqlite3.Connection = Depends(get_conn),
) -> HTMLResponse:
    rows = conn.execute(
        "SELECT id, url, title, is_active, last_fetched_at, consecutive_failures, created_at "
        "FROM feeds ORDER BY created_at DESC, id DESC"
    ).fetchall()
    feeds = [dict(r) for r in rows]
    return _render_feeds_html(request, feeds)


@router.post("/feeds/add")
async def add_feed(
    url: str = Form(...),
    title: str | None = Form(None),
    conn: sqlite3.Connection = Depends(get_conn),
) -> RedirectResponse:
    normalized = url.strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="URL is required")
    try:
        conn.execute(
            "INSERT INTO feeds (url, title) VALUES (?, ?)",
            (normalized, title.strip() if title else None),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Feed URL already exists")
    return RedirectResponse(url="/feeds", status_code=303)


@router.post("/feeds/{feed_id}/toggle")
async def toggle_feed(
    feed_id: int,
    conn: sqlite3.Connection = Depends(get_conn),
) -> RedirectResponse:
    cursor = conn.execute(
        "UPDATE feeds SET is_active = 1 - is_active WHERE id = ?",
        (feed_id,),
    )
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Feed not found")
    conn.commit()
    return RedirectResponse(url="/feeds", status_code=303)


@router.post("/feeds/{feed_id}/delete")
async def delete_feed(
    feed_id: int,
    conn: sqlite3.Connection = Depends(get_conn),
) -> RedirectResponse:
    cursor = conn.execute("DELETE FROM feeds WHERE id = ?", (feed_id,))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Feed not found")
    conn.commit()
    return RedirectResponse(url="/feeds", status_code=303)


def _render_index_html(request: Request, categories: list[dict]) -> HTMLResponse:
    if _template_exists(request, "index.html"):
        return request.app.state.templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"categories": categories},
        )

    items = []
    for c in categories:
        badge = " <strong>(업데이트)</strong>" if c.get("has_unread_updates") else ""
        items.append(
            "<li data-category-id=\"{id}\"><a href=\"/categories/{id}\">{name}</a>{badge}</li>".format(
                id=c["id"],
                name=html.escape(c["name"]),
                badge=badge,
            )
        )
    rows_html = "".join(items) or "<li>(카테고리 없음)</li>"
    body = (
        "<!doctype html><html><body>"
        "<h1>RSS Wiki</h1>"
        "<h2>카테고리</h2>"
        f"<ul>{rows_html}</ul>"
        "<p><a href=\"/feeds\">피드 관리</a></p>"
        "</body></html>"
    )
    return HTMLResponse(body)


def _render_category_html(
    request: Request,
    category: dict,
    content_html: str,
    articles: list[dict],
    children: list[dict],
) -> HTMLResponse:
    if _template_exists(request, "category.html"):
        return request.app.state.templates.TemplateResponse(
            request=request,
            name="category.html",
            context={
                "category": category,
                "content_html": content_html,
                "articles": articles,
                "children": children,
            },
        )

    articles_html = "".join(
        "<li><a href=\"{url}\">{title}</a>{pub}</li>".format(
            url=html.escape(a["url"]),
            title=html.escape(a["title"]),
            pub=f" — {html.escape(a['published_at'])}" if a.get("published_at") else "",
        )
        for a in articles
    ) or "<li>(원문 없음)</li>"

    children_section = ""
    if children:
        children_items = "".join(
            "<li><a href=\"/categories/{id}\">{name}</a></li>".format(
                id=c["id"], name=html.escape(c["name"])
            )
            for c in children
        )
        children_section = f"<h2>하위 카테고리</h2><ul>{children_items}</ul>"

    body = (
        "<!doctype html><html><body>"
        f"<p><a href=\"/\">← 카테고리 목록</a></p>"
        f"<h1>{html.escape(category['name'])}</h1>"
        f"<section class=\"wiki\">{content_html or '<p>(위키 페이지가 아직 생성되지 않았습니다)</p>'}</section>"
        f"{children_section}"
        "<h2>원문</h2>"
        f"<ul>{articles_html}</ul>"
        "</body></html>"
    )
    return HTMLResponse(body)


@router.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    conn: sqlite3.Connection = Depends(get_conn),
) -> HTMLResponse:
    rows = conn.execute(
        """
        SELECT c.id, c.name, c.description,
               COALESCE(w.has_unread_updates, 0) AS has_unread_updates,
               w.last_rebuilt_at
        FROM categories c
        LEFT JOIN wiki_pages w ON w.category_id = c.id
        WHERE c.parent_id IS NULL AND c.merged_into_id IS NULL
        ORDER BY COALESCE(w.has_unread_updates, 0) DESC, c.name ASC
        """
    ).fetchall()
    categories = [dict(r) for r in rows]
    return _render_index_html(request, categories)


def _render_manage_html(request: Request, categories: list[dict]) -> HTMLResponse:
    if _template_exists(request, "categories_manage.html"):
        return request.app.state.templates.TemplateResponse(
            request=request,
            name="categories_manage.html",
            context={"categories": categories},
        )

    rows_html = "".join(
        (
            "<tr data-category-id=\"{id}\">"
            "<td>{name}</td>"
            "<td>{parent}</td>"
            "<td>{user_edited}</td>"
            "</tr>"
        ).format(
            id=c["id"],
            name=html.escape(c["name"]),
            parent=html.escape(c["parent_name"] or ""),
            user_edited="user" if c["is_user_edited"] else "",
        )
        for c in categories
    )
    body = (
        "<!doctype html><html><body>"
        "<h1>카테고리 관리</h1>"
        "<table><thead><tr>"
        "<th>이름</th><th>상위</th><th>수정</th>"
        "</tr></thead><tbody>"
        f"{rows_html}"
        "</tbody></table>"
        "<p><a href=\"/\">← 카테고리 목록</a></p>"
        "</body></html>"
    )
    return HTMLResponse(body)


@router.get("/categories/manage", response_class=HTMLResponse)
async def manage_categories(
    request: Request,
    conn: sqlite3.Connection = Depends(get_conn),
) -> HTMLResponse:
    rows = conn.execute(
        """
        SELECT c.id, c.name, c.parent_id, c.is_user_edited,
               p.name AS parent_name
        FROM categories c
        LEFT JOIN categories p ON p.id = c.parent_id
        WHERE c.merged_into_id IS NULL
        ORDER BY COALESCE(p.name, c.name), c.name
        """
    ).fetchall()
    categories = [dict(r) for r in rows]
    return _render_manage_html(request, categories)


@router.post("/categories/{category_id}/rename")
async def rename_category(
    category_id: int,
    name: str = Form(...),
    conn: sqlite3.Connection = Depends(get_conn),
) -> RedirectResponse:
    normalized = name.strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="Name is required")
    cur = conn.execute("SELECT id FROM categories WHERE id = ?", (category_id,))
    if cur.fetchone() is None:
        raise HTTPException(status_code=404, detail="Category not found")
    try:
        conn.execute(
            "UPDATE categories SET name = ?, is_user_edited = 1 WHERE id = ?",
            (normalized, category_id),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Category name already exists")
    return RedirectResponse(url="/categories/manage", status_code=303)


@router.post("/categories/{category_id}/merge")
async def merge_category(
    category_id: int,
    target_id: int = Form(...),
    conn: sqlite3.Connection = Depends(get_conn),
) -> RedirectResponse:
    if target_id == category_id:
        raise HTTPException(status_code=400, detail="Cannot merge category into itself")

    src = conn.execute(
        "SELECT id FROM categories WHERE id = ?", (category_id,)
    ).fetchone()
    if src is None:
        raise HTTPException(status_code=404, detail="Category not found")
    tgt = conn.execute(
        "SELECT id FROM categories WHERE id = ? AND merged_into_id IS NULL",
        (target_id,),
    ).fetchone()
    if tgt is None:
        raise HTTPException(status_code=400, detail="Target category not found")

    conn.execute(
        "UPDATE articles SET primary_category_id = ? WHERE primary_category_id = ?",
        (target_id, category_id),
    )
    conn.execute("DELETE FROM wiki_pages WHERE category_id = ?", (category_id,))
    conn.execute(
        "UPDATE categories SET merged_into_id = ? WHERE id = ?",
        (target_id, category_id),
    )

    existing = conn.execute(
        "SELECT id FROM wiki_pages WHERE category_id = ?", (target_id,)
    ).fetchone()
    if existing is None:
        conn.execute(
            "INSERT INTO wiki_pages (category_id, has_unread_updates) VALUES (?, 1)",
            (target_id,),
        )
    else:
        conn.execute(
            "UPDATE wiki_pages SET has_unread_updates = 1 WHERE category_id = ?",
            (target_id,),
        )
    conn.commit()
    return RedirectResponse(url="/categories/manage", status_code=303)


@router.post("/categories/{category_id}/parent")
async def set_category_parent(
    category_id: int,
    parent_id: str = Form(""),
    conn: sqlite3.Connection = Depends(get_conn),
) -> RedirectResponse:
    row = conn.execute(
        "SELECT id FROM categories WHERE id = ?", (category_id,)
    ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Category not found")

    new_parent: int | None
    stripped = parent_id.strip()
    if stripped == "":
        new_parent = None
    else:
        try:
            new_parent = int(stripped)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid parent_id")
        if new_parent == category_id:
            raise HTTPException(status_code=400, detail="Cannot set category as its own parent")
        parent_row = conn.execute(
            "SELECT parent_id FROM categories WHERE id = ? AND merged_into_id IS NULL",
            (new_parent,),
        ).fetchone()
        if parent_row is None:
            raise HTTPException(status_code=400, detail="Parent category not found")
        # 2단계 고정: 부모가 이미 부모를 가지면 3단계가 된다.
        if parent_row["parent_id"] is not None:
            raise HTTPException(status_code=400, detail="Category hierarchy limited to 2 levels")
        # 2단계 고정: 본인에게 이미 자식이 있으면 부모를 붙일 수 없다.
        child_count = conn.execute(
            "SELECT COUNT(*) AS n FROM categories "
            "WHERE parent_id = ? AND merged_into_id IS NULL",
            (category_id,),
        ).fetchone()
        if child_count is not None and int(child_count["n"]) > 0:
            raise HTTPException(status_code=400, detail="Category hierarchy limited to 2 levels")

    conn.execute(
        "UPDATE categories SET parent_id = ? WHERE id = ?",
        (new_parent, category_id),
    )
    conn.commit()
    return RedirectResponse(url="/categories/manage", status_code=303)


@router.get("/categories/{category_id}", response_class=HTMLResponse)
async def category_detail(
    category_id: int,
    request: Request,
    conn: sqlite3.Connection = Depends(get_conn),
) -> HTMLResponse:
    cat_row = conn.execute(
        "SELECT id, name, description, parent_id FROM categories WHERE id = ?",
        (category_id,),
    ).fetchone()
    if cat_row is None:
        raise HTTPException(status_code=404, detail="Category not found")
    category = dict(cat_row)

    wiki_row = conn.execute(
        "SELECT content_markdown, last_rebuilt_at, has_unread_updates, last_seen_at "
        "FROM wiki_pages WHERE category_id = ?",
        (category_id,),
    ).fetchone()
    content_markdown = wiki_row["content_markdown"] if wiki_row else ""

    articles = [
        dict(r)
        for r in conn.execute(
            "SELECT id, title, url, published_at, llm_summary "
            "FROM articles "
            "WHERE primary_category_id = ? AND status = 'ok' "
            "ORDER BY published_at DESC, id DESC",
            (category_id,),
        ).fetchall()
    ]

    children = [
        dict(r)
        for r in conn.execute(
            "SELECT id, name FROM categories "
            "WHERE parent_id = ? AND merged_into_id IS NULL "
            "ORDER BY name ASC",
            (category_id,),
        ).fetchall()
    ]

    # 방문 시 읽음 처리: wiki_pages 가 있을 때만 업데이트.
    conn.execute(
        "UPDATE wiki_pages SET has_unread_updates = 0, last_seen_at = datetime('now') "
        "WHERE category_id = ?",
        (category_id,),
    )
    conn.commit()

    content_html = markdown_lib.markdown(content_markdown) if content_markdown else ""
    return _render_category_html(request, category, content_html, articles, children)


# ---------- /search (PRD §9) ----------

# FTS5 쿼리에서 식별자로 사용할 수 있는 토큰 후보. unicode61 토크나이저 기준으로
# 문자/숫자 + 한중일 블록을 "단어" 문자로 취급. 나머지 구두점은 토큰 구분자로 본다.
_FTS_TOKEN_PATTERN = re.compile(r"[\w　-〿぀-ヿ一-鿿]+", re.UNICODE)


def _build_fts_match(query: str) -> str | None:
    """사용자 입력을 안전한 FTS5 MATCH 쿼리 문자열로 바꾼다.

    원시 입력을 그대로 넘기면 `"`, `AND`, `:` 같은 연산자 때문에 문법 오류가 난다.
    모든 토큰을 따옴표로 감싸 phrase 로 취급하고, AND 결합한다. 토큰이 하나도 없으면
    `None` 을 반환해 호출자가 빈 결과로 처리하도록 한다.
    """
    tokens = _FTS_TOKEN_PATTERN.findall(query)
    if not tokens:
        return None
    # FTS5 phrase 는 `"..."` 로 감싸고 내부 `"` 는 `""` 로 이스케이프한다.
    quoted = ['"' + t.replace('"', '""') + '"' for t in tokens]
    return " AND ".join(quoted)


def _render_search_html(
    request: Request, query: str, results: list[dict]
) -> HTMLResponse:
    if _template_exists(request, "search.html"):
        return request.app.state.templates.TemplateResponse(
            request=request,
            name="search.html",
            context={"query": query, "results": results},
        )

    rows_html = "".join(
        (
            "<li data-article-id=\"{id}\">"
            "<a href=\"{url}\">{title}</a>"
            "{pub}{category}{summary}"
            "</li>"
        ).format(
            id=r["id"],
            url=html.escape(r["url"]),
            title=html.escape(r["title"]),
            pub=f" — {html.escape(r['published_at'])}" if r.get("published_at") else "",
            category=(
                f" [<a href=\"/categories/{r['category_id']}\">"
                f"{html.escape(r['category_name'])}</a>]"
                if r.get("category_name")
                else ""
            ),
            summary=(
                f"<p>{html.escape(r['llm_summary'])}</p>"
                if r.get("llm_summary")
                else ""
            ),
        )
        for r in results
    )
    if query and not results:
        rows_html = "<li>(검색 결과 없음)</li>"
    list_section = f"<ul>{rows_html}</ul>" if query else ""

    body = (
        "<!doctype html><html><body>"
        "<h1>검색</h1>"
        "<form action=\"/search\" method=\"get\">"
        f'<input type="text" name="q" value="{html.escape(query)}" placeholder="검색어">'
        "<button type=\"submit\">검색</button>"
        "</form>"
        f"{list_section}"
        "<p><a href=\"/\">← 카테고리 목록</a></p>"
        "</body></html>"
    )
    return HTMLResponse(body)


@router.get("/search", response_class=HTMLResponse)
async def search(
    request: Request,
    q: str = "",
    conn: sqlite3.Connection = Depends(get_conn),
) -> HTMLResponse:
    query = q.strip()
    if not query:
        return _render_search_html(request, "", [])

    match_expr = _build_fts_match(query)
    if match_expr is None:
        return _render_search_html(request, query, [])

    rows = conn.execute(
        """
        SELECT a.id, a.url, a.title, a.published_at, a.llm_summary,
               c.id   AS category_id,
               c.name AS category_name
        FROM articles_fts
        JOIN articles a ON a.id = articles_fts.rowid
        LEFT JOIN categories c ON c.id = a.primary_category_id
        WHERE articles_fts MATCH ?
          AND a.status = 'ok'
        ORDER BY bm25(articles_fts), a.published_at DESC
        LIMIT 100
        """,
        (match_expr,),
    ).fetchall()
    results = [dict(r) for r in rows]
    return _render_search_html(request, query, results)


# ---------- /logs (PRD §9, §10) ----------


def _render_logs_html(request: Request, logs: list[dict]) -> HTMLResponse:
    if _template_exists(request, "logs.html"):
        return request.app.state.templates.TemplateResponse(
            request=request,
            name="logs.html",
            context={"logs": logs},
        )

    rows_html = "".join(
        (
            "<tr data-log-id=\"{id}\" data-status=\"{status}\">"
            "<td>{started_at}</td>"
            "<td>{job_type}</td>"
            "<td>{target_ref}</td>"
            "<td>{status}</td>"
            "<td>{error_message}</td>"
            "</tr>"
        ).format(
            id=r["id"],
            started_at=html.escape(r["started_at"] or ""),
            job_type=html.escape(r["job_type"] or ""),
            target_ref=html.escape(r["target_ref"] or ""),
            status=html.escape(r["status"] or ""),
            error_message=html.escape(r["error_message"] or ""),
        )
        for r in logs
    )
    if not rows_html:
        rows_html = "<tr><td colspan=\"5\">(로그 없음)</td></tr>"

    body = (
        "<!doctype html><html><body>"
        "<h1>작업 로그</h1>"
        "<table><thead><tr>"
        "<th>시작</th><th>종류</th><th>대상</th><th>상태</th><th>메시지</th>"
        "</tr></thead><tbody>"
        f"{rows_html}"
        "</tbody></table>"
        "<p><a href=\"/\">← 카테고리 목록</a></p>"
        "</body></html>"
    )
    return HTMLResponse(body)


@router.get("/logs", response_class=HTMLResponse)
async def list_logs(
    request: Request,
    conn: sqlite3.Connection = Depends(get_conn),
) -> HTMLResponse:
    rows = conn.execute(
        """
        SELECT id, job_type, target_ref, status, error_message,
               attempt_count, started_at, finished_at
          FROM job_logs
         ORDER BY started_at DESC, id DESC
         LIMIT ?
        """,
        (config.JOB_LOG_LIST_LIMIT,),
    ).fetchall()
    logs = [dict(r) for r in rows]
    return _render_logs_html(request, logs)


# ---------- POST /api/fetch (PRD §9, §7.1) ----------


@router.post("/api/fetch")
async def trigger_fetch(request: Request) -> JSONResponse:
    try:
        result = await run_fetch_cycle(
            connection_factory=request.app.state.connection_factory,
        )
    except FetchBusyError:
        raise HTTPException(status_code=409, detail="fetch cycle already running")
    return JSONResponse(
        status_code=202,
        content={
            "feeds_attempted": result.feeds_attempted,
            "feeds_succeeded": result.feeds_succeeded,
            "feeds_failed": result.feeds_failed,
            "new_articles": result.new_articles,
            "ok_articles": result.ok_articles,
            "failed_articles": result.failed_articles,
            "affected_category_ids": result.affected_category_ids,
            "rebuilt_category_ids": result.rebuilt_category_ids,
            "rebuild_failed_category_ids": result.rebuild_failed_category_ids,
        },
    )
