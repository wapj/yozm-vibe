# IMPL: T30 — 접근성·반응형 통합 점검 마감 (M12 2단계·M12 마감)

## 처리한 항목

**T30. 접근성·반응형 통합 점검 마감 (WCAG AA 대비·키보드 포커스·승계 관찰)**

이 항목으로 M12(디자인 품질 마감, PRD 3.3)가 마감되며 잔여 마일스톤이 없어진다.

## 변경 파일

- 코드 변경 없음. 정적 측정·통합 점검 결과 토큰 조정이나 CSS 보강이 필요한
  갭이 발견되지 않아, `styles.css`·`app.py`·`fetch.js`·코어 모듈(`feeds.py`·
  `store.py`·`wiki.py`·`pipeline.py`) 모두 미변경이다. 이번 사이클 산출물은
  본 문서(측정·점검 결과 기록)와 TASKS.md 체크뿐이다.

## (1) WCAG AA 대비 정적 측정

`styles.css`에 정의된 라이트(`:root`)·다크(`prefers-color-scheme: dark` 및
`[data-theme="dark"]`) 토큰 값으로 실제 사용되는 텍스트/배경 조합의 대비비를
WCAG 2.1 상대 휘도 공식으로 직접 계산했다(본문 4.5:1, 큰 텍스트 3:1 요구,
모두 더 엄격한 4.5:1 기준으로 판정). 대상은 코드베이스에서 실제 소비되는
색상 조합만 선정했다(`--color-success`/`--color-warning` 토큰은 정의만 되어
있고 텍스트 색으로 소비하는 규칙이 없어 측정 대상에서 제외 — `grep`으로
사용처 부재 확인).

**라이트 테마**

| 조합 | 전경/배경 | 대비비 | 판정 |
|---|---|---|---|
| 본문 텍스트 (`--color-fg` on `--color-bg`) | `#1a1a1e` / `#ffffff` | 17.35:1 | PASS |
| 부가 텍스트·헤더 내비 (`--color-fg-muted` on `--color-bg`) | `#52525b` / `#ffffff` | 7.73:1 | PASS |
| 버튼 기본 (`--color-fg` on `--color-bg-subtle`) | `#1a1a1e` / `#f5f5f7` | 15.93:1 | PASS |
| 버튼 primary (`--color-accent-fg` on `--color-accent`) | `#ffffff` / `#1d4ed8` | 6.70:1 | PASS |
| 링크 (`--color-accent` on `--color-bg`) | `#1d4ed8` / `#ffffff` | 6.70:1 | PASS |
| 오류 메시지·`state-error`·`button-danger` (`--color-error` on `--color-bg`) | `#b91c1c` / `#ffffff` | 6.47:1 | PASS |
| `button-danger:hover` (`--color-accent-fg` on `--color-error`) | `#ffffff` / `#b91c1c` | 6.47:1 | PASS |
| 피드 상태 배지 `fetch-feed-status--running` (`--color-accent` on `--color-bg-subtle`) | `#1d4ed8` / `#f5f5f7` | 6.15:1 | PASS |
| `fetch-report__failures` (`--color-error` on `--color-bg-subtle`) | `#b91c1c` / `#f5f5f7` | 5.94:1 | PASS |

**다크 테마**

| 조합 | 전경/배경 | 대비비 | 판정 |
|---|---|---|---|
| 본문 텍스트 | `#e4e4e7` / `#121214` | 14.75:1 | PASS |
| 부가 텍스트·헤더 내비 | `#a1a1aa` / `#121214` | 7.30:1 | PASS |
| 버튼 기본 | `#e4e4e7` / `#1e1e21` | 13.11:1 | PASS |
| 버튼 primary | `#0b1220` / `#60a5fa` | 7.36:1 | PASS |
| 링크 | `#60a5fa` / `#121214` | 7.36:1 | PASS |
| 오류 메시지·`state-error`·`button-danger` | `#f87171` / `#121214` | 6.76:1 | PASS |
| `button-danger:hover` | `#0b1220` / `#f87171` | 6.77:1 | PASS |
| 피드 상태 배지 running | `#60a5fa` / `#1e1e21` | 6.54:1 | PASS |
| `fetch-report__failures` | `#f87171` / `#1e1e21` | 6.01:1 | PASS |

