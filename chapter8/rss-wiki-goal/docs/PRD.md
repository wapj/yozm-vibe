# RSS Wiki — PRD

> 작성일: 2026-04-22
> 상태: v0.1 (MVP 설계 확정)

## 1. 개요

### 1.1 한 줄 정의

RSS 리더의 수집 기능에 LLM(Claude CLI `-p` 모드)을 결합하여, 여러 피드에서 수집한 글을 자동으로 요약·분류하고, **주제별로 누적되는 위키 페이지**를 자동 생성하는 개인용 웹 도구.

### 1.2 문제

매일 여러 RSS 피드에서 30+개의 새 글이 쏟아진다. 전부 읽기 어렵고, 놓치는 글이 생기며, 같은 주제의 여러 글이 흩어져 있어 맥락을 잡기 어렵다.

### 1.3 목표

- **매일 30개 글을 읽는 대신** → **10개 내외의 잘 정리된 주제 페이지**를 읽는다.
- 같은 주제의 여러 글이 **하나의 진화하는 위키 페이지**로 통합된다.
- LLM이 카테고리를 자동 제안하고, 사용자가 나중에 상위 카테고리로 재정리할 수 있다.

### 1.4 성공 지표 (개인용 기준)

- 하루 수집량 대비 주제 페이지 수 비율 ≥ 3:1 (30개 → 10개 이하)
- 주제 페이지 재방문 시 "한 번에 맥락 파악 가능"하다고 사용자가 느낌
- Cron 수집·요약 파이프라인이 **사용자 개입 없이** 1주일 이상 안정적으로 돌아감

## 2. 사용자 및 범위

- **사용자**: 개인 1인 (본인). 로컬 머신에서 단독 실행.
- **인증/권한**: 없음. 인터넷에 노출하지 않는 로컬 전용 도구.
- **멀티 유저/팀 공유**: 범위 밖. 아키텍처도 단일 사용자 전제.

## 3. 핵심 기능 (MVP)

MVP에 **반드시** 포함:

1. **피드 구독 관리** — 웹 UI에서 RSS 피드 추가/삭제/비활성화/목록 조회
2. **주기적 자동 수집** — cron 기반 (시간당 1회), 새 글만 식별 후 수집
3. **원문 본문 추출** — RSS가 summary만 제공해도 링크에서 전문 추출 (`trafilatura` 또는 `readability`)
4. **LLM 요약·분류** — Claude CLI `-p` 모드로 글별 요약 + 카테고리 자동 생성
5. **주제별 위키 페이지 자동 재구성** — 수집 배치가 끝날 때마다 해당 카테고리에 속한 글들을 모아 페이지 전체를 재요약/재구성
6. **웹 UI (Jinja2 SSR)**
   - 피드 관리 화면
   - 카테고리 목록 화면 + 각 카테고리의 주제 페이지 조회
   - 키워드 검색 (SQLite FTS5)
7. **카테고리 편집/병합** — LLM이 자동 생성한 카테고리를 사용자가 편집하거나 여러 개를 하나로 병합
8. **다국어 피드 지원** — 한국어·영어 피드 혼재 수용. 요약 출력은 항상 한국어로 통일
9. **읽음/안읽음 상태 추적** — **카테고리(위키 페이지) 단위로만** 추적. 재구성 시 `has_unread_updates=true`, 사용자가 페이지 방문 시 `false`. 개별 글 단위 읽음 상태는 추적하지 않음

## 4. 기술 스택

| 영역          | 선택                                                    | 이유                                                                                                          |
| ------------- | ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| 언어/런타임   | Python 3.11+                                            | RSS·LLM·웹 생태계가 풍부                                                                                      |
| 웹 프레임워크 | FastAPI                                                 | 비동기 I/O, 타입 힌트 기반                                                                                    |
| 템플릿        | Jinja2 (SSR)                                            | JS 프레임워크 없이 간결                                                                                       |
| DB            | SQLite (FTS5 확장)                                      | 단일 파일, 백업·이동 용이, 개인용에 충분                                                                      |
| RSS 파싱      | `feedparser`                                            | 사실상 표준                                                                                                   |
| 본문 추출     | `trafilatura` (1순위) / `readability-lxml` (대체)       | 전문 추출 품질이 우수                                                                                         |
| LLM 호출      | Claude CLI `-p` 모드 (subprocess)                       | 사용자의 Claude Code 구독을 활용, 별도 API 키·비용 관리 불필요                                                |
| 스케줄링      | **`APScheduler`** (FastAPI 앱 내부 BackgroundScheduler) | 시스템 cron 미사용. 앱 실행 중일 때만 수집이 돌아도 충분 (개인용 전제). 배포가 "앱 하나만 실행" 으로 단일화됨 |
| 패키지 관리   | **`uv`**                                                | 빠르고 lock 파일 일관성                                                                                       |

