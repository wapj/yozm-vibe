# PLAN: rss-wiki

PRD.md를 기준으로 한 구현 계획. Python 3.12+ / uv / Typer 기반이다.

**현재 상태(M1~M11 완료)와 잔여 축(M12 디자인 품질 마감)**: M1~M6으로 CLI(`add`/
`remove`/`list`/`fetch`)와 순차 수집·요약·위키 생성 파이프라인이, M7(T16·T17·
T18)으로 asyncio 기반 병렬 LLM 요약과 `--concurrency` 옵션이 완성되었다.
이어 M8(T19·T20 웹 서버 스캐폴딩·디자인 시스템), M9(T21·T22 글 열람 + 후속
T23·T25 원문 링크 실화면 갭 마감), M10(T24 피드 관리 웹 UI 라우트, REVIEW T24
**PASS 15/15**), M11(T26 순수 상태·락 → T27 배선·구동·폴링 → T28 진행 UI·완료
리포트, REVIEW T28 **PASS 14/15**, `uv run pytest -x` 139 passed)까지 완료했다.
`web/`에는 수집 트리거·진행 상태(`progress.py`)·폴링 라우트·수집 실행 화면
(`fetch.html`/`fetch.js`)이 모두 배선되어 있다. 남은 축은 **M12(디자인 품질
마감)** 하나이며, PRD 3.3의 인터랙션 완성도·반응형·WCAG AA 대비를 통합 점검하고
REVIEW T24 비차단 메모 2건(`feed-list__info` CSS 미정의, `_form_value` URL
인코딩 경계 회귀 부재)을 해소해 마감한다.

- **병렬 LLM 요약**(PRD 4.3·8): **완료(M7)**. `summarize_article_async`
  (`asyncio.create_subprocess_exec`)·`pipeline.run_fetch_async`(세마포어 병렬)·
  CLI `fetch --concurrency`(기본 4) 배선까지 REVIEW PASS.
- **로컬 웹 UI `rss-wiki serve`**(PRD 3.1·3.2·3.3·8): FastAPI + Uvicorn +
  Jinja2 웹 서버, 피드 관리·수집 실행(진행 상황 실시간·중복 차단)·글 열람,
  그리고 디자인 품질 요구(디자인 토큰·읽기 최적화 타이포그래피·다크 모드·
  반응형·상태 표현·인터랙션 완성도·WCAG AA)가 전부 미구현이다. → **M8~M12
  (이번 라운드 잔여)**.

따라서 이번 라운드의 종료 조건은 미충족이며(DONE 생성 안 함), 잔여 M12(디자인
품질 마감)를 진행한다. M1~M7 자산(store·feeds·ingest·extract·summarize·wiki·
pipeline·cli·`run_fetch_async`)과 M8~M11 웹 계층(app·render·progress·템플릿·
정적 자원)은 그대로 재사용하며, M12는 신규 화면·모듈을 추가하지 않고 기존
CSS·마크업·폼 파싱의 완성도만 통합 점검해 마감한다(최소 변경 원칙).

## 모듈 책임 (목표 구조)

```
rss-wiki/
├─ pyproject.toml            # uv 프로젝트 정의, 의존성, 콘솔 스크립트
├─ src/rss_wiki/
│  ├─ __init__.py
│  ├─ cli.py                 # Typer 앱, 서브커맨드(add/remove/list/fetch)
│  ├─ config.py              # 경로 상수, feeds.json/state.json 위치
│  ├─ store.py               # feeds.json / state.json 읽기·쓰기
│  ├─ feeds.py               # 피드 등록/삭제/목록, 유효성 검증
│  ├─ ingest.py              # RSS/Atom 파싱, 새 글 판별(--limit)
│  ├─ extract.py             # 원문 HTML fetch + 본문 추출, RSS 본문 대체
│  ├─ summarize.py           # claude CLI 서브프로세스 호출, 한국어 요약
│  ├─ wiki.py                # 마크다운 파일·인덱스 생성/갱신, 슬러그 처리
│  └─ pipeline.py            # fetch 오케스트레이션(피드/글 루프, 실패 스킵, state 적재, 실행 리포트)
└─ tests/                    # pytest 단위 테스트
```

## 마일스톤

- [x] **M1. 프로젝트 스캐폴딩 & CLI 뼈대** (T1·T2 완료, 둘 다 REVIEW PASS)
  - [x] uv 프로젝트 초기화, `pyproject.toml`, 콘솔 스크립트 `rss-wiki`. (T1, REVIEW PASS 9/12)
  - [x] Typer 앱과 서브커맨드 스텁(add/remove/list/fetch) — 실제 로직 전, `--help` 동작. (T1)
  - [x] `config.py`(경로 상수), `store.py`(feeds.json/state.json 로드·저장) 기본 골격. (T2, REVIEW PASS 11/12)
  - [x] pytest 환경 구성(tests/ 디렉터리, dev 의존성) — REVIEW T1 메모 반영, T2에서 선행. (T2)
- [x] **M2. 피드 관리 (add / remove / list)** (T3·T4 완료)
  - [x] 저장 계층 실패 경로 회귀 테스트 + 손상 JSON 로드 예외 정책 확정. (T4, REVIEW PASS 12/12)
  - `add`: 피드 유효성 검증(feedparser로 파싱 성공 및 항목 존재) 후 등록.
  - `remove`: URL 또는 이름으로 삭제. `list`: 등록 피드 표 출력.
  - 중복 등록 방지, feeds.json 스키마 확정({name, url, added_at}).
  - 유효성 검증(feedparser 호출)은 검증 함수를 주입 가능한 형태로 분리해
    단위 테스트가 네트워크 없이 동작하도록 설계.
  - **REVIEW T2 메모 반영**: `load_feeds`가 손상된 JSON을 만났을 때의
    저장 계층 예외 정책은 T4에서 `StoreError`로 확정. 이 예외를 CLI에서
    사용자 대면 오류·비0 종료 코드로 변환하는 것을 T3에서 마무리한다.
  - [x] **REVIEW T2 메모 반영**: `_atomic_write` 실패 시 원본 보존과 손상 JSON
    로드 동작을 회귀 테스트로 고정. (T4에서 해소, `tests/test_store.py:71,84,97,105`)
- [x] **M3. 피드 수집 & 본문 확보** (T5·T6·T7 완료)
  - [x] `ingest.py`: feedparser로 각 피드 파싱, state.json 기준 처리 완료 글 스킵. (T5, REVIEW PASS 11/12)
  - [x] 첫 수집 시 최신 10개 상한, `--limit` 옵션. "첫 수집" 판정 기본값 —
    해당 피드의 어떤 항목도 `state.processed`에 없으면 첫 수집으로 간주. (T5)
  - [x] 글 식별자는 항목의 GUID(있으면), 없으면 링크 URL을 채택(PRD 5절). (T5)
  - [x] `ingest` 반환 dict 메타 계약(6개 키, `description`→`summary` fallback,
    `content` 매핑) 회귀 테스트 고정. (T7, REVIEW PASS 12/12)
  - [x] `extract.py`: 원문 HTML fetch + trafilatura 본문 추출, 실패 시 RSS description/content 대체. (T6)
  - **REVIEW T3 메모 반영**: 순수 로직 계층은 `feeds.py`와 동일하게 파서·HTTP
    fetch·본문 추출 함수를 **주입 가능한 형태**로 분리해 단위 테스트가 네트워크
    없이 동작하도록 설계한다. `add`의 기본 검증(`feedparser.parse(url)`)이 실
    네트워크에 의존하고 아직 실측되지 않은 점(REVIEW T3)은, extract의 HTTP fetch
    실패·타임아웃 처리 정책을 T6에서 확정하며 함께 점검한다.
  - **REVIEW T5 메모 해소(T7)**: `ingest.select_new_articles` 반환 article dict의
    메타 계약(6개 키, `description`→`summary` fallback, `content` 매핑)을 T7에서
    구체 값 단언 테스트 3건으로 고정 완료(`tests/test_ingest.py`, REVIEW T7 PASS).
  - **REVIEW T7 메모 이월(M5로)**: `_to_article`은 발행일을 파싱하지 않고 원문
    문자열을 그대로 넘긴다(`ingest.py:27`). 위키 파일명 `YYYY-MM-DD` 슬러그 생성 시
    발행일 정규화가 필요하므로, 정규화 책임을 어느 모듈이 질지는 M5 착수 시 결정한다.
    `title`/`link`/`published` 값 매핑 단언 보강(선택)도 M5 `published` 정규화와
    함께 다룬다.