**결론**: 라이트·다크 모든 주요 조합이 AA 기준(4.5:1)을 최소 5.9배 이상의
여유로 충족한다. 미달 조합이 없어 디자인 토큰 조정은 불필요했다.

## (2) 640px 반응형 무결 점검

`styles.css:254`(전역: 헤더·`.page` 패딩)와 `:421`(피드 관리 폼·목록)의
미디어쿼리, 그리고 화면이 있는 전 템플릿(`base.html`·`index.html`·
`feed.html`·`daily.html`·`article.html`·`feeds_admin.html`·`fetch.html`·
`_article_list.html`)의 레이아웃을 정적으로 점검했다.

- 헤더(`site-header`): `flex-wrap: wrap`으로 640px 이하에서 제목·내비·테마
  토글이 필요 시 다음 줄로 넘어가며, 각 요소가 고정 폭을 갖지 않아 겹침
  없음.
- 글 목록(`_article_list.html`이 재사용되는 index/feed/daily 3개 화면):
  `.article-list`가 `display: flex; flex-direction: column`이라 폭에
  무관하게 세로 배치이며 넘침 없음.
- 개별 글 본문(`article.html`): `.prose`의 `max-width: 70ch`는 상한값이라
  뷰포트가 좁아지면 그에 맞춰 줄어들며 고정 폭 넘침이 없음.
- 피드 관리(`feeds_admin.html`): `.feed-form`이 640px 이하에서
  `flex-direction: column`으로 전환되고 `input[type="url"]`의
  `min-width: 20rem`이 `0`으로 재정의되어 좁은 화면에서 입력창이 넘치지
  않음. `.feed-list__item`도 같은 breakpoint에서 세로 배치로 전환.
- 수집 실행(`fetch.html`/`fetch.js` 렌더 결과): `.fetch-feed-list__item`이
  `justify-content: space-between`이나 고정 폭이 없어 좁은 화면에서도
  줄바꿈 없이 배치 유지(피드명이 매우 길 경우 줄바꿈은 발생할 수 있으나
  겹침·잘림은 없음).
- 사이트 내비(`.site-nav ul`, index.html 하단 피드별/날짜별 링크 목록):
  `flex-wrap: wrap`이 이미 적용되어 항목 수가 많아도 겹침 없이 줄바꿈.

**결론**: 점검한 모든 화면에서 640px 이하 겹침·넘침이 발견되지 않아 CSS
보강이 필요하지 않았다.

## (3) 키보드 포커스 재점검

T29에서 이미 `:focus-visible`(`styles.css:112`)이 특정 클래스에 스코프되지
않은 전역 규칙임을 확인했다. 이번 사이클에서 전 템플릿의 인터랙티브 요소
(헤더 내비 링크·`.button`류 전부·`.article-list__title`·`.theme-toggle`·
`input[type="url"]`)를 다시 순회해 전역 규칙 상속 여부를 재확인했고, 누락
요소를 발견하지 못했다(T29 결과와 동일, 회귀 없음 확인 목적의 재점검).

## (4) `fetch.js` 렌더 분기 자동 검증 도입 판정 — **수동 후속으로 승계(도입하지 않음)**

REVIEW T28·T29가 남긴 판정 요청 대상은 `fetch.js`의 `renderIdle`/
`renderRunning`/`renderDone`/`renderError` 상태 전환, 버튼 `disabled` 토글,
`report.failures` 목록화, 상태 전환 후 `role` 속성 부재, 폴링 거부 시 재시도
(`.catch()`)다.

**판정: 도입하지 않는다.** 근거:

