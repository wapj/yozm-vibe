# RSS Wiki — PLAN

PRD를 7개 마일스톤으로 분해한다. 각 마일스톤은 코드 디렉터리에 명확한 모듈 책임을 갖는다.

**전체 상태: 모든 마일스톤(M1~M8) 완료(218/218 PASS, 2026-05-06 02:30Z). T-019C PASS 확인으로 M8 종결 — PRD §13 갱신본의 잔여 4 요구(컴포넌트 클래스 통일·매거진 본문 스타일·active GNB 강조·`GET /tags` 인덱스) 모두 충족. PRD §1~13 전 섹션이 코드/문서/테스트에 반영됨을 본 사이클 Planner가 점검 완료 → `docs/DONE` 빈 파일 발행으로 Planner→Generator→Evaluator 사이클 종료 신호 발신.**

## 모듈 책임 (목표 디렉터리 구조)

```
src/rss_wiki/
  config.py          # 피드 설정 파일(TOML) 로딩, 환경 상수
  storage/
    schema.sql       # SQLite DDL
    db.py            # 커넥션, 마이그레이션
    repo.py          # 글/카테고리/태그/매거진 CRUD
  ingest/
    fetcher.py       # RSS 수집 (feedparser + httpx 타임아웃)
    extractor.py     # 본문 추출 (trafilatura), summary 폴백
    dedupe.py        # URL 정규화, 제목 해시 중복 판정
    failures.py      # 피드별 연속 실패 카운트
  llm/
    client.py        # Claude CLI subprocess 래퍼
    prompts.py       # 글 요약/카테고리/태그, 트렌드, 주월간 프롬프트
  publish/
    daily.py         # 일간 매거진 마크다운 빌드
    weekly.py        # 주간 통합 요약
    monthly.py       # 월간 통합 요약
    indexes.py       # 카테고리/태그 인덱스 페이지
    renderer.py      # 공통 마크다운 렌더링 헬퍼 (현재 미생성, 4중 중복 시점에 추출)
  pipeline/          # M6 결선 모듈 (수집/LLM/발행 결선)
    ingest.py        # 단일 entry 처리 → 여러 피드 순회 + 통계
    llm.py           # 글 단위 분석 + 카테고리별 트렌드 결선
    publish.py       # 일간/주간/월간 매거진 + 인덱스 갱신 + 파일 쓰기
  cli.py             # 엔트리포인트 (argparse + 트리거 판정 + daily/weekly/monthly 결선 + web 서브커맨드)
  web/               # M7 FastAPI 웹 인터페이스 (PRD §13)
    __init__.py      # 빈 파일
    app.py           # FastAPI 앱 인스턴스 + DI + 라우트 등록 + WAL 모드
    routes_magazines.py  # 매거진/카테고리/태그 GET 라우트
    routes_feeds.py  # 피드 CRUD GET/POST 라우트 (303 redirect)
    templates/       # Jinja2 템플릿 (base.html, magazine.html, list.html, feeds.html, feed_edit.html, feed_new.html, _flash.html)
    static/          # 정적 자산 (style.css 단일 파일, 디자인 토큰 + 컴포넌트 + GNB + 다크모드)
    markdown.py      # markdown-it-py 래퍼

tests/                # 각 모듈 단위 테스트
output/               # 발행된 마크다운 (gitignore 제외)
feeds.toml            # 피드 부트스트랩 시드 (PRD §11; 운영 SoT는 SQLite feeds 테이블)
```

## 마일스톤

### M1. 프로젝트 골격 & 설정 로더 — ✅ 완료 (T-001, T-002)

- 패키지 디렉터리/`__init__.py` 생성, `pyproject.toml` 의존성 선언.
- 의존성: `feedparser`, `httpx`, `trafilatura`, `pytest` (개발).
- `feeds.toml` 포맷 정의 + 로더 + 단위 테스트.
- 산출: `src/rss_wiki/config.py`, `feeds.example.toml`, `tests/test_config.py`.

### M2. SQLite 스키마 & 저장소 — ✅ 완료 (T-003, T-004, T-004B)

- `articles`, `feeds`, `categories`, `tags`, `article_tags`, `magazines`, `magazine_articles` 등 테이블 정의.
- DDL 파일 + 초기화 함수 + 기본 CRUD.
- 중복 키(URL hash, title hash) 인덱스 포함.
- 산출: `src/rss_wiki/storage/{schema.sql,db.py,repo.py}`, 단위 테스트 (20/20 PASS).
- **확립된 인터페이스 패턴:** `repo.py` 함수는 모두 `sqlite3.Connection`을 첫 인자로 받고 트랜잭션 생명주기는 호출자가 관리한다. 카테고리/태그 이름 정규화는 PRD §12.1에 따라 `strip()` + 소문자화를 storage 레이어에서 수행한다. `IntegrityError`는 가공 없이 전파.

### M3. RSS 수집 / 본문 추출 / 중복 처리 — ✅ 완료 (T-005, T-006, T-007, T-008)

- `fetcher`가 피드별 HTTP 타임아웃으로 RSS 가져오고 항목 파싱.
- `extractor`가 trafilatura로 본문 추출, 실패 시 RSS `summary` 폴백, 둘 다 실패 시 스킵.
- `dedupe`가 URL 정규화(쿼리/UTM 제거)와 제목 해시로 중복 판정.
- `failures`가 피드별 연속 실패 횟수 누적, 임계값(5) 노출.
- 산출: `src/rss_wiki/ingest/*`, 단위 테스트 (40/40 PASS).
- **확립된 인터페이스 패턴(M3):**
  - 외부 IO를 가진 모듈은 호출자가 `httpx.Client`나 콜러블을 주입할 수 있도록 만들어 테스트 시 `httpx.MockTransport`/스텁을 끼울 수 있게 한다(외부 네트워크에 의존하지 않는 단위 테스트).
  - 각 모듈은 자신만의 도메인 예외(`FetchError`, `ExtractError` 등)를 정의하고, 원본 예외를 `raise ... from e`로 체인한다. 운영 시 원인 추적 용이성 확보.
  - DB 접근은 ingest 모듈에서 직접 하지 않는다. ingest는 순수 함수에 가깝게 유지하고 영속성은 호출자(파이프라인)가 storage repo에 위임한다.
- **레이어 단방향 의존성:** `failures.py`(ingest)는 `storage` 미임포트, `repo.py`(storage)는 `ingest` 미임포트. 임계값(`5`)는 `failures.FAILURE_THRESHOLD`를 단일 진실 원천으로 하되, `repo.list_failing_feeds`는 인자 기본값으로 `5`를 중복 적어 단방향 의존성을 깨지 않는다. 일관성은 PLAN 차원에서 보증.

### M4. LLM 통합 (Claude CLI) — ✅ 완료 (T-009, T-010, T-011, T-017)

- `claude -p "..."` subprocess 호출 래퍼(`call_claude`, `LLMError`/`LLMTimeoutError`, `runner` 주입).
- 프롬프트 3종 완성: 글 요약+카테고리+태그(`build_article_prompt`/`parse_article_response`), 카테고리별 트렌드 1단락(`build_trend_prompt`/`parse_trend_response`), 주간/월간 통합 요약(`build_weekly_prompt`/`build_monthly_prompt`).
- 응답 파서: 주간/월간은 `parse_trend_response` 재사용(별도 파서 없음).
- 산출: `src/rss_wiki/llm/{client.py,prompts.py}`, 모킹 기반 테스트(전체 62/62 PASS).
- **확립된 인터페이스 패턴(M4):**
  - subprocess 호출 모듈은 `runner` 콜러블 주입 패턴으로 외부 프로세스 비의존 단위 테스트 보장.
  - 모듈별 도메인 예외(`LLMError`, `LLMTimeoutError`, `PromptParseError`) + `raise ... from e` 체인.
  - `prompts.py`는 순수 함수 모듈(`call_claude`/DB/네트워크/`subprocess`/`storage`/`ingest` 미임포트). 외부 IO는 `client.py` 단독.
  - DB 데이터(기존 카테고리 목록 등)는 호출자(파이프라인)가 storage repo에서 조회해 인자로 전달.
  - 빈 입력 등 도메인 위반은 `ValueError`, 응답 파싱 오류는 `PromptParseError`로 분리.

### M5. 매거진/인덱스 마크다운 발행 — ✅ 완료 (T-012, T-013, T-014)

- 일간 매거진: 카테고리별 섹션 + 글 카드(요약 1~3줄) + 트렌드 단락 + 하단 장애 피드. **(T-012 완료)**
- 주간/월간: LLM 통합 요약본을 별도 파일로 발행. **(T-013 완료)**
- 카테고리/태그별 인덱스 페이지에 글 카드 append. **(T-014 완료)**
- 산출: `src/rss_wiki/publish/{daily,weekly,monthly,indexes}.py`, 단위 테스트 (84/84 PASS, 신규 27 케이스).
- **확립된 인터페이스 패턴(M5):**
  - publish 모듈은 **순수 함수**로 구성 — 입력은 구조화된 dataclass 시퀀스, 출력은 마크다운 문자열. DB/파일 IO/네트워크/`subprocess` 미접근. 영속성(파일 쓰기, magazines 행 INSERT)은 호출자(M6 파이프라인)가 storage repo와 stdlib `pathlib`로 처리한다.
  - DB 행/도메인 객체와의 결합 금지. publish는 자체 dataclass(`ArticleCard`, `CategorySection`, `FailingFeed`, `SourceArticle`, `IndexEntry`)를 입력 인터페이스로 정의하고, 호출자가 `sqlite3.Row` → dataclass 변환을 책임진다(M3/M4 "ingest/llm은 DB 미접근" 원칙의 publish 적용).
  - `frozen=True` dataclass로 입력 불변성 보장. 멀티라인 텍스트는 `splitlines()`로 분해 후 라인별 처리. 빈 컬렉션은 해당 줄·섹션 자체 누락(빈 섹션 비노출 원칙).
  - dataclass·헬퍼 재사용은 publish 패키지 내부 sibling import로(예: `weekly.py`의 `SourceArticle`을 `monthly.py`에서 사용, `daily.py`의 `FailingFeed`를 `weekly`/`monthly`에서 사용). 이중 정의 금지.
  - `failing_feeds` 렌더링은 daily/weekly/monthly 3중 중복 유지 — `publish/renderer.py` 추출은 4번째 사용처가 등장할 때까지 보류(YAGNI). 인덱스 페이지는 `failing_feeds` 인자 미수용(PRD §4 "매거진 하단" 정의에 인덱스 미해당).

### M6. CLI / 파이프라인 통합 / 운영 안내 — ✅ 완료 (T-015A~I 모두 완료, 2026-05-05)