- [x] **M4. LLM 요약** (T8 완료)
  - `summarize.py`: `claude -p` 비대화 모드 서브프로세스 호출. `feeds.py`/
    `ingest.py`/`extract.py`와 동일하게 **서브프로세스 실행 함수를 인자로 주입**
    받아(기본값은 `claude -p` 호출) 단위 테스트가 프로세스·네트워크 없이
    동작하게 설계한다. (T8)
  - 한국어 요약(3~5줄 + 핵심 포인트 불릿), 메타데이터(원제·링크·발행일·피드명) 포함.
    - 피드명은 article dict에 없으므로(`ingest._to_article`은 글 메타만 담음)
      `summarize`가 피드명을 별도 인자로 받아 반환 메타에 포함한다. (T8, 자체 결정)
    - 반환은 순수 데이터(요약 텍스트 + 메타 dict)이며, 마크다운 조립은 M5 wiki의
      책임으로 분리한다. (T8)
  - `claude` 미설치(`FileNotFoundError`) 또는 비0 종료 시 정의된 예외
    (`SummarizeError`)로 올려, 미설치는 실행 불가(비0 종료 코드), 요약 실패는
    글 단위 건너뜀(M6 리포트)으로 분기할 수 있게 한다. 예외 정의·발생까지가
    T8 범위이며 CLI 종료 코드 배선·건너뜀은 M6 범위다. (T8)
  - **REVIEW T6 이월(M4 무관, M6 유지)**: 기본 `fetch`/`extract` 실호출부
    통합 확인과 CLI `fetch` 배선·CliRunner 회귀는 M6로 유지한다.
- [x] **M5. 위키 생성** (T9·T10·T11 완료)
  - [x] 글 1개당 `articles/YYYY-MM-DD-<슬러그>.md` 1개, 슬러그 충돌 시 접미사(순수 로직, 실제 파일 쓰기는 T11). (T9)
  - [x] `index.md`, `feeds/<슬러그>.md`, `daily/YYYY-MM-DD.md` 마크다운을 조립하는
    순수 함수(`render_index`/`render_feed_page`/`render_daily_page`). (T10, REVIEW PASS 11/12)
  - [x] 조립 결과와 개별 글 파일을 `wiki/` 아래로 실제로 쓰고 인덱스를 재생성/갱신. (T11)
  - [x] 상태(state.json)와 산출물(wiki/) 분리로 수동 편집·삭제해도 중복 수집 없음. (T11)
  - **책임 분리(자체 결정)**: `wiki.py`는 다른 모듈과 동일하게 순수 로직 계층으로
    두되, 이 마일스톤은 (1) 개별 글 조립·슬러그·발행일 정규화 등 파일 시스템 무의존
    순수 함수(T9), (2) 인덱스/피드/데일리 페이지 마크다운을 조립하는 순수 함수(T10),
    (3) 개별 글·인덱스의 실제 파일 쓰기 통합(T11)으로 나눈다. T9→T10→T11은
    순수 로직 우선·I/O 나중 패턴으로, 다른 모듈(주입형 순수 로직)과 일관된다.
  - **REVIEW T9 이월 해소(T10)**: (1) `render_article`이 `published`를 정규화 없이
    원문 그대로 상단 메타에 노출하나 `article_filename`은 `normalize_date` 결과
    (`YYYY-MM-DD`)를 쓴다(`wiki.py:71` vs `wiki.py:51`). 표시용 발행일도
    `normalize_date` 결과로 통일해 파일명 날짜와 본문 날짜 형식을 일치시킨다
    (자체 결정: 표시 형식은 되돌리기 쉬움). (2) `render_article` 레이블-값 결합
    미검증(비차단) — T10 테스트에서 마크다운 구조 단언을 보강한다.
  - **REVIEW T9 이월(T11)**: `slugify` fallback "untitled" 고정은 무제목 글이
    같은 날 여럿 들어오면 접미사(`-2`,`-3`)로만 구분된다. 식별자 기반 fallback이
    필요하면 T11 호출부에서 `slugify`/`article_filename`에 `fallback` 키워드로
    주입한다(T9 IMPL 자체 결정 기록과 일치).
  - **인덱스 입력 계약(자체 결정, T10)**: `render_*` 함수는 파일 시스템에 의존하지
    않도록, 각 글의 표시 메타(파일명·제목·발행일·수집일·피드명)를 담은 dict 리스트를
    입력으로 받는 순수 함수로 설계한다. 리스트 조립(무엇을 넘길지)은 T11 호출부의
    책임이며, 데이터 계약은 되돌리기 쉬운 수준이므로 IMPL에 근거를 남긴다.
  - **REVIEW T10 이월 해소(T11)**: (1) `render_index` "최신 글" 정렬이 함수 내부에
    없어 입력 리스트 순서대로 나열된다(`wiki.py:97-101`). T11 파일 쓰기 호출부에서
    정렬 책임을 명시적으로 배선(발행일 또는 수집일 내림차순)하고 회귀로 고정한다.
    (2) 개별 글 링크 말미 `(published)` 표기 형식은 현재 미검증(비차단). 표시 형식이
    굳어지는 T11 통합 테스트에서 함께 고정하는 것을 권장한다.
  - **인덱스 전체 재생성 입력원(M6 결정 사항)**: `fetch` 실행마다 인덱스를
    "재생성 또는 갱신"하려면(PRD 4.4) 이번 수집분뿐 아니라 **누적 전체 글**의 표시
    메타가 필요하다. 그 전체 집합을 어디서 얻는가(수집 메타를 상태에 적재 vs
    `wiki/articles/` 스캔)는 저장 형식에 영향을 줄 수 있는 결정이므로 T11이 아닌 M6
    파이프라인 배선 시점에 정한다. T11은 전달받은 표시 메타 리스트만으로 쓰는
    입력 주도(input-driven) 방식으로 한정해 이 결정과 분리한다(자체 결정: 되돌리기 쉬움).
  - **REVIEW T7 이월 해소(T9)**: `_to_article`이 발행일을 원문 문자열로 그대로
    넘기는 점(`ingest.py:27`) — 파일명 `YYYY-MM-DD` 슬러그를 위해 발행일 정규화가
    필요하다. 정규화 책임은 `wiki.py`가 진다(파일명 슬러그 생성이 wiki 소관).
    `articles/` 파일명 날짜는 **발행일**을 정규화해 쓰고, 발행일 부재·파싱 실패
    시 **수집일**로 대체한다(자체 결정 — PRD 4.4는 `daily/`만 "수집일"로 명시,
    `articles/` 날짜 기준은 미명시이므로 발행일 우선이 자연스럽다). `daily/`는
    PRD 명시대로 수집일 기준(T10).
  - **REVIEW T8 이월 해소(T9)**: `_default_run`이 stdout을 후처리 없이 반환하므로
    (`summarize.py:27`) summary 앞뒤 공백·개행 정리는 `wiki.py`의 마크다운 조립
    시점에서 처리한다.
  - **프롬프트 형식 지시 검증(T9, REVIEW T8 비차단 메모)**: 요약 마크다운 조립
    검증 시 "3~5줄 + 핵심 포인트 불릿" 형식과의 연계 고정을 검토한다.