- 이 프로젝트는 Python/`uv` 단일 툴체인이며(`pyproject.toml`), JS 전용
  테스트 러너·DOM 환경(jsdom 등)이나 `package.json` 자체가 존재하지 않는다.
  `fetch.js`의 렌더 분기를 자동 검증하려면 (a) Node.js 기반 JS 테스트
  스택(jest/vitest + jsdom)을 신규 도입하거나 (b) 헤드리스 브라우저
  (Playwright 등)를 신규 의존성으로 도입해야 한다. 둘 다 PRD 8이 명시한
  스택(Python/uv/Typer/FastAPI/Jinja2 + "경량 JavaScript")의 범위를 넘어서는
  새 런타임·패키지 관리 체계를 프로젝트에 추가하는 것이라, 대상이 약 150줄
  단일 정적 자원 파일 하나임을 고려하면 비용 대비 효용이 낮다.
  - 대안으로 Python에서 `fetch.js`를 문자열로 파싱해 정규식으로 특정 패턴
    (`removeAttribute("role")` 존재 등) 존재를 확인하는 방식도 검토했으나,
    이는 실제 렌더 동작을 검증하지 못하는 문자열 포함 단언에 불과해(코드
    삭제·리팩터링 시에도 우연히 패턴 문자열이 남으면 통과) 실질적인 회귀
    방지 효과가 낮다고 판단해 채택하지 않았다.
- 이 네 가지 렌더 분기는 이미 소스 리딩으로 로직이 단순함이 확인된다
  (`fetch.js:15-104`): 상태값에 따른 단순 분기이며 서버 쪽 계약
  (`GET /fetch/progress` 스냅샷 형태)은 `tests/test_web_app.py`·
  `tests/test_progress.py`가 이미 충실히 회귀로 고정하고 있어, 클라이언트
  렌더 로직이 잘못된 스냅샷을 받을 위험은 낮다.
- **수동 후속 확인 방법(승계)**: 브라우저에서 `rss-wiki serve` 실행 후
  (a) 수집 트리거 클릭 시 버튼이 비활성화되고 진행 패널이 표시되는지,
  (b) 완료 후 성공/실패 리포트가 표시되고 버튼이 다시 활성화되는지,
  (c) 오류 상태 진입 후 다른 상태로 전환 시 `role="alert"`가 개발자 도구
  DOM 검사에서 사라지는지, (d) 네트워크 탭에서 폴링 요청을 일시 차단했다가
  복구했을 때 폴링이 재개되는지를 육안으로 1회 확인할 것을 권장한다.

## (5) 수동 후속 승계 항목 (비차단, 최종 확정)

M12 전체에 걸쳐 이월되어 온 다음 항목들은 블로킹 서버·라이브 외부 서비스
의존이라는 동일한 구조적 이유로 자동 acceptance 고정이 어려워, M12 마감
시점에도 수동 후속으로 유지한다(신규로 발생한 항목 없음, 기존 승계의
재확인):

- M8~M11 각 화면의 브라우저 종단 육안 확인(다크 모드 토글 실동작, 반응형
  레이아웃, 폼 리다이렉트, 폴링 실시간 갱신).
- 실환경 `claude` CLI 종단 `fetch --limit 1 --concurrency 2` 실호출 회귀
  기준선 확보(동기·async 경로 공통, M7부터 승계).
- `fetch.js` 렌더 분기 브라우저 육안 확인((4)에서 구체 방법 명시).

## 검증 결과

- `uv run pytest -x`: **141 passed**(기존과 동일, 회귀 없음 — 코드 변경이
  없으므로 테스트 결과도 불변).
- `uv run rss-wiki --help`: 종료 코드 0, 서브커맨드 5개(add/remove/list/
  fetch/serve) 정상 표시.
- WCAG AA 대비비는 위 (1)의 계산을 독립 스크립트(WCAG 2.1 상대 휘도 공식,
  `srgb_to_linear`→`luminance`→`(L1+0.05)/(L2+0.05)`)로 직접 실행해 얻은
  수치이며, 모든 조합이 4.5:1 이상이다.

## 결론: M12 마감

PRD 3.3(디자인 품질 요구사항)의 일관된 디자인 시스템(M8 토큰)·읽기 경험
(M9 `.prose`)·다크 모드(M8)·반응형 레이아웃((2))·상태 표현(M8 `.state-*`,
전 화면 소비)·인터랙션 완성도(M8~M11 hover/active/포커스, T29 정리) 요구가
모두 충족되었고, 이번 사이클의 정적 측정·점검에서 추가 조정이 필요한 갭이
발견되지 않았다. M12(디자인 품질 마감)가 마감되며, PLAN.md의 전체 마일스톤
(M1~M12)이 완료된다. 잔여 항목은 위 (5)에 기록한 수동 후속(비차단)뿐이다.
