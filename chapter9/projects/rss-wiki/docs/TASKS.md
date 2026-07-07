# TASKS: rss-wiki

상태 표기: `[ ]` 미완료 / `[x]` 완료 / `[~]` 진행 중

## 이번 사이클 선정 (M12 마감: T30 — 접근성·반응형 통합 점검)

> REVIEW T29 **PASS(14/15, 화면 있는 항목)**, `uv run pytest -x` 141 passed(기존 139 +
> 신규 2, 회귀 없음)로 M12 1단계(인터랙션 마감 + 폼 파싱 견고화)가 완료되었다.
> REVIEW T24 이월 비차단 메모 2건(`feed-list__info` CSS 미정의, `_form_value`
> URL 인코딩 경계 회귀 부재)이 해소되고, `:focus-visible` 포커스 링 전역 커버리지
> 일관성과 `fetch.js` 저비용 정리(잔존 `role="alert"` 제거·폴링 `.catch()`)까지
> 반영되었다.
>
> 이번 사이클은 **M12의 마지막 항목 T30(접근성·반응형 통합 점검 마감)**을
> 선정한다. 이로써 M12(디자인 품질 마감, PRD 3.3)를 마감하고 잔여 마일스톤이
> 없어진다. WCAG AA 대비를 라이트/다크 각 테마 주요 조합에 대해 정적 측정·기록하고
> (미달 시 토큰 조정), 640px 반응형 무결을 통합 점검하며, `fetch.js` 렌더 분기
> 자동 검증 도입 여부를 판정한다(도입이 과하면 근거와 함께 수동 후속으로 명시
> 승계). 브라우저 종단 육안 확인·실환경 `claude` 종단 실호출은 블로킹 서버 특성상
> 수동 후속으로 승계한다. REVIEW T29 비차단 메모 3건은 모두 이 항목이 흡수한다.
>
> 참고(마감된 직전 사이클): REVIEW T28 **PASS(14/15, 화면 있는 항목)**, `uv run pytest -x` 139 passed(기존 135 +
> 신규 4, 회귀 없음)로 M11 3단계(수집 진행 상황 실시간 표시 UI + 완료 리포트)가
> 마감되며 **M11(수집 실행 웹 UI)이 완료**되었다. 이로써 PRD 3.1·3.2의 CLI·웹 UI
> 기능 축(피드 관리·수집 실행·글 열람)이 모두 구현되었고, 남은 축은 **M12(디자인
> 품질 마감, PRD 3.3)** 하나다.
>
> 인터랙션·접근성 상태는 M8~M11에서 화면별로 이미 상당 부분 구현되어 있으므로
> (`styles.css`에 `:focus-visible`·hover/active·`prefers-reduced-motion`·반응형
> 미디어쿼리·전환 규칙 존재), M12는 신규 화면·모듈을 추가하지 않고 미해소 갭을
> 통합 점검해 마감한다. 이번 사이클은 그중 **정적 회귀로 고정 가능한 T29(인터랙션
> 마감 + 폼 파싱 견고화)**를 선정한다. REVIEW T24가 M12로 이월한 비차단 메모 2건
> (`feed-list__info` CSS 미정의, `_form_value` URL 인코딩 경계 회귀 부재)을 해소하고,
> 인터랙티브 요소의 `:focus-visible` 포커스 링 커버리지 일관성을 맞춘다. REVIEW T28이
> 남긴 저비용 `fetch.js` 정리(잔존 `role="alert"` 제거·폴링 `.catch()` 부재)도 같은
> 정적 자원 계열이라 함께 처리한다. WCAG AA 대비 정적 측정·반응형 통합 점검·승계
> 관찰 항목은 다음 사이클 T30(M12 마감)으로 넘긴다.
>
> 참고(마감된 직전 사이클): REVIEW T27 **PASS(11/12, 화면 없는 항목)**, `uv run pytest -x` 135 passed(기존 128 +
> 신규 7, 회귀 없음)로 M11 2단계(수집 트리거·백그라운드 구동·폴링 라우트 배선 +
> `on_progress` 훅)가 마감되었다. JSON 라우트(`POST /fetch`·`GET /fetch/progress`)와
> 파이프라인 콜백 배선까지 종단으로 동작하며, 트리거 버튼·진행 표시 마크업은 T27이
> 명시적으로 T28 범위로 이월했다.
>
> REVIEW T27이 남긴 비차단 메모 3건 중 2건은 T28이 같은 파일(`app.py`)·같은 라우트를
> 다루므로 함께 해소한다 — (1) **[운영 고려] 백그라운드 태스크 참조 유지**:
> `asyncio.create_task(...)` 반환값을 보관하지 않아 실행 중 GC될 수 있으므로(Python
> 공식 경고) 앱 상태의 `set` 컨테이너에 담고 `add_done_callback`으로 제거한다.
> (2) **[테스트 충실도] 완료 단계 실패 경로 회귀**: `write_wiki`/`save_state` 예외 시
> 트래커가 `error`로 전이·메시지 노출하는지 회귀 1건으로 고정한다. 나머지 1건(실환경
> `claude` CLI 종단 실호출)은 블로킹 서버 특성상 수동 후속으로 승계한다. 두 메모를
> T28 acceptance·touch에 반영했다.
>
> 이번 사이클은 M11의 3단계 **T28(화면 완성도)**를 선정해 M11을 마감한다. M8 디자인
> 토큰·`.state-*` 골격 위에 수집 실행 화면(트리거 버튼 + 진행 상황 영역)을 구성하고,
> 경량 JS로 `GET /fetch/progress`를 폴링해 피드별·글 단위 진행을 실시간 갱신하며, 완료
> 시 성공/실패 리포트를 표시한다. 진행 중 트리거 버튼 비활성화로 중복 제출을 UI에서도
> 억제한다. 폴링 실시간 갱신의 브라우저 종단 육안 확인은 수동 후속으로 남기고, 자동
> acceptance는 정적 검증 가능한 범위(마크업 산출·JS 서빙·라우트 응답·완료 실패 회귀)로
> 고정한다.

- [x] **T30. 접근성·반응형 통합 점검 마감 (WCAG AA 대비·키보드 포커스·승계 관찰, M12 2단계·M12 마감)** — 완료 (`uv run pytest -x` 141 passed, 회귀 없음. 라이트/다크 전 조합 AA 대비 통과, 640px 반응형 무결 확인, `fetch.js` 자동 검증은 근거와 함께 수동 후속 승계. 코드 변경 없음 — **M12 마감, PLAN 전체 마일스톤 완료**)
  - 배경:
    - T29(M12 1단계) 완료로 인터랙션·폼 파싱 갭이 해소되었다. M12의 남은 축은
      정적 측정·통합 점검으로 마감하는 접근성(WCAG AA 대비)·반응형과, M8~M11에서
      승계된 관찰 항목이다. 이 항목을 마치면 잔여 마일스톤이 없어진다.
    - REVIEW T29가 남긴 비차단 메모 3건을 이 항목이 모두 흡수한다 — (1) `fetch.js`
      변경 무커버, (2) `feed-list__info` 속성 단언 심화(비용 대비 낮아 강제 안 함),
      (3) WCAG AA 대비·반응형 640px·브라우저 종단 육안·실환경 `claude` 종단 승계.
  - 내용:
    - **(1) WCAG AA 대비 정적 측정**: 라이트/다크 각 테마의 주요 텍스트/배경 조합
      (본문·부가 텍스트·버튼·링크·상태 배지·오류 메시지)의 대비비를 1회 정적
      측정해 AA(본문 4.5:1·큰 텍스트 3:1) 만족을 확인·기록한다(측정 결과를
      IMPL에 남겨 REVIEW에서 확인 가능하게 한다). 미달 조합이 있으면 디자인 토큰
      값을 조정한다(새 화면·새 인터랙션 패턴을 발명하지 않는다).
    - **(2) 반응형 무결 점검**: 640px 미디어쿼리(`styles.css:254·421`) 하에서
      헤더 내비·목록·본문·피드 관리·수집 실행 화면이 겹침·넘침 없이 배치됨을
      점검하고 필요 시 보강한다.
    - **(3) `fetch.js` 렌더 분기 자동 검증 도입 판정(REVIEW T28·T29 승계)**:
      running/done/error/idle 상태 전환, 버튼 disabled, `report.failures` 목록화,
      상태 전환 후 `role` 부재, 폴링 거부 시 재시도 — 이 렌더 분기의 자동 검증
      공백을 어떻게 좁힐지(경량 DOM 스냅샷 또는 헤드리스 스모크) 판정하고, 도입
      가능하면 회귀를 추가한다. 도입이 과하면 근거와 함께 수동 후속으로 명시 승계한다.
    - **(4) 수동 후속 승계(비차단)**: M8~M11 각 화면의 브라우저 종단 육안 확인
      (다크 모드 토글·반응형·폼 리다이렉트·폴링 실시간 갱신)과 실환경 `claude`
      CLI 종단 `fetch` 실호출 회귀 기준선 확보는 블로킹 서버·라이브 외부 서비스
      특성상 수동 후속으로 남긴다.
  - acceptance:
    - WCAG AA 대비비 측정 결과를 IMPL/REVIEW에서 확인 가능하게 기록(라이트/다크
      각 테마 주요 조합, AA 만족 여부 명시). 미달 조합 발견 시 토큰 조정 반영.
    - 640px 반응형·포커스 점검 결과 반영(겹침·넘침 없음 확인, 필요 시 CSS 보강).
    - `fetch.js` 렌더 분기 자동 검증 도입 판정을 명시(도입 시 회귀 추가·통과,
      수동 후속 시 근거 기록).
    - `uv run pytest -x` 회귀 없음. `uv run rss-wiki --help` 종료 코드 0.
  - touch: `src/rss_wiki/web/static/styles.css`(대비·반응형 필요 시 조정),
    `tests/`(렌더 회귀 도입 시). 코어 모듈(`feeds.py`·`store.py`·`wiki.py`·
    `pipeline.py`)은 미변경(재사용 원칙).

- [x] **T29. 인터랙션 마감 + 폼 파싱 견고화 (REVIEW T24 비차단 메모 해소, M12 1단계)** — 완료 (`uv run pytest -x` 141 passed, 회귀 없음)
  - 배경:
    - M11 완료로 PRD 3.1·3.2 기능 축이 모두 구현되었고, 남은 축은 M12(디자인 품질
      마감, PRD 3.3)다. 인터랙션·접근성 CSS는 M8~M11에서 화면별로 이미 상당 부분
      구현되어 있으므로(`styles.css`에 `:focus-visible` `112`, hover/active
      `168·183·187·285·340·344·360`, `prefers-reduced-motion` `248`, 반응형
      `254·421`, 전환 `337`), M12는 신규 화면을 추가하지 않고 미해소 갭만 마감한다.
    - REVIEW T24가 M12로 이월한 비차단 메모 2건이 아직 미해소다 — (1) `feed-list__info`
      클래스가 `styles.css`에 미정의(HTML `feeds_admin.html:22`에는 존재), (2)
      `_form_value`의 URL 인코딩 경계(`+`·`%` 포함 URL) 회귀 부재. 두 항목은 정적
      회귀로 고정 가능하므로 이번 사이클에서 우선 해소한다.
  - 내용:
    - **(1) `feed-list__info` CSS 규칙 정의(REVIEW T24 메모 1 해소)**: 이름/URL 블록
      간격을 명시 제어하는 규칙을 기존 디자인 토큰(`--space-*`)만으로 `styles.css`에
      추가한다. 새 색상값·임의 크기를 도입하지 않는다.
    - **(2) 폼 파싱 경계 회귀(REVIEW T24 메모 2 해소)**: `_form_value`(`app.py:50-57`)는
      `parse_qs`로 폼 본문을 파싱한다. `application/x-www-form-urlencoded`에서 `+`는
      공백으로, `%`는 퍼센트 이스케이프로 해석되므로, RSS URL에 `+`·`%`가 포함될 때
      등록 후 목록에 원형 URL이 보존되는지를 겨냥한 회귀가 필요하다. 클라이언트가
      올바르게 퍼센트 인코딩한 본문을 `POST /feeds-admin/add`로 제출하면 서버가 원형
      URL로 복원해 `feeds.json`에 저장·목록에 노출함을 회귀 1건으로 고정한다. 필요 시
      `_form_value` 디코딩 처리를 조정하되 되돌리기 쉬운 범위로 한정한다(자체 결정).
    - **(3) 포커스 링 커버리지 일관성(정적 통합 점검)**: 헤더 내비 링크·버튼(`.button`류)·
      목록 링크(`.article-list__title`)·테마 토글·폼 입력이 `:focus-visible` 포커스
      링을 일관되게 갖는지 점검하고, 누락 요소가 있으면 기존 포커스 토큰으로 보강한다.
      새 인터랙션 패턴을 발명하지 않는다.
    - **(4) REVIEW T28 비차단 저비용 정리(선택, 같은 정적 자원 계열)**: (a) `fetch.js:82`
      `renderError`가 부여한 `role="alert"`가 재-트리거 시 제거되지 않는 점을 상태
      전환에서 정리(화면·비차단), (b) `fetch.js:104-115` 폴링 `fetch()` 체인에
      `.catch()`가 없어 네트워크 거부 시 조용히 멈추는 점에 최소 오류 처리 추가(운영
      고려·비차단). 본질 acceptance는 (1)·(2)이며, (4)는 저비용일 때만 함께 처리한다.
  - acceptance:
    - `POST /feeds-admin/add`에 `+`·`%` 포함 URL을 퍼센트 인코딩해 제출하면 목록에
      원형 URL이 노출됨을 단언하는 회귀 1건을 `tests/test_web_app.py`에 추가·통과.
    - `styles.css`에 `feed-list__info` 규칙이 정의됨을 정적 단언(문자열 포함)으로 고정.
    - `uv run pytest -x` 회귀 없음. `uv run rss-wiki --help` 종료 코드 0.
  - touch: `src/rss_wiki/web/static/styles.css`(`feed-list__info` 규칙·포커스 링
    커버리지 보강), `src/rss_wiki/web/app.py`(`_form_value` 필요 시 조정),
    `src/rss_wiki/web/static/fetch.js`(선택 정리), `tests/test_web_app.py`(회귀).
    `feeds.py`·`store.py`·`wiki.py`·`pipeline.py`는 미변경(재사용 원칙).
  - **다음 사이클(T30, M12 마감)로 넘김**: WCAG AA 대비 정적 측정, 반응형 640px 통합
    점검, `fetch.js` 렌더 분기 자동 검증 도입 판정(REVIEW T28 메모 1 승계), 브라우저
    종단 육안 확인·실환경 `claude` 종단 실호출 수동 후속 승계.