## 5. 아키텍처

```
  ┌────────────┐        ┌────────────────────────────────┐
  │   cron     │ ──▶    │  Fetcher (feedparser)          │
  │ (hourly)   │        └────────────┬───────────────────┘
  └────────────┘                     │ 새 글 URL 목록
                                     ▼
                       ┌─────────────────────────────────┐
                       │  Article Extractor (trafilatura)│
                       └────────────┬────────────────────┘
                                    │ 원문 텍스트
                                    ▼
                       ┌─────────────────────────────────┐
                       │  LLM Summarizer (claude -p)     │
                       │  · 개별 글 요약 + 카테고리 제안 │
                       └────────────┬────────────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────────────┐
                       │  SQLite (articles, feeds,       │
                       │  categories, wiki_pages, FTS5)  │
                       └────────────┬────────────────────┘
                                    │ 배치 종료 시 1회
                                    ▼
                       ┌─────────────────────────────────┐
                       │  Wiki Rebuilder (claude -p)     │
                       │  · 변경된 카테고리의 페이지 전체 │
                       │    재요약/재구성                │
                       └────────────┬────────────────────┘
                                    ▼
                       ┌─────────────────────────────────┐
                       │  FastAPI + Jinja2 (SSR)         │
                       │  · 피드 관리 / 주제 페이지 /    │
                       │    FTS 검색 / 카테고리 편집     │
                       └─────────────────────────────────┘
```

## 6. 데이터 모델 (SQLite 스키마 — 확정)

앱 시작 시 `CREATE TABLE IF NOT EXISTS` 로 그대로 생성. 마이그레이션 도구 없음.

```sql
CREATE TABLE IF NOT EXISTS feeds (
  id                   INTEGER PRIMARY KEY AUTOINCREMENT,
  url                  TEXT NOT NULL UNIQUE,
  title                TEXT,
  is_active            INTEGER NOT NULL DEFAULT 1,         -- 0/1
  last_fetched_at      TEXT,                               -- ISO8601
  consecutive_failures INTEGER NOT NULL DEFAULT 0,
  created_at           TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS categories (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  name            TEXT NOT NULL UNIQUE,
  parent_id       INTEGER REFERENCES categories(id) ON DELETE SET NULL,
  description     TEXT,
  is_user_edited  INTEGER NOT NULL DEFAULT 0,
  merged_into_id  INTEGER REFERENCES categories(id) ON DELETE SET NULL,
  created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_id);

CREATE TABLE IF NOT EXISTS articles (
  id                  INTEGER PRIMARY KEY AUTOINCREMENT,
  feed_id             INTEGER NOT NULL REFERENCES feeds(id) ON DELETE CASCADE,
  url                 TEXT NOT NULL UNIQUE,
  title               TEXT NOT NULL,
  author              TEXT,
  published_at        TEXT,
  raw_summary         TEXT,
  extracted_content   TEXT,
  llm_summary         TEXT,
  primary_category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
  language            TEXT,                                -- 'ko'|'en'|...
  status              TEXT NOT NULL DEFAULT 'ok',          -- 'ok'|'failed'
  fetched_at          TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_articles_feed    ON articles(feed_id);
CREATE INDEX IF NOT EXISTS idx_articles_cat     ON articles(primary_category_id);
CREATE INDEX IF NOT EXISTS idx_articles_pub     ON articles(published_at DESC);

CREATE TABLE IF NOT EXISTS wiki_pages (
  id                         INTEGER PRIMARY KEY AUTOINCREMENT,
  category_id                INTEGER NOT NULL UNIQUE REFERENCES categories(id) ON DELETE CASCADE,
  content_markdown           TEXT NOT NULL DEFAULT '',
  last_rebuilt_at            TEXT,
  articles_count_at_rebuild  INTEGER NOT NULL DEFAULT 0,
  last_seen_at               TEXT,
  has_unread_updates         INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS job_logs (
  id             INTEGER PRIMARY KEY AUTOINCREMENT,
  job_type       TEXT NOT NULL,                            -- 'fetch_feed'|'extract'|'summarize'|'rebuild_wiki'
  target_ref     TEXT,                                     -- feed_id / article_id / category_id
  status         TEXT NOT NULL,                            -- 'ok'|'failed'
  error_message  TEXT,
  attempt_count  INTEGER NOT NULL DEFAULT 1,
  started_at     TEXT NOT NULL,
  finished_at    TEXT
);
CREATE INDEX IF NOT EXISTS idx_joblogs_started ON job_logs(started_at DESC);

-- 전문 검색: articles.title + llm_summary + extracted_content
CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
  title, llm_summary, extracted_content,
  content='articles', content_rowid='id',
  tokenize='unicode61'
);

-- FTS 동기화 트리거
CREATE TRIGGER IF NOT EXISTS articles_ai AFTER INSERT ON articles BEGIN
  INSERT INTO articles_fts(rowid, title, llm_summary, extracted_content)
  VALUES (new.id, new.title, new.llm_summary, new.extracted_content);
END;
CREATE TRIGGER IF NOT EXISTS articles_ad AFTER DELETE ON articles BEGIN
  INSERT INTO articles_fts(articles_fts, rowid, title, llm_summary, extracted_content)
  VALUES ('delete', old.id, old.title, old.llm_summary, old.extracted_content);
END;
CREATE TRIGGER IF NOT EXISTS articles_au AFTER UPDATE ON articles BEGIN
  INSERT INTO articles_fts(articles_fts, rowid, title, llm_summary, extracted_content)
  VALUES ('delete', old.id, old.title, old.llm_summary, old.extracted_content);
  INSERT INTO articles_fts(rowid, title, llm_summary, extracted_content)
  VALUES (new.id, new.title, new.llm_summary, new.extracted_content);
END;
```

