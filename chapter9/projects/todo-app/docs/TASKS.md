# TASKS — Todo + Pomodoro Web App

## 현재 사이클

상태: **M5-1a PASS(12/12, 프론트 75 passed + 백엔드 71 passed)** 반영. 활성 = **M5-1b** (App.tsx 통합: `useNotification` 마운트 + 만료 시점 `notify` 호출 + `toasts` state/`showToast`/`<Toast>` 마운트). PRD 6.5(브라우저 알림 + 소리, 권한 없으면 토스트 폴백) 반영의 두 번째 사이클(인프라→통합). 사운드(Web Audio beep)는 M5-1c, 카운트 정책은 M5-2, 설정 화면은 M5-3로 분할(PLAN M5 절 참조). 마운트 복원 만료 분기 다이얼로그 확장은 M5-3에서 처리(설정값 기반). 백로그(M3-2b-followup-A 태그 입력 점프, M1-2-followup-A ESLint flat config, M1-3 README)는 본 사이클 비포함.

## 활성 (이번 사이클)

### [x] M5-1b. 프론트 — App.tsx에 `useNotification` 통합 + 만료 시점 `notify` 발화 + 토스트 마운트
- 목표: PRD 6.5(세션 종료 시 브라우저 알림 + 권한 없으면 토스트 폴백)의 두 번째 사이클로, M5-1a에서 신설한 `useNotification` 훅을 App.tsx에 연결한다. 만료(focus/break/마운트 복원 모두)에서 `notify` 호출, fallback에 `showToast`를 주입하여 권한 없을 때 토스트로 대체한다. 사운드는 본 사이클 비포함(M5-1c).
- 자체 결정 사항(IMPL.md에 한 줄씩 기록):
  - **`toasts` state 형태**: `{ id: number; message: string }[]`. 다중 토스트 동시 노출 가능(focus → break 자동 전환 시 2회 발화 케이스 대비). `id`는 `Date.now()` 또는 단조 증가 카운터(jsdom fake timer 환경 안정성 위해 카운터 ref 권장).
  - **`showToast(message)` 함수**: `setToasts(prev => [...prev, { id, message }])` 만 수행. 자동 닫힘은 `Toast` 컴포넌트 `useEffect`가 담당하고, 닫힘 시점에 `setToasts(prev => prev.filter(t => t.id !== id))`로 제거. 따라서 `<Toast>` 호출 시 `onClose`에 `() => removeToast(id)` 주입.
  - **`notify` 호출 시점**: (1) `handlePomodoroExpire` 진입 직후 — focus 만료 시 `notify("집중 종료", "...", showToast)`, break 만료 시 `notify("휴식 종료", "...", showToast)`. body 메시지는 `expired.task_id` 또는 phase 정보 활용. (2) 마운트 복원 만료 분기(`App.tsx:28-35`) — focus/break phase에 따라 동일 분기. 어느 시점에서도 endPomodoro 호출 **전후**보다는 **endPomodoro 시도 전**에 발화하여 endPomodoro 실패 시에도 사용자가 만료를 인지하도록 함.
  - **`requestPermission` 자동 호출**: App.tsx 마운트 시 `useEffect(() => { requestPermission(); }, [])` 1회. 이미 granted/denied면 브라우저가 noop 처리. 거부 시에도 추가 안내 카드 등은 미포함(후속 사이클).
  - **`<Toast>` 마운트 위치**: JSX 최상위(`<div>` 루트 내부 마지막), top-right 정렬은 인라인 스타일 또는 임시 클래스로 처리(스타일 시스템 미도입 상태이므로 `style={{ position: "fixed", top: 16, right: 16 }}` 정도). 다중 토스트는 `flex-direction: column` 스택.
  - **타이틀/본문 문구**: PRD 명시 없음 → 한국어 단순 문구. focus 만료 = `"집중 세션이 종료되었습니다"`, break 만료 = `"휴식이 종료되었습니다"`. body는 `task #{task_id}` 형태.
  - **fallback 시 표시 메시지**: `notify`가 fallback 호출 시 body를 그대로 토스트에 표시. 제목/본문 합쳐 한 줄로 만들지 여부는 단순화 위해 body만.
  - **자동 break 시작 vs 알림 발화 순서**: `handlePomodoroExpire` focus 분기에서 `notify` → `endPomodoro` → `getNextPhase` → 자동 break 시작. break 만료 분기는 `notify` → `endPomodoro` → `setNextFocusPromptTask`. notify를 가장 앞에 두어 만료 발화는 모든 후속 분기와 독립.
  - **테스트 mock 전략**: `vi.stubGlobal("Notification", MockNotificationCtor)`로 permission granted/denied 분기 검증. 마운트 시 `requestPermission` 호출은 `MockNotificationCtor.requestPermission = vi.fn().mockResolvedValue("granted")` 모킹.