- [x] **T28. 수집 진행 상황 실시간 표시 UI + 완료 리포트 (화면 완성도, M11 3단계)** — 완료 (`uv run pytest -x` 139 passed, 회귀 없음)
  - 배경:
    - REVIEW T27이 PASS(11/12)로 확인했듯 수집 트리거(`POST /fetch`)·폴링
      (`GET /fetch/progress`) JSON 라우트와 `on_progress` 파이프라인 배선은 종단으로
      동작한다. 그러나 화면(트리거 버튼·진행 상황 표시·완료 리포트 마크업)은 T27이
      명시적으로 T28 범위로 이월했다. PRD 3.2-2는 수집 실행을 **버튼 클릭**으로 시작하고
      실행 중 **피드별·글 단위 진행 상황을 실시간 표시**하며 완료 시 **성공/실패 리포트**를
      보여 주도록 요구한다. PRD 3.3은 대기·진행·완료·오류 상태를 각각 명확한 화면으로
      구분할 것을 요구한다.
  - 내용:
    - **수집 실행 화면 구성**: M8 디자인 토큰·`.state-*` 상태 골격을 재사용해 트리거
      버튼 + 진행 상황 영역을 구성한다. 헤더 내비에 수집 실행 화면 링크를 추가한다.
    - **폴링 실시간 갱신**: 경량 JS(`web/static/`)가 `POST /fetch`로 수집을 트리거하고
      `GET /fetch/progress`를 주기적으로 폴링해 피드별·글 단위 진행을 실시간 갱신한다.
      완료 시 성공/실패 건수·실패 사유(파이프라인 리포트)를 표시한다. 진행 중에는
      트리거 버튼을 비활성화해 중복 제출을 UI에서도 억제한다(서버 락과 이중 방어).
    - **상태 표현(PRD 3.3)**: 대기·진행 중·완료·오류 각 상태를 명확한 화면으로 구분한다.
    - **REVIEW T27 비차단 메모 흡수(같은 `app.py`·같은 라우트라 함께 처리)**:
      - **(메모 1) 백그라운드 태스크 참조 유지**: `app.py`의
        `asyncio.create_task(_run_fetch_in_background())`가 반환 태스크를 보관하지 않아
        실행 중 GC될 수 있다(Python 공식 경고). 태스크 참조를 앱 상태의 `set`
        컨테이너에 담고 `add_done_callback`으로 완료 시 제거해 GC 위험을 없앤다.
      - **(메모 2) 완료 단계 실패 경로 회귀**: `run_fetch_async` 성공 이후
        `write_wiki`/`save_state` 예외가 `except → tracker.fail`로 방어되나 회귀가
        없다. 완료 단계 실패 시 트래커가 `error`로 전이·메시지 노출함을 회귀로 고정한다.
  - acceptance:
    - `uv run pytest tests/test_web_app.py` 통과 — 수집 실행 라우트가 200이며 응답
      본문에 (a) 트리거 폼/버튼, (b) 진행 상황 영역, (c) 폴링 JS 로드(`<script>` 또는
      정적 서빙 200)가 산출됨을 단언.
    - 폴링 JS 정적 자원이 `text/javascript`(또는 동등)로 서빙됨을 회귀로 고정.
    - **(d) 완료 단계 실패 회귀(REVIEW T27 메모 2 해소)**: `write_wiki`/`save_state`가
      예외를 올리도록 주입한 뒤 수집을 트리거하면, 트래커가 `error`로 전이하고
      `GET /fetch/progress` 스냅샷에 오류 메시지가 노출됨을 단언.
    - `uv run pytest -x` 회귀 없음. `uv run rss-wiki --help` 종료 코드 0.
  - touch: `src/rss_wiki/web/templates/`(수집 실행 템플릿·`base.html` 내비 링크),
    `src/rss_wiki/web/static/`(폴링 JS·필요 CSS),
    `src/rss_wiki/web/app.py`(백그라운드 태스크 참조 유지 — REVIEW T27 메모 1),
    `tests/test_web_app.py`(마크업 산출·JS 서빙·완료 실패 회귀).
  - **승계(비차단, 수동 후속)**: 폴링 실시간 갱신의 브라우저 종단 육안 확인은 블로킹
    서버 특성상 M8~M10과 동일하게 수동 후속으로 남긴다. 실환경 `claude` CLI 종단
    `fetch` 실호출 확인(REVIEW T27 메모 3)도 동일하게 수동 후속으로 승계한다.

- [x] **T27. 수집 트리거·백그라운드 구동·폴링 라우트 배선 + `on_progress` 훅 (M11 2단계)** — 완료 (`uv run pytest -x` 135 passed, 회귀 없음)
  - 배경:
    - REVIEW T26이 확인했듯 `pipeline.run_fetch_async`(`pipeline.py:111-`)에는 아직
      `on_progress` 훅이 없고, `app.py`에는 수집 트리거·폴링 라우트가 없다. T26이
      확정한 이벤트 계약 `{"kind": "feed_started"|"article_done"|"article_failed",
      "feed": str}`을 실제 수집 경로에 연결해 실시간 진행 표시(폴링)와 단일 실행
      락(중복 차단)을 종단으로 동작시킨다.
  - 내용:
    - **`pipeline.run_fetch_async`에 `on_progress` 가법 추가**: 선택적 콜백 인자(기본
      `None`, CLI 경로 T18 무변경)를 추가하고, 피드 시작·글 성공·글 실패 지점에서 T26이
      정한 이벤트를 방출한다. 기존 async 회귀·하위 호환을 유지한다.
    - **`app.py` 라우트 배선**: `POST /fetch`(트리거) — 트래커 `begin()`으로 락 획득
      (이미 `running`이면 사용자 대면 메시지로 차단, 트레이스백 미노출),
      `run_fetch_async`를 `asyncio.create_task` 등 백그라운드 태스크로 구동해 요청을
      막지 않는다. 완료 시 CLI `fetch`(T13·T18)와 동일하게 `wiki.write_wiki`(state 누적
      표시 메타로 index/feeds/daily 재생성) + `store.save_state` + 트래커 `finish(report)`.
      `claude` 미설치 프리플라이트로 실행 불가를 트래커 `fail`로 표현.
      `GET /fetch/progress` — 트래커 `snapshot()`을 **변형 없이 그대로** JSON으로 반환
      (REVIEW T26 메모 (1) 해소: 라우트가 스냅샷 report를 재변형하지 않음을 회귀로 고정).
    - **트래커 인스턴스 보유**: `create_app`이 진행 트래커 인스턴스를 앱 상태로 보유
      (단일 실행 락의 인메모리 특성상 앱 인스턴스 수명과 일치). 기존 `state_path`/
      `wiki_dir`/`feeds_path`/`validate` 주입 패턴과 일관되게, 테스트가 가짜
      `run_fetch_async`·경로를 주입할 수 있도록 설계한다.
    - **재사용 원칙**: `feeds.py`·`store.py`·`wiki.py`는 재사용만 하고 변경하지 않는다.
  - acceptance:
    - `uv run pytest tests/test_web_app.py` 종료 코드 0으로 통과 —
      (a) `POST /fetch`가 주입한 가짜 `run_fetch_async`(네트워크·프로세스 미사용)로
      백그라운드 실행을 시작하고 즉시 응답, (b) 실행 중 `POST /fetch` 재요청이 사용자
      대면 메시지로 차단(중복 실행 방지)·트레이스백 미노출, (c) `GET /fetch/progress`가
      진행/완료 상태 JSON을 반환하며 트래커 `snapshot()`을 변형 없이 그대로 노출함을
      단언(REVIEW T26 메모 (1)), (d) 완료 후 `store.save_state` 저장·`wiki.write_wiki`
      인덱스 재생성이 호출됨을 단언, (e) `claude` 미설치(프리플라이트 실패) 주입 시
      트래커가 `error`로 전이. 백그라운드 태스크(생산자)→폴링 라우트(소비자) 종단
      경로가 `asyncio.Lock`으로 경합 없이 동작함을 (a)~(c) 시나리오로 확인(REVIEW T26
      메모 (2)).
    - `uv run pytest tests/test_pipeline.py` 통과 — `on_progress=None` 기본값에서 기존
      async 결과 동등성(하위 호환), 콜백 주입 시 피드/글 이벤트가 순서대로 방출됨을 단언.
    - `uv run pytest -x` 회귀 없음. `uv run rss-wiki --help` 종료 코드 0(CLI 경로 무변경).
  - touch: `src/rss_wiki/pipeline.py`(`on_progress` 가법 추가), `src/rss_wiki/web/app.py`
    (라우트·트래커 배선), `tests/test_web_app.py`·`tests/test_pipeline.py`(회귀).
    최소 트리거 버튼·진행 표시 마크업 완성은 T28 범위(이번엔 라우트·배선까지).

- [x] **T26. `web/progress.py` — 수집 진행 상태 + 단일 실행 락 (순수 인메모리 계층, M11 1단계)** — 완료 (`uv run pytest -x` 128 passed, 회귀 없음)
  - 배경:
    - PRD 3.2-2는 수집 실행 중 **피드별·글 단위 진행 상황을 실시간 표시**하고,
      **수집 진행 중 중복 실행을 차단**하며, 완료 시 **성공/실패 리포트**를 보여
      주도록 요구한다. 미해결 의사결정 표에서 진행 상황 전송 방식은 **폴링**을
      채택했다(로컬 단일 사용자·짧은 실행, 되돌리기 쉬움).
    - 현재 `pipeline.run_fetch_async`(`pipeline.py:111-205`)는 진행 상황을 종료
      시점 `report`로만 집계하고 실행 중 피드/글 단위 이벤트를 밖으로 내보내는
      훅이 없다. 실시간 표시·중복 차단을 위해서는 실행 상태를 인메모리로 보유하는
      계층이 먼저 필요하다.
  - 내용:
    - `web/progress.py`(파일 시스템·서버·프로세스 무접근 순수 인메모리): 한 번의
      수집 실행 진행 상태를 담는 트래커. 상태 전이는 `idle → running → done|error`.
      메서드 골격(이름은 구현 재량) — `begin()`(락 획득, 이미 `running`이면 정의된
      예외로 **중복 실행 차단**), 피드/글 진행 갱신(`note_feed_started`/
      `note_article_done`/`note_article_failed` 등), `finish(report)`(리포트 저장 후
      `done` 전이·락 해제), `fail(message)`(`error` 전이·락 해제), `snapshot()`
      (폴링 응답용 JSON 직렬화 가능한 현재 상태 dict 반환).
    - **동시 접근 안전성**: 백그라운드 태스크(생산자)와 폴링 라우트(소비자)가 동시에
      접근하므로 갱신·스냅샷을 `asyncio.Lock` 또는 동등한 방식으로 경합 없이
      처리한다(자체 결정: 되돌리기 쉬움).
    - **`on_progress` 콜백 이벤트 계약 확정(T27 소비)**: T27이 `run_fetch_async`에
      주입할 콜백이 받을 이벤트 형태(예: `{"kind": "feed_started"|"article_done"|
      "article_failed", ...}`)를 이 태스크에서 확정하고, 트래커가 그 이벤트를
      상태에 반영하는 경로를 단위 테스트로 고정한다. `run_fetch_async`에 콜백
      인자를 실제로 배선하는 것은 T27 범위다(`pipeline.py`·`app.py` 미변경).
  - acceptance:
    - `uv run pytest tests/test_progress.py` 종료 코드 0으로 통과 — (1) 초기 상태가
      `idle`, (2) `begin()` 후 `running`, (3) `running` 중 재-`begin()`이 정의된
      예외로 차단(중복 실행 방지), (4) 진행 갱신(또는 `on_progress` 이벤트 반영)이
      `snapshot()`에 피드/글 카운터로 반영, (5) `finish(report)` 후 `done`이며
      스냅샷에 리포트 포함·이후 재-`begin()` 가능(락 해제 확인), (6) `fail(msg)` 후
      `error`이며 메시지 노출.
    - `uv run pytest -x` 회귀 없음.
    - `uv run rss-wiki --help` 종료 코드 0(변경 범위 밖 회귀 없음).
  - touch: `src/rss_wiki/web/progress.py`(신규), `tests/test_progress.py`(신규).
    (`pipeline.py`·`app.py`는 T27에서 다루므로 이번엔 미변경)

## 이전 사이클 (M10 본체 착수: T24 — 피드 관리 웹 UI 라우트)

> REVIEW T25 **PASS(15/15)**로 M10 선행(T23 순방향 교정 + T25 저장 콘텐츠 렌더
> 시점 정규화)이 모두 마감되었다. REVIEW T25가 남긴 유일한 메모는 "비차단 — 다음
> 사이클 M10 본체 T24 착수(블로킹·조건부 없음)"이므로, 이번 사이클은 M10 본체
> T24(피드 관리 웹 UI 라우트)를 착수한다.
>
> **T24**는 PRD 3.2-1(웹에서 피드 등록·삭제·목록 조회)을 배선한다. `app.py`에
> `GET /feeds-admin`(목록)·`POST` 등록·`POST` 삭제 라우트를 추가하고, `feeds.py`의
> 유효성 검증·CRUD 로직과 `store` 파일 I/O를 재사용해 `feeds.json` 진실 소스를
> CLI와 단일하게 공유한다. `create_app`에 `feeds_path`·`validate` 주입 인자를
> 추가해(다른 모듈의 주입 패턴과 일관) 회귀가 네트워크 없이 결정적으로 동작하게
> 한다. 성공 등록/삭제는 PRG 리다이렉트, 검증 오류·중복·미존재 삭제는 목록 화면을
> 오류 메시지와 함께 재렌더(트레이스백 미노출)한다.

- [x] **T24. 피드 관리 웹 UI 라우트 — 목록 조회 + 등록/삭제 핸들러 (M10 본체)** — 완료 (`uv run pytest -x` 119 passed, 회귀 없음)
  - 배경:
    - PRD 3.2-1은 웹에서 피드 URL 등록(유효성 검증 포함)·삭제·목록 조회를
      요구한다. PRD 3.1은 피드 목록의 진실 소스가 도구가 관리하는 설정 파일이며
      CLI와 웹 UI가 동일한 설정 파일을 공유하도록 요구한다.
    - CLI `add`/`remove`/`list`는 이미 `feeds.py`의 유효성 검증·CRUD 로직을
      사용한다(`cli.py`). 웹은 이 로직을 재사용해 진실 소스를 단일하게 유지한다.
  - 내용:
    - `app.py`에 피드 관리 라우트를 배선한다. `GET /feeds-admin`(등록된 피드
      나열), `POST` 등록(URL 입력 → `feeds.add_feed` 유효성 검증 →
      `store.save_feeds`로 `feeds.json` 반영), `POST` 삭제(`feeds.remove_feed`,
      URL 또는 이름 지정). 성공한 등록/삭제는 `303` PRG로 목록 라우트로
      리다이렉트한다(자체 결정: 되돌리기 쉬움).
    - **feeds_path·validate 주입**: `create_app`에 `feeds_path`(기본
      `config.FEEDS_PATH`)와 `validate` 콜러블(기본은 `feeds.py` 기본값) 주입
      인자를 `state_path`/`wiki_dir`와 동일 패턴으로 추가한다. `feeds.add_feed`의
      기본 검증(`feedparser.parse`)이 실 네트워크에 의존하므로, 주입으로 등록
      라우트 회귀가 네트워크 없이 결정적으로 동작하게 한다(자체 결정: 되돌리기 쉬움).
    - **오류 표현(PRG + 오류 재렌더)**: `feeds.py`가 던지는 검증 오류
      (`FeedValidationError`)·중복(`DuplicateFeedError`)·미존재 삭제
      (`FeedNotFoundError`)를 사용자 대면 메시지로 변환해, 세션·플래시 없이 목록
      화면을 오류 메시지와 함께 재렌더한다(트레이스백 미노출). M8 `.state-*`·토큰 재사용.
    - Jinja2 템플릿(`base.html` 상속)과 필요한 CSS는 M8 디자인 토큰만 참조한다.
  - acceptance:
    - `uv run pytest tests/test_web_app.py` 통과 — (a) `GET /feeds-admin`가
      `feeds.json`(임시 경로 주입)의 등록 피드 목록을 렌더, (b) 유효 URL 등록
      `POST`가 `feeds.json`에 반영되고 목록으로 `303` 리다이렉트(validate 주입으로
      네트워크 미사용), (c) 중복/무효 URL 등록이 트레이스백 없이 사용자 메시지로
      재렌더, (d) 삭제 `POST`가 해당 피드를 `feeds.json`에서 제거하고 리다이렉트,
      (e) 미존재 삭제가 트레이스백 없이 사용자 메시지로 표현.
    - `uv run pytest -x` 회귀 없음.
    - `uv run rss-wiki --help` 종료 코드 0(기존 서브커맨드 회귀 없음).
  - touch: `src/rss_wiki/web/app.py`, `src/rss_wiki/web/templates/`(신규 템플릿),
    필요 시 `src/rss_wiki/web/static/styles.css`, `tests/test_web_app.py`.
    (`feeds.py`·`store.py`는 재사용만, 미변경 원칙)

## 이전 사이클 (REVIEW T23 블로킹 승계 해소 — 저장 콘텐츠 원문 링크 실화면)

