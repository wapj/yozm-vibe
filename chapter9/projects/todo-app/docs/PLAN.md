# PLAN — Todo + Pomodoro Web App

PRD를 기준으로 구현을 6개 마일스톤으로 분해한다. 각 마일스톤은 독립적으로 동작 가능한 상태에서 끝나는 것을 목표로 한다.

## 마일스톤

### M1. 프로젝트 스켈레톤
- `backend/` (FastAPI + SQLAlchemy + SQLite) 초기화. `/health` 엔드포인트 동작.
- `frontend/` (Vite + React + TS) 초기화. 빈 페이지에서 백엔드 `/health` 호출 성공.
- pytest, vitest 최소 1개 통과.
- 결과물: 두 프로세스 띄우면 빈 페이지가 뜨고 `/health` ok가 표시됨.
- 부수 정비(M1-2 REVIEW 후속):
  - `frontend/eslint.config.js` (ESLint v9 flat config)와 필요한 의존성(`@eslint/js`, `@typescript-eslint/eslint-plugin`, parser)을 추가하여 `npm run lint`가 동작하게 한다.
  - 프론트엔드 테스트에서 fetch 실패 경로(에러 메시지 렌더링) 케이스를 1개 추가한다.

### M2. 할일(Task) 도메인 + CRUD API + 기본 UI — **마감(전 단계 PASS)**
- DB 스키마: `tasks`, `tags`, `task_tags` (소프트 삭제 컬럼 포함). — **M2-1 PASS**.
- 백엔드 API: `GET/POST /tasks`, `PATCH /tasks/{id}`, `DELETE /tasks/{id}`(soft delete), 태그 자동 생성/연결. — **M2-2a/b1/b2 모두 PASS**.
- 프론트 UI: 할일 목록 + 추가/편집/삭제, 태그 입력, 우선순위/상태 토글, "완료된 항목 보기" 토글. — **M2-3a/b/c1/c2 모두 PASS(22/22 vitest)**.
- 누적 뽀모도로 횟수는 일단 0 고정(M4에서 연결).
- 부수 정비(M2-2b2 REVIEW 후속, **M3-1에 흡수**):
  - `done→done` 동일 상태 PATCH 시 `completed_at` 불변을 직접 검증하는 테스트 1건 추가.
  - `tests/test_tasks_api.py`의 `__import__("sqlalchemy", fromlist=["select"]).select(...)` 인라인 호출을 파일 상단 `from sqlalchemy import select` import로 정리.

### M3. 검색 및 필터 — **마감(전 단계 PASS)**
- 백엔드(M3-1): `GET /tasks` 쿼리 파라미터로 키워드(`q`: 제목+메모 부분일치), 태그(`tags`: 다중 값 AND 조건), 날짜 프리셋(`date_preset`: `today`/`this_week`/`all`), 상태(`status`: `active`/`done`) 필터. — **M3-1 PASS(38/38)**.
  - 날짜 프리셋 **기준일은 `created_at`** 으로 시작. PRD 5절은 "마지막 활동(뽀모도로) 시각이 자연스러움"이라 표현했으나 `pomodoro_sessions`는 M4-1에서 도입되므로, 그 시점에 기준을 last pomodoro 시각으로 전환한다(M4 절 참조). 단순/단계적 도입 원칙.
  - 모든 파라미터는 Optional. 미지정 시 기존 동작(soft-delete 제외 + `updated_at DESC`) 유지하여 기존 프론트와 호환.
- 프론트(M3-2): 검색바 + 태그 다중 선택 + 날짜 프리셋 토글 + 상태 토글. 클라이언트 사이드 "완료된 항목 보기"(M2-3c1)를 `status` 백엔드 필터로 통합.
  - **M3-2a** — **PASS(12/12, 30 passed)**. `TaskFilters` 타입과 `listTasks(filters?)` URL 빌더가 `q/tags/date_preset/status` 4종 모두 지원하도록 선반영됨. App.tsx의 `visibleTasks` 클라이언트 필터링이 제거되고, "완료된 항목 보기" 토글이 `status` 쿼리 파라미터 토글로 통합됨.
  - **M3-2b** — **PASS(11/12, 36 passed)**. `frontend/src/features/tasks/TaskFilters.tsx` 신규 컴포넌트(controlled, q/tags/date_preset 3종) 추가, App.tsx에 마운트. 운영고려 -1점은 태그 입력 controlled value `tags.join(", ")`의 trailing comma+space 점프 현상(기능 정확도 영향 없음, UX 후속 권고). 백로그의 "태그 입력 UX 후속" 항목으로 분리하여 M4 이후 UX 개선 사이클에서 처리.