- `rss-wiki daily|weekly|monthly` 커맨드 정리.
- daily 파이프라인: 수집 → 추출 → 중복 → LLM → 발행 → 인덱스 갱신.
- 주간/월간 트리거 조건(금요일 / 매월 마지막 금요일) 판정 로직.
- README에 cron/launchd 등록 예시.
- 산출: `src/rss_wiki/pipeline/{ingest,llm,publish}.py`, `src/rss_wiki/cli.py`, `main.py` 정리, `README.md` 갱신.
- **슬라이싱(9 슬라이스):** T-015A(`pipeline/ingest.py` 단일 entry 처리 `process_entry` + extract None 로깅, ✅ 완료) → T-015B(`pipeline/ingest.py` 다피드 순회 `run_daily_ingest` + 통계 + 피드 단위 실패 격리, ✅ 완료) → T-015C(`pipeline/llm.py` 신규 `analyze_articles` 글 분석 + 카테고리별 트렌드 결선 + storage repo 3 함수 추가, ✅ 완료) → T-015D(`pipeline/publish.py` 신규 일간 매거진 발행 결선 — 빌드 + 파일 쓰기 + `magazines` INSERT + `magazine_articles` 링크, ✅ 완료) → T-015E(`pipeline/publish.py` `publish_indexes` 추가 — 카테고리/태그별 인덱스 페이지 갱신 + storage repo 인덱스 조회 함수 3개 신설, ✅ 완료) → T-015F(`pipeline/publish.py` `publish_weekly` 결선 — `list_articles_published_between` 신규 + ISO 주차 헬퍼 + LLM 통합 요약 + 주간 매거진 빌드/INSERT, ✅ 완료) → T-015G(`pipeline/publish.py` `publish_monthly` 결선 — 발행일이 속한 달의 1일~발행일 범위 + LLM 통합 요약 + 월간 매거진 빌드/INSERT, ✅ 완료) → T-015H(`cli.py` 신규 — argparse 엔트리포인트 + 주간/월간 트리거 판정(`is_friday`/`is_last_friday_of_month`) + `daily`/`weekly`/`monthly` 서브커맨드 결선, ✅ 완료) → T-015I(`main.py` 진입점 정리 + `pyproject.toml [project.scripts]` 등록 + README 신규 작성: 설치·`feeds.toml` 작성·`rss-wiki daily` 사용법·cron/launchd 등록 예시·자동 트리거 동작 설명·트러블슈팅. 🟢 활성, **M6 마지막 슬라이스**).
- **슬라이스 분할 사유(2026-05-05 Planner 자체 결정 갱신):** 원 PLAN의 T-015D가 "매거진 발행 + 인덱스 갱신"을 한 슬라이스로 묶었던 것을 두 슬라이스(D/E)로 분리한 데 이어, 원 T-015F("주간/월간 트리거 + 발행") 역시 한 세션 범위를 넘는 사이즈(주월간 각각 LLM 호출 + 매거진 빌더 호출 + 파일 쓰기 + INSERT/링크 + 트리거 판정)이므로 자체 판단으로 추가 분할: 주간 발행 단독(F), 월간 발행 단독(G), CLI/트리거(H)로 3분할. 이어 원 T-015H("CLI + main.py + pyproject + README")도 한 세션을 넘는 사이즈(argparse 골격 + 트리거 판정 함수 + 3개 서브커맨드 결선 + 8~10 통합 테스트 + 운영 문서 작성)로 판단되어 추가 분할: CLI 결선·테스트(H)와 운영 안내(I=main.py 진입점 정리 + pyproject scripts + README cron/launchd 사용법)로 2분할. **분할 사유:** (a) CLI 결선은 코드+테스트 비중이 큼(외부 IO 주입 패턴으로 fake fetcher/extractor/runner 통합 테스트 필요), (b) 운영 안내(I)는 README 작성이 본질로 코드 변경 미미(main.py 1~3줄, pyproject 2~3줄). 한 슬라이스로 묶으면 acceptance가 코드/문서 모두 비대해져 회귀 위험 증가. M6 슬라이스 8→9개로 확장.
- **T-015G 자체 결정(2026-05-05, 인계):** (a) 월간 기간 = 발행일이 속한 달의 1일 ~ 발행일(달력월 기준). (b) `period_label`은 `YYYY-MM`. (c) `start_date`는 `date.fromisoformat(end_date).replace(day=1).isoformat()`. (d) `_iso_week_label` 같은 별도 헬퍼 미추가. (e) `list_articles_published_between` 재사용.
- **T-015H 자체 결정(2026-05-05):** (a) 트리거 판정 함수(`is_friday(d: date) -> bool`, `is_last_friday_of_month(d: date) -> bool`)는 `cli.py` 모듈 내부에 둠 — 별도 `pipeline/triggers.py` 분리하지 않음(YAGNI, 사용처가 cli.py 단독). 함수는 stdlib `datetime.date`만 사용하는 순수 함수. (b) 서브커맨드 결선 함수(`run_daily`/`run_weekly`/`run_monthly`)는 `cli.py` 내부에 둠 — `pipeline/` 패키지 신규 모듈 미추가. M6 인터페이스 원칙 "결선층은 storage/ingest/llm/publish 자유 import"는 `pipeline/`뿐 아니라 `cli.py`에도 적용. (c) argparse 진입점 시그니처 `main(argv: Sequence[str] | None = None) -> int` — 테스트에서 argv 주입 가능, exit code 반환. (d) 일간 흐름에서 트리거 충족(`now.weekday() == 4` 금요일 → 주간 자동 발행, 그날이 그 달 마지막 금요일이면 월간 자동 발행) 시 자동 호출 — PRD §5 "5. 금요일이면 주간 통합 요약 추가 발행, 매월 마지막 주 금요일이면 월간 통합 요약도 추가 발행" 그대로 구현, 별도 옵트아웃 옵션(`--no-auto-trigger`) 미도입(단순함 우선, 테스트는 `now` 인자 주입으로 분기 검증). (e) `now` 시계는 함수 인자로 콜러블 비주입(date 값 직접 주입) — `Callable` 깊이 1단계 더 늘리는 것보다 단순. 호출자가 실제 호출 시 `date.today()` 기본값 사용. (f) DB 경로/feeds 경로/output_dir 기본값: `data/rss-wiki.db`/`feeds.toml`/`output` — argparse `--db`/`--feeds`/`--output` 옵션으로 오버라이드 가능. (g) 로깅은 `cli.main`에서 `logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")` 호출(이미 설정되어 있으면 stdlib 동작상 무시). (h) 도메인 예외(`FetchError`/`LLMError`/`PromptParseError`/`ValueError`) 발생 시 `logger.error` 후 exit code 1 반환, 정상 완료 시 0. `sqlite3.IntegrityError`/`OSError`는 캐치하지 않고 traceback 전파(데이터 정합성 보호). (i) `conn.commit()`은 `cli.py`의 서브커맨드 결선 함수가 호출(M6 인터페이스 원칙 — 최상위 엔트리포인트에서 commit 책임). (j) `weekly`/`monthly` 서브커맨드는 `--end-date` 옵션 받음, 기본값은 `date.today().isoformat()`. weekly/monthly 단독 호출 시에는 트리거 판정 우회(운영자가 명시적으로 호출했으므로 발행 강제). daily에서만 트리거 판정 사용.
- **T-015I 자체 결정(2026-05-05):** (a) `main.py`는 `cli.main()`을 호출하는 얇은 진입점만 유지 — `from rss_wiki.cli import main`(또는 `as cli_main`) + `if __name__ == "__main__": raise SystemExit(main())` 3~5줄. 기존 `print("Hello from rss-wiki!")` 제거. exit code 전파 보장. (b) `pyproject.toml`에 `[project.scripts]` 테이블 추가 — `rss-wiki = "rss_wiki.cli:main"` 단일 엔트리. `uv sync`/`pip install -e .` 후 `rss-wiki daily` 실행 가능. (c) README는 한국어로 작성(기존 docs/_ 일관). 섹션 순서: 개요 → 요구사항 → 설치 → 설정(`feeds.toml`) → 사용법(daily/weekly/monthly) → 자동 트리거 동작 설명 → 자동화 등록(cron/macOS launchd) → 트러블슈팅 → 디렉터리 구조. (d) cron 예시: 매일 12:00 발행 — `0 12 _ \* \* cd /path/to/rss-wiki && /path/to/uv run rss-wiki daily`. macOS launchd 예시: `~/Library/LaunchAgents/com.user.rss-wiki.plist` plist XML 골격(`StartCalendarInterval` Hour=12, Minute=0). (e) 트러블슈팅 항목: ① Claude CLI 미인증(`claude login`안내, PRD §10) ②`feeds.toml` 미존재(`cp feeds.example.toml feeds.toml` 가이드) ③ SQLite 디렉터리 미존재(`--db` 부모 디렉터리 자동 생성됨, 권한 이슈만 안내) ④ 피드 HTTP 타임아웃(연속 5회 실패 시 "장애 피드" 섹션 노출 동작 설명, PRD §9) ⑤ 빈 분석 결과(LLM 호출 0건일 때 daily 매거진 미발행, 인덱스 갱신만 수행되는 동작 설명). (f) README 길이는 약 100~180줄 — 너무 짧으면 운영자가 cron 등록 시 추측해야 하고, 너무 길면 유지보수 부담. (g) **테스트 추가 없음** — main.py와 pyproject scripts는 통합 테스트(`uv run rss-wiki --help`수동 확인)로 충분, README는 테스트 불가. T-015H의 146 테스트 회귀 없음(146/146 PASS) 유지. (h) 코드 변경량 최소: main.py 3~5줄, pyproject.toml 2~3줄. README 신규 작성이 본질. (i) M6 완료 = 모든 마일스톤 완료 — T-015I PASS 시 다음 사이클에서`docs/DONE` 빈 파일 생성하여 종료 신호.
- **인터페이스 원칙(M6 공통):**
  - `pipeline/*` 모듈은 **결선층** — `storage`, `ingest`, `llm`, `publish`를 자유롭게 import해 호출 그래프를 구성한다. DB/파일 IO는 결선층에서 직접 수행 가능(M3·M4·M5의 "DB 미접근" 원칙은 도메인 모듈 한정이며 결선층에는 적용하지 않음).
  - 외부 IO를 가진 함수는 콜러블 주입(`fetcher`, `extractor`, `runner`, `now` 등) 패턴 유지 — 단위 테스트는 fake/stub로 외부 네트워크/subprocess/시계 비의존.
  - 트랜잭션은 결선층 함수 호출자가 commit 책임을 지며, 결선층 자체는 commit하지 않는다(M2 패턴 유지). 단, `cli.py`의 최상위 엔트리포인트는 commit을 수행할 수 있다.
  - 도메인 예외(`FetchError`, `ExtractError`, `LLMError`, `PromptParseError` 등)는 결선층에서 try/except로 감싸 PRD §9 "조용히 스킵" 정책을 구현하되, stdlib `logging` WARNING 이상으로 원인 추적 가능하게 한다. **격리 범위는 도메인 예외 한정** — `sqlite3.IntegrityError` 등 정합성 예외는 캐치 금지(데이터 정합성 문제 은폐 방지).
  - 결과 파일 쓰기는 `pathlib.Path.write_text(encoding="utf-8")` 단순 사용 + 디렉터리 미존재 시 `mkdir(parents=True, exist_ok=True)`. 외부 마크다운/템플릿 라이브러리 미도입(stdlib only 원칙 유지).
  - `pipeline/__init__.py`는 빈 파일 — sub-module들이 결선층 책임을 분담.
  - `pipeline/llm.py`의 `runner` 시그니처는 단순화하여 `Callable[[str], str]`로 둔다 — `call_claude(prompt, runner=...)`처럼 timeout/runner 키워드를 노출하지 않는다(단순함 우선). 호출자가 timeout 조정이 필요하면 `lambda p: call_claude(p, timeout=120.0)` 형태로 주입한다.
  - 카테고리·태그 정규화 책임은 storage 레이어(`upsert_category`/`upsert_tag`의 `strip()`+`lower()`) — `pipeline/llm.py`는 트렌드 그룹화 키로만 `category.strip().lower()`를 사용하며, `repo`에 저장되는 정규화는 `upsert_*`가 단일 진실 원천(M2 패턴 유지).

### M7. FastAPI 웹 인터페이스 (PRD §13) — ✅ 완료 (T-018A~G 모두 PASS, 196/196, 2026-05-05)

PRD §13 신설로 도입. 9 슬라이스(T-018A, T-018B, T-018B2, T-018C, T-018D, T-018D2, T-018E~G). 원 7 슬라이스에서 자체 결정으로 (1) T-018B를 두 슬라이스로 재분할(부트스트랩+CLI 전환과 외래키/`delete_feed`), (2) T-018D를 두 슬라이스로 재분할(매거진 GET과 카테고리/태그 GET).

- 목표 산출: `src/rss_wiki/web/{app.py,routes_magazines.py,routes_feeds.py,markdown.py,templates/*.html}`, `cli.py`에 `web` 서브커맨드 + uvicorn 실행, README §13 갱신.
- 의존성 추가: `fastapi`, `uvicorn[standard]`, `jinja2`, `markdown-it-py`. (T-018C에서 일괄 추가)

**슬라이싱:**

- **T-018A** `storage` 레이어 확장 — `feeds` 테이블에 `enabled`/`last_fetched_at`/`updated_at` 컬럼 추가 + `init_db` 멱등 마이그레이션(`PRAGMA table_info` → `ALTER TABLE ADD COLUMN`) + repo에 `list_feeds`/`update_feed`/`set_feed_enabled`/`reset_feed_failures` 4 함수 추가. 단위 테스트. **(M7 첫 슬라이스, ✅ 완료, PASS 153/153, 2026-05-05)**
- **T-018B** TOML→DB 부트스트랩 + `cli.run_daily` 전환 — `pipeline/bootstrap.py` 신규(`bootstrap_feeds_from_toml(conn, path) -> int`), `cli.main`의 `daily` 분기에서 부트스트랩 호출 → `list_feeds(conn, enabled_only=True)` 결과를 `FeedConfig`로 변환해 `run_daily(feeds=...)`에 주입(PRD §11 SoT 변경 반영). `cli.run_daily` 시그니처는 변경 없음(테스트 격리 유지). **(✅ 완료, PASS 158/158, 2026-05-05)**
- **T-018B2** 외래키 정합성 + `delete_feed` — `articles.feed_id`를 NOT NULL → nullable로 SQLite 테이블 재생성 패턴 마이그레이션, `articles.feed_url_snapshot`/`feed_name_snapshot` 2 컬럼 추가, `repo.delete_feed(conn, feed_id)` 신설(스냅샷 채움 → `feed_id=NULL` → DELETE feeds 행). PRD §13 "삭제 시 피드 메타를 글 row에 스냅샷" 충족. T-018B와 분할 사유는 본 절 끝 메모 참조. **(✅ 완료, PASS 164/164, 2026-05-05)**
- **T-018C** `web/` 패키지 골격 — fastapi/uvicorn/jinja2/markdown-it-py 의존성 추가, `web/app.py`(FastAPI 인스턴스 + lifespan에서 SQLite 커넥션 + WAL 모드), `web/markdown.py`(markdown-it-py 래퍼), 첫 라우트 `GET /healthz` + `GET /` 임시 인덱스. `tests/test_web_app.py`는 `fastapi.testclient.TestClient`로 healthz/index 200 검증. **(✅ 완료, PASS 168/168, 2026-05-05)**
- **T-018D** 매거진 GET 라우트 + 템플릿 토대 — `repo.list_magazines`/`repo.get_magazine_by_id` 2 함수 추가, `templates/{base,magazine,list}.html` 3 템플릿 신설, `routes_magazines.py` 신규(APIRouter `/magazines` 목록 + `/magazines/{magazine_id}` 단건 마크다운→HTML), `web/app.py` 수정(Jinja2Templates 모듈 레벨 인스턴스 + `include_router` + `/` 라우트를 매거진 인덱스 페이지로 교체), `tests/test_web_app.py` 5 케이스 추가. **(✅ 완료, PASS 173/173, 2026-05-05)**
- **T-018D2** 카테고리/태그 GET 라우트 — `/categories`(인덱스), `/categories/{name}`(글 목록), `/tags/{name}`(글 목록). `routes_magazines.py` 확장(별도 `routes_browse.py` 분리하지 않음, 자체 결정) + 기존 `templates/list.html` 재사용. `repo.get_category_by_name`/`repo.get_tag_by_name` 2 함수 신설(자체 결정 — 이름 정규화 책임을 storage 레이어에 둠, M2 패턴 일관). 5 신규 통합 테스트. **(✅ 완료, PASS 178/178, 2026-05-05)**
- **T-018E** 피드 GET 라우트 + `routes_feeds.py` 신설 — `/feeds` 목록 페이지(name/url/enabled/실패 카운트/마지막 수집 표시) + `/feeds/{id}/edit` 수정 폼(name/enabled 프리필; URL은 readonly 표기). 템플릿 `feeds.html`, `feed_edit.html` 2종 신설. `repo.get_feed_by_id` 1 함수 추가. `web/app.py`는 `include_router(feeds_router)` 1 줄만 추가. **(✅ 완료, PASS 182/182, 2026-05-05)**
- **T-018F** 피드 POST 라우트 5종 — `POST /feeds`(추가, URL 정규화 + UNIQUE), `POST /feeds/{id}`(수정 — name/enabled), `POST /feeds/{id}/delete`(`delete_feed` 호출), `POST /feeds/{id}/toggle`, `POST /feeds/{id}/reset`. 모두 처리 후 `303 See Other`로 `/feeds`로 리다이렉트. form-encoded 본문(`Form(...)` 의존성). `python-multipart` 의존성 추가. **(✅ 완료, PASS 192/192, 2026-05-05)**
- **T-018G** CLI `rss-wiki web` 서브커맨드 + uvicorn 실행(`127.0.0.1:8765` 기본) + README에 웹 인터페이스 운영 섹션(웹 시작 명령, 호스트/포트 옵션, 보안 경고, 라우트 요약) 추가. **(✅ 완료, PASS 196/196, 2026-05-05)**

### M8. 웹 UI 모던화 + PRD §13 CRUD 충돌 해소 — ✅ 완료 (T-019A ✅ 202/202, T-019B ✅ 211/211, T-019C ✅ 218/218)

PRD §13이 2026-05-05 23:32Z에 갱신되어 신규 UI/UX 요구가 추가됨. M7이 라우트·템플릿 골격만 충족했으므로 모던 디자인·플래시 메시지·URL 수정 허용 등을 신설 마일스톤으로 분리해 작업한다.

**PRD §13 신규 요구 ↔ 현재 코드 간극:**

| 신규 요구                                                                          | 현재 상태                                                   | 슬라이스   |
| ---------------------------------------------------------------------------------- | ----------------------------------------------------------- | ---------- |
| 모던 디자인 + 디자인 토큰(컬러/간격/폰트/라운드/섀도우) 단일 CSS 파일              | `base.html`에 인라인 1줄 `<style>`                          | T-019A     |
| 라이트/다크 모드 자동(`prefers-color-scheme`)                                      | 미구현                                                      | T-019A     |
| 반응형(모바일/태블릿/데스크탑) 레이아웃                                            | `max-width:720px`만                                         | T-019A     |
| 상단 GNB(타이틀 + 매거진/카테고리/태그/피드 관리, active 강조, 모바일 햄버거/탭바) | `<h1><a href="/">RSS Wiki</a></h1>`만                       | T-019A     |
| 카드/리스트/배지/버튼/폼 공통 컴포넌트 통일                                        | 미구현                                                      | T-019A·B·C |
| 본문 영역 ~720px 폭 + 코드/인용/표/링크 스타일                                     | 폭만 적용                                                   | T-019C     |
| 피드 수정 시 **`url`도 수정 가능**(정규화 후 UNIQUE 검증, 충돌 시 폼 에러)         | `feed_edit.html`에 "URL 변경 불가" 명시·라우트도 url 미수용 | T-019B     |
| `GET /feeds/new` 별도 페이지                                                       | 미구현(`/feeds` 인라인 폼만)                                | T-019B     |
| 폼 제출 후 토스트/배너 결과 표시(쿼리스트링 플래시)                                | 미구현                                                      | T-019B     |
| `GET /tags` 인덱스(GNB "태그" 메뉴 대상)                                           | 미구현                                                      | T-019C     |

**슬라이싱(3 슬라이스):**