> T23이 REVIEW **조건부 PASS(11/15)**로 완료되었다. T23은 `wiki.render_article`의
> 링크 줄을 마크다운 링크로 바꿔 **순방향 생성 경로**를 교정했으나, REVIEW T23이
> 실데이터로 확인한 대로 저장된 `wiki/articles/*.md`가 여전히 구식 평문
> `- 원문 링크: https://...`를 유지하는 **기존 콘텐츠**는 개별 글 라우트가 그
> 파일을 읽어 렌더할 때 원문 `<a href>`가 0건이다. 즉 T22 메모 1의 본래 목표(실
> 사용자 화면에서 원문 링크 클릭 가능)가 기존 콘텐츠에 미달성이며, REVIEW T23이
> 이를 **[블로킹 승계]**로 남겼다. 규칙상 REVIEW 메모 해소 항목을 먼저 선정한다.
>
> **T25**는 REVIEW T23이 권한 (b) 렌더 시점 정규화로 이 갭을 마감한다.
> `web/render.render_article_html`이 `markdown` 변환 전에 원문 링크 줄의 평문
> URL을 마크다운 링크로 정규화하도록 확장해, 저장 형식과 무관하게 실화면에서 원문
> 링크가 클릭 가능해진다. 함께 REVIEW T23 메모 2(실화면 경로 종단 회귀 부재)를
> 해소하는 라우트 종단 회귀를 추가한다. M10 본체(T24)는 T25 마감 후 착수한다.

- [x] **T25. REVIEW T23 블로킹 승계 해소 — 저장 형식 무관 원문 링크 실화면 클릭 + 실화면 종단 회귀** — 완료 (`uv run pytest -x` 112 passed, 회귀 없음)
  - 배경:
    - REVIEW T23 메모 1(블로킹 승계): `wiki.render_article`(`wiki.py:82`)의 링크
      형식 수정은 **순방향 생성 경로만** 교정한다. 개별 글 라우트
      `GET /articles/{filename}`(`app.py:80-97`)은 저장된 `wiki/articles/*.md`를
      읽어 `render.render_article_html`로 렌더하는데, 기존 파일은 전부 구식 평문
      `- 원문 링크: https://...`(예:
      `wiki/articles/2026-07-07-코드-청결도...md:3`)를 유지한다. `render_article_html`은
      `markdown.markdown(text)`을 확장 없이 호출하므로(`render.py:63`) 평문 URL이
      자동 링크되지 않아 실데이터 개별 글 화면 원문 `<a href>`가 0건이다.
    - REVIEW T23 메모 2(테스트 승계): 현재 회귀는 `render_article`→`render_article_html`
      격리 경로만 검증한다. 저장 `.md`를 라우트로 읽어 렌더한 실화면에서 원문
      `<a href>`가 산출되는지를 단언하는 종단 회귀가 없어, 격리 통과와 실화면 갭을
      테스트가 포착하지 못한다.
  - 내용:
    - **해소안 채택(REVIEW T23 제시 2택 중 b)**: `render.render_article_html`이
      `markdown` 변환 **전에** 원문 링크 줄의 평문 URL을 마크다운 링크 문법으로
      정규화하도록 확장한다. python-markdown 표준은 bare URL 자동링크를 지원하지
      않으므로(`extensions=['extra']`만으로 미해결) 서드파티 의존성 도입 대신
      **원문 링크 줄에 한정한 정규식 전처리**로 평문 URL을 `[url](url)`로 치환하는
      방식을 채택한다(가장 단순하며 되돌리기 쉬움, 자체 결정). 구식 평문
      (`- 원문 링크: {url}`)과 신규 마크다운 링크(`- 원문: [{url}]({url})`)를 모두
      올바르게 `<a href>`로 렌더하고, 링크 부재(`(링크 없음)`) 글은 `<a>`를 만들지
      않는다. (a) 저장 파일 마이그레이션은 본문 요약이 `state.json`에 없어 재생성이
      불가하고 범위가 넓어 채택하지 않는다.
    - **실화면 종단 회귀(메모 2 해소)**: 임시 `wiki/articles/`에 구식 평문 링크
      `.md` 픽스처를 두고 `TestClient`로 `GET /articles/{filename}`을 호출해 응답
      본문에 원문 `<a href="https://...">`가 1건 이상 산출됨을 단언한다(통과-위장
      방지: 정규화 제거 시 실패). 신규 마크다운 링크 형식 `.md`도 동일하게 `<a href>`
      산출을 유지함을 회귀로 고정한다.
  - acceptance:
    - `uv run pytest tests/test_render.py tests/test_web_app.py -q` 통과 —
      (1) `render_article_html`이 구식 평문 `- 원문 링크: {url}` 입력에서
      `<a href="{url}">`를 산출, (2) 신규 마크다운 링크 입력에서도 `<a href>` 산출,
      (3) 링크 부재 입력에서 예외 없이 렌더하며 잘못된 `<a>` 미생성,
      (4) 구식 평문 링크 `.md`를 담은 임시 저장소로 `GET /articles/{filename}` 200이며
      본문에 원문 `<a href="http...">` 1건 이상(실화면 종단 회귀).
    - `uv run pytest -x` 회귀 없음.
    - `uv run rss-wiki --help` 종료 코드 0(변경 범위 밖 회귀 없음).
  - touch: `src/rss_wiki/web/render.py`(원문 링크 줄 정규화), `tests/test_render.py`
    (단위 회귀), `tests/test_web_app.py`(실화면 종단 회귀). `app.py`·`wiki.py`·
    템플릿은 미변경 원칙(라우트는 이미 `render_article_html`을 소비).

## 이전 사이클 (REVIEW T22 메모 해소: T23 완료 / M10 T24 대기)

> T22가 REVIEW PASS(15/15, `uv run pytest -x` 105 passed)로 완료되어 M9(글 열람)가
> 마감되었다. REVIEW T22는 두 건의 후속 메모를 남겼고, 그중 (1) 원문 링크가
> 실사용자 화면에서 클릭 불가한 문제를 "우선 검토 권장"으로 표시했다. 규칙상
> REVIEW 메모 해소 항목을 먼저 선정한다.
>
> **T23**은 그 메모를 해소한다. 실개별 글 화면에서 `wiki.py:84`의
> `- 원문 링크: {link}` 평문이 `markdown` 라이브러리를 통과해도 `<a href>`로
> 변환되지 않아 원문 링크가 클릭 불가하다(REVIEW가 실데이터로 0건 확인). 링크를
> 마크다운 링크 문법으로 바꿔 실화면에서 클릭 가능하게 만든다. 함께 남은 미관
> 메모(발행일 부재 시 목록 메타에 구분점만 남음)도 조건부 처리한다.
>
> **T24**는 M10(피드 관리 웹 UI)의 본체를 착수한다. `feeds.py`의 유효성 검증·
> CRUD 로직을 재사용해 웹에서 피드 목록 조회·등록·삭제를 제공한다. CLI와 동일한
> `feeds.json`을 공유해 진실 소스를 단일하게 유지한다. 상세는 PLAN.md M10 참조.

- [x] **T23. REVIEW T22 메모 해소 — 원문 링크 실화면 클릭 가능 + 발행일 부재 목록 구분점 정리** — 완료 (`uv run pytest -x` 108 passed, 회귀 없음)
  - 배경:
    - REVIEW T22 메모 1(우선 검토 권장): `wiki.render_article`(`wiki.py:82-88`)이
      원문 링크를 `- 원문 링크: {link}` 평문으로 적는다. `web/render.render_article_html`이
      `markdown` 라이브러리로 변환해도 평문 URL은 자동 링크가 되지 않아, 개별 글
      화면에 원문 `<a href="http...">`가 0건이다. PRD 3.2-3은 개별 글 페이지에
      "원문 링크"를 표시하도록 요구하므로 실사용자 관점에서 링크가 동작해야 한다.
    - REVIEW T22 메모 2(미관·비차단): `_article_list.html`의
      `{{ article.feed_name }} · {{ article.published }}`는 `published`가 없으면
      Jinja Undefined가 빈 문자열로 렌더되어 "피드 A · "처럼 구분점만 남는다.
  - 내용:
    - `wiki.render_article`의 원문 링크 줄을 마크다운 링크 문법으로 바꾼다
      (예: `- 원문: [{link}]({link})`). `link`가 빈 문자열인 기존 분기(원문
      링크 부재)는 자동 링크 대상이 없으므로 회귀로 함께 고정한다.
    - `_article_list.html`에서 `published`가 있을 때만 ` · {published}` 구분점을
      렌더하도록 조건부 처리한다(개별 글 페이지의 메타 표시는 이미 정상이면 미변경).
    - 실렌더 회귀: `render_article` 산출 마크다운을 `render_article_html`에 통과시켜
      원문 `<a href="{link}">`가 1건 이상 산출됨을 단언(통과-위장 방지: 평문
      복원 시 실패). 발행일 부재 목록 항목에서 후행 구분점이 없음을 단언.
  - acceptance:
    - `uv run pytest tests/test_wiki.py` 통과 — 원문 링크가 있는 글에서
      `render_article` 산출물을 `render_article_html`로 변환 시 `<a href="{link}">`
      1건 이상, 원문 링크 부재 글에서는 예외 없이 렌더.
    - `uv run pytest tests/test_web_app.py` 통과 — 발행일 부재 목록 항목이
      후행 ` · ` 구분점 없이 렌더(또는 렌더링 함수 단위 회귀).
    - `uv run pytest -x` 회귀 없음(기존 105 passed 유지 + 신규).
  - touch: `src/rss_wiki/wiki.py`, `src/rss_wiki/web/templates/_article_list.html`,
    `tests/test_wiki.py`, `tests/test_web_app.py`. (`web/render.py`·`app.py` 미변경)

> T24(M10 본체)의 상세 정의는 이 문서 상단 "이번 사이클 선정" 섹션으로
> 승격되어 이번 사이클에 착수한다.

## 이전 사이클 (M9 마무리: T22 — 글 열람 라우트·템플릿 배선 + 읽기 경험 CSS)

> T21(`web/render.py` 순수 렌더링 로직)이 REVIEW PASS(12/12, `uv run pytest -x`
> 96 passed)로 완료되어, M9의 순수 계층(목록 뷰모델 구성 + 마크다운→HTML
> 변환)이 확정되었다. 다음은 M9를 마무리하는 라우트·템플릿·CSS 배선(T22)이다.
>
> T22는 M8·M5 패턴의 "I/O·라우트 나중" 절반을 담당한다. `app.py`에서
> `state.json`을 로드하고 `wiki/articles/<filename>.md`를 읽어 T21의 순수
> 함수(`build_list_viewmodel`·`render_article_html`)에 주입한 뒤 Jinja2
> 템플릿으로 렌더한다. 전체 최신순 목록·피드별 목록·날짜별 목록·개별 글
> 페이지(요약문·핵심 포인트·원문 링크·발행일·피드명)를 화면으로 제공한다.
> 개별 글은 `wiki/` 마크다운을 렌더해 위키 파일과 화면이 항상 일치한다
> (PRD 3.2-3). 상세는 PLAN.md M9/T22 참조.
>
> REVIEW T21 메모 반영 — (1) 화면이 T21 순수 함수를 실데이터로 소비하는
> 시점이므로, 발행일(`published`) 부재 글이 목록/그룹에서 어떻게 나열되는지
> 회귀 1건으로 고정한다. REVIEW T20 승계 — (2) 화면이 M8 토큰·테마를 실제로
> 소비하므로 다크 셀렉터 존재·`theme.js` 200 서빙을 회귀로 고정하고,
> (3) 라이트/다크 실제 텍스트·배경 조합의 WCAG AA 대비를 1회 정적 측정한다.

- [x] **T22. 글 열람 라우트·템플릿 배선 + 읽기 경험 CSS (M9 마무리: 목록·개별 글 라우트 + Jinja2 템플릿 + `.prose` 읽기 경험 + 상태 화면 + REVIEW 승계 회귀)** — 완료 (`uv run pytest -x` 105 passed, 회귀 없음)
  - 배경:
    - PRD 3.2-3은 웹에서 수집된 글 요약을 읽을 수 있어야 하며, 전체 최신순
      목록·피드별 목록·날짜별 목록과 개별 글 페이지(요약문·핵심 포인트·원문
      링크·발행일·피드명)를 제공하도록 요구한다. 개별 글은 마크다운 산출물
      (`wiki/`)을 렌더링해 보여 주므로 위키 파일과 웹 화면 내용이 항상 일치해야
      한다. PRD 3.3은 읽기 경험 최우선(본문 폭 65~75자·충분한 행간·위계 있는
      제목)과 상태 표현(빈 목록·오류 각각 명확한 화면)을 요구한다.
    - T21이 순수 계층을 확정했다. `web/render.py`에 `build_list_viewmodel`
      (표시 메타 리스트 → `latest`·`by_feed`·`by_date` 뷰모델)과
      `render_article_html`(마크다운 문자열 → HTML)이 있고, 피드 그룹 슬러그는
      `wiki.slugify`로 산출되어 인덱스·피드 페이지 링크와 정합한다.
    - 데이터 소스는 M6에서 확정했다. 목록 메타는 `state.json`의
      `processed[id].meta`(filename·title·published·collected_date·feed_name)에
      누적되어 있고, 개별 글 본문은 `wiki/articles/<filename>.md`에 있다.
      `store.load_state`·`config.STATE_PATH`·`config.WIKI_DIR`를 재사용한다.
    - 현재 `app.py`는 `GET /`가 `base.html`을 스텁 렌더할 뿐이며(`app.py:18-22`),
      목록·개별 글 라우트와 화면 템플릿은 전무하다. M8 T20이 `.prose`·`.state-*`
      골격을 CSS 토큰으로 마련해 두었으므로 이를 소비한다.
  - 내용:
    - `app.py`에 목록·개별 글 라우트를 배선한다. 각 라우트는 (1) `state.json`을
      로드해 `processed[*].meta` 표시 메타 리스트를 구성하고, (2) T21 순수 함수
      (`build_list_viewmodel`)로 뷰모델을 얻어 Jinja2 템플릿에 전달한다.
      - `GET /`: 전체 최신순 목록(`viewmodel["latest"]`).
      - 피드별 목록: `viewmodel["by_feed"]` 전체 나열 또는 피드 슬러그별 상세
        경로(예: `GET /feeds/{slug}`). 슬러그는 `wiki.slugify`와 정합
        (자체 결정: 되돌리기 쉬움).
      - 날짜별 목록: `viewmodel["by_date"]`(예: `GET /daily/{date}` 또는 전체
        나열). 수집일(`collected_date`) 기준(PRD 4.4·render 계약과 일치).
      - 개별 글 페이지(예: `GET /articles/{filename}`): `wiki/articles/
        <filename>.md`를 읽어 `render_article_html`로 HTML 변환 후 렌더한다.
        요약문·핵심 포인트는 마크다운 본문에서, 원문 링크·발행일·피드명은
        표시 메타에서 채운다(PRD 3.2-3). 위키 파일과 화면 내용이 일치한다.
    - Jinja2 템플릿을 `web/templates/`에 추가한다(`base.html` 상속). 목록
      템플릿(최신순·피드별·날짜별)과 개별 글 템플릿을 두되, M8 토큰·`.prose`
      (가독 폭 65~75자·행간)·제목 위계를 재사용해 임의 값을 새로 도입하지
      않는다(PRD 3.3 일관 디자인).
    - **상태 표현**(PRD 3.3): 빈 목록(글 0건)과 오류(파일 부재 등) 화면을 M8
      `.state-*` 골격으로 채운다. T21이 빈 입력 시 빈 뷰모델을 반환하므로 빈
      목록 분기는 템플릿에서 처리한다. 개별 글 파일 부재는 사용자 대면 오류
      화면(예: 404)으로 처리하고 트레이스백을 노출하지 않는다.
    - **발행일 부재 처리(REVIEW T21 메모 (1))**: `state.json`에 `published`가
      없거나 빈 글이 섞일 수 있다. T21 순수 함수의 관대 처리(`published=None`
      정렬·빈 `feed_name`/`collected_date` 그룹핑)가 실데이터에서 어떻게
      나열되는지 이 시점에 회귀로 고정한다(아래 acceptance 참조).
    - **REVIEW T20 승계 회귀 고정**: 화면이 M8 토큰·테마를 실제로 소비하므로
      (2) 다크 셀렉터(`[data-theme="dark"]`) 존재와 `theme.js` 200 서빙을
      회귀로 고정하고, (3) 라이트/다크 실제 텍스트·배경 조합의 WCAG AA 대비를
      1회 정적 측정해 IMPL에 기록한다(측정은 정적 확인, 회귀 고정 대상 아님).
  - acceptance (실행할 명령과 기대 결과):
    - `uv run pytest tests/test_web_app.py` 종료 코드 0으로 통과. `TestClient`와
      주입/격리한 `state.json`·`wiki/articles/`(임시 경로)로 다음을 단언한다 —
      (1) `GET /`가 200·`text/html`이고 본문에 최신순으로 배치된 글 제목이
      published 내림차순 순서로 나타남(통과-위장 방지: 순서 뒤집으면 실패),
      (2) 피드별/날짜별 목록 라우트가 200이고 해당 피드/수집일 글만 나열함,
      (3) 개별 글 라우트가 `wiki/articles/<filename>.md` 렌더 HTML(제목 `<h1>`·
      불릿 `<li>`·원문 링크 `<a href>`)과 표시 메타(발행일·피드명)를 포함함,
      (4) 존재하지 않는 글 파일 요청 시 사용자 대면 오류 화면(예: 404)이고
      트레이스백을 노출하지 않음, (5) 빈 `state.json`(글 0건)에서 목록 라우트가
      빈 목록 상태 화면(`.state-*`)을 렌더함, (6) **발행일 부재 글**(`meta`에
      `published` 없음)이 섞여도 목록 라우트가 예외 없이 200을 반환하고 해당
      글이 목록에 나열됨(REVIEW T21 메모 (1) 해소, 통과-위장 방지: 예외 시 실패).
    - `GET /static/theme.js`가 200·`content-type`에 javascript를 포함하고,
      렌더된 목록/개별 글 화면 본문에 다크 셀렉터를 소비하는 마크업(테마 토글·
      `data-theme` 훅)이 포함됨을 단언한다(REVIEW T20 메모 (2) 승계).
    - `uv run pytest -x` 전체 통과(회귀 없음, 현재 96 passed 기준 증가).
    - `uv run rss-wiki --help` 종료 코드 0, 서브커맨드 5개(add/remove/list/
      fetch/serve) 정상 표시(회귀 없음).
  - touch:
    - `src/rss_wiki/web/app.py`(목록·개별 글 라우트 배선, `state.json` 로드·
      `wiki/` 마크다운 읽기 → T21 순수 함수 호출 → 템플릿 렌더),
    - `src/rss_wiki/web/templates/`(목록·개별 글 템플릿 신규, `base.html` 상속),
    - `src/rss_wiki/web/static/styles.css`(`.prose`·목록 위계 읽기 경험 CSS
      보강, M8 토큰만 참조),
    - `tests/test_web_app.py`(목록·개별 글·빈 상태·오류·발행일 부재·`theme.js`
      서빙 회귀 추가).
    - `web/render.py`는 import 참조만(T21 순수 함수 재사용, 수정 없음).
      `store.py`·`config.py`는 로드·경로 참조만.
  - 참고(비차단): 브라우저 종단 확인(다크 토글 실동작·반응형 레이아웃 무결·
    포커스 표시)은 블로킹 서버 특성상 자동 acceptance로 고정하기 어렵다. 정적
    검증 가능한 범위(라우트 응답·본문 단언·`theme.js` 서빙·다크 셀렉터 존재)만
    회귀로 고정하고, 실기동 확인과 WCAG AA 대비 실측 기록은 수동/정적 후속으로
    남긴다(REVIEW T19·T20 승계 패턴과 동일).

