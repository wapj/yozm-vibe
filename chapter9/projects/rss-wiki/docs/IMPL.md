# IMPL — T-019C

## 처리 항목

**T-019C** 컴포넌트 클래스 부착 + `GET /tags` 인덱스 + active GNB 강조 + 매거진 본문 스타일 — M8 마지막 슬라이스

## 변경 파일 (9개)

| 파일 | 변경 내용 |
|---|---|
| `src/rss_wiki/web/routes_magazines.py` | `GET /tags` 인덱스 라우트 신설(`tags_index`); 기존 6 GET 라우트 `active_nav` 키 주입(`index`→`"magazines"`, `magazines_list`→`"magazines"`, `magazine_detail`→`"magazines"`, `categories_index`→`"categories"`, `category_articles`→`"categories"`, `tag_articles`→`"tags"`) |
| `src/rss_wiki/web/routes_feeds.py` | 3 GET 라우트(`feeds_index`/`feed_new_form`/`feed_edit_form`)에 `active_nav="feeds"` 주입 |
| `src/rss_wiki/web/static/style.css` | `.magazine-body` 스코프 스타일 약 50줄 추가(H1~H4 계층, `p`, `a`/`a:hover`, `code`, `pre`, `pre code`, `blockquote`) |
| `src/rss_wiki/web/templates/list.html` | `<ul><li>` 마크업 → `<div class="card">` 카드 래퍼로 교체 |
| `src/rss_wiki/web/templates/magazine.html` | `<article>` → `<article class="magazine-body">` |
| `src/rss_wiki/web/templates/feeds.html` | 추가 폼 `<button class="btn btn-primary">`, 활성/비활성 `.badge-success`/`.badge-danger`, 수정 링크/토글/리셋/삭제 버튼에 `.btn`/`.btn-danger` 클래스 부착 |
| `src/rss_wiki/web/templates/feed_edit.html` | 저장 버튼 `.btn btn-primary`, 취소 링크 `.btn` |
| `src/rss_wiki/web/templates/feed_new.html` | 추가 버튼 `.btn btn-primary`, 취소 링크 `.btn` |
| `tests/test_web_app.py` | `upsert_tag` import 추가; 신규 7 케이스 추가 |

## 신규 테스트 케이스 (7개)

1. `test_tags_index_empty` — `GET /tags` 200 + "태그" 헤딩 + "아직 항목이 없습니다"
2. `test_tags_index_with_entries` — ai/kotlin 태그 등록 후 `GET /tags` → href + `.card` 클래스 검증
3. `test_active_nav_marks_feeds_link_when_on_feeds_page` — `GET /feeds` → `href="/feeds" class="active"` 포함
4. `test_active_nav_marks_magazines_link_when_on_magazines_page` — `GET /magazines` → `href="/magazines" class="active"` 포함
5. `test_active_nav_marks_tags_link_when_on_tags_page` — `GET /tags` → `href="/tags" class="active"` 포함
6. `test_feeds_html_uses_btn_class` — 피드 등록 후 `GET /feeds` → `class="btn` 마커 포함
7. `test_magazine_body_styles_in_css` — `GET /static/style.css` → `.magazine-body` + `pre` + `blockquote` 포함

## 검증 결과

```
218 passed in 1.51s
```

기존 211 케이스 회귀 0, 신규 7 케이스 모두 PASS → **218/218 PASS**

## 자체 결정

- `GET /tags` 라우트는 `routes_magazines.py`에 배치(`/tags/{name}`과 동일 모듈, 분리 불필요).
- `active_nav` 4값: `magazines`/`categories`/`tags`/`feeds`(`/` 랜딩은 `magazines`).
- POST 라우트는 redirect 반환만 하므로 `active_nav` 미주입.
- `.magazine-body` 스코프로 본문 스타일 격리(GNB/카드 링크 영향 차단).
- 폭 720px는 `.container`가 단일 진실 원천(`.magazine-body` 폭 재정의 안 함).
- `<table>` 매거진 본문 스타일 미추가(T-019A element 정의 재사용, YAGNI).
- 인라인 form `style="display:inline"` 유지(JS 없이 동작 + `.btn` inline-flex 정렬 호환).