**날짜/시간 규칙**: 모든 `_at` 컬럼은 UTC ISO8601 (`datetime('now')` = UTC). 표시 시점에 로컬 타임존 변환.

## 7. 핵심 파이프라인

### 7.1 수집 사이클 (시간당 1회)

**트리거**: `APScheduler.BackgroundScheduler`, cron trigger `hour='*', minute=0`. 앱 시작 시 자동 등록. 동시 실행 방지를 위해 전역 `fetch_lock` (asyncio.Lock) 사용. 수동 트리거는 `POST /api/fetch` 엔드포인트.

**사이클 단계**:

1. `feeds`에서 `is_active=true`인 피드 조회
2. **피드별 최대 5개 병렬**로 feedparser 호출 (`asyncio.Semaphore(5)`), 개별 fetch 타임아웃 30초
3. 피드 내 새 항목 판별 (URL이 `articles`에 없으면 신규)
4. 각 신규 항목에 대해 (순차 처리 — LLM 호출 직렬화):
   - `trafilatura`로 링크에서 본문 추출 (20초 타임아웃). 추출 실패 시 RSS summary로 fallback
   - Claude CLI `-p`로 요약 + 카테고리 제안 (한국어 출력) — §7.2 참조
   - `articles`에 저장
5. 이번 사이클에서 글이 추가된 카테고리 ID 집합 `affected_category_ids` 수집
6. 각 카테고리에 대해 **Wiki Rebuilder** 1회 실행 (순차). 재구성 성공 시 `wiki_pages.has_unread_updates=true`

### 7.2 LLM 호출 패턴 (Claude CLI `-p` 모드)

**호출 방식** (Python `asyncio.create_subprocess_exec`):

```bash
claude -p --output-format text
```

- 프롬프트는 **stdin** 으로 전달 (긴 입력 안전)
- 프롬프트 끝에 항상 다음 문장 포함: `응답은 반드시 유효한 JSON 객체 하나만 출력하세요. 마크다운 코드펜스, 설명, 인사말 일절 금지.`
- Subprocess 타임아웃: **120초**
- 환경변수: 없음 (Claude CLI는 사용자의 구독 컨텍스트 사용)

**JSON 파싱 폴백 체인** (모든 단계 실패 시 에러로 간주):