- **T-019A** 디자인 토큰 + 단일 CSS 파일 + base.html GNB + 다크모드 + 반응형 + StaticFiles 마운트. 신규 `src/rss_wiki/web/static/style.css`(디자인 토큰 CSS 변수 + 라이트/다크 자동 + 반응형 미디어 쿼리 + 카드/배지/버튼/폼 기본 컴포넌트), `web/app.py` `app.mount("/static", StaticFiles(...))` + `from fastapi.staticfiles import StaticFiles`. `base.html` 재작성 — `<link rel="stylesheet" href="/static/style.css">` + `<header>` GNB(좌측 사이트 타이틀 → `/`, 우측 매거진/카테고리/태그/피드 관리 4 링크). active 강조는 Jinja2 컨텍스트 변수 `active_nav`로 후속 슬라이스에서 채움(본 슬라이스는 없는 상태로도 동작). 단위 테스트 — `/static/style.css` 200, `base.html` 렌더 결과에 `<link>` + GNB 마커(매거진·카테고리·태그·피드 관리 4 텍스트) 포함, 헬스체크/매거진/피드 기존 라우트 회귀 0. **(✅ 완료, PASS 202/202, 2026-05-06)**
- **T-019B** 피드 CRUD URL 편집 허용 + 토스트/배너 플래시 + `GET /feeds/new` 별도 페이지. `repo.update_feed`에 `url: str | None = None` 인자 추가(NULL 시 미변경, 명시 시 새 url 그대로 SET — 자기 자신 갱신은 SQLite UPDATE 동작상 UNIQUE 위반 안 함, 다른 행과 동일하면 `IntegrityError`), `routes_feeds.py` `feed_update`에 `url: str = Form("")` 추가 + 정규화 + 기존 url과 동일하면 `url_arg=None`, `IntegrityError` 캐치 시 `conn.rollback()` + `RedirectResponse(url=f"/feeds/{feed_id}/edit?error=duplicate", status_code=303)`, 성공 시 `?ok=updated`. `POST /feeds`는 `?ok=created` redirect(silent 멱등 유지). `GET /feeds/new` 라우트 + `templates/feed_new.html` 신설. `templates/_flash.html` 부분 템플릿(쿼리스트링 `ok`/`error` 코드를 한국어 메시지로 매핑, JS 없이 `.flash`/`.flash-success`/`.flash-danger` CSS 배너). `style.css`에 `.flash` 3 클래스 추가(약 12줄). `feed_edit.html` URL 입력 readonly 제거 + 안내 문구 교체 + `_flash.html` include. `feeds.html`의 인라인 추가 폼은 유지(`/feeds/new` 별도 페이지는 보조 진입점) + `_flash.html` include. **(✅ 완료, PASS 211/211, 2026-05-06)**
- **T-019C** 카드/리스트/배지/버튼/폼 컴포넌트 적용(`feeds.html`/`list.html`/`magazine.html`/`feed_edit.html`/`feed_new.html` 클래스 부착) + `GET /tags` 인덱스 라우트(`/tags` → list.html, 모든 태그 정렬, `repo.list_tags` 재사용) + GNB active 강조(`routes_magazines.py` 7 GET 라우트 + `routes_feeds.py` 3 GET 라우트에 `active_nav` 컨텍스트 4값(magazines/categories/tags/feeds) 주입) + 매거진 본문 영역 스타일(`style.css`에 `.magazine-body` 스코프로 H1~H4/`pre`/`code`/`blockquote` 스타일 약 50줄 추가). 7 신규 케이스(`tags_index_empty`/`tags_index_with_entries`/`active_nav_marks_feeds_link`/`active_nav_marks_magazines_link`/`active_nav_marks_tags_link`/`feeds_html_uses_btn_class`/`magazine_body_styles_in_css`) → 합계 218/218 PASS 목표. **(🟢 활성, M8 마지막 슬라이스)**

**T-019C 자체 결정(2026-05-06 Planner):**

1. **`/tags` 인덱스 라우트 위치**: `routes_magazines.py`에 `tags_index` 추가(별도 `routes_browse.py` 분리 미수행, T-018D2 결정과 일관). 위치는 `tag_articles`(`/tags/{name}`) 라우트 직전 — 가독성 우선(FastAPI는 등록 순서 의존이 아니므로 동작은 무관). `_tag_items` 헬퍼는 T-018D2에서 정의된 것을 재사용.
2. **`active_nav` 컨텍스트 4값 매핑**: `magazines`/`categories`/`tags`/`feeds` 4 string. `base.html`의 Jinja2 조건부 클래스(`{% if active_nav == "magazines" %} class="active"{% endif %}` 등)는 T-019A에서 이미 작성됨 — 본 슬라이스는 라우트 컨텍스트 주입만 추가. 자체 결정: `/` 라우트는 `magazines`로 매핑(랜딩 페이지가 매거진 목록 역할 — `routes_magazines.py:index`).
3. **POST 라우트 active_nav 미주입**: `routes_feeds.py`의 5 POST 라우트(`feeds_create`/`feed_update`/`feed_delete`/`feed_toggle`/`feed_reset`)는 모두 `RedirectResponse` 반환 — `base.html` 미렌더라 컨텍스트 미관여. 자체 결정: GET 라우트만 컨텍스트 주입(M7 인터페이스 원칙 일관).
4. **컴포넌트 클래스 부착 범위**: `.card`(컨테이너 박스, T-019A 정의), `.badge`/`.badge-success`/`.badge-danger`(상태 표시), `.btn`/`.btn-primary`/`.btn-danger`(인터랙티브 액션). 자체 결정: `feeds.html`은 추가 폼 `.card` + 활성 상태 `.badge` + 5+ 버튼 `.btn`. `list.html`은 항목별 `.card` 래퍼(`<ul><li>` → `<div class="card">`). `magazine.html`은 `<article class="magazine-body">`. `feed_edit.html`/`feed_new.html`은 제출/취소 버튼 `.btn`만.
5. **매거진 본문 스타일 스코프**: `.magazine-body` 클래스로 한정 — `<article class="magazine-body">` 내부에서만 H1~H4 계층/`pre`/`code`/`blockquote` 스타일 적용. 자체 결정: 글로벌 element 스타일이 다른 페이지(목록/폼)에 영향 주지 않도록 스코프 제한. PRD §13 "본문 영역 ~720px 폭"은 T-019A `.container`에서 이미 충족, 본 슬라이스는 매거진 본문 시각 디테일만.
6. **폭 제한 중복 회피**: `.magazine-body`에 `max-width: 720px` 재정의하지 않음 — `.container`(부모)가 이미 720px 적용. 자체 결정: 단일 진실 원천(`.container`)으로 폭 관리.
7. **표(`<table>`) 매거진 본문 스타일 미추가**: T-019A `<table>` element 스타일이 이미 정의됨(`width: 100%` + `border-collapse` + 셀 padding/border). 자체 결정: `.magazine-body table` 별도 정의 미추가(중복 회피, YAGNI).
8. **링크(`<a>`) 매거진 본문 스타일**: `.magazine-body a`에 `text-decoration: underline` 추가 — 본문 내 링크는 가독성 위해 밑줄 강조(GNB/카드 링크는 밑줄 없는 디자인 유지). 자체 결정: PRD §13 "코드/인용/표/링크 스타일을 정리" 충족.
9. **인용(`<blockquote>`)**: `border-left: 4px solid var(--color-accent)` + 좌측 패딩 + `color-text-muted` + `surface` 배경. 자체 결정: 시각적으로 명확한 인용 구분.
10. **코드(`<pre>`/`<code>`)**: `<code>`는 인라인(미세한 padding + border + surface 배경), `<pre>`는 블록(큰 패딩 + radius + `overflow-x: auto`로 긴 줄 스크롤). `<pre><code>` 중첩은 padding/border/background 제거(이중 박스 회피). 자체 결정: 운영자가 매거진에 코드 예시를 마크다운 fenced code block으로 작성할 때 자연스럽게 렌더.
11. **테스트 케이스 7개**: (a) `/tags` 인덱스 빈/2건 2 케이스(`tags_index_empty`/`tags_index_with_entries`), (b) GNB active 강조 3 페이지(`active_nav_marks_feeds_link`/`active_nav_marks_magazines_link`/`active_nav_marks_tags_link`), (c) 컴포넌트 클래스 부착 1(`feeds_html_uses_btn_class`), (d) 매거진 본문 CSS 1(`magazine_body_styles_in_css`). 자체 결정: 카테고리 active 케이스는 magazines/feeds와 동일 코드 경로이므로 생략(YAGNI). `list.html` `.card` 래퍼는 `tags_index_with_entries`에서 함께 검증.
12. **빈 목록 메시지 일관성**: `/tags` 빈 목록은 `list.html`의 `{% else %}<p>아직 항목이 없습니다.</p>{% endif %}` 분기를 그대로 노출 — 카테고리/매거진/태그 빈 목록 메시지 통일. 자체 결정: `/tags` 전용 메시지 별도 작성하지 않음.
13. **DONE 발행 시점**: T-019C PASS 후 다음 사이클 Planner가 PRD §1~13 전 섹션이 코드/문서/테스트에 반영됐음을 점검 → `docs/DONE` 빈 파일 발행. T-019C가 PRD §13 갱신본의 마지막 미반영 항목(`/tags` 인덱스 + active 강조 + 컴포넌트 클래스 부착 + 매거진 본문 스타일 4 항목)을 모두 충족하므로 다음 사이클이 종료 사이클.
14. **회귀 목표**: 기존 211 케이스 회귀 0(211/211 PASS 유지) + 신규 7 케이스 → 합계 **218/218 PASS** 목표.
15. **모듈 경계**: 변경 파일 9개 — `src/rss_wiki/web/routes_magazines.py`(수정), `src/rss_wiki/web/routes_feeds.py`(수정), `src/rss_wiki/web/static/style.css`(수정), `src/rss_wiki/web/templates/feeds.html`(수정), `src/rss_wiki/web/templates/list.html`(수정), `src/rss_wiki/web/templates/magazine.html`(수정), `src/rss_wiki/web/templates/feed_edit.html`(수정), `src/rss_wiki/web/templates/feed_new.html`(수정), `tests/test_web_app.py`(수정). 변경 금지: `src/rss_wiki/{config,cli,main}.py`, `src/rss_wiki/{ingest,llm,publish,pipeline}/*.py`, `src/rss_wiki/storage/{schema.sql,db.py,repo.py}`(repo는 변경 없음 — `list_tags`/`list_feeds` 등 모두 기존 함수 재사용), `src/rss_wiki/web/{__init__.py,app.py,markdown.py}`, `src/rss_wiki/web/templates/{base.html,_flash.html}`(T-019A·B에서 이미 작성됨, 변경 불필요), `pyproject.toml`(의존성 미추가), `feeds.toml`, `feeds.example.toml`, `README.md`, `output/*`, `data/*`. **신규 외부 의존성 미추가.**
16. **인라인 form `style="display:inline"` 유지**: `feeds.html`의 토글/리셋/삭제 form 3개에 이미 `style="display:inline"` 인라인 스타일이 있음 — 본 슬라이스에서 그대로 유지(`.btn` 클래스가 `display: inline-flex`이지만 부모 form이 inline이므로 행 내 정렬 정상). 자체 결정: 인라인 스타일을 CSS 클래스로 추출하지 않음(작은 변경 surface, YAGNI).

**T-019B 자체 결정(2026-05-06 Planner):**