- acceptance:
  - `frontend/src/App.tsx` 수정 사항:
    1. `import { useNotification } from "./hooks/useNotification"` + `import { Toast } from "./components/Toast"` 추가.
    2. 컴포넌트 상단에 `const { notify, requestPermission } = useNotification()` 호출.
    3. `const [toasts, setToasts] = useState<{ id: number; message: string }[]>([])` 상태 추가.
    4. `const toastIdRef = useRef(0)` + `const showToast = (message: string) => { const id = ++toastIdRef.current; setToasts(prev => [...prev, { id, message }]); }` 헬퍼.
    5. `const removeToast = (id: number) => setToasts(prev => prev.filter(t => t.id !== id))` 헬퍼.
    6. 마운트 useEffect 신규: `useEffect(() => { requestPermission(); }, [])` (의존성 빈 배열).
    7. `handlePomodoroExpire` 진입 직후(현재 `if (!activePomodoro) return;` 다음 줄, `const expired = activePomodoro;` 직후)에 `const title = expired.phase === "focus" ? "집중 세션이 종료되었습니다" : "휴식이 종료되었습니다"; const body = \`task #${expired.task_id}\`; notify(title, body, showToast);` 추가.
    8. 마운트 복원 만료 분기(`App.tsx:28-35`)에 동일 `notify(...)` 호출 삽입(`if (active && Date.parse(...) <= Date.now())` 분기 진입 후 endPomodoro 호출 전).
    9. JSX 마지막에 토스트 컨테이너 추가:
       ```tsx
       <div data-testid="toast-container" style={{ position: "fixed", top: 16, right: 16, display: "flex", flexDirection: "column", gap: 8 }}>
         {toasts.map((t) => (
           <Toast key={t.id} message={t.message} onClose={() => removeToast(t.id)} />
         ))}
       </div>
       ```
  - 신규 통합 테스트 (`frontend/tests/App.test.tsx`, ≥ 4건):
    1. **마운트 시 `requestPermission` 1회 호출**: `MockNotificationCtor.requestPermission` mock + render → `await waitFor(() => expect(MockNotificationCtor.requestPermission).toHaveBeenCalledTimes(1))`.
    2. **focus 만료 → granted 시 `new Notification` 1회 호출**: permission `"granted"` 환경 + 활성 focus 세션 모킹 → fake timer로 `vi.advanceTimersByTime(planned_duration_sec * 1000)` → `MockNotificationCtor` 인스턴스화 1회 + 토스트 미노출(`queryByTestId("toast")` null).
    3. **break 만료 → granted 시 `new Notification` 호출 + `NextFocusPromptDialog` 동시 노출**: 기존 break 만료 다이얼로그 회귀 + notify 1회 추가 검증.
    4. **permission denied → 토스트 폴백 노출**: `MockNotificationCtor.permission = "denied"` 환경 + focus 만료 → `MockNotificationCtor` 인스턴스화 0회 + `findByTestId("toast")` 텍스트 확인.
    5. (권장, 강제 아님) **마운트 복원 만료 분기에서도 notify 호출**: 만료된 활성 세션 모킹(started_at + duration < now) → 마운트 시 endPomodoro 자동 호출 + notify 1회 호출 검증.
  - 검증:
    - 백엔드: `cd backend && uv run pytest -q` → **71 passed, 0 failed** (변경 없음 — 백엔드 무수정).
    - 프론트: `cd frontend && npm test -- --run` (vitest) → **≥ 79 passed, 0 failed** (기존 75 + 신규 ≥ 4).
    - 타입체크: `cd frontend && npx tsc --noEmit` → 신규 에러 0건(pre-existing 11건 유지 허용).
  - 비목표 (이번 사이클 밖):
    - 사운드(Web Audio API beep) — **M5-1c**.
    - 알림 소리 on/off 설정 — M5-3.
    - 카운트 정책(완주/포기 분리) — M5-2.
    - 권한 거부 안내 카드, 권한 재요청 버튼 등 UX 보강 — 후속 사이클.
    - 마운트 복원 만료 분기에 다이얼로그(`NextFocusPromptDialog`) 노출 — M5-3 설정 도입 후 검토.
    - 토스트 닫기 버튼/수동 닫기 UX — 후속 사이클(현재는 자동 닫힘만).
    - `Notification` 클릭 시 창 포커스 동작 — 후속 사이클.