- [x] **T21. `web/render.py` 순수 렌더링 로직 (M9 착수: 목록 뷰모델 구성 + 마크다운→HTML 변환, 주입형 순수 함수)** — 완료 (`uv run pytest -x` 96 passed, 회귀 없음)
  - 배경:
    - PRD 3.2-3은 웹에서 수집된 글 요약을 읽을 수 있어야 하며, 전체 최신순
      목록·피드별 목록·날짜별 목록과 개별 글 페이지(요약문·핵심 포인트·원문
      링크·발행일·피드명)를 제공하도록 요구한다. 개별 글은 마크다운 산출물
      (`wiki/`)을 렌더링해 보여 주므로 위키 파일과 웹 화면 내용이 항상 일치해야
      한다.
    - 데이터 소스는 M6에서 확정했다. 목록 메타는 `state.json`의
      `processed[id].meta`(filename·title·published·collected_date·feed_name)에
      누적되어 있고, 개별 글 본문은 `wiki/articles/<filename>.md`에 있다.
    - M5·M8 패턴대로 순수 로직을 먼저 확정한다. T21은 파일 시스템·서버 없이
      동작하는 순수 함수까지만 담당하고, 라우트·템플릿·CSS는 T22가 맡는다.
  - 내용:
    - `pyproject.toml` `dependencies`에 `markdown`을 추가한다(`uv add markdown`).
      PRD 미명시이나 PLAN 미해결 의사결정 표에서 (a) `markdown`으로 채택한
      되돌리기 쉬운 결정(표준·안전 변환, 교체 용이).
    - `src/rss_wiki/web/render.py`를 신설한다(순수 로직, 파일 시스템·네트워크
      무접근):
      - 목록 뷰모델 구성 함수: 표시 메타 dict 리스트를 입력받아 (1) 전체
        최신순(published 내림차순) 목록, (2) 피드별 그룹, (3) 날짜별
        (collected_date) 그룹의 뷰모델을 만든다. 피드 링크 슬러그는
        `wiki.slugify`를 재사용해 인덱스·피드 페이지 링크와 정합을 유지한다.
      - 마크다운→HTML 변환 함수: 개별 글 마크다운 문자열을 `markdown`으로
        HTML로 변환한다.
      - 입력(메타 리스트·마크다운 텍스트)을 인자로 주입받아, 단위 테스트가
        실제 파일·`state.json`·서버 없이 동작하도록 설계한다(다른 모듈의
        주입형 순수 로직과 일관).
  - acceptance (실행할 명령과 기대 결과):
    - `uv run pytest tests/test_render.py` 통과. 회귀는 다음을 단언한다 —
      (1) 최신순 목록이 `published` 내림차순으로 정렬됨, (2) 피드별 그룹이
      `feed_name`으로 묶이고 그룹 키 슬러그가 `wiki.slugify(feed_name)`와
      일치함(인덱스 링크 정합), (3) 날짜별 그룹이 `collected_date`로 묶임,
      (4) 마크다운→HTML 변환이 제목(`<h1>`)·불릿(`<ul>`/`<li>`)·링크
      (`<a href>`)를 산출함, (5) 빈 메타 리스트 입력 시 빈 뷰모델을 반환함
      (T22 빈 목록 상태 화면 대비).
    - `uv run pytest -x` 회귀 없음(기존 91 passed 유지 + 신규).
  - touch:
    - `pyproject.toml`(`markdown` 의존성 추가),
    - `src/rss_wiki/web/render.py`(신규 순수 렌더링 로직),
    - `tests/test_render.py`(신규 단위 테스트).
    - `app.py`·템플릿·CSS는 미변경(T22 범위).

- [x] **T20. 디자인 시스템 기반 (M8 마무리: 디자인 토큰 + 라이트/다크 테마 + 공통 레이아웃 + 반응형 골격 + 테스트 충실도 보강)** — 완료 (`uv run pytest -x` 91 passed, 회귀 없음)
  - 배경:
    - PRD 3.3은 웹 UI에 완성도 있는 제품 수준의 디자인을 요구한다. 색상
      팔레트·타이포그래피·간격 스케일을 토큰으로 정의해 전 화면에 일관 적용
      (임의 색상값·크기 금지), 읽기 경험 최우선(본문 폭 65~75자·충분한 행간·
      위계 있는 제목), 라이트/다크 테마(시스템 설정 추종 + 수동 전환),
      반응형(창 축소 시 무너지지 않음), 상태 표현·인터랙션 완성도를 명시한다.
    - T19는 서버 뼈대만 세웠고 `base.html`은 스타일이 전무하다(`base.html`은
      `<title>`·`content` 블록과 `lang="ko"`·viewport만 존재, `/static`은
      `.gitkeep`만). REVIEW T19 화면 완성도 1점은 이 태스크가 끌어올릴 대상이다.
    - 이 토큰·레이아웃은 이후 M9~M12의 모든 화면이 상속하는 기반이므로 M8에서
      확정한다. 개별 화면(글 열람·피드 관리·수집 실행)의 구현은 각 마일스톤이
      담당하고, T20은 공통 기반과 빈/오류 상태 골격까지만 둔다.
  - 내용:
    - `web/static/`에 디자인 토큰 CSS(예: `styles.css` 또는 `tokens.css`)를
      신설한다. 색상 팔레트·타이포그래피(글꼴 스택·크기 스케일·행간)·간격
      스케일을 CSS 커스텀 프로퍼티(`:root`)로 한 곳에 정의한다. 화면마다
      다른 임의 값을 쓰지 않고 이 토큰만 참조하도록 한다.
    - 라이트/다크 테마: 시스템 설정을 기본 추종(`prefers-color-scheme`)하되,
      수동 전환 토글을 제공한다. 토글 상태는 경량 JS로 저장(`localStorage`)해
      새로고침 후에도 유지한다. 다크 모드용 토큰 값을 테마 셀렉터(예:
      `[data-theme="dark"]`)로 오버라이드한다.
    - `base.html`을 확장한다. `<head>`에서 `/static`의 토큰 CSS를 링크하고,
      헤더(사이트 제목·테마 토글)·본문 컨테이너(가독 폭 제한)·반응형 기본
      골격을 배치한다. 이후 화면이 상속할 `content` 블록 구조는 유지한다.
    - 빈 목록·오류·로딩 상태의 기본 화면 골격(재사용 가능한 CSS 클래스 또는
      부분 템플릿)을 두어 M9~M12가 채우도록 한다(PRD 3.3 상태 표현 기반).
    - 키보드 포커스 표시(`:focus-visible`)와 WCAG AA 대비를 토큰 단계에서
      확보한다(색 대비는 정적 검증 범위에서 확인).
  - REVIEW T19 메모 반영(테스트 충실도, 비차단이었으나 이번에 해소):
    - `tests/test_web_app.py`에 `GET /` 렌더 본문 단언(예:
      `assert "rss-wiki" in response.text`)을 추가해 빈 응답 통과-위장을 막는다.
    - `/static`의 토큰 CSS를 실제로 서빙하는지 회귀를 추가한다(`TestClient`로
      `GET /static/<css 파일>` → 200·`content-type: text/css`). T20이 CSS
      링크를 추가하므로 마운트 실서빙 회귀를 함께 고정한다.
  - touch: `src/rss_wiki/web/static/`(토큰 CSS 신규, `.gitkeep`은 대체/유지),
    `src/rss_wiki/web/templates/base.html`(CSS 링크·헤더·컨테이너·테마 토글),
    필요 시 `src/rss_wiki/web/static/`에 경량 테마 토글 JS,
    `tests/test_web_app.py`(본문 단언 + `/static` CSS 서빙 회귀).
    앱 팩토리(`app.py`)는 정적 마운트가 이미 있으므로 원칙적으로 미변경
    (변경이 필요하면 최소 범위로 한정).
  - acceptance:
    - `uv run pytest tests/test_web_app.py` 종료 코드 0으로 통과. `GET /`가
      200·`text/html`이면서 본문에 `rss-wiki`(또는 헤더 제목 텍스트)가
      포함됨을 단언하고, `GET /static/<토큰 css>`가 200·`content-type:
      text/css`를 반환함을 단언한다.
    - `uv run pytest -x` 전체 통과(회귀 없음, 현재 90건 기준 증가).
    - 디자인 토큰(색상·타이포·간격)이 단일 CSS 파일 한 곳에서 정의되고
      `base.html`이 이를 링크한다(정적 확인). 다크 모드 토큰이 테마 셀렉터로
      오버라이드되고 토글 요소가 `base.html`에 존재한다(정적 확인).
  - 참고(비차단): 다크 모드 토글 실동작·반응형 레이아웃 무결·포커스 표시의
    브라우저 종단 확인은 블로킹 서버 특성상 자동 acceptance로 고정하기
    어렵다. 정적 검증 가능한 범위(CSS 서빙·본문 단언·토큰 정의 위치·토글
    요소 존재)만 회귀로 고정하고, 실기동 확인은 수동 후속으로 남긴다
    (REVIEW T19 승계 패턴과 동일).

- [x] **T19. 웹 서버 스캐폴딩 & `serve` 명령 (M8 착수: FastAPI 앱 팩토리 + serve 서브커맨드 + 루트 라우트 + 회귀)** — 완료 (`uv run pytest -x` 90 passed, 회귀 없음)
  - 배경:
    - PRD 3.1은 `rss-wiki serve`로 로컬 웹 UI 서버를 실행하도록, PRD 8은
      FastAPI + Uvicorn(로컬 실행 전용) + Jinja2 템플릿 스택을 명시한다.
      현재 코드에는 `web/` 계층도 `serve` 서브커맨드도 없다(`cli.py`에는
      add/remove/list/fetch 4개만 존재).
    - M8은 이후 M9~M12(글 열람·피드 관리·수집 실행·디자인 마감)가 채울
      서버 골격과 라우트 뼈대를 세운다. 이 태스크(T19)는 그중 프레임워크·
      서버 배선만 담당하고, 디자인 토큰·다크 모드·반응형·상태 표현 골격은
      T20으로 분리한다.
  - 내용:
    - 의존성 추가: `pyproject.toml`의 `dependencies`에 `fastapi`,
      `uvicorn`, `jinja2`를 추가한다(PRD 8 명시 스택. 버전 하한은 uv가
      해석하는 최신 안정 버전으로 둔다). 새 의존성이나 되돌리기 어려운
      결정이 아니다(PRD가 스택을 직접 지정).
    - `src/rss_wiki/web/__init__.py`, `src/rss_wiki/web/app.py`를 신설한다.
      `app.py`는 `create_app() -> FastAPI` 앱 팩토리를 제공한다. Jinja2
      템플릿(`web/templates/`)과 정적 파일(`web/static/`, `StaticFiles`
      마운트) 경로를 앱에 연결한다. 경로는 `config.py`의 경로 상수 패턴과
      일관되게 패키지 기준 절대경로로 해석한다.
    - 최소 라우트 `GET /`: `web/templates/base.html`을 렌더링해 200과
      `text/html`을 반환한다. 본문 내용은 최소(제목·본문 블록)로 두고,
      완성도 있는 디자인·상태 표현은 T20 이후가 채운다.
    - `web/templates/base.html`: 이후 화면이 상속할 공통 레이아웃 골격
      (`<title>` 블록·본문 `block content`). 디자인 토큰·다크 모드 전면
      도입은 T20이므로 여기서는 최소 골격만 둔다.
    - `web/static/`: 정적 파일 마운트 대상 디렉터리를 만든다(`.gitkeep`
      또는 T20이 채울 최소 CSS 링크 골격). StaticFiles 마운트가 부팅
      시점에 실패하지 않도록 디렉터리가 존재해야 한다.
    - `cli.py`에 `serve` 서브커맨드 추가: `--host`(기본 `127.0.0.1`,
      로컬 전용)·`--port`(기본 `8000`) 옵션을 받아 `uvicorn.run(app, ...)`로
      구동한다. 실제 서버 기동은 테스트에서 실행하지 않고, 앱은
      `web.app.create_app()`으로 얻어 TestClient로 검증한다. `serve`는
      블로킹 실행이므로 `--help`와 옵션 배선만 회귀로 고정한다.
  - touch: `pyproject.toml`(fastapi·uvicorn·jinja2 추가),
    `src/rss_wiki/web/__init__.py`, `src/rss_wiki/web/app.py`,
    `src/rss_wiki/web/templates/base.html`, `src/rss_wiki/web/static/`(.gitkeep
    또는 최소 css), `src/rss_wiki/cli.py`(`serve` 서브커맨드),
    `tests/test_web_app.py`(신규), `tests/test_cli.py`(`serve --help` 회귀).
  - acceptance:
    - `uv run rss-wiki serve --help` 종료 코드 0, `--host`·`--port` 옵션이
      모두 표시된다.
    - `uv run rss-wiki --help` 종료 코드 0, 서브커맨드가 add/remove/list/
      fetch/serve 5개로 표시된다(회귀: 기존 4개 + serve).
    - `uv run pytest tests/test_web_app.py` 종료 코드 0으로 통과.
      `fastapi.testclient.TestClient(create_app())`로 `GET /`가 200과
      `content-type: text/html`을 반환함을 단언한다(실제 uvicorn 기동·
      네트워크 미사용).
    - `uv run pytest -x` 전체 통과(회귀 없음, 현재 87건 기준 증가).
  - 참고(비차단): 실환경 `uv run rss-wiki serve` 기동으로 브라우저가 루트에
    접속되는지의 종단 확인은 블로킹 서버 특성상 자동 acceptance로 고정하기
    어렵다. TestClient로 앱 팩토리 계약을 고정하고, 실기동 확인은 수동
    후속으로 남긴다(REVIEW T18의 라이브 검증 승계 패턴과 동일).