1. **`update_feed` `url` 인자 시그니처**: `url: str | None = None` 키워드 전용. None이면 url 컬럼 미터치(기존 SQL 그대로), 문자열이면 `UPDATE feeds SET name=?, url=?, updated_at=...` SQL 분기. 자체 결정: 빈 문자열 분기는 라우트 레이어 책임(라우트가 `url.strip()` 비면 None 전달) — storage는 패스스루.
2. **UNIQUE 검증 방식**: 별도 SELECT 미수행. SQLite `feeds.url UNIQUE` 제약 + `UPDATE` 실행 시 자동 발생하는 `sqlite3.IntegrityError`에 위임. M2 패턴 일관(`IntegrityError` 가공 없이 전파). 자기 자신 제외 검증도 SQLite UPDATE 동작에 의존(같은 행에 동일 url 재set은 제약 위반 안 함, 다른 행과 동일하면 위반).
3. **라우트 레이어 정규화**: `feed_update`에서 `url.strip()` 비면 `url_arg=None`(미변경), 비지 않으면 `normalize_url()` 적용 후 기존 `feed["url"]`과 동일하면 다시 `url_arg=None`(불필요한 SQL 회피). 다르면 정규화된 url을 storage에 전달. 자체 결정: 정규화 책임은 라우트 — `ingest.dedupe.normalize_url`을 단일 진실 원천으로 재사용(M3 패턴).
4. **`IntegrityError` 처리**: `feed_update`에서 try/except 블록으로 감싼 후 `conn.rollback()` 호출 + redirect. `set_feed_enabled`가 같은 트랜잭션 내 부분 적용되지 않도록 rollback 필수. 자체 결정: M7 인터페이스 원칙 "쓰기 라우트만 commit/rollback" 일관.
5. **redirect 쿼리스트링 코드**: `?ok=created`(POST /feeds 성공) / `?ok=updated`(POST /feeds/{id} 성공) / `?error=duplicate`(UNIQUE 충돌). 자체 결정: 코드 매핑은 `_flash.html`이 단일 진실 원천. 운영자가 보지 않을 내부 코드(`created`/`updated`/`duplicate`)는 짧은 영문 식별자로 통일(URL 길이 절약).
6. **`feeds_create` UNIQUE 처리**: 기존 `INSERT OR IGNORE` silent 멱등 유지(`upsert_feed` 동작 그대로). duplicate 추가 시도도 `?ok=created`로 redirect — PRD §13 "추가 ... URL 정규화 후 UNIQUE 제약으로 중복 방지"의 "방지"는 silent 멱등으로 해석(기존 행 보존이 의도된 동작). 자체 결정: 명시적 에러 메시지는 수정 흐름에서만 노출(수정은 자기 자신 제외 의도적 충돌이라 표면화).
7. **`GET /feeds/new` 라우트 위치**: `routes_feeds.py`에서 `feeds_index` GET 직후, `feed_edit_form` GET 이전에 배치 — `/feeds/new`는 `/feeds/{feed_id}` path보다 우선 매칭. FastAPI는 등록 순서 의존이 아니므로 실제 동작은 무관하지만 가독성 우선. 자체 결정: 라우트 함수명 `feed_new_form`(M7 명명 규칙 일관).
8. **`feed_new.html` vs `feeds.html` 인라인 폼**: PRD §13 라우트 표 `GET /feeds/new`(별도 페이지) 항목 충족 위해 별도 템플릿 신설하되, `feeds.html`의 기존 인라인 추가 폼은 그대로 유지 — 운영자에게 두 진입점 제공(빠른 등록은 인라인, 안내 페이지는 별도). 자체 결정: 단일 진입점으로 단순화하지 않음(PRD가 별도 페이지를 명시했고, 인라인 폼이 이미 있으므로 제거 시 회귀 surface 확장).
9. **`_flash.html` 부분 템플릿 위치**: `templates/_flash.html`. 언더스코어 prefix는 Jinja2/django 관행으로 부분(partial) 표시. `feeds.html`/`feed_edit.html`/`feed_new.html` 3 곳에서 `{% include "_flash.html" %}` 호출. 자체 결정: include는 `<h2>` 헤딩 직후 한 줄로 — form 위에 노출되어 운영자가 즉시 인지.
10. **`request` 컨텍스트 자동 주입**: FastAPI 0.110+ 권장 시그니처 `templates.TemplateResponse(request, ...)`로 호출하면 `request` 객체가 자동으로 Jinja2 컨텍스트에 들어감. `_flash.html`에서 `request.query_params.get("ok"/"error")`로 접근. 자체 결정: 별도 컨텍스트 추출 helper 미도입(YAGNI).
11. **CSS `.flash` 3 클래스**: T-019A에서 토큰 정의(`--color-success`/`--color-danger`/`--color-surface`/`--space-3`/`--space-4`/`--radius-md`/`--color-border`)를 모두 재사용. `padding`/`border-radius`/`margin-bottom`/`border`/`background` 5 속성 + 성공/실패 변종 2 변종. 약 12줄. 자체 결정: 닫기 버튼 미도입(JS 의존, PRD §13 "JS 없이 동작" strict). 새로고침/링크 이동 시 자동 사라짐.
12. **3 단순 액션 라우트(`feed_delete`/`feed_toggle`/`feed_reset`)**: 본 슬라이스에서 플래시 메시지 미추가(redirect는 `/feeds`로만, 쿼리스트링 추가 시 회귀 surface 확장). 자체 결정: PRD §13 "폼 제출 후 토스트/배너로 처리 결과 노출"은 추가/수정 흐름이 핵심(URL 충돌 등 사용자 입력 검증이 필요한 곳). 단순 액션은 동작 결과가 즉시 목록 갱신으로 시각화되므로 별도 메시지 불필요. T-019C에서 추가 검토 가능.
13. **`feed_edit.html` URL input value**: `value="{{ feed.url }}"`로 기존 url 프리필. readonly 속성 제거. 안내 문구는 "URL (변경 시 정규화 후 중복 검증)"으로 교체. 자체 결정: 빈 문자열 입력 허용(라우트가 빈 문자열은 미변경으로 처리) — 운영자가 url 비워두고 저장해도 안전.
14. **`feeds.html` 인라인 폼은 그대로**: 본 슬라이스에서 `feeds.html` 변경은 `_flash.html` include 1줄만 추가. 인라인 추가 폼은 유지 — `/feeds/new` 별도 페이지로 대체하지 않음(PRD가 둘 다 허용). 자체 결정: 회귀 surface 최소화 + 운영자 편의(빠른 등록 경로 보존).
15. **테스트 전략**: storage 2 케이스(url 변경 성공 / UNIQUE 충돌 raise) + web 7 케이스(GET /feeds/new / url 변경 성공 / url 변경 충돌 / 빈 url 미변경 / POST /feeds redirect / `?ok=created` 플래시 렌더 / `?error=duplicate` 플래시 렌더). 합계 9 케이스 → 211/211 PASS 목표.
16. **`url=None` 미변경 동작 검증 케이스 생략**: 기존 `update_feed` 호출자(테스트 또는 라우트)가 이미 검증하므로 별도 케이스 미추가(YAGNI). 본 슬라이스에서 url=None 동작은 `test_post_feed_update_empty_url_keeps_existing`이 라우트 통합 시점에서 커버.
17. **DONE 발행 시점**: T-019B PASS 후 T-019C(컴포넌트 클래스 부착 + `/tags` 인덱스 + active GNB + 매거진 본문 스타일) PASS까지 완료한 다음 사이클 Planner가 PRD §13 갱신본 전 항목을 점검 → `docs/DONE` 발행. T-019B 단독 PASS는 DONE 조건 미충족.
18. **모듈 경계**: 변경 파일 9개 — `src/rss_wiki/storage/repo.py`(수정), `src/rss_wiki/web/routes_feeds.py`(수정), `src/rss_wiki/web/static/style.css`(수정), `src/rss_wiki/web/templates/_flash.html`(신규), `src/rss_wiki/web/templates/feed_new.html`(신규), `src/rss_wiki/web/templates/feed_edit.html`(수정), `src/rss_wiki/web/templates/feeds.html`(수정), `tests/test_storage_repo.py`(수정), `tests/test_web_app.py`(수정). 변경 금지: `src/rss_wiki/{config,cli,main}.py`, `src/rss_wiki/{ingest,llm,publish,pipeline}/*.py`, `src/rss_wiki/storage/{schema.sql,db.py}`, `src/rss_wiki/web/{__init__.py,app.py,markdown.py,routes_magazines.py}`, `src/rss_wiki/web/templates/{base,list,magazine}.html`, `pyproject.toml`, `feeds.toml`, `feeds.example.toml`, `README.md`, `output/*`, `data/*`. 신규 외부 의존성 미추가.

**T-019A 자체 결정(2026-05-05 Planner):**

1. **단일 CSS 파일 위치**: `src/rss_wiki/web/static/style.css` 신규. 패키지 내 정적 자산은 `web/static/` 하위로 통일(향후 favicon·이미지 추가 시에도 동일 위치). FastAPI `StaticFiles(directory=...)`로 마운트, 경로는 `/static/style.css`. 자체 결정: 외부 CDN/프레임워크(Tailwind 등) 미도입 — PRD §13 "빌드 단계 없이" strict 준수.
2. **StaticFiles 마운트 위치**: `web/app.py`의 `create_app` 내부, `include_router` 호출 직후 `app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")`. import 1줄(`from fastapi.staticfiles import StaticFiles`) 추가. `app.state` 갱신 미필요. 자체 결정: 모든 정적 자산은 패키지 상대 경로 — 운영자가 실행 디렉터리에 의존하지 않도록.
3. **디자인 토큰 구성**: CSS 변수(`:root` + `[data-theme="dark"]` 또는 `@media (prefers-color-scheme: dark)`)로 색상/간격/폰트/라운드/섀도우 정의. 자체 결정 — PRD §13 5축(컬러 팔레트/간격 스케일/폰트 사이즈/라운드/섀도우) 모두 변수화.
   - **컬러**: `--color-bg`/`--color-surface`/`--color-text`/`--color-text-muted`/`--color-border`/`--color-accent`/`--color-accent-hover`/`--color-success`/`--color-danger`. 라이트/다크 두 세트.
   - **간격**: `--space-1` ~ `--space-8`(4/8/12/16/24/32/48/64 px).
   - **폰트**: `--font-sans`(시스템 폰트 스택), `--font-mono`(SFMono-Regular 등), `--text-sm`/`--text-base`/`--text-lg`/`--text-xl`/`--text-2xl`.
   - **라운드**: `--radius-sm`/`--radius-md`/`--radius-lg`(4/8/12 px).
   - **섀도우**: `--shadow-sm`/`--shadow-md`(미세 + 카드용).
4. **다크 모드 자동화**: `@media (prefers-color-scheme: dark)` 블록에서 `:root` CSS 변수 재정의. 토글 UI(수동 전환) 미도입 — PRD가 자동 적용만 명시. 자체 결정: 토글 UI는 후속 PRD 갱신 시점에 검토.
5. **반응형 브레이크포인트**: `@media (max-width: 768px)`(모바일/태블릿)에서 GNB 가로 스크롤 탭바로 전환(햄버거 메뉴는 JS 의존도가 있어 PRD §13 "JS 없이 동작"과 충돌 — 자체 결정: 가로 스크롤 탭바 채택). `@media (min-width: 1024px)`는 컨테이너 폭만 확장(본문은 720px 유지). 자체 결정: 2 브레이크포인트로 단순화.
6. **GNB 마크업**: `<header class="gnb">` 안에 `<a class="gnb-brand" href="/">RSS Wiki</a>` + `<nav class="gnb-nav"><a href="/magazines">매거진</a><a href="/categories">카테고리</a><a href="/tags">태그</a><a href="/feeds">피드 관리</a></nav>`. active 강조는 `{% if active_nav == "magazines" %}class="active"{% endif %}` Jinja2 조건부 — 본 슬라이스에서는 컨텍스트 미주입(라우트 핸들러 변경 없음 → 미강조 상태 노출), T-019C에서 라우트 컨텍스트 갱신. 자체 결정: PRD "현재 활성 메뉴는 시각적으로 강조"는 컨텍스트 도입과 함께 후속 처리, 본 슬라이스는 마크업 토대만.
7. **`/tags` 링크 미구현 라우트**: T-019A 시점에 `/tags`는 라우트 미존재 → 클릭 시 404. 자체 결정: GNB 마크업은 PRD §13 GNB 정의 그대로 4 메뉴 모두 포함, `/tags` 라우트는 T-019C에서 추가. 본 슬라이스 단위 테스트는 `/tags` 클릭을 검증하지 않음(텍스트 노출만 확인).
8. **`base.html` 재작성 범위**: 기존 1줄 인라인 CSS 제거 + `<link rel="stylesheet" href="/static/style.css">` 1줄 추가, `<header>`를 GNB 골격으로 교체, `<main>` `class="container"` 추가. `{% block title %}`/`{% block content %}` 슬롯은 그대로 유지(다른 템플릿 영향 0). 자체 결정: `<meta name="viewport" content="width=device-width, initial-scale=1">` 추가(반응형 동작 필수).
9. **CSS 파일 길이**: 약 200~300줄 — 토큰 + 리셋 + GNB + 본문 컨테이너 + 카드 + 배지 + 버튼 + 폼 + 표 + 미디어 쿼리. 너무 짧으면 컴포넌트 누락, 너무 길면 유지보수 부담. 자체 결정: 본 슬라이스에서 토큰·GNB·기본 타이포그래피·컨테이너 + 카드/배지/버튼/폼 클래스만 정의(클래스 부착은 T-019B·C에서 점진 진행). 즉 CSS는 본 슬라이스에 통째로 작성하되, 적용은 점진적.
10. **테스트 케이스 4~5개**(`tests/test_web_app.py`에 추가, 단일 파일 유지):
    1. `test_static_style_css_served` — `client.get("/static/style.css")` → 200 + `Content-Type` `text/css`(또는 startswith) + 본문에 `:root`, `--color-bg`, `@media (prefers-color-scheme: dark)`, `.gnb` 4 마커 포함.
    2. `test_base_html_includes_stylesheet_link` — 기존 매거진 인덱스 라우트 응답 본문에 `<link rel="stylesheet" href="/static/style.css">` 포함.
    3. `test_base_html_renders_gnb_with_four_links` — 응답 본문에 `class="gnb"` + 4 텍스트(`매거진`/`카테고리`/`태그`/`피드 관리`) + 4 href(`/magazines`/`/categories`/`/tags`/`/feeds`) 포함.
    4. `test_base_html_includes_viewport_meta` — `<meta name="viewport"` 마커 포함.
    5. (선택) `test_existing_routes_no_regression` — `/`, `/magazines`, `/feeds`, `/healthz` 4 GET 200 회귀 검증(기존 테스트로 커버되므로 본 케이스는 생략 가능 — 자체 결정: 생략).
    - 픽스처: 기존 `with TestClient(create_app(tmp_db)) as client:` 패턴. `tmp_path` 기반 임시 SQLite.
    - 자체 결정: CSS 본문 마커 검증은 4개 핵심 키워드(`:root`/`--color-bg`/`prefers-color-scheme`/`.gnb`)로 한정 — 토큰 정의/다크모드/GNB 컴포넌트 3축이 모두 작동 확인. 추가 마커는 T-019B·C 컴포넌트 사용 시점에 검증.
11. **회귀**: 기존 196 케이스 회귀 0(196/196 PASS 유지) + 신규 4 케이스 → 합계 **200/200 PASS** 목표.
12. **모듈 경계**: 변경 파일 — `src/rss_wiki/web/app.py`(수정 — `from fastapi.staticfiles import StaticFiles` import 1줄 + `app.mount(...)` 1줄 추가), `src/rss_wiki/web/static/style.css`(신규 200~300줄), `src/rss_wiki/web/templates/base.html`(수정 — 기존 1줄 인라인 CSS 제거 + viewport meta + stylesheet link + GNB 마크업 12줄 내외), `tests/test_web_app.py`(수정 — 4 케이스 추가) — 합계 4개. 변경 금지: `src/rss_wiki/{config,cli,main}.py`, `src/rss_wiki/{ingest,llm,publish,pipeline,storage}/*.py`, `src/rss_wiki/web/{__init__.py,markdown.py,routes_magazines.py,routes_feeds.py}`, `src/rss_wiki/web/templates/{feeds,feed_edit,list,magazine}.html`(컴포넌트 클래스 부착은 T-019B·C 책임), `pyproject.toml`(의존성 미추가 — fastapi.staticfiles는 fastapi 본체 동봉), `feeds.toml`, `feeds.example.toml`, `README.md`(GNB·UI는 시각적 변경이라 README 운영 안내에 추가 불요, T-019B의 플래시 메시지 시점에 트러블슈팅 보강 검토).
13. **신규 외부 의존성 미추가**: `fastapi.staticfiles.StaticFiles`는 fastapi 본체에 포함, 별도 패키지 미필요. CSS 빌드 도구(Tailwind/PostCSS) 미도입 — PRD §13 "빌드 단계 없이" strict.
14. **PRD §13 "JS 없이 동작" 충돌 회피**: 햄버거 메뉴는 JS 의존도(클릭 토글)가 있어 가로 스크롤 탭바로 대체. 모바일에서 `<nav class="gnb-nav">`에 `overflow-x: auto`를 적용하면 좌우 드래그/스크롤로 메뉴 접근. 자체 결정: PRD §13 "햄버거 메뉴 또는 가로 스크롤 가능한 탭바로 대체" 후자 채택.
15. **active 강조 유보**: 라우트 핸들러에서 `active_nav` 컨텍스트 주입은 T-019C에서 `/tags` 추가 시 함께 처리(TemplateResponse 5+ 곳 일괄 수정 비용을 분산하기 위함). 본 슬라이스는 active 클래스 정의만 CSS에 포함, 적용은 후속.
16. **DONE 발행 시점**: M8 3 슬라이스(T-019A·B·C) 모두 PASS 후 PRD §13 신규 요구가 코드/문서/테스트에 반영되었음을 다음 사이클 Planner가 점검 → `docs/DONE` 발행. T-019A 단독 PASS는 DONE 조건 미충족.

**T-018G 자체 결정(2026-05-05 Planner):**