- touch:
  - `frontend/src/App.tsx` (수정 — useNotification 도입, toasts state, requestPermission 자동 호출, notify 호출 3개 지점, JSX 토스트 컨테이너 추가)
  - `frontend/tests/App.test.tsx` (수정 — 신규 통합 테스트 ≥ 4건)
  - 변경 없음 예상: `frontend/src/components/Toast.tsx`, `frontend/src/hooks/useNotification.ts`, `frontend/src/api/*`, `frontend/src/features/*`, `frontend/src/hooks/useTimer.ts`, 백엔드 전체.

## 백로그 (다음 사이클 이후)

### M1 보완 (M1-2 REVIEW 후속)
- [ ] M1-2-followup-A. `frontend/eslint.config.js` (ESLint v9 flat config) 추가 + `@eslint/js`, `@typescript-eslint/eslint-plugin`, `@typescript-eslint/parser` 의존성 추가. `npm run lint`가 0 에러로 통과.
- [x] M1-2-followup-B. `frontend/tests/App.test.tsx` fetch 실패 경로 테스트 — M2-3a에서 흡수 완료.

### M1
- [ ] M1-3. 루트 `README.md` — 두 프로세스 실행 방법, 프로젝트 구조, 백업 방법(SQLite 파일 경로) 안내.

### M2 보완 (M2-2b2 REVIEW 후속) — **M3-1에 흡수 완료**
- [x] M2-2b2-followup-A. `done→done` 동일 상태 PATCH `completed_at` 불변 테스트 — M3-1에 흡수.
- [x] M2-2b2-followup-B. `__import__("sqlalchemy", fromlist=["select"]).select(...)` 인라인 호출 정리 — M3-1에 흡수.

### M3 보완 (M3-2b REVIEW 후속)
- [ ] M3-2b-followup-A. `frontend/src/features/tasks/TaskFilters.tsx` 태그 입력 UX 점프 개선 — controlled value를 로컬 string state로 분리하고 `onBlur`/Enter 시점에만 `onChange` 호출하여 trailing comma+space 점프 제거. 기능 정확도에는 영향 없는 UX 개선이므로 M4 이후 UX 사이클에서 처리.

### M4 — 타이머 코어 — **마감(전 단계 PASS)**
- (M4-4c PASS로 마감. 후속 메모는 M5-3 설정 도입 시 처리.)

### M5 — 알림/카운트/설정
- (이번 사이클 활성: **M5-1b** — 위 "활성" 섹션 참조)
- [ ] M5-1c. 사운드(Web Audio API beep) 발화 — M5-1b의 `notify` 호출 시점과 동일 시점에 발화. `useNotification`에 `playBeep()` 추가하거나 별도 `useBeep` 훅 분리. 설정 도입 시 on/off 토글로 분기(M5-3).
- [ ] M5-2. 카운트 정책 분리 — 백엔드 `Task` 응답에 `pomodoro_completed_count`/`pomodoro_abandoned_count` 두 필드 추가(`pomodoro_sessions`에서 `end_reason` 분기 집계). UI 표시는 M6-3.
- [ ] M5-3. `settings` 테이블 + 설정 화면 — 백엔드 `Setting` 모델/API + 프론트 `SettingsPanel.tsx` + `routers/pomodoros.py` 상수→DB 조회 교체 + `NextFocusPromptDialog` 자동 시작 토글 분기 + 마운트 복원 만료 분기 자동 break 전환 검토. 한 사이클 분량 초과 가능 → 백엔드/프론트 분할(M5-3a/b/c) 후속 결정.

### M6 — 통계/백업
- [ ] M6-1. 백엔드 통계 API: 일별/요약/할일별.
- [ ] M6-2. 프론트 통계 화면: 요약 카드 + Recharts 막대 그래프.
- [ ] M6-3. 할일 카드의 🍅 ×N 표시 연결.
- [ ] M6-4. README에 SQLite 백업 절차 명시.

## 완료