- [x] **M6. 실패 정책 & 리포트 + `fetch` 파이프라인 배선** (T12·T13·T14·T15 완료)
  - [x] **REVIEW T14 메모 1·2 반영(T15, 완료)**: T14는 PASS(11/12)이나 테스트
    충실도 감점 근거가 남았다. T14 내용이 "회귀로 고정"하라 요구한 5개 종료 코드
    경계 중 2개 — (a) 새 글 없음→0, (b) 등록 피드 없음→0 — 의 독립 회귀가 부재해
    `total_failed==0` 분기로 간접 경유될 뿐이었다. T15에서 두 경계 독립 회귀를
    `tests/test_cli.py`(`test_fetch_no_new_articles_exits_zero`,
    `test_fetch_no_feeds_registered_exits_zero`)에 추가해 T14 acceptance의 회귀
    고정을 완결했다. 코드 동작은 이미 정합이므로 `cli.py`는 불변, 테스트·문서만
    다뤘다. REVIEW T14 메모 2(IMPL/JOURNAL의 test_cli.py "10 passed" 수치 오기,
    실제 9건)도 T15에서 실제 값(신규 2건 추가 후 11건)으로 정정했다.
  - **REVIEW T13 메모 1 반영(T14, 완료)**: T13은 PASS(12/12)로 확정되었으나, 종료 코드
    경계(`cli.py:135-138`)가 "피드 파싱 성공 + 그 피드 글 전부 실패(요약 산출 0건)"를
    종료 코드 0으로 매핑하는 점이 PRD 7("전체 실패는 비0")의 산출-단위 해석과
    어긋났다. T14에서 종료 코드 판정을 `articles_succeeded == 0`(글 산출 기준)으로
    좁혀 정합하고 경계 회귀(`tests/test_cli.py`)를 고정했다(자체 결정: 되돌리기 쉬움).
  - **REVIEW T13 메모 2(비차단, DONE 비차단)**: 실 환경 `claude` + 실 RSS + 실
    HTTP를 사용하는 종단 `fetch --limit 1` 스모크는 이번까지도 미실측이다. 다만
    이는 라이브 외부 서비스(네트워크·`claude` CLI)에 의존해 결정적 acceptance로
    고정하기 어렵고, 모든 단위 경로는 주입형 테스트로 검증되어 PRD 각 요구에
    대응하는 코드가 존재한다. 따라서 종단 스모크는 **DONE 차단 요소가 아닌**
    수동 후속 검증으로 남긴다(사람이 실환경에서 1회 실행해 회귀 기준선 확보 권장).
  - **분할 근거**: `fetch` 배선은 (1) 피드/글 루프·실패 스킵·state 적재·리포트를
    수행하는 순수 오케스트레이션 계층과 (2) 그 결과를 실제 파일·`state.json`으로
    영속화하고 종료 코드로 매핑하는 CLI 계층으로 나뉜다. 다른 모듈과 동일한
    "순수 로직 우선, I/O 나중" 패턴을 따라 T12(순수)→T13(I/O·CLI)로 진행한다.
  - [x] **T12. `pipeline.run_fetch` 순수 오케스트레이션** (완료, REVIEW PASS 11/12)
    - `pipeline.py`(순수 로직, 주입형): `select`/`extract`/`summarize`와 처리
      시각(`now`)·수집일(`collected_date`)을 주입받아 피드/글을 순회한다.
      파일 시스템·네트워크·프로세스에 접근하지 않는다.
    - 피드 단위 실패(`ingest.FeedParseError`)는 해당 피드를 건너뛰고 계속.
      글 단위 실패(`extract.ArticleExtractionError`/`summarize.SummarizeError`)는
      해당 글을 건너뛰되 **state에 처리 완료로 기록하지 않아** 다음 `fetch`에서
      재시도되게 한다(PRD 7).
    - 성공 글은 `state["processed"][id]`에 `{processed_at, status, meta}`로 적재.
      `meta`에는 인덱스 누적 재생성에 필요한 표시 메타(파일명·제목·정규화 발행일·
      수집일·피드명)를 담는다(누적 인덱스 입력원 결정, 아래 미해결 의사결정 참조).
    - **파일명 안정성**: 파일명은 성공 시점에 한 번 배정(`wiki.article_filename`,
      state에 누적된 기존 파일명 집합과 대조)하고 state에 저장한다. 이후 `fetch`에서
      같은 날짜·슬러그 글이 들어와도 기존 파일명이 바뀌지 않도록 접미사로 회피한다.
    - 실행 리포트(피드/글 성공·실패 건수와 사유)를 반환값에 담는다. 실제 파일
      쓰기(`write_wiki`)·`state.json` 저장·종료 코드 매핑·stdout 출력은 T13.
  - [x] **T13. CLI `fetch` 배선 + 누적 인덱스 쓰기 + 종료 코드 + CliRunner 회귀** (완료, REVIEW PASS 12/12)
    - `cli.py`의 `fetch` 스텁(`cli.py:69`)을 배선: `load_feeds`/`load_state` →
      `run_fetch` → `write_wiki`(이번 배치의 글 파일 + **state에 누적된 전체 표시
      메타**로 index/feeds/daily 재생성) → `save_state` → 리포트 stdout 출력.
    - **누적 인덱스 반영(REVIEW T11 이월 해소)**: `write_wiki`는 현재 입력 주도로
      이번 배치만 인덱스에 반영한다(`wiki.py:160-161`). 개별 글 파일은 이번 배치만
      쓰되, index/feeds/daily는 state에 누적된 전체 표시 메타로 재생성하도록
      `write_wiki` 시그니처를 확장한다(기존 T11 테스트와 하위 호환 유지).
    - **claude 미설치 프리플라이트**: `fetch` 진입 시 `claude` 실행 가능 여부를
      확인해, 없으면 명확한 메시지와 비0 종료 코드로 중단한다(PRD 6·7). 이로써
      개별 글 요약 실패(`SummarizeError` → 글 스킵)와 "실행 불가"(claude 미설치 →
      전체 중단)를 분리한다.
    - **종료 코드**: 부분 실패(성공 1건 이상 + 실패 존재)는 0, 전체 실패
      (시도했으나 성공 0건)·실행 불가(claude 미설치)는 비0(PRD 7).
    - **REVIEW T3 메모 이월(비차단) 해소**: `typer.testing.CliRunner`로
      `tests/test_cli.py`를 만들어 add/remove/list/fetch의 사용자 대면 오류·종료
      코드를 회귀에 고정한다(`StoreError`/`DuplicateFeedError`/
      `FeedValidationError`/`FeedNotFoundError` 변환 경로 포함).
    - **write_wiki fallback·(published) 표기(REVIEW T11 이월, 비차단)**: `published`
      부재 글이 `collected_date`로 파생되는 경로와 링크 말미 `(published)` 표기
      형식을 이 통합 테스트에서 함께 고정한다.
    - **누적 인덱스 파일명 일관성(REVIEW T12 이월 해소)**: `run_fetch`는 성공 글의
      파일명을 배정해 `state.meta.filename`에 저장한다(`pipeline.py:79-91`). 현재
      `write_wiki`는 파일명을 자체 재계산하므로(`wiki.py:174-175`) state에 저장된
      파일명과 어긋날 수 있다. T13에서 index/feeds/daily 재생성 입력을 **state에
      누적된 표시 메타(파일명 포함)**로 확장할 때, 개별 글 파일명과 인덱스 링크가
      state가 배정한 파일명과 정확히 일치하도록 배선한다. `write_wiki`는 하위 호환을
      위해 기존 시그니처를 유지하되 누적 표시 메타를 주입받는 경로를 가법적으로 추가한다
      (자체 결정: 되돌리기 쉬움).
    - **입력 state 불변성 회귀(REVIEW T12 이월 해소, 비차단)**: `run_fetch`는 입력
      `state`를 얕은 복사로 보존하나(`pipeline.py:49`) 원본 `state["processed"]`가
      변경되지 않았는지 직접 단언하는 테스트가 없다. T13 통합 테스트에서 원본 불변성
      회귀를 함께 고정한다.
    - **본문 출처(원문/RSS 대체) 리포트 반영 결정(REVIEW T12·T6 이월)**: `extract_body`는
      `source`(원문 추출/RSS 대체)를 반환하나 `run_fetch`는 이를 리포트에 담지 않는다.
      T13 리포트 stdout 설계 시 출처 통계를 포함할지 결정한다(기본값: 최소 리포트에는
      성공/실패 건수만 표시하고 출처 통계는 생략 — 되돌리기 쉬움. 자체 결정).

## 신규 마일스톤 (PRD 확장 반영: 병렬 요약 + 웹 UI)

목표 추가 구조:

```
src/rss_wiki/
├─ summarize.py     # summarize_article_async 추가 (asyncio.create_subprocess_exec)
├─ pipeline.py      # run_fetch 병렬 경로(세마포어), 인덱스/state 기록 직렬화
├─ cli.py           # fetch --concurrency 옵션, serve 서브커맨드
└─ web/
   ├─ app.py        # FastAPI 앱 팩토리, 라우트
   ├─ render.py     # wiki/ 마크다운 → HTML 렌더링(순수 로직)
   ├─ progress.py   # 수집 진행 상황 상태(인메모리, 단일 실행 락)
   ├─ templates/    # Jinja2 (base, index, feed, daily, article, feeds 관리)
   └─ static/       # 디자인 토큰 CSS, 다크 모드, 경량 JS(SSE/폴링)
```