1. **`web` 서브커맨드 위치**: `cli.py`의 `argparse` `subparsers` 블록에 `p_web = sub.add_parser("web", help="로컬 웹 인터페이스 실행")` 추가. `p_web.add_argument("--host", default="127.0.0.1")` + `p_web.add_argument("--port", type=int, default=8765)`. PRD §13 "기본 바인딩은 `127.0.0.1`로만 listen" + 실행 예시 `--port 8765` 그대로 반영.
2. **uvicorn 호출 패턴**: `cli.main`의 `web` 분기에서 `uvicorn.run(create_app(db_path, run_init_db=True), host=args.host, port=args.port, log_level="info")` 호출. **앱 인스턴스를 직접 전달**(import 문자열 `"rss_wiki.web.app:app"` 미사용) — `--db` 옵션이 명시되면 해당 경로의 SQLite를 사용하도록 보장(전역 `app = create_app()`은 환경변수/기본값에만 반응). 자체 결정: 단일 워커·reload 미지원이지만 PRD §13 "개인용·로컬 전용" + uvicorn 단일 프로세스로 충분. `workers`/`reload` 옵션 미도입(YAGNI).
3. **uvicorn import 위치**: `cli.py` **모듈 레벨 import**(`import uvicorn`) — 테스트에서 `monkeypatch.setattr("rss_wiki.cli.uvicorn.run", fake_run)`로 mock하기 위해 모듈 레벨 노출이 필요. uvicorn은 이미 의존성이며 대규모 import 비용 우려는 daily 분기에 영향 없도록 lazy import(`def cmd_web():` 내부 import)로 둘지 검토했으나, 테스트 격리 우선(M3·M4 패턴 일관 — `runner` 콜러블 주입과 동등). 자체 결정: `import uvicorn`을 파일 상단에 추가.
4. **`create_app` import**: `from rss_wiki.web.app import create_app` 상단 import 추가 — `web/app.py`는 fastapi/uvicorn 의존성이므로 daily 분기 진입자에게도 import 비용이 발생하나, daily 흐름에서 fastapi import가 부가되는 것은 수용 가능(런타임 ~수십 ms). 자체 결정: 분기별 lazy import는 코드 복잡도가 증가하므로 단순 상단 import 채택.
5. **`run_web` 결선 함수**: `cli.py` 내부에 `def run_web(*, db_path: Path, host: str, port: int, run_uvicorn: Callable[..., None] | None = None) -> int:` 추가. 본문은 `(run_uvicorn or uvicorn.run)(create_app(db_path), host=host, port=port, log_level="info")` + `return 0`. 자체 결정: `run_uvicorn` 콜러블 주입 패턴(M3·M4 일관)으로 단위 테스트에서 fake 주입. 기존 `run_daily`/`run_weekly`/`run_monthly`와 명명 일관(`run_*` prefix).
6. **반환 타입과 종료 코드**: `run_web`은 `uvicorn.run`이 정상 종료(KeyboardInterrupt 등)되면 `0` 반환. uvicorn 자체 예외(포트 점유 등)는 캐치하지 않고 traceback 전파(운영자 즉시 인지). `cli.main`의 `web` 분기는 `return run_web(...)`. 자체 결정: M6 인터페이스 원칙 "도메인 예외만 캐치, 인프라 예외는 전파" 일관.
7. **DB 경로 처리**: `cli.main`의 공통 흐름이 `db_path = Path(args.db)` + `db_path.parent.mkdir` + `init_db(db_path)`를 수행하므로 `web` 분기도 동일하게 통과. 자체 결정: `web` 분기는 `init_db` 후 추가로 `create_app(db_path, run_init_db=True)` 호출(이중 init_db이지만 멱등이므로 무해, 일관성 우선). conn 미사용이므로 `conn = get_connection(db_path)` 후 `try`/`finally`로 close하는 흐름은 그대로 유지(다른 분기와 패턴 일관). web 분기는 `conn` 비사용이지만 conn 생성 부작용 없음(추가 비용 미미).
8. **로깅**: `cli.main`이 이미 `logging.basicConfig(level=logging.INFO, ...)` 호출 — uvicorn은 자체 logger 사용하므로 `log_level="info"`로 일관 정합. 자체 결정: 별도 `--log-level` 옵션 미도입(단순함 우선, uvicorn 기본값 의존).
9. **README 새 섹션 추가**: 기존 README §6(자동 트리거 동작) 뒤에 **§7 "웹 인터페이스" 신설**(기존 §7 자동화 등록은 §8로, §8 트러블슈팅 →§9, §9 디렉터리 구조 →§10으로 일괄 시프트). 섹션 내용: (a) 시작 명령(`rss-wiki web`), (b) 기본 호스트/포트(`127.0.0.1:8765`)와 변경 옵션(`--host`/`--port`), (c) 보안 경고("개인용·로컬 전용. 외부 노출 시나리오 미지원"), (d) 라우트 요약 표(매거진/카테고리/태그/피드 — PRD §13 표 압축본), (e) 동시 실행 안내("daily 파이프라인과 동시 실행 가능 — WAL 모드"). 자체 결정: README 섹션 번호 시프트는 큰 영향 없음(목차/외부 링크 미존재). 길이 약 50~80줄 추가.
10. **README 트러블슈팅 추가 항목**: 기존 트러블슈팅에 "포트 점유" 항목 1개 추가 — `OSError: [Errno 48] Address already in use` 발생 시 `--port` 다른 값으로 재실행 안내. 자체 결정: 운영 흔한 시나리오 1줄.
11. **테스트 케이스 4개**(`tests/test_cli.py`에 추가):
    1. `test_run_web_invokes_uvicorn_with_create_app` — `run_uvicorn`에 fake 주입(`captured = []`) → `run_web(db_path=tmp_db, host="127.0.0.1", port=8765, run_uvicorn=lambda app, **kw: captured.append((app, kw)))` → `captured`에 `(FastAPI 인스턴스, {"host": "127.0.0.1", "port": 8765, "log_level": "info"})` 1건 + 반환값 0.
    2. `test_run_web_passes_custom_host_port` — `run_web(db_path=tmp_db, host="0.0.0.0", port=9000, run_uvicorn=fake)` → `kw["host"] == "0.0.0.0"`, `kw["port"] == 9000`.
    3. `test_main_web_subcommand_routes_to_run_web` — `monkeypatch.setattr(rss_wiki.cli, "uvicorn", types.SimpleNamespace(run=fake))` + `main(["--db", str(tmp_db), "web"])` → fake 호출 1회 + 반환 0. argparse 진입점 검증.
    4. `test_main_web_subcommand_honors_host_port_args` — `main(["--db", str(tmp_db), "web", "--host", "0.0.0.0", "--port", "9000"])` → fake에 전달된 host/port 검증.
    - 자체 결정: 실제 uvicorn 서버 기동 미수행(테스트 격리). FastAPI 앱 인스턴스 검증은 `isinstance(app, FastAPI)` 또는 `hasattr(app, "router")`로 단순 확인. 회귀 위험 낮은 표면(서브커맨드 라우팅 + 인자 전달).
12. **회귀 목표**: 기존 192개 회귀 0(192/192 PASS 유지) + 신규 4 케이스 → 합계 **196/196 PASS**.
13. **모듈 경계**: 변경 파일 — `src/rss_wiki/cli.py`(수정 — `import uvicorn` + `from rss_wiki.web.app import create_app` import 2 + `run_web` 결선 함수 추가 + `web` 서브커맨드 argparse + main 분기), `README.md`(수정 — §7 웹 인터페이스 신설 + 기존 §7~9 시프트 + 트러블슈팅 1 항목 추가), `tests/test_cli.py`(수정 — 4 케이스 추가 + 필요 import 확장: `types` 등) — 합계 3개. 변경 금지: `src/rss_wiki/{config.py,main.py}`, `src/rss_wiki/{ingest,llm,publish,pipeline,storage}/*.py`, `src/rss_wiki/web/{__init__.py,app.py,markdown.py,routes_magazines.py,routes_feeds.py}`, `src/rss_wiki/web/templates/*.html`, `pyproject.toml`(이미 uvicorn/fastapi 등 모든 의존성 등록 완료, `[project.scripts]` 미터치), `feeds.toml`, `feeds.example.toml`, `output/*`, `data/*`. **`pyproject.toml [project.scripts]` 미수정** — `rss-wiki = "rss_wiki.cli:main"`은 T-015I에서 이미 등록됨.
14. **import 문자열 vs 인스턴스 직접 전달**: `uvicorn.run("rss_wiki.web.app:app", ...)` 문자열 import는 reload/workers를 활성화할 때만 필요. 본 슬라이스는 single-process · no-reload이므로 `uvicorn.run(create_app(db_path), ...)` 인스턴스 직접 전달이 더 단순하고 `--db` 옵션과 정합. 자체 결정 기록.
15. **`init_db` 중복 호출**: `cli.main`의 공통 흐름이 `init_db(db_path)` 호출 후 `web` 분기에서 `create_app(db_path, run_init_db=True)`도 init_db를 호출(lifespan startup). init_db는 멱등이므로 부작용 없음. 자체 결정: `web` 분기에서만 `create_app(db_path, run_init_db=False)`로 두 번째 호출을 회피하는 분기는 가독성 손해 대비 이득 미미 — 일관성 우선.
16. **PRD §13 "실행" 섹션 표기 차이**: PRD는 `rss_wiki.web:app`라고 표기하지만 실제 모듈은 `rss_wiki.web.app:app`(`web/__init__.py`는 빈 파일이므로 `rss_wiki.web` 자체에는 `app` 심볼이 없음). 자체 결정: PRD 본문은 변경하지 않고(README·코드에서는 `rss-wiki web` 서브커맨드 실행을 권장하므로 import 경로는 운영자 노출 면 외) T-018G 구현은 `from rss_wiki.web.app import create_app`로 진행. uvicorn 직접 호출 시 import 경로는 `rss_wiki.web.app:app`로 README에 안내(기존 모듈 레벨 `app = create_app()` 참조).
17. **CSRF/CORS/인증**: T-018F와 동일 — PRD §13 "개인용·로컬 전용. 인증 없음" strict. README에 보안 경고 1줄 추가.
18. **수동 검증**: 본 슬라이스 PASS 후 운영자가 `rss-wiki web` 명령으로 서버를 띄우고 브라우저에서 `http://127.0.0.1:8765/`/`/magazines`/`/feeds` 등 라우트 동작을 확인하는 것을 권장(자동 테스트는 서브커맨드 라우팅까지만 커버, 실제 브라우저 동작은 T-018C·D·E·F의 단위 테스트가 라우트 단위로 이미 검증).
19. **DONE 발행 조건**: T-018G PASS + (a) PRD 모든 섹션이 코드/문서/테스트에 반영, (b) TASKS.md 모든 항목 `[x]`. T-018G PASS 시점에 PRD §13 라우트 표 + 실행 명령이 모두 충족되며 README §7 신설로 운영 안내 완료. 다음 사이클의 Planner가 PRD 전 섹션 점검 후 `docs/DONE` 빈 파일 생성.

**T-018F 자체 결정(2026-05-05 Planner):**

1. **`python-multipart` 의존성 추가**: `pyproject.toml dependencies`에 `python-multipart` 추가(상한·범위 미지정, 기존 의존성과 동일 표기). FastAPI `Form(...)` 의존성이 multipart 파서를 요구. T-018E에서 의도적으로 보류한 의존성을 본 슬라이스에서 도입. 자체 결정: `uv sync` 호출은 운영자 재량(generator는 `uv add python-multipart` 또는 `pyproject.toml` 직접 편집 후 `uv lock` 수행).
2. **5 POST 라우트 위치**: `routes_feeds.py`에 append(라우트 모듈 분리 미수행 — T-018E에서 신설된 `routes_feeds.py`에 5 라우트 추가하여 단일 모듈에 GET 2 + POST 5 = 7 라우트). M7 인터페이스 원칙 일관(피드 라우트는 `routes_feeds.py`).
3. **`POST /feeds` 시그니처**: `feeds_create(url: str = Form(...), name: str = Form(""), enabled: str | None = Form(None), conn = Depends(get_db)) -> RedirectResponse`. (a) `url` 필수, 빈 문자열은 `HTTPException(status_code=400, detail="url is required")`. (b) `name`은 선택 — 빈 문자열이면 `url`을 기본값으로 사용(피드 표시 이름 폴백). (c) `enabled`는 HTML checkbox 동작상 미체크 시 form data에 부재 → `Form(None)`로 받고 `bool(enabled)`로 변환. 기본 활성으로 추가하려면 추가 폼에 checkbox checked 기본값을 넣음 — 단순함 우선으로 본 슬라이스는 무조건 활성으로 추가(`enabled` 값 무시), `feeds.enabled` DEFAULT 1 사용. 자체 결정: 운영자가 추가 직후 비활성화하려면 토글로 처리. 추가 폼은 본 슬라이스 시점에는 `feeds.html`에 미포함(GET 폼 추가는 T-018F 책임 외 — 현재 폼 미존재 시 운영자는 별도 도구로 POST 호출 가능, 하지만 운영성 위해 본 슬라이스에서 `feeds.html`에 간단한 추가 폼 1개 추가하는 것을 자체 결정으로 채택).
4. **추가 폼 `feeds.html` 갱신**: `<table>` 위 또는 아래에 `<form method="post" action="/feeds">` 1개 추가 — `<input type="url" name="url" required>` + `<input type="text" name="name" placeholder="이름(선택)">` + `<button type="submit">추가</button>`. `enabled`는 미포함(기본 활성). 자체 결정: 추가 폼 없이는 운영자가 피드를 등록할 수단이 없음(부트스트랩 외) → PRD §13 "피드 관리 UI" 충족을 위해 본 슬라이스에서 함께 처리. 변경 범위 최소(테이블 위에 form 5~7줄 추가).
5. **URL 정규화**: `from rss_wiki.ingest.dedupe import normalize_url` 재사용 — `POST /feeds`에서 입력 URL을 정규화 후 `repo.upsert_feed(conn, name, normalized_url)` 호출. 정규화 후 동일 URL이 이미 존재하면 `INSERT OR IGNORE`로 silent 멱등(기존 피드 행 유지). 자체 결정: M3 인터페이스 원칙 "URL 정규화는 dedupe 단일 진실 원천" 일관, 라우트가 직접 `urllib.parse`를 import하지 않는다.
6. **`POST /feeds/{feed_id}` 시그니처(수정)**: `feed_update(feed_id: int, name: str = Form(...), enabled: str | None = Form(None), conn = Depends(get_db))`. (a) `get_feed_by_id`로 조회 → 미존재 시 404. (b) `repo.update_feed(conn, feed_id, name=name)` + `repo.set_feed_enabled(conn, feed_id, bool(enabled))` 두 호출. URL은 readonly이므로 form에 미포함, 라우트도 미수정. 자체 결정: `name` 필수(폼에서도 required) — 빈 이름 허용 시 운영성 저하.
7. **`POST /feeds/{feed_id}/delete` 시그니처**: `feed_delete(feed_id: int, conn = Depends(get_db))`. `get_feed_by_id`로 사전 검증 → 미존재 시 404. 존재 시 `repo.delete_feed(conn, feed_id)` 호출(스냅샷 채움 + feed_id NULL + DELETE feeds 3 SQL). 자체 결정: silent no-op 대신 명시적 404로 운영자가 잘못된 id 즉시 인지.
8. **`POST /feeds/{feed_id}/toggle` 시그니처**: `feed_toggle(feed_id: int, conn = Depends(get_db))`. `get_feed_by_id` 미존재 시 404. 존재 시 `repo.set_feed_enabled(conn, feed_id, not bool(feed["enabled"]))`. 자체 결정: form 본문 미사용(idempotent flip) — `request.method=="POST"` + `feed_id` path만으로 동작.
9. **`POST /feeds/{feed_id}/reset` 시그니처**: `feed_reset(feed_id: int, conn = Depends(get_db))`. `get_feed_by_id` 미존재 시 404. 존재 시 `repo.reset_feed_failures(conn, feed_id)`. 자체 결정: form 본문 미사용.
10. **모든 POST 라우트 응답**: `RedirectResponse(url="/feeds", status_code=303)` 반환 — `from fastapi.responses import RedirectResponse` import. PRD §13 "처리 후 `303 See Other`로 목록 페이지로 리다이렉트" 그대로. 자체 결정: 304/307이 아닌 303(POST→GET 변환 표준).
11. **모든 POST 라우트 commit**: 각 라우트 함수 끝에 `conn.commit()` 호출 후 redirect. 자체 결정: M7 인터페이스 원칙 "쓰기 라우트만 commit() 호출" 그대로. `get_db` dependency는 close만 책임.
12. **트랜잭션 격리**: 5 라우트 모두 단일 함수 내 단일 commit으로 종료. `delete_feed`의 3 SQL은 단일 commit으로 묶어 원자성 보장.
13. **CSRF 미도입**: PRD §13 "개인용·로컬 전용. 기본 바인딩 127.0.0.1, 인증 없음" strict — CSRF 토큰/Origin 검증 미도입(외부 노출 시나리오는 PRD 범위 외). 자체 결정 기록.
14. **에러 케이스**: (a) `url` 누락(`POST /feeds`) → FastAPI 422(자동), (b) `url` 빈 문자열 → `HTTPException(400)`(명시 검증), (c) `name` 누락(`POST /feeds/{id}`) → 422, (d) 미존재 feed_id → 404. 자체 결정: 422 vs 400 — FastAPI 자동 422는 누락이고, 빈 문자열은 라우트 본문에서 명시적 400으로 분기.
15. **`feed_edit.html` 변경 없음**: T-018E에서 `action="/feeds/{id}"`로 사전 작성 → 본 슬라이스에서 자동 활성화. 추가 변경 불필요.
16. **`feeds.html`에 토글/삭제/리셋 버튼 추가**: 기존 `수정` 링크 옆에 3개 버튼 추가 — 각 버튼은 별도 `<form method="post" action="...">` + 단일 submit. 자체 결정: 한 행에 3 form은 가독성 저하지만 PRD §13 "활성/비활성 토글 / 연속 실패 카운트 리셋 / 삭제" UI 충족을 위해 필요. JS 미사용(PRD §13 strict). 변경 범위는 테이블 마지막 컬럼에 3 버튼 form 추가(약 10~15줄).
17. **테스트 케이스 7개**:
    1. `test_post_feeds_creates` — `client.post("/feeds", data={"url": "https://example.com/rss", "name": "Example"})` → 303 + `Location` 헤더 = `/feeds` + DB feeds 행 1개(`url="https://example.com/rss"`, `name="Example"`).
    2. `test_post_feeds_normalizes_url` — `client.post("/feeds", data={"url": "https://example.com/rss?utm_source=x", "name": "Example"})` → 303 + DB `feeds.url == "https://example.com/rss"`(UTM 제거 검증).
    3. `test_post_feeds_duplicate_url_idempotent` — 같은 url 두 번 POST → 둘 다 303 + DB 행 1개(멱등).
    4. `test_post_feed_update` — 기존 feed_id에 `client.post(f"/feeds/{feed_id}", data={"name": "New", "enabled": "on"})` → 303 + `repo.get_feed_by_id` 결과 `name="New"`, `enabled=1`.
    5. `test_post_feed_update_disables_when_unchecked` — `data={"name": "Same"}`(enabled 키 부재) → 303 + `enabled=0`(checkbox 미체크 동작 검증).
    6. `test_post_feed_delete` — feed_id + articles 1행(연결) → POST `/feeds/{id}/delete` → 303 + feeds 행 삭제 + articles `feed_id IS NULL` + 스냅샷 채움(`delete_feed` 호출 검증).
    7. `test_post_feed_toggle` — enabled=1 feed_id → POST `/feeds/{id}/toggle` → 303 + `enabled=0`. 두 번째 호출 → `enabled=1`(반전 동작).
    8. `test_post_feed_reset` — `record_feed_failure(conn, feed_id)` 3회 → POST `/feeds/{id}/reset` → 303 + `consecutive_failures=0`.
    9. `test_post_feed_404_for_missing_id` — POST `/feeds/99999/delete` → 404. (toggle/reset/update에 대해서는 코드 경로 동일이므로 1 케이스로 커버)
    - 합계 8 케이스 신규 + 9번을 포함하면 9 케이스. 자체 결정: 9 케이스는 PRD 핵심 동작(추가/정규화/멱등/수정/체크박스/삭제/토글/리셋/404)을 균형있게 커버. 수정 라우트의 404 케이스는 9번에서 통합 검증 가능하므로 별도 테스트 미작성(코드 경로 동일).
    - 픽스처: `with TestClient(create_app(tmp_db)) as client:` 컨텍스트 패턴 일관(`follow_redirects=False`로 303 응답 직접 검증).
    - import 추가: `from rss_wiki.storage.repo import upsert_feed, set_feed_enabled, record_feed_failure, get_feed_by_id, list_feeds`(기존에 일부 이미 있으면 차이만).