- [x] **T18. CLI `fetch --concurrency` 배선 + async 구동 + CliRunner 회귀 갱신 + REVIEW T17 메모 해소** — 완료 (`uv run pytest -x` 87 passed, 회귀 없음)
  - 배경:
    - PRD 4.3·8은 글 단위 LLM 요약을 asyncio 병렬로 실행하고 동시 실행 개수를
      옵션(`--concurrency`, 기본 4)으로 조정하도록 요구한다. T17로 순수 병렬
      오케스트레이션(`pipeline.run_fetch_async`, `pipeline.py:111-207`)은
      갖췄으나, CLI `fetch`는 아직 동기 `run_fetch`를 호출한다(`cli.py:118-124`).
      `--concurrency` 옵션도 없다.
    - REVIEW T17이 비차단으로 남긴 async `FeedParseError` 격리 미커버
      (`pipeline.py:148-151`, `test_pipeline.py`에 async 대응 회귀 부재)를
      async 경로를 CLI로 처음 구동하는 이 태스크에서 함께 고정한다.
  - 내용:
    - `cli.py`의 `fetch`에 `--concurrency`(기본 4) 옵션을 추가한다
      (`typer.Option(4, "--concurrency", help=...)`). PRD 4.3이 기본값 4를
      명시하므로 그대로 채택한다.
    - `fetch` 본문의 동기 `pipeline.run_fetch(...)` 호출(`cli.py:118-124`)을
      `asyncio.run(pipeline.run_fetch_async(..., concurrency=concurrency))`로
      교체한다. 프리플라이트(claude 미설치)·누적 인덱스 쓰기(`write_wiki`)·
      `save_state`·리포트 출력(`_echo_report`)·종료 코드 판정
      (`articles_succeeded == 0` 기준, `cli.py:135-138`) 순서와 로직은
      **불변**으로 유지한다(T13·T14 자산 재사용).
    - 동기 `run_fetch`가 더 이상 CLI에서 호출되지 않게 되면, 순수 계층으로
      제거할지 하위 호환용으로 유지할지 이 시점에 결정한다. 기본 채택값 —
      기존 회귀(`test_pipeline.py`의 동기판 테스트 6건)가 계약을 고정하고
      있으므로 **유지**한다(자체 결정: 되돌리기 쉬움. 제거는 테스트까지
      함께 정리해야 하므로 최소 변경 원칙에 따라 보류).
    - **REVIEW T17 메모 해소**: `tests/test_pipeline.py`에 async
      `FeedParseError` 격리 회귀 1건을 추가한다. 동기판
      `test_run_fetch_skips_feed_on_parse_error_and_continues_other_feeds`
      (`test_pipeline.py:70-96`)에 대응하여, 한 피드의 `select`가
      `FeedParseError`를 올릴 때 그 피드만 `report["feeds"]["failed"]`에
      집계되고 다른 피드의 글은 정상 병렬 처리됨을 단언한다(통과-위장 방지:
      해당 피드가 실패로 집계되지 않으면 실패).
    - [선택] `test_run_fetch_async_respects_concurrency_limit`의 상한 단언에
      하한(`max_seen >= 2`)을 더해 세마포어의 과도 억제(실질 순차화) 회귀를
      함께 잡는다.
  - touch: `src/rss_wiki/cli.py`(`--concurrency` 옵션·`asyncio.run` 배선),
    `tests/test_cli.py`(async 경로 회귀 갱신·`--concurrency` 전달 회귀),
    `tests/test_pipeline.py`(async `FeedParseError` 격리 회귀 추가).
  - acceptance:
    - `uv run rss-wiki fetch --help` 종료 코드 0, `--limit`·`--concurrency`
      옵션이 모두 표시된다.
    - `uv run pytest tests/test_cli.py` 종료 코드 0으로 통과. 신규/갱신 회귀로
      (1) `fetch`가 async 경로(`run_fetch_async`)를 `asyncio.run`으로 구동함,
      (2) `--concurrency 값`이 파이프라인에 전달됨(주입/모킹으로 값 전달 단언),
      (3) 기존 종료 코드 경계(부분 실패→0, 전체 실패→비0, claude 미설치→비0,
      새 글 없음→0, 등록 피드 없음→0)가 async 전환 후에도 불변임을 회귀로
      고정한다(통과-위장 방지: 실제 프로세스·네트워크 미사용, 주입 fake).
    - `uv run pytest tests/test_pipeline.py` 종료 코드 0으로 통과. 신규 async
      `FeedParseError` 격리 회귀가 한 피드만 실패로 집계되고 다른 피드 글은
      병렬 처리됨을 단언(REVIEW T17 메모 해소).
    - `uv run pytest -x` 전체 통과(회귀 없음, 현재 85건 기준 증가).
    - `uv run rss-wiki --help` 종료 코드 0, 기존 4개 서브커맨드 정상 표시.

- [x] **T17. `pipeline.run_fetch_async` 순수 async 병렬 오케스트레이션 + `_default_run_async` 회귀 (REVIEW T16 메모 해소)** — 완료 (`uv run pytest -x` 85 passed, 회귀 없음)
  - 배경:
    - PRD 4.3·8은 수집된 글의 LLM 요약을 글 단위 asyncio 병렬로 실행하고
      세마포어로 동시 실행 개수를 제한하도록 요구한다. T16으로 실행 단위
      (`summarize_article_async`)는 갖췄으나, `pipeline.run_fetch`는 아직 순차
      for 루프(`pipeline.py:58-104`)로 이를 병렬 소비하지 못한다.
    - CLI `--concurrency` 옵션·`asyncio.run` 구동·CliRunner 회귀 갱신은 T18
      범위다. T17은 그 선행으로, 순수 로직(파일 시스템·네트워크·프로세스 미접근)
      계층에서 병렬 오케스트레이션 함수만 추가한다(한 세션 크기).
    - REVIEW T16이 비차단으로 남긴 `_default_run_async` 미커버(`summarize.py:62-66`,
      `returncode != 0` 분기·`stdout.decode()`)를 async 요약을 처음 병렬 소비하는
      이 태스크에서 함께 고정한다.
  - 내용:
    - `pipeline.py`에 `run_fetch_async(feeds, state, *, limit, now, collected_date,
      concurrency, select=ingest.select_new_articles, extract=extract_module.extract_body,
      summarize=summarize_module.summarize_article_async)`를 추가한다. 반환 계약
      (`batch`/`state`/`report` 3키)은 동기 `run_fetch`와 동일하게 유지한다.
    - 피드별 새 글 선정(`select`)은 **순차**로 두어 피드 파싱 실패
      (`ingest.FeedParseError`) 격리를 동기판과 동일하게 유지한다. 선정된 전체
      글의 본문 확보+요약은 `asyncio.Semaphore(concurrency)`로 동시 실행 개수를
      제한한다. 동기 `extract`는 이벤트 루프를 막지 않도록
      `asyncio.to_thread(extract, article)`로 감싼다(PLAN 미해결 의사결정 채택값).
    - 개별 글 실패(`extract.ArticleExtractionError`/`summarize.SummarizeError`)는
      해당 글만 건너뛰고(state에 기록하지 않아 다음 `fetch`에서 재시도) 다른 글
      처리에 영향을 주지 않는다(PRD 4.3·7).
    - **결정성**: 병렬 요약 완료 후 파일명 배정(`wiki.article_filename`)·state
      적재·리포트 집계는 입력 순서(피드 순서 × 각 피드 내 글 순서)대로 직렬
      수행한다. 같은 날짜·같은 슬러그 글이 여럿이어도 파일명 접미사(`-2`)와
      리포트 건수가 실행마다 달라지지 않아야 한다.
    - 동기 `run_fetch`는 **변경하지 않는다**(하위 호환 유지, CLI 전환은 T18).
    - REVIEW T16 메모: `tests/test_summarize.py`에 `_default_run_async` 회귀 2건을
      추가한다. `asyncio.create_subprocess_exec`를 스텁으로 대체해 (1) `returncode`가
      비0인 가짜 프로세스에서 `subprocess.CalledProcessError`가 생성됨을,
      (2) `returncode==0`·`communicate`가 바이트를 반환하는 가짜 프로세스에서
      `stdout.decode()` 결과가 반환됨을 직접 단언한다(통과-위장 방지: 실제 조립부를
      경유).
  - touch: `src/rss_wiki/pipeline.py`(async 오케스트레이션 함수 추가),
    `tests/test_pipeline.py`(async 회귀 추가), `tests/test_summarize.py`
    (`_default_run_async` 회귀 2건). `cli.py`는 손대지 않는다(T18).
  - acceptance:
    - `uv run pytest tests/test_pipeline.py` 종료 코드 0으로 통과. 주입한 async
      fake로 (1) 정상 병렬 처리 결과의 `batch`/`state`/`report`가 순차판과 동일한
      값(파일명·meta 5키 포함)임을 단언, (2) 한 글의 `summarize`가
      `SummarizeError`를 올릴 때 그 글만 실패로 격리되고 다른 글은 성공함을
      리포트 건수로 단언, (3) 같은 날짜·슬러그 글 2개 입력 시 파일명이 입력
      순서대로 결정적으로 배정됨(`-2` 접미사)을 단언, (4) `concurrency=2`일 때
      동시 실행 최대치가 2를 넘지 않음을 카운터로 단언(통과-위장 방지: 제한 없이는
      실패). `asyncio.run` + 주입 fake로 실제 프로세스·네트워크·파일 I/O 미사용.
    - `uv run pytest tests/test_summarize.py` 종료 코드 0으로 통과. 신규 2건이
      `_default_run_async`의 비0 종료→`CalledProcessError`, 정상 종료→`decode`
      반환을 직접 단언(REVIEW T16 메모 해소).
    - `uv run pytest -x` 전체 통과(회귀 없음, 현재 79건 기준 증가).
    - `uv run rss-wiki --help` 종료 코드 0, 기존 4개 서브커맨드 정상 표시.

- [x] **T16. `summarize_article_async` — asyncio 기반 비동기 요약 함수 추가 (M7 선행)** — 완료 (`uv run pytest -x` 79 passed, 회귀 없음)
  - 배경:
    - PRD 4.3·8은 수집된 글의 LLM 요약을 글 단위 asyncio 병렬로 실행하고
      세마포어로 동시 실행 개수를 제한하도록 요구한다. 현재 `summarize.py`의
      `summarize_article`은 동기 `subprocess.run`(`summarize.py:20-27`)이라
      병렬화할 수 없다.
    - 병렬 오케스트레이션(`pipeline.run_fetch` async화)과 CLI `--concurrency`
      배선은 T17 범위다. T16은 그 선행으로, 병렬 실행의 단위가 되는 비동기
      요약 함수만 추가한다(순수 로직·주입형 단위 테스트, 한 세션 크기).
  - 내용:
    - `summarize.py`에 `summarize_article_async(article, body, *, feed_name,
      run=_default_run_async)`를 추가한다. 기본 실행기 `_default_run_async`는
      `asyncio.create_subprocess_exec("claude", "-p", prompt, ...)`로 서브프로세스를
      비동기 실행하고 stdout을 반환한다. `claude` 미설치(`FileNotFoundError`)와
      비0 종료(반환 코드 != 0)는 동기판과 동일하게 `SummarizeError`로 감싼다.
    - 반환 계약은 동기 `summarize_article`과 동일한 5키
      (`summary`·`title`·`link`·`published`·`feed_name`)를 유지한다.
      프롬프트 조립(`_build_prompt`)은 기존 함수를 재사용한다.
    - 실행기 `run`을 주입 가능하게 두어 단위 테스트가 실제 프로세스 없이
      async fake로 동작하게 한다(기존 동기판 주입 패턴과 대칭).
    - 동기 `summarize_article`은 **변경하지 않는다**(하위 호환 유지, 파이프라인
      이관은 T17).
  - touch: `src/rss_wiki/summarize.py`(async 함수·기본 실행기 추가),
    `tests/test_summarize.py`(async 회귀 추가).
  - acceptance:
    - `uv run pytest tests/test_summarize.py` 종료 코드 0으로 통과. 주입한
      async fake로 (1) 정상 경로에서 5키 반환 계약과 값 매핑을 단언,
      (2) 미설치(`FileNotFoundError`)·비0 종료 각각에서 `SummarizeError`가
      발생함을 단언(통과-위장 방지: 예외 미발생 시 실패). 실제 프로세스·
      네트워크 미사용(`asyncio.run` + 주입 fake).
    - `uv run pytest -x` 전체 통과(회귀 없음, 현재 76건 기준 증가).
    - `uv run rss-wiki --help` 종료 코드 0, 기존 4개 서브커맨드 정상 표시.

- [x] **T15. 미고정 종료 코드 경계 2건 독립 회귀 추가 + IMPL/JOURNAL 보고 수치 정합 (REVIEW T14 메모 1·2 해소)** — 완료 (`uv run pytest -x` 76 passed, 회귀 없음)
  - 배경:
    - REVIEW T14가 테스트 충실도를 2점으로 감점한 근거는, T14 내용이 "회귀로
      고정"하라 요구한 5개 종료 코드 경계 중 2개 — **(a) 피드 파싱 성공 + 새 글
      없음(실패 0, 산출 0) → 0**, **(b) 등록 피드 없음(전부 0) → 0** — 의 독립
      단언이 부재한 점이다. 두 경계 모두 `total_failed == 0` 분기로 귀결되어
      현재 부분 실패 테스트가 간접 경유할 뿐, 판정식(`cli.py:135-138`)이
      의도대로 exit 0을 반환하는지 직접 고정하는 회귀가 없다.
    - 코드는 이미 두 경계에서 올바르게 exit 0을 반환한다(조건 `total_failed > 0
      and articles_succeeded == 0`에 진입하지 않음). 이번 태스크는 동작 변경이
      아니라 T14 acceptance가 요구한 회귀 고정의 미완결분을 채우는 마감 정비다.
    - REVIEW T14 메모 2: `docs/IMPL.md`와 `docs/JOURNAL.md`의 generator 항목이
      `tests/test_cli.py`를 "10 passed"로 보고했으나 실제 수집·통과는 9건이다.
      실질 영향은 없으나 보고 수치를 실행 출력에 맞춰 정정한다.
  - 내용:
    - `tests/test_cli.py`에 두 경계의 독립 회귀를 추가한다(통과-위장 방지를 위해
      각 경계가 판정식을 실제로 경유하도록 구성).
      - (a) **새 글 없음**: `feeds.succeeded>=1, articles.succeeded=0,
        articles.failed=0`(할 일 없음) 조합에서 `fetch` 종료 코드 0을 단언.
      - (b) **등록 피드 없음**: `feeds`/`articles` 전부 0(피드 없음) 조합에서
        `fetch` 종료 코드 0을 단언.
      - `CliRunner`와 주입한 가짜 `pipeline.run_fetch` 반환 리포트로 구성하고
        프로세스·네트워크·파일 I/O를 사용하지 않는다(기존 test_cli.py 패턴 준수).
    - `src/rss_wiki/cli.py`의 판정식은 **변경하지 않는다**(이미 정합). 이번 태스크는
      테스트·문서만 다룬다.
    - `docs/IMPL.md`의 `tests/test_cli.py` 통과 건수 표기를 실제 수집 건수로
      정정한다(신규 회귀 2건 추가 후의 실제 값으로 기재).
  - touch: `tests/test_cli.py`(경계 회귀 2건 추가), `docs/IMPL.md`(보고 수치 정정).
    `src/rss_wiki/cli.py`는 import 참조만(수정 금지).
  - acceptance:
    - `uv run pytest tests/test_cli.py` 종료 코드 0으로 통과. 신규 2건이
      (a) 새 글 없음·(b) 피드 없음 경계에서 각각 `fetch` 종료 코드 0을 단언.
      통과 건수는 기존 9건 + 신규 2건 = 11건.
    - `uv run pytest -x` 전체 통과(회귀 없음, 현재 74건 기준 76건으로 증가).
    - `uv run rss-wiki --help` 종료 코드 0, 4개 서브커맨드 정상 표시(회귀 없음).
    - `docs/IMPL.md`의 `test_cli.py` 통과 건수 표기가 실제 실행 출력과 일치.