1. `json.loads(stdout.strip())` 시도
2. 실패 시 ` ```json ... ``` ` 코드펜스 제거 후 재시도
3. 실패 시 정규식 `r'\{[\s\S]*\}'` 로 첫 JSON-like 블록 추출 후 재시도
4. 여전히 실패 시 **프롬프트에 "이전 응답이 JSON이 아니었다. JSON만 출력하라" 를 덧붙여 1회 재호출**
5. 그래도 실패면 `job_logs`에 기록하고 해당 글 이번 사이클에서 **skip** (다음 사이클 재시도 없음 — URL 중복 검사가 재수집 막으므로 `articles`에 `status='failed'` 레코드 삽입)

**지수 백오프** (네트워크/프로세스 레벨 에러에만 적용, JSON 파싱 실패는 위 체인으로 처리):

- 최대 3회, 대기 2s → 4s → 8s
- 대상: subprocess timeout, non-zero exit, stderr에 rate-limit 단서

**두 종류의 프롬프트** (정확한 템플릿은 §16 참조):

1. **ARTICLE_SUMMARIZE_PROMPT** — 입력: 원문 + 기존 카테고리 전체 목록. 출력:
   ```json
   {
     "summary": "한국어 3-5문장 요약",
     "category_name": "기존 목록에서 고른 이름 또는 신규 이름",
     "is_new_category": false,
     "language_detected": "ko"
   }
   ```
2. **WIKI_REBUILD_PROMPT** — 입력: 카테고리명 + 기존 위키 Markdown(있으면) + 이번 배치에 추가된 글들의 요약/제목/링크. 출력: 순수 Markdown 텍스트 (JSON 아님 — 이 프롬프트만 예외, `--output-format text` 그대로 사용). 섹션 구조는 §8.2 에 명시된 형식을 따르도록 프롬프트에 고정.

### 7.3 재요약 트리거 정책

- **수집 배치 종료 시 변경된 카테고리에 대해서만 1회** 재구성
- 같은 카테고리가 동일 사이클 내 여러 번 영향을 받더라도 재구성은 **사이클당 1회** (중복 방지)
- 동일 카테고리의 연속된 사이클 간 재구성은 허용 (새 글이 있으면 매 시간 1회까지)

## 8. 카테고리 / 위키 페이지 전략

### 8.1 Bootstrapping 및 카테고리 정규화 (결정사항)

- **초기**: 카테고리 테이블 빈 상태에서 시작
- **LLM 프롬프트에 항상 기존 카테고리 전체 목록을 주입**. 프롬프트는 "이 목록에 의미적으로 맞는 항목이 있으면 반드시 재사용하고, 정말 없을 때만 새 이름을 제안하라" 고 명시
  - 이로써 "AI" / "인공지능" / "ML" 이 따로 생성되는 빈도를 줄임 (완전 방지는 불가능)
  - **자동 카테고리 병합/탐지 로직은 구현하지 않음**. LLM의 목록 인지에만 의존
- **사용자 수동 병합**: UI에서 카테고리 A를 B로 병합. 내부적으로 `categories.merged_into_id=B`, 속한 `articles`의 `primary_category_id`를 B로 이동, A의 `wiki_pages` 삭제, B의 위키 재구성 트리거
- **상위 카테고리**: 사용자가 UI에서 `parent_id` 지정. 2단계 트리 한정 (부모의 부모는 없음 — 구현 단순화). 첫 화면은 최상위 카테고리만 나열하고 클릭 시 하위로 드릴다운

### 8.2 위키 페이지 재구성 방식 (증분 전략)

카테고리 하위 글이 수백 개 쌓여도 토큰 한계를 넘지 않도록 **증분(incremental) 재구성**:

**입력 구성**:

- `previous_wiki_markdown`: `wiki_pages.content_markdown` 이 있으면 그대로, 없으면 빈 문자열
- `new_articles`: **이번 배치에서 해당 카테고리에 추가된 글만** (title, url, llm_summary, published_at)
- `existing_recent_articles`: 기존 글 중 최신 10개 (컨텍스트 유지용, title + 1줄 요약만)

**토큰 예산 가드**: 입력 총 길이가 100,000자를 초과하면 `new_articles` 는 모두 넣되 `existing_recent_articles` 를 5개로 축소. 그래도 넘으면 3개로. 그래도 넘으면 0개.