- [x] **M7. 병렬 LLM 요약** (PRD 4.3·8) — T16·T17·T18 전체 완료(T16·T17 REVIEW PASS 11/12, T18 `uv run pytest -x` 87 passed)
  - [x] `summarize.py`: `asyncio.create_subprocess_exec("claude", "-p", ...)`를 쓰는
    `summarize_article_async` 추가. 반환 계약(summary·title·link·published·
    feed_name)과 `SummarizeError`(미설치=`FileNotFoundError`, 비0=반환코드) 의미는
    동기판과 동일. 서브프로세스 실행 함수를 주입 가능하게 유지해 단위 테스트가
    실제 프로세스 없이 async fake로 동작하게 설계. 동기 `summarize_article`은
    하위 호환으로 유지(파이프라인 이관은 M7 후속). (T16, REVIEW PASS 11/12)
  - [x] **T17. `pipeline.run_fetch_async` 순수 async 병렬 오케스트레이션**: 피드별
    새 글 선정(`select`)은 순차로 두어 피드 파싱 실패 격리를 유지하되, 글 단위
    본문 확보+요약은 `asyncio.Semaphore(concurrency)`로 동시 실행한다. 개별 글
    실패(`ArticleExtractionError`/`SummarizeError`)는 다른 글에 영향 없음(PRD 4.3·7).
    동기 `extract`는 이벤트 루프를 막지 않도록 `asyncio.to_thread`로 감싼다(자체
    결정: 되돌리기 쉬움). **병렬 완료 후** 파일명 배정·state 적재·리포트 집계는
    입력 순서(피드×글)대로 직렬 수행해 파일명 접미사(`-2`)·리포트가 실행마다
    달라지지 않는 결정성을 보장한다. 반환 계약(batch/state/report)은 동기
    `run_fetch`와 동일. 동기 `run_fetch`는 하위 호환 유지(파일 시스템·프로세스
    미접근 순수 계층 유지). CLI 배선은 T18. (T17 완료, REVIEW PASS 11/12)
  - [x] **T18. CLI `fetch --concurrency` 배선 + async 구동 + CliRunner 회귀 갱신**:
    `cli.py`의 `fetch`에 `--concurrency`(기본 4) 옵션을 추가하고, 동기
    `run_fetch` 호출을 `asyncio.run(run_fetch_async(...))`로 교체한다. 프리플라이트·
    누적 인덱스 쓰기·종료 코드 판정·리포트 출력 순서는 불변(T13·T14 자산 재사용).
    기존 CliRunner 회귀를 async 경로에 맞춰 갱신하고, `--concurrency` 값이
    파이프라인에 전달되는지 회귀로 고정한다. 동기 `run_fetch`가 더 이상 호출되지
    않으면 정리 여부를 이 시점에 결정한다(되돌리기 쉬움). (T18)
  - **REVIEW T17 메모 반영(T18에서 해소)**: (1) [테스트 충실도] `run_fetch_async`의
    `FeedParseError` 격리 분기(`pipeline.py:148-151`)가 async 회귀로 미커버다.
    동기판 `test_run_fetch_skips_feed_on_parse_error_and_continues_other_feeds`
    (`test_pipeline.py:70-96`)에 대응하는 async 버전(한 피드 `select`가
    `FeedParseError`를 올릴 때 그 피드만 `report["feeds"]["failed"]`에 집계되고
    다른 피드 글은 병렬 처리됨을 단언)을 T18에서 `tests/test_pipeline.py`에 함께
    고정한다. (2) [선택] `test_run_fetch_async_respects_concurrency_limit`의 상한
    단언(`max_seen <= concurrency`)에 하한(`max_seen >= 2`)을 더해 세마포어가
    병렬을 과도 억제(실질 순차화)하는 회귀도 잡는다.
  - **승계(비차단, DONE 비차단)**: 실환경 `claude` CLI 종단 실호출(동기·async
    공통)은 여전히 미실측이다. T18 CLI 배선 완료 후 사람이 실환경에서
    `fetch --limit 1 --concurrency 2`를 1회 실행해 회귀 기준선을 확보할 것을
    권한다. 라이브 외부 서비스(네트워크·`claude` CLI) 의존으로 결정적 acceptance
    고정이 어려워 DONE 차단 요소가 아닌 수동 후속 검증으로 유지한다.
  - **REVIEW T16 메모 해소(T17에 포함)**: `_default_run_async`의 `returncode != 0`
    분기(`summarize.py:62-65`)와 `stdout.decode()`는 현재 미커버 코드다. 동기판
    `_default_run`(`check=True`)과 달리 async는 반환 코드를 수동 확인해
    `CalledProcessError`를 직접 구성하므로 버그 위험이 가장 높은 지점이다. T17에서
    `asyncio.create_subprocess_exec`를 스텁으로 대체해 비0 종료 시 `CalledProcessError`
    생성·정상 종료 시 `decode` 반환을 직접 단언하는 회귀 2건을 함께 고정한다.
    async 요약을 병렬로 처음 소비하는 태스크가 T17이므로 자연스럽게 흡수한다.
  - **승계(비차단)**: 실환경 `claude` CLI 종단 실호출(동기·async 공통)은 여전히
    미실측이다. T18 CLI 배선 완료 후 사람이 실환경에서 `fetch --limit 1 --concurrency 2`
    를 1회 실행해 회귀 기준선을 확보할 것을 권한다(라이브 외부 서비스 의존으로
    결정적 acceptance 고정이 어려워 DONE 비차단 수동 후속으로 유지).
  - 착수 순서: T16(async 요약 단위, 완료) → T17(순수 병렬 오케스트레이션 +
    `_default_run_async` 회귀, 완료) → **T18(CLI `--concurrency` 배선, 이번 사이클)**.

- [x] **M8. 웹 서버 스캐폴딩 & 디자인 시스템 기반** (PRD 3.1·3.3·8) — 완료
  (T19 REVIEW PASS 12/15, T20 REVIEW PASS 14/15). "순수 로직 우선, I/O 나중"
  패턴에 맞춰 프레임워크·서버 배선(T19)과 디자인 시스템 골격(T20)으로 분할했다.
  - [x] **T19. 웹 서버 스캐폴딩 & `serve` 명령** (완료, REVIEW PASS 12/15)
    - 의존성 추가: `fastapi`, `uvicorn`, `jinja2`(pyproject `dependencies`).
      PRD 8 명시 스택이므로 되돌리기 어려운 결정이 아니다.
    - `web/app.py`: `create_app() -> FastAPI` 앱 팩토리. Jinja2
      템플릿(`web/templates/`)·정적 파일(`web/static/`, `StaticFiles`) 마운트.
      경로는 `config.py` 패턴과 일관되게 패키지 기준 절대경로로 해석.
    - `cli.py`에 `serve` 서브커맨드 추가(`--host` 기본 `127.0.0.1`·`--port`
      기본 `8000`, `uvicorn.run` 구동, 로컬 전용). 블로킹 서버이므로 실기동은
      테스트하지 않고 앱 팩토리를 TestClient로 검증.
    - 최소 라우트 `GET /` → `base.html` 렌더(200, `text/html`). 완성도 있는
      디자인·상태 표현은 T20 이후.
    - acceptance: `serve --help` 종료 코드 0(`--host`·`--port` 노출),
      `--help`가 add/remove/list/fetch/serve 5개 표시, `TestClient` `GET /`
      200·`text/html`, `uv run pytest -x` 회귀 없음.
  - [x] **T20. 디자인 시스템 기반** (완료, REVIEW PASS 14/15)
    - `static/`에 색상 팔레트·타이포그래피·간격 스케일을 CSS 커스텀
      프로퍼티(토큰)로 한 곳에 정의. 라이트/다크 테마(시스템 설정 추종 +
      수동 전환 토글), 공통 레이아웃(`base.html`) 확장, 반응형 기본 골격.
    - 라우트 스텁과 빈/오류 상태 기본 화면 골격을 두어 이후 마일스톤이 채운다.
    - `base.html`이 `/static`의 토큰 CSS를 링크하도록 확장하고, 헤더·본문
      컨테이너(가독 폭)·다크 모드 토글을 골격에 배치한다.
    - **REVIEW T19 메모 반영(테스트 충실도)**: `test_web_app.py`에 렌더된
      본문 단언(예: `assert "rss-wiki" in response.text`)과 `/static`의 토큰
      CSS를 실제로 서빙하는지(200·`text/css`)의 회귀를 추가해, 빈 응답
      통과-위장과 정적 마운트 회귀를 함께 차단한다.
    - acceptance 예: 다크 모드 토글 동작(정적 검증 가능한 범위), 디자인
      토큰이 한 곳에서 정의되어 전 화면 참조, 창 축소 시 레이아웃 무결,
      `/static/<토큰 css>` 200·`text/css`, `GET /` 본문 텍스트 단언 통과.
    - **승계(비차단)**: 다크 모드 토글·반응형 레이아웃의 브라우저 종단
      확인은 블로킹 서버 특성상 수동 후속으로 남긴다. 자동 acceptance는
      정적 검증 가능한 범위(CSS 서빙·본문 단언·토큰 정의 위치)로 고정한다.
  - **REVIEW T18 메모 2 반영(동기 `run_fetch` 정리 결정)**: 동기
    `pipeline.run_fetch`가 T18 이후 CLI에서 호출되지 않는다. REVIEW T18은 웹 UI
    착수 전 동기·async 두 오케스트레이션 경로의 계약 중복 정리 여부를 재점검할
    것을 남겼다. **결정(자체 결정, 되돌리기 쉬움): 동기 `run_fetch`와 그 회귀
    6건을 당분간 유지한다.** 근거 — 수집 실행 웹 UI(M11)는 CLI와 동일한
    `run_fetch_async`를 재사용하므로 동기 경로가 신규 소비처를 얻지 않아 두 경로가
    M8~M12 동안 발산할 위험이 커지지 않는다. 제거는 순수 데드코드·테스트 정리라
    언제든 가능하고 마일스톤 경계 이동을 늘리지 않는 편이 최소 변경 원칙에
    부합한다. 유지보수 마찰이 실제로 확인되면 그때 별도 정리 태스크로 다룬다.
  - **REVIEW T18 메모 1 승계(비차단, DONE 비차단)**: 실환경 `claude` CLI 종단
    실호출(`fetch --limit 1 --concurrency 2`)은 라이브 외부 서비스 의존으로
    결정적 acceptance 고정이 어려워 미실측이다. 사람이 실환경에서 1회 실행해
    병렬 요약 경로의 회귀 기준선(정상 출력·종료 코드 0)을 확보할 것을 권장하는
    수동 후속 검증으로 승계한다. `serve` 실기동 종단 확인도 블로킹 서버 특성상
    동일하게 수동 후속으로 남긴다.