- [x] **T14. 종료 코드 경계를 "글 산출 0건이면 비0"으로 정합 (REVIEW T13 메모 1 해소)** — 완료 (`uv run pytest -x` 74 passed, 회귀 없음)
  - 배경:
    - REVIEW T13 메모 1(비차단)이 남긴 종료 코드 경계 논쟁을 해소한다. 현재
      `cli.py:135-138`의 판정은 `total_succeeded = feeds.succeeded + articles.succeeded`
      로 계산하므로, **피드 파싱은 성공(feeds.succeeded≥1)했으나 그 피드의 모든
      글이 실패(articles.succeeded=0, articles.failed≥1)**해 요약 산출물이 0건인
      경우에도 종료 코드 0을 반환한다(REVIEW에서 직접 재현 확인).
    - PRD 7의 "전체 실패(시도했으나 성공 0건)는 0이 아닌 종료 코드"를 이 도구의
      산출 단위(요약된 글)로 읽으면 이 경계는 비0이 기대된다. 도구의 목적이
      "글을 요약해 위키에 적재"하는 것이므로, 요약 산출이 0건인 실패 있는 실행을
      성공(0)으로 신호하는 것은 목적에 어긋난다. 종료 코드 의미를 **글 산출
      기준**으로 좁힌다. (자체 결정: 종료 코드 의미는 되돌리기 쉬움)
  - 내용:
    - `cli.py`의 `fetch` 종료 코드 판정(`cli.py:135-138`)을 다음 규칙으로 교체한다.
      성공의 단위를 피드 파싱이 아니라 **글 산출**로 본다.
      - `articles_succeeded = report["articles"]["succeeded"]`
      - `total_failed = report["feeds"]["failed"] + report["articles"]["failed"]`
      - `if total_failed > 0 and articles_succeeded == 0: raise typer.Exit(code=1)`
    - 이 규칙의 각 경계는 다음과 같이 매핑되어야 한다(회귀로 고정).
      - 피드 전부 파싱 실패(글 시도 0) → 비0 (기존 동작 유지).
      - 피드 파싱 성공 + 그 피드의 모든 글 실패(글 산출 0) → **비0** (변경점).
      - 일부 글 성공 + 일부 글 실패(부분 실패) → 0 (경고 포함, 기존 유지).
      - 피드 파싱 성공 + 새 글 없음(실패 0, 산출 0) → 0 (할 일 없음, 기존 유지).
      - 등록 피드 없음(전부 0) → 0 (할 일 없음, 기존 유지).
    - `_echo_report` 리포트 출력 형식·프리플라이트·배선 순서는 변경하지 않는다.
      이번 태스크는 종료 코드 판정식만 좁히는 최소 변경이다.
  - touch: `src/rss_wiki/cli.py`(종료 코드 판정식만), `tests/test_cli.py`(경계 회귀 보강).
    필요 시 `src/rss_wiki/pipeline.py`는 import 참조만.
  - acceptance:
    - `uv run pytest tests/test_cli.py` 종료 코드 0으로 통과. `CliRunner`와 주입한
      가짜 의존으로 신규/보강 회귀가 (1) **피드 파싱 성공 + 그 피드 글 전부 실패**
      (feeds.succeeded=1, articles.succeeded=0, articles.failed≥1) 시 **비0 종료
      코드**임을 단언(현재 로직에서는 0이 나오므로 판정식 변경 없이는 실패 →
      통과-위장 방지), (2) 일부 글 성공 + 일부 글 실패(부분 실패)는 여전히 종료
      코드 0임을 단언, (3) 기존 "전체 실패(피드 파싱 실패) 비0" 회귀가 유지됨을
      확인한다. 프로세스·네트워크 미사용.
    - `uv run pytest -x` 전체 통과(회귀 없음, 현재 73건 기준 유지 또는 증가).
    - `uv run rss-wiki --help` 종료 코드 0, 4개 서브커맨드 정상 표시(회귀 없음).

## 이전 사이클 (M6 실패 정책 & 파이프라인: T13 완료)

- [x] **T13. CLI `fetch` 배선 + 누적 인덱스 쓰기 + claude 프리플라이트 + 종료 코드 + CliRunner 회귀** — 완료 (`uv run pytest -x` 73 passed, 회귀 없음)
  - 내용:
    - `cli.py`의 `fetch` 스텁(`cli.py:66-69`)을 실제 파이프라인으로 배선한다.
      `load_feeds`/`load_state` → `pipeline.run_fetch` → `wiki.write_wiki` →
      `save_state` → 리포트 stdout 출력 순서로 연결한다. `run_fetch`에 넘길
      `now`(처리 시각 ISO8601)·`collected_date`(수집일 `YYYY-MM-DD`)는 CLI에서
      생성해 주입한다(순수 계층은 시각을 직접 읽지 않는다).
    - **claude 미설치 프리플라이트(PRD 6·7)**: `fetch` 진입 시 `claude` 실행 가능
      여부를 확인해, 없으면 명확한 사용자 대면 메시지와 **비0 종료 코드**로 중단한다.
      이로써 "실행 불가"(claude 미설치 → 전체 중단)와 개별 글 요약 실패
      (`SummarizeError` → 글 스킵, `run_fetch`가 이미 리포트로 처리)를 분리한다.
      프리플라이트 확인 함수는 주입 가능하게 하여(기본값은 `shutil.which("claude")`
      또는 유사) CliRunner 테스트가 프로세스 없이 동작하게 한다.
    - **누적 인덱스 쓰기(REVIEW T11·T12 이월 해소)**: index/feeds/daily는 이번 배치만이
      아니라 **`state`에 누적된 전체 글의 표시 메타**로 재생성해야 `fetch` 재실행 시
      이전 글이 인덱스에서 사라지지 않는다(PRD 4.4 "재생성 또는 갱신"). 누적 입력원은
      PLAN 미해결 의사결정 표의 채택값대로 **`state.json`의 표시 메타 캐시**를 쓴다
      (`state["processed"][id]["meta"]`, `run_fetch`가 이미 적재). 개별 글 파일은
      이번 배치(`run_fetch` 반환 `batch`)만 쓰되, 인덱스·피드·데일리는 누적 전체
      메타로 재생성하도록 `wiki.write_wiki` 시그니처를 **하위 호환 가법 확장**한다
      (기존 T11 테스트가 그대로 통과해야 한다).
    - **파일명 일관성(REVIEW T12 이월 해소)**: `run_fetch`가 배정해 `state.meta.filename`에
      저장한 파일명과, 개별 글 파일·인덱스 링크의 파일명이 정확히 일치하도록 배선한다.
      `write_wiki`가 파일명을 자체 재계산해 state와 어긋나지 않게 한다.
    - **종료 코드(PRD 7)**: 부분 실패(성공 1건 이상 + 실패 존재)는 0(경고 포함),
      전체 실패(시도했으나 성공 0건)·실행 불가(claude 미설치)는 비0으로 매핑한다.
      성공/실패 건수와 실패 사유 요약을 stdout 리포트로 출력한다.
    - **입력 state 불변성(REVIEW T12 이월, 비차단)**: `run_fetch`는 입력 state를
      보존하므로, CLI는 반환된 새 state만 `save_state`로 저장한다. 통합 테스트에서
      원본 state 불변성 회귀를 함께 고정한다.
    - **본문 출처 리포트(REVIEW T12·T6 이월, 비차단)**: 리포트에는 성공/실패 건수와
      실패 사유만 표시하고 본문 출처(원문/RSS) 통계는 생략한다(자체 결정, 되돌리기 쉬움).
    - **CliRunner 회귀(REVIEW T3 이월 해소)**: `typer.testing.CliRunner`로
      `tests/test_cli.py`를 신규 작성해 add/remove/list/fetch의 사용자 대면 오류·종료
      코드를 회귀에 고정한다. `StoreError`/`DuplicateFeedError`/`FeedValidationError`/
      `FeedNotFoundError` 변환 경로와 `fetch`의 claude 미설치·부분 실패·전체 실패
      종료 코드 분기를 포함한다.
  - touch: `src/rss_wiki/cli.py`, `src/rss_wiki/wiki.py`(누적 인덱스 입력을 위한
    `write_wiki` 가법 확장), `tests/test_cli.py`(신규), `tests/test_wiki.py`(확장
    시그니처 회귀 보강). 필요 시 `src/rss_wiki/pipeline.py`·`store.py`·`config.py`는
    import 참조만.
  - acceptance:
    - `uv run pytest tests/test_cli.py` 종료 코드 0으로 통과. `CliRunner`와 주입한
      가짜 의존(피드/state 로드·`run_fetch`·claude 프리플라이트)으로 (1) claude 미설치
      시 사용자 대면 메시지 + 비0 종료 코드, (2) 부분 실패(성공≥1 + 실패 존재)는 종료
      코드 0 + 리포트에 성공/실패 건수 표시, (3) 전체 실패(성공 0건)는 비0 종료 코드,
      (4) `save_state`에 `run_fetch` 반환 state가 저장되고 원본 state가 변경되지 않음,
      (5) add/remove/list의 `StoreError`/`DuplicateFeedError`/`FeedValidationError`/
      `FeedNotFoundError`가 트레이스백 없이 오류 메시지 + 종료 코드 1로 변환됨을 검증한다.
      프로세스·네트워크 미사용.
    - `uv run pytest tests/test_wiki.py` 종료 코드 0으로 통과. `write_wiki` 가법 확장
      후에도 기존 T11 테스트가 통과하고(하위 호환), 누적 표시 메타를 주입하면 개별 글
      파일은 이번 배치만, index/feeds/daily는 누적 전체 메타로 재생성되며 인덱스 링크가
      배정 파일명과 정확히 일치함을 `tmp_path` 격리로 검증한다.
    - `uv run pytest -x` 전체 통과(회귀 없음, 현재 63건 기준 증가).
    - `uv run rss-wiki --help` 종료 코드 0, 4개 서브커맨드 정상 표시(회귀 없음).

## 이전 사이클 (M6 실패 정책 & 파이프라인: T12 완료)

- [x] **T12. `pipeline.run_fetch` 순수 오케스트레이션 (피드/글 루프 + 실패 스킵 + state 적재 + 실행 리포트)** — 완료 (REVIEW PASS 11/12)
  - 내용:
    - `pipeline.py`: 순수 로직 계층. `feeds.py`/`ingest.py`/`extract.py`/
      `summarize.py`/`wiki.py`와 동일하게 파일 시스템·네트워크·프로세스에 의존하지
      않도록, 각 단계 함수(`select`/`extract`/`summarize`)와 처리 시각(`now`)·
      수집일(`collected_date`)을 **주입 가능**하게 설계한다. 실제 파일 쓰기·
      `state.json` 저장·종료 코드 매핑·stdout 출력은 T13(CLI) 범위다.
    - **`run_fetch(feeds, state, *, limit, now, collected_date, select=ingest.select_new_articles, extract=extract.extract_body, summarize=summarize.summarize_article)`**
      형태로, 전체 피드를 순회하며 새 글을 수집→본문 확보→요약한 결과를 모아 반환한다.
      - **피드 루프**: 각 피드에 대해 `select(feed, state, limit=limit)`를 호출한다.
        `ingest.FeedParseError`가 오르면 해당 피드를 건너뛰고 리포트에 피드 실패로
        기록한 뒤 다음 피드로 계속한다(PRD 7 "건너뛰고 계속").
      - **글 루프**: 선정된 각 글에 대해 `extract(article)` → `summarize(article, body, feed_name=feed["name"])`를
        수행한다. `extract.ArticleExtractionError` 또는 `summarize.SummarizeError`가
        오르면 해당 글을 건너뛰고 리포트에 글 실패로 기록한다. **이 글은 state에
        처리 완료로 기록하지 않아** 다음 `fetch`에서 재시도된다(PRD 7). 같은 피드의
        다른 글 처리는 계속한다.
      - **성공 처리**: 성공한 글은 `state["processed"][id]`에
        `{"processed_at": now, "status": "ok", "meta": {...}}`로 적재한다. `meta`에는
        인덱스 누적 재생성에 필요한 표시 메타(파일명·제목·정규화 발행일·수집일·
        피드명)를 담는다(누적 인덱스 입력원 자체 결정, PLAN 미해결 의사결정 참조).
      - **파일명 안정성(자체 결정)**: 파일명은 성공 시점에 한 번 배정하고 state에
        저장한다. 발행일은 `wiki.normalize_date(published, fallback=collected_date)`로
        정규화하고, `wiki.article_filename(title, date, existing=<state 누적 파일명 +
        이번 실행 배정분>)`로 배정해 이전 `fetch` 산출물과 충돌 시 접미사로 회피한다.
        (`wiki`의 순수 함수만 import하며 파일 쓰기는 하지 않는다.)
      - **반환값**: 이번 배치에서 성공한 글 목록(각 글의 `summary_result`·
        `collected_date`·배정 `filename`; T13이 `write_wiki`로 실제 파일을 쓸 입력),
        갱신된 `state`(성공 글만 processed 적재), 실행 리포트(피드/글 성공·실패
        건수와 사유)를 담아 돌려준다. 반환은 순수 데이터이며 영속화·출력은 T13.
    - **claude 미설치 구분(비범위, T13)**: `SummarizeError`는 이 계층에서 글 단위
      스킵으로 처리한다. "claude 미설치 → 전체 중단·비0 종료"는 T13의 CLI 프리플라이트
      (`claude` 실행 가능 여부 확인)에서 분리 처리하므로 T12는 다루지 않는다.
  - touch: `src/rss_wiki/pipeline.py`, `tests/test_pipeline.py`
    (필요 시 `src/rss_wiki/wiki.py`·`ingest.py`·`extract.py`·`summarize.py`는 import 참조만)
  - acceptance:
    - `uv run pytest tests/test_pipeline.py` 종료 코드 0으로 통과. 주입한 가짜
      `select`/`extract`/`summarize`와 고정 `now`/`collected_date`로 (1) 정상 경로에서
      성공 글이 반환 배치에 담기고 `state["processed"][id]`에 `meta`(파일명·제목·
      정규화 발행일·수집일·피드명)+`processed_at`/`status`로 적재됨, (2) 한 피드가
      `FeedParseError`를 올리면 그 피드는 건너뛰고(배치·processed에 없음, 리포트
      피드 실패 1건) 다른 피드는 정상 처리됨, (3) `ArticleExtractionError`와
      `SummarizeError` 각각에 대해 해당 글이 `processed`에 기록되지 않고(재시도 보장)
      배치에서 제외되며 리포트 글 실패가 증가하고 같은 피드의 다른 글은 정상 처리됨,
      (4) state에 기존 파일명이 있는 상태에서 같은 날짜·슬러그 새 글이 들어오면
      접미사가 붙어 기존 파일명과 충돌하지 않고 배정 파일명이 state `meta`에 저장됨,
      (5) `published` 부재·파싱 실패 글은 파일명·`meta`의 발행일이 주입한
      `collected_date`로 대체됨을 검증한다. 파일 시스템·네트워크·프로세스 미사용,
      `state.json` 미접근.
    - `uv run pytest -x` 전체 통과(회귀 없음).

## 이전 사이클 (M5 위키 생성: T11 완료)