18. **`tests/test_web_app.py` 단일 파일 유지**: 8~9 케이스 추가하여 합계 190~191 케이스. 자체 결정: T-018E와 동일 — 단일 파일 가독성 한계까지는 분리 미수행. T-018G 시점에 200 케이스 근처가 되면 분리 검토.
19. **모듈 경계**: 변경 파일 — `pyproject.toml`(수정 — `python-multipart` 1 의존성 추가), `src/rss_wiki/web/routes_feeds.py`(수정 — POST 5 라우트 + 필요 import 추가), `src/rss_wiki/web/templates/feeds.html`(수정 — 추가 폼 + 토글/삭제/리셋 버튼), `tests/test_web_app.py`(수정 — 8~9 케이스 추가) — 합계 4개. 변경 금지: `src/rss_wiki/{config,cli,main}.py`, `src/rss_wiki/{ingest,llm,publish,pipeline}/*.py`, `src/rss_wiki/storage/{schema.sql,db.py,repo.py}`(repo는 본 슬라이스에서 신규 함수 미추가 — 기존 `upsert_feed`/`update_feed`/`set_feed_enabled`/`reset_feed_failures`/`delete_feed` 모두 T-018A/B2/E에서 도입 완료), `src/rss_wiki/web/{__init__.py,app.py,markdown.py,routes_magazines.py}`(`include_router(feeds_router)`는 T-018E에서 이미 호출 — 5 라우트 자동 노출), `src/rss_wiki/web/templates/{base,list,magazine,feed_edit}.html`(feed_edit은 T-018E에서 이미 POST action으로 작성됨 — 추가 변경 불필요), `feeds.toml`, `feeds.example.toml`, `README.md`(T-018G 책임).
20. **회귀 목표**: 기존 182개 회귀 0(182/182 PASS 유지) + 신규 8~9 케이스 → 합계 **190~191/190~191 PASS**.

**T-018E 자체 결정(2026-05-05 Planner):**

1. **`routes_feeds.py` 신규 모듈**: `src/rss_wiki/web/routes_feeds.py` 신설 — `APIRouter()` 기반. 매거진 라우트가 6개로 성장한 시점에 피드 라우트(GET 2 + POST 5 = 합계 7)를 동일 모듈에 묶으면 단일 파일 비대(라우트 13개)로 가독성·테스트성 저하. M7 인터페이스 원칙 "라우트 모듈이 3개 이상이면 분리 고려"에 부합하는 자연스러운 분리 시점. T-018F의 POST 5 라우트도 본 모듈에 추가될 예정이므로 토대를 본 슬라이스에서 마련.
2. **`web/app.py` 수정 범위 최소화**: `from rss_wiki.web.routes_feeds import router as feeds_router` import 1 줄 + `app.include_router(feeds_router)` 1 줄 추가. `create_app` 시그니처/lifespan/healthz 미변경. 자체 결정: 변경 surface 최소화로 회귀 위험 차단.
3. **`repo.get_feed_by_id` 신설**: 시그니처 `get_feed_by_id(conn: sqlite3.Connection, feed_id: int) -> sqlite3.Row | None` — `SELECT * FROM feeds WHERE id = ?`. M2 패턴 일관(Connection 첫 인자, commit 미수행, `Row | None`). 자체 결정: 기존 `get_feed_by_url`은 부트스트랩/수집 흐름의 URL 기반 조회 전용이고, `/feeds/{id}/edit` 라우트는 정수 id 기반 lookup이 필요하므로 별도 헬퍼 도입(이름은 카테고리/태그 lookup 패턴 `get_*_by_*`와 일관).
4. **라우트 시그니처 2종**:
   - `GET /feeds` (`feeds_index`) — `repo.list_feeds(conn)` → `feeds.html` 렌더(`feeds=rows` 컨텍스트). 정렬은 `list_feeds` 기본(`id ASC`) 그대로 — 운영자가 부트스트랩 순서대로 보는 것이 자연스러움. 자체 결정: enabled_only=False(전체 표시 — 비활성 피드도 운영자가 토글로 다시 켤 수 있도록 노출).
   - `GET /feeds/{feed_id}/edit` (`feed_edit_form`) — `repo.get_feed_by_id(conn, feed_id)` → 없으면 `HTTPException(404)` → `feed_edit.html` 렌더(`feed=row`). 자체 결정: `feed_id` path param은 정수(FastAPI 자동 캐스팅), 음수/문자열은 422 반환(FastAPI 기본 동작).
5. **`feeds.html` 템플릿**: `base.html` 확장, 헤딩 "피드", 비공개 `<table>` 또는 `<ul>`로 피드별 행 렌더. 컬럼: name / url / enabled(boolean → "활성"/"비활성" 텍스트) / consecutive_failures / last_fetched_at(NULL → "—"). 행 끝에 `<a href="/feeds/{{ feed.id }}/edit">수정</a>` 링크. 빈 목록 시 "아직 등록된 피드가 없습니다." 안내. 자체 결정: 본 슬라이스는 GET 전용 — POST 폼(토글/리셋/삭제 버튼)은 T-018F에서 별도 PR로 추가, 본 슬라이스 템플릿은 GET 링크만 포함(테스트 surface 최소화 + 클릭 시 405 회피). PRD §13 "추가 폼"도 T-018F 책임(`POST /feeds`).
6. **`feed_edit.html` 템플릿**: `base.html` 확장, 헤딩 "피드 수정", `<form method="post" action="/feeds/{{ feed.id }}">` 골격. 필드 — `name` (`<input type="text" name="name" value="{{ feed.name }}" required>`), `enabled` (`<input type="checkbox" name="enabled" {% if feed.enabled %}checked{% endif %}>`), `url`은 readonly 표기(`<input type="url" value="{{ feed.url }}" readonly>` 또는 `<p>` 텍스트). PRD §13 "url 변경은 사실상 다른 피드이므로 삭제 후 재추가로 안내" → 폼에 안내 문구 1줄. 제출 버튼 + "취소"(=`/feeds` 링크). 자체 결정: 폼 `action`은 T-018F의 `POST /feeds/{id}` 엔드포인트 — 본 슬라이스 시점에는 405지만, T-018F가 즉시 후속이므로 템플릿 한 번에 작성하여 T-018F에서 템플릿 재수정 회피. 회귀 안전(GET만 테스트, 폼 action 동작은 T-018F 테스트 책임).
7. **`feeds.html`/`feed_edit.html`은 `list.html` 미재사용**: 피드 목록은 다중 컬럼(name/url/enabled/failures/last_fetched_at)이고 수정 폼은 form 기반이므로 `list.html`의 `heading`+`items=[{title, href, subtitle?}]` 단순 모델로 표현 불가. 자체 결정: 별도 템플릿 신설이 명료성·확장성 우선.
8. **`tests/test_web_app.py`에 케이스 추가**: 파일 분리 미수행(`test_web_feeds.py` 신설하지 않음, YAGNI — 기존 모듈 178 케이스에서 4 추가 → 182 케이스, 단일 파일 가독성 유지 가능). 4 신규 케이스:
   1. `test_feeds_index_empty` — feeds 0건 → `client.get("/feeds")` → 200 + `"피드"` 헤딩 + `"아직 등록된 피드가 없습니다"` 본문.
   2. `test_feeds_index_with_entries` — `repo.upsert_feed(conn, "Google", "https://example.com/rss")` + 다른 피드 1개 → 200 + 두 피드 name/url 본문 포함 + `'href="/feeds/1/edit"'`(또는 동등 검증) 포함.
   3. `test_feed_edit_form_renders` — feed 1행 + `set_feed_enabled(conn, feed_id, False)` → 200 + name/url 값 폼 프리필 + `enabled` checkbox unchecked + form `action="/feeds/{id}"` 본문 포함.
   4. `test_feed_edit_404_for_missing_id` — `/feeds/99999/edit` → 404.
   - 픽스처: 기존 `with TestClient(create_app(tmp_db)) as client:` 컨텍스트 패턴 일관. enabled 토글 검증을 위해 `set_feed_enabled` 호출.
   - 자체 결정: 활성 피드 GET 케이스에서 `consecutive_failures` 표시 검증은 생략(라우트 동작 핵심은 name/url/enabled/edit 링크, failures는 표시 detail) — 회귀 위험 낮음, 테스트 비중 균형.
9. **모듈 경계**: 변경 파일 — `src/rss_wiki/storage/repo.py`(수정 — `get_feed_by_id` 1 함수 추가), `src/rss_wiki/web/app.py`(수정 — import 1 + include_router 1, 합계 2 줄 추가), `src/rss_wiki/web/routes_feeds.py`(신규), `src/rss_wiki/web/templates/feeds.html`(신규), `src/rss_wiki/web/templates/feed_edit.html`(신규), `tests/test_web_app.py`(수정 — 4 케이스 + 필요 import 추가) — 합계 6개. 변경 금지: `src/rss_wiki/{config,cli,main}.py`, `src/rss_wiki/{ingest,llm,publish,pipeline}/*.py`, `src/rss_wiki/storage/{schema.sql,db.py}`, `src/rss_wiki/web/{__init__.py,markdown.py,routes_magazines.py,templates/{base,list,magazine}.html}`, `feeds.toml`, `feeds.example.toml`, `pyproject.toml`(의존성 미추가), `README.md`.
10. **신규 외부 의존성 미추가**: `python-multipart`는 form-encoded POST에서만 필요(T-018F 책임). 본 슬라이스는 GET 라우트만이므로 미도입. fastapi/jinja2는 T-018C에서 이미 추가됨.
11. **회귀 목표**: 기존 178개 회귀 0(178/178 PASS 유지) + 신규 4 케이스 → 합계 **182/182 PASS**.
12. **CSRF 미도입**: 본 슬라이스는 GET 전용. T-018F의 POST 라우트도 PRD §13 "개인용·로컬 전용. 기본 바인딩 127.0.0.1, 인증 없음" strict — CSRF 미도입(개인용 단일 사용자, 외부 노출 시나리오 PRD 범위 외).

**T-018D2 자체 결정(2026-05-05 Planner):**