### M4. 뽀모도로 타이머 코어 — **마감(전 단계 PASS, M4-4c PASS)**
- DB 스키마: `pomodoro_sessions` (task_id, phase, started_at, planned_duration_sec, ended_at, end_reason). — **M4-1 PASS**.
- 백엔드 API: 세션 시작/종료/폐기, 현재 활성 세션 조회(상태 복원용). — **M4-2a/b/c 모두 PASS**.
- 프론트: 할일 클릭 → 25분 카운트다운, 진행률, 단일 세션 보장(전환 시 다이얼로그), 새로고침 후 복원. — **M4-3a/b/c/d 모두 PASS**.
- 단계 자동 전환(집중→짧은 휴식→집중, 4세션마다 긴 휴식). 휴식 후 다음 집중은 "묻기"가 기본. — **M4-4에서 분할 진행**.
- M3-1 후속: `GET /tasks`의 `date_preset` 기준일을 `created_at`에서 last pomodoro 시각으로 전환(서브쿼리 또는 left join). 변경 시점은 M4-2c(세션 API 등록 직후)가 자연스러움. — **M4-2c에서 흡수 완료**.
- 한 세션 단위로 분할:
  - **M4-1** — **PASS(12/12, 42 passed)**. DB 스키마/모델만 추가. `pomodoro_sessions` 테이블(`id`, `task_id` FK→`tasks.id`, `phase`, `started_at`, `planned_duration_sec`, `ended_at` nullable, `end_reason` nullable) + `PomodoroSession` 모델 + `Task ↔ PomodoroSession` 양방향 relationship + 모델 테스트 4건. Task soft-delete 시 sessions는 보존(통계용) — `ondelete` 미지정.
  - **M4-2a** — **PASS(12/12, 51 passed)**. 백엔드 세션 시작 + 활성 세션 조회 API. `POST /pomodoros`(body: task_id/phase/planned_duration_sec, 검증: Task 존재 & soft-delete 아님, **전역 단일 활성 세션** 보장 — 다른 활성 세션이 있으면 409, detail에 충돌 세션 id 포함) + `GET /pomodoros/active`(전역 활성 세션 1건 또는 404). Pydantic 스키마 `PomodoroSessionCreate`/`PomodoroSessionRead` 신설, phase Literal로 422 검증, `planned_duration_sec gt=0`. main.py에 include_router 등록 완료.
  - **M4-2b** — **PASS(12/12, 61 passed)**. 세션 종료/폐기 API. `POST /pomodoros/{id}/end`(no body, end_reason=`completed`로 고정) + `POST /pomodoros/{id}/discard`(body Literal `abandoned`/`discarded`). 404/409 가드, `ended_at` 채움으로 M4-2a 전역 활성 검사 자연 해제 검증 완료.
  - **M4-2c** — **PASS(12/12, 65 passed)**. `GET /tasks` `date_preset` 기준일을 `created_at` → 마지막 활동(last pomodoro `started_at`) 시각으로 전환. `pomodoro_sessions` 상관 서브쿼리로 `MAX(started_at)` 산출 + `COALESCE(..., tasks.created_at)`로 세션 없는 Task는 `created_at` 폴백. 정렬은 기존 `updated_at DESC` 유지. 신규 테스트 4건 통과.
  - **M4-3** — 프론트 타이머. 한 세션 분량 유지를 위해 a/b/c/d로 분할.
    - **M4-3a** — **PASS(12/12, 43 passed)**. 프론트 Pomodoro API 클라이언트 + 마운트 시 활성 세션 조회 + 상단 배너 단순 표시. `frontend/src/api/pomodoros.ts` 신규(`PomodoroSession` 타입 + `startPomodoro`/`getActivePomodoro`/`endPomodoro`/`discardPomodoro` 함수, 404는 `null` 반환). App.tsx 마운트 시 `getActivePomodoro()` 호출 → 결과를 상태로 보관하여 `<ActivePomodoroBanner>` 단순 텍스트 렌더. 카운트다운/진행률 UI, 카드 클릭 시작, 다이얼로그는 M4-3b 이후로 이월.
    - **M4-3b** — **PASS(11/12, 49 passed)**. 카드의 "시작" 버튼 클릭 → `startPomodoro({task_id, phase:"focus", planned_duration_sec:1500})` 호출 → 결과를 `setActivePomodoro`로 반영. `PomodoroTimer` 컴포넌트(MM:SS 카운트다운 + `<progress>` 진행률) 신규, `useTimer` 훅(1초 tick `setInterval`) 신규. `ActivePomodoroBanner`는 기존 텍스트(`활성 세션 #{id} task=… phase=…`)를 유지한 채 `<PomodoroTimer>`를 추가 마운트하여 기존 어서션 회귀 방지. 시작 트리거는 카드 전체 클릭 대신 "시작" 버튼(`task-start-{id}`)으로 구현. 집중 길이 25분=1500초 하드코딩(설정 화면 M5에서 동적화). 409(전역 활성 세션 충돌) 응답은 본 사이클에서 단순 `throw`로 `setError` 표시까지만 처리됨 — 다이얼로그 분기는 M4-3c. 만료(remaining=0) 시 "00:00"만 표시 — 자동 만료 처리는 M4-3d. **REVIEW 후속**: `App.test.tsx:240-258` "검색바 입력" 테스트 fetchMock이 `/api/pomodoros/active`에도 적용되어 `<progress value={NaN}>` 경고 발생 — M4-3c에서 URL 분기로 수정.
    - **M4-3c** — **PASS(11/12, 54 passed)**. 단일 세션 보장 다이얼로그 완성. `frontend/src/api/pomodoros.ts`에 `PomodoroConflictError extends Error` 신설, `startPomodoro`가 409 응답 시 throw하여 App.tsx catch에서 `instanceof` 분기. `frontend/src/features/pomodoro/PomodoroConflictDialog.tsx`(`<div role="dialog" aria-modal="true">` 루트, conflict 세션 요약 1줄, 완료/폐기/취소 버튼 3개) 신규. App.tsx 상태 2개(`conflictSession`, `pendingStartTask`) + 핸들러 3개(`handleConflictComplete`/`Discard`/`Cancel`) 추가. M4-3b REVIEW 후속(`App.test.tsx:240-258` NaN mock → URL 분기 `mockImplementation`)도 흡수 완료. 운영고려 -1점은 catch 블록 내부 `getActivePomodoro()`/재시도 `startPomodoro()` 중첩 await의 unhandled rejection 경로 — **M4-3d에 흡수**.
    - **M4-3d** — **PASS(12/12, 58 passed)**. 마운트 시 `getActivePomodoro()` 응답에서 `started_at + planned_duration_sec * 1000 <= now`이면 자동 `endPomodoro` + `setActivePomodoro(null)` 처리. `<PomodoroTimer>`에 `onExpire` prop + `useRef<boolean>(false)` 가드(`firedRef`)로 1회 발화 보장. `ActivePomodoroBanner`에 `key={active.id}`로 새 세션 시 자연 리마운트. `App.tsx` `handlePomodoroExpire`는 `finally`에서 항상 `setActivePomodoro(null)`. M4-3c catch 블록 unhandled rejection도 inner try/catch로 흡수 완료. 만료 후 다음 단계 자동 시작은 비포함(M4-4 범위).
  - **M4-4** — 단계 자동 전환 로직: focus → short_break/long_break 자동 전환(4세션마다 long_break), break 종료 후 다음 focus는 "묻기"가 기본(자동 시작 토글은 M5-3 설정 화면에서 도입). 한 세션 분량 유지를 위해 a/b/c로 분할.
    - **M4-4a** — **PASS(12/12, 70 passed)**. 백엔드 `GET /pomodoros/next-phase` 엔드포인트 완성. 응답 `PomodoroNextPhase{phase, planned_duration_sec}` 스키마 + 모듈 상수 `_FOCUS_SEC=1500/_SHORT_BREAK_SEC=300/_LONG_BREAK_SEC=900` + `last_long_id` 기반 focus 완주 카운트 로직(`% 4 == 0 && > 0`). 정적 `/next-phase`를 `/active` 바로 아래(동적 `/{id}/end`/`/discard` 위)에 등록. 신규 테스트 5건(빈 DB / focus 1회 / focus 4회 / break 후 / 폐기 후) 추가, 70 passed(0 failed, 기존 65 + 신규 5).
    - **M4-4b** — **PASS(12/12, 63 passed + 백엔드 71 passed)**. 프론트 focus 만료 시 자동 break 시작 + `getNextPhase` API 클라이언트 함수 신설 + 백엔드 회귀 테스트 1건 흡수.
      - **API 클라이언트 신설**: `frontend/src/api/pomodoros.ts`에 `PomodoroNextPhase` 타입 + `getNextPhase()` 함수 추가. 200 → JSON 매핑, !ok → throw.
      - **`handlePomodoroExpire` 확장**: `expired = activePomodoro` 스냅샷 → `endPomodoro(expired.id)` → `if (expired.phase === "focus")`: `getNextPhase()` 호출 → break 응답이면 동일 task로 `startPomodoro` 후 `setActivePomodoro(새 break 세션)` early return. 그 외/실패는 `setActivePomodoro(null)` + setError 폴백. break→focus "묻기" 다이얼로그는 M4-4c로 이월.
      - **백엔드 회귀 테스트 흡수**: `test_next_phase_after_long_break_resets_count` 1건 — long_break 종료 후 다시 focus 4회 완주 시 `last_long_id` 카운트 리셋이 작동하여 `long_break` 응답이 다시 나오는지 검증.
      - 신규 테스트 6건(App 통합 3 + API 단위 2 + 백엔드 회귀 1).
    - **M4-4c** — **PASS(12/12, 68 passed)**. 프론트 break 만료 시 "다음 집중 시작할까요?" 다이얼로그 완성. `frontend/src/features/pomodoro/NextFocusPromptDialog.tsx`(`role="dialog" aria-modal="true"` 루트, taskId 텍스트, 예/아니오 버튼) 신규. `App.tsx` 신규 상태 `nextFocusPromptTask: number | null` 단일화, `handlePomodoroExpire` break 분기 확장(`if (expired.phase !== "focus") setNextFocusPromptTask(expired.task_id)`), `handleNextFocusYes`(getNextPhase → focus 확인 → startPomodoro → setActivePomodoro, finally에서 항상 setNextFocusPromptTask(null))/`handleNextFocusNo`(다이얼로그 닫기만) 핸들러 추가, JSX 조건부 마운트. focus 만료 분기는 M4-4b 자동 break 시작 동작 그대로 유지(회귀 없음). 마운트 복원 만료 분기(App.tsx:28-35)는 비변경(M5-3 후 검토). 신규 테스트 5건(App 통합 4 + 컴포넌트 단위 1).