- [x] M1-1. 백엔드 스켈레톤 (FastAPI + SQLite) — PASS(10/12)
- [x] M1-2. 프론트엔드 스켈레톤 (Vite + React + TS) — PASS(9/12)
- [x] M2-1. Task 도메인 DB 스키마/모델 + 부트스트랩 정비 — PASS(11/12)
- [x] M2-2a. 태그 동기화 서비스 + 관계 테스트 + `POST /tasks` — PASS(11/12)
- [x] M2-2b1. `GET /tasks` + `DELETE /tasks/{id}` + REVIEW 후속 흡수 — PASS(11/12)
- [x] M2-2b2. `PATCH /tasks/{id}` + `GET /tasks` N+1 개선 — PASS(11/12)
- [x] M2-3a. 프론트엔드 Task API 클라이언트 + 읽기 전용 TaskList — PASS(12/12)
- [x] M2-3b. 프론트엔드 새 할일 추가 폼 + `POST /api/tasks` 연동 — PASS(12/12)
- [x] M2-3c1. 프론트엔드 카드 상태 토글 + 삭제 + "완료된 항목 보기" 필터 — PASS(12/12)
- [x] M2-3c2. 프론트엔드 카드 인라인 편집 폼 (제목/메모/우선순위/태그) — PASS(12/12)
- [x] M3-1. 백엔드 `GET /tasks` 검색·필터 쿼리 파라미터 + M2-2b2 후속 흡수 — PASS(12/12, 38 passed)
- [x] M3-2a. 프론트엔드 `listTasks(filters?)` 시그니처 확장 + `showCompleted` → 백엔드 `status` 필터 통합 — PASS(12/12, 30 passed)
- [x] M3-2b. 프론트엔드 검색바 / 태그 다중 입력 / 날짜 프리셋 UI (`TaskFilters.tsx` 분리) — PASS(11/12, 36 passed)
- [x] M4-1. 백엔드 `pomodoro_sessions` DB 스키마/모델 + Task 양방향 관계 + 모델 테스트 4건 — PASS(12/12, 42 passed)
- [x] M4-2a. 백엔드 `POST /pomodoros` + `GET /pomodoros/active` (전역 단일 활성 세션 보장 409) — PASS(12/12, 51 passed)
- [x] M4-2b. 백엔드 `POST /pomodoros/{id}/end` + `POST /pomodoros/{id}/discard` (404/409 가드, Literal end_reason, 활성 잠금 자연 해제) — PASS(12/12, 61 passed)
- [x] M4-2c. 백엔드 `GET /tasks` `date_preset` 기준 last pomodoro 전환 (COALESCE 상관 서브쿼리 + 4건 회귀 테스트) — PASS(12/12, 65 passed)
- [x] M4-3a. 프론트엔드 Pomodoro API 클라이언트(`pomodoros.ts`, 4개 함수, 404→null) + `ActivePomodoroBanner.tsx` + App.tsx 마운트 effect/배너 — PASS(12/12, 43 passed)
- [x] M4-3b. 프론트엔드 카드 "시작" 버튼 → `POST /pomodoros` 시작 + `PomodoroTimer` 컴포넌트(MM:SS + `<progress>`) + `useTimer` 훅(1초 tick) — PASS(11/12, 49 passed)
- [x] M4-3c. 프론트엔드 단일 세션 보장 다이얼로그(409 → `getActivePomodoro` 재조회 → 완료/폐기/취소 분기 → `/end` 또는 `/discard` 후 신규 시작 재시도) + `App.test.tsx` NaN mock URL 분기 수정 — PASS(11/12, 54 passed)
- [x] M4-3d. 프론트엔드 새로고침 복원 만료 자동 처리(마운트/진행 중) + `<PomodoroTimer>` `onExpire`/`firedRef` 1회 발화 가드 + `handleStartPomodoro` catch 블록 inner try/catch 보강 — PASS(12/12, 58 passed)
- [x] M4-4a. 백엔드 `GET /pomodoros/next-phase` (`PomodoroNextPhase` 스키마 + 길이 상수 3개 + last_long_id 기반 focus 완주 카운트 % 4 분기) + 신규 테스트 5건 — PASS(12/12, 70 passed)
- [x] M4-4b. 프론트 focus 만료 시 자동 break 시작 + `getNextPhase` API 클라이언트 신설 + 백엔드 long_break 카운트 리셋 회귀 테스트 1건 — PASS(12/12, 프론트 63 passed + 백엔드 71 passed)
- [x] M4-4c. 프론트 break 만료 시 "다음 집중 시작할까요?" 다이얼로그 (`NextFocusPromptDialog` + `App.tsx` 신규 상태/핸들러 2개 + JSX 마운트, focus 만료 회귀 보존) — PASS(12/12, 프론트 68 passed + 백엔드 71 passed)
- [x] M5-1a. 프론트 알림 인프라 (`Toast.tsx` + `useNotification.ts` + 단위 테스트 7건) — PASS(12/12, 프론트 75 passed + 백엔드 71 passed)