**최초 빌드 (previous가 빈 문자열일 때)**: `existing_recent_articles` 대신 해당 카테고리의 전체 글 중 최신 20개를 입력에 포함.

**LLM에 강제하는 출력 Markdown 구조** (프롬프트에 명시):

```
# {카테고리명}

## 한줄 요약
(이 주제에 대한 현재까지의 맥락을 1-2문장으로)

## 핵심 내용
(여러 글을 통합한 한국어 서술, 3-7단락)

## 최근 동향
(이번 배치에서 새로 추가된 내용 하이라이트, 없으면 섹션 생략)

## 참고한 글
- [제목](url) — {발행일} — 한 줄 요약
- ...
(발행일 내림차순)
```

**기존 내용 처리**: `wiki_pages.content_markdown` 덮어쓰기. 버전 이력 저장 없음 (MVP 범위 밖).

### 8.3 카테고리 편집/병합

- 사용자가 UI에서:
  - 카테고리 이름 수정 (`is_user_edited=true`)
  - 여러 카테고리를 하나로 병합 (`merged_into_id` 설정, 속한 글들이 대상 카테고리로 이동)
  - 상위 카테고리 지정

## 9. 웹 UI 화면 구성

| 경로                      | 메서드 | 내용                                                                                                      |
| ------------------------- | ------ | --------------------------------------------------------------------------------------------------------- |
| `/`                       | GET    | 카테고리 목록 (최상위만, `has_unread_updates=true` 상단 정렬). 카테고리 클릭 시 하위로 드릴다운           |
| `/categories/{id}`        | GET    | 주제 위키 페이지 (Markdown 렌더) + 원문 링크 목록. 방문 시 `has_unread_updates=false`, `last_seen_at=now` |
| `/categories/manage`      | GET    | 전체 카테고리 테이블: 이름 수정, 병합, 상위 카테고리 지정 폼                                              |
| `/categories/{id}/rename` | POST   | 이름 수정 (form)                                                                                          |
| `/categories/{id}/merge`  | POST   | `target_id` 로 병합 (글 이동 + 소스 삭제 + 타겟 rebuild 트리거)                                           |
| `/categories/{id}/parent` | POST   | `parent_id` 지정/해제                                                                                     |
| `/feeds`                  | GET    | 피드 목록 + 추가/삭제/비활성화 폼                                                                         |
| `/feeds/add`              | POST   | URL 추가 (중복 시 409)                                                                                    |
| `/feeds/{id}/toggle`      | POST   | `is_active` 토글                                                                                          |
| `/feeds/{id}/delete`      | POST   | 삭제 (CASCADE로 articles도 제거)                                                                          |
| `/search?q=...`           | GET    | FTS5 `MATCH` 키워드 검색 결과 (제목/요약/본문 하이라이트)                                                 |
| `/logs`                   | GET    | `job_logs` 최근 200건                                                                                     |
| `/api/fetch`              | POST   | 수동 수집 트리거 (mutex 걸려 있으면 409)                                                                  |

인터랙션은 Jinja2 + 최소한의 HTML form. JS 프레임워크 없음.

## 10. 실패 처리 / 관측성

- **재시도 정책**: RSS fetch, 본문 추출, LLM 호출 모두 **지수 백오프 최대 3회**
- **로깅**: 모든 실패는 `job_logs` 테이블 + stderr
- **피드 격리 정책**: MVP에서는 실패해도 자동 비활성화 **하지 않음** (수동 비활성화만). 향후 확장에서 "연속 N회 실패 시 quarantine" 고려
- **실패 로그 페이지**: `/logs` 는 MVP에 **포함**. `job_logs` 최근 200건을 테이블로 렌더 (status, job_type, target_ref, error_message, started_at). 필터 없음.

## 11. 비기능 요구사항

- **배포**: 로컬 단일 머신. Docker는 선택 사항
- **백업**: SQLite 파일 복사 + `feeds` 테이블을 주기적으로 OPML export (향후 기능)
- **성능**: 개인용이므로 동시성 낮음. 피드 30개, 하루 글 50개 정도 가정
- **프라이버시**: 외부로 보내는 것은 LLM 입력(글 본문·요약)뿐. DB는 로컬에만 존재
- **보안**: 외부 노출 없음. `127.0.0.1` 바인딩 전제

## 12. Out of Scope (MVP 제외)