- [x] **T11. 위키 파일 쓰기 통합 (wiki.py: write_wiki — 개별 글 파일 쓰기 + index/feeds/daily 재생성 + 최신 글 정렬 배선)** — 완료 (REVIEW PASS 11/12)
  - 내용:
    - T9·T10에서 만든 순수 함수(`render_article`/`render_index`/`render_feed_page`/
      `render_daily_page`/`article_filename`)를 실제 파일 시스템에 배선하는
      통합 계층을 `wiki.py`에 추가한다. 이번 태스크에서 처음으로 파일을 실제로
      쓴다.
    - **`write_wiki(articles, *, wiki_dir=config.WIKI_DIR)`** (또는 유사 시그니처):
      전달받은 글 표시 메타 리스트를 받아 `wiki/` 트리를 생성·갱신한다.
      - 출력 디렉터리(`wiki_dir`)는 **주입 가능**하게 하여(기본값 `config.WIKI_DIR`)
        단위 테스트가 `tmp_path`로 파일 시스템 격리 상태에서 동작하게 한다. 다른
        모듈의 주입형 순수 로직 패턴과 일관되며, WIKI_DIR가 처음으로 실제 사용된다.
      - `wiki_dir/articles/`, `wiki_dir/feeds/`, `wiki_dir/daily/`를 생성한다
        (부모 포함, 이미 있으면 무시).
      - 각 글에 대해 `article_filename`(배치 내 충돌 시 접미사)으로 파일명을 정하고
        `render_article` 결과를 `articles/<파일명>.md`로 쓴다. 파일명은 인덱스 링크와
        정확히 일치해야 한다.
      - `render_index` 결과를 `index.md`로, 피드별로 `render_feed_page`를
        `feeds/<슬러그>.md`로, 수집일별로 `render_daily_page`를
        `daily/YYYY-MM-DD.md`로 쓴다(재생성/갱신, PRD 4.4).
    - **최신 글 정렬 배선** (REVIEW T10 이월 해소): `render_index`는 입력 순서대로
      나열하므로, `write_wiki`가 인덱스에 넘기기 전 글 리스트를 **발행일(또는 수집일)
      내림차순**으로 정렬한다. 정렬 책임을 이 호출부에 명시적으로 두고 회귀로 고정한다.
    - **입력 주도(input-driven) 한정 (자체 결정)**: 인덱스/피드/데일리 재생성은
      전달받은 표시 메타 리스트만으로 수행한다. 누적 전체 글 집합을 어디서 얻는가
      (상태 적재 vs `wiki/articles/` 스캔)는 M6 파이프라인 배선 시점의 결정이므로
      T11에서는 다루지 않는다. 이로써 `write_wiki`는 사전 wiki 상태에 의존하지 않아
      테스트가 격리된다(되돌리기 쉬움, 근거를 IMPL에 남긴다).
    - **상태/산출물 분리 확인** (PRD 5): `write_wiki`는 `state.json`을 읽거나 쓰지
      않는다. 위키 파일 쓰기와 처리 완료 상태 기록을 분리해, 위키 파일을 수동
      편집·삭제해도 중복 수집이 발생하지 않는 구조임을 이 계층에서 보장한다.
      (state 기반 스킵은 이미 `ingest`가 담당한다.)
    - **비고**: 이번 태스크는 파일 쓰기 통합까지이며, `fetch` 파이프라인 배선
      (ingest→extract→summarize→write_wiki)과 실패 리포트·종료 코드는 M6 범위다.
  - touch: `src/rss_wiki/wiki.py`, `tests/test_wiki.py` (필요 시 `src/rss_wiki/config.py` 참조만)
  - acceptance:
    - `uv run pytest tests/test_wiki.py` 종료 코드 0으로 통과. `tmp_path`를 `wiki_dir`로
      주입해 (1) `write_wiki`가 `articles/`·`feeds/`·`daily/` 디렉터리와 `index.md`를
      생성함, (2) 각 입력 글이 `articles/<파일명>.md`로 쓰이고 파일 내용이
      `render_article` 결과와 일치함, (3) `index.md`가 글을 최신순(발행일/수집일
      내림차순)으로 나열함을 순서 단언으로 고정함(정렬 제거 시 실패), (4) 피드별
      `feeds/<슬러그>.md`가 해당 피드 글만, 수집일별 `daily/<날짜>.md`가 해당 수집일
      글만 나열함, (5) 배치 내 파일명 충돌 시 접미사가 붙고 인덱스 링크가 실제 쓰인
      파일명과 일치함을 검증한다. 네트워크 미사용, `state.json` 미접근.
    - `uv run pytest -x` 전체 통과(회귀 없음).

## 이전 사이클 (M5 위키 생성: T10 완료)

- [x] **T10. 위키 인덱스 순수 조립 (wiki.py: render_index / render_feed_page / render_daily_page + 발행일 표시 통일 + 구조 단언 보강)** — 완료 (REVIEW PASS 11/12)
  - 내용:
    - `wiki.py`에 인덱스·피드·데일리 페이지 마크다운을 조립하는 순수 함수를
      추가한다. T9와 동일하게 파일 시스템·네트워크에 의존하지 않는다. 실제 파일
      쓰기와 디렉터리 생성은 T11 범위이며, 이번 태스크는 마크다운 문자열 조립까지만
      다룬다.
    - **인덱스 입력 계약(자체 결정)**: `render_*` 함수는 각 글의 표시 메타
      (파일명·제목·발행일·수집일·피드명)를 담은 dict 리스트를 입력으로 받는다.
      리스트가 무엇을 담는지(호출부 조립)는 T11 소관이며, 이 데이터 계약은
      되돌리기 쉬운 수준이므로 채택 근거를 IMPL에 남긴다.
    - **`render_index(articles)`** (PRD 4.4): 전체 인덱스(`index.md`)를 조립한다.
      최신 글 목록(개별 글 파일 `articles/<파일명>`로의 상대 링크)과 피드 목록
      링크(`feeds/<슬러그>.md`)를 포함한다.
    - **`render_feed_page(feed_name, articles)`**: 해당 피드의 글만 링크로 나열한
      피드별 페이지(`feeds/<슬러그>.md`)를 조립한다.
    - **`render_daily_page(date, articles)`**: 해당 수집일의 글을 나열한 날짜별
      페이지(`daily/YYYY-MM-DD.md`)를 조립한다. `daily/`는 PRD 4.4 명시대로
      **수집일** 기준이다(발행일 아님).
    - **발행일 표시 통일** (REVIEW T9 이월 해소): `render_article`이 `published`를
      정규화 없이 원문 그대로 상단 메타에 노출하는 문제를 해소한다. 표시용 발행일도
      `normalize_date` 결과(`YYYY-MM-DD`)로 통일해 파일명 날짜(`article_filename`이
      쓰는 `normalize_date` 결과)와 본문 표시 날짜의 형식을 일치시킨다.
      `render_article`이 수집일 fallback을 주입받도록 시그니처를 조정한다.
      (자체 결정: 표시 형식은 되돌리기 쉬움.)
    - **레이블-값 구조 단언 보강** (REVIEW T9 비차단 메모): `render_article` 테스트가
      각 메타값의 존재만 단언하던 것을, 레이블과 값의 결합(`link`가 "원문 링크:"
      줄에, `published`가 "발행일:" 줄에 배치)까지 단언하도록 보강한다.
    - 반환은 순수 데이터(마크다운 문자열)이며, 디렉터리 생성·파일 쓰기·인덱스
      실제 재생성은 T11 범위로 분리한다.
  - touch: `src/rss_wiki/wiki.py`, `tests/test_wiki.py`
  - acceptance:
    - `uv run pytest tests/test_wiki.py` 종료 코드 0으로 통과. 순수 함수 단언으로
      (1) `render_index`가 전달된 글들의 개별 파일 링크와 피드 목록 링크를 포함함,
      (2) `render_feed_page`가 해당 피드의 글만 링크로 나열함,
      (3) `render_daily_page`가 해당 날짜(수집일)의 글을 나열함,
      (4) `render_article`의 발행일 표시가 `normalize_date` 결과(파일명 날짜와 동일
      형식)와 일치하고, 발행일 부재·파싱 실패 시 주입한 수집일 fallback으로 대체됨,
      (5) `render_article`의 레이블-값 결합(원문 링크·발행일 줄 배치)을 단언함을
      검증한다. 파일 시스템·네트워크 미사용.
    - `uv run pytest -x` 전체 통과(회귀 없음).

## 이전 사이클 (M5 위키 생성: T9 완료)

- [x] **T9. 위키 순수 조립 로직 (wiki.py: 개별 글 마크다운 렌더링 + 슬러그 + 발행일 정규화)** — 완료
  - 내용:
    - `wiki.py`: 순수 로직 계층. `feeds.py`/`ingest.py`/`extract.py`/`summarize.py`와
      동일하게 파일 시스템에 의존하지 않는 순수 함수로 구성한다. 실제 파일 쓰기와
      인덱스(`index.md`/`feeds/`/`daily/`) 재생성은 T10 범위이며, 이번 태스크는
      개별 글 마크다운 조립·슬러그·발행일 정규화까지만 다룬다.
    - **발행일 정규화** (REVIEW T7 이월 해소): `normalize_date(published, *, fallback)`
      형태로, `summarize_article` 반환 dict의 `published`(RSS 원문 문자열,
      `ingest.py:27`에서 미정규화) 문자열을 `YYYY-MM-DD`로 변환한다. 발행일이
      없거나 파싱 실패 시 주입된 `fallback`(수집일)을 사용한다. `articles/`
      파일명 날짜는 이 정규화 결과를 쓴다(자체 결정: PRD 4.4는 `daily/`만 수집일로
      명시, `articles/` 날짜 기준은 미명시이므로 발행일 우선·부재 시 수집일 대체).
      파서(예: `email.utils.parsedate_to_datetime` 또는 표준 라이브러리)는 되돌리기
      쉬운 수준으로 선택하고 IMPL에 근거를 남긴다.
    - **슬러그 생성**: `slugify(title)` — 제목을 파일명 안전한 슬러그로 변환한다
      (소문자화·공백/특수문자 치환 등). 제목이 없으면 대체 슬러그(예: 식별자
      기반)를 쓴다.
    - **파일명 충돌 처리**: `article_filename(title, date, *, existing)` 형태로
      `YYYY-MM-DD-<슬러그>.md`를 만들고, 이미 존재하는 이름(`existing` 집합)과
      충돌하면 접미사(`-2`, `-3` …)를 붙인다(PRD 4.4). `existing`은 주입받아
      파일 시스템 무의존으로 테스트한다.
    - **마크다운 렌더링**: `render_article(summary_result)` — `summarize_article`
      반환 dict(요약 텍스트 + 메타 4종: 원제·링크·발행일·피드명)를 개별 글
      마크다운 문자열로 조립한다. 메타를 문서 상단에 배치하고 요약 본문을 잇는다.
      summary 앞뒤 공백·개행은 이 시점에서 정리한다(REVIEW T8 이월 해소,
      `summarize.py:27`이 미후처리 stdout 반환).
    - 반환은 순수 데이터(문자열·파일명)이며, 디렉터리 생성·파일 쓰기·인덱스
      갱신은 T10 범위로 분리한다.
  - touch: `src/rss_wiki/wiki.py`, `tests/test_wiki.py`
  - acceptance:
    - `uv run pytest tests/test_wiki.py` 종료 코드 0으로 통과. 순수 함수 단언으로
      (1) `normalize_date`가 유효 RSS 날짜 문자열을 `YYYY-MM-DD`로 변환하고
      발행일 부재·파싱 실패 시 주입한 `fallback`(수집일)로 대체함,
      (2) `slugify`가 제목을 파일명 안전 슬러그로 변환함(공백·특수문자 처리),
      (3) `article_filename`이 `existing`과 충돌 시 접미사를 붙임,
      (4) `render_article`가 메타 4종(원제·링크·발행일·피드명)을 모두 포함하고
      summary 앞뒤 공백이 정리됨을 검증한다. 파일 시스템·네트워크 미사용.
    - `uv run pytest -x` 전체 통과(회귀 없음).

## 이전 사이클 (M4 LLM 요약: T8 완료)

- [x] **T8. LLM 요약 로직 (summarize.py: claude CLI 서브프로세스 호출 + 한국어 요약)** — 완료
  - 내용:
    - `summarize.py`: 순수 로직 계층. `feeds.py`/`ingest.py`/`extract.py`와
      동일하게 **서브프로세스 실행 함수를 인자로 주입**받아(기본값은
      `claude -p` 호출) 단위 테스트가 프로세스·네트워크 없이 동작하게 설계한다.
    - `summarize_article(article, body, *, feed_name, run=_default_run)` 형태로,
      `ingest`의 article dict(`id`/`title`/`link`/`published`/`description`/
      `content`)와 `extract.extract_body`의 결과 본문(문자열)을 입력받아 한국어
      요약을 생성한다.
      - **프롬프트 구성**: 원문 언어와 무관하게 **한국어**로 요약하도록 지시하고,
        요약문 3~5줄 + 핵심 포인트 불릿 목록을 요청한다(PRD 4.3). 본문 텍스트를
        프롬프트에 포함한다.
      - **claude 호출**: 기본 `run`은 `claude -p <프롬프트>`를 비대화 모드
        서브프로세스로 실행하고 표준 출력(요약 텍스트)을 반환한다. `run`은
        주입 가능하며, 프롬프트 문자열을 인자로 받아 요약 텍스트를 반환하는
        계약으로 정의한다.
      - **메타데이터**: 반환 dict에 요약 텍스트와 함께 원문 제목(원어), 링크,
        발행일, 피드명을 담는다(PRD 4.3). 피드명은 article dict에 없으므로
        `feed_name` 인자로 받는다. (자체 결정: 되돌리기 쉬운 계약 — PLAN M4 근거)
      - **실패 처리**: `claude` 미설치(`FileNotFoundError`)나 비0 종료 시
        정의된 예외(`SummarizeError`)로 감싸 올린다. 미설치는 실행 불가(M6에서
        비0 종료 코드), 요약 실패는 글 단위 건너뜀(M6 리포트)으로 분기할 수
        있게 한다. 이번 태스크는 예외를 명확히 정의·발생시키는 데까지만 하고,
        CLI 종료 코드 배선·건너뜀은 M6 범위다.
    - 반환은 순수 데이터이며 마크다운 조립은 M5 wiki의 책임으로 분리한다.
  - touch: `src/rss_wiki/summarize.py`, `tests/test_summarize.py`
  - acceptance:
    - `uv run pytest tests/test_summarize.py` 종료 코드 0으로 통과. 주입한 가짜
      `run`으로 (1) 정상 호출 시 반환 dict에 요약 텍스트 + 메타 4종(제목·링크·
      발행일·피드명)이 담김, (2) `run`이 프롬프트 문자열을 인자로 받고 그
      프롬프트에 본문 텍스트와 "한국어" 요약 지시가 포함됨, (3) `claude` 미설치
      (`FileNotFoundError`) 시 `SummarizeError` 발생, (4) 비0 종료 시
      `SummarizeError` 발생을 검증한다. 프로세스·네트워크 미사용.
    - `uv run pytest -x` 전체 통과(회귀 없음).

## 이전 사이클 (M3 피드 수집 & 본문 확보: T5·T6·T7 완료)

- [x] **T7. ingest 반환 dict 메타 계약 회귀 테스트 (REVIEW T5 메모 해소)** — 완료 (REVIEW PASS 12/12)
  - 내용:
    - REVIEW T5가 남긴 "반환 dict의 메타 계약이 검증되지 않았다"(비차단) 메모를
      해소한다. `ingest.py`의 로직·계약은 이미 구현되어 동작하므로(수동·간접
      확인됨) **회귀 테스트만** 추가하고 소스는 손대지 않는다.
    - `select_new_articles`가 반환하는 article dict가 `_to_article`
      (`src/rss_wiki/ingest.py:22-30`)의 계약대로 `id`/`title`/`link`/
      `published`/`description`/`content` 키를 담는지 단언한다.
    - 특히 `description`이 없을 때 `summary`로 대체되는 fallback
      (`ingest.py:28`)과 `content` 매핑(`ingest.py:29`)을 각각 별도 케이스로
      고정해, 해당 매핑을 제거하면 테스트가 실패하도록 구성한다(통과-위장 방지).
  - touch: `tests/test_ingest.py`
  - acceptance:
    - `uv run pytest tests/test_ingest.py` 종료 코드 0으로 통과. 신규 케이스로
      (1) 반환 article이 6개 메타 키를 모두 담음, (2) `description` 부재 시
      `summary`로 대체됨, (3) `content` 필드가 항목의 `content`로 매핑됨을
      단언한다. 네트워크 미사용.
    - `uv run pytest -x` 전체 통과(회귀 없음).

