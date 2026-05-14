# RSS Wiki — TASKS

표기:
- `[ ]` 미완료 / `[x]` 완료 / `[~]` 진행 중 / `[!]` BLOCKED
- 각 항목에 `acceptance`(완료 판정 기준), `touch`(생성/수정 파일 후보) 명시.

## 현재 사이클 (1~2개만 활성)

**전체 상태: 모든 마일스톤(M1~M8) 완료(218/218 PASS, 2026-05-06 02:30Z). T-019C PASS로 PRD §13 갱신본 잔여 요구 모두 충족 — 컴포넌트 클래스 통일·매거진 본문 스타일·active GNB 강조·`GET /tags` 인덱스. PRD §1~13 전 섹션이 코드/문서/테스트에 반영됨을 본 사이클 Planner가 점검 완료. 활성 슬라이스 없음. `docs/DONE` 발행으로 Planner→Generator→Evaluator 사이클 종료. 백로그 비어 있음.**

### [x] T-019C 컴포넌트 클래스 부착 + `GET /tags` 인덱스 + active GNB 강조 + 매거진 본문 스타일 — M8 마지막 슬라이스 🟢

- **목표:** PRD §13(2026-05-05 갱신본)의 잔여 UI/UX 요구를 한 슬라이스에 충족하여 M8을 마무리한다. (a) `routes_magazines.py`에 `GET /tags` 인덱스 라우트 신설(`repo.list_tags` 재사용 + `templates/list.html` 재사용 — GNB "태그" 메뉴 동작 활성화). (b) `routes_magazines.py`의 GET 7 라우트 + `routes_feeds.py`의 GET 3 라우트 모두에 `active_nav` 컨텍스트 키 주입(매거진/카테고리/태그/피드 4값) → `base.html`의 Jinja2 조건부 active 클래스 활성화(T-019A에서 마크업만 작성, 본 슬라이스에서 컨텍스트 주입). (c) `feeds.html`/`list.html`/`magazine.html`/`feed_edit.html`/`feed_new.html`에 T-019A에서 정의한 컴포넌트 클래스(`.card`/`.badge`/`.badge-success`/`.badge-danger`/`.btn`/`.btn-primary`/`.btn-danger`) 부착. (d) `style.css`에 매거진 본문 영역 스타일 확장(`.magazine-body` 클래스로 스코프 — 헤딩 H1~H4 계층 + `pre`/`code` + `blockquote` 인용 + `table`/`a` 보강). (e) `tests/test_web_app.py`에 7 케이스 추가. PASS 시 PRD §13 갱신본의 모든 신규 요구가 코드/문서/테스트에 반영되어 다음 사이클에서 `docs/DONE` 발행 가능.

- **acceptance:**

  - **`src/rss_wiki/web/routes_magazines.py` 수정 — `/tags` 인덱스 라우트 신설 + 기존 6 라우트에 `active_nav` 주입:**
    1. **`GET /tags` 라우트 신설**(기존 `/tags/{name}` 라우트보다 위에 배치, FastAPI 등록 순서 의존이 아니지만 가독성 우선):
       ```python
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
       ```
       - 자체 결정: `_tag_items` 헬퍼는 T-018D2에서 이미 정의됨(`/tags/{name}` 라우트와 공유). `repo.list_tags`는 M5에서 이미 정의됨(`SELECT id, name FROM tags ORDER BY name ASC`).
    2. **기존 6 라우트에 `active_nav` 컨텍스트 주입** — `index`/`magazines_list`/`magazine_detail`(magazines), `categories_index`/`category_articles`(categories), `tag_articles`(tags). 각 `TemplateResponse` 컨텍스트 dict에 `"active_nav": "<key>"` 키 한 줄 추가. 매핑:
       - `index` (`/`) → `"magazines"`(랜딩 페이지가 매거진 목록 역할)
       - `magazines_list` (`/magazines`) → `"magazines"`
       - `magazine_detail` (`/magazines/{id}`) → `"magazines"`
       - `categories_index` (`/categories`) → `"categories"`
       - `category_articles` (`/categories/{name}`) → `"categories"`
       - `tag_articles` (`/tags/{name}`) → `"tags"`
       - 신규 `tags_index` (`/tags`) → `"tags"`
    - 자체 결정: POST 라우트는 redirect만 반환하므로 active_nav 미관여(`base.html` 미렌더).
    - 자체 결정: `active_nav`는 string 4값(`magazines`/`categories`/`tags`/`feeds`)으로 한정 — `base.html` Jinja2 조건이 이 4값과 비교.

  - **`src/rss_wiki/web/routes_feeds.py` 수정 — 3 GET 라우트에 `active_nav="feeds"` 주입:**
    1. `feeds_index` (`/feeds`): `templates.TemplateResponse(request, "feeds.html", {"feeds": feeds, "active_nav": "feeds"})`
    2. `feed_new_form` (`/feeds/new`): `templates.TemplateResponse(request, "feed_new.html", {"active_nav": "feeds"})`
    3. `feed_edit_form` (`/feeds/{id}/edit`): `templates.TemplateResponse(request, "feed_edit.html", {"feed": feed, "active_nav": "feeds"})`
    - 자체 결정: POST 5 라우트(`feeds_create`/`feed_update`/`feed_delete`/`feed_toggle`/`feed_reset`)는 redirect 반환만 하므로 변경 없음.

  - **`src/rss_wiki/web/static/style.css` 수정 — `.magazine-body` 매거진 본문 스타일 확장(약 30~50줄 추가):**
    ```css
    /* ── Magazine Body (matter rendered from markdown) ───────────────── */
    .magazine-body h1,
    .magazine-body h2,
    .magazine-body h3,
    .magazine-body h4 {
      margin-top: var(--space-6);
      margin-bottom: var(--space-3);
      font-weight: 700;
      line-height: 1.3;
    }
    .magazine-body h1 { font-size: var(--text-2xl); }
    .magazine-body h2 { font-size: var(--text-xl); }
    .magazine-body h3 { font-size: var(--text-lg); }
    .magazine-body h4 { font-size: var(--text-base); }
    .magazine-body p {
      margin: var(--space-3) 0;
    }
    .magazine-body a {
      color: var(--color-accent);
      text-decoration: underline;
    }
    .magazine-body a:hover {
      color: var(--color-accent-hover);
    }
    .magazine-body code {
      font-family: var(--font-mono);
      font-size: 0.9em;
      padding: 2px var(--space-1);
      background-color: var(--color-surface);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-sm);
    }
    .magazine-body pre {
      font-family: var(--font-mono);
      font-size: var(--text-sm);
      padding: var(--space-3) var(--space-4);
      background-color: var(--color-surface);
      border: 1px solid var(--color-border);
      border-radius: var(--radius-md);
      overflow-x: auto;
    }
    .magazine-body pre code {
      padding: 0;
      background: none;
      border: none;
    }
    .magazine-body blockquote {
      margin: var(--space-4) 0;
      padding: var(--space-2) var(--space-4);
      border-left: 4px solid var(--color-accent);
      color: var(--color-text-muted);
      background-color: var(--color-surface);
    }
    ```
    - 자체 결정: 매거진 본문 스타일은 `.magazine-body` 클래스로 스코프 — `<article>` element에 클래스 부착하여 다른 페이지(목록/폼)에 영향 주지 않음. PRD §13 "본문 영역 ~720px 폭 제한"은 T-019A `.container`에서 이미 720px max-width로 충족, 본 슬라이스는 코드/인용/표/링크/제목 계층 스타일 추가.
    - 자체 결정: 표(`<table>`)는 T-019A 기본 element 스타일이 이미 적용됨 — `.magazine-body table` 별도 정의 미추가(중복 회피).

  - **`src/rss_wiki/web/templates/magazine.html` 수정 — `<article>`에 `.magazine-body` 클래스 부착:**
    ```html
    {% extends "base.html" %}
    {% block title %}{{ title }} — RSS Wiki{% endblock %}
    {% block content %}
    <article class="magazine-body">
        {{ magazine_html | safe }}
    </article>
    {% endblock %}
    ```

  - **`src/rss_wiki/web/templates/list.html` 수정 — 항목별 `.card` 래퍼:**
    ```html
    {% extends "base.html" %}
    {% block title %}{{ heading }} — RSS Wiki{% endblock %}
    {% block content %}
    <h2>{{ heading }}</h2>
    {% if items %}
    {% for item in items %}
    <div class="card">
        <a href="{{ item.href }}">{{ item.title }}</a>
        {% if item.subtitle %}<small>{{ item.subtitle }}</small>{% endif %}
    </div>
    {% endfor %}
    {% else %}
    <p>아직 항목이 없습니다.</p>
    {% endif %}
    {% endblock %}
    ```
    - 자체 결정: `<ul>` 리스트 마크업 → `<div class="card">` 카드 형태로 변경. PRD §13 "카드/리스트/배지/버튼/폼 등 공통 컴포넌트의 스타일을 통일" 충족(매거진/카테고리/태그/글 목록 모두 동일 카드 컴포넌트 노출).

  - **`src/rss_wiki/web/templates/feeds.html` 수정 — 컴포넌트 클래스 부착:**
    1. 추가 폼을 `<div class="card">`로 래핑(혹은 form 자체에 `class="card"` 부착).
    2. 활성/비활성 표시를 `.badge` 컴포넌트로:
       ```html
       <td>{% if feed.enabled %}<span class="badge badge-success">활성</span>{% else %}<span class="badge badge-danger">비활성</span>{% endif %}</td>
       ```
    3. 수정 링크/버튼들에 `.btn` 클래스 부착:
       - 추가 폼 `<button type="submit" class="btn btn-primary">추가</button>`
       - `<a href="/feeds/{{ feed.id }}/edit" class="btn">수정</a>`
       - 토글: `<button type="submit" class="btn">토글</button>`
       - 실패 리셋: `<button type="submit" class="btn">실패 리셋</button>`
       - 삭제: `<button type="submit" class="btn btn-danger">삭제</button>`
    - 자체 결정: 인라인 form 3개의 `style="display:inline"` 속성은 그대로 유지(PRD §13 "JS 없이 동작" + 한 행 다중 form 가시성 확보). `.btn` 클래스는 inline-flex이지만 부모 form이 inline이므로 행 내 정렬 정상.

  - **`src/rss_wiki/web/templates/feed_edit.html` / `feed_new.html` 수정 — 제출/취소 버튼에 `.btn` 클래스 부착:**
    - 제출: `<button type="submit" class="btn btn-primary">저장</button>` / `추가`
    - 취소: `<a href="/feeds" class="btn">취소</a>`
    - 자체 결정: form 자체를 카드 래핑하지는 않음(편집 페이지는 단일 폼 페이지로 GNB+컨테이너만으로 충분).

  - **`tests/test_web_app.py` 수정 — 7 케이스 추가:**
    1. `test_tags_index_empty(tmp_path)` — `client.get("/tags")` → 200 + `"태그"` 헤딩 + `"아직 항목이 없습니다"` 본문(빈 목록).
    2. `test_tags_index_with_entries(tmp_path)` — `repo.upsert_tag(conn, "ai")` + `repo.upsert_tag(conn, "kotlin")` + `conn.commit()` → `client.get("/tags")` → 200 + `"ai"` + `"kotlin"` + `'href="/tags/ai"'` + `'href="/tags/kotlin"'` 모두 포함.
    3. `test_active_nav_marks_feeds_link_when_on_feeds_page(tmp_path)` — `client.get("/feeds")` → 200 + `'href="/feeds" class="active"'` 또는 동등 패턴 본문 포함(GNB active 강조 검증).
    4. `test_active_nav_marks_magazines_link_when_on_magazines_page(tmp_path)` — `client.get("/magazines")` → 200 + `'href="/magazines" class="active"'` 본문 포함.
    5. `test_active_nav_marks_tags_link_when_on_tags_page(tmp_path)` — `client.get("/tags")` → 200 + `'href="/tags" class="active"'` 본문 포함.
    6. `test_feeds_html_uses_btn_class(tmp_path)` — `repo.upsert_feed(conn, "Example", "https://example.com/rss")` + `conn.commit()` → `client.get("/feeds")` → 200 + `'class="btn'` 마커 본문 포함(추가 버튼/수정 링크/토글/리셋/삭제 5+ 인스턴스 중 최소 1 발견).
    7. `test_magazine_body_styles_in_css(tmp_path)` — `client.get("/static/style.css")` → 200 + `".magazine-body"` + `"pre"` + `"blockquote"` 3 마커 본문 포함.
    - 자체 결정: 카테고리 active 강조는 `categories` 매핑이 magazines/feeds와 동일 패턴이므로 별도 케이스 미추가(YAGNI). 5 케이스 active 검증 → 3 케이스(`/feeds`/`/magazines`/`/tags`) 균형.
    - 자체 결정: `list.html` `.card` 래퍼 검증은 `test_tags_index_with_entries`에서 `'class="card"'` 마커도 함께 확인(중복 케이스 회피).
    - 픽스처: 기존 `with TestClient(create_app(tmp_db)) as client:` 컨텍스트 패턴 일관.

  - **회귀:** 기존 211 케이스 회귀 0(211/211 PASS 유지). 신규 7 케이스 → 합계 **218/218 PASS** 목표.

- **모듈 경계(엄수):**
  - 변경 파일 9개: `src/rss_wiki/web/routes_magazines.py`(수정 — `/tags` 라우트 + 6 라우트 active_nav 주입), `src/rss_wiki/web/routes_feeds.py`(수정 — 3 GET 라우트 active_nav 주입), `src/rss_wiki/web/static/style.css`(수정 — `.magazine-body` 본문 스타일 약 50줄 추가), `src/rss_wiki/web/templates/feeds.html`(수정 — `.btn`/`.badge`/`.card` 클래스 부착), `src/rss_wiki/web/templates/list.html`(수정 — 항목별 `.card` 래퍼), `src/rss_wiki/web/templates/magazine.html`(수정 — `<article class="magazine-body">`), `src/rss_wiki/web/templates/feed_edit.html`(수정 — 제출/취소 버튼 `.btn`), `src/rss_wiki/web/templates/feed_new.html`(수정 — 제출/취소 버튼 `.btn`), `tests/test_web_app.py`(수정 — 7 케이스 추가).
  - 변경 금지: `src/rss_wiki/{config,cli,main}.py`, `src/rss_wiki/{ingest,llm,publish,pipeline}/*.py`, `src/rss_wiki/storage/{schema.sql,db.py,repo.py}`(repo는 본 슬라이스에서 변경 없음 — `list_tags`/`list_feeds` 등 모두 기존 함수 재사용), `src/rss_wiki/web/{__init__.py,app.py,markdown.py}`, `src/rss_wiki/web/templates/{base.html,_flash.html}`(T-019A·B에서 이미 작성됨 — 변경 불필요), `pyproject.toml`(의존성 미추가), `feeds.toml`, `feeds.example.toml`, `README.md`, `output/*`, `data/*`.
  - 신규 외부 의존성 미추가.

- **touch:**
  - `src/rss_wiki/web/routes_magazines.py` (수정 — `/tags` 라우트 + 6 라우트 active_nav 주입, 약 15줄 추가/변경)
  - `src/rss_wiki/web/routes_feeds.py` (수정 — 3 GET 라우트 active_nav 주입, 약 3줄 변경)
  - `src/rss_wiki/web/static/style.css` (수정 — `.magazine-body` 본문 스타일 약 50줄 추가)
  - `src/rss_wiki/web/templates/feeds.html` (수정 — 컴포넌트 클래스 부착, 약 10줄 변경)
  - `src/rss_wiki/web/templates/list.html` (수정 — 항목별 `.card` 래퍼)
  - `src/rss_wiki/web/templates/magazine.html` (수정 — 1줄: `<article class="magazine-body">`)
  - `src/rss_wiki/web/templates/feed_edit.html` (수정 — 버튼 `.btn` 부착)
  - `src/rss_wiki/web/templates/feed_new.html` (수정 — 버튼 `.btn` 부착)
  - `tests/test_web_app.py` (수정 — 7 케이스 추가)

- **참고:**
  - PRD §13 (2026-05-05 갱신) "카드/리스트/배지/버튼/폼 등 공통 컴포넌트의 스타일을 통일" — `.card`/`.badge`/`.btn` 클래스를 5 템플릿에 부착하여 충족.
  - PRD §13 "본문 영역은 가독성 있는 폭(최대 ~720px)으로 제한하고, 코드/인용/표/링크 스타일을 정리" — 폭은 T-019A `.container`에서 이미 충족, 코드/인용/표/링크는 `.magazine-body` CSS 확장으로 충족.
  - PRD §13 "현재 활성 메뉴는 시각적으로 강조(active 스타일)" — `routes_*.py`의 GET 라우트 10곳에 `active_nav` 주입 + `base.html` Jinja2 조건부 클래스로 충족.
  - PRD §13 라우트 표 — GNB "태그" 메뉴는 PRD §13 GNB 정의에 명시되어 있으나 현재 `/tags` 인덱스 라우트가 미존재(404). `tags_index` 신설로 충족(PRD strict 4 메뉴 모두 동작).
  - **DONE 발행 조건**: T-019C PASS + 다음 사이클 Planner가 PRD §1~13 전 섹션이 코드/문서/테스트에 반영되었음을 점검 → `docs/DONE` 빈 파일 발행으로 프로젝트 종료 신호.

---

### [x] T-019B 피드 CRUD URL 편집 허용 + 토스트/배너 플래시 + `GET /feeds/new` 별도 페이지 — M8 두 번째 슬라이스 (PASS 211/211, 2026-05-06)

- **목표:** PRD §13(2026-05-05 갱신본) "수정: `url`도 수정 가능하도록 한다(변경 시 정규화 후 UNIQUE 검증, 충돌 시 폼에 에러 표시)" + "폼 제출 후 토스트/배너로 처리 결과(성공/실패)를 노출한다(쿼리스트링 플래시 메시지로 구현, JS 없이 동작)" + 라우트 표 `GET /feeds/new`(별도 페이지) 3가지 신규 요구를 한 슬라이스에 충족한다. (a) `repo.update_feed`에 `url: str | None = None` 인자 추가(NULL 시 미변경, 명시 시 정규화 후 자기 자신 제외 UNIQUE 검증 → 충돌 시 `sqlite3.IntegrityError`로 raise — M2 패턴 일관). (b) `routes_feeds.py` 수정 — `feed_update`에 `url: str = Form("")` 추가 + 정규화 + UNIQUE 충돌 시 `RedirectResponse(url=f"/feeds/{feed_id}/edit?error=duplicate", status_code=303)`, 성공 시 `?ok=updated`. `feeds_create`도 동일 패턴(`?error=duplicate` / `?ok=created`). (c) `GET /feeds/new` 라우트 신설 + `templates/feed_new.html` 신규(별도 페이지 추가 폼). (d) `templates/_flash.html` 부분 템플릿 신설(쿼리스트링 `ok`/`error` 코드를 한국어 메시지로 매핑, JS 없이 CSS 배너/배지로 표시). 기존 `feeds.html`/`feed_edit.html`/신규 `feed_new.html`에서 `{% include "_flash.html" %}` 한 줄로 사용. (e) `feed_edit.html` URL 입력 readonly 제거 + 안내 문구("URL 변경 시 정규화 후 중복 검증 — 충돌 시 다시 표시" 류) 교체. (f) `feeds.html` 인라인 추가 폼은 그대로 유지(`/feeds/new` 별도 페이지는 보조 진입점). (g) `tests/test_storage_repo.py`에 2 케이스(`update_feed_url`/`update_feed_url_duplicate_raises`) + `tests/test_web_app.py`에 6~7 케이스 추가.