- 다중 사용자/인증/권한
- 의미 검색(임베딩 기반) — MVP는 FTS5만
- 실시간 푸시/알림
- 위키 페이지 버전 이력 (재구성은 덮어쓰기)
- OPML import/export (향후 확장)
- 피드 실패 자동 격리
- 모바일 최적화 UI (데스크톱 우선)
- 공유·댓글·북마크
- 임베딩 기반 유사 기사 병합 (URL 중복만 검사)

## 13. 향후 확장 후보

- OPML import (기존 RSS 리더 마이그레이션)
- 의미 검색 (sqlite-vec 또는 pgvector)
- 연속 실패 피드 자동 quarantine + 복구 UI
- 위키 페이지 diff 뷰어 (재구성 이력)
- 사용자 관심사 기반 스코어링 ("내가 읽는 것 학습")
- 원문 전체 아카이브(오프라인 읽기)

## 14. 운영 상수 (Ralph 루프 구현 시 이 값 그대로 사용)

| 항목                                 | 값                                                            |
| ------------------------------------ | ------------------------------------------------------------- |
| 수집 주기                            | `APScheduler` cron trigger `hour='*', minute=0` (매시 정각)   |
| 동시성 제어                          | 전역 `asyncio.Lock`, fetch 중복 방지                          |
| 피드 fetch 병렬도                    | 5 (`asyncio.Semaphore(5)`)                                    |
| 피드 fetch 타임아웃                  | 30초                                                          |
| 본문 추출 타임아웃                   | 20초                                                          |
| Claude CLI subprocess 타임아웃       | 120초                                                         |
| LLM 지수 백오프                      | 최대 3회, 2s → 4s → 8s                                        |
| Wiki 재구성 입력 글자 상한           | 100,000자. 초과 시 `existing_recent_articles` 축소 (10→5→3→0) |
| 최초 Wiki 빌드 시 포함 기사 수       | 최신 20개                                                     |
| 증분 Wiki 빌드 시 기존 기사 컨텍스트 | 최신 10개 (제목+1줄)                                          |
| 카테고리 계층                        | 2단계 고정 (root → leaf)                                      |
| 읽음 상태 단위                       | 카테고리(위키 페이지)만                                       |
| 중복 판별                            | `articles.url` UNIQUE 제약만                                  |
| DB 파일 경로                         | `./data/rss-wiki.db`                                          |
| 로그 파일 경로                       | `./data/logs/rss-wiki.log` (+ `job_logs` 테이블)              |
| 바인딩 주소                          | `127.0.0.1:8000`                                              |
| LLM 출력 언어                        | 한국어로 통일 (프롬프트에 명시)                               |

### 14.1 프로젝트 디렉토리 레이아웃 (구현 시 이 구조대로 생성)

```
rss-wiki/
├── pyproject.toml
├── uv.lock
├── README.md
├── docs/
│   └── PRD.md
├── data/                     # 런타임 생성, .gitignore
│   ├── rss-wiki.db
│   └── logs/rss-wiki.log
├── src/rss_wiki/
│   ├── __init__.py
│   ├── main.py               # FastAPI app entrypoint
│   ├── config.py             # 상기 운영 상수
│   ├── db.py                 # SQLite 연결, 스키마, 마이그레이션
│   ├── models.py             # Pydantic/dataclass 모델
│   ├── scheduler.py          # APScheduler 등록
│   ├── pipeline/
│   │   ├── fetcher.py        # feedparser 래퍼
│   │   ├── extractor.py      # trafilatura 래퍼
│   │   ├── llm.py            # claude -p subprocess + JSON 파싱 폴백
│   │   ├── summarizer.py     # 개별 글 요약/분류
│   │   └── rebuilder.py      # 위키 페이지 재구성
│   ├── web/
│   │   ├── routes.py         # FastAPI 라우터
│   │   └── templates/        # Jinja2
│   └── prompts/
│       ├── article_summarize.txt
│       └── wiki_rebuild.txt
└── tests/
```

### 14.2 실행 명령

