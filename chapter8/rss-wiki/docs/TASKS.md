# RSS Wiki — TASKS

> PRD: docs/PRD.md 기반. 한 세션(약 10~20분) 단위로 쪼갬.
> 상단일수록 의존성 먼저.

## 0. 기초 설정

- [x] 프로젝트 초기화: `uv init --package`로 pyproject 생성, `src/rss_wiki/`, `tests/`, `data/logs/` 디렉토리 및 `.gitignore` 작성, `uv add --dev pytest`로 테스트 러너 설치
- [x] 런타임 의존성 추가: `uv add fastapi "uvicorn[standard]" jinja2 pydantic feedparser trafilatura apscheduler python-multipart markdown`
- [x] 추가 개발 의존성: `uv add --dev pytest-asyncio httpx`

## 1. 설정 / DB

- [x] `config.py`: PRD §14 운영 상수 정의 (DB 경로, 타임아웃, 병렬도 등) + 테스트
- [x] `db.py`: SQLite 연결 팩토리(`get_connection`) + `feeds`, `categories` 테이블 생성 + 테스트
- [x] `db.py`: `articles` 테이블 + 인덱스 + `articles_fts` 가상 테이블 + 트리거 생성 + 테스트
- [x] `db.py`: `wiki_pages`, `job_logs` 테이블 + 인덱스 생성 + 테스트

## 2. 모델

- [x] `models.py`: Pydantic 모델 (Feed, Category, Article, WikiPage, JobLog) + 테스트

## 3. 프롬프트 템플릿

- [x] `prompts/article_summarize.txt` + `prompts/wiki_rebuild.txt` 작성 (PRD §15 그대로) + 렌더 스모크 테스트

## 4. 파이프라인

- [x] `pipeline/llm.py`: Claude CLI subprocess 호출 함수 + 120s 타임아웃 + 지수 백오프(2/4/8s, 최대 3회) + 테스트
- [x] `pipeline/llm.py`: JSON 파싱 폴백 체인 (strip → 코드펜스 제거 → 정규식 → 재호출) + 테스트
- [x] `pipeline/fetcher.py`: feedparser 래퍼(async), Semaphore(5), 30s 타임아웃, 신규 URL 판별 + 테스트
- [x] `pipeline/extractor.py`: trafilatura 래퍼 + 20s 타임아웃 + RSS summary fallback + 테스트
- [x] `pipeline/summarizer.py`: 개별 글 요약/분류 + articles INSERT (status='ok'|'failed') + 카테고리 upsert + 테스트
- [x] `pipeline/rebuilder.py`: 위키 재구성, 입력 100k자 가드(10→5→3→0), 최초 빌드 시 최신 20개 + 테스트
- [x] `pipeline/cycle.py`: 전체 수집 사이클 (fetch → extract → summarize → affected 카테고리 rebuild) + 테스트

## 5. 스케줄러

- [x] `scheduler.py`: APScheduler BackgroundScheduler 등록 (cron hour='*' minute=0) + 전역 `fetch_lock` + 테스트

## 6. Web (FastAPI + Jinja2)

- [x] `web/main.py`: FastAPI 앱 + lifespan(DB init, scheduler start) + Jinja2 환경 + 기본 라우트(/) + 테스트
- [x] `web/routes.py`: 피드 라우트 (GET /feeds, POST /feeds/add, /{id}/toggle, /{id}/delete, 중복 409) + 테스트
- [x] `web/routes.py`: 카테고리 라우트 (GET /, GET /categories/{id} — 방문 시 has_unread_updates=false) + 테스트
- [x] `web/routes.py`: 카테고리 관리 (GET /categories/manage, POST /{id}/rename, /{id}/merge, /{id}/parent) + 테스트
- [x] `web/routes.py`: 검색 (GET /search, FTS5 MATCH) + 테스트
- [x] `web/routes.py`: 로그(GET /logs, 최근 200) + 수동 수집(POST /api/fetch, 409 on lock) + 테스트
- [x] 템플릿: `base.html` + `feeds.html`
- [x] 템플릿: 카테고리 목록(`index.html`) + 상세(`category.html`)
- [x] 템플릿: 관리(`categories_manage.html`) + 검색(`search.html`) + 로그(`logs.html`)

## 7. 마무리

- [x] README.md: 실행 방법 (개발/프로덕션) + PRD §14.2 명령 반영
- [x] 엔드투엔드 스모크: `uv run uvicorn rss_wiki.main:app` 기동 확인 로그 테스트