- **acceptance:**

  - **`src/rss_wiki/storage/repo.py` 수정 — `update_feed` 시그니처 확장:**
    ```python
    def update_feed(
        conn: sqlite3.Connection,
        feed_id: int,
        *,
        name: str,
        url: str | None = None,
    ) -> None:
        if url is None:
            conn.execute(
                "UPDATE feeds SET name = ?, updated_at = datetime('now') WHERE id = ?",
                (name, feed_id),
            )
        else:
            conn.execute(
                "UPDATE feeds SET name = ?, url = ?, updated_at = datetime('now') WHERE id = ?",
                (name, url, feed_id),
            )
    ```
    - 자체 결정: UNIQUE 검증은 별도 SELECT 추가 없이 `feeds.url` UNIQUE 제약 + `sqlite3.IntegrityError` 전파에 위임 — M2 패턴 일관(`IntegrityError`는 가공 없이 전파). 자기 자신 제외는 `UPDATE`가 `WHERE id = ?`로 자신만 갱신하므로 동일 url을 자기 자신에 대해 set 시 제약 위반 안 함(SQLite 동작 검증 — UPDATE 시 새 값이 다른 행과 동일하면 IntegrityError, 같은 행에 동일 값 set은 OK).
    - 자체 결정: `url`이 None이 아니라 빈 문자열이면 그대로 빈 문자열로 UPDATE — 라우트 레이어에서 빈 문자열은 None으로 변환해 storage에 전달(라우트가 정규화 책임). storage는 단순 패스스루.

  - **`src/rss_wiki/web/routes_feeds.py` 수정 — 4 변경:**
    1. **`feeds_create` redirect 변경**: 빈 url은 기존 `HTTPException(400)` 유지(폼 누락은 422로 운영자에 명시적). 성공 시 `RedirectResponse(url="/feeds?ok=created", status_code=303)`. UNIQUE 충돌은 `upsert_feed`가 `INSERT OR IGNORE` 멱등이므로 발생 안 함 — 자체 결정: 멱등 성공도 `?ok=created`로 통일(중복 메시지 분리 안 함, 단순함 우선).
    2. **`feed_update`에 `url` Form 추가 + 정규화 + UNIQUE 충돌 분기**:
       ```python
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
       ```
       - 자체 결정: 빈 url Form 입력 시 url 미변경(name/enabled만 갱신) — 운영자가 url을 비워두고 저장해도 동작.
       - 자체 결정: 정규화 후 기존 url과 동일하면 `url_arg = None`으로 두어 UPDATE에서 url 컬럼 미터치(불필요한 SQL 회피).
       - 자체 결정: `IntegrityError` 캐치 시 `conn.rollback()` 호출 — 같은 트랜잭션 내 `set_feed_enabled` 부분 적용을 막음. M7 인터페이스 원칙 "쓰기 라우트만 commit/rollback".
       - 자체 결정: `import sqlite3`은 이미 import됨.
    3. **`feeds_create`에도 UNIQUE 충돌 처리 추가**: 현재는 `INSERT OR IGNORE`로 silent 멱등. 본 슬라이스도 동일 동작 유지 — duplicate URL 추가는 `?ok=created`로 redirect(중복 인지 메시지는 기존 행 유지가 의도된 멱등 동작이라 별도 분리하지 않음). 자체 결정: PRD §13 "추가 ... URL 정규화 후 `feeds.url` UNIQUE 제약으로 중복 방지"의 "방지"는 silent 멱등으로 해석, 명시적 에러 메시지는 수정 흐름에서만 노출(수정은 자기 자신 제외 검증이 의도적 충돌이므로 `?error=duplicate`로 표면화). 코드 변경 최소(`feeds_create` 본문은 `?ok=created` redirect 1줄만 변경).
    4. **`GET /feeds/new` 라우트 신설:**
       ```python
       @router.get("/feeds/new", response_class=HTMLResponse)
       def feed_new_form(request: Request) -> HTMLResponse:
           templates = request.app.state.templates
           return templates.TemplateResponse(request, "feed_new.html", {})
       ```
       - 자체 결정: `conn` 주입 미필요(폼 렌더만, DB 조회 없음). 라우트 위치는 기존 `feeds_index`/`feed_edit_form` 사이 또는 직후 — `/feeds/new`는 `/feeds/{feed_id}/edit`보다 먼저 등록되어야 path matching 충돌 회피(`new`가 정수가 아니므로 FastAPI 자동 422가 나오지만, 명시적 라우트 등록 순서가 운영 안전). 본 슬라이스에서는 `/feeds/new` GET을 `/feeds` GET 직후, `/feeds/{feed_id}/edit` GET 이전에 배치.
    - 자체 결정: 5+ POST 라우트 중 `feed_delete`/`feed_toggle`/`feed_reset` 3개는 단순 동작이라 본 슬라이스에서 플래시 메시지 미추가(redirect는 `/feeds`로만, 쿼리스트링 추가 시 회귀 surface 확장). T-019C에서 추가 검토.

  - **`src/rss_wiki/web/templates/_flash.html` 신규 — 부분 템플릿(약 15~20줄):**
    ```html
    {% if request.query_params.get("ok") %}
        {% set _ok = request.query_params.get("ok") %}
        <div class="flash flash-success" role="status">
            {% if _ok == "created" %}피드를 추가했습니다.
            {% elif _ok == "updated" %}피드를 수정했습니다.
            {% else %}완료했습니다.
            {% endif %}
        </div>
    {% endif %}
    {% if request.query_params.get("error") %}
        {% set _err = request.query_params.get("error") %}
        <div class="flash flash-danger" role="alert">
            {% if _err == "duplicate" %}이미 같은 URL의 피드가 존재합니다.
            {% else %}처리 중 오류가 발생했습니다.
            {% endif %}
        </div>
    {% endif %}
    ```
    - 자체 결정: `request` 객체는 `Jinja2Templates.TemplateResponse`가 자동 컨텍스트로 주입(FastAPI 0.110+ 권장 시그니처 — `templates.TemplateResponse(request, ...)`). `_flash.html`은 `feeds.html`/`feed_edit.html`/`feed_new.html`이 `{% include "_flash.html" %}` 호출 시 부모 컨텍스트의 `request`를 그대로 사용.
    - 자체 결정: CSS 스타일은 T-019A `style.css`에 `.flash`/`.flash-success`/`.flash-danger` 클래스를 추가 정의(약 10줄, 본 슬라이스 acceptance에 포함). 색상은 토큰(`--color-success`/`--color-danger`/`--color-surface`) 재사용. JS 없이 정적 표시(닫기 버튼 미도입 — 새로고침/링크 이동 시 자동 사라짐).
    - 자체 결정: `role="status"`/`role="alert"` ARIA로 접근성 보강(스크린 리더 인식).
    - 자체 결정: 한국어 메시지 4종(`created`/`updated`/`duplicate` + 기본). 코드 추가 시 본 템플릿만 갱신.

  - **`src/rss_wiki/web/static/style.css` 수정 — `.flash` 컴포넌트 추가(약 10줄):**
    ```css
    .flash {
      padding: var(--space-3) var(--space-4);
      border-radius: var(--radius-md);
      margin-bottom: var(--space-4);
      border: 1px solid var(--color-border);
      background: var(--color-surface);
    }
    .flash-success {
      border-color: var(--color-success);
      color: var(--color-success);
    }
    .flash-danger {
      border-color: var(--color-danger);
      color: var(--color-danger);
    }
    ```
    - 자체 결정: 본 슬라이스에서 `style.css`는 `.flash` 3 클래스만 추가(다른 컴포넌트 클래스 부착은 T-019C 책임). 줄수 약 280줄로 증가.

  - **`src/rss_wiki/web/templates/feed_new.html` 신규(약 20줄):**
    ```html
    {% extends "base.html" %}
    {% block title %}피드 추가 — RSS Wiki{% endblock %}
    {% block content %}
    <h2>피드 추가</h2>
    {% include "_flash.html" %}
    <form method="post" action="/feeds">
        <p>
            <label>피드 URL
                <input type="url" name="url" required>
            </label>
        </p>
        <p>
            <label>이름(선택)
                <input type="text" name="name">
            </label>
        </p>
        <p>
            <button type="submit">추가</button>
            <a href="/feeds">취소</a>
        </p>
    </form>
    {% endblock %}
    ```

  - **`src/rss_wiki/web/templates/feed_edit.html` 수정 — URL readonly 제거 + 안내 교체 + 플래시 include:**
    ```html
    {% extends "base.html" %}
    {% block title %}피드 수정 — RSS Wiki{% endblock %}
    {% block content %}
    <h2>피드 수정</h2>
    {% include "_flash.html" %}
    <form method="post" action="/feeds/{{ feed.id }}">
        <p>
            <label>이름
                <input type="text" name="name" value="{{ feed.name }}" required>
            </label>
        </p>
        <p>
            <label>URL (변경 시 정규화 후 중복 검증)
                <input type="url" name="url" value="{{ feed.url }}">
            </label>
        </p>
        <p>
            <label>
                <input type="checkbox" name="enabled" {% if feed.enabled %}checked{% endif %}>
                활성
            </label>
        </p>
        <p>
            <button type="submit">저장</button>
            <a href="/feeds">취소</a>
        </p>
    </form>
    {% endblock %}
    ```
    - 자체 결정: URL input은 `name="url"`로 form에 포함(라우트가 빈 문자열이면 미변경 처리), readonly 속성 제거.

  - **`src/rss_wiki/web/templates/feeds.html` 수정 — 플래시 include 1줄 추가:**
    - `<h2>피드</h2>` 다음 줄에 `{% include "_flash.html" %}` 추가. 인라인 추가 폼은 그대로 유지(자체 결정: `/feeds/new` 별도 페이지는 보조 진입점, 인라인 폼이 운영자에게 더 빠른 경로).

  - **`tests/test_storage_repo.py` 수정 — 2 케이스 추가:**
    1. `test_update_feed_url_changes_url(tmp_db)` — `feed_id = upsert_feed(conn, "Old", "https://a.example.com/rss")`. `update_feed(conn, feed_id, name="Old", url="https://b.example.com/rss")` → `get_feed_by_id(conn, feed_id)["url"] == "https://b.example.com/rss"`.
    2. `test_update_feed_url_duplicate_raises(tmp_db)` — 두 피드 생성(`https://a...`, `https://b...`) → `update_feed(conn, feed_b_id, name="B", url="https://a.example.com/rss")` → `pytest.raises(sqlite3.IntegrityError)`.
    - 자체 결정: `url=None`(미변경) 동작은 기존 `update_feed` 호출자(test 또는 라우트)가 이미 검증 — 본 슬라이스에서 별도 케이스 미추가.

  - **`tests/test_web_app.py` 수정 — 6 케이스 추가:**
    1. `test_get_feeds_new_returns_form(tmp_path)` — `client.get("/feeds/new")` → 200 + `<form method="post" action="/feeds">` + `name="url"` + `name="name"` 마커.
    2. `test_post_feed_update_changes_url(tmp_path)` — 피드 1행 → `client.post(f"/feeds/{id}", data={"name": "X", "url": "https://b.example.com/rss", "enabled": "on"}, follow_redirects=False)` → 303 + `Location` `/feeds?ok=updated` + DB url 변경.
    3. `test_post_feed_update_duplicate_url_redirects_to_edit_with_error(tmp_path)` — 두 피드(A, B) → B를 A의 url로 변경 시도 → 303 + `Location` `/feeds/{B.id}/edit?error=duplicate` + DB url 미변경(rollback).
    4. `test_post_feed_update_empty_url_keeps_existing(tmp_path)` — 피드 1행 → `data={"name": "X", "url": ""}` → 303 + DB url 미변경.
    5. `test_feeds_create_redirects_with_ok(tmp_path)` — `client.post("/feeds", data={"url": "https://example.com/rss"}, follow_redirects=False)` → 303 + `Location` `/feeds?ok=created`.
    6. `test_feeds_index_renders_flash_on_ok_query(tmp_path)` — `client.get("/feeds?ok=created")` → 200 + `class="flash"` + `class="flash-success"` + `피드를 추가했습니다.` 포함.
    7. `test_feed_edit_renders_flash_on_error_query(tmp_path)` — feed 1개 + `client.get(f"/feeds/{id}/edit?error=duplicate")` → 200 + `class="flash-danger"` + `이미 같은 URL의 피드가 존재합니다.` 포함.
    - 자체 결정: 7 케이스로 핵심 흐름(`/feeds/new` GET, URL 변경 성공/실패/빈/생성 redirect, 플래시 렌더 ok/error) 균형 커버.
    - 픽스처: 기존 `with TestClient(create_app(tmp_db)) as client:` 컨텍스트 패턴 일관. `follow_redirects=False`로 303 응답 직접 검증.

  - **회귀:** 기존 202 케이스 회귀 0(202/202 PASS 유지). 신규 storage 2 + web 7 = 9 케이스 → 합계 **211/211 PASS** 목표.

- **모듈 경계(엄수):**
  - 변경 파일: `src/rss_wiki/storage/repo.py`(수정 — `update_feed` `url` 인자 추가), `src/rss_wiki/web/routes_feeds.py`(수정 — `feeds_create` redirect 쿼리스트링, `feed_update` url Form + UNIQUE 충돌 분기, `GET /feeds/new` 라우트 추가), `src/rss_wiki/web/static/style.css`(수정 — `.flash` 3 클래스 추가), `src/rss_wiki/web/templates/_flash.html`(신규), `src/rss_wiki/web/templates/feed_new.html`(신규), `src/rss_wiki/web/templates/feed_edit.html`(수정 — URL readonly 제거 + 안내 교체 + flash include), `src/rss_wiki/web/templates/feeds.html`(수정 — flash include 1줄), `tests/test_storage_repo.py`(수정 — 2 케이스), `tests/test_web_app.py`(수정 — 7 케이스) — 합계 9개.
  - 변경 금지: `src/rss_wiki/{config,cli,main}.py`, `src/rss_wiki/{ingest,llm,publish,pipeline}/*.py`, `src/rss_wiki/storage/{schema.sql,db.py}`, `src/rss_wiki/web/{__init__.py,app.py,markdown.py,routes_magazines.py}`, `src/rss_wiki/web/templates/{base,list,magazine}.html`(GNB·매거진 본문 스타일은 T-019C 책임), `pyproject.toml`(의존성 미추가), `feeds.toml`, `feeds.example.toml`, `README.md`, `output/*`, `data/*`.
  - 신규 외부 의존성 미추가.

- **touch:**
  - `src/rss_wiki/storage/repo.py` (수정 — `update_feed` `url` 인자 추가, 약 8줄)
  - `src/rss_wiki/web/routes_feeds.py` (수정 — `feeds_create`/`feed_update` 본문 + `GET /feeds/new` 라우트, 약 25줄 추가/변경)
  - `src/rss_wiki/web/static/style.css` (수정 — `.flash` 3 클래스 약 12줄 추가)
  - `src/rss_wiki/web/templates/_flash.html` (신규 — 약 18줄)
  - `src/rss_wiki/web/templates/feed_new.html` (신규 — 약 20줄)
  - `src/rss_wiki/web/templates/feed_edit.html` (수정 — URL readonly 제거 + 안내 교체 + flash include, 약 5줄 변경)
  - `src/rss_wiki/web/templates/feeds.html` (수정 — flash include 1줄 추가)
  - `tests/test_storage_repo.py` (수정 — 2 케이스 추가)
  - `tests/test_web_app.py` (수정 — 7 케이스 추가)

- **참고:**
  - PRD §13 (2026-05-05 갱신) "수정: `url`도 수정 가능하도록 한다(변경 시 정규화 후 UNIQUE 검증, 충돌 시 폼에 에러 표시)" — `feed_update`의 url Form + 정규화 + IntegrityError 캐치 → `?error=duplicate` redirect로 충족.
  - PRD §13 "폼 제출 후 토스트/배너로 처리 결과(성공/실패)를 노출한다(쿼리스트링 플래시 메시지로 구현, JS 없이 동작)" — `_flash.html` + `.flash`/`.flash-success`/`.flash-danger` CSS + redirect 시 `?ok=`/`?error=` 쿼리로 충족.
  - PRD §13 라우트 표 `GET /feeds/new` "피드 추가 폼 (별도 페이지)" — `feed_new_form` 라우트 + `feed_new.html` 신규로 충족.
  - **DONE 발행 조건:** T-019B PASS 후 T-019C(M8 마지막 슬라이스 — 컴포넌트 클래스 부착 + `/tags` 인덱스 + active GNB + 매거진 본문 스타일) PASS까지 완료한 다음 사이클 Planner가 PRD §13 갱신본 전 항목을 점검하고 `docs/DONE` 발행. T-019B 단독 PASS는 DONE 조건 미충족.

---

### [x] T-019A 디자인 토큰 + 단일 CSS 파일 + base.html GNB + 다크모드 + 반응형 + StaticFiles 마운트 — M8 첫 슬라이스 (PASS 202/202, 2026-05-06)

- **목표:** PRD §13(2026-05-05 갱신본) "모던한 디자인" + "단일 CSS 파일 디자인 시스템" + "라이트/다크 모드 자동" + "반응형" + "상단 GNB"의 토대를 한 슬라이스에 마련한다. (a) `src/rss_wiki/web/static/style.css` 신규(약 200~300줄, 디자인 토큰 5축 + 라이트/다크 자동 + 반응형 미디어 쿼리 + GNB 컴포넌트 + 카드/배지/버튼/폼 기본 클래스), (b) `web/app.py`에 `from fastapi.staticfiles import StaticFiles` import 1줄 + `app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")` 1줄 추가, (c) `templates/base.html` 재작성(기존 1줄 인라인 CSS 제거 + `<meta name="viewport">` + `<link rel="stylesheet" href="/static/style.css">` + `<header class="gnb">` GNB 4 메뉴 마크업), (d) `tests/test_web_app.py`에 4 케이스 추가. 모바일은 햄버거 메뉴 대신 **가로 스크롤 탭바**로 대체(PRD §13 "JS 없이 동작" strict 준수). active 강조 컨텍스트 주입은 T-019C로 분리(라우트 5+ 곳 일괄 수정 비용 분산). 컴포넌트 클래스 부착(`feeds.html`/`list.html`/`magazine.html`)은 T-019B·C 책임 — 본 슬라이스는 CSS 정의 + GNB + 골격까지.

- **acceptance:**

  - **`src/rss_wiki/web/static/style.css` 신규** — 디자인 토큰 5축(컬러/간격/폰트/라운드/섀도우) + 라이트/다크 자동 + 반응형 + GNB + 카드/배지/버튼/폼 기본 컴포넌트. 약 200~300줄. **반드시 포함되어야 하는 마커**(테스트 검증): `:root`, `--color-bg`, `@media (prefers-color-scheme: dark)`, `.gnb`. 토큰 항목:
    - **컬러**: `--color-bg`/`--color-surface`/`--color-text`/`--color-text-muted`/`--color-border`/`--color-accent`/`--color-accent-hover`/`--color-success`/`--color-danger` (라이트/다크 두 세트).
    - **간격**: `--space-1`~`--space-8` (4/8/12/16/24/32/48/64 px).
    - **폰트**: `--font-sans`(시스템 폰트 스택), `--font-mono`(SFMono-Regular 등), `--text-sm`/`--text-base`/`--text-lg`/`--text-xl`/`--text-2xl`.
    - **라운드**: `--radius-sm`/`--radius-md`/`--radius-lg` (4/8/12 px).
    - **섀도우**: `--shadow-sm`/`--shadow-md` (라이트/다크 두 세트).
    - **컴포넌트**: `.gnb`/`.gnb-brand`/`.gnb-nav` + `.gnb-nav a.active`(active 클래스 정의), `.container`(`max-width: 720px`), `.card`(surface bg + border + shadow), `.badge`/`.badge-success`/`.badge-danger`, `.btn`/`.btn-primary`/`.btn-danger`, `<input type="text">`/`<input type="url">` 폼 스타일 + `:focus` outline, `<table>` 기본 스타일.
    - **반응형**: `@media (max-width: 768px)` 블록에서 `.gnb` 패딩 축소 + `.gnb-nav` `overflow-x: auto` + `-webkit-overflow-scrolling: touch` (가로 스크롤 탭바).
    - **다크모드**: `@media (prefers-color-scheme: dark)` 블록에서 `:root` 변수 재정의(라이트 변수 키 동일).
    - 자체 결정: CSS 빌드 도구(Tailwind/PostCSS) 미도입(PRD §13 "빌드 단계 없이" strict). vendor prefix는 최소(`-webkit-overflow-scrolling`만 — iOS 모멘텀 스크롤).
    - 자체 결정: 본 슬라이스는 토큰·GNB·컴포넌트 클래스 정의까지. `feeds.html`/`list.html`/`magazine.html`에서 클래스 부착은 T-019B·C 책임. 본 슬라이스 CSS는 클래스 미부착 상태에서도 기본 타이포그래피·여백이 자연스럽게 보이도록 `body`/`a`/`label`/`input`/`table` 등 element 스타일도 포함.

  - **`src/rss_wiki/web/app.py` 수정** — `from fastapi.staticfiles import StaticFiles` import 1 줄 추가, `create_app` 내부 `app.include_router(...)` 호출 직후 다음 1줄 추가:

    ```python
    app.mount(
        "/static",
        StaticFiles(directory=Path(__file__).parent / "static"),
        name="static",
    )
    ```

    - 자체 결정: `app.state` 갱신 미필요(StaticFiles 인스턴스 자체 폐쇄). `name="static"`은 `request.url_for("static", path="...")` 가능성을 위해 등록(현재는 `<link href="/static/style.css">` 정적 경로로 충분).
    - 자체 결정: `create_app` 시그니처/lifespan/healthz 미변경 — 회귀 surface 최소화.

  - **`src/rss_wiki/web/templates/base.html` 재작성** — 기존 1줄 인라인 `<style>` 제거 + viewport meta + 외부 stylesheet link + GNB 마크업으로 교체. `{% block title %}`/`{% block content %}` 슬롯은 그대로 유지(다른 템플릿 영향 0).

    ```html
    <!doctype html>
    <html lang="ko">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{% block title %}RSS Wiki{% endblock %}</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <header class="gnb">
            <a class="gnb-brand" href="/">RSS Wiki</a>
            <nav class="gnb-nav">
                <a href="/magazines"{% if active_nav == "magazines" %} class="active"{% endif %}>매거진</a>
                <a href="/categories"{% if active_nav == "categories" %} class="active"{% endif %}>카테고리</a>
                <a href="/tags"{% if active_nav == "tags" %} class="active"{% endif %}>태그</a>
                <a href="/feeds"{% if active_nav == "feeds" %} class="active"{% endif %}>피드 관리</a>
            </nav>
        </header>
        <main class="container">{% block content %}{% endblock %}</main>
    </body>
    </html>
    ```

    - 자체 결정: `active_nav` 컨텍스트는 본 슬라이스에서 라우트 핸들러 미주입 → Jinja2 default(undefined → falsy) 동작으로 active 미강조 상태가 노출됨. T-019C에서 라우트 5+ 곳 일괄 갱신.
    - 자체 결정: `<main class="container">`로 본문 폭(720px) 제한 + 반응형 패딩.
    - 자체 결정: `<header class="gnb">`는 `position: sticky`로 스크롤 시에도 GNB 고정(PRD §13 "모든 페이지에 고정 배치").

  - **`tests/test_web_app.py` 수정** — 4 케이스 추가. 픽스처는 기존 `with TestClient(create_app(tmp_db)) as client:` 컨텍스트 패턴 일관.

    1. `test_static_style_css_served(tmp_path)` — `client.get("/static/style.css")` → `assert resp.status_code == 200`. `assert resp.headers["content-type"].startswith("text/css")`. `body = resp.text`. `assert ":root" in body and "--color-bg" in body and "@media (prefers-color-scheme: dark)" in body and ".gnb" in body`. — 디자인 토큰 + 다크모드 + GNB 컴포넌트 4 마커 검증.
    2. `test_base_html_includes_stylesheet_link(tmp_path)` — `client.get("/")` → `assert resp.status_code == 200`. `assert '<link rel="stylesheet" href="/static/style.css">' in resp.text`. — 외부 CSS 연결 검증.
    3. `test_base_html_renders_gnb_with_four_links(tmp_path)` — `client.get("/")` → 본문에 `class="gnb"` + 4 텍스트(`매거진`/`카테고리`/`태그`/`피드 관리`) + 4 href(`href="/magazines"`/`href="/categories"`/`href="/tags"`/`href="/feeds"`) 모두 포함. — GNB 마크업 검증.
    4. `test_base_html_includes_viewport_meta(tmp_path)` — `client.get("/")` → `'<meta name="viewport"' in resp.text`. — 반응형 동작 메타 검증.
    - 자체 결정: 5번째 회귀 케이스(`/healthz`/`/magazines`/`/feeds` 200) 미추가 — 기존 테스트가 이미 200을 검증하므로 중복.
    - 자체 결정: 다크모드 자동 검증은 CSS 본문 `@media (prefers-color-scheme: dark)` 마커 1개로 충분 — 실제 색상 스왑은 브라우저 동작이라 단위 테스트 범위 외.
    - 자체 결정: 모바일 가로 스크롤 동작 검증은 CSS `.gnb-nav` `overflow-x: auto` 마커 추가 검증 안 함(테스트 비중 균형).

  - **회귀:** 기존 196 케이스 회귀 0(196/196 PASS 유지). 신규 4 케이스 → 합계 **200/200 PASS** 목표.