### M5. 알림 + 카운트 정책 + 설정
- 세션 종료 시 브라우저 알림 + 소리. 권한 없으면 토스트 폴백(PRD 6.5).
- 카운트 정책: 정상 종료(25분 완주) → 누적 +1, 폐기 → 포기 카운터 별도 기록(PRD 6.6).
- 설정 화면: 집중/짧은 휴식/긴 휴식 길이, 긴 휴식 주기, 휴식 후 자동 시작 여부, 알림 소리 on/off. `settings` 테이블에 단일 행 저장(PRD 8).
- 한 세션 분량으로 분할:
  - **M5-1** — 알림 인프라 + 발화 연결. 다시 a/b/c로 분할:
    - **M5-1a** — **PASS(12/12, 75 passed)**. `frontend/src/components/Toast.tsx`(자동 닫힘 `<div role="status">`) + `frontend/src/hooks/useNotification.ts`(`{ permission, requestPermission, notify(title, body, fallback) }`, granted/denied/미정의 분기 + try/catch 폴백) 신규. App.tsx 무수정. 단위 테스트 7건 통과(Toast 3 + useNotification 4).
    - **M5-1b** — **이번 사이클 활성**. App.tsx 통합. `handlePomodoroExpire`(focus/break 만료)와 마운트 복원 만료 분기(`App.tsx:28-35`)에서 `notify("집중 종료" / "휴식 종료", body, showToast)` 호출. `toasts: { id, message }[]` state + `showToast(message)` 함수 + `<Toast>` 다중 마운트. 마운트 시 `useEffect`로 `requestPermission()` 1회 호출(이미 granted/denied면 브라우저가 noop 처리). 통합 테스트(focus 만료 → notify 1회 / break 만료 → notify 1회 + 다이얼로그 동시 노출 / permission denied → 토스트 노출).
    - **M5-1c** — 사운드(Web Audio API beep) 발화. `useNotification.notify` 인자 확장 또는 별도 `playBeep()` 훅. M5-1b의 `notify` 호출 시점과 동일 시점에 발화. M5-3 설정 도입 시 on/off 토글로 분기.
  - **M5-2** — 카운트 정책 분리.
    - 백엔드 `Task` 응답에 `pomodoro_completed_count`, `pomodoro_abandoned_count` 두 필드 추가(`pomodoro_sessions`에서 집계, `end_reason` 분기). `GET /tasks` `selectinload` 그대로 유지하되 추가 서브쿼리 또는 `func.count` + `case` 사용.
    - `Task` 카드 우측 표시는 M6-3에서 연결. 본 마일스톤은 API 응답 필드만.
    - 한 사이클이면 충분.
  - **M5-3** — `settings` 테이블 + 설정 화면.
    - 백엔드 `Setting` 모델(단일 행, id=1) + `GET /settings` + `PATCH /settings`. 필드: `focus_sec`, `short_break_sec`, `long_break_sec`, `long_break_every`, `auto_start_next_focus`, `sound_on`.
    - 프론트 `frontend/src/features/settings/SettingsPanel.tsx` 신규 + 라우트/탭 분기(또는 모달).
    - `routers/pomodoros.py`의 `_FOCUS_SEC/_SHORT_BREAK_SEC/_LONG_BREAK_SEC` 상수를 settings 조회로 교체.
    - 자동 시작 토글이 켜져 있으면 `NextFocusPromptDialog`를 우회하고 즉시 focus 시작.
    - 한 사이클 분량 초과 가능 → 백엔드/프론트로 분할(M5-3a/b/c)하여 후속 결정.