- 개발 실행: `uv run uvicorn rss_wiki.main:app --host 127.0.0.1 --port 8000 --reload`
- 프로덕션(로컬) 실행: `uv run uvicorn rss_wiki.main:app --host 127.0.0.1 --port 8000`
- DB 초기화: 앱 시작 시 `db.py` 가 `CREATE TABLE IF NOT EXISTS` 실행 (별도 마이그레이션 도구 없음)
- 수동 수집 트리거: UI의 "Fetch now" 버튼 또는 `curl -X POST http://127.0.0.1:8000/api/fetch`

## 15. 프롬프트 템플릿 (고정, Ralph 루프가 이 형식 그대로 구현)

### 15.1 `prompts/article_summarize.txt`

```
당신은 한국어 기술 큐레이터입니다. 아래 글을 읽고 요약과 카테고리를 제안하세요.

[기존 카테고리 목록]
{% for c in existing_categories %}- {{ c.name }}{% if c.description %}: {{ c.description }}{% endif %}
{% endfor %}

규칙:
- 위 목록에 의미적으로 맞는 카테고리가 있으면 반드시 그 이름을 그대로 재사용하세요.
- 정말 어울리는 것이 없을 때만 새 카테고리 이름을 제안하세요 (짧고 일반적인 명사구, 예: "LLM 에이전트", "데이터 엔지니어링").
- 요약은 반드시 한국어로, 3-5문장, 핵심만.

[입력 글]
제목: {{ title }}
원문 URL: {{ url }}
언어: {{ detected_language }}
본문:
{{ content }}

응답은 반드시 유효한 JSON 객체 하나만 출력하세요. 마크다운 코드펜스, 설명, 인사말 일절 금지.
스키마:
{
  "summary": "한국어 3-5문장",
  "category_name": "카테고리 이름",
  "is_new_category": true | false,
  "language_detected": "ko" | "en" | "기타"
}
```

### 15.2 `prompts/wiki_rebuild.txt`

```
당신은 한국어 기술 큐레이터입니다. 하나의 주제에 대한 "진화하는 위키 페이지"를 재작성합니다.

카테고리명: {{ category_name }}

[이전 위키 내용 (있다면 이것을 기반으로 진화시키세요)]
{{ previous_wiki_markdown or "(없음 — 최초 생성)" }}

[이번 배치에서 새로 추가된 글]
{% for a in new_articles %}
- 제목: {{ a.title }}
  URL: {{ a.url }}
  발행일: {{ a.published_at }}
  요약: {{ a.llm_summary }}
{% endfor %}

[기존 글 중 최근 맥락용 (제목+1줄)]
{% for a in existing_recent_articles %}
- {{ a.title }} ({{ a.published_at }}) — {{ a.one_line }}
{% endfor %}

출력 규칙:
- 반드시 한국어.
- 아래 Markdown 구조를 정확히 따를 것.
- "최근 동향" 섹션은 새 글이 있을 때만 포함.
- "참고한 글" 은 이전 위키의 링크 + 이번 배치 링크를 모두 포함, 발행일 내림차순.
- 코드펜스, 설명문, 인사말 금지. Markdown 본문만 출력.

# {{ category_name }}

## 한줄 요약
...

## 핵심 내용
...

## 최근 동향
...

## 참고한 글
- [제목](url) — YYYY-MM-DD — 한 줄 요약
```

## 16. 결정된 내용 요약 (대화 기록)

| 항목          | 결정                                                                |
| ------------- | ------------------------------------------------------------------- |
| 사용 범위     | 개인용 (본인만, 로컬)                                               |
| UI 형태       | FastAPI + Jinja2 SSR 웹 앱                                          |
| LLM           | Claude CLI `-p` 모드 (subprocess)                                   |
| 카테고리 체계 | LLM 자동 생성 → 사용자가 추후 상위 카테고리 정의 + 편집/병합        |
| 수집 주기     | cron 기반 시간당 1회                                                |
| 누적 전략     | 수집 배치 종료 시 LLM이 카테고리 페이지 전체 재구성                 |
| 저장소        | SQLite (FTS5)                                                       |
| 검색          | 키워드 검색만 (FTS5)                                                |
| 원문 처리     | trafilatura/readability로 전문 추출                                 |
| 실패 정책     | 지수 백오프 3회 + 실패 로그                                         |
| 중복 처리     | URL 중복만 검사                                                     |
| 피드 관리     | 웹 UI에서 CRUD                                                      |
| 추가 포함     | 카테고리 편집/병합, 다국어 피드(한국어 요약 통일), 읽음/안읽음 추적 |