- **모듈 경계(엄수):**
  - 변경 파일: `src/rss_wiki/web/app.py`(수정 — import 1줄 + `app.mount(...)` 1줄, 합계 2줄 추가), `src/rss_wiki/web/static/style.css`(신규 약 200~300줄), `src/rss_wiki/web/templates/base.html`(수정 — 기존 12줄 본문을 18줄 내외로 교체), `tests/test_web_app.py`(수정 — 4 케이스 추가) — 합계 4개.
  - 변경 금지: `src/rss_wiki/{config,cli,main}.py`, `src/rss_wiki/{ingest,llm,publish,pipeline,storage}/*.py`, `src/rss_wiki/web/{__init__.py,markdown.py,routes_magazines.py,routes_feeds.py}`, `src/rss_wiki/web/templates/{feeds,feed_edit,list,magazine}.html`(컴포넌트 클래스 부착은 T-019B·C 책임), `pyproject.toml`(의존성 미추가), `feeds.toml`, `feeds.example.toml`, `README.md`(GNB·UI는 시각적 변경, 운영 안내 추가는 T-019B 플래시 메시지 시점에 검토), `output/*`, `data/*`.
  - 신규 외부 의존성 미추가: `fastapi.staticfiles.StaticFiles`는 fastapi 본체에 동봉, 별도 패키지 미필요.

- **touch:**
  - `src/rss_wiki/web/app.py` (수정 — 2줄 추가)
  - `src/rss_wiki/web/static/style.css` (신규 — 약 200~300줄)
  - `src/rss_wiki/web/templates/base.html` (수정 — 18줄 내외로 교체)
  - `tests/test_web_app.py` (수정 — 4 케이스 추가)