1. **라우트 모듈 분리 미수행**: T-018D에서 도입한 `routes_magazines.py`를 그대로 확장(라우트 6개로 단일 모듈 유지). 별도 `routes_browse.py` 신규 모듈 미도입(YAGNI). M7 인터페이스 원칙의 "라우트 모듈이 3개 이상이면 분리 고려"는 T-018E·F의 `routes_feeds.py` 신설 시점에 충족 — 본 슬라이스는 매거진 라우트 모듈 단독 시점.
2. **`repo.get_category_by_name`/`get_tag_by_name` 신설**: 원 PLAN 메모 "repo 변경 미필요"를 본 슬라이스 진입 시 갱신. 이름 정규화 책임을 storage 레이어(M2 패턴)에 두기 위해 thin lookup 헬퍼 2 함수 추가. 라우트 핸들러는 정규화 미신경(`name.strip().lower()`는 storage 내부에서 수행). PRD §6 "카테고리·태그는 자동 생성 + 정규화" 일관.
3. **이름 기반 라우트 + 정수 id 미사용**: PRD §13 라우트 표가 `/categories/{name}` / `/tags/{name}` 형태이므로 path param은 이름. URL 인코딩은 FastAPI 기본 동작에 위임(`/`을 포함한 이름은 충돌 가능성이 있으나 LLM 자동 생성 카테고리/태그가 `/`를 포함할 가능성 낮음 — PRD §6 자유 형식이지만 M2 정규화에서 strip만 수행, slash escape는 후속 사이클 검토). 자체 결정: 단순함 우선.
4. **`/tags` 인덱스 라우트 미도입**: PRD §13 라우트 표에 `/tags` 인덱스 항목 없음(카테고리 인덱스 `/categories`만 정의). PRD strict로 본 슬라이스에서는 `/tags/{name}`만 제공. 태그 인덱스가 운영자 요청으로 발생하면 후속 사이클에서 검토.
5. **글 카드 `href`는 원문 URL**: 글 상세 라우트(`/articles/{id}`)는 PRD §13 라우트 표에 없음 → 글 카드는 외부 원문 URL(`articles.url`)로 직접 링크. 본 도구의 본질이 "큐레이팅 + 원문 발견"이므로 합리적 — 별도 글 상세 페이지 미도입(YAGNI). 호스팅 시점에 `target="_blank"` 처리 등은 후속 사이클 검토.
6. **글 카드 `title` 폴백**: `articles.title`이 NULL/빈 문자열인 경우 `articles.url`로 폴백 — 빈 링크 텍스트로 인한 UI 깨짐 방지. 자체 결정: PRD에 미명시이나 운영 안전 원칙.
7. **태그 200 케이스 테스트 생략**: 카테고리 200 케이스(`test_category_articles_renders_articles`)가 동일 코드 경로(`get_*_by_name` + `list_articles_by_*`)를 충분히 커버하므로 태그 200 케이스 추가는 회귀 위험 대비 비용 과다. 태그는 라우팅 동작 검증 차원에서 404 케이스 1개만 작성. 자체 결정: 테스트 비중 균형.
8. **헤딩 텍스트 정규화 노출**: `category_articles`의 heading은 정규화된 이름(`category["name"]` = lowercase) 그대로 노출 — `"카테고리: ai"`. 자체 결정: 운영자가 정규화 결과를 확인할 수 있는 투명성 우선(저장 형태 그대로 노출). 디스플레이용 표기 변환(`title()` 등)은 도입하지 않음 — 정규화 일관성과 단순함 우선.
9. **모듈 경계**: 변경 파일은 `src/rss_wiki/storage/repo.py`(2 함수 추가), `src/rss_wiki/web/routes_magazines.py`(3 헬퍼 + 3 라우트 추가), `tests/test_web_app.py`(5 케이스 추가) — 합계 3개. 변경 금지: `cli.py`, `main.py`, `web/app.py`(라우트 등록은 이미 include_router로 자동 노출), `web/markdown.py`, `web/templates/*.html`(list.html 재사용 가능), `storage/{schema.sql,db.py}`, `ingest/`/`llm/`/`publish/`/`pipeline/`, `feeds.toml`, `feeds.example.toml`, `pyproject.toml`(의존성 미추가), `README.md`.
10. **회귀 목표**: 기존 173개 회귀 0(173/173 PASS 유지) + 신규 5 케이스 → 합계 **178/178 PASS**.

**T-018D 자체 결정(2026-05-05 Planner):**

1. **슬라이스 분할 사유**: 원 T-018D가 매거진/카테고리/태그 GET 라우트 5개 + 3 템플릿 + 5+ 통합 테스트 + 라우트 모듈/Jinja2 토대를 한 슬라이스에 묶었으나, 한 세션(10~20분) 범위 초과로 판단하여 자체 결정으로 2분할: T-018D=매거진 GET 라우트 단독(라우트 모듈/Jinja2 토대 + 3 템플릿 + 매거진 2 라우트), T-018D2=카테고리/태그 GET 라우트(기존 list.html 재사용). M7 슬라이스 8→9개 확장.
2. **매거진 슬러그 규칙**: PRD §13 표의 `/magazines/{slug}` 경로에서 `{slug}` = `magazines.id` 정수값. 별도 slug 컬럼 미추가(YAGNI, schema.sql 변경 회피). 자체 결정: 단순함 우선 + 운영자 친화(`/magazines/12` 식 URL은 사람이 읽기에도 충분, M5 산출 file_path는 이미 `output/daily/YYYY-MM-DD.md`로 추적 가능).
3. **라우트 모듈 분리**: `src/rss_wiki/web/routes_magazines.py` 신규 — `APIRouter()` 기반. `web/app.py`에서 `app.include_router(magazines_router)` 호출. PLAN.md 모듈 트리에 이미 정의된 모듈명 그대로 사용. 자체 결정: 라우트 분리는 T-018E/F/G에서 `routes_feeds.py`도 함께 도입할 예정 — 토대를 본 슬라이스에서 마련.
4. **Jinja2Templates 인스턴스 위치**: `web/app.py` 모듈 레벨 — `templates = Jinja2Templates(directory=Path(__file__).parent / "templates")`. routes_magazines.py에서 `from rss_wiki.web.app import templates`로 import. 자체 결정: 단일 인스턴스 + 모듈 레벨 export. 별도 `web/dependencies.py` 미도입(YAGNI).
5. **`/` 라우트 교체**: T-018C 임시 HTML(`<h1>RSS Wiki</h1>...`)을 매거진 인덱스 페이지로 교체. PRD §13 "GET / : 최신 일간 매거진 + 최근 발행 매거진 목록" 그대로 구현. 자체 결정: `/` 와 `/magazines`의 차이 — `/` 는 최신 일간 매거진 단건 + 최근 5건 매거진 링크 목록(랜딩 페이지 성격), `/magazines` 는 전체 매거진 인덱스(목록만). 본 슬라이스에서는 `/` 도 최근 매거진 목록(`/magazines`와 동일 항목, 단순화)을 보여주도록 구현 — "최신 일간 + 최근 매거진 목록" 분리는 T-018D 통합테스트 통과 후 후속 사이클에서 재검토(YAGNI). **간소화: `/` 는 `/magazines`와 동일한 list.html을 렌더한다.**
6. **신규 repo 함수 2개**: `list_magazines(conn) -> list[sqlite3.Row]` — `SELECT id, kind, published_at, file_path FROM magazines ORDER BY published_at DESC, id DESC`, 정렬은 최신 발행이 먼저. `get_magazine_by_id(conn, magazine_id: int) -> sqlite3.Row | None` — `SELECT * FROM magazines WHERE id = ?`. M2 패턴(Connection 첫 인자, commit 미수행) 일관.
7. **단건 라우트 마크다운 렌더**: `magazines.file_path`를 `Path(file_path).read_text(encoding="utf-8")`로 읽어 `web.markdown.render_markdown(text)` → HTML 본문 컨텍스트(`magazine_html`). 파일 미존재(`FileNotFoundError`) 시 `HTTPException(status_code=404)`. 미존재 magazine_id도 `HTTPException(404)`.
8. **템플릿 3종 책임 분리**: `base.html` — `{% block content %}` 슬롯 + 최소 HTML 골격(`<!doctype html><html><head><title>{% block title %}RSS Wiki{% endblock %}</title></head><body>{% block content %}{% endblock %}</body></html>`). 정적 자산은 인라인/미도입(PRD §13 "최소한의 CSS만 인라인"). `magazine.html` — base 확장, `{{ magazine_html | safe }}` 한 블록(이미 render_markdown 결과). `list.html` — base 확장, `{% for item in items %}<li><a href="{{ item.href }}">{{ item.title }}</a> <small>{{ item.subtitle }}</small></li>{% endfor %}` 식 단순 구조. 카테고리/태그(T-018D2)에서도 `items=[{title, subtitle, href}]` 표준 형식 재사용. 자체 결정: 인라인 CSS는 1줄 이내(`<style>body { font-family: -apple-system, sans-serif; }</style>`) 또는 미도입.
9. **테스트 케이스 5개**: (a) `test_magazines_list_empty` — magazines 0건 → 200 + 응답 본문 비공백(템플릿 헤더 노출), (b) `test_magazines_list_with_entries` — magazines 2 행 삽입(`insert_magazine`) → 200 + 두 매거진 published_at + kind 본문 포함, (c) `test_magazine_detail_renders_markdown` — magazines 1행 + tmp_path에 `# Hello\n\n본문` md 파일 작성 → 200 + `<h1>Hello</h1>` + `본문` 포함, (d) `test_magazine_detail_404_for_missing_id` — `/magazines/99999` → 404, (e) `test_index_renders_magazine_list` — `/` 가 list.html 렌더(매거진 목록 표시) — T-018C의 `test_index_returns_200`은 임시 HTML 검증이었으므로 본 슬라이스에서 매거진 목록 검증으로 갱신.
10. **테스트 갱신**: T-018C의 `test_index_returns_200`은 본문 검증 문구를 "RSS Wiki" → 매거진 목록 페이지 골격 마커(예: `<title>` 또는 빈 목록 표시 텍스트)로 바꿈. 자체 결정: 단순한 200 + 응답 본문 비공백 검증으로 회귀.
11. **`web/app.py` 수정 범위**: (a) `from fastapi.templating import Jinja2Templates` import 추가, (b) `templates = Jinja2Templates(directory=Path(__file__).parent / "templates")` 모듈 레벨, (c) `from rss_wiki.web.routes_magazines import router as magazines_router` import + `app.include_router(magazines_router)`, (d) 기존 `/` 라우트는 list.html을 렌더하도록 교체(또는 `routes_magazines.py`로 이동). 자체 결정: `/` 라우트는 `routes_magazines.py`로 이동(매거진 인덱스이므로 모듈 일관). `web/app.py`는 healthz + Jinja2 셋업 + include_router로 단순화.
12. **HTMLResponse vs TemplateResponse**: `routes_magazines.py`의 라우트는 `templates.TemplateResponse(request, "list.html", {...})` 사용. FastAPI 0.110+ 권장 시그니처(첫 인자 `request`). 자체 결정: 최신 권장 패턴 사용.
13. **`include_router` 시점**: `create_app` 내부 — `app = FastAPI(lifespan=lifespan)` 직후 `app.include_router(magazines_router)`. 자체 결정: 팩토리 일관성 유지(create_app 외부에서 라우터 등록 금지).
14. **모듈 경계**: 변경 파일은 `src/rss_wiki/storage/repo.py`(2 함수 추가), `src/rss_wiki/web/app.py`(수정), `src/rss_wiki/web/routes_magazines.py`(신규), `src/rss_wiki/web/templates/{base.html,magazine.html,list.html}`(신규 3개), `tests/test_web_app.py`(수정 — 5 케이스 추가/`test_index_returns_200` 갱신) — 합계 7. 변경 금지: `cli.py`, `main.py`, `ingest/`, `llm/`, `publish/`, `pipeline/`, `storage/{schema.sql,db.py}`, `feeds.toml`, `feeds.example.toml`, `pyproject.toml`(의존성 미추가 — 본 슬라이스는 기존 fastapi/jinja2/markdown-it-py로 충분), `README.md`.
15. **신규 외부 의존성 미추가**: `python-multipart`는 form-encoded POST에서만 필요(T-018F 책임). 본 슬라이스는 GET 라우트만이므로 미도입.
16. **회귀 목표**: 기존 168개 테스트 회귀 0(168/168 PASS 유지) + 신규 5 케이스 → 합계 **173/173 PASS**. (단, T-018C의 `test_index_returns_200`은 검증 텍스트 갱신만, 신규로 카운트하지 않음.)

**T-018C 자체 결정(2026-05-05 Planner):**

1. **의존성 버전 핀(pyproject.toml)**: `fastapi`/`uvicorn[standard]`/`jinja2`/`markdown-it-py` 모두 **하한 미지정**(상한·범위 없이 단순 이름만 추가) — 기존 `feedparser`/`httpx`/`trafilatura`와 동일 표기법(미핀). uv lockfile이 정확한 버전을 고정. 자체 결정: 단순함 우선 + 일관성. PEP 631 지원 안정 패키지 4종이라 호환성 위험 낮음.
2. **`web/__init__.py`**: 빈 파일. 패키지 외부에서는 `from rss_wiki.web.app import app`/`create_app(...)` 형태로 명시적 import. 패키지 레벨 re-export 미도입(YAGNI).
3. **`web/app.py` 핵심 함수 시그니처**: `create_app(db_path: str | Path | None = None, *, run_init_db: bool = True) -> FastAPI`. (a) `db_path=None`이면 환경변수 `RSS_WIKI_DB` → 기본값 `data/rss-wiki.db` 순으로 결정, (b) `run_init_db=True`이면 lifespan startup에서 `init_db(db_path)` 호출(멱등 + WAL 모드 활성화), (c) 인스턴스 모듈 레벨 export `app = create_app()` 별도 추가 — `uvicorn rss_wiki.web.app:app` 호출 가능. 자체 결정: 팩토리 패턴(`create_app`)으로 테스트 격리 + 모듈 레벨 `app`으로 운영 호출 호환.
4. **WAL 모드 활성화 위치**: `init_db` 내부가 아니라 `web/app.py`의 lifespan startup에서 별도 커넥션을 잠깐 열어 `PRAGMA journal_mode=WAL` 실행 후 닫음. 자체 결정: WAL은 DB 파일 영속 설정으로 한 번만 실행하면 되며, `storage/db.py:init_db`는 도메인 레이어이므로 WAL 같은 운영 정책을 결선층(`web/`)이 책임지도록 분리. 단위 테스트의 `init_db` 호출은 WAL 부작용 없음 → 기존 storage 테스트 회귀 0 보장.
5. **요청 단위 DB 커넥션(`get_db`)**: FastAPI `Depends(get_db)` 패턴 — 요청마다 `sqlite3.connect(app.state.db_path)` + `row_factory = sqlite3.Row`로 yield → 종료 시 close. 풀링 미도입(SQLite WAL 모드는 다중 reader OK, 단일 writer는 lock 처리). 자체 결정: 단순함 우선, 풀 라이브러리 미사용.
6. **`get_db`/`create_app` 위치**: 모두 `web/app.py` 내부에 둠 — 별도 `web/dependencies.py` 분리 미도입(라우트 추가 시 import 경로 단순). T-018E/T-018F에서 라우트 모듈 분리 시 `from rss_wiki.web.app import get_db`로 재사용.
7. **`web/markdown.py` 시그니처**: `render_markdown(text: str) -> str`. 내부적으로 `markdown_it.MarkdownIt("commonmark", {"linkify": True}).render(text)` 사용. 단일 함수만 export — 라이브러리 인스턴스 외부 노출 금지(라이브러리 교체 용이성). `markdown-it-py` 외 다른 마크다운 라이브러리 사용 금지(M7 인터페이스 원칙).
8. **`GET /healthz` 응답**: `JSONResponse({"status": "ok"})` 200. DB 헬스체크 미포함(단순 liveness probe; T-018D 이후 매거진 라우트가 DB 의존성을 자체 검증).
9. **`GET /` 임시 응답**: 본 슬라이스에서는 임시 — `HTMLResponse("<h1>RSS Wiki</h1><p>최신 매거진 라우트는 T-018D에서 추가 예정.</p>")` 또는 `JSONResponse({"message": "RSS Wiki"})`. T-018D에서 매거진 인덱스로 교체. 자체 결정: HTML 응답으로 두어 브라우저 동작 검증 가능.
10. **단위 테스트 패턴(`tests/test_web_app.py`)**: `fastapi.testclient.TestClient` + `tmp_path` 기반 임시 SQLite. `create_app(tmp_path / "x.db")`로 격리. 4 케이스 — (a) `test_healthz_returns_ok` (200 + `{"status": "ok"}`), (b) `test_index_returns_200` (200 + 응답 본문 비공백), (c) `test_create_app_runs_init_db` (`tmp_path / "x.db"` 생성 + WAL 모드 확인 — `PRAGMA journal_mode` 결과 == "wal"), (d) `test_render_markdown_basic` (`render_markdown("# Hello")`이 `<h1>Hello</h1>` 포함). 외부 네트워크/uvicorn 비의존.
11. **lifespan 구현 패턴**: FastAPI `lifespan` 매개변수에 `@asynccontextmanager` 함수 전달. startup에서 `init_db(db_path)` + WAL 활성화, shutdown에서는 별도 정리 없음(요청 단위 커넥션이라 풀 종료 불필요). 자체 결정: deprecated `@app.on_event("startup")` 미사용(FastAPI 0.93+ 권장).
12. **외부 의존성 추가 검증**: `uv sync` 시 4 패키지 모두 PyPI에서 다운로드 가능. CI/로컬 테스트 시 `uv add fastapi 'uvicorn[standard]' jinja2 markdown-it-py` 형태로 등록 권장이나 PLAN/TASKS에서는 `pyproject.toml dependencies` 직접 편집을 acceptance로 명시(uv 명령 호출은 운영자 재량). 자체 결정: 문서 acceptance는 파일 상태 기준.
13. **모듈 경계**: 변경 파일은 `pyproject.toml`, `src/rss_wiki/web/{__init__.py,app.py,markdown.py}` (신규 3), `tests/test_web_app.py` (신규 1) — 합계 5. 변경 금지: `storage/`, `ingest/`, `llm/`, `publish/`, `pipeline/`, `cli.py`, `main.py`, `feeds.toml`, `feeds.example.toml`, `README.md`. 라우트 모듈(`routes_magazines.py`/`routes_feeds.py`/`templates/`) 미도입 — T-018D 이후 슬라이스 책임.
14. **회귀**: 기존 164개 테스트 회귀 0(164/164 PASS 유지). 신규 4 케이스 → 합계 **168/168 PASS** 목표.
15. **CLI `rss-wiki web` 서브커맨드 미도입**: T-018G에서 처리. 본 슬라이스 PASS 시점에는 `uv run uvicorn rss_wiki.web.app:app --host 127.0.0.1 --port 8765` 직접 호출로 실행 가능. README 갱신은 T-018G 동시 처리.
16. **인증/CORS 미도입**: PRD §13 "개인용·로컬 전용. 기본 바인딩은 `127.0.0.1`로만 listen, 인증 없음" 그대로. CORS 미도입.