- [x] **M9. 글 열람 (읽기 경험)** (PRD 3.2-3·3.3) — 완료 (T21·T22 완료, REVIEW T22 PASS 15/15).
  후속 원문 링크 실화면 갭은 T23(순방향 교정)→T25(저장 콘텐츠 렌더 시점 해소)로
  M10 선행에서 마감한다.
  - **REVIEW T22 메모(후속 필수)**: (1) 원문 링크가 실사용자 화면에서 클릭 불가.
    `wiki.render_article`이 `- 원문 링크: {link}` 평문으로 적어 `markdown`이
    자동 링크로 변환하지 않아 개별 글 화면의 원문 `<a href>`가 0건이다.
    PRD 3.2-3의 "원문 링크" 요구를 실화면에서 충족하려면 링크 형식을
    `[원문]({link})` 마크다운 링크로 바꿔야 한다(T23). (2) 발행일 부재 시 목록
    메타에 구분점만 남는 미관 이슈(T23에 함께 처리).
  M5(T9→T10→T11)·M8(T19→T20)에서 확립한 "순수 로직 우선, I/O·라우트 나중"
  패턴을 따라 순수 렌더링(T21)과 FastAPI 라우트·템플릿 배선(T22)으로 분할한다.
  - `web/render.py`: `wiki/` 마크다운 산출물을 HTML로 렌더링(순수 로직,
    주입형 입력). 위키 파일과 웹 화면 내용 일치 보장(PRD 3.2-3).
  - 전체 최신순 목록·피드별 목록·날짜별 목록·개별 글 페이지(요약문·핵심
    포인트·원문 링크·발행일·피드명). 목록/글 데이터 소스는 `state.json` 표시
    메타(`processed[id].meta` — filename·title·published·collected_date·
    feed_name)와 `wiki/articles/*.md` 마크다운(M6에서 확정한 누적 표시 메타
    재사용). 개별 글 본문은 `wiki/articles/<filename>.md`를 HTML로 렌더해
    위키 파일과 화면이 항상 일치(PRD 3.2-3).
  - 읽기 경험: 본문 폭 65~75자, 충분한 행간, 위계 있는 제목 체계(M8 `.prose`
    토큰 재사용).
  - 상태 표현: 로딩·빈 목록·오류 각각 명확한 화면(M8 `.state-*` 골격 소비).
  - **마크다운→HTML 렌더링 방식(자체 결정, 미해결 의사결정 표)**: `markdown`
    라이브러리를 채택한다. `wiki/` 산출물을 표준·안전하게 HTML로 변환하며 교체
    용이(되돌리기 쉬움).
  - [x] **T21. `web/render.py` 순수 렌더링 로직** (완료, REVIEW PASS 12/12)
    - `markdown` 의존성 추가(pyproject `dependencies`). PRD 미명시이나 PLAN
      미해결 의사결정 표에서 (a) `markdown`으로 채택한 되돌리기 쉬운 결정.
    - `web/render.py`(순수 로직, 파일 시스템·네트워크 무접근): (1) `state.json`
      표시 메타 dict 리스트를 입력받아 전체 최신순 목록·피드별 그룹·날짜별
      그룹의 뷰모델을 구성하는 순수 함수(정렬·그룹핑·피드 슬러그 매핑은
      `wiki.slugify` 재사용으로 링크 일관성 보장), (2) 개별 글 마크다운
      문자열을 `markdown`으로 HTML로 변환하는 순수 함수. 입력(메타 리스트·
      마크다운 텍스트)을 주입받아 단위 테스트가 파일·서버 없이 동작하게 설계.
    - 라우트 배선·템플릿·상태 화면·CSS는 T22. T21은 순수 함수와 그 단위
      테스트까지만 담당한다.
    - acceptance: 최신순 정렬(published 내림차순)·피드별 그룹·날짜별 그룹
      뷰모델 구성 회귀, 피드 슬러그가 `wiki.slugify`와 일치(인덱스 링크
      정합) 단언, 마크다운→HTML 변환이 제목(`<h1>`)·불릿(`<ul><li>`)·링크
      (`<a href>`)를 산출하는 회귀, 빈 메타 리스트에서 빈 뷰모델 반환(빈
      목록 상태 대비), `uv run pytest -x` 회귀 없음.
    - touch: `pyproject.toml`(`markdown` 추가), `src/rss_wiki/web/render.py`
      (신규), `tests/test_render.py`(신규). `app.py`·템플릿은 미변경(T22).
  - [x] **T22. 글 열람 라우트·템플릿 배선 + 읽기 경험 CSS** (완료, REVIEW PASS 15/15)
    - `app.py`에 목록·개별 글 라우트 배선: `GET /`(전체 최신순), 피드별·
      날짜별 목록, 개별 글 페이지(`wiki/articles/<filename>.md` 렌더). `state.json`
      로드 + `wiki/` 마크다운 읽기 → `render.py` 순수 함수 호출 → Jinja2 템플릿.
    - 상태 표현: 빈 목록(글 0건)·오류(파일 부재 등) 화면을 M8 `.state-*`
      골격으로 채운다.
    - 읽기 경험 CSS: 개별 글 본문에 `.prose`(가독 폭 70ch·행간) 적용, 목록
      위계 정리.
    - **REVIEW T20 메모 2 해소(테스트 완결성)**: 화면이 M8 토큰·테마를 실제로
      소비하는 이 시점에 다크 셀렉터 존재·`theme.js` 200 서빙을 회귀로 고정해
      통과-위장 여지를 줄인다.
    - **REVIEW T20 메모 3(WCAG AA 대비)**: 실제 텍스트/배경 조합이 확정되므로
      라이트/다크 각 조합의 대비비를 1회 정적 측정 확인한다.