- **참고:**
  - PRD §13 UI/UX 요구사항(2026-05-05 갱신) — "모던한 디자인 / 디자인 토큰 단일 CSS 파일 / 라이트·다크 자동 / 카드·리스트·배지·버튼·폼 공통 / 본문 ~720px / 반응형 / 상단 GNB(매거진·카테고리·태그·피드 관리) / 모바일 햄버거 또는 가로 스크롤 탭바 / 토스트·배너 플래시(JS 없이)". 본 슬라이스는 토대(토큰·CSS·StaticFiles·base.html GNB) 마련 + 컴포넌트 정의. 컴포넌트 클래스 부착·플래시 메시지·`/feeds/new`·URL 수정 허용·`/tags` 인덱스는 T-019B·T-019C에서 처리.
  - PRD §13 "JS 없이 동작" — 햄버거 메뉴는 JS 의존(클릭 토글)이라 가로 스크롤 탭바로 대체. 자체 결정 기록(PLAN.md M8 T-019A 자체 결정 #14).
  - **DONE 발행 조건**: T-019A·B·C 3 슬라이스 모두 PASS 후 PRD §13 신규 요구가 코드/문서/테스트에 반영됐음을 다음 사이클 Planner가 점검 → `docs/DONE` 발행. T-019A 단독 PASS는 DONE 조건 미충족.

---

### [x] T-018G CLI `rss-wiki web` 서브커맨드 + README 웹 인터페이스 섹션 — M7 마지막 슬라이스 (PASS 196/196, 2026-05-05)
- **목표:** PRD §13 "실행" 섹션을 충족하는 CLI 진입점을 추가하고 운영 안내를 README에 정리한다. (a) `cli.py`에 `import uvicorn` + `from rss_wiki.web.app import create_app` 추가, (b) `cli.run_web` 결선 함수 신설(`run_uvicorn` 콜러블 주입 패턴 — M3·M4 일관), (c) `argparse`에 `web` 서브커맨드 추가(`--host` 기본 `127.0.0.1`, `--port` 기본 `8765`), (d) `cli.main`의 `web` 분기에서 `run_web` 호출 + 반환값 전달, (e) `README.md`에 §7 "웹 인터페이스" 신설(기존 §7~9 시프트, 트러블슈팅 1 항목 추가), (f) `tests/test_cli.py`에 4 케이스 추가. PRD §13 "기본 바인딩 `127.0.0.1`" + "개인용·로컬 전용, 인증 없음" strict 준수. uvicorn은 인스턴스 직접 전달(`uvicorn.run(create_app(db_path), ...)`)로 `--db` 옵션 정합.

- **acceptance:**
  - **`src/rss_wiki/cli.py` 수정** — 모듈 상단 import 추가 + `run_web` 결선 함수 신설 + argparse `web` 서브커맨드 + main 분기.
    ```python
    # 기존 import 블록에 추가
    import uvicorn
    from rss_wiki.web.app import create_app


    # 기존 run_monthly 다음에 append
    def run_web(
        *,
        db_path: Path,
        host: str,
        port: int,
        run_uvicorn: Callable[..., None] | None = None,
        logger: logging.Logger | None = None,
    ) -> int:
        _logger = logger or logging.getLogger(__name__)
        _logger.info("starting web server on %s:%d (db=%s)", host, port, db_path)
        runner = run_uvicorn or uvicorn.run
        runner(create_app(db_path), host=host, port=port, log_level="info")
        return 0


    # cli.main의 sub.add_parser 블록에 추가
    p_web = sub.add_parser("web", help="로컬 웹 인터페이스 실행")
    p_web.add_argument("--host", default="127.0.0.1", help="바인딩 호스트")
    p_web.add_argument("--port", type=int, default=8765, help="바인딩 포트")

    # cli.main의 분기 블록에 추가(elif args.cmd == "monthly": 다음에)
    elif args.cmd == "web":
        return run_web(db_path=db_path, host=args.host, port=args.port, logger=logger)
    ```
    - 자체 결정: `import uvicorn`은 모듈 레벨(테스트에서 `monkeypatch.setattr(rss_wiki.cli, "uvicorn", ...)` 또는 `run_uvicorn` 주입으로 격리). `run_uvicorn` 콜러블 주입 패턴(M3·M4 일관) — 단위 테스트 비의존.
    - 자체 결정: `init_db(db_path)` 중복 호출 회피하지 않음 — `cli.main` 공통 흐름의 `init_db` + `create_app(db_path, run_init_db=True)`(기본값) lifespan 호출은 모두 멱등, 일관성 우선. `conn = get_connection(db_path)` 후 `try`/`finally close`도 그대로(다른 분기 패턴 일관, web 분기에서는 conn 비사용이지만 부작용 없음).
    - 자체 결정: uvicorn 자체 예외(포트 점유 `OSError` 등)는 캐치하지 않고 traceback 전파(M6 인터페이스 원칙 — 인프라 예외는 운영자가 즉시 인지).
    - 자체 결정: `uvicorn.run(...)`은 인스턴스 직접 전달(import 문자열 `"rss_wiki.web.app:app"` 미사용) — `--db` 옵션이 명시되면 해당 경로의 SQLite를 사용하도록 보장. reload/workers 미지원이지만 PRD §13 단일 프로세스 운영 strict.
  - **`README.md` 수정** — 기존 §7(자동화 등록)을 §8로, §8(트러블슈팅)을 §9로, §9(디렉터리 구조)를 §10으로 시프트. 새 §7 "웹 인터페이스" 신설(약 50~80줄). 트러블슈팅에 "포트 점유" 항목 1개 추가.
    ```markdown
    ## 7. 웹 인터페이스

    매거진/인덱스 열람과 피드 관리(추가·수정·삭제·토글·실패 리셋)를 위한 로컬 FastAPI 웹 UI를 제공합니다 (PRD §13).

    ### 시작

    ```bash
    rss-wiki web
    ```

    - 기본 바인딩: `http://127.0.0.1:8765`
    - 브라우저에서 위 주소를 열면 매거진 인덱스가 나타납니다.

    ### 호스트/포트 변경

    ```bash
    rss-wiki web --host 127.0.0.1 --port 9000
    ```

    | 옵션 | 기본값 | 설명 |
    |------|--------|------|
    | `--host` | `127.0.0.1` | 바인딩 호스트 |
    | `--port` | `8765` | 바인딩 포트 |

    ### 보안 경고

    - 본 도구는 **개인용·로컬 전용**입니다. 인증·CSRF 보호가 없으므로 외부 노출(`0.0.0.0`/공인 IP 바인딩, 리버스 프록시 노출 등)은 PRD §13 범위 외이며 권장하지 않습니다.
    - 다중 사용자, 외부 트래픽이 필요한 경우 별도의 인증 레이어를 운영자가 직접 구성해야 합니다.

    ### 라우트 요약

    | 경로 | 용도 |
    |------|------|
    | `GET /` | 최근 매거진 목록 |
    | `GET /magazines` | 일간/주간/월간 매거진 인덱스 |
    | `GET /magazines/{id}` | 매거진 단건(마크다운 → HTML) |
    | `GET /categories` | 카테고리 인덱스 |
    | `GET /categories/{name}` | 카테고리별 글 목록 |
    | `GET /tags/{name}` | 태그별 글 목록 |
    | `GET /feeds` | 피드 목록(관리 UI) |
    | `POST /feeds` | 피드 추가 |
    | `GET /feeds/{id}/edit` | 피드 수정 폼 |
    | `POST /feeds/{id}` | 피드 수정 적용 |
    | `POST /feeds/{id}/delete` | 피드 삭제(스냅샷 보존) |
    | `POST /feeds/{id}/toggle` | 활성/비활성 토글 |
    | `POST /feeds/{id}/reset` | 연속 실패 카운트 리셋 |
    | `GET /healthz` | 헬스체크 |

    ### 동시 실행

    - `rss-wiki daily`(수집·발행 파이프라인)와 `rss-wiki web`은 **별도 프로세스**로 동시에 실행 가능합니다.
    - SQLite는 WAL 모드로 활성화되어 있어 한쪽이 쓰는 동안 다른 쪽이 읽을 수 있습니다.
    ```

    트러블슈팅에 포트 점유 항목 1개 추가:

    ```markdown
    ### 포트 점유

    `rss-wiki web` 실행 시 `OSError: [Errno 48] Address already in use` 오류가 나오면 다른 프로세스가 같은 포트를 사용 중입니다. 다른 포트로 재실행하세요:

    ```bash
    rss-wiki web --port 8766
    ```
    ```
    - 자체 결정: 섹션 번호 시프트는 단순 마크다운 헤더 변경(목차/외부 링크 미존재). 기존 콘텐츠는 보존, 헤더 번호만 +1.
    - 자체 결정: PRD §13 라우트 표를 압축본으로 README에 재게시 — 운영자가 PRD를 별도 열지 않고도 라우트 개요 파악 가능. 상세 동작은 PRD §13 참조 안내 1줄 포함.
    - 자체 결정: 한국어 작성(README 일관). 약 50~80줄 추가. 트러블슈팅 1 항목.
  - **`tests/test_cli.py` 수정** — 4 케이스 추가. 픽스처는 기존 `_setup_db` 재사용. uvicorn 호출 격리는 (a) `run_web`에 `run_uvicorn=fake` 직접 주입, (b) `cli.main` 진입점은 `monkeypatch.setattr(rss_wiki.cli.uvicorn, "run", fake)` 패턴.
    1. `test_run_web_invokes_uvicorn_with_create_app(tmp_path)` — `db_path = tmp_path / "x.db"; init_db(db_path)`. `captured: list[tuple] = []`. `def fake(app, **kw): captured.append((app, kw))`. `rc = run_web(db_path=db_path, host="127.0.0.1", port=8765, run_uvicorn=fake)`. `assert rc == 0`. `assert len(captured) == 1`. `(app, kw) = captured[0]`. `assert kw["host"] == "127.0.0.1"`. `assert kw["port"] == 8765`. `assert kw["log_level"] == "info"`. `from fastapi import FastAPI; assert isinstance(app, FastAPI)`.
    2. `test_run_web_passes_custom_host_port(tmp_path)` — `run_web(db_path=db_path, host="0.0.0.0", port=9000, run_uvicorn=fake)` → `kw["host"] == "0.0.0.0"`, `kw["port"] == 9000`.
    3. `test_main_web_subcommand_routes_to_run_web(tmp_path, monkeypatch)` — `db_path = tmp_path / "x.db"`. `captured = []`. `def fake(app, **kw): captured.append((app, kw))`. `monkeypatch.setattr(rss_wiki.cli.uvicorn, "run", fake)`. `rc = main(["--db", str(db_path), "web"])`. `assert rc == 0`. `assert len(captured) == 1`. `assert captured[0][1]["host"] == "127.0.0.1"`. `assert captured[0][1]["port"] == 8765`.
    4. `test_main_web_subcommand_honors_host_port_args(tmp_path, monkeypatch)` — 동일 픽스처. `main(["--db", str(db_path), "web", "--host", "0.0.0.0", "--port", "9000"])` → `captured[0][1]["host"] == "0.0.0.0"`, `captured[0][1]["port"] == 9000`.
    - 픽스처 패턴: 기존 `_setup_db(tmp_path)` 미재사용(web 분기는 conn 비사용) — `db_path = tmp_path / "x.db"; init_db(db_path)`만으로 충분. main 진입점 테스트는 `cli.main`이 자체적으로 `init_db`를 호출하므로 사전 init_db 호출 불필요(테스트 단순화).
    - 자체 결정: 실제 uvicorn 서버 기동·포트 바인딩·HTTP 트랜잭션 미수행(테스트 격리). FastAPI 앱 인스턴스 검증은 `isinstance(app, FastAPI)`로 단순 확인. 회귀 위험 낮은 표면(서브커맨드 라우팅 + 인자 전달).
    - 자체 결정: `monkeypatch.setattr(rss_wiki.cli.uvicorn, "run", fake)` 패턴 — `import uvicorn` 모듈 레벨 노출 덕분에 동작. 테스트 import에 `import rss_wiki.cli` 또는 `from rss_wiki import cli`가 이미 존재(test_cli.py:14).
  - **회귀:** 기존 192개 테스트 회귀 0(192/192 PASS 유지). 신규 4 케이스 → 합계 **196/196 PASS** 목표.

- **모듈 경계(엄수):**
  - 변경 파일: `src/rss_wiki/cli.py`(수정 — `import uvicorn` + `from rss_wiki.web.app import create_app` import 2 + `run_web` 결선 함수 추가 + `web` 서브커맨드 argparse + main 분기), `README.md`(수정 — §7 웹 인터페이스 신설 + 기존 §7~9 시프트 + 트러블슈팅 1 항목 추가), `tests/test_cli.py`(수정 — 4 케이스 추가) — 합계 3개.
  - 변경 금지: `src/rss_wiki/{config.py,main.py}`, `src/rss_wiki/{ingest,llm,publish,pipeline,storage}/*.py`, `src/rss_wiki/web/{__init__.py,app.py,markdown.py,routes_magazines.py,routes_feeds.py}`, `src/rss_wiki/web/templates/*.html`, `pyproject.toml`(이미 uvicorn/fastapi 등 모든 의존성 + `[project.scripts]` 등록 완료, T-018C·F·T-015I), `feeds.toml`, `feeds.example.toml`, `output/*`, `data/*`.
  - 신규 외부 의존성 미추가(uvicorn은 T-018C에서 이미 추가됨).

- **touch:**
  - `src/rss_wiki/cli.py` (수정 — import 2줄 + `run_web` 함수 + `web` 서브커맨드 + main 분기 elif 1개)
  - `README.md` (수정 — §7 웹 인터페이스 신설 + §7~9 시프트 + 트러블슈팅 포트 점유 항목 추가)
  - `tests/test_cli.py` (수정 — 4 케이스 추가)

- **참고:**
  - PRD §13 "실행" — `uvicorn rss_wiki.web:app --host 127.0.0.1 --port 8765` 또는 동등 CLI 서브커맨드(`rss-wiki web`). 본 슬라이스가 후자를 충족. 자체 결정: PRD 본문의 import 경로 표기(`rss_wiki.web:app`)는 변경하지 않음 — `rss-wiki web` CLI가 `from rss_wiki.web.app import create_app`로 우회 import하여 운영자 노출 면(README + CLI)에서 차이 없음.
  - PRD §13 "수집/발행 파이프라인과는 별도 프로세스. 동일 SQLite 파일을 공유하며 쓰기 충돌 방지를 위해 WAL 모드 사용" — README §7 동시 실행 안내로 반영. WAL 모드는 T-018C `web/app.py` lifespan에서 이미 활성화.
  - PRD §13 "기본 바인딩은 `127.0.0.1`로만 listen, 인증 없음" — `--host` 기본값 `127.0.0.1` + README 보안 경고 1단락으로 반영.
  - **DONE 발행 조건 사전 점검:** T-018G PASS 시 PRD 섹션별 반영 상태 — §1~12 M1~M6에서 모두 충족, §13 M7 9 슬라이스(T-018A~G)로 모두 충족. TASKS.md 모든 항목 `[x]` 완료. 따라서 다음 사이클 Planner가 PRD 전 섹션을 다시 점검한 후 `docs/DONE` 빈 파일 생성하여 종료 신호.

---

### [x] T-018F 피드 POST 라우트 5종 — M7 여덟 번째 슬라이스 (PASS 192/192, 2026-05-05)
- **목표:** PRD §13 웹 인터페이스의 피드 관리 흐름을 완성. (a) `pyproject.toml`에 `python-multipart` 1 의존성 추가(FastAPI `Form(...)` 의존성), (b) `routes_feeds.py`에 5 POST 라우트 추가(`POST /feeds`/`POST /feeds/{id}`/`POST /feeds/{id}/delete`/`POST /feeds/{id}/toggle`/`POST /feeds/{id}/reset`), 모두 처리 후 `RedirectResponse(url="/feeds", status_code=303)` 반환, (c) `feeds.html`에 추가 폼 1개(table 위) + 행별 토글/삭제/리셋 버튼 3개(별도 form) 추가, (d) `tests/test_web_app.py`에 8~9 케이스 추가. URL 정규화는 `ingest.dedupe.normalize_url` 재사용. UNIQUE 충돌은 기존 `upsert_feed`의 `INSERT OR IGNORE`로 silent 멱등 처리. 미존재 feed_id는 명시적 404. CSRF 미도입(PRD §13 strict — 개인용·로컬 전용).

- **acceptance:**
  - **`pyproject.toml` 수정** — `dependencies` 리스트에 `python-multipart` 한 줄 추가(상한·범위 미지정, 기존 의존성 표기와 일관). `uv sync` 또는 `uv lock` 후 의존성 설치 가능. 자체 결정: 추가 위치는 `markdown-it-py` 다음 줄(M7 의존성 그룹 일관).
    ```toml
    dependencies = [
        "feedparser",
        "httpx",
        "trafilatura",
        "fastapi",
        "uvicorn[standard]",
        "jinja2",
        "markdown-it-py",
        "python-multipart",
    ]
    ```
  - **`src/rss_wiki/web/routes_feeds.py` 수정** — 5 POST 라우트 추가. `Form`/`RedirectResponse` import 추가. `normalize_url` import 추가.
    ```python
    from __future__ import annotations

    import sqlite3

    from fastapi import APIRouter, Depends, Form, HTTPException, Request
    from fastapi.responses import HTMLResponse, RedirectResponse

    from rss_wiki.ingest.dedupe import normalize_url
    from rss_wiki.storage import repo
    from rss_wiki.web.app import get_db

    router = APIRouter()


    # ... 기존 GET 라우트 2개 유지 ...


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
        return RedirectResponse(url="/feeds", status_code=303)


    @router.post("/feeds/{feed_id}")
    def feed_update(
        feed_id: int,
        name: str = Form(...),
        enabled: str | None = Form(None),
        conn: sqlite3.Connection = Depends(get_db),
    ) -> RedirectResponse:
        feed = repo.get_feed_by_id(conn, feed_id)
        if feed is None:
            raise HTTPException(status_code=404, detail="feed not found")
        repo.update_feed(conn, feed_id, name=name.strip())
        repo.set_feed_enabled(conn, feed_id, bool(enabled))
        conn.commit()
        return RedirectResponse(url="/feeds", status_code=303)


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
    ```
    - 자체 결정: `POST /feeds`에서 `enabled` form 미수용 — 기본 활성으로 추가(`feeds.enabled` 컬럼 DEFAULT 1). 운영자가 추가 직후 비활성화하려면 토글로 처리(단순함 우선).
    - 자체 결정: 미존재 feed_id는 명시적 404(silent no-op 회피, 운영자 즉시 인지).
    - 자체 결정: `name` 입력은 `strip()` 적용 후 빈 문자열이면 정규화된 url 사용(추가 라우트만). 수정 라우트의 `name`은 required(필수 입력).
    - 자체 결정: URL 정규화는 `ingest.dedupe.normalize_url` 재사용 — M3 인터페이스 원칙 "URL 정규화 단일 진실 원천" 일관.
    - 자체 결정: 각 라우트 끝에 `conn.commit()` 호출(M7 인터페이스 원칙 — 쓰기 라우트만 commit).
  - **`src/rss_wiki/web/templates/feeds.html` 수정** — (1) 테이블 위에 추가 폼 1개, (2) 행별 마지막 컬럼에 토글/삭제/리셋 버튼 3 form 추가.
    ```html
    {% extends "base.html" %}
    {% block title %}피드 — RSS Wiki{% endblock %}
    {% block content %}
    <h2>피드</h2>

    <form method="post" action="/feeds">
        <p>
            <label>새 피드 URL
                <input type="url" name="url" required>
            </label>
            <label>이름(선택)
                <input type="text" name="name">
            </label>
            <button type="submit">추가</button>
        </p>
    </form>

    {% if feeds %}
    <table>
        <thead>
            <tr><th>이름</th><th>URL</th><th>활성</th><th>연속 실패</th><th>마지막 수집</th><th></th></tr>
        </thead>
        <tbody>
            {% for feed in feeds %}
            <tr>
                <td>{{ feed.name }}</td>
                <td><a href="{{ feed.url }}">{{ feed.url }}</a></td>
                <td>{% if feed.enabled %}활성{% else %}비활성{% endif %}</td>
                <td>{{ feed.consecutive_failures }}</td>
                <td>{{ feed.last_fetched_at or "—" }}</td>
                <td>
                    <a href="/feeds/{{ feed.id }}/edit">수정</a>
                    <form method="post" action="/feeds/{{ feed.id }}/toggle" style="display:inline">
                        <button type="submit">토글</button>
                    </form>
                    <form method="post" action="/feeds/{{ feed.id }}/reset" style="display:inline">
                        <button type="submit">실패 리셋</button>
                    </form>
                    <form method="post" action="/feeds/{{ feed.id }}/delete" style="display:inline" onsubmit="return confirm('삭제하시겠습니까?');">
                        <button type="submit">삭제</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p>아직 등록된 피드가 없습니다.</p>
    {% endif %}
    {% endblock %}
    ```
    - 자체 결정: `style="display:inline"`은 인라인 CSS 1줄(PRD §13 "최소한의 CSS만 인라인" strict). JS는 `confirm` 다이얼로그 1줄만 사용(브라우저 표준, 외부 JS 미도입).
    - 자체 결정: 추가 폼은 `enabled` 미포함(자체 결정 3 — 기본 활성 추가).
  - **`src/rss_wiki/web/templates/feed_edit.html` 변경 없음** — T-018E에서 `action="/feeds/{id}"`로 사전 작성 → 본 슬라이스에서 자동 활성화.
  - **`tests/test_web_app.py` 수정** — 8~9 케이스 추가. `TestClient`는 `follow_redirects=False`로 303 응답 직접 검증.
    1. `test_post_feeds_creates` — `client.post("/feeds", data={"url": "https://example.com/rss", "name": "Example"}, follow_redirects=False)` → 303 + `response.headers["location"] == "/feeds"` + `list_feeds(conn)` 1행(`url="https://example.com/rss"`, `name="Example"`).
    2. `test_post_feeds_normalizes_url` — `client.post("/feeds", data={"url": "https://example.com/rss?utm_source=x", "name": "Example"}, follow_redirects=False)` → 303 + DB `feeds.url == "https://example.com/rss"`(UTM 제거).
    3. `test_post_feeds_duplicate_url_idempotent` — 같은 url 두 번 POST → 둘 다 303 + DB 1행(멱등).
    4. `test_post_feeds_rejects_empty_url` — `client.post("/feeds", data={"url": " ", "name": "x"}, follow_redirects=False)` → 400.
    5. `test_post_feed_update` — `feed_id = upsert_feed(conn, "Old", "https://example.com/rss")` → `client.post(f"/feeds/{feed_id}", data={"name": "New", "enabled": "on"}, follow_redirects=False)` → 303 + `get_feed_by_id` 결과 `name="New"`, `enabled=1`.
    6. `test_post_feed_update_disables_when_unchecked` — `data={"name": "Same"}`(enabled 키 부재) → 303 + `enabled=0`.
    7. `test_post_feed_delete` — feed_id + `insert_article` 1행(연결) → POST `/feeds/{id}/delete` → 303 + `list_feeds(conn)` 빈 + articles 행 잔존 + `feed_id IS NULL` + `feed_url_snapshot` 채워짐.
    8. `test_post_feed_toggle` — enabled=1 feed_id → POST 한 번 → `enabled=0` + 303. 두 번째 POST → `enabled=1`(반전 검증).
    9. `test_post_feed_reset` — `record_feed_failure` 3회 → POST `/feeds/{id}/reset` → 303 + `consecutive_failures=0`.
    10. `test_post_feed_404_for_missing_id` — POST `/feeds/99999/delete` → 404. (toggle/reset/update의 404 코드 경로 동일이므로 1 케이스로 통합 커버 — 자체 결정)
    - 자체 결정: 합계 10 케이스(추가 4 + 수정 2 + 삭제 1 + 토글 1 + 리셋 1 + 404 1). PRD §13의 5 POST 라우트 동작과 핵심 에러(빈 url/미존재 id)를 균형있게 커버.
    - 픽스처: `with TestClient(create_app(tmp_db)) as client:` 컨텍스트 패턴 일관(T-018C/D/E와 동일). `client.post(..., follow_redirects=False)` 명시.
    - import 추가: `from rss_wiki.storage.repo import upsert_feed, set_feed_enabled, record_feed_failure, get_feed_by_id, list_feeds, insert_article`(T-018E에서 일부 이미 있을 수 있음 — 차이만 추가).
  - **회귀:** 기존 182개 테스트 회귀 0(182/182 PASS 유지). 신규 10 케이스 → 합계 **192/192 PASS** 목표.

- **모듈 경계(엄수):**
  - 변경 파일: `pyproject.toml`(수정 — `python-multipart` 1 의존성 추가), `src/rss_wiki/web/routes_feeds.py`(수정 — 5 POST 라우트 + 필요 import 추가), `src/rss_wiki/web/templates/feeds.html`(수정 — 추가 폼 + 행별 3 버튼 form), `tests/test_web_app.py`(수정 — 10 케이스 추가) — 합계 4개.
  - 변경 금지: `src/rss_wiki/{config,cli,main}.py`, `src/rss_wiki/{ingest,llm,publish,pipeline}/*.py`(`ingest.dedupe.normalize_url`는 import만, 코드 변경 없음), `src/rss_wiki/storage/{schema.sql,db.py,repo.py}`(repo는 본 슬라이스에서 신규 함수 미추가 — `upsert_feed`/`update_feed`/`set_feed_enabled`/`reset_feed_failures`/`delete_feed`/`get_feed_by_id` 모두 기존 도입 완료), `src/rss_wiki/web/{__init__.py,app.py,markdown.py,routes_magazines.py}`(`include_router(feeds_router)`는 T-018E에서 이미 호출 — POST 5 라우트 자동 노출), `src/rss_wiki/web/templates/{base,list,magazine,feed_edit}.html`, `feeds.toml`, `feeds.example.toml`, `README.md`(T-018G 책임).
  - CLI `rss-wiki web` 서브커맨드(T-018G), README §13 운영 안내(T-018G)는 본 슬라이스 범위 외.

- **touch:**
  - `pyproject.toml` (수정 — `python-multipart` 의존성 1줄 추가)
  - `src/rss_wiki/web/routes_feeds.py` (수정 — 5 POST 라우트 + Form/RedirectResponse/normalize_url import 추가)
  - `src/rss_wiki/web/templates/feeds.html` (수정 — 추가 폼 1개 + 행별 토글/리셋/삭제 3 form 버튼)
  - `tests/test_web_app.py` (수정 — 10 케이스 추가 + repo import 확장)

- **참고:**
  - PRD §13 라우트 표 — `POST /feeds`(추가), `POST /feeds/{id}`(수정), `POST /feeds/{id}/delete`, `POST /feeds/{id}/toggle`, `POST /feeds/{id}/reset` 5종. 본 슬라이스가 모두 충족.
  - PRD §13 "모든 변경 라우트는 처리 후 `303 See Other`로 목록 페이지로 리다이렉트" — 5 라우트 모두 `RedirectResponse(url="/feeds", status_code=303)` 반환.
  - PRD §13 "url 변경은 사실상 다른 피드이므로 삭제 후 재추가로 안내" — 수정 라우트는 `name`/`enabled`만 처리, url 미수정. T-018E에서 `feed_edit.html`에 안내 문구 이미 포함.
  - PRD §13 "활성/비활성 토글: enabled=false 피드는 수집 사이클 스킵, 카운터는 유지" — `set_feed_enabled`만 호출(`consecutive_failures` 미터치) → 카운터 보존.
  - PRD §13 "삭제: 소프트 삭제 없이 하드 삭제. 단, 이미 수집·발행된 글은 그대로 유지" — `repo.delete_feed`(T-018B2)가 스냅샷 + feed_id NULL + DELETE feeds 3 SQL로 PRD 의도 충족.
  - 후속 슬라이스 T-018G — CLI `rss-wiki web` 서브커맨드 + uvicorn 실행(`127.0.0.1:8765` 기본) + README §13 운영 안내. M7 마지막 슬라이스. 본 슬라이스 PASS 후 활성화.

### [x] T-018E 피드 GET 라우트 + `routes_feeds.py` 신설 — M7 일곱 번째 슬라이스 (PASS 182/182, 2026-05-05)
- **목표:** PRD §13 웹 인터페이스의 피드 관리 흐름 토대를 마련. (a) `src/rss_wiki/web/routes_feeds.py` 신규 모듈(APIRouter 기반), (b) `GET /feeds` 피드 목록 페이지 + `GET /feeds/{feed_id}/edit` 수정 폼 2 라우트 추가, (c) `templates/feeds.html` + `templates/feed_edit.html` 2 템플릿 신설, (d) `repo.get_feed_by_id` 1 함수 추가(M2 패턴 thin lookup), (e) `web/app.py`에 `include_router(feeds_router)` 1 줄 추가. POST 라우트 5종(추가/수정/삭제/토글/리셋)은 T-018F 책임이며 본 슬라이스 범위 외.

- **acceptance:**
  - **`src/rss_wiki/storage/repo.py` 수정** — `get_feed_by_id` 1 함수 추가(파일 끝 또는 `get_feed_by_url` 다음에 append). M2 패턴 일관.
    ```python
    def get_feed_by_id(
        conn: sqlite3.Connection, feed_id: int
    ) -> sqlite3.Row | None:
        return conn.execute(
            "SELECT * FROM feeds WHERE id = ?", (feed_id,)
        ).fetchone()
    ```
  - **`src/rss_wiki/web/routes_feeds.py` 신규** — APIRouter 기반 2 라우트. `Depends(get_db)`는 `from rss_wiki.web.app import get_db`로 import 재사용(magazines 라우트와 동일).
    ```python
    from __future__ import annotations

    import sqlite3

    from fastapi import APIRouter, Depends, HTTPException, Request
    from fastapi.responses import HTMLResponse

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
            request, "feeds.html", {"feeds": feeds}
        )


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
            request, "feed_edit.html", {"feed": feed}
        )
    ```
    - 자체 결정: `enabled_only=False`(전체 표시 — 비활성 피드도 운영자가 토글로 켤 수 있도록 노출).
    - 자체 결정: 정렬은 `list_feeds` 기본(`id ASC`) 그대로 — 부트스트랩 순서 유지.
  - **`src/rss_wiki/web/templates/feeds.html` 신규** — 피드 목록 템플릿(다중 컬럼이라 `list.html` 미재사용).
    ```html
    {% extends "base.html" %}
    {% block title %}피드 — RSS Wiki{% endblock %}
    {% block content %}
    <h2>피드</h2>
    {% if feeds %}
    <table>
        <thead>
            <tr><th>이름</th><th>URL</th><th>활성</th><th>연속 실패</th><th>마지막 수집</th><th></th></tr>
        </thead>
        <tbody>
            {% for feed in feeds %}
            <tr>
                <td>{{ feed.name }}</td>
                <td><a href="{{ feed.url }}">{{ feed.url }}</a></td>
                <td>{% if feed.enabled %}활성{% else %}비활성{% endif %}</td>
                <td>{{ feed.consecutive_failures }}</td>
                <td>{{ feed.last_fetched_at or "—" }}</td>
                <td><a href="/feeds/{{ feed.id }}/edit">수정</a></td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p>아직 등록된 피드가 없습니다.</p>
    {% endif %}
    {% endblock %}
    ```
  - **`src/rss_wiki/web/templates/feed_edit.html` 신규** — 수정 폼 템플릿. `action`은 T-018F의 `POST /feeds/{id}` — 본 슬라이스 시점에는 405지만 템플릿 한 번에 작성(T-018F 후속).
    ```html
    {% extends "base.html" %}
    {% block title %}피드 수정 — RSS Wiki{% endblock %}
    {% block content %}
    <h2>피드 수정</h2>
    <form method="post" action="/feeds/{{ feed.id }}">
        <p>
            <label>이름
                <input type="text" name="name" value="{{ feed.name }}" required>
            </label>
        </p>
        <p>
            <label>URL (변경 불가 — 변경하려면 삭제 후 재추가)
                <input type="url" value="{{ feed.url }}" readonly>
            </label>
        </p>
        <p>
            <label>
                <input type="checkbox" name="enabled" {% if feed.enabled %}checked{% endif %}>
                활성
            </label>
        </p>
        <p>
            <button type="submit">저장</button>
            <a href="/feeds">취소</a>
        </p>
    </form>
    {% endblock %}
    ```
    - 자체 결정: `url` 필드는 `readonly`로 표시만 하고 form data 전송 미포함(name 속성 제거). PRD §13 "url 변경은 사실상 다른 피드이므로 삭제 후 재추가" 명시.
  - **`src/rss_wiki/web/app.py` 수정** — 2 줄 추가(import + include_router). 기존 magazines_router 패턴과 일관.
    ```python
    # 기존 import 블록에 추가
    from rss_wiki.web.routes_feeds import router as feeds_router  # noqa: E402

    # create_app 내 include_router 호출 다음 줄에 추가
    app.include_router(feeds_router)
    ```
    - 자체 결정: import 위치는 magazines_router와 동일 패턴(모듈 끝 import + `# noqa: E402`). create_app 시그니처/lifespan/healthz/get_db 미변경.
  - **`tests/test_web_app.py` 수정** — 4 케이스 추가. 필요 시 import 확장(`set_feed_enabled` 등). 픽스처 패턴(`with TestClient(create_app(tmp_db)) as client:`) 일관.
    1. `test_feeds_index_empty` — feeds 0건 → `client.get("/feeds")` → 200 + `"피드" in response.text` + `"아직 등록된 피드가 없습니다" in response.text`.
    2. `test_feeds_index_with_entries` — `upsert_feed(conn, "Google News", "https://news.google.com/rss")` + `upsert_feed(conn, "HN", "https://news.ycombinator.com/rss")` → 200 + 두 피드 name + url 본문 포함 + `'href="/feeds/' in response.text`(또는 `/edit` 링크 검증).
    3. `test_feed_edit_form_renders` — `feed_id = upsert_feed(conn, "Google News", "https://news.google.com/rss")` + `set_feed_enabled(conn, feed_id, False)` → `client.get(f"/feeds/{feed_id}/edit")` → 200 + `"Google News" in response.text` + `"https://news.google.com/rss" in response.text` + `'action="/feeds/' in response.text`.
    4. `test_feed_edit_404_for_missing_id` — `client.get("/feeds/99999/edit")` → 404.
    - 자체 결정: enabled checkbox checked/unchecked 상태 검증은 생략(텍스트 매칭으로 정확히 잡기 어려움 — Jinja2 출력 형태 의존). T-018F의 POST 토글 테스트가 동작 검증 충분히 커버.
    - 자체 결정: `consecutive_failures`/`last_fetched_at` 표시 검증 생략 — 라우트 동작 핵심은 name/url/edit 링크 + 404, 부수 컬럼은 회귀 위험 낮음.
  - **회귀:** 기존 178개 테스트 회귀 0(178/178 PASS 유지). 신규 4 케이스 → 합계 **182/182 PASS** 목표.

- **모듈 경계(엄수):**
  - 변경 파일: `src/rss_wiki/storage/repo.py`(수정 — `get_feed_by_id` 1 함수), `src/rss_wiki/web/app.py`(수정 — import 1 + include_router 1, 합계 2 줄), `src/rss_wiki/web/routes_feeds.py`(신규), `src/rss_wiki/web/templates/feeds.html`(신규), `src/rss_wiki/web/templates/feed_edit.html`(신규), `tests/test_web_app.py`(수정 — 4 케이스 추가) — 합계 6개.
  - 변경 금지: `src/rss_wiki/{config,cli,main}.py`, `src/rss_wiki/{ingest,llm,publish,pipeline}/*.py`, `src/rss_wiki/storage/{schema.sql,db.py}`, `src/rss_wiki/web/{__init__.py,markdown.py,routes_magazines.py}`, `src/rss_wiki/web/templates/{base,list,magazine}.html`, `feeds.toml`, `feeds.example.toml`, `pyproject.toml`(의존성 미추가), `README.md`.
  - 신규 외부 의존성 미추가(`python-multipart`는 T-018F 책임).
  - POST 라우트 5종(추가/수정/삭제/토글/리셋), CLI `web` 서브커맨드(T-018G)는 본 슬라이스 범위 외.

- **touch:**
  - `src/rss_wiki/storage/repo.py` (수정 — `get_feed_by_id` 1 함수 추가)
  - `src/rss_wiki/web/routes_feeds.py` (신규 — APIRouter + `feeds_index` + `feed_edit_form` 2 라우트)
  - `src/rss_wiki/web/templates/feeds.html` (신규 — 다중 컬럼 테이블)
  - `src/rss_wiki/web/templates/feed_edit.html` (신규 — 수정 폼)
  - `src/rss_wiki/web/app.py` (수정 — import 1 + include_router 1)
  - `tests/test_web_app.py` (수정 — 4 케이스 + import 확장)

- **참고:**
  - PRD §13 라우트 표 — `GET /feeds` 피드 목록, `GET /feeds/{id}/edit` 수정 폼. 본 슬라이스가 2 라우트 모두 충족.
  - PRD §13 "url 변경은 사실상 다른 피드이므로 삭제 후 재추가로 안내" — `feed_edit.html`의 url 필드 readonly + 안내 문구 1줄로 반영.
  - PRD §13 "feeds 컬럼" — name/url/enabled/consecutive_failures/last_fetched_at 모두 `feeds.html` 테이블에 노출.
  - 후속 슬라이스 T-018F — POST 라우트 5종(`POST /feeds`/`POST /feeds/{id}`/`POST /feeds/{id}/delete`/`POST /feeds/{id}/toggle`/`POST /feeds/{id}/reset`) + `python-multipart` 의존성 추가 + 303 리다이렉트. 본 슬라이스 PASS 후 활성화.

### [x] T-018D2 카테고리/태그 GET 라우트 — M7 여섯 번째 슬라이스 (PASS 178/178, 2026-05-05)
- **목표:** PRD §13 웹 인터페이스의 카테고리/태그 탐색 흐름을 구축. (a) `routes_magazines.py` 확장(별도 모듈 분리하지 않음, 자체 결정 — 라우트 6개로 단일 모듈 유지 가능, YAGNI), (b) `GET /categories` 카테고리 인덱스 + `GET /categories/{name}` 글 목록 + `GET /tags/{name}` 글 목록 3 라우트 추가, (c) 기존 `templates/list.html` 재사용(`heading` + `items=[{title, href, subtitle?}]` 표준 컨텍스트 그대로), (d) `repo.get_category_by_name`/`repo.get_tag_by_name` 2 함수 추가(이름→Row 정규화 lookup, 자체 결정 — PLAN 메모 "repo 변경 미필요"를 본 슬라이스 진입 시 갱신: 이름 정규화 책임을 storage에 두기 위해 thin lookup 헬퍼 도입), (e) `tests/test_web_app.py`에 5 케이스 추가. 카테고리는 PRD §13 표대로 `/categories` 인덱스 + `/categories/{name}` 단건만 제공, 태그는 PRD §13 표대로 `/tags/{name}`만 제공(`/tags` 인덱스 라우트 미도입 — PRD strict).

- **acceptance:**
  - **`src/rss_wiki/storage/repo.py` 수정** — 2 함수 추가(파일 끝 또는 `list_tags` 다음에 append). 자체 결정: M2 패턴 일관 — `Connection` 첫 인자, `commit` 미수행, `Row | None` 반환. 이름 정규화는 storage 레이어 책임(PRD §6/§12.1, M2 패턴 일관) — `name.strip().lower()`로 입력 정규화 후 `WHERE name = ?` 조회. 호출자(라우트)는 정규화 미신경.
    ```python
    def get_category_by_name(
        conn: sqlite3.Connection, name: str
    ) -> sqlite3.Row | None:
        normalized = name.strip().lower()
        return conn.execute(
            "SELECT id, name FROM categories WHERE name = ?", (normalized,)
        ).fetchone()


    def get_tag_by_name(
        conn: sqlite3.Connection, name: str
    ) -> sqlite3.Row | None:
        normalized = name.strip().lower()
        return conn.execute(
            "SELECT id, name FROM tags WHERE name = ?", (normalized,)
        ).fetchone()
    ```
  - **`src/rss_wiki/web/routes_magazines.py` 수정** — 3 라우트 추가(파일 끝에 append). 기존 `_magazine_items` 헬퍼 패턴을 따라 `_category_items`/`_tag_items`/`_article_items` 비공개 헬퍼 신설. 자체 결정: 라우트 모듈 분리 미수행(라우트 6개 → 단일 모듈로 충분). T-018E·F에서 `routes_feeds.py` 신설 시 그쪽이 별도 모듈이 됨.
    ```python
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
            {"heading": "카테고리", "items": _category_items(rows)},
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
            },
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
            },
        )
    ```
    - 자체 결정: 글 목록의 `href`는 글의 원문 URL(`articles.url`)을 그대로 사용 — 별도 글 상세 라우트 미도입(PRD §13 라우트 표에 글 상세 라우트 없음). 운영자는 외부 원문으로 직접 이동.
    - 자체 결정: 글 카드 `title`은 `articles.title`이 NULL/빈 문자열인 경우 `articles.url`로 폴백(빈 링크 텍스트 방지).
    - 자체 결정: `/categories`만 인덱스 제공(PRD §13 표 충족). `/tags` 인덱스는 PRD에 미정의이므로 미도입 — `/categories/{name}` 글 카드에서 글의 카테고리/태그를 보여주는 흐름은 후속 사이클 검토(YAGNI).
    - `Depends(get_db)`는 T-018D에서 이미 정의된 import 경로 재사용. import 추가 불필요(이미 존재하는 `from rss_wiki.web.app import get_db`).
  - **`src/rss_wiki/web/app.py` 변경 없음** — `include_router(magazines_router)`만 이미 호출되어 있으므로 신규 라우트 3개도 자동 노출. 자체 결정: include 시점·순서 변경 금지.
  - **템플릿 변경 없음** — `templates/list.html`이 카테고리/태그/글 항목 모두 `heading` + `items` 표준 컨텍스트로 표현 가능. T-018D에서 `subtitle?` 옵션 처리 이미 포함.
  - **`tests/test_web_app.py` 수정** — 5 케이스 추가.
    1. `test_categories_index_empty` — categories 0건 → `client.get("/categories")` → 200 + `"카테고리" in response.text` + `"아직 항목이 없습니다" in response.text`.
    2. `test_categories_index_with_entries` — `repo.upsert_category(conn, "AI")` + `repo.upsert_category(conn, "데이터")` → 200 + `"ai" in response.text`(저장 시 lowercase) + `"데이터" in response.text` + `'href="/categories/ai"' in response.text`(혹은 동등 검증).
    3. `test_category_articles_renders_articles` — 카테고리 1개 + articles 2개 + `link_article_category(conn, article_id, category_id)` → `client.get("/categories/AI")` → 200 + 두 글의 `title` 본문 포함 + `"카테고리: ai" in response.text`(정규화된 이름 표기).
    4. `test_category_articles_404_for_missing_name` — `client.get("/categories/존재하지않는카테고리")` → 404.
    5. `test_tag_articles_404_for_missing_name` — `client.get("/tags/없는태그")` → 404.
    - 자체 결정: 태그 200 케이스(`test_tag_articles_renders_articles`) 미작성 — 카테고리 200 케이스가 동일 코드 경로를 충분히 커버하고 태그도 같은 패턴(`get_tag_by_name`+`list_articles_by_tag`)이므로 회귀 위험 낮음. PRD §13에 비추어 GET /tags/{name} 자체는 404 케이스 1개로 라우팅 동작 검증 + 카테고리 200을 통한 공통 코드 경로 커버로 충족(테스트 비중 균형).
    - 픽스처: 기존 `with TestClient(create_app(tmp_db)) as client:` 컨텍스트 패턴 일관(T-018C/D 패턴 그대로).
  - **회귀:** 기존 173개 테스트 회귀 0(173/173 PASS 유지). 신규 5 케이스 → 합계 **178/178 PASS** 목표.

- **모듈 경계(엄수):**
  - 변경 파일: `src/rss_wiki/storage/repo.py`(수정 — 2 함수 추가), `src/rss_wiki/web/routes_magazines.py`(수정 — 3 헬퍼 + 3 라우트 추가), `tests/test_web_app.py`(수정 — 5 케이스 추가) — 합계 3개.
  - 변경 금지: `src/rss_wiki/{config,cli,main}.py`, `src/rss_wiki/{ingest,llm,publish,pipeline}/*.py`, `src/rss_wiki/storage/{schema.sql,db.py}`, `src/rss_wiki/web/{__init__.py,app.py,markdown.py,templates/*.html}`, `feeds.toml`, `feeds.example.toml`, `pyproject.toml`(의존성 미추가), `README.md`.
  - 신규 외부 의존성 미추가(`python-multipart`는 T-018F 책임).
  - 신규 라우트 모듈/템플릿 신설 금지(`routes_browse.py`/`routes_feeds.py`/`category.html` 등 미도입 — `routes_magazines.py` 확장으로 충분).
  - 피드 GET/POST 라우트(T-018E/T-018F), CLI `web` 서브커맨드(T-018G)는 본 슬라이스 범위 외.

- **touch:**
  - `src/rss_wiki/storage/repo.py` (수정 — `get_category_by_name` + `get_tag_by_name` 2 함수 추가)
  - `src/rss_wiki/web/routes_magazines.py` (수정 — `_category_items`/`_tag_items`/`_article_items` 3 헬퍼 + `categories_index`/`category_articles`/`tag_articles` 3 라우트 추가)
  - `tests/test_web_app.py` (수정 — 5 케이스 추가)

- **참고:**
  - PRD §13 라우트 표 — `GET /categories` 카테고리 인덱스, `GET /categories/{name}` 해당 카테고리 글 목록, `GET /tags/{name}` 해당 태그 글 목록. 본 슬라이스가 3 라우트 모두 충족.
  - PRD §6 — 카테고리/태그는 storage 레이어에서 `strip()` + 소문자화로 정규화됨(M2 확립 패턴, `upsert_category`/`upsert_tag`). `get_category_by_name`/`get_tag_by_name`도 동일 정규화를 적용하여 입력 케이스/공백에 무관하게 매칭.
  - 후속 슬라이스 T-018E — 피드 GET 라우트 + `routes_feeds.py` 신규 모듈 + `feeds.html`/`feed_edit.html` 템플릿. 본 슬라이스 PASS 후 활성화.

### [x] T-018D 매거진 GET 라우트 + 템플릿 토대 — M7 다섯 번째 슬라이스 (PASS 173/173, 2026-05-05)
- **목표:** PRD §13 웹 인터페이스의 매거진 열람 흐름을 구축. (a) `repo.list_magazines`/`repo.get_magazine_by_id` 2 함수 추가, (b) `src/rss_wiki/web/templates/` 디렉터리 + `base.html`/`magazine.html`/`list.html` 3 템플릿 신설, (c) `src/rss_wiki/web/routes_magazines.py` 신규 — `APIRouter` 기반 `GET /` 매거진 인덱스 + `GET /magazines` 목록 + `GET /magazines/{magazine_id}` 단건(마크다운→HTML), (d) `web/app.py` 수정 — `Jinja2Templates` 모듈 레벨 인스턴스 + `include_router`, 기존 `/` 임시 HTML 라우트는 `routes_magazines.py`로 이전. (e) `tests/test_web_app.py`에 5 케이스 추가/1 케이스 갱신. 카테고리/태그 라우트는 본 슬라이스 범위 외(T-018D2). 매거진 슬러그는 `magazines.id` 정수로 단순화(별도 슬러그 컬럼 미추가, 자체 결정).

- **acceptance:**
  - **`src/rss_wiki/storage/repo.py` 수정** — 2 함수 추가(파일 끝에 append).
    ```python
    def list_magazines(conn: sqlite3.Connection) -> list[sqlite3.Row]:
        return list(
            conn.execute(
                "SELECT id, kind, published_at, file_path FROM magazines "
                "ORDER BY published_at DESC, id DESC"
            ).fetchall()
        )


    def get_magazine_by_id(
        conn: sqlite3.Connection, magazine_id: int
    ) -> sqlite3.Row | None:
        return conn.execute(
            "SELECT * FROM magazines WHERE id = ?", (magazine_id,)
        ).fetchone()
    ```
    - M2 패턴 일관: `Connection` 첫 인자, `conn.commit()` 미수행, `sqlite3.Row` 반환.
    - 정렬은 `published_at DESC, id DESC` — 같은 published_at 내에서는 최신 입력 먼저.
  - **`src/rss_wiki/web/templates/base.html` 신규** — 골격 템플릿.
    ```html
    <!doctype html>
    <html lang="ko">
    <head>
        <meta charset="utf-8">
        <title>{% block title %}RSS Wiki{% endblock %}</title>
        <style>body { font-family: -apple-system, sans-serif; max-width: 720px; margin: 2em auto; padding: 0 1em; line-height: 1.6; }</style>
    </head>
    <body>
        <header><h1><a href="/">RSS Wiki</a></h1></header>
        <main>{% block content %}{% endblock %}</main>
    </body>
    </html>
    ```
    - 정적 자산은 인라인 CSS 1줄(PRD §13 "최소한의 CSS만 인라인" 충족).
    - 헤더 링크는 `/` 매거진 인덱스로 회귀.
  - **`src/rss_wiki/web/templates/list.html` 신규** — 항목 목록 템플릿(매거진 + 후속 카테고리/태그 재사용).
    ```html
    {% extends "base.html" %}
    {% block title %}{{ heading }} — RSS Wiki{% endblock %}
    {% block content %}
    <h2>{{ heading }}</h2>
    {% if items %}
    <ul>
        {% for item in items %}
        <li>
            <a href="{{ item.href }}">{{ item.title }}</a>
            {% if item.subtitle %}<small>{{ item.subtitle }}</small>{% endif %}
        </li>
        {% endfor %}
    </ul>
    {% else %}
    <p>아직 항목이 없습니다.</p>
    {% endif %}
    {% endblock %}
    ```
    - 컨텍스트: `heading: str`, `items: list[dict]` (`title`, `href`, `subtitle?`).
    - 빈 목록은 `<p>아직 항목이 없습니다.</p>` 노출.
  - **`src/rss_wiki/web/templates/magazine.html` 신규** — 매거진 단건 템플릿.
    ```html
    {% extends "base.html" %}
    {% block title %}{{ title }} — RSS Wiki{% endblock %}
    {% block content %}
    <article>
        {{ magazine_html | safe }}
    </article>
    {% endblock %}
    ```
    - 컨텍스트: `title: str`(예: `"daily 2026-05-05"`), `magazine_html: str`(`render_markdown` 결과).
    - `| safe`는 `render_markdown`이 안전한 HTML을 반환한다는 가정(markdown-it-py CommonMark 기본 출력은 `<script>` 등 raw HTML을 escape).
  - **`src/rss_wiki/web/routes_magazines.py` 신규**
    ```python
    from __future__ import annotations

    import sqlite3
    from pathlib import Path

    from fastapi import APIRouter, Depends, HTTPException, Request
    from fastapi.responses import HTMLResponse

    from rss_wiki.storage import repo
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
    def index(request: Request, conn: sqlite3.Connection = Depends(...)) -> HTMLResponse:
        rows = repo.list_magazines(conn)
        templates = request.app.state.templates
        return templates.TemplateResponse(
            request,
            "list.html",
            {"heading": "최근 매거진", "items": _magazine_items(rows)},
        )


    @router.get("/magazines", response_class=HTMLResponse)
    def magazines_list(request: Request, conn: sqlite3.Connection = Depends(...)) -> HTMLResponse:
        rows = repo.list_magazines(conn)
        templates = request.app.state.templates
        return templates.TemplateResponse(
            request,
            "list.html",
            {"heading": "매거진 인덱스", "items": _magazine_items(rows)},
        )


    @router.get("/magazines/{magazine_id}", response_class=HTMLResponse)
    def magazine_detail(
        magazine_id: int,
        request: Request,
        conn: sqlite3.Connection = Depends(...),
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
            },
        )
    ```
    - **자체 결정**: `Depends(...)` 부분은 generator가 실제 import한 `from rss_wiki.web.app import get_db`로 채움(순환 import 회피 — `routes_magazines.py`가 `app.py`를 import하므로 `app.py`에서 `routes_magazines.py`의 router를 import하는 시점에 `get_db`가 이미 정의되어 있어야 함). 순서: `app.py`의 `get_db` 함수 선언 → 그 이후에 `from rss_wiki.web.routes_magazines import router as magazines_router` import + `app.include_router(magazines_router)`. 자체 결정: 라우트 모듈에서 `from rss_wiki.web.app import get_db`를 함수 본문 내부 import 또는 모듈 상단 import 둘 다 가능 — 단순함을 위해 모듈 상단 권장.
    - `request.app.state.templates`로 Jinja2Templates 인스턴스 접근 — `web/app.py`의 lifespan/create_app에서 `app.state.templates = templates`로 등록.
    - 매거진 목록 항목 변환 헬퍼 `_magazine_items`는 라우트 모듈 내부 비공개 함수(언더스코어 prefix). 카테고리/태그 라우트(T-018D2)에서도 유사 헬퍼를 추가하되 본 슬라이스에서는 매거진만 처리.
  - **`src/rss_wiki/web/app.py` 수정**
    - import 추가: `from fastapi.templating import Jinja2Templates`, `from rss_wiki.web.routes_magazines import router as magazines_router`.
    - 모듈 레벨: `templates = Jinja2Templates(directory=Path(__file__).parent / "templates")`.
    - `create_app` 내부 변경:
      - `app.state.templates = templates` (lifespan 또는 create_app 본문에 1줄 추가).
      - 기존 `/` 라우트(`@app.get("/", response_class=HTMLResponse) def index(): ...`) **제거** — `routes_magazines.py`의 `index` 라우트가 대체.
      - `app.include_router(magazines_router)` 호출(get_db 함수 정의 이후 + app 인스턴스 생성 직후).
    - 변경 금지: `DEFAULT_DB_PATH`, `lifespan`(WAL 활성화 로직 그대로), `get_db` 함수, `GET /healthz` 라우트, 모듈 레벨 `app = create_app()` export.
  - **`tests/test_web_app.py` 수정** — 1 케이스 갱신 + 4 신규 케이스 추가.
    - 갱신: `test_index_returns_200` — 검증 본문을 "RSS Wiki" 포함 → 매거진 목록 페이지 골격 검증(예: `"<title>" in response.text` 또는 `"매거진" in response.text` 또는 `"<h1>" in response.text` + 200). 자체 결정: 본문 검증은 `"RSS Wiki" in response.text`(base.html 헤더가 항상 노출) 유지로 갱신 최소화.
    - 신규:
      1. `test_magazines_list_empty` — `TestClient(create_app(tmp_db))` + magazines 0건 → `client.get("/magazines")` → 200 + `"매거진 인덱스" in response.text` + `"아직 항목이 없습니다" in response.text`.
      2. `test_magazines_list_with_entries` — `init_db` + `insert_magazine` 2 행(kind=`"daily"`, published_at=`"2026-05-04"` / kind=`"weekly"`, published_at=`"2026-05-03"`) → 200 + 두 published_at 본문 포함 + `"daily"` + `"weekly"` 본문 포함. 자체 결정: file_path는 임시 더미 경로 사용(목록 라우트는 file_path를 읽지 않음).
      3. `test_magazine_detail_renders_markdown` — `tmp_path / "out.md"`에 `# Hello\n\n본문 텍스트` 작성 → `insert_magazine(file_path=str(md_path), kind="daily", published_at="2026-05-05")` → `client.get(f"/magazines/{mag_id}")` → 200 + `"<h1>Hello</h1>" in response.text` + `"본문 텍스트" in response.text` + `"daily 2026-05-05" in response.text`(`<title>` 또는 본문).
      4. `test_magazine_detail_404_for_missing_id` — `client.get("/magazines/99999")` → 404.
      5. `test_magazine_detail_404_when_file_missing` — `insert_magazine(file_path="/nonexistent/path.md", kind="daily", published_at="2026-05-05")` → 200 아님, 404 응답.
    - 픽스처: 기존 `tmp_path` 패턴 + `with TestClient(create_app(tmp_db)) as client:` 컨텍스트(lifespan startup 보장).
  - **회귀:** 기존 168개 테스트 회귀 0(168/168 PASS 유지). 신규 5 케이스(`test_index_returns_200`은 갱신이라 카운트 변동 없음) → 합계 **173/173 PASS** 목표.

- **모듈 경계(엄수):**
  - 변경 파일: `src/rss_wiki/storage/repo.py`(수정 — 2 함수 추가), `src/rss_wiki/web/app.py`(수정 — Jinja2Templates 인스턴스 + include_router + `/` 라우트 제거), `src/rss_wiki/web/routes_magazines.py`(신규), `src/rss_wiki/web/templates/base.html`(신규), `src/rss_wiki/web/templates/magazine.html`(신규), `src/rss_wiki/web/templates/list.html`(신규), `tests/test_web_app.py`(수정 — 5 케이스 추가/1 갱신) — 합계 7개.
  - 변경 금지: `src/rss_wiki/{config,cli,main}.py`, `src/rss_wiki/{ingest,llm,publish,pipeline}/*.py`, `src/rss_wiki/storage/{schema.sql,db.py}`, `src/rss_wiki/web/{__init__.py,markdown.py}`, `feeds.toml`, `feeds.example.toml`, `pyproject.toml`(의존성 미추가 — 본 슬라이스는 기존 fastapi/jinja2/markdown-it-py로 충분), `README.md`.
  - 신규 외부 의존성 미추가(`python-multipart`는 T-018F 책임).
  - 카테고리/태그 라우트(`routes_browse.py` 또는 routes_magazines.py 확장), 피드 라우트(`routes_feeds.py`/`feeds.html`/`feed_edit.html`), CLI `web` 서브커맨드(`cli.py`)는 본 슬라이스 범위 외.

- **touch:**
  - `src/rss_wiki/storage/repo.py` (수정 — `list_magazines` + `get_magazine_by_id` 2 함수 추가)
  - `src/rss_wiki/web/app.py` (수정 — Jinja2Templates 모듈 레벨 인스턴스 + include_router + `/` 라우트 routes_magazines.py로 이전)
  - `src/rss_wiki/web/routes_magazines.py` (신규 — `APIRouter` + 3 라우트: `/`, `/magazines`, `/magazines/{magazine_id}`)
  - `src/rss_wiki/web/templates/base.html` (신규 — 골격)
  - `src/rss_wiki/web/templates/list.html` (신규 — 항목 목록, 매거진/카테고리/태그 공용)
  - `src/rss_wiki/web/templates/magazine.html` (신규 — 매거진 단건)
  - `tests/test_web_app.py` (수정 — `test_index_returns_200` 갱신 + 5 신규 케이스)

- **참고:**
  - PRD §13 라우트 표 — `GET /` 최신 일간 매거진 + 최근 발행 매거진 목록, `GET /magazines` 일간/주간/월간 매거진 인덱스, `GET /magazines/{slug}` 매거진 단건. 본 슬라이스는 `/` 와 `/magazines`를 동일한 list.html로 단순화(`/`는 "최근 매거진" 헤딩, `/magazines`는 "매거진 인덱스" 헤딩) — "최신 일간 단건 + 최근 목록 분리"는 후속 사이클 검토(YAGNI).
  - PRD §13 "템플릿: Jinja2 (서버 사이드 렌더링; SPA 미도입)" — 본 슬라이스가 Jinja2 도입 토대.
  - PRD §13 "마크다운 렌더: markdown-it-py 또는 markdown 패키지" — T-018C에서 markdown-it-py 채택 + `web/markdown.render_markdown` 정의 완료. 본 슬라이스가 첫 사용처.
  - 후속 슬라이스 T-018D2 — 카테고리/태그 GET 라우트 + 기존 `templates/list.html` 재사용. `routes_magazines.py` 확장 또는 별도 `routes_browse.py` 모듈 분리는 T-018D2 진입 시 결정.

### [x] T-018C `web/` 패키지 골격 + 의존성 + healthz/index 라우트 — M7 네 번째 슬라이스 (PASS 168/168, 2026-05-05)
- **목표:** PRD §13 FastAPI 웹 인터페이스의 토대 구축. (a) `pyproject.toml dependencies`에 `fastapi`/`uvicorn[standard]`/`jinja2`/`markdown-it-py` 4 패키지 추가, (b) `src/rss_wiki/web/` 패키지 골격 — `__init__.py`(빈), `app.py`(`create_app` 팩토리 + lifespan startup에서 `init_db` 호출 + `PRAGMA journal_mode=WAL` 활성화 + 모듈 레벨 `app` 인스턴스 + `get_db` 의존성 + `GET /healthz`/`GET /` 두 라우트), `markdown.py`(`render_markdown(text) -> str` 단일 함수, markdown-it-py 래퍼). (c) `tests/test_web_app.py` 신규 — `fastapi.testclient.TestClient` + `tmp_path` 기반 4 케이스. 본 슬라이스는 토대만 다루고 매거진/피드 라우트는 T-018D~F에서 추가, CLI `web` 서브커맨드와 README는 T-018G에서 처리.

- **acceptance:**
  - **`pyproject.toml` 수정** — `[project] dependencies` 배열에 4 항목 추가(기존 `feedparser`/`httpx`/`trafilatura` 표기법 일관 — 버전 핀 미지정). 최종 형태:
    ```toml
    dependencies = [
        "feedparser",
        "httpx",
        "trafilatura",
        "fastapi",
        "uvicorn[standard]",
        "jinja2",
        "markdown-it-py",
    ]
    ```
    - 기존 `[project.scripts]`/`[project.optional-dependencies]`/`[tool.setuptools.packages.find]`/`[tool.pytest.ini_options]` 섹션 변경 금지.
    - `requires-python = ">=3.12"` 변경 금지.
  - **`src/rss_wiki/web/__init__.py` 신규** — 빈 파일(0 byte 또는 newline 1줄).
  - **`src/rss_wiki/web/app.py` 신규** — 다음 항목 포함.
    ```python
    from __future__ import annotations

    import os
    import sqlite3
    from contextlib import asynccontextmanager
    from pathlib import Path
    from typing import Iterator

    from fastapi import Depends, FastAPI
    from fastapi.responses import HTMLResponse, JSONResponse

    from rss_wiki.storage.db import init_db


    DEFAULT_DB_PATH = "data/rss-wiki.db"


    def create_app(db_path: str | Path | None = None, *, run_init_db: bool = True) -> FastAPI:
        if db_path is None:
            db_path = os.environ.get("RSS_WIKI_DB", DEFAULT_DB_PATH)
        resolved = Path(db_path)

        @asynccontextmanager
        async def lifespan(_: FastAPI):
            if run_init_db:
                init_db(resolved)
            conn = sqlite3.connect(resolved)
            try:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.commit()
            finally:
                conn.close()
            yield

        app = FastAPI(lifespan=lifespan)
        app.state.db_path = resolved

        @app.get("/healthz")
        def healthz() -> JSONResponse:
            return JSONResponse({"status": "ok"})

        @app.get("/", response_class=HTMLResponse)
        def index() -> HTMLResponse:
            return HTMLResponse(
                "<h1>RSS Wiki</h1>"
                "<p>최신 매거진 라우트는 다음 슬라이스(T-018D)에서 추가 예정.</p>"
            )

        return app


    def get_db(request) -> Iterator[sqlite3.Connection]:
        db_path: Path = request.app.state.db_path
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()


    app = create_app()
    ```
    - **자체 결정**: `get_db`는 본 슬라이스 라우트(`/healthz`, `/`)에서 사용하지 않지만 T-018D 이후 슬라이스가 즉시 import할 수 있도록 미리 정의. 미사용 import 경고는 없음(별도 라우트 모듈에서 사용 예정).
    - 모듈 레벨 `app = create_app()`이 있어 `uvicorn rss_wiki.web.app:app` 호출이 동작.
    - `request: Request`(또는 `Depends(get_db)` 시 자동 주입)는 FastAPI가 처리하므로 stdlib `Request` import 불필요(타입 힌트 없이 동작 가능). 자체 결정: 단순함 우선 — 본 슬라이스에서는 `get_db` 시그니처에 `request` 파라미터를 받되 타입 힌트 미부착(Sequel 슬라이스에서 `from fastapi import Request`로 정리 가능).
  - **`src/rss_wiki/web/markdown.py` 신규** — 단일 함수.
    ```python
    from __future__ import annotations

    from markdown_it import MarkdownIt


    _md = MarkdownIt("commonmark", {"linkify": True})


    def render_markdown(text: str) -> str:
        """마크다운 문자열을 HTML로 렌더링."""
        return _md.render(text)
    ```
    - 모듈 레벨 단일 인스턴스(`_md`) 재사용 — 요청마다 재생성 비용 회피.
    - 라이브러리 인스턴스 외부 노출 금지(`render_markdown` 단일 export).
  - **`tests/test_web_app.py` 신규** — 4 케이스.
    1. `test_healthz_returns_ok` — `TestClient(create_app(tmp_path / "x.db"))` → `client.get("/healthz")` → 200 + `response.json() == {"status": "ok"}`.
    2. `test_index_returns_200` — `client.get("/")` → 200 + `"<h1>" in response.text`(또는 `"RSS Wiki" in response.text`).
    3. `test_create_app_runs_init_db_and_enables_wal` — `tmp_db = tmp_path / "x.db"` → `with TestClient(create_app(tmp_db)) as client: client.get("/healthz")` → `tmp_db.exists() == True` + 별도 커넥션 열어 `PRAGMA journal_mode` 결과가 `"wal"`. 자체 결정: lifespan startup이 동작하려면 `with TestClient(...)` 컨텍스트 매니저로 사용해야 함(FastAPI 표준). 본 케이스는 lifespan 동작도 함께 검증.
    4. `test_render_markdown_basic` — `from rss_wiki.web.markdown import render_markdown` → `render_markdown("# Hello")` → 결과에 `"<h1>"` + `"Hello"` 포함. `render_markdown("[link](https://example.com)")` → 결과에 `"<a"` + `"https://example.com"` 포함(linkify 검증은 선택, h1 검증만으로도 충분).
    - 픽스처는 `tmp_path` 기반(다른 테스트와 일관). 외부 네트워크/uvicorn 직접 호출 금지.
  - **회귀:** 기존 164개 테스트 회귀 0(164/164 PASS 유지). 신규 4 케이스 → 합계 **168/168 PASS** 목표.

- **모듈 경계(엄수):**
  - 신규 파일 4개: `src/rss_wiki/web/__init__.py`, `src/rss_wiki/web/app.py`, `src/rss_wiki/web/markdown.py`, `tests/test_web_app.py`.
  - 수정 파일 1개: `pyproject.toml`(dependencies 4 항목 추가만).
  - 변경 금지: `src/rss_wiki/{config,cli,storage/*,ingest/*,llm/*,publish/*,pipeline/*}.py`, `main.py`, `feeds.toml`, `feeds.example.toml`, `README.md`.
  - 신규 외부 의존성 4개(`fastapi`, `uvicorn[standard]`, `jinja2`, `markdown-it-py`)만 추가. 다른 패키지 추가 금지(예: `python-multipart`는 T-018F 폼 처리 시점에 추가 검토).
  - 라우트 모듈/템플릿 디렉터리 신설 금지: `routes_magazines.py`/`routes_feeds.py`/`templates/` 미도입(T-018D 이후 슬라이스 책임).
  - CLI 변경 금지: `cli.py`에 `web` 서브커맨드 추가 금지(T-018G 책임).

- **touch:**
  - `pyproject.toml` (수정 — dependencies 4 항목 추가)
  - `src/rss_wiki/web/__init__.py` (신규 — 빈 파일)
  - `src/rss_wiki/web/app.py` (신규 — `create_app`/`get_db`/lifespan/healthz/index)
  - `src/rss_wiki/web/markdown.py` (신규 — `render_markdown` 단일 함수)
  - `tests/test_web_app.py` (신규 — 4 케이스)

- **참고:**
  - PRD §13 "FastAPI + Uvicorn / 템플릿: Jinja2 / 마크다운 렌더: markdown-it-py 또는 markdown 패키지" — markdown-it-py 채택(자체 결정, 더 활발한 유지보수 + CommonMark 표준 준수).
  - PRD §13 "동일 SQLite 파일을 공유하며 쓰기 충돌 방지를 위해 WAL 모드 사용" — lifespan startup에서 영구 활성화.
  - PRD §13 "기본 바인딩은 `127.0.0.1`로만 listen" — 본 슬라이스는 라우트만 정의(바인딩은 uvicorn 호출 시 결정), T-018G의 `rss-wiki web` 서브커맨드에서 `--host 127.0.0.1 --port 8765` 명시.
  - 후속 슬라이스 T-018D — 매거진/카테고리/태그 GET 라우트 + `templates/{base,magazine,list}.html` 신설 + `web/markdown.py`의 `render_markdown` 활용.

### [x] T-018B2 articles 외래키 nullable + 스냅샷 컬럼 + `delete_feed` — M7 세 번째 슬라이스 (PASS 164/164, 2026-05-05)
- **목표:** PRD §13 피드 CRUD의 "삭제 시 피드 메타를 글 row에 스냅샷"을 코드에 반영. (a) `articles.feed_id`를 NOT NULL → nullable로 SQLite 테이블 재생성 패턴 마이그레이션, (b) `articles.feed_url_snapshot`/`feed_name_snapshot` 2 컬럼 추가(멱등 ALTER TABLE ADD COLUMN), (c) `repo.delete_feed(conn, feed_id)` 함수 신설(스냅샷 채움 → `feed_id=NULL` → DELETE feeds 행). 본 슬라이스 PASS 시 피드 CRUD 토대 완성, 후속 T-018F의 `POST /feeds/{id}/delete` 라우트가 본 함수 직접 호출.

- **acceptance:**
  - **`src/rss_wiki/storage/schema.sql` 수정** — `articles` 테이블 정의 갱신.
    - 기존: `feed_id INTEGER NOT NULL REFERENCES feeds(id),` → 변경: `feed_id INTEGER REFERENCES feeds(id),` (NOT NULL 제거).
    - 신규 컬럼 2개 추가: `feed_url_snapshot TEXT,` 및 `feed_name_snapshot TEXT,` (둘 다 nullable). 컬럼 위치는 `summary` 뒤, `created_at` 앞 권장(읽기 가독성).
    - 기존 컬럼(`id`/`url`/`url_hash`/`title`/`title_hash`/`published_at`/`content`/`summary`/`created_at`)은 그대로 유지. 인덱스 정의(`idx_articles_url_hash`, `idx_articles_title_hash`)는 그대로 유지.
  - **`src/rss_wiki/storage/db.py` `init_db` 수정** — articles 마이그레이션 추가.
    - 기존 feeds 마이그레이션 블록 다음에 articles 마이그레이션 블록 추가.
    - **단계 1 — feed_id NOT NULL → nullable 재생성:**
      - `PRAGMA table_info(articles)`로 컬럼 정보 조회.
      - `feed_id` 행의 `notnull == 1`이면 재생성 수행. `notnull == 0` 또는 articles 테이블 비어 있으면 스킵(멱등).
      - 재생성 순서:
        ```
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.executescript("""
            CREATE TABLE articles_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                feed_id INTEGER REFERENCES feeds(id),
                url TEXT NOT NULL,
                url_hash TEXT NOT NULL UNIQUE,
                title TEXT,
                title_hash TEXT,
                published_at TEXT,
                content TEXT,
                summary TEXT,
                feed_url_snapshot TEXT,
                feed_name_snapshot TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            INSERT INTO articles_new (id, feed_id, url, url_hash, title, title_hash, published_at, content, summary, created_at)
                SELECT id, feed_id, url, url_hash, title, title_hash, published_at, content, summary, created_at FROM articles;
            DROP TABLE articles;
            ALTER TABLE articles_new RENAME TO articles;
            CREATE INDEX IF NOT EXISTS idx_articles_url_hash ON articles(url_hash);
            CREATE INDEX IF NOT EXISTS idx_articles_title_hash ON articles(title_hash);
        """)
        conn.execute("PRAGMA foreign_keys = ON")
        ```
      - 재생성 후 신규 articles에는 스냅샷 2 컬럼이 자동 포함되어 단계 2가 불필요.
    - **단계 2 — 스냅샷 컬럼 멱등 추가(재생성을 거치지 않은 경우):**
      - 재생성 미수행 경로(이미 nullable이지만 스냅샷 컬럼 누락 가능)에 대비.
      - 재생성 후에도 멱등성 보장을 위해 항상 `PRAGMA table_info(articles)` 재조회 후 누락 컬럼만 `ALTER TABLE articles ADD COLUMN feed_url_snapshot TEXT` / `ADD COLUMN feed_name_snapshot TEXT`.
      - feeds 마이그레이션과 동일 패턴(T-018A 재사용).
    - 두 번째 호출 시 멱등(이미 nullable + 컬럼 존재 → 둘 다 스킵).
    - 신규 DB(첫 호출): `CREATE TABLE IF NOT EXISTS`가 신 스키마(nullable + 스냅샷 2 컬럼) 그대로 생성 → 단계 1·2 모두 스킵.
  - **`src/rss_wiki/storage/repo.py` 신규 함수 1개 추가:**
    ```python
    def delete_feed(conn: sqlite3.Connection, feed_id: int) -> None:
        conn.execute(
            """
            UPDATE articles
            SET feed_url_snapshot = (SELECT url FROM feeds WHERE id = ?),
                feed_name_snapshot = (SELECT name FROM feeds WHERE id = ?)
            WHERE feed_id = ?
            """,
            (feed_id, feed_id, feed_id),
        )
        conn.execute("UPDATE articles SET feed_id = NULL WHERE feed_id = ?", (feed_id,))
        conn.execute("DELETE FROM feeds WHERE id = ?", (feed_id,))
    ```
    - `Connection` 첫 인자(M2 패턴). 트랜잭션 commit은 호출자 책임(M2 패턴).
    - 미존재 `feed_id`는 silent no-op(존재 검사 미수행 — 호출자가 검증). UPDATE/DELETE 모두 0 행 영향이 자연스럽게 처리.
    - 외래키 정합성: 단계 (2)의 명시적 NULL 처리가 단계 (3) DELETE보다 먼저 수행되므로 `PRAGMA foreign_keys = ON` 상태에서도 외래키 위반 없음.
  - **단위 테스트 — `tests/test_storage_repo.py`에 6 케이스 추가.** 자체 결정: 기존 파일 확장(테스트 파일 분산 방지, T-018A 일관).
    1. `init_db_articles_feed_id_nullable_migration` — 구 NOT NULL 스키마 DB(`feed_id INTEGER NOT NULL REFERENCES feeds(id)`) 만들고 articles 1~2 행 삽입(feed 1 행 선삽입 → FK 충족) → `init_db` 호출 → `PRAGMA table_info(articles)`에서 `feed_id` 행의 `notnull == 0` 확인 + 인덱스 2개(`idx_articles_url_hash`, `idx_articles_title_hash`) 존재 확인. 기존 articles 행 보존(SELECT COUNT == 원본).
    2. `init_db_articles_snapshot_columns_migration` — 신 nullable 스키마 + 스냅샷 컬럼 누락 DB 만들고 `init_db` 호출 → `PRAGMA table_info(articles)`에 `feed_url_snapshot`, `feed_name_snapshot` 두 컬럼 모두 존재.
    3. `init_db_articles_migration_preserves_data` — 구 스키마 DB에 articles 행 1개 삽입(url_hash="abc123", title="원본") → `init_db` 호출 후 `SELECT * FROM articles WHERE url_hash = ?` → 원본 모든 컬럼 값 보존(title/published_at/summary 등).
    4. `init_db_articles_double_call` — 신 스키마 DB(nullable + 스냅샷)에 articles 1행 삽입 후 `init_db` 두 번 호출 → 에러 없음, 행 보존, 컬럼 멱등(추가 컬럼 미생성).
    5. `delete_feed_fills_snapshot_and_nulls_feed_id` — feeds 1행(`name="X", url="https://x.example.com/rss"`) + articles 2행(같은 feed_id) 삽입 → `delete_feed(conn, feed_id)` → `SELECT feed_id, feed_url_snapshot, feed_name_snapshot FROM articles` 결과: `feed_id IS NULL`, `feed_url_snapshot == "https://x.example.com/rss"`, `feed_name_snapshot == "X"` 두 행 모두. `SELECT COUNT(*) FROM feeds WHERE id = ?` == 0.
    6. `delete_feed_no_articles` — feeds 1행 + articles 0건 → `delete_feed(conn, feed_id)` → 예외 없음, feeds 행 삭제 확인.
  - **회귀:** 기존 158개 테스트 회귀 0(158/158 PASS 유지). 신규 6 케이스 → 합계 **164/164 PASS** 목표.

- **모듈 경계(엄수):**
  - 변경 파일은 `src/rss_wiki/storage/{schema.sql,db.py,repo.py}` + `tests/test_storage_repo.py` 4개로 한정.
  - 변경 금지: `src/rss_wiki/{config,cli}.py`, `src/rss_wiki/{ingest,llm,publish,pipeline}/*.py`, `main.py`, `feeds.toml`, `feeds.example.toml`, `pyproject.toml`, `README.md`.
  - 신규 외부 의존성 미추가(stdlib `sqlite3`만 사용).
  - 마이그레이션은 단일 `init_db` 호출 내 완결. 별도 마이그레이션 스크립트 파일 미도입.

- **touch:**
  - `src/rss_wiki/storage/schema.sql` (수정 — `articles` NOT NULL 제거 + 스냅샷 2 컬럼 추가)
  - `src/rss_wiki/storage/db.py` (수정 — `init_db`에 articles 재생성 + 스냅샷 컬럼 멱등 추가)
  - `src/rss_wiki/storage/repo.py` (수정 — `delete_feed` 1 함수 추가)
  - `tests/test_storage_repo.py` (수정 — 6 케이스 추가)

- **참고:**
  - PRD §13 "피드 CRUD 동작 → 삭제: 소프트 삭제 없이 하드 삭제. 단, 이미 수집·발행된 글은 그대로 유지(글의 `feed_id`는 nullable로 두거나, 삭제 시점에 피드 메타를 글 row에 스냅샷)" — 본 슬라이스가 두 옵션 모두 채택(nullable + 스냅샷)하여 정합성 + 운영자 추적성을 동시에 보장.
  - PRD §11 — feeds SoT 변경(T-018B 완료) 후 운영자가 SQL/웹으로 피드 삭제 시 articles 잔존이 가능해야 함. 본 슬라이스가 그 가능성을 코드에 반영.
  - 후속 슬라이스 T-018C — `web/` 패키지 골격(fastapi/uvicorn/jinja2/markdown-it-py 의존성, FastAPI 인스턴스 + WAL 모드, `GET /healthz` + `GET /` 임시 인덱스).

### [x] T-018B TOML→DB 부트스트랩 + `cli.run_daily` 전환 — M7 두 번째 슬라이스 (PASS 158/158, 2026-05-05)
- **목표:** PRD §11 "피드 목록은 SQLite의 `feeds` 테이블을 단일 진실 원천(SoT)으로 한다. 초기 부트스트랩용으로 TOML 시드 파일을 두고, 최초 실행 시 DB에 upsert한다"를 코드에 반영. `pipeline/bootstrap.py`에 `bootstrap_feeds_from_toml(conn, path)` 함수를 신설하고, `cli.main`의 `daily` 분기에서 부트스트랩 호출 → `list_feeds(conn, enabled_only=True)` 결과를 `FeedConfig`로 변환해 `run_daily`에 주입한다. `cli.run_daily` 시그니처는 변경하지 않아 단위 테스트 격리(인자 주입) 패턴을 유지한다. 외래키 정합성과 `delete_feed`는 본 슬라이스 범위 외(T-018B2에서 처리).

- **acceptance:**
  - **`src/rss_wiki/pipeline/bootstrap.py` 신규 작성** — 단일 함수 `bootstrap_feeds_from_toml`.
    ```python
    from __future__ import annotations

    import sqlite3
    from pathlib import Path

    from rss_wiki.config import load_feeds
    from rss_wiki.storage.repo import upsert_feed


    def bootstrap_feeds_from_toml(conn: sqlite3.Connection, path: str | Path) -> int:
        """feeds.toml의 모든 피드를 upsert. 반환: 처리된 피드 수."""
        feeds = load_feeds(path)
        for cfg in feeds:
            upsert_feed(conn, cfg.name, cfg.url)
        return len(feeds)
    ```
    - 결선층 패턴: `config.load_feeds` + `repo.upsert_feed`만 import. `storage/db.py`/`ingest/`/`llm/`/`publish/`/`pipeline/{ingest,llm,publish}.py` 미import.
    - `conn.commit()` 미호출 (M2/M6 인터페이스 원칙: commit은 호출자 책임).
    - 반환값은 `len(feeds)` — 호출자가 로깅·테스트에 활용.
    - `upsert_feed`는 기존 `INSERT OR IGNORE` 동작 그대로 — 같은 URL 재호출 시 `enabled`/`name` 등 기존 상태 유지(운영자가 웹/SQL로 수정한 메타가 부트스트랩으로 덮어쓰이지 않음). PRD §11 "운영 SoT는 DB" 의도와 일치.
  - **`src/rss_wiki/cli.py` 수정** — `main` 함수의 `daily` 분기 본문 교체.
    - import 추가: `from rss_wiki.pipeline.bootstrap import bootstrap_feeds_from_toml`, `from rss_wiki.storage.repo import list_feeds, list_unanalyzed_article_ids` (`list_feeds` 추가, `list_unanalyzed_article_ids` 유지).
    - import 제거: `from rss_wiki.config import FeedConfig, load_feeds` → `from rss_wiki.config import FeedConfig` (load_feeds는 더 이상 cli에서 직접 호출 안 함, 부트스트랩이 내부에서 호출).
    - `main` 함수 daily 분기:
      ```python
      if args.cmd == "daily":
          bootstrap_feeds_from_toml(conn, args.feeds)
          rows = list_feeds(conn, enabled_only=True)
          feeds = [FeedConfig(name=r["name"], url=r["url"]) for r in rows]
          return run_daily(conn=conn, feeds=feeds, output_dir=Path(args.output), logger=logger)
      ```
    - `weekly`/`monthly` 분기 변경 없음(부트스트랩 미수행, 발행만 수행).
    - `run_daily`/`run_weekly`/`run_monthly`/`is_friday`/`is_last_friday_of_month` 함수 시그니처/본문 변경 금지.
  - **`tests/test_pipeline_bootstrap.py` 신규 작성** — 4 케이스.
    1. `test_bootstrap_inserts_all_feeds` — 빈 DB + 2 피드 toml(`feeds.example.toml` 활용 또는 `tmp_path`로 인라인 toml 생성) → 호출 후 `list_feeds(conn)` 결과 2개 + `name`/`url` 일치.
    2. `test_bootstrap_idempotent` — 동일 toml 두 번 호출 → 여전히 같은 피드 수(중복 미생성). UNIQUE 제약 의존.
    3. `test_bootstrap_returns_count` — 반환값이 `len(feeds)`.
    4. `test_bootstrap_preserves_existing_state` — 미리 DB에 같은 URL의 피드를 `enabled=0`/`name="legacy"`로 삽입 → 부트스트랩 호출 후 `enabled=0`/`name="legacy"` 유지(`upsert_feed`의 INSERT OR IGNORE 의존). 운영자가 비활성화한 피드가 부트스트랩으로 활성화되지 않는 것을 보장.
    - 픽스처: `init_db(tmp_path / "x.db")` + `get_connection(...)` 패턴(다른 pipeline 테스트와 일관).
  - **`tests/test_cli.py` 수정** — `daily` 분기 통합 흐름 1 케이스 추가.
    5. `test_main_daily_bootstraps_and_runs` 또는 동등 명칭 — `cli.main(["--db", str(tmp_db), "--feeds", str(toml_path), "--output", str(out_dir), "daily"])` 호출이 `bootstrap_feeds_from_toml`을 거쳐 DB의 `list_feeds` 결과가 1개 이상이 되는지 확인. fetcher/extractor/runner는 monkeypatch 또는 환경상 호출 자체가 빈 entries를 받도록 처리해 외부 네트워크 비의존 보장. 자체 결정: 기존 `test_cli.py` 픽스처/패턴(이미 fetcher/runner 주입 검증)을 그대로 따르며, 본 케이스는 DB 상태 변화(`feeds` 테이블에 행이 생성)만 검증해도 충분(LLM/publish 흐름은 기존 케이스가 커버).
    - 신규 케이스 1개. 기존 12 케이스 회귀 0.
  - **회귀:** 기존 153개 테스트 회귀 0(153/153 PASS 유지). 신규 5 케이스(bootstrap 4 + cli 1) → 합계 **158/158 PASS** 목표.

- **모듈 경계(엄수):**
  - 신규 파일: `src/rss_wiki/pipeline/bootstrap.py`, `tests/test_pipeline_bootstrap.py`.
  - 수정 파일: `src/rss_wiki/cli.py`, `tests/test_cli.py`.
  - 변경 금지: `src/rss_wiki/{config,storage/{schema.sql,db.py,repo.py},ingest/*,llm/*,publish/*,pipeline/{__init__,ingest,llm,publish}.py}`, `feeds.toml`, `feeds.example.toml`, `main.py`, `pyproject.toml`, `README.md`.
  - 신규 의존성 미추가(stdlib + 기존 임포트만 사용).
  - `delete_feed`/외래키 nullable 마이그레이션/`articles` 스냅샷 컬럼은 본 슬라이스 범위 외(T-018B2에서 처리).

- **touch:**
  - `src/rss_wiki/pipeline/bootstrap.py` (신규)
  - `src/rss_wiki/cli.py` (수정 — import 갱신 + `daily` 분기 본문 교체)
  - `tests/test_pipeline_bootstrap.py` (신규 — 4 케이스)
  - `tests/test_cli.py` (수정 — 1 케이스 추가)

- **참고:**
  - PRD §11 — "피드 목록은 SQLite의 `feeds` 테이블을 단일 진실 원천(SoT)으로 한다. 초기 부트스트랩용으로 TOML 시드 파일을 두고, 최초 실행 시 DB에 upsert한다."
  - PRD §13 — 피드 CRUD UI는 DB 기반(웹 라우트는 T-018E/T-018F가 본격 구현). 본 슬라이스는 그 토대.
  - 후속 슬라이스 T-018B2 — `articles.feed_id` nullable 마이그레이션(SQLite 테이블 재생성 패턴), `articles.feed_url_snapshot`/`feed_name_snapshot` 2 컬럼 추가, `repo.delete_feed(conn, feed_id)` 신설.

### [x] T-018A `feeds` 스키마 확장 + storage repo 4 함수 — M7 첫 슬라이스 (PASS 153/153, 2026-05-05)
- **목표:** PRD §13 웹 인터페이스가 요구하는 피드 토글/리셋/메타 갱신을 위한 storage 레이어 확장. `feeds` 테이블에 신규 컬럼 3종 추가하고 `init_db`가 신규 DB·기존 DB 양쪽에서 멱등하게 동작하도록 마이그레이션 처리. repo에 list/update/toggle/reset 4 함수 추가. delete는 외래키 정합성 결정과 함께 T-018B에서 처리.

- **acceptance:**
  - **`src/rss_wiki/storage/schema.sql` 수정** — `feeds` 테이블 정의에 다음 3 컬럼 추가.
    - `enabled INTEGER NOT NULL DEFAULT 1` (boolean으로 사용; PRD §11)
    - `last_fetched_at TEXT` (nullable; PRD §11)
    - `updated_at TEXT NOT NULL DEFAULT (datetime('now'))` (PRD §11)
    - 기존 컬럼(`id`/`name`/`url`/`consecutive_failures`/`last_success_at`/`created_at`)은 그대로 유지. PRD §11 표의 `title`은 기존 `name` 컬럼으로 매핑(자체 결정 — 호환 유지, 컬럼 이중화 회피).
  - **`src/rss_wiki/storage/db.py` `init_db` 수정** — 멱등 마이그레이션 추가.
    - `CREATE TABLE IF NOT EXISTS`로 신규 DB는 신 스키마 그대로 생성.
    - 기존 DB(이미 `feeds` 테이블이 구 스키마로 존재하는 경우): `PRAGMA table_info(feeds)`로 컬럼 목록 조회 후 누락된 신규 3 컬럼만 `ALTER TABLE feeds ADD COLUMN ...`로 추가.
    - 기존 행은 `enabled=1`(default) / `last_fetched_at=NULL` / `updated_at=datetime('now')` (default)로 자동 채워짐.
    - 동일 함수 두 번 호출 시 멱등(이미 존재하는 컬럼은 스킵).
  - **`src/rss_wiki/storage/repo.py` 신규 함수 4개 추가:**
    - `list_feeds(conn: sqlite3.Connection, *, enabled_only: bool = False) -> list[sqlite3.Row]` — `enabled_only=True`면 `WHERE enabled = 1` 필터, 정렬은 `id ASC`.
    - `update_feed(conn: sqlite3.Connection, feed_id: int, *, name: str) -> None` — `name` 갱신 + `updated_at = datetime('now')` 동시 갱신.
    - `set_feed_enabled(conn: sqlite3.Connection, feed_id: int, enabled: bool) -> None` — `enabled` 토글(`int(enabled)`로 변환) + `updated_at` 갱신.
    - `reset_feed_failures(conn: sqlite3.Connection, feed_id: int) -> None` — `consecutive_failures = 0` + `updated_at` 갱신.
    - 모두 `Connection`을 첫 인자로 받는 함수형(M2 패턴). 트랜잭션 commit은 호출자 책임. 미존재 `feed_id`는 silent no-op(존재 검사 미수행 — 호출자가 검증).
  - **단위 테스트** — `tests/test_storage_repo.py`에 다음 6 케이스 추가(또는 신규 `tests/test_storage_feeds.py` 분리). 자체 결정: 기존 파일 확장(테스트 파일 분산 방지).
    1. `init_db_idempotent_migration` — 구 스키마 DB(컬럼 3개 누락) 만들고 `init_db` 호출 후 `PRAGMA table_info`에 신규 컬럼 3개 모두 존재 검증.
    2. `init_db_double_call` — 신 스키마에 `init_db` 두 번 호출해도 에러 없이 멱등.
    3. `list_feeds_default` — `enabled=1`/`enabled=0` 섞인 데이터에서 `list_feeds(conn)`(기본값)는 모두 반환, `id ASC` 정렬.
    4. `list_feeds_enabled_only` — 같은 데이터에서 `enabled_only=True`는 활성 피드만 반환.
    5. `update_feed_changes_name_and_updated_at` — `update_feed` 호출 후 `name` 변경 + `updated_at`이 호출 전보다 같거나 큰 값.
    6. `set_feed_enabled_toggle` — `True`로 호출 후 1, `False`로 호출 후 0. `updated_at` 갱신 검증.
    7. `reset_feed_failures` — `consecutive_failures`를 5로 세팅 후 `reset_feed_failures` 호출 → 0.
  - **회귀:** 기존 146개 테스트 회귀 0(146/146 PASS 유지).

- **모듈 경계(엄수):**
  - `storage/` 단독 변경. `ingest/`/`llm/`/`publish/`/`pipeline/`/`cli.py`/`main.py` 미변경.
  - 신규 의존성 미추가(stdlib `sqlite3`만 사용).
  - `delete_feed`는 본 슬라이스 범위 외(T-018B에서 외래키 결정과 함께 추가).

- **touch:**
  - `src/rss_wiki/storage/schema.sql` (수정 — feeds 테이블 3 컬럼 추가)
  - `src/rss_wiki/storage/db.py` (수정 — `init_db`에 ALTER TABLE 마이그레이션 로직 추가)
  - `src/rss_wiki/storage/repo.py` (수정 — 4 함수 추가)
  - `tests/test_storage_repo.py` (수정 — 7 케이스 추가)

- **참고:**
  - PRD §11 `feeds` 테이블 스키마 표 — `enabled`/`last_fetched_at`/`updated_at` 명시. `title`은 기존 `name` 컬럼으로 매핑(자체 결정).
  - PRD §13 피드 CRUD — `enabled` 토글, 연속 실패 카운트 리셋이 본 슬라이스의 repo 함수로 충족.
  - 후속 슬라이스 T-018B에서 `delete_feed` + 외래키 결정(메타 스냅샷 컬럼 추가) + `bootstrap_feeds_from_toml` 처리.

### [x] T-015I 운영 안내 (`main.py` 진입점 + `pyproject.toml [project.scripts]` + `README.md`) — M6 마지막 슬라이스 (PASS 146/146, 2026-05-05)
- **목표:** PRD §5 일간 파이프라인과 §11 "피드 추가/삭제는 설정 파일 편집"을 운영자가 실제로 등록·실행할 수 있는 형태로 마무리한다. T-015H에서 완성한 `cli.main()`을 (a) 패키지 진입점(`main.py`)에 연결하고, (b) `pyproject.toml`에 `[project.scripts]`로 등록해 `rss-wiki` 명령으로 호출 가능하게 만들고, (c) `README.md`에 설치/설정/사용법/cron·launchd 등록/트러블슈팅을 정리한다. 본 슬라이스 완료 시 M6 종료, 모든 마일스톤 완료.

- **acceptance:**
  - **`main.py` 수정** — 기존 `def main(): print("Hello from rss-wiki!")` 본문을 제거하고 `rss_wiki.cli.main`을 호출하는 얇은 진입점으로 교체.
    ```python
    from rss_wiki.cli import main as cli_main


    if __name__ == "__main__":
        raise SystemExit(cli_main())
    ```
    - `raise SystemExit(...)`로 exit code 전파(쉘에서 `$?` 확인 가능).
    - `python main.py daily` 호출이 `rss-wiki daily`와 동등하게 동작.
    - 기타 함수 정의/print 문 추가 금지.
  - **`pyproject.toml` 수정** — 기존 `[project]`/`[project.optional-dependencies]`/`[tool.setuptools.packages.find]`/`[tool.pytest.ini_options]` 섹션 사이의 적절한 위치(`[project.optional-dependencies]` 앞 또는 뒤)에 다음 테이블 추가.
    ```toml
    [project.scripts]
    rss-wiki = "rss_wiki.cli:main"
    ```
    - 단 1개 엔트리. 별도 `rss-wiki-daily`/`rss-wiki-weekly` 분리 미도입(서브커맨드로 충분).
    - 기존 의존성/패키지 디스커버리 설정 변경 금지.
  - **`README.md` 신규 작성** — 빈 파일이므로 처음부터 작성. 한국어, GitHub Flavored Markdown.
    - **섹션 1: 개요** — RSS Wiki가 무엇인지 1~2 단락. PRD §1 "수십 개의 RSS 피드를 자동으로 수집·요약·분류하여 AI 큐레이팅 매거진으로 발행" 인용 수준의 요약.
    - **섹션 2: 요구사항** — Python 3.12 이상(`pyproject.toml` `requires-python = ">=3.12"`), Claude CLI(`claude` 명령) 인증 완료(PRD §10), `uv` 권장(또는 `pip`).
    - **섹션 3: 설치**
      ```bash
      git clone <repo>
      cd rss-wiki
      uv sync
      ```
      또는 `pip install -e .`. 설치 후 `rss-wiki --help` 동작 확인.
    - **섹션 4: 피드 설정 (`feeds.toml`)** — `cp feeds.example.toml feeds.toml` 가이드 + `[[feed]]` 형식 예시 표기 + 피드 추가/삭제는 파일 편집(PRD §11). 형식은 `feeds.example.toml`과 일치.
    - **섹션 5: 사용법**
      - `rss-wiki daily` — 매일 발행. 일간 매거진 + 인덱스 갱신. 금요일이면 주간 자동 발행, 매월 마지막 금요일이면 월간 자동 발행.
      - `rss-wiki weekly --end-date 2026-05-08` — 주간 매거진 단독 발행(트리거 우회).
      - `rss-wiki monthly --end-date 2026-05-29` — 월간 매거진 단독 발행(트리거 우회).
      - 전역 옵션: `--db data/rss-wiki.db`(SQLite 경로), `--feeds feeds.toml`(피드 설정 경로), `--output output`(마크다운 출력 디렉터리). 기본값은 모두 현재 디렉터리 기준.
    - **섹션 6: 자동 트리거 동작** — PRD §5 그대로. daily 호출 시점이 금요일이면 weekly 자동 추가, 그날이 그 달 마지막 금요일이면 monthly까지 추가. weekly/monthly 단독 서브커맨드는 트리거 판정 우회. 트리거 판정은 `cli.is_friday`/`cli.is_last_friday_of_month`(stdlib `calendar.monthrange` 기반).
    - **섹션 7: 자동화 등록**
      - **cron(매일 12:00)** — PRD §5 동작 흐름과 일치하는 시간.
        ```cron
        0 12 * * * cd /Users/<user>/rss-wiki && /Users/<user>/.local/bin/uv run rss-wiki daily >> logs/rss-wiki.log 2>&1
        ```
        `which uv`로 절대경로 확인 안내. `crontab -e` 편집 안내.
      - **macOS launchd 예시** — `~/Library/LaunchAgents/com.user.rss-wiki.plist`.
        ```xml
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
            <key>Label</key>
            <string>com.user.rss-wiki</string>
            <key>ProgramArguments</key>
            <array>
                <string>/Users/&lt;user&gt;/.local/bin/uv</string>
                <string>run</string>
                <string>rss-wiki</string>
                <string>daily</string>
            </array>
            <key>WorkingDirectory</key>
            <string>/Users/&lt;user&gt;/rss-wiki</string>
            <key>StartCalendarInterval</key>
            <dict>
                <key>Hour</key>
                <integer>12</integer>
                <key>Minute</key>
                <integer>0</integer>
            </dict>
            <key>StandardOutPath</key>
            <string>/Users/&lt;user&gt;/rss-wiki/logs/rss-wiki.log</string>
            <key>StandardErrorPath</key>
            <string>/Users/&lt;user&gt;/rss-wiki/logs/rss-wiki.err</string>
        </dict>
        </plist>
        ```
        등록: `launchctl load ~/Library/LaunchAgents/com.user.rss-wiki.plist`.
    - **섹션 8: 트러블슈팅**
      - **Claude CLI 미인증** — `claude` 명령이 인증 프롬프트를 띄우는 경우. PRD §10 "API 키 관리 불필요(CLI 자체 인증 사용)" — `claude login`(또는 해당 CLI의 인증 절차) 수행 안내. `LLMError` 트레이스백이 운영자에게 노출됨(`cli.main`에서 캐치하지 않음).
      - **`feeds.toml` 미존재** — `cp feeds.example.toml feeds.toml`로 복사 후 편집.
      - **SQLite 경로 권한** — `--db data/rss-wiki.db` 기본값은 현재 작업 디렉터리 기준. 부모 디렉터리는 `cli.main`이 자동 생성하지만 디스크 권한 부족 시 `OSError` 트레이스백 노출.
      - **연속 실패 피드** — PRD §9에 따라 5회 연속 실패 시 매거진 하단 "장애 피드" 섹션에 노출. 피드 URL 변경 또는 제거가 필요.
      - **빈 분석 결과(daily 발행 스킵)** — 미분석 글이 0건이면 daily 매거진 파일 미생성(WARNING 로그), 인덱스 갱신만 수행. 트리거(주간/월간)는 별도 데이터로 동작하므로 영향 없음.
    - **섹션 9: 디렉터리 구조** — `src/rss_wiki/{config,cli,storage,ingest,llm,publish,pipeline}.py` 간략 트리. 산출물 위치(`output/daily-YYYY-MM-DD.md`, `output/weekly-YYYY-Www.md`, `output/monthly-YYYY-MM.md`, `output/index-{kind}-{name}.md`).
    - 분량: 약 100~180줄. 너무 짧으면 운영 가이드 누락, 너무 길면 유지보수 부담.
    - 외부 링크는 안정적인 것만(예: PEP 라벨 미사용, 외부 블로그 인용 금지). PRD/PLAN/JOURNAL 등 docs 내부 파일 링크는 무방.

  - **테스트:** 신규 테스트 파일 추가 없음. 기존 146개 테스트는 회귀 0(146/146 PASS 유지). main.py·pyproject scripts·README는 단위 테스트 대상이 아니며, 다음으로 수동 검증.
    - `uv run python -c "from rss_wiki.cli import main"` 임포트 성공.
    - `uv sync` 후 `uv run rss-wiki --help` 호출 시 argparse 도움말이 출력.
    - `uv run pytest --tb=short` → `146 passed`.

  - **모듈 경계(엄수):**
    - `main.py`는 `from rss_wiki.cli import main`만 import(다른 패키지 직접 import 금지).
    - `pyproject.toml [project.scripts]` 엔트리는 `rss_wiki.cli:main` 단일.
    - `README.md`는 코드 미포함(셸 명령·plist XML·TOML 예시는 운영 안내 목적이라 허용).

- **touch:**
  - `main.py` (수정 — 진입점 본문 교체)
  - `pyproject.toml` (수정 — `[project.scripts]` 테이블 추가)
  - `README.md` (신규 작성 — 빈 파일을 운영 가이드로 채움)

- **참고:**
  - PRD §5 "12:00 RSS 수집 시작 / 13:00 일간 매거진 발행" — cron은 12:00 시작 권장(LLM 분석에 1시간 여유). 사용자가 13:00 발행을 원하면 cron 시각 조정만 안내.
  - PRD §10 "Claude CLI 헤드리스 모드(`claude -p "..."`)" — README 트러블슈팅에 `claude` 명령 인증 절차 안내가 핵심.
  - PRD §11 "별도 설정 파일(YAML 또는 TOML)" — TOML 채택(PRD §12.6)을 README에 명시.
  - **M6 종료 신호:** 본 슬라이스 PASS 시 다음 Planner 사이클이 모든 항목 완료를 확인하면 `docs/DONE` 빈 파일 생성으로 종료. T-016(README 업데이트)는 본 슬라이스에 흡수되어 별도 활성 불필요.

## 완료

### [x] T-015H CLI 엔트리포인트 + 트리거 판정 + 서브커맨드 결선 (`cli.py` 신규) — M6 여덟 번째 슬라이스 (PASS 12/12, 2026-05-05)
- 산출: `src/rss_wiki/cli.py`(신규 — `is_friday`/`is_last_friday_of_month`/`run_daily`/`run_weekly`/`run_monthly`/`main` 6개 함수, argparse 진입점 + 트리거 판정 + 서브커맨드 결선), `src/rss_wiki/storage/repo.py`(`list_unanalyzed_article_ids` 추가 — `summary IS NULL OR summary = ''` + `id ASC` 멱등 회수), `tests/test_cli.py` 12 케이스(트리거 4 + run_daily 3 + run_weekly 1 + run_monthly 1 + main 디스패치 3) + `tests/test_storage_repo.py` 1 케이스 신규 PASS, 전체 **146/146 PASS**, 기존 133 회귀 없음.
- 인계: M6 여덟 번째 슬라이스 완료. CLI 결선층 패턴 확립 — `argv: Sequence[str] | None = None` 시그니처(테스트 주입 가능), `now: date | None` 직접 주입(콜러블 시계 미도입, YAGNI), `cli.main`은 `ValueError`만 캐치(exit 1)하고 `LLMError`/`PromptParseError`/`sqlite3.IntegrityError`/`OSError`는 traceback 전파(데이터 정합성 + 운영자 알림). `conn.commit()` 책임은 `run_daily`/`run_weekly`/`run_monthly` 종료 직전(M6 인터페이스 원칙). 자동 트리거(금요일=주간, 마지막 금요일=월간)는 PRD §5 그대로 daily 흐름 안에 결선. 트리거 판정 함수와 서브커맨드 결선 함수는 모두 `cli.py` 내부에 둠 — `pipeline/triggers.py` 미생성(YAGNI). 다음 사이클 T-015I(운영 안내 — `main.py` 진입점 + `pyproject scripts` + README cron/launchd) 활성화. **M6 마지막 슬라이스.**

### [x] T-015G 월간 매거진 발행 결선 (`pipeline/publish.py` `publish_monthly` 추가) — M6 일곱 번째 슬라이스 (PASS 12/12, 2026-05-05)
- 산출: `src/rss_wiki/pipeline/publish.py`(`publish_monthly(*, conn, end_date, output_dir, runner=None, logger=None) -> Path | None` 추가, import 2종 — `build_monthly_prompt`/`build_monthly_magazine`, 달력월 1일~end_date 조회 → LLM 통합 요약 1회 → 빌드 → 파일 쓰기 → INSERT/링크), `tests/test_pipeline_publish.py` 4 케이스(empty/write/period_label/exclude) 신규 PASS, 전체 **133/133 PASS**, 기존 129 회귀 없음. **storage repo 신규 함수 없음** — `list_articles_published_between`(T-015F 신설) 재사용.
- 인계: M6 일곱 번째 슬라이스 완료. 결선층 패턴(`conn.commit()` 미호출, `LLMError`/`PromptParseError` 결선층 캐치 금지(매거진 1개 = LLM 1회 단위), `output_dir.mkdir(parents=True, exist_ok=True)`, `Path.write_text(encoding="utf-8")`) 완전 준수. period_label은 `end_date[:7]` 슬라이스(`YYYY-MM`)로 zero-pad ISO 자체 보장. start_date는 `date.fromisoformat(end_date).replace(day=1).isoformat()`. 빈 기간 → WARNING + None 반환(파일/INSERT 부작용 0). `articles.summary=""`도 LLM 입력에 포함(단순함 우선, PRD §9 일관). 다음 사이클 T-015H(CLI 엔트리포인트 + 트리거 판정) 활성화.

### [x] T-015F 주간 매거진 발행 결선 (`pipeline/publish.py` `publish_weekly` 추가) — M6 여섯 번째 슬라이스 (PASS 12/12, 2026-05-05)
- 산출: `src/rss_wiki/storage/repo.py`(`list_articles_published_between` 추가, `published_at IS NOT NULL` 가드 + ASC 시간순 정렬, NULL 매거진 누적 제외), `src/rss_wiki/pipeline/publish.py`(`_iso_week_label` 헬퍼 + `publish_weekly(*, conn, end_date, output_dir, runner=None, logger=None) -> Path | None` 함수, import 4종 추가, 직전 7일 양 끝 포함 → LLM 통합 요약 1회 → 빌드 → 파일 쓰기 → INSERT/링크), `tests/test_storage_repo.py` 1 케이스 + `tests/test_pipeline_publish.py` 4 케이스 신규 PASS, 전체 **129/129 PASS**, 기존 124 회귀 없음.
- 인계: M6 여섯 번째 슬라이스 완료. 결선층 패턴(`conn.commit()` 미호출, `LLMError`/`PromptParseError` 결선층 캐치 금지(매거진 발행 단위가 LLM 호출 1회 단위), `output_dir.mkdir(parents=True, exist_ok=True)`, `Path.write_text(encoding="utf-8")`) 완전 준수. period_label은 ISO 주차(`YYYY-Www`) zero-pad 보장, 발행일(end_date) 기준. `Callable` 미사용 import는 본 슬라이스에서 `runner: Callable[[str], str] | None`로 사용 전환되어 자연 해소(T-015D REVIEW 인계 정리). 빈 기간 → WARNING + None 반환(파일/INSERT 부작용 0). `articles.summary=""`도 LLM 입력에 포함(단순함 우선, PRD §9 일관). 다음 사이클 T-015G(월간 매거진 발행 결선) 활성화 — `list_articles_published_between` 재사용, `period_label`은 `end_date[:7]`(YYYY-MM), `start_date`는 `date.fromisoformat(end_date).replace(day=1).isoformat()`.

### [x] T-015E 카테고리/태그 인덱스 페이지 갱신 (`pipeline/publish.py` `publish_indexes` 추가) — M6 다섯 번째 슬라이스 (PASS 12/12, 2026-05-05)
- 산출: `src/rss_wiki/storage/repo.py`(`list_tags`/`list_articles_by_category`/`list_articles_by_tag` 3 함수 추가, `published_at DESC NULLS LAST, id DESC` 결정적 정렬), `src/rss_wiki/pipeline/publish.py`(`publish_indexes(*, conn, output_dir, logger=None) -> list[Path]` 함수 + import 5개 추가, 빈 카테고리/태그 WARNING 후 스킵, `output_dir/index-{kind}-{name}.md` 덮어쓰기, 슬래시만 치환), `tests/test_storage_repo.py` 3 케이스 + `tests/test_pipeline_publish.py` 6 케이스 신규 PASS, 전체 **124/124 PASS**, 기존 115 회귀 없음.
- 인계: M6 다섯 번째 슬라이스 완료. 결선층 패턴(`conn.commit()` 미호출, WARNING 격리, `mkdir(parents=True, exist_ok=True)`, `Path.write_text(encoding="utf-8")`) 완전 준수. 인덱스 파일은 SQLite로부터 매번 전체 재생성하는 결과 캐시 성격(PRD §8 재생성성 자체 결정). `IndexEntry`에 `tags` 필드 미포함 + 인덱스에는 `failing_feeds` 미수용(T-014 인계 유지). `publish.py:6`의 `Callable` import는 본 슬라이스에서도 미사용 — T-015F에서 `runner` 인자에 사용되므로 자연 해소될 예정. 다음 사이클 T-015F(주간 매거진 발행 결선) 활성화.

### [x] T-015D 일간 매거진 발행 결선 (`pipeline/publish.py` 신규) — M6 네 번째 슬라이스 (PASS 12/12, 2026-05-05)
- 산출: `src/rss_wiki/pipeline/publish.py`(`publish_daily(*, conn, result: AnalyzeResult, output_dir: Path, date: str, logger=None) -> Path`: 빈 `analyzed_ids`/카테고리 미할당 시 `ValueError`, 카테고리별 그룹화(name ASC 정렬상 첫 카테고리만) + `build_daily_magazine` + 파일 쓰기 + `magazines` INSERT + `magazine_articles` 링크), `src/rss_wiki/storage/repo.py`(`list_categories_for_article`/`list_tags_for_article` 2 함수 추가 — JOIN + name ASC 정렬), `tests/test_pipeline_publish.py` 7 케이스 + `tests/test_storage_repo.py` 2 케이스 신규 PASS, 전체 **115/115 PASS**, 기존 106 회귀 없음.
- 인계: M6 네 번째 슬라이스 완료. 결선층 패턴(`conn.commit()` 미호출, WARNING 격리, `Path.write_text(encoding="utf-8")`, `mkdir(parents=True, exist_ok=True)`) 완전 준수. 카테고리 미할당 글은 매거진에서 스킵하되 `magazine_articles` 미링크(included_ids에서 제외). `failing_feeds` 조회는 결선층 책임. **소수점 관찰:** `publish.py:6`의 `Callable` import는 본 슬라이스에서 미사용 — T-015E 이후에도 사용처가 없으면 제거 권장(REVIEW 메모). 다음 사이클 T-015E(인덱스 갱신) 활성화.

### [x] T-015C LLM 분석 결선 (`pipeline/llm.py` 신규) — M6 세 번째 슬라이스 (PASS 12/12, 2026-05-05)
- 산출: `src/rss_wiki/pipeline/llm.py`(`AnalyzeStats`/`AnalyzeResult` frozen dataclass + `analyze_articles(*, conn, article_ids, runner=None, logger=None) -> AnalyzeResult`. `LLMError`/`PromptParseError` 글 단위·트렌드 단위로 격리, 그 외 예외 전파. `analyzed_article_ids`는 정렬 튜플), `src/rss_wiki/storage/repo.py`(3 함수 추가: `list_categories`/`list_articles_by_ids`/`update_article_summary` + `Sequence` import 추가), `tests/test_pipeline_llm.py` 7 케이스 + `tests/test_storage_repo.py` 3 케이스 신규 PASS, 전체 **106/106 PASS**, 기존 96 회귀 없음.
- 인계: M6 세 번째 슬라이스 완료. `runner=None`이면 `_runner = call_claude` 직접 할당(`call_claude(prompt, runner=...)` 키워드 미노출 — 단순함 우선). 트렌드 그룹화 키는 `analysis.category.strip().lower()` — DB 저장 정규화는 `upsert_category`가 단일 진실 원천(M2 패턴 유지). `conn.commit()` 미호출(트랜잭션 호출자 책임). 다음 사이클 T-015D(`pipeline/publish.py` 일간 매거진 발행 결선) 활성화.

### [x] T-015B 일간 수집 다피드 순회 + 통계 + 실패 격리 (`pipeline/ingest.py` `run_daily_ingest`) (PASS 12/12, 2026-05-05)
- 산출: `src/rss_wiki/pipeline/ingest.py`(`IngestStats` frozen dataclass + `run_daily_ingest` 함수: `upsert_feed` → `_fetcher` try/except `FetchError` 격리 → `record_feed_{success,failure}` → entry 위임), `tests/test_pipeline_ingest.py` 6 케이스 추가 PASS, 전체 96/96 PASS, 기존 90 회귀 없음.
- 인계: M6 두 번째 슬라이스 완료. 비-`FetchError` 예외 전파 정책 확립(데이터 정합성 보호). `extractor` 인자는 `process_entry`에 그대로 전달(중첩 콜러블 생성 금지) — 호출자가 `lambda e: extract_body(e, timeout=t, client=c)`로 주입. WARNING 로깅 lazy `%s` 포맷팅 + `logger` 콜러블 주입 패턴 유지. 다음 사이클 T-015C(`pipeline/llm.py` LLM 분석 결선) 활성화.

### [x] T-015A 일간 수집 단일 entry 처리 (`pipeline/ingest.py` `process_entry`) (PASS 12/12, 2026-05-05)
- 산출: `src/rss_wiki/pipeline/__init__.py`(빈 파일), `src/rss_wiki/pipeline/ingest.py`(`process_entry` 함수, stdlib + ingest/storage 결선층 import만 사용), `tests/test_pipeline_ingest.py` 6 케이스 PASS, 전체 90/90 PASS, 기존 84 회귀 없음.
- 인계: M6 첫 슬라이스 완료. 결선층 패턴 확립 — `Callable` 주입(`extractor`)로 외부 네트워크 비의존, stdlib `logging.getLogger(__name__)` 기본 로거 + `logger` 인자로 호출자 주입 가능, `conn.commit()` 미호출(M2 패턴 유지). T-006 REVIEW 인계("extract_body None 반환 시 URL+이유 로깅") 본 슬라이스에서 완전 해소 — 백로그에서 제거. 다음 사이클 T-015B(`run_daily_ingest` 다피드 순회 + 통계 + 실패 격리) 활성화.


### [x] T-014 카테고리/태그 인덱스 페이지 빌더 (`publish/indexes.py`) (PASS 12/12, 2026-05-05)
- 산출: `src/rss_wiki/publish/indexes.py`(`IndexEntry` frozen dataclass + `build_index` 순수 함수, stdlib only), `src/rss_wiki/publish/daily.py`(미사용 `field` import 제거), `tests/test_publish_indexes.py` 7 케이스 PASS, 전체 84/84 PASS, 기존 77 회귀 없음.
- 인계: M5 마일스톤(매거진/인덱스 마크다운 발행) 전체 완료. `IndexEntry`에 `tags` 필드 미포함 — 카테고리/태그 인덱스에서는 같은 주제 글이 모이므로 표기 중복 회피(정보 모델 단순화). `failing_feeds` 인자 미수용 — PRD §4 후미 "매거진 하단" 정의에 인덱스 미해당. 호출자(T-015D)가 카테고리/태그별 누적 entries를 SQLite에서 조회해 빌더에 전달, 결과 마크다운으로 파일 덮어쓰기 — 정렬은 호출자가 `published_date` 역순으로 수행. T-006 인계(`extract_body` `None` 반환 로깅)는 T-015A로 이관 완료(본 사이클).

### [x] T-013 주간/월간 매거진 빌더 (`publish/{weekly,monthly}.py`) (PASS 77/77, 2026-05-06)
- 산출: `src/rss_wiki/publish/weekly.py`(`SourceArticle` dataclass + `build_weekly_magazine` 순수 함수), `src/rss_wiki/publish/monthly.py`(`build_monthly_magazine` — `SourceArticle`/`FailingFeed` sibling import), `tests/test_publish_weekly.py` 5 케이스 + `tests/test_publish_monthly.py` 3 케이스 PASS, 전체 77/77 PASS, 기존 69 회귀 없음.
- 인계: M5 두 번째 슬라이스 완료. `frozen=True` + `splitlines()` + 빈 컬렉션 시 섹션 자체 누락 패턴 유지. dataclass 재사용은 sibling import(`from .daily import FailingFeed`, `from .weekly import SourceArticle`)로. 통합 요약 본문은 평문 단락(블록인용 없음) — 일간 트렌드 단락 처리와 다름. 다음 사이클 T-014(인덱스 빌더) 활성화 권장. `daily.py:3` 미사용 `field` import 제거는 T-014에서 동반 정리. `failing_feeds` 렌더링 4중 중복 우려는 T-014가 인덱스 페이지에 failing_feeds 미수용으로 결정되어 3중 유지 — `publish/renderer.py` 추출 보류(YAGNI). T-006 인계(`extract_body` `None` 반환 로깅)는 여전히 T-015 백로그.

### [x] T-012 일간 매거진 빌더 (`publish/daily.py`) (PASS 12/12, 2026-05-05)
- 산출: `src/rss_wiki/publish/__init__.py`(빈 파일), `src/rss_wiki/publish/daily.py`(`ArticleCard`/`CategorySection`/`FailingFeed` dataclass 3개 + `build_daily_magazine` 순수 함수, stdlib only), `tests/test_publish_daily.py` 7 케이스 PASS, 전체 69/69 PASS, 기존 62 회귀 없음.
- 인계: M5 첫 슬라이스 완료. publish 모듈은 자체 dataclass + 순수 함수 + stdlib only 패턴 확립(DB/네트워크/파일 IO/subprocess 미접근). `frozen=True` + `splitlines()` 기반 멀티라인 처리 + 빈 컬렉션 시 섹션 자체 누락(빈 섹션 비노출) 패턴은 T-013/T-014에서도 유지. `daily.py:3` 미사용 `field` import는 T-014 또는 별도 정리 슬라이스에서 제거 권장(기능 영향 없음). 다음 사이클 T-013(주간/월간 빌더) 활성화. T-006 인계(`extract_body` `None` 반환 로깅)는 여전히 T-015 백로그.

### [x] T-017 주간/월간 통합 요약 프롬프트 (`llm/prompts.py` 확장) (PASS 12/12, 2026-05-05)
- 산출: `src/rss_wiki/llm/prompts.py`(`_build_period_prompt` 헬퍼 + `build_weekly_prompt`/`build_monthly_prompt` 추가, stdlib only), `tests/test_llm_prompts.py` 5 케이스 추가, 전체 62/62 PASS, 기존 57 회귀 없음.
- 인계: M4 마일스톤(LLM 통합) 전체 완료. 주간/월간 응답 파싱은 호출자(M5 publish 모듈)가 기존 `parse_trend_response` 재사용 — 별도 파서/별칭 미추가(단순함 원칙). 입력은 (title, summary) 페어만 — 본문 미입력은 PRD §4 흐름(일간 요약 → 주월간 통합)과 LLM 컨텍스트 비용 절감 자체 결정. 다음 사이클 M5 진입 권장(T-012 일간 매거진 빌더). T-006 인계(`extract_body` `None` 반환 로깅)는 여전히 T-015 백로그.

### [x] T-011 카테고리별 트렌드 요약 프롬프트 (`llm/prompts.py` 확장) (PASS 12/12, 2026-05-05)
- 산출: `src/rss_wiki/llm/prompts.py`(`build_trend_prompt`/`parse_trend_response` 추가, dead code 2줄 제거, `Mapping` import 추가, stdlib only), `tests/test_llm_prompts.py` 7 케이스(트렌드 5 + 빈 summary/category 거부 2) 추가, 전체 57/57 PASS.
- 인계: 트렌드 프롬프트 패턴 확립 — 자연어 단락 응답이므로 JSON·dataclass 미사용, `PromptParseError` 재사용, 빈 입력은 `ValueError`(도메인 위반과 응답 파싱 오류 분리). 코드 펜스 제거 로직은 두 파서가 인라인으로 보유(헬퍼 추출 없음). T-010 REVIEW 인계(dead code, 빈 summary/category 거부) 정리 완료. T-006 인계(`extract_body` `None` 반환 로깅)는 여전히 T-015 백로그.

### [x] T-010 글 요약/카테고리/태그 프롬프트 (`llm/prompts.py`) (PASS 12/12, 2026-05-05)
- 산출: `src/rss_wiki/llm/prompts.py`(`PromptParseError`/`ArticleAnalysis`/`build_article_prompt`/`parse_article_response`, stdlib only — `json`/`dataclasses`/`typing.Sequence`), `tests/test_llm_prompts.py` 6 케이스 PASS (전체 50/50, 기존 44 회귀 없음).
- 인계: 순수 함수 모듈 원칙 확립(`call_claude`/DB/네트워크/`subprocess` 미접근). 카테고리·태그 lower 정규화는 storage 레이어 위임(M2 인계 패턴 유지). REVIEW 인계 — (a) `prompts.py:58-59` dead code 제거, (b) 빈 summary/category 거부 테스트 2개 보강은 T-011 같은 파일 작업에 포함. T-006 인계(`extract_body` `None` 반환 로깅)는 여전히 T-015 백로그.

### [x] T-009 Claude CLI subprocess 래퍼 (`llm/client.py`) (PASS 12/12, 2026-05-05)
- 산출: `src/rss_wiki/llm/{__init__.py,client.py}`(`LLMError`/`LLMTimeoutError`/`DEFAULT_TIMEOUT=60.0`/`call_claude`, stdlib subprocess만 사용), `tests/test_llm_client.py` 4 케이스 PASS (전체 44/44).
- 인계: `runner` 주입 패턴으로 외부 바이너리 비의존 단위 테스트 확립. JSON 파싱은 본 모듈 미포함 — T-010 `prompts.py` 책임. `LLMError`/`LLMTimeoutError`(상속)로 호출자가 재시도 정책 분기 가능. T-006 인계(파이프라인 로깅)는 여전히 T-015 백로그.

### [x] T-008 연속 실패 카운터 (`ingest/failures.py`) + storage 갱신 함수 (PASS 12/12, 2026-05-05)
- 산출: `src/rss_wiki/ingest/failures.py`(`FAILURE_THRESHOLD=5`+`is_failing`), `src/rss_wiki/storage/repo.py`(3 함수 추가: `record_feed_success`/`record_feed_failure`/`list_failing_feeds`), `tests/test_ingest_failures.py` 3 케이스 + `tests/test_storage_repo.py` 3 케이스 추가 PASS (전체 40/40).
- 인계: M3 마일스톤 전체 완료. 임계값 단일 진실 원천은 `failures.FAILURE_THRESHOLD`이고 `repo.list_failing_feeds(threshold=5)`는 단방향 의존성 유지를 위한 안전망 — 향후 임계값 변경 시 두 위치 동시 갱신 필요(PLAN.md M3 메모 참조).

### [x] T-007 URL 정규화 + 해시 + 중복 판정 키 (`ingest/dedupe.py`) (PASS 12/12, 2026-05-05)
- 산출: `src/rss_wiki/ingest/dedupe.py`(`TRACKING_PARAM_PREFIXES`/`TRACKING_PARAM_NAMES`/`normalize_url`/`url_hash`/`title_hash`), `tests/test_ingest_dedupe.py` 6 케이스 PASS (전체 34/34).
- 인계: 64자 hex 출력이 `repo.get_article_by_url_hash`/`repo.get_article_by_title_hash`(T-004)와 직접 호환. 순수 함수 모듈로 도메인 예외 생략. 후속 사이클에서 trailing slash 통일이 필요해지면 보강.

### [x] T-006 본문 추출기 (`ingest/extractor.py`) — trafilatura + RSS summary 폴백 (PASS 11/12, 2026-05-05)
- 산출: `src/rss_wiki/ingest/extractor.py`(`ExtractError`+`extract_body`), `tests/test_ingest_extractor.py` 4 케이스 PASS (전체 28/28).
- 인계: 함수형 + `httpx.Client | None` 주입 + DB 미접근 패턴 유지. 운영 시 실패 추적은 후속 T-015A(파이프라인 결선 첫 슬라이스)에서 호출자가 `None` 반환을 탐지·로깅하는 래퍼로 보완 — 본 사이클 T-015A acceptance에 통합 완료. `except Exception: pass` 패턴은 향후 `ExtractError`로 구체화 권장.

### [x] T-005 RSS 수집기 (`ingest/fetcher.py`) (PASS 12/12, 2026-05-05)
- 산출: `src/rss_wiki/ingest/{__init__.py,fetcher.py}`(`FeedEntry`+`FetchError`+`fetch_feed`), `tests/test_ingest_fetcher.py` 4케이스 PASS (전체 24/24).
- 인계: T-006 extractor도 동일한 의존성 주입(`httpx.Client | None`) + 도메인 예외 + DB 미접근 + raise from e 체인 패턴 유지. `FeedEntry.summary`는 빈 문자열이 `None`으로 정규화된 상태이므로 polback에서 `if entry.summary:` 한 줄로 검사 가능.

### [x] T-004B categories/tags/magazines CRUD (`storage/repo.py`) (PASS 12/12, 2026-05-05)
- 산출: `src/rss_wiki/storage/repo.py`(6개 함수 추가: upsert_category/upsert_tag/link_article_category/link_article_tag/insert_magazine/link_magazine_article), `tests/test_storage_repo.py` 6 케이스 추가 PASS (전체 20/20).
- 인계: 함수형 + Connection 첫 인자 + IntegrityError 가공 없이 전파 + stdlib only 패턴을 후속 모듈에서도 유지.

### [x] T-004 feeds + articles CRUD (`storage/repo.py`) (PASS 12/12, 2026-05-05)
- 산출: `src/rss_wiki/storage/repo.py`(5개 함수: upsert_feed/get_feed_by_url/insert_article/get_article_by_url_hash/get_article_by_title_hash), `tests/test_storage_repo.py` 6 케이스 PASS (전체 14/14).
- 인계: T-004B에서 동일 인터페이스 패턴(`Connection` 첫 인자, 트랜잭션 호출자 책임, IntegrityError 가공 없이 전파) 유지.

### [x] T-003 SQLite 스키마 정의 + DB 초기화 함수 (PASS 12/12, 2026-05-05)
- 산출: `src/rss_wiki/storage/{schema.sql,db.py}`(8개 테이블 + url_hash/title_hash 인덱스, `get_connection`/`init_db`), `tests/test_storage_db.py` 4케이스 PASS (8/8 전체).
- 인계: T-004 CRUD 설계 시 `url_hash`/`title_hash`는 외부 주입 인터페이스로. `get_connection`을 재사용. stdlib만 유지.

### [x] T-002 피드 설정 파일(TOML) 로더 (PASS 11/12, 2026-05-05)
- 산출: `src/rss_wiki/config.py`(FeedConfig + load_feeds), `feeds.example.toml`, `tests/test_config.py` 3케이스 PASS.
- 인계: 파일 IO 에러는 경로 포함 메시지로 래핑(`FileNotFoundError` 등).

### [x] T-001 패키지 골격과 의존성 선언 (PASS 10/12, 2026-05-05)
- 산출: `pyproject.toml` 의존성 선언, `src/rss_wiki/__init__.py`, `tests/test_smoke.py`.
- 인계: pytest src 레이아웃 (`pythonpath = ["src"]`) 설정 완료.

## 백로그 (다음 사이클 후보, 활성화하지 말 것)

(현재 비어 있음 — T-019C가 활성화되어 현재 사이클로 이동, M8 마지막 슬라이스. T-019C PASS 시 PRD §13 전 항목 충족 → 다음 사이클 Planner가 `docs/DONE` 발행.)

### M8 PASS 후 DONE 발행 조건
- T-019A·B·C 모두 `[x]` PASS + PRD §13 신규 요구가 코드/문서/테스트에 반영됨을 다음 사이클 Planner가 점검 → `docs/DONE` 빈 파일 발행으로 프로젝트 종료 신호.
