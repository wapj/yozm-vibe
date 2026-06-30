"""E2E 테스트 — TC.md 전체 케이스 구현.

외부 서비스(feedparser, trafilatura, LLM)는 mock 처리.
DB·HTTP·라우팅·템플릿 렌더링은 실제 코드 경로 사용.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 헬퍼
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _insert_feed(db, url="https://example.com/feed", is_active=1):
    db.execute("INSERT INTO feeds(url, is_active) VALUES (?, ?)", (url, is_active))
    db.commit()
    return db.execute("SELECT id FROM feeds WHERE url=?", (url,)).fetchone()["id"]


def _insert_category(db, name="AI", parent_id=None):
    db.execute("INSERT OR IGNORE INTO categories(name, parent_id) VALUES (?, ?)", (name, parent_id))
    db.commit()
    return db.execute("SELECT id FROM categories WHERE name=?", (name,)).fetchone()["id"]


def _insert_article(db, feed_id, url, title, cat_id=None, llm_summary=None):
    db.execute(
        "INSERT INTO articles(feed_id, url, title, llm_summary, primary_category_id) VALUES (?,?,?,?,?)",
        (feed_id, url, title, llm_summary, cat_id),
    )
    db.commit()
    return db.execute("SELECT id FROM articles WHERE url=?", (url,)).fetchone()["id"]


def _insert_wiki(db, cat_id, content="# AI\n내용", has_unread=0):
    db.execute(
        "INSERT INTO wiki_pages(category_id, content_markdown, has_unread_updates) VALUES (?,?,?)",
        (cat_id, content, has_unread),
    )
    db.commit()


def _insert_job_log(db, job_type="fetch_feed", status="ok"):
    db.execute(
        "INSERT INTO job_logs(job_type, status, started_at) VALUES (?,?,datetime('now'))",
        (job_type, status),
    )
    db.commit()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TC-F: 피드 관리
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestFeedManagement:
    """TC-F01 ~ TC-F06"""

    def test_f01_feed_list_empty(self, client):
        """TC-F01: 피드 목록 화면 정상 렌더링 (빈 상태)"""
        resp = client.get("/feeds")
        assert resp.status_code == 200
        assert "피드 관리" in resp.text

    def test_f02_feed_add_success(self, client, app):
        """TC-F02: 피드 추가 정상"""
        resp = client.post(
            "/feeds/add",
            data={"url": "https://example.com/rss"},
            follow_redirects=False,
        )
        assert resp.status_code == 303
        assert resp.headers["location"] == "/feeds"

        db = app.state.db
        row = db.execute("SELECT * FROM feeds WHERE url='https://example.com/rss'").fetchone()
        assert row is not None
        assert row["is_active"] == 1
        assert row["consecutive_failures"] == 0

    def test_f03_feed_add_empty_url(self, client):
        """TC-F03: 피드 추가 — 빈 URL → 400"""
        resp = client.post("/feeds/add", data={"url": "   "})
        assert resp.status_code == 400

    def test_f04_feed_add_duplicate(self, client, app):
        """TC-F04: 피드 추가 — 중복 URL → 409"""
        db = app.state.db
        _insert_feed(db, url="https://dup.com/feed")

        resp = client.post("/feeds/add", data={"url": "https://dup.com/feed"})
        assert resp.status_code == 409

    def test_f05_feed_toggle_active_inactive(self, client, app):
        """TC-F05: 피드 활성/비활성 토글 — 2회 반복"""
        db = app.state.db
        feed_id = _insert_feed(db)

        # 1차 토글: active → inactive
        resp = client.post(f"/feeds/{feed_id}/toggle", follow_redirects=False)
        assert resp.status_code == 303
        row = db.execute("SELECT is_active FROM feeds WHERE id=?", (feed_id,)).fetchone()
        assert row["is_active"] == 0

        # 2차 토글: inactive → active
        client.post(f"/feeds/{feed_id}/toggle", follow_redirects=False)
        row = db.execute("SELECT is_active FROM feeds WHERE id=?", (feed_id,)).fetchone()
        assert row["is_active"] == 1

    def test_f06_feed_delete_cascades_articles(self, client, app):
        """TC-F06: 피드 삭제 + 연관 글 CASCADE"""
        db = app.state.db
        feed_id = _insert_feed(db)
        cat_id = _insert_category(db)
        _insert_article(db, feed_id, "https://example.com/1", "글1", cat_id)
        _insert_article(db, feed_id, "https://example.com/2", "글2", cat_id)

        # 삭제 전: 글 2건 확인
        assert db.execute("SELECT COUNT(*) as c FROM articles WHERE feed_id=?", (feed_id,)).fetchone()["c"] == 2

        resp = client.post(f"/feeds/{feed_id}/delete", follow_redirects=False)
        assert resp.status_code == 303

        # 피드 삭제 확인
        assert db.execute("SELECT id FROM feeds WHERE id=?", (feed_id,)).fetchone() is None
        # CASCADE로 글도 삭제 확인
        assert db.execute("SELECT COUNT(*) as c FROM articles WHERE feed_id=?", (feed_id,)).fetchone()["c"] == 0

    def test_f06b_feed_list_shows_added_feed(self, client, app):
        """TC-F01 연장: 추가된 피드가 목록에 표시됨"""
        db = app.state.db
        _insert_feed(db, url="https://visible.com/rss")

        resp = client.get("/feeds")
        assert resp.status_code == 200
        assert "visible.com" in resp.text


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TC-C: 카테고리 및 위키 페이지
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestCategoryAndWiki:
    """TC-C01 ~ TC-C13"""

    def test_c01_home_empty(self, client):
        """TC-C01: 홈 화면 빈 상태"""
        resp = client.get("/")
        assert resp.status_code == 200
        assert "수집된 카테고리가 없습니다" in resp.text

    def test_c02_home_shows_categories(self, client, app):
        """TC-C02: 홈 — 카테고리 목록 표시"""
        db = app.state.db
        _insert_category(db, "Python")
        _insert_category(db, "DevOps")

        resp = client.get("/")
        assert resp.status_code == 200
        assert "Python" in resp.text
        assert "DevOps" in resp.text

    def test_c03_home_unread_category_sorted_first(self, client, app):
        """TC-C03: 미읽음 카테고리가 상단에 표시"""
        db = app.state.db
        cat_a = _insert_category(db, "읽은카테고리")
        cat_b = _insert_category(db, "안읽은카테고리")
        _insert_wiki(db, cat_a, has_unread=0)
        _insert_wiki(db, cat_b, has_unread=1)

        resp = client.get("/")
        assert resp.status_code == 200
        pos_a = resp.text.index("읽은카테고리")
        pos_b = resp.text.index("안읽은카테고리")
        assert pos_b < pos_a, "미읽음 카테고리가 더 먼저 표시되어야 함"

    def test_c04_category_detail_normal(self, client, app):
        """TC-C04: 카테고리 위키 상세 정상 조회"""
        db = app.state.db
        feed_id = _insert_feed(db)
        cat_id = _insert_category(db, "AI")
        _insert_wiki(db, cat_id, content="# AI\n## 핵심 내용\nAI는 중요합니다.")
        _insert_article(db, feed_id, "https://example.com/ai1", "AI 동향", cat_id, "AI 요약")

        resp = client.get(f"/categories/{cat_id}")
        assert resp.status_code == 200
        assert "AI" in resp.text
        assert "AI 동향" in resp.text

    def test_c05_category_detail_not_found(self, client):
        """TC-C05: 존재하지 않는 카테고리 → 404"""
        resp = client.get("/categories/99999")
        assert resp.status_code == 404

    def test_c06_category_visit_marks_read(self, client, app):
        """TC-C06: 카테고리 방문 시 has_unread_updates → 0"""
        db = app.state.db
        cat_id = _insert_category(db, "미읽음카테고리")
        _insert_wiki(db, cat_id, has_unread=1)

        # 방문 전 확인
        wp = db.execute("SELECT has_unread_updates FROM wiki_pages WHERE category_id=?", (cat_id,)).fetchone()
        assert wp["has_unread_updates"] == 1

        resp = client.get(f"/categories/{cat_id}")
        assert resp.status_code == 200

        # 방문 후: 읽음 처리 확인
        wp = db.execute("SELECT has_unread_updates, last_seen_at FROM wiki_pages WHERE category_id=?", (cat_id,)).fetchone()
        assert wp["has_unread_updates"] == 0
        assert wp["last_seen_at"] is not None

    def test_c07_category_rename_success(self, client, app):
        """TC-C07: 카테고리 이름 수정 → is_user_edited=1"""
        db = app.state.db
        cat_id = _insert_category(db, "원래이름")

        resp = client.post(
            f"/categories/{cat_id}/rename",
            data={"name": "새이름"},
            follow_redirects=False,
        )
        assert resp.status_code == 303

        row = db.execute("SELECT name, is_user_edited FROM categories WHERE id=?", (cat_id,)).fetchone()
        assert row["name"] == "새이름"
        assert row["is_user_edited"] == 1

    def test_c08_category_rename_empty_name(self, client, app):
        """TC-C08: 카테고리 이름 수정 — 빈 이름 → 400"""
        db = app.state.db
        cat_id = _insert_category(db, "이름있는카테고리")

        resp = client.post(f"/categories/{cat_id}/rename", data={"name": "  "})
        assert resp.status_code == 400

    def test_c09_category_set_parent(self, client, app):
        """TC-C09: 카테고리 상위 지정"""
        db = app.state.db
        parent_id = _insert_category(db, "기술")
        child_id = _insert_category(db, "AI")

        resp = client.post(
            f"/categories/{child_id}/parent",
            data={"parent_id": str(parent_id)},
            follow_redirects=False,
        )
        assert resp.status_code == 303

        row = db.execute("SELECT parent_id FROM categories WHERE id=?", (child_id,)).fetchone()
        assert row["parent_id"] == parent_id

        # 홈 화면에서 AI(하위)는 보이지 않고 기술(상위)만 표시
        resp_home = client.get("/")
        assert "기술" in resp_home.text
        assert "AI" not in resp_home.text  # parent_id IS NULL 조건으로 필터

    def test_c10_category_clear_parent(self, client, app):
        """TC-C10: 카테고리 상위 해제 (parent_id → NULL)"""
        db = app.state.db
        parent_id = _insert_category(db, "상위카테고리")
        child_id = _insert_category(db, "하위카테고리", parent_id=parent_id)

        resp = client.post(
            f"/categories/{child_id}/parent",
            data={"parent_id": ""},
            follow_redirects=False,
        )
        assert resp.status_code == 303

        row = db.execute("SELECT parent_id FROM categories WHERE id=?", (child_id,)).fetchone()
        assert row["parent_id"] is None

    def test_c11_category_merge_moves_articles(self, client, app):
        """TC-C11: 카테고리 병합 — 글이 타겟으로 이동, 소스는 merged_into_id 설정"""
        db = app.state.db
        feed_id = _insert_feed(db)
        src_id = _insert_category(db, "소스카테고리")
        tgt_id = _insert_category(db, "타겟카테고리")

        # 소스에 글 2건
        _insert_article(db, feed_id, "https://example.com/s1", "소스글1", src_id)
        _insert_article(db, feed_id, "https://example.com/s2", "소스글2", src_id)

        with patch("rss_wiki.pipeline.rebuilder.call_llm_text", new=AsyncMock(return_value="# 타겟\n내용")):
            resp = client.post(
                f"/categories/{src_id}/merge",
                data={"target_id": str(tgt_id)},
                follow_redirects=False,
            )
        assert resp.status_code == 303

        # 소스 글이 타겟으로 이동
        moved = db.execute(
            "SELECT COUNT(*) as c FROM articles WHERE primary_category_id=?", (tgt_id,)
        ).fetchone()["c"]
        assert moved == 2

        # 소스 카테고리에 merged_into_id 설정
        src_row = db.execute("SELECT merged_into_id FROM categories WHERE id=?", (src_id,)).fetchone()
        assert src_row["merged_into_id"] == tgt_id

    def test_c12_category_merge_self(self, client, app):
        """TC-C12: 카테고리 병합 — 자기 자신 → 400"""
        db = app.state.db
        cat_id = _insert_category(db, "자기자신")

        resp = client.post(
            f"/categories/{cat_id}/merge",
            data={"target_id": str(cat_id)},
        )
        assert resp.status_code == 400

    def test_c13_category_manage_page(self, client, app):
        """TC-C13: 카테고리 관리 화면 정상 렌더링"""
        db = app.state.db
        _insert_category(db, "관리테스트")

        resp = client.get("/categories/manage")
        assert resp.status_code == 200
        assert "관리테스트" in resp.text
        assert "카테고리 관리" in resp.text

    def test_c14_category_detail_shows_children(self, client, app):
        """TC-C14 (추가): 카테고리 상세 — 하위 카테고리 표시"""
        db = app.state.db
        parent_id = _insert_category(db, "부모카테고리")
        child_id = _insert_category(db, "자식카테고리", parent_id=parent_id)

        resp = client.get(f"/categories/{parent_id}")
        assert resp.status_code == 200
        assert "자식카테고리" in resp.text

    def test_c15_merged_category_not_on_home(self, client, app):
        """TC-C15 (추가): 병합된(merged) 카테고리는 홈 목록에 표시되지 않음"""
        db = app.state.db
        src_id = _insert_category(db, "병합된카테고리")
        tgt_id = _insert_category(db, "타겟")
        db.execute("UPDATE categories SET merged_into_id=? WHERE id=?", (tgt_id, src_id))
        db.commit()

        resp = client.get("/")
        assert resp.status_code == 200
        # merged 카테고리는 홈에 표시 안 됨
        assert "병합된카테고리" not in resp.text


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TC-S: 검색
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestSearch:
    """TC-S01 ~ TC-S03"""

    def test_s01_search_no_query(self, client):
        """TC-S01: 빈 쿼리 → 200, 결과 없음"""
        resp = client.get("/search")
        assert resp.status_code == 200
        assert "검색" in resp.text

    def test_s02_search_fts5_match(self, client, app):
        """TC-S02: FTS5 키워드 검색 — 결과 있음"""
        db = app.state.db
        feed_id = _insert_feed(db)
        _insert_article(
            db, feed_id,
            "https://example.com/ai1",
            "AI 기술 동향",
            llm_summary="AI 관련 최신 동향 요약",
        )

        resp = client.get("/search?q=AI")
        assert resp.status_code == 200
        assert "AI 기술 동향" in resp.text

    def test_s03_search_no_result(self, client):
        """TC-S03: 검색 결과 없음"""
        resp = client.get("/search?q=절대없는키워드xyz")
        assert resp.status_code == 200
        assert "검색 결과가 없습니다" in resp.text

    def test_s04_search_special_chars(self, client, app):
        """TC-S04 (추가): FTS5 검색 — 한국어 키워드"""
        db = app.state.db
        feed_id = _insert_feed(db)
        _insert_article(
            db, feed_id,
            "https://example.com/k1",
            "쿠버네티스 운영 가이드",
            llm_summary="쿠버네티스 클러스터 운영 방법",
        )

        resp = client.get("/search?q=쿠버네티스")
        assert resp.status_code == 200
        assert "쿠버네티스" in resp.text

    def test_s05_search_result_count(self, client, app):
        """TC-S05 (추가): 여러 글 중 키워드 매칭 글만 반환"""
        db = app.state.db
        feed_id = _insert_feed(db)
        _insert_article(db, feed_id, "https://example.com/r1", "Python 튜토리얼", llm_summary="Python 기초")
        _insert_article(db, feed_id, "https://example.com/r2", "Rust 입문", llm_summary="Rust 언어 소개")
        _insert_article(db, feed_id, "https://example.com/r3", "Python 고급", llm_summary="Python 심화 내용")

        resp = client.get("/search?q=Python")
        assert resp.status_code == 200
        assert "Python 튜토리얼" in resp.text
        assert "Python 고급" in resp.text
        assert "Rust 입문" not in resp.text


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TC-L: 로그 페이지
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestLogs:
    """TC-L01 ~ TC-L02"""

    def test_l01_logs_empty(self, client):
        """TC-L01: 로그 페이지 빈 상태"""
        resp = client.get("/logs")
        assert resp.status_code == 200
        assert "작업 로그" in resp.text

    def test_l02_logs_show_entries(self, client, app):
        """TC-L02: 로그 항목 표시"""
        db = app.state.db
        _insert_job_log(db, "fetch_feed", "ok")
        _insert_job_log(db, "summarize", "failed")

        resp = client.get("/logs")
        assert resp.status_code == 200
        assert "fetch_feed" in resp.text
        assert "summarize" in resp.text

    def test_l03_logs_limit_200(self, client, app):
        """TC-L03 (추가): 로그 200건 제한"""
        db = app.state.db
        for i in range(220):
            db.execute(
                "INSERT INTO job_logs(job_type, status, started_at) VALUES ('test','ok',datetime('now'))",
            )
        db.commit()

        resp = client.get("/logs")
        assert resp.status_code == 200
        # 200건 초과하는 내용이 그대로 렌더되지 않도록 (페이지 크기 간접 확인)
        count = resp.text.count("test")
        assert count <= 200


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TC-A: API 엔드포인트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestAPI:
    """TC-A01 ~ TC-A02"""

    def test_a01_manual_fetch_no_feeds(self, client):
        """TC-A01: 수동 수집 트리거 — 즉시 /logs로 리다이렉트"""
        resp = client.post("/api/fetch", follow_redirects=False)
        # 백그라운드 실행 후 즉시 303 → /logs
        assert resp.status_code == 303
        assert resp.headers["location"] == "/logs"

    def test_a01b_manual_fetch_already_running(self, client, app):
        """TC-A01b: 이미 수집 중일 때 409"""
        import asyncio
        from rss_wiki.scheduler import _fetch_lock

        async def _check():
            async with _fetch_lock:
                # 잠긴 상태에서 요청
                resp = client.post("/api/fetch", follow_redirects=False)
                assert resp.status_code == 409

        asyncio.get_event_loop().run_until_complete(_check())

    def test_a02_manual_fetch_with_mock_rss(self, client, app):
        """TC-A02: 수동 수집 트리거 — RSS mock으로 글 1건 처리 (BackgroundTask 동기 실행)"""
        db = app.state.db
        feed_id = _insert_feed(db, "https://mock.com/feed")

        mock_feed_result = MagicMock()
        mock_feed_result.bozo = False
        entry = MagicMock()
        entry.get = lambda k, d=None: {
            "link": "https://mock.com/article1",
            "title": "Mock 테스트 글",
            "author": "테스터",
            "published": "2024-01-01",
            "summary": "Mock 요약",
        }.get(k, d)
        mock_feed_result.entries = [entry]
        wiki_content = "# Mock테스트\n\n## 한줄 요약\nMock 관련 내용입니다."

        with (
            patch("rss_wiki.pipeline.fetcher.feedparser.parse", return_value=mock_feed_result),
            patch("rss_wiki.pipeline.extractor.trafilatura.fetch_url", return_value="<html>Mock 본문</html>"),
            patch("rss_wiki.pipeline.extractor.trafilatura.extract", return_value="Mock 추출 본문"),
            patch("rss_wiki.pipeline.llm._run_claude", new=AsyncMock(side_effect=[
                '{"summary": "Mock 글의 한국어 요약입니다.", "category_name": "Mock테스트", "is_new_category": true, "language_detected": "ko"}',
                wiki_content,
            ])),
        ):
            # TestClient는 BackgroundTasks를 응답 전송 후 동기적으로 실행함
            resp = client.post("/api/fetch", follow_redirects=False)

        assert resp.status_code == 303

        # BackgroundTask 완료 후 DB 확인
        article = db.execute("SELECT * FROM articles WHERE url='https://mock.com/article1'").fetchone()
        assert article is not None
        assert article["title"] == "Mock 테스트 글"
        assert article["status"] == "ok"

        cat = db.execute("SELECT * FROM categories WHERE name='Mock테스트'").fetchone()
        assert cat is not None

        wp = db.execute("SELECT * FROM wiki_pages WHERE category_id=?", (cat["id"],)).fetchone()
        assert wp is not None
        assert wp["has_unread_updates"] == 1


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TC-W: 전체 워크플로 (End-to-End 시나리오)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TestWorkflow:
    """전체 흐름 시나리오 테스트"""

    def test_w01_feed_crud_workflow(self, client, app):
        """W01: 피드 추가 → 목록 확인 → 비활성화 → 삭제"""
        db = app.state.db
        url = "https://workflow.com/feed"

        # 1. 추가
        client.post("/feeds/add", data={"url": url})
        feed_id = db.execute("SELECT id FROM feeds WHERE url=?", (url,)).fetchone()["id"]

        # 2. 목록 확인
        resp = client.get("/feeds")
        assert "workflow.com" in resp.text

        # 3. 비활성화
        client.post(f"/feeds/{feed_id}/toggle")
        assert db.execute("SELECT is_active FROM feeds WHERE id=?", (feed_id,)).fetchone()["is_active"] == 0

        # 4. 삭제
        client.post(f"/feeds/{feed_id}/delete")
        assert db.execute("SELECT id FROM feeds WHERE id=?", (feed_id,)).fetchone() is None

    def test_w02_category_wiki_read_workflow(self, client, app):
        """W02: 카테고리 생성 → 위키 방문(읽음) → 홈에서 미읽음 없음"""
        db = app.state.db
        cat_id = _insert_category(db, "읽음워크플로")
        _insert_wiki(db, cat_id, has_unread=1)

        # 홈에서 미읽음 확인
        resp = client.get("/")
        assert "badge-unread" in resp.text  # 미읽음 뱃지

        # 위키 방문
        client.get(f"/categories/{cat_id}")

        # 홈 재방문: 미읽음 마크 사라짐
        resp = client.get("/")
        # has_unread=0이 됐으므로 ★ 없어야 함 (카테고리는 여전히 표시)
        wp = db.execute("SELECT has_unread_updates FROM wiki_pages WHERE category_id=?", (cat_id,)).fetchone()
        assert wp["has_unread_updates"] == 0

    def test_w03_search_after_article_insert(self, client, app):
        """W03: 글 삽입 → 즉시 FTS5 검색 가능"""
        db = app.state.db
        feed_id = _insert_feed(db)

        # 처음엔 검색 결과 없음
        resp = client.get("/search?q=독특한키워드")
        assert "검색 결과가 없습니다" in resp.text

        # 글 삽입
        _insert_article(db, feed_id, "https://example.com/fts1", "독특한키워드 포함 글", llm_summary="설명")

        # 이제 검색 결과 있음
        resp = client.get("/search?q=독특한키워드")
        assert "독특한키워드 포함 글" in resp.text

    def test_w04_category_merge_then_search(self, client, app):
        """W04: 카테고리 병합 후 타겟 카테고리에서 검색 가능"""
        db = app.state.db
        feed_id = _insert_feed(db)
        src_id = _insert_category(db, "소스")
        tgt_id = _insert_category(db, "타겟")
        _insert_article(db, feed_id, "https://example.com/m1", "병합테스트글", cat_id=src_id, llm_summary="병합요약")

        with patch("rss_wiki.pipeline.rebuilder.call_llm_text", new=AsyncMock(return_value="# 타겟\n내용")):
            client.post(f"/categories/{src_id}/merge", data={"target_id": str(tgt_id)})

        # 글이 타겟으로 이동했는지 확인
        row = db.execute("SELECT primary_category_id FROM articles WHERE url='https://example.com/m1'").fetchone()
        assert row["primary_category_id"] == tgt_id

        # 검색에서도 여전히 찾을 수 있어야 함
        resp = client.get("/search?q=병합테스트글")
        assert resp.status_code == 200
        assert "병합테스트글" in resp.text