- [x] **M10. 피드 관리 웹 UI** (PRD 3.2-1) — 완료 (선행 T23·T25 + 본체 T24 완료, REVIEW T24 **PASS 15/15**, `uv run pytest -x` 119 passed)
  - 피드 목록 조회, URL 등록(유효성 검증 재사용 — `feeds.py` 로직 공유),
    삭제. CLI와 동일한 `feeds.json`·`state.json`을 공유(진실 소스 단일).
  - 폼 검증 오류·중복 등록 등을 사용자 대면 메시지로 표현.
  - [x] **T23. REVIEW T22 메모 해소 — 원문 링크 실화면 클릭 + 발행일 부재 구분점**
    — 완료(조건부 PASS 11/15). `wiki.render_article`의 링크 줄을 마크다운 링크
    (`- 원문: [{link}]({link})`)로 바꾸고 `_article_list.html` 발행일 부재 구분점을
    조건부 처리했다. **다만 순방향 생성 경로만 교정**되어, 저장된
    `wiki/articles/*.md`가 여전히 구식 평문 `- 원문 링크: https://...`를 유지하는
    기존 콘텐츠는 실화면에서 원문 `<a href>`가 0건(REVIEW T23 실데이터 확인).
    발행일 부재 구분점(비차단)은 정상 해소.
  - [x] **T25. REVIEW T23 블로킹 승계 해소 — 저장 형식 무관 원문 링크 실화면 클릭 + 종단 회귀**
    (완료, REVIEW PASS 15/15, `uv run pytest -x` 112 passed). REVIEW T23이 권한 (b) 렌더 시점 정규화를 채택했다.
    `web/render.render_article_html`이 `markdown` 변환 **전에** 원문 링크 줄의 평문
    URL을 마크다운 링크로 정규화하도록 확장해, 저장 형식(구식 평문·신규 마크다운
    링크)과 무관하게 개별 글 라우트가 저장 `.md`를 읽어 렌더한 실화면에 원문
    `<a href>`가 산출되게 한다. python-markdown 표준은 bare URL 자동링크를
    지원하지 않으므로(`extensions=['extra']`만으로 미해결) 서드파티 의존성 도입
    대신 대상 줄 한정 정규식 전처리가 가장 단순하다(자체 결정: 되돌리기 쉬움).
    저장 파일 마이그레이션(a)은 본문 요약이 `state.json`에 없어 재생성 불가하고
    범위가 넓어 채택하지 않는다. **REVIEW T23 메모 2(테스트 승계)** — 저장 `.md`를
    라우트로 읽어 렌더한 실화면에서 원문 `<a href>` 산출을 단언하는 종단 회귀를
    함께 추가해 격리 함수 통과와 실화면 갭의 재발을 막는다.
  - [x] **T24. 피드 관리 라우트 — 목록 조회 + 등록/삭제 핸들러** (M10 본체, 완료 REVIEW PASS 15/15).
    `GET /feeds-admin`(등록 피드 목록), `POST` 등록(유효성 검증 — `feeds.py`
    재사용), `POST` 삭제. CLI와 동일한 `feeds.json` 공유. 검증 오류·중복
    등록을 사용자 대면 메시지로 표현.
    - **feeds.json 진실 소스 공유**: `store.load_feeds`/`store.save_feeds`로
      CLI와 동일 파일을 읽고 쓴다. `create_app`에 `feeds_path`(기본
      `config.FEEDS_PATH`) 주입 인자를 `state_path`/`wiki_dir`와 동일 패턴으로
      추가해 테스트가 임시 경로를 격리 주입한다.
    - **validate 주입(네트워크 격리, 자체 결정)**: `feeds.add_feed`의 기본
      `validate`(`_default_validate`)는 `feedparser.parse(url)`로 실 네트워크에
      의존한다. `create_app`이 `validate` 콜러블을 주입받아(기본은 `feeds.py`
      기본값) `add_feed`에 전달하도록 확장해, 등록 라우트 회귀가 네트워크 없이
      결정적으로 동작하게 한다. 다른 모듈의 주입 패턴과 일관(되돌리기 쉬움).
    - **오류 표현 방식(PRG + 오류 재렌더, 자체 결정)**: 성공한 등록/삭제는
      `303 See Other`로 목록 라우트로 리다이렉트(PRG)한다. 검증 오류
      (`FeedValidationError`)·중복(`DuplicateFeedError`)·미존재 삭제
      (`FeedNotFoundError`)는 세션·플래시 없이 목록 화면을 오류 메시지와 함께
      재렌더(비-리다이렉트, 트레이스백 미노출)한다. 세션 도입 없이 단순
      유지(되돌리기 쉬움).

