# RSS Wiki — TASKS

PRD: docs/PRD.md 기반 구현 목록. 순서대로 진행, 의존성 상위 → 하위.

## 태스크 목록

- [x] T01: 프로젝트 초기 설정 — pyproject.toml, 디렉토리 구조, 의존성 설치 (`uv add fastapi uvicorn jinja2 feedparser trafilatura apscheduler pytest httpx`)
- [x] T02: config.py — PRD §14 운영 상수 모두 Python 상수로 정의
- [x] T03: db.py — SQLite 연결·스키마 초기화 (feeds, categories, articles, wiki_pages, job_logs, articles_fts + 트리거)
- [x] T04: models.py — Pydantic/dataclass 모델 (Feed, Category, Article, WikiPage, JobLog)
- [x] T05: pipeline/fetcher.py — feedparser 래퍼, 신규 URL 판별, asyncio.Semaphore(5), 타임아웃 30초
- [x] T06: pipeline/extractor.py — trafilatura 본문 추출, 실패 시 RSS summary fallback, 타임아웃 20초
- [x] T07: pipeline/llm.py — claude -p subprocess 래퍼, JSON 파싱 폴백 체인(5단계), 지수 백오프 3회
- [x] T08: pipeline/summarizer.py — ARTICLE_SUMMARIZE_PROMPT 적용, 카테고리 upsert
- [x] T09: pipeline/rebuilder.py — WIKI_REBUILD_PROMPT 적용, 증분 재구성, 토큰 예산 가드
- [x] T10: prompts/ — article_summarize.txt, wiki_rebuild.txt (PRD §15 템플릿 그대로)
- [x] T11: scheduler.py — APScheduler BackgroundScheduler, cron hour='*' minute=0, fetch_lock
- [x] T12: web/routes.py — 모든 HTTP 라우트 구현 (PRD §9 표 전체)
- [x] T13: web/templates/ — Jinja2 HTML 템플릿 (index, category_detail, category_manage, feeds, search, logs)
- [x] T14: main.py — FastAPI 앱 엔트리포인트, lifespan으로 DB 초기화·스케줄러 시작/종료
- [x] T15: tests/ — 전체 pytest 통과 검증 (db, config, models, fetcher, extractor, llm, summarizer, rebuilder, routes)