- [x] **T5. 피드 수집 로직 (ingest.py: 새 글 판별 + --limit + state 스킵)** — 완료
  - 내용:
    - `ingest.py`: 순수 로직 계층. `feeds.py`와 동일하게 **파서 함수를
      인자로 주입**받아(기본값은 `feedparser.parse`) 단위 테스트가 네트워크
      없이 동작하게 설계한다.
    - `select_new_articles(feed, state, *, limit, parse=...)` 형태로,
      단일 피드에 대해 처리 대상 새 글 목록을 반환한다.
      - **글 식별자**: 항목의 GUID(`id`/`guid`)가 있으면 그것을, 없으면
        링크 URL을 식별자로 채택(PRD 5절). `state["processed"]`의 키와 대조해
        이미 처리한 글은 제외한다.
      - **첫 수집 판정**: 해당 피드의 어떤 항목도 `state["processed"]`에
        없으면 첫 수집으로 보고 최신 `limit`개까지만 반환한다. 첫 수집이
        아니면(이미 처리 이력이 있으면) 미처리 신규 글을 전부 반환한다.
        (자체 결정: 되돌리기 쉬운 판정 규칙 — PLAN M3에 근거 기록)
      - 반환 항목에는 요약·위키 단계가 소비할 최소 메타(제목, 링크, 발행일,
        식별자, description/content 원본)를 담아 후속 모듈에 넘긴다.
    - 파싱 실패(feedparser bozo 등) 시 피드 단위로 예외를 올려 CLI/리포트
      계층이 "건너뛰고 계속"으로 처리할 수 있게 한다. 실제 건너뜀·리포트는
      M6 범위이므로 이번 태스크는 예외를 명확히 정의·발생시키는 데까지만 한다.
  - touch: `src/rss_wiki/ingest.py`, `tests/test_ingest.py`
  - acceptance:
    - `uv run pytest tests/test_ingest.py` 종료 코드 0으로 통과. 주입한 가짜
      parse로 (1) 빈 state에서 첫 수집 시 `limit` 상한 적용(최신순),
      (2) 이미 처리한 식별자(GUID·URL 각각) 스킵, (3) GUID 없을 때 링크 URL을
      식별자로 채택, (4) 첫 수집이 아닐 때 미처리 신규 글 전부 반환을 검증한다.
      네트워크 미사용.
    - `uv run pytest -x` 전체 통과(회귀 없음).

- [x] **T6. 본문 확보 로직 (extract.py: HTML fetch + trafilatura + RSS 대체)** — 완료
  - 내용:
    - `extract.py`: 순수 로직 계층. **HTTP fetch 함수와 본문 추출 함수를
      인자로 주입**받아(기본값은 `httpx` GET + `trafilatura.extract`) 단위
      테스트가 네트워크 없이 동작하게 설계한다.
    - `extract_body(article, *, fetch=..., extract=...)` 형태로, 원문 링크의
      HTML을 가져와 본문을 추출한 결과를 반환한다.
      - **대체 순서(PRD 4.2)**: (1) 원문 fetch + 본문 추출 성공 시 그 본문 사용,
        (2) fetch 실패 또는 추출 결과가 비면 RSS 항목의 description/content로
        대체, (3) RSS 본문도 없으면 글 단위 실패로 예외를 올린다(M6에서
        건너뜀 처리).
      - 반환값에 본문 텍스트와 **출처 구분**(원문 추출 / RSS 대체)을 포함해
        이후 요약·리포트가 활용할 수 있게 한다.
      - HTTP fetch의 타임아웃·상태 코드 실패는 fetch 함수 내부에서 예외로
        표현하고, `extract_body`는 이를 잡아 RSS 대체 경로로 전환한다.
        타임아웃 기본값 등 네트워크 정책을 IMPL에 근거로 남긴다(REVIEW T3
        메모 반영). (자체 결정: 되돌리기 쉬운 네트워크 처리 수준)
    - **REVIEW T7 이월 반영**: `add`의 기본 검증(`feedparser.parse(url)`)이
      실 네트워크에 의존하고 아직 실측되지 않았다(REVIEW T3·T7 이월). T6의
      HTTP fetch 실패·타임아웃 처리 정책을 확정하면서, 동일한 주입형 설계로
      네트워크 무의존 테스트가 가능함을 근거로 남기고 fetch 실패 경로를 실측한다.
  - touch: `src/rss_wiki/extract.py`, `tests/test_extract.py`
  - acceptance:
    - `uv run pytest tests/test_extract.py` 종료 코드 0으로 통과. 주입한 가짜
      fetch/extract로 (1) 정상 fetch+추출 성공 시 원문 본문·출처=원문,
      (2) fetch 실패 시 RSS description으로 대체·출처=RSS, (3) 추출 결과가
      빈 문자열이면 RSS 본문으로 대체, (4) RSS 본문도 없으면 정의된 예외
      발생을 검증한다. 네트워크 미사용.
    - `uv run pytest -x` 전체 통과(회귀 없음).

## 이전 사이클 (M2 피드 관리: T3·T4 완료)

- [x] **T4. 저장 계층 실패 경로 테스트 보강 (REVIEW T2 메모 해소)** — 완료
  - 내용:
    - REVIEW T2가 남긴 "실패-정리 경로·손상 JSON 로드 미검증" 메모를 해소한다.
      코드는 이미 구현되어 동작하므로(수동 확인됨), **회귀 테스트만** 추가하고
      필요 최소한의 정책 코드만 손댄다.
    - `_atomic_write` 실패 시 원본 보존: `save_feeds`/`save_state`에 직렬화
      불가 값(예: `set`)을 전달해 쓰기 도중 예외가 발생해도 (1) 대상
      디렉터리에 잔존 임시 파일이 없고 (2) 기존 파일 내용이 그대로
      유지됨을 검증하는 테스트를 추가한다.
    - 손상된 JSON 로드 정책 확정: 파일은 존재하되 내용이 깨진 경우
      (`store.py:25,36`의 `json.load` 예외 전파) 처리 정책을 정한다.
      기본 채택값 — `load_feeds`/`load_state`는 원인을 알 수 있는
      명확한 예외로 감싸 올린다(예: `StoreError` 또는 파일 경로를 포함한
      메시지). CLI 계층에서 이 예외를 사용자 대면 오류로 변환하는 것은
      T3에서 다룬다. (자체 결정: 되돌리기 쉬운 오류 처리 수준)
  - touch: `src/rss_wiki/store.py`, `tests/test_store.py`
  - acceptance:
    - `uv run pytest tests/test_store.py` 종료 코드 0으로 통과. 신규 테스트로
      (1) 쓰기 실패 시 임시 파일 잔존 없음 + 원본 보존, (2) 손상된 JSON
      파일 로드 시 정의된 예외 발생을 검증한다.

- [x] **T3. 피드 관리 (feeds.py + CLI add/remove/list 연결)** — 완료
  - 내용:
    - `feeds.py`: 순수 로직 계층. `add_feed`, `remove_feed`, `list_feeds`
      함수를 구현한다.
      - 스키마 확정: feeds 항목은 `{name, url, added_at}`(PLAN 스키마 초안).
      - `add_feed`: 유효성 검증(feedparser 파싱 성공 + 항목 존재)을 통과한
        경우에만 등록. **검증 함수를 인자로 주입**받는 형태로 설계하여
        (기본값은 feedparser 호출) 단위 테스트가 네트워크 없이 동작하게 한다.
        `name`은 검증 결과의 피드 제목에서 도출하고, 제목이 없으면 URL로 대체.
        `added_at`은 호출 시각(주입 가능하게 하거나 `store` 저장 시점 기록).
      - 중복 등록 방지: 동일 URL이 이미 있으면 등록하지 않고 그 사실을 알린다.
      - `remove_feed`: URL 또는 name으로 매칭하여 삭제. 매칭 없으면 그 사실을 알린다.
      - `list_feeds`: 등록된 피드 목록을 반환.
    - `cli.py`: `add`/`remove`/`list` 커맨드가 `feeds.py`를 호출하도록 연결.
      유효성 검증 실패·중복·미존재·손상된 feeds.json 등을 명확한 메시지와
      적절한 종료 코드로 사용자에게 보여 준다.
      **REVIEW T4 메모 반영**: `load_feeds`가 올리는 `store.StoreError`
      (`store.py:32`)를 CLI에서 포착해 사용자 대면 메시지와 0이 아닌 종료
      코드(`typer.Exit(code=1)` 등)로 변환한다. T4가 정한 예외 타입을
      그대로 소비할 것.
      `fetch`는 이번 태스크 범위 밖(스텁 유지).
  - touch: `src/rss_wiki/feeds.py`, `src/rss_wiki/cli.py`,
    `tests/test_feeds.py`
  - acceptance:
    - `uv run pytest tests/test_feeds.py` 종료 코드 0으로 통과: 주입한 가짜
      검증 함수로 정상 등록, 항목 없는 피드 거부, 중복 URL 거부,
      URL/name 삭제, 목록 반환을 검증(네트워크 미사용).
    - `uv run rss-wiki list` 종료 코드 0(피드 없을 때 빈 목록 안내).
    - 손상된 `feeds.json`에서 `list`/`add`/`remove` 실행 시 `StoreError`가
      트레이스백으로 새지 않고 사용자 대면 메시지 + 0이 아닌 종료 코드로
      변환됨(테스트 또는 수동 확인). REVIEW T4 메모 해소.
    - `uv run rss-wiki --help` 종료 코드 0, 4개 서브커맨드 정상 표시(회귀 없음).

- [x] **T1. 프로젝트 스캐폴딩 & CLI 뼈대** — 완료 (REVIEW PASS 9/12)
  - 내용:
    - uv 기반 Python 3.12+ 프로젝트 구성. `pyproject.toml`에 의존성
      (typer, feedparser, trafilatura, requests 또는 httpx) 선언.
    - 콘솔 스크립트 `rss-wiki` → `rss_wiki.cli:app` 진입점 등록.
    - Typer 앱과 서브커맨드 스텁 4개(add/remove/list/fetch) 정의. 각 커맨드는
      아직 실제 로직 없이 "미구현" 안내 또는 빈 동작이어도 되며, 인자 시그니처는
      PRD 3절 표와 일치해야 한다(`add <URL>`, `remove <URL 또는 이름>`,
      `list`, `fetch [--limit N]`).
  - touch: `pyproject.toml`, `src/rss_wiki/__init__.py`, `src/rss_wiki/cli.py`
  - acceptance:
    - `uv run rss-wiki --help` 종료 코드 0, 4개 서브커맨드가 목록에 표시.
    - `uv run rss-wiki add --help`, `... fetch --help` 종료 코드 0.

- [x] **T2. 저장 계층 (config + store)** — 완료
  - 내용:
    - **pytest 환경 선행 구성 (REVIEW T1 메모 반영)**: 현재 `tests/`
      디렉터리와 pytest 설정이 없음. `pyproject.toml`에 dev 의존성으로
      `pytest`를 추가하고(`[dependency-groups]` 또는 `[project.optional-dependencies]`
      중 uv 관례에 맞는 방식), `tests/` 디렉터리를 생성하여
      `uv run pytest`가 동작하는 환경을 먼저 갖춘다.
    - `config.py`: 프로젝트 기준 경로 상수 정의(`feeds.json`, `state.json`,
      `wiki/` 위치). 초기값은 프로젝트 내 고정(PLAN 미해결 의사결정 채택값).
    - `store.py`: feeds.json / state.json 로드·저장 함수. 파일이 없으면 빈
      기본 구조를 반환하고, 저장 시 원자적 쓰기(임시 파일 후 교체)로 손상 방지.
      테스트에서 경로를 주입할 수 있도록 로드·저장 함수는 대상 경로를
      인자로 받도록 설계한다(config 상수는 기본값으로만 사용).
    - 스키마 초안: feeds = 리스트[{name, url, added_at}],
      state = {processed: {글식별자: {processed_at, status}}, failures: [...]}.
  - touch: `pyproject.toml`(pytest dev 의존성 추가), `src/rss_wiki/config.py`,
    `src/rss_wiki/store.py`, `tests/__init__.py`, `tests/test_store.py`
  - acceptance:
    - `uv run pytest tests/test_store.py` 종료 코드 0으로 통과: 빈 상태
      로드→저장→재로드 왕복(feeds·state 각각), 존재하지 않는 파일에서
      기본 구조 반환, 원자적 쓰기 후 재로드 무결성을 검증.
  - 참고(REVIEW T1 메모): 사용자 대면 명령은 `rss-wiki`, 배포 이름은
    `rss-wiki-ch9`로 이원화되어 있음. touch 밖 변경이 불가피하면 IMPL에
    근거를 남기는 T1 관행을 유지할 것.

## 백로그 (후속 마일스톤)

- [x] M2. 피드 관리 (add/remove/list) — 유효성 검증, feeds.json CRUD (T3·T4 완료)
- [x] M3. 피드 수집 & 본문 확보 — feedparser 파싱, state 스킵, --limit, trafilatura 추출 (T5·T6·T7 완료)
- [x] M4. LLM 요약 — claude CLI 서브프로세스, 한국어 요약, claude 미설치 처리 (T8 완료)
- [x] M5. 위키 생성 — 글 md, index/feeds/daily 갱신, 슬러그 충돌 처리 (T9·T10·T11 완료)
- [x] M6. 실패 정책 & 리포트 + `fetch` 파이프라인 배선 — 건너뛰고 계속, 말미 리포트, 종료 코드 정책, CliRunner 회귀 (T12 순수 오케스트레이션 **완료** / T13 CLI 배선·누적 인덱스·claude 프리플라이트·종료 코드·CliRunner **완료** / T14 종료 코드 경계 정합 **완료** / T15 경계 회귀 완결 **완료**)

### PRD 확장 반영 (병렬 요약 + 웹 UI)

- [~] M7. 병렬 LLM 요약 (PRD 4.3·8) — asyncio·세마포어·`--concurrency` (T16 async 요약 함수 **완료** / T17 순수 병렬 오케스트레이션 **완료** / T18 CLI `--concurrency` 배선·async 구동)
- [x] M8. 웹 서버 스캐폴딩 & 디자인 시스템 기반 (PRD 3.1·3.3·8) — `serve` 명령, FastAPI, Jinja2, 디자인 토큰·다크 모드·반응형 골격 (T19·T20 완료)
- [x] M9. 글 열람 (PRD 3.2·3.3) — 마크다운 렌더링, 전체/피드별/날짜별 목록, 개별 글 페이지, 읽기 최적화 타이포그래피, 상태 표현 (T21·T22 완료, REVIEW T22 PASS 15/15. 후속 원문 링크 실화면 갭: T23 순방향 교정 완료 → T25 저장 콘텐츠 렌더 시점 해소)
- [x] M10. 피드 관리 웹 UI (PRD 3.2) — 목록·등록(유효성 검증)·삭제, feeds.json 공유 (선행 T23·T25 + 본체 T24 완료, REVIEW T24 PASS 15/15)
- [x] M11. 수집 실행 웹 UI (PRD 3.2) — fetch 트리거, 진행 상황 실시간(폴링), 중복 실행 차단, 성공/실패 리포트 (T26 순수 상태·락 → T27 배선·구동·폴링 → T28 진행 UI·완료 리포트, REVIEW T28 PASS 14/15, `uv run pytest -x` 139 passed)
- [~] M12. 디자인 품질 마감 (PRD 3.3) — 인터랙션 완성도, 반응형, WCAG AA 접근성 (T29 인터랙션 마감·폼 파싱 견고화 **선정** → T30 접근성·반응형 통합 점검 마감)