- [x] **M11. 수집 실행 웹 UI** (PRD 3.2-2) — 완료 (T26 순수 상태·락 **PASS 12/12** → T27 배선·구동·폴링 **PASS 11/12** → T28 진행 UI·완료 리포트 **PASS 14/15**, `uv run pytest -x` 139 passed)
  - 버튼 클릭으로 `fetch`와 동일한 수집·요약·위키 갱신 실행.
  - 실행 중 피드별·글 단위 진행 상황 실시간 표시(미해결 의사결정 채택값: **폴링**, PRD 8).
  - 수집 진행 중 중복 실행 차단(인메모리 단일 실행 락, `web/progress.py`).
  - 완료 시 성공/실패 리포트 표시(파이프라인 리포트 재사용).
  - **재사용 원칙**: 수집 경로는 CLI와 동일한 `pipeline.run_fetch_async`를 쓴다.
    수집 이후 산출물 영속화(`wiki.write_wiki` 누적 인덱스 재생성 + `store.save_state`)와
    `claude` 미설치 프리플라이트도 CLI `fetch`(T13·T18)가 확립한 순서를 그대로
    따른다. `feeds.py`·`store.py`·`wiki.py`는 재사용만 하고 변경하지 않는다.
  - **분할 근거(순수 로직 우선, I/O·라우트 나중)**: M6(T12→T13)·M8(T19→T20)·
    M9(T21→T22)와 동일하게, (1) 파일 시스템·서버 무접근 인메모리 상태·락 계층(T26),
    (2) 그 상태를 소비하는 백그라운드 구동·트리거/폴링 라우트 배선(T27),
    (3) 진행 상황 실시간 표시·완료 리포트 화면 완성도(T28)로 나눈다.
  - **실시간 진행 입력원 결정(자체 결정, 되돌리기 쉬움)**: 현재
    `run_fetch_async`는 진행 상황을 종료 시점 `report`로만 집계하고 실행 중
    피드/글 단위 이벤트를 밖으로 내보내는 훅이 없다(`pipeline.py:111-205`). 실시간
    표시를 위해 `run_fetch_async`에 **선택적 `on_progress` 콜백 인자(기본 `None`)**를
    가법적으로 추가한다. 기본값이 `None`이면 CLI 경로(T18)는 무변경으로 회귀가
    보존되고, 웹 경로만 콜백을 주입해 피드/글 시작·성공·실패 이벤트를 상태 계층에
    반영한다. 콜백 인터페이스 정의와 상태 반영은 T26/T27 경계에서 다룬다(아래 참조).
  - [x] **T26. `web/progress.py` — 수집 진행 상태 + 단일 실행 락 (순수 인메모리 계층)** (완료, REVIEW PASS)
    - `web/progress.py`(파일 시스템·서버·프로세스 무접근): 한 번의 수집 실행
      진행 상태를 담는 인메모리 트래커. 상태 전이는 `idle → running → done|error`.
      메서드 골격 — `begin()`(락 획득, 이미 `running`이면 정의된 예외를 올려 중복
      실행 차단), 피드/글 단위 진행 갱신(`note_feed_started`/`note_article_done`/
      `note_article_failed` 등 이름은 구현 재량), `finish(report)`(리포트 저장 후
      `done`으로 전이·락 해제), `fail(message)`(`error`로 전이·락 해제),
      `snapshot()`(폴링 응답용 JSON 직렬화 가능한 현재 상태 dict 반환).
    - 스레드/태스크 안전성: 백그라운드 태스크(생산자)와 폴링 라우트(소비자)가
      동시에 접근하므로, 갱신·스냅샷을 `asyncio.Lock` 또는 동등한 방식으로
      경합 없이 처리한다(자체 결정: 되돌리기 쉬움). 실제 구동·라우트는 T27.
    - **`on_progress` 콜백 계약 정의(T27 소비)**: 트래커가 `run_fetch_async`에
      주입할 콜백이 받을 이벤트 형태(예: `{"kind": "feed_started"|"article_done"|
      "article_failed", ...}`)를 이 태스크에서 확정하고 단위 테스트로 고정한다.
      `run_fetch_async`에 콜백 인자를 실제로 배선하는 것은 T27.
    - acceptance: `uv run pytest tests/test_progress.py` 통과 — (1) 초기 상태가
      `idle`, (2) `begin()` 후 `running`, (3) `running` 중 재-`begin()`이 정의된
      예외로 차단(중복 실행 방지), (4) 진행 갱신이 `snapshot()`에 피드/글 카운터로
      반영, (5) `finish(report)` 후 `done`이며 스냅샷에 리포트 포함·이후 재-`begin()`
      가능(락 해제 확인), (6) `fail(msg)` 후 `error`이며 메시지 노출. `uv run pytest -x`
      회귀 없음.
    - touch: `src/rss_wiki/web/progress.py`(신규), `tests/test_progress.py`(신규).
      `pipeline.py`·`app.py`는 미변경(T27).
  - [x] **T27. 수집 트리거·백그라운드 구동·폴링 라우트 배선 + `on_progress` 훅** (M11 배선, **완료 PASS 11/12**)
    - **REVIEW T26 비차단 메모 흡수(T27 소비 지점 해소)**: (1) `snapshot()["report"]`가
      원본 참조를 그대로 노출(`progress.py:77`)하므로, 폴링 라우트가 스냅샷을 **변형 없이
      그대로** JSON으로 반환함을 회귀로 고정한다. (2) `asyncio.Lock` 동시성 정합은 단위로
      고정하기 어려워, 백그라운드 태스크(생산자)와 폴링 라우트(소비자) 종단 경로를 배선하는
      이번 태스크의 acceptance (a)~(c) 시나리오로 확인한다.
    - `pipeline.run_fetch_async`에 선택적 `on_progress` 콜백 인자를 가법적으로
      추가(기본 `None`, CLI 경로 무변경)하고, 피드/글 시작·성공·실패 지점에서
      T26이 정한 이벤트를 방출한다. 기존 async 회귀와 하위 호환 유지.
    - `app.py`에 라우트 배선: `POST /fetch`(수집 트리거) — 트래커 `begin()`으로
      락 획득(이미 `running`이면 사용자 대면 메시지로 차단), `run_fetch_async`를
      `asyncio.create_task` 등 백그라운드 태스크로 구동해 요청을 막지 않는다.
      완료 시 CLI `fetch`와 동일하게 `write_wiki`(state 누적 표시 메타로 index/
      feeds/daily 재생성) + `save_state` + 트래커 `finish(report)`. `claude` 미설치
      프리플라이트로 실행 불가를 트래커 `fail`로 표현. `GET /fetch/progress` —
      트래커 `snapshot()`을 JSON으로 반환(폴링 소비).
    - `create_app`에 진행 트래커 인스턴스를 앱 상태로 보유(단일 실행 락의
      인메모리 특성상 앱 인스턴스 수명과 일치). 테스트가 상태·경로를 주입할 수
      있도록 기존 `state_path`/`wiki_dir` 주입 패턴과 일관되게 설계.
    - acceptance: `uv run pytest tests/test_web_app.py` 통과 — (a) `POST /fetch`가
      주입한 가짜 `run_fetch_async`(네트워크·프로세스 미사용)로 백그라운드 실행을
      시작하고 즉시 응답, (b) 실행 중 `POST /fetch` 재요청이 사용자 대면 메시지로
      차단(중복 실행 방지)·트레이스백 미노출, (c) `GET /fetch/progress`가 진행/완료
      상태 JSON을 반환, (d) 완료 후 `state.json` 저장·`wiki/` 인덱스 재생성이
      호출됨을 단언, (e) `claude` 미설치(프리플라이트 실패) 주입 시 트래커가 `error`로
      전이. `uv run pytest -x` 회귀 없음. `uv run rss-wiki --help` 종료 코드 0.
    - touch: `src/rss_wiki/pipeline.py`(`on_progress` 가법 추가), `src/rss_wiki/web/app.py`
      (라우트·트래커 배선), `tests/test_web_app.py`·`tests/test_pipeline.py`(회귀).
      최소 트리거 버튼·상태 표시 마크업은 T28에서 완성한다.
  - [x] **T28. 수집 진행 상황 실시간 표시 UI + 완료 리포트 (화면 완성도)** (M11 마감, 완료 REVIEW PASS 14/15)
    - 수집 실행 화면(버튼 + 진행 상황 영역)을 M8 디자인 토큰·`.state-*` 골격으로
      구성한다. 경량 JS로 `GET /fetch/progress`를 폴링해 피드별·글 단위 진행을
      실시간 갱신하고, 완료 시 성공/실패 건수와 실패 사유(파이프라인 리포트)를
      표시한다. 진행 중에는 트리거 버튼을 비활성화해 중복 제출을 UI에서도 억제한다.
    - 상태 표현(PRD 3.3): 대기·진행 중·완료·오류 각 상태를 명확한 화면으로
      구분한다. 헤더 내비에 수집 실행 화면 링크를 추가한다.
    - **REVIEW T27 비차단 메모 흡수(T28에서 함께 처리)**:
      (1) **[운영 고려] 백그라운드 태스크 참조 유지** — `app.py`의
      `asyncio.create_task(_run_fetch_in_background())`가 반환 태스크를 어디에도
      보관하지 않아, asyncio가 실행 중 태스크를 GC할 수 있다(Python 공식 경고).
      태스크 참조를 앱 상태의 `set` 컨테이너에 담고 `add_done_callback`으로 제거해
      실행 중 GC 위험을 제거한다(되돌리기 쉬움). 진행 UI 배선과 같은 파일이므로
      함께 처리한다.
      (2) **[테스트 충실도] 완료 단계 실패 경로 회귀** — `run_fetch_async` 성공 이후
      `write_wiki`/`save_state`가 예외를 올리면 `except → tracker.fail`로 방어되나
      회귀가 없다. 완료 단계 실패 시 트래커가 `error`로 전이하고 메시지를 노출하는지
      회귀 1건으로 고정해 방어 코드의 통과-위장 여지를 줄인다.
    - acceptance: `uv run pytest tests/test_web_app.py` 통과 — 수집 실행 라우트가
      200이며 응답 본문에 (a) 트리거 폼/버튼, (b) 진행 상황 영역, (c) 폴링 JS
      로드(`<script>` 또는 정적 서빙 200)가 산출됨을 단언. 폴링 JS 정적 자원이
      `text/javascript`(또는 동등)로 서빙됨을 회귀로 고정. (d) **완료 단계 실패 회귀**:
      `write_wiki`/`save_state`가 예외를 올리도록 주입했을 때 트래커가 `error`로
      전이하고 `snapshot()`에 오류 메시지가 노출됨을 단언(REVIEW T27 메모 2 해소).
      `uv run pytest -x` 회귀 없음.
    - touch: `src/rss_wiki/web/templates/`(수집 실행 템플릿·`base.html` 내비 링크),
      `src/rss_wiki/web/static/`(폴링 JS·필요 CSS),
      `src/rss_wiki/web/app.py`(백그라운드 태스크 참조 유지 — REVIEW T27 메모 1),
      `tests/test_web_app.py`.
    - **승계(비차단, 수동 후속)**: 폴링 실시간 갱신의 브라우저 종단 육안 확인은
      블로킹 서버 특성상 M8~M10과 동일하게 수동 후속으로 남기고, 자동 acceptance는
      정적 검증 가능한 범위(마크업 산출·JS 서빙·라우트 응답)로 고정한다. 실환경
      `claude` CLI 종단 `fetch` 실호출 확인(REVIEW T27 메모 3)도 동일하게 수동 후속.