### M6. 통계 + 백업
- 백엔드: 일별 완주 세션 집계 API(최근 30일), 오늘/이번 주/이번 달 요약 API, 할일별 누적 횟수.
- 프론트: 할일 카드 우측에 🍅 ×N, 통계 페이지(요약 카드 + Recharts 막대 그래프).
- 백업: SQLite 파일 위치를 README/UI에 안내. 별도 export UI는 1차 범위 외.

## 모듈 책임 (백엔드)

- `backend/app/main.py` — FastAPI 앱 부트스트랩, 정적 파일 서빙(prod).
- `backend/app/db.py` — 엔진/세션 팩토리, 스키마 마이그레이션(1차는 `create_all`).
- `backend/app/models/` — SQLAlchemy 모델(Task, Tag, TaskTag, PomodoroSession, Setting).
- `backend/app/schemas/` — Pydantic 입출력 스키마.
- `backend/app/routers/` — `tasks.py`, `pomodoros.py`, `stats.py`, `settings.py`, `health.py`.
- `backend/app/services/` — 도메인 로직(태그 동기화, 세션 단계 전환, 통계 집계).
- `backend/tests/` — pytest 기반 라우터/서비스 테스트.

## 모듈 책임 (프론트엔드)

- `frontend/src/api/` — fetch 래퍼 + 엔드포인트별 함수.
- `frontend/src/features/tasks/` — 할일 목록/카드/편집 폼.
- `frontend/src/features/pomodoro/` — 타이머 컴포넌트, 단계 표시, 다이얼로그.
- `frontend/src/features/stats/` — 요약 카드, 일별 그래프.
- `frontend/src/features/settings/` — 설정 폼.
- `frontend/src/components/` — 공통 UI(Toast, Dialog, TagInput).
- `frontend/src/hooks/` — `useTimer`, `useNotification`.
- `frontend/tests/` — Vitest + RTL.

## 비목표 (재확인)

- 인증/멀티 사용자/멀티 디바이스 동기화
- 모바일 네이티브
- 캘린더 등 외부 연동
- 드래그앤드롭 정렬, 다크모드, 단축키, 세션 메모, JSON export