**T-018B 분할 사유(2026-05-05 Planner 자체 결정):** 원 T-018B가 (a) `bootstrap_feeds_from_toml` 신설, (b) `cli.run_daily`를 DB 기반으로 전환, (c) `articles` 외래키 nullable 마이그레이션(SQLite 테이블 재생성 패턴), (d) `articles.feed_url_snapshot`/`feed_name_snapshot` 2 컬럼 추가, (e) `delete_feed(conn, feed_id)` 함수 신설을 한 슬라이스에 묶었다. 한 세션(약 10~20분) 범위에서 (c) SQLite 테이블 재생성 마이그레이션은 단독으로도 작성·테스트 부담이 크며, (a)+(b)는 cli 통합 테스트 위주로 묶이고 (c)+(d)+(e)는 storage 마이그레이션 위주라 응집도가 다르다. 따라서 응집도 기준으로 분할: T-018B = 부트스트랩 + cli 전환(pipeline/cli 변경, articles 미터치), T-018B2 = articles 외래키/스냅샷/`delete_feed`(storage 마이그레이션 단일 책임). M7 슬라이스 7→8개로 확장. PRD §13 충족 시점은 동일(T-018B2 PASS 시 피드 CRUD 토대 완성, T-018F에서 `delete_feed` 라우트로 노출).

**T-018B2 자체 결정(2026-05-05 Planner):**

1. **마이그레이션 트리거 조건**: `init_db`가 `PRAGMA table_info(articles)`로 `feed_id` 컬럼의 `notnull` 플래그를 확인 — `notnull == 1`이면 SQLite 테이블 재생성 패턴 수행, 이미 `0`(nullable)이면 스킵(멱등). 별도 마이그레이션 버전 테이블 미도입(PRAGMA로 충분, YAGNI).
2. **재생성 패턴 순서**: (a) 외래키 일시 OFF(`PRAGMA foreign_keys = OFF`), (b) 신규 `articles_new` 테이블 생성(스키마는 `feed_id INTEGER REFERENCES feeds(id)` — NOT NULL 제거, 스냅샷 2 컬럼 포함), (c) `INSERT INTO articles_new (...) SELECT ... FROM articles`(컬럼 명시), (d) `DROP TABLE articles`, (e) `ALTER TABLE articles_new RENAME TO articles`, (f) 인덱스 재생성(`idx_articles_url_hash`, `idx_articles_title_hash`), (g) 외래키 재활성화(`PRAGMA foreign_keys = ON`). 트랜잭션은 `init_db` 단일 트랜잭션 내(commit 1회).
3. **스냅샷 컬럼 추가**: 재생성 패턴이 작동하면 신규 컬럼이 자동 포함됨. 그러나 이미 nullable로 마이그레이션된 기존 DB에서는 재생성 미수행 → `PRAGMA table_info(articles)`로 컬럼 존재 확인 후 누락 시 `ALTER TABLE articles ADD COLUMN feed_url_snapshot TEXT` / `ADD COLUMN feed_name_snapshot TEXT` 멱등 추가. T-018A의 feeds 컬럼 마이그레이션과 동일 패턴.
4. **신규 DB(첫 init_db)**: `schema.sql` 자체에 `feed_id INTEGER REFERENCES feeds(id)`(NOT NULL 제거)로 정의 + `feed_url_snapshot TEXT` + `feed_name_snapshot TEXT` 컬럼 포함. `CREATE TABLE IF NOT EXISTS`로 신규 DB는 신 스키마 그대로 생성 → 재생성 패턴 미수행(`notnull == 0`).
5. **`delete_feed` 시그니처**: `delete_feed(conn: sqlite3.Connection, feed_id: int) -> None`. 트랜잭션 흐름은 단일 함수 내 3 SQL: (1) `UPDATE articles SET feed_url_snapshot = (SELECT url FROM feeds WHERE id = ?), feed_name_snapshot = (SELECT name FROM feeds WHERE id = ?) WHERE feed_id = ?`(서브쿼리로 NULL 채움 — 피드 미존재면 NULL), (2) `UPDATE articles SET feed_id = NULL WHERE feed_id = ?`, (3) `DELETE FROM feeds WHERE id = ?`. `conn.commit()` 미호출(M2 패턴).
6. **`feed_id` 외래키 동작**: `REFERENCES feeds(id)`만 명시(ON DELETE 절 미사용) — 삭제 시 외래키 위반은 (2)단계의 명시적 NULL 처리로 회피. `ON DELETE SET NULL` 채택은 SQLite 기존 데이터에 외래키 위반 행이 있을 가능성을 줄이고 명시성을 높이기 위해 보류(자체 결정 — 명시적 흐름이 운영자 추적에 유리).
7. **단위 테스트 위치**: `tests/test_storage_repo.py`에 추가(파일 분산 방지, T-018A와 일관). 별도 `tests/test_storage_migration.py` 미생성.
8. **테스트 케이스 6개**: (a) `init_db_articles_feed_id_nullable_migration` — 구 NOT NULL 스키마 DB 만들고 init_db → `PRAGMA table_info(articles)`에서 `feed_id.notnull == 0` 확인, (b) `init_db_articles_snapshot_columns_migration` — 스냅샷 컬럼 누락 DB에 init_db → 두 컬럼 존재 확인, (c) `init_db_articles_migration_preserves_data` — 기존 articles 행 1~2개 있는 DB에 init_db → 행 보존 + 컬럼 값 보존(url_hash 기준 SELECT 일치), (d) `init_db_articles_double_call` — 신 스키마에 init_db 두 번 호출 멱등(예외 없음, 데이터 보존), (e) `delete_feed_fills_snapshot_and_nulls_feed_id` — 피드 1개 + articles 1~2개 → delete_feed → articles 행 잔존 + `feed_url_snapshot`/`feed_name_snapshot` 채워짐 + `feed_id IS NULL` + feeds 행 삭제, (f) `delete_feed_no_articles` — 피드만 있고 articles 0건일 때 delete_feed 동작(feeds 행만 삭제, 예외 없음).
9. **회귀**: 기존 158개 테스트 회귀 0(158/158 PASS 유지). 신규 6 케이스 → 합계 **164/164 PASS** 목표.
10. **모듈 경계**: 변경 파일은 `src/rss_wiki/storage/{schema.sql,db.py,repo.py}` + `tests/test_storage_repo.py` 4개로 한정. `ingest/`/`llm/`/`publish/`/`pipeline/`/`cli.py`/`main.py`/`feeds.toml`/`pyproject.toml`/`README.md` 미변경. 신규 외부 의존성 미추가(stdlib `sqlite3`만 사용).
11. **운영 안전**: 마이그레이션은 단일 트랜잭션 내 수행 → 중간 실패 시 롤백되어 원본 보존. 외래키 OFF/ON 토글은 트랜잭션 밖에서 별도 `PRAGMA` 실행이 필요 — `init_db`는 `conn.execute("PRAGMA foreign_keys = OFF")` → `BEGIN` → 재생성 SQL → `COMMIT` → `conn.execute("PRAGMA foreign_keys = ON")` 순서. 자체 결정: stdlib sqlite3의 자동 트랜잭션 관리 대신 명시적 BEGIN/COMMIT은 사용하지 않고, 기존 `executescript` 흐름 유지(`executescript` 자체가 트랜잭션 외부 실행). 멱등성은 `notnull == 1` 체크가 보장.

**T-018B 자체 결정(2026-05-05 인계, 완료):**

1. `bootstrap_feeds_from_toml` 위치는 **`src/rss_wiki/pipeline/bootstrap.py` 신규 모듈** — `config.load_feeds` + `repo.upsert_feed`를 결합하는 결선층 성격이므로 `storage/`(데이터 액세스 단일 책임)에 두지 않고 결선층(`pipeline/`) 패턴을 따른다(M6 인터페이스 원칙 일관).
2. 시그니처 `bootstrap_feeds_from_toml(conn: sqlite3.Connection, path: str | Path) -> int` — 반환값은 처리된 피드 수(테스트/로깅 활용). `path` 인자명을 그대로 두고 `Path` 객체도 허용.
3. `upsert_feed`는 기존 `INSERT OR IGNORE` 동작 그대로 — 같은 URL 재호출 시 `enabled`/`name` 등 기존 상태를 유지(부트스트랩 멱등 + 운영자 수동 비활성 보존). PRD §11 "운영 SoT는 SQLite, TOML은 시드 전용" 의도와 일치.
4. `cli.run_daily`의 시그니처는 기존 `feeds: Sequence[FeedConfig]` 유지 — 단위 테스트의 격리(외부 IO 미접근, 인자 주입) 패턴이 무너지지 않도록 한다. DB 조회는 `cli.main`에서 수행해 `FeedConfig` 시퀀스로 변환 후 `run_daily`에 전달.
5. `cli.main`의 `daily` 분기 변경:
   - 기존: `feeds = load_feeds(args.feeds); run_daily(conn=conn, feeds=feeds, ...)`
   - 변경: `bootstrap_feeds_from_toml(conn, args.feeds); rows = list_feeds(conn, enabled_only=True); feeds = [FeedConfig(name=r["name"], url=r["url"]) for r in rows]; run_daily(conn=conn, feeds=feeds, ...)`
   - 기존 `from rss_wiki.config import FeedConfig, load_feeds`에서 `load_feeds`는 cli에서 직접 호출 안 함 — 미사용 import는 자체 결정으로 **제거**(린트 클린).
6. weekly/monthly 분기는 부트스트랩 미수행 — 발행만 수행하고 피드 변경 영향 없음(단순함 우선, 부트스트랩 비용 회피).
7. `bootstrap_feeds_from_toml`은 `conn.commit()` 미호출 — M6/M2 인터페이스 원칙(commit은 호출자=`cli.run_daily`의 상위 흐름이 책임) 일관. `cli.main`은 `run_daily` 진입 후에만 commit을 수행하나, 부트스트랩은 `run_daily` 진입 전이므로 첫 commit은 `run_daily` 내 commit 시점에 함께 반영(부트스트랩만 수행하고 fetcher 실패해도 피드 행은 commit 안 됨 — 수용 가능, 다음 daily 호출 시 다시 부트스트랩하여 회복).
8. 단위 테스트 위치 `tests/test_pipeline_bootstrap.py` 신규 — 다른 pipeline 서브모듈도 `tests/test_pipeline_{ingest,llm,publish}.py`로 분리되어 있어 일관 유지. cli 통합 테스트는 기존 `tests/test_cli.py`에 1 케이스만 추가(부트스트랩 호출 + DB feeds 조회 흐름 검증).
9. **모듈 경계:** `pipeline/bootstrap.py`(신규), `cli.py`(수정 — 6개 import 추가/제거 + main daily 분기) 외에 코드 디렉터리 무변경. `storage/`/`ingest/`/`llm/`/`publish/`/`pipeline/{ingest,llm,publish}.py`/`config.py`/`feeds.toml`/`feeds.example.toml`/`schema.sql`/`db.py` 미터치.

**인터페이스 원칙(M7 공통):**

- `web/` 모듈은 **결선층** — `storage`, `pipeline`(필요 시) 자유 import. 도메인 모듈(`ingest`/`llm`/`publish`) 직접 import는 권장하지 않음(웹은 조회/CRUD 중심).
- DB 커넥션은 FastAPI Depends 패턴으로 요청 단위 주입(`Depends(get_db)`). 각 요청 종료 시 close. 쓰기 라우트만 `commit()` 호출. WAL 모드 활성화로 수집 파이프라인과 동시 실행 시 쓰기 충돌 방지(PRD §13 끝).
- 템플릿은 stdlib 호환 — Jinja2만 사용, htmx/SPA 미도입(PRD §13 명시). 정적 자산은 인라인 CSS 한 곳.
- 마크다운 → HTML 변환은 `web/markdown.py` 단일 헬퍼로 제한 — 라이브러리 직접 import는 금지(라이브러리 교체 용이).
- form-encoded 입력은 Pydantic 모델 또는 `Form(...)` 의존성. URL 정규화는 `ingest.dedupe.normalize_url` 재사용.
- 단위 테스트는 `fastapi.testclient.TestClient` + 임시 SQLite 파일(`tmp_path`) 패턴 — 외부 네트워크/uvicorn 비의존.
- 보안: `host="127.0.0.1"` 고정. 인증 미도입(PRD §13 명시). CORS 미도입.

## 진행 원칙

- 한 사이클에 1~2개 작은 작업만 진행.
- 각 작업은 TASKS.md에서 acceptance/touch가 명시된 채로 추출.
- REVIEW.md가 도착하면 다음 사이클 PLAN/TASKS에 반영.

## 공통 운영 가이드 (REVIEW 반영)

- 파일/DB IO에서 발생하는 `FileNotFoundError`, `OSError` 등은 가능한 한 경로/원인 정보를 포함한 메시지로 래핑하여 운영 시 원인 파악을 쉽게 한다. (T-002 REVIEW 인계)
- 외부 의존성 추가는 PRD/PLAN에 명시된 경우에만. SQLite는 표준 라이브러리(`sqlite3`)로 충분.
- M6 결선층은 stdlib `logging` 기반 로깅을 표준으로 한다. `logger = logging.getLogger(__name__)`로 모듈 단위 로거 획득, 호출자가 logger 콜러블 주입 가능(테스트에서 mock 가능). 실패 격리 흐름은 WARNING 이상으로 기록.