- [~] **M12. 디자인 품질 마감** (PRD 3.3) — 진행 (T29 인터랙션·폼 파싱 견고화 **완료(REVIEW PASS 14/15)** → T30 접근성·반응형 통합 점검 마감 **선정**)
  - 인터랙션 완성도: 버튼·링크 hover/focus/active, 진행률 표시, 부드러운 전환.
  - 반응형 점검(창 축소 시 레이아웃 무결), 키보드 포커스 표시, WCAG AA 대비.
  - M8~M11에서 남은 상태 표현·접근성 항목을 통합 점검해 마감.
  - **분할 근거(정적 검증 가능한 갭 우선, 통합 점검 나중)**: 인터랙션·접근성 상태는
    M8~M11에서 화면별로 이미 상당 부분 구현되어 있다(`styles.css`에 `:focus-visible`
    `112`, hover/active `168·183·187·285·340·344·360`, `prefers-reduced-motion` `248`,
    반응형 `254·421`, 전환 `337`). 따라서 M12는 신규 화면·모듈을 추가하지 않고,
    (1) 회귀로 고정 가능한 미해소 갭(REVIEW T24 메모 2건 + 인터랙티브 요소 포커스
    링 일관성)을 T29에서, (2) 정적 측정·통합 점검으로 마감하는 WCAG AA 대비·반응형·
    승계된 관찰 항목을 T30에서 다룬다.
  - [x] **T29. 인터랙션 마감 + 폼 파싱 견고화 (REVIEW T24 비차단 메모 해소)** (M12 1단계, 완료 — REVIEW T29 PASS 14/15, `uv run pytest -x` 141 passed)
    - **REVIEW T24 메모 1 해소**: `feeds_admin.html:22`의 `feed-list__info` 클래스가
      `styles.css`에 미정의다(현재 flex 자식으로 기본 배치되어 레이아웃 문제는 없음).
      이름/URL 블록 간격을 명시 제어하는 규칙을 기존 디자인 토큰(`--space-*`)만으로
      추가한다. 새 색상값·임의 크기를 도입하지 않는다.
    - **REVIEW T24 메모 2 해소**: `_form_value`(`app.py:50-57`)는 `parse_qs`로 폼
      본문을 파싱하는데, `application/x-www-form-urlencoded`에서 `+`는 공백으로
      디코딩되고 `%`는 퍼센트 인코딩 이스케이프로 해석된다. RSS URL에 `+`·`%`가
      포함될 때 등록 후 목록에 원형이 보존되는지를 직접 겨냥한 회귀가 없다. 특수문자
      포함 URL(`+`·`%` 포함)로 `POST /feeds-admin/add`를 호출해, 클라이언트가 올바르게
      퍼센트 인코딩한 본문이 서버에서 원형 URL로 복원되어 `feeds.json`에 저장·목록에
      노출됨을 회귀 1건으로 고정한다(폼 파싱 계약 견고화). 필요 시 `_form_value`의
      디코딩 처리를 조정하되 되돌리기 쉬운 범위로 한정한다(자체 결정).
    - **인터랙션 완성도 통합 점검(정적 범위)**: 헤더 내비 링크·버튼(`.button`류)·
      목록 링크(`.article-list__title`)·테마 토글·폼 입력이 `:focus-visible` 포커스
      링을 일관되게 갖는지 점검하고, 누락된 인터랙티브 요소가 있으면 기존 포커스
      토큰으로 보강한다. 새 인터랙션 패턴을 발명하지 않고 기존 규칙의 커버리지
      일관성만 맞춘다.
    - **REVIEW T28 비차단 메모 흡수(선택, 저비용 한정)**: (a) `fetch.js:82`의
      `renderError`가 부여한 `role="alert"`가 재-트리거로 `renderRunning` 진입 시
      제거되지 않는 점을 상태 전환에서 정리한다(화면·비차단). (b) `fetch.js:104-115`
      폴링 `fetch()` 체인에 `.catch()`가 없어 네트워크 거부 시 조용히 멈추는 점에
      최소 오류 처리(예: 안내 표시 또는 재시도)를 더한다(운영 고려·비차단). 두 항목은
      같은 파일 계열의 저비용 정리이므로 T29에서 함께 처리하되, 본질 acceptance는
      위의 CSS·폼 회귀다.
    - acceptance: `uv run pytest -x` 회귀 없음. `POST /feeds-admin/add`에 `+`·`%`
      포함 URL을 퍼센트 인코딩해 제출하면 목록에 원형 URL이 노출됨을 단언하는 회귀
      1건 추가·통과(`tests/test_web_app.py`). `styles.css`에 `feed-list__info` 규칙이
      정의됨을 정적 단언(문자열 포함)으로 고정. `uv run rss-wiki --help` 종료 코드 0.
    - touch: `src/rss_wiki/web/static/styles.css`(`feed-list__info` 규칙·포커스 링
      커버리지 보강), `src/rss_wiki/web/app.py`(`_form_value` 필요 시 조정),
      `src/rss_wiki/web/static/fetch.js`(선택 정리), `tests/test_web_app.py`(회귀).
      `feeds.py`·`store.py`·`wiki.py`·`pipeline.py`는 미변경(재사용 원칙).
  - [x] **T30. 접근성·반응형 통합 점검 마감 (WCAG AA 대비·키보드 포커스·승계 관찰)** (M12 2단계·M12 마감, 완료 REVIEW PASS 14/15)
    - **REVIEW T29 비차단 메모 흡수**: (1) `fetch.js` 변경 무커버(상태 전환 후
      `role` 부재·폴링 거부 시 재시도)는 아래 "렌더 분기 자동 검증 도입 판정"에
      함께 포함해 판단한다. (2) `feed-list__info` 속성 단언 심화(flex/gap/min-width)는
      CSS 문자열 단언의 취약성을 감안해 비용 대비 효용이 낮으므로 강제하지 않는다.
      (3) WCAG AA 대비·반응형 640px·브라우저 종단 육안·실환경 `claude` 종단은 아래
      해당 항목으로 마감·승계한다.
    - **WCAG AA 대비 정적 측정**: 라이트/다크 각 테마의 주요 텍스트/배경 조합
      (본문·부가 텍스트·버튼·링크·상태 배지·오류 메시지)의 대비비를 1회 정적 측정해
      AA(본문 4.5:1·큰 텍스트 3:1)를 만족함을 확인·기록한다(M8~M11에서 추가된 색
      조합 통합). 미달 조합이 있으면 디자인 토큰 값을 조정한다.
    - **반응형 무결 점검**: 640px 미디어쿼리(`styles.css:254·421`) 하에서 헤더 내비·
      목록·본문·피드 관리·수집 실행 화면이 겹침·넘침 없이 배치됨을 점검하고 필요 시
      보강한다.
    - **REVIEW T28 메모 (1) 승계 반영(테스트 충실도)**: `fetch.js` 렌더 분기
      (running/done/error/idle, 버튼 disabled, `report.failures` 목록화)의 자동
      검증 공백을 어떻게 좁힐지(경량 DOM 스냅샷 테스트 또는 헤드리스 스모크) 판정하고,
      도입 가능하면 회귀를 추가한다. 도입이 과하면 근거와 함께 수동 후속으로 명시 승계한다.
    - **승계(비차단, 수동 후속)**: M8~M11 각 화면의 브라우저 종단 육안 확인(다크 모드
      토글·반응형·폼 리다이렉트·폴링 실시간 갱신)은 블로킹 서버 특성상 수동 후속으로
      남긴다. 실환경 `claude` CLI 종단 `fetch` 실호출 회귀 기준선 확보도 동일하게
      수동 후속으로 승계한다.
    - acceptance: 대비비 측정 결과를 IMPL/REVIEW에서 확인 가능하게 기록. 반응형·포커스
      점검 결과 반영. `uv run pytest -x` 회귀 없음. `uv run rss-wiki --help` 종료 코드 0.
    - touch: `src/rss_wiki/web/static/styles.css`(대비·반응형 필요 시 조정),
      `tests/`(도입 시 렌더 회귀). 코어 모듈은 미변경.

## 미해결 의사결정

아래 항목은 PRD 본문에 초기 기본값이 명시되어 있으므로, 그 기본값으로 구현을
진행한다. 향후 확장 필요가 확인되면 결정 합의 절차로 재검토한다. 모두 되돌리기
쉬운 동작 수준의 결정이다.

| 항목 | 검토한 후보 | 초기 채택값 | 비고 |
|---|---|---|---|
| 요약 실패 글의 재시도 상한 | (a) 무제한 재시도 (b) N회 실패 후 영구 건너뜀 | (a) 무제한 재시도 | 반복 실패 글이 리포트를 오염시키면 상한 도입 검토 |
| 피드별 요약 프롬프트 커스터마이징 | (a) 전역 프롬프트 고정 (b) 피드별 오버라이드 | (a) 전역 고정 | 필요성 확인 시 설정 파일에 필드 추가 |
| 위키 출력 디렉터리 위치 | (a) 프로젝트 내 `wiki/` 고정 (b) 설정으로 변경 | (a) 프로젝트 내 고정 | `--output` 옵션 도입 여부는 M5 구현 시 결정 |
| 누적 전체 글 인덱스 입력원 (M6 결정) | (a) `state.json`에 표시 메타 적재 (b) `wiki/articles/` 스캔 후 마크다운 재파싱 | (a) state에 표시 메타 적재 | 자체 결정. PRD 4.4는 매 `fetch`마다 인덱스를 누적 재생성/갱신하도록 요구하므로 입력원이 필수다. (b)는 도구 자신의 산출물을 되파싱해 취약하다. (a)는 `state.json`이 도구 전용 내부 파일이고 `wiki/`는 파생물이라 되돌리기 쉽다(스키마 확장은 하위 호환 가법적). 파일명은 최초 배정 시 state에 저장해 재생성 간 안정성을 보장한다. 근거를 IMPL에 남긴다. |
| 병렬 요약 중 동기 extract 처리 (M7) | (a) `asyncio.to_thread`로 감싸 병렬 실행 (b) extract도 async로 재작성 | (a) `to_thread` 래핑 | 자체 결정. PRD 8은 요약의 asyncio 병렬만 명시하고 extract 방식은 미명시. (a)가 M6 extract 로직·테스트를 그대로 재사용해 최소 변경이며 되돌리기 쉽다. |
| 수집 진행 상황 전송 방식 (M11) | (a) 폴링 (b) SSE | (a) 폴링 | 자체 결정. PRD 8이 "SSE 또는 폴링" 허용. 로컬 단일 사용자·짧은 실행이라 가장 단순한 폴링을 채택. 필요 시 SSE로 교체(되돌리기 쉬움). |
| 웹 마크다운 렌더링 (M9) | (a) `markdown` 라이브러리 (b) 직접 파싱 | (a) `markdown` 의존성 | 자체 결정. `wiki/` 산출물을 HTML로 안전·표준 렌더링. 표준 라이브러리 채택이 가장 단순하며 교체 용이. |
