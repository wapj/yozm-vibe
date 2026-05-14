# REVIEW — M5-1b

## 평가 대상

**M5-1b**: App.tsx에 `useNotification` 통합 + 만료 시점 `notify` 발화 + `<Toast>` 다중 마운트

## 테스트 실행 결과

| 대상 | 명령 | 결과 |
|------|------|------|
| 백엔드 | `cd backend && uv run pytest -q` | **71 passed, 0 failed** (변경 없음) |
| 프론트엔드 | `cd frontend && npm test -- --run` | **79 passed, 0 failed** (기존 75 + 신규 4) |
| 타입 체크 | `npx tsc --noEmit` | 신규 에러 0건 (기존 11건 유지) |

---

## 점수

| 축 | 점수 | 근거 |
|----|------|------|
| 사양 충족 | 3 | acceptance 9개 항목 + 신규 테스트 4건 모두 충족, 권장 항목 5번 코드도 구현됨 |
| 모듈 경계 | 3 | `hooks/useNotification`, `components/Toast` PLAN 모듈 책임 정위치, 경계 위반 없음 |
| 테스트 충실도 | 2 | 4개 필수 케이스 포함, 알림 제목/본문 내용 상세 검증 없음, 마운트 복원 분기 알림 검증 미포함 |
| 운영 고려 | 2 | toastIdRef 카운터 적절, notify 위치 endPomodoro 전 적절, stale notify 클로저 이론적 위험 존재 |
| **합계** | **10** | |

## 판정: **PASS** (10 ≥ 9)

---

## 세부 평가

### 사양 충족 (3/3)

TASKS.md acceptance 항목 전부 충족:

- `import useNotification/Toast` — `App.tsx:10-11` ✓
- `const { notify, requestPermission } = useNotification()` — `App.tsx:14` ✓
- `toasts` state + `toastIdRef` + `showToast`/`removeToast` — `App.tsx:22-30` ✓
- 마운트 `useEffect(() => { requestPermission(); }, [])` — `App.tsx:39-40` ✓
- `handlePomodoroExpire` 진입 직후 `notify` 호출 — `App.tsx:113-115` ✓
- 마운트 복원 만료 분기 `notify` 호출 — `App.tsx:46-48` ✓
- `data-testid="toast-container"` div + `<Toast>` 다중 마운트 — `App.tsx:255-262` ✓
- 신규 통합 테스트 4건 — `App.test.tsx:860-981` ✓
- 권장 항목 5번(마운트 복원 만료 분기 notify) 코드 구현됨 — `App.tsx:46-48` ✓

### 모듈 경계 (3/3)

- `useNotification` → `frontend/src/hooks/useNotification.ts` — PLAN.md:101 `hooks/` 책임 준수 ✓
- `Toast` → `frontend/src/components/Toast.tsx` — PLAN.md:100 `components/` 책임 준수 ✓
- App.tsx가 `hooks/`와 `components/`를 올바르게 참조, 역방향 의존성 없음 ✓
- 백엔드 전체 무수정 ✓

### 테스트 충실도 (2/3)

**충족:**
- 필수 acceptance 4건 모두 구현됨:
  1. 마운트 시 `requestPermission` 1회 호출 — `App.test.tsx:860`
  2. focus 만료 → granted → `new Notification` 1회 + 토스트 미노출 — `App.test.tsx:878`
  3. break 만료 → granted → `new Notification` 1회 + `NextFocusPromptDialog` 동시 노출 — `App.test.tsx:914`
  4. focus 만료 → denied → 토스트 폴백 노출 + Notification 미생성 — `App.test.tsx:947`

**미진:**
- 알림 제목/본문 내용 상세 검증 없음 — `App.test.tsx:908`에서 `notificationInstances.length >= 1`만 검사, `notificationInstances[0].title === "집중 세션이 종료되었습니다"` 어서션 없음
- 마운트 복원 만료 분기(`App.tsx:46-48`) notify 발화 테스트 미포함 — 코드 구현됐으나 검증 없어 회귀 위험 약간 존재
- break 만료 케이스(`App.test.tsx:914`)에서 `"휴식이 종료되었습니다"` 타이틀 직접 검증 없음

### 운영 고려 (2/3)

**잘된 점:**
- `toastIdRef` 카운터 방식(`App.tsx:23`) — fake timer 환경에서 `Date.now()` 충돌 회피 ✓
- `notify` 위치 endPomodoro 전(`App.tsx:115`) — API 실패 시에도 사용자 만료 인지 보장 ✓
- eslint-disable 처리 의도 `IMPL.md` 자체 결정 항목 3번에 문서화 ✓

**미진:**
- `useNotification.ts:22-34`에서 `notify`가 `useCallback([permission])` 선언됨. 마운트 복원 분기 useEffect(`App.tsx:42-62`)가 빈 의존성 배열로 클로저 캡처되어, `requestPermission()` 결과로 permission이 변경된 후에도 마운트 시점의 stale `notify`가 사용될 수 있음. 실질 영향은 낮음(마운트 시 동시 실행)이나 이론적 위험 존재
- 마운트 복원 만료 notify 경로의 테스트 미포함으로 향후 리팩토링 시 회귀 감지 어려움

---

## 다음 사이클로 넘기는 메모

본 사이클은 PASS이므로 블로킹 이슈 없음. 다음 사이클은 **M5-1c**(사운드 Web Audio beep 발화) 또는 **M5-2**(카운트 정책) 중 선택.

단, 이후 사이클에서 처리 권장:

1. **알림 내용 어서션 보강** (테스트 충실도): `notificationInstances[0].title`/`body` 직접 검증 어서션 추가. M5-1c 또는 M5-2 사이클에서 흡수 가능.
2. **마운트 복원 만료 notify 테스트** (테스트 충실도): 기존 "마운트 시 만료된 활성 세션" 테스트(`App.test.tsx:417`)에 `MockNotification` mock을 추가하여 notify 1회 호출 검증 병합 가능.
3. **stale notify 클로저** (운영 고려): 마운트 복원 분기 useEffect에서 `notify`를 의존성에 포함하거나 `useRef`로 최신 참조를 유지하는 방식으로 개선 가능. 실질 영향 낮으므로 M5-3 이후 useEffect 재구성 시 같이 처리 권장.

---

# REVIEW — M5-1a

## 평가 대상

**M5-1a**: 프론트 알림 인프라 (`useNotification` 훅 + `Toast` 컴포넌트) 단위 컴포넌트만

## 테스트 실행 결과

```
# 프론트엔드
cd frontend && npm test -- --run
→ 75 passed (13 test files), 0 failed
   기존 68 + 신규 7 (Toast 3건 + useNotification 4건)

# 백엔드
cd backend && uv run pytest -q
→ 71 passed, 0 failed  (변경 없음)

# 타입체크
cd frontend && npx tsc --noEmit
→ pre-existing 11건 유지, 본 사이클 신규 에러 0건
```

---

## 점수

| 축 | 점수 | 근거 |
|----|------|------|
| 사양 충족 | 3 | Toast.tsx / useNotification.ts 코드가 acceptance spec과 1:1 일치, 테스트 7건(의무 ≥ 5건) 전부 통과, App.tsx 무수정 |
| 모듈 경계 | 3 | `components/Toast.tsx`, `hooks/useNotification.ts` PLAN.md 모듈 책임 정위치, 백엔드/App.tsx 무수정 |
| 테스트 충실도 | 3 | acceptance 명세 7가지 시나리오 전부 구현, 기존 68건 회귀 없음 |
| 운영 고려 | 3 | `typeof Notification === "undefined"` 환경 가드, try/catch fallback, useEffect clearTimeout 정리, dependency injection 설계로 결합도 최소화 |
| **합계** | **12** | |

## 판정: **PASS**

---

## 세부 평가

### 사양 충족 (3/3)

- `frontend/src/components/Toast.tsx:1-15` — acceptance spec 코드와 완전 일치: `Props = { message, onClose, durationMs? }`, `useEffect(() => { const id = setTimeout(onClose, durationMs); return () => clearTimeout(id); }, [onClose, durationMs])`, `<div role="status" aria-live="polite" data-testid="toast">{message}</div>` ✓
- `frontend/src/hooks/useNotification.ts:1-38` — acceptance spec 코드와 완전 일치: `useState<NotificationPermission>` lazy initializer, `requestPermission` useCallback, `notify` useCallback(permission 의존) ✓
- `notify` 분기 정책: `typeof Notification === "undefined" || permission !== "granted"` → `fallback(body)` + 예외 시 `fallback(body)` 안전 폴백 ✓ (`useNotification.ts:24-32`)
- 신규 테스트 7건(≥ 5건 충족): Toast 3건 + useNotification 4건 ✓
- 프론트 75 passed / 백엔드 71 passed / 신규 tsc 에러 0건 ✓
- App.tsx 무수정 (git status 확인) ✓

### 모듈 경계 (3/3)

- `frontend/src/components/Toast.tsx` — PLAN.md:100 `components/: 공통 UI(Toast, Dialog, TagInput)` 준수 ✓
- `frontend/src/hooks/useNotification.ts` — PLAN.md:101 `hooks/: useTimer, useNotification` 준수 ✓
- `frontend/src/App.tsx` 무수정 — TASKS.md "App.tsx 변경 없음" 명시 준수 ✓
- 백엔드 전체 무수정 ✓
- `frontend/src/api/*`, `frontend/src/features/*`, `frontend/src/hooks/useTimer.ts` 무수정 ✓

### 테스트 충실도 (3/3)

| # | 파일 | 테스트 케이스 | 검증 범위 | 위치 |
|---|------|-------------|---------|------|
| 1 | `Toast.test.tsx` | 메시지 렌더 | `getByTestId("toast").textContent === "hi"` | :14 |
| 2 | `Toast.test.tsx` | durationMs 후 onClose 1회 호출 | fake timer 4000ms → 1회 / 5000ms → 추가 없음 | :19 |
| 3 | `Toast.test.tsx` | unmount 시 setTimeout 정리 | unmount 후 5000ms advance → onClose 미호출 | :28 |
| 4 | `useNotification.test.ts` | granted → new Notification 호출 + fallback 미호출 | `MockNotificationCtor` 1회 인스턴스화 검증 | :10 |
| 5 | `useNotification.test.ts` | denied → fallback 호출 + 인스턴스화 없음 | `fallback` 1회 / `MockNotificationCtor` 0회 | :25 |
| 6 | `useNotification.test.ts` | Notification 미정의 → fallback 호출 | `vi.stubGlobal("Notification", undefined)` | :40 |
| 7 | `useNotification.test.ts` | requestPermission 후 permission state 갱신 | `act` 후 `result.current.permission === "granted"` | :51 |

- TASKS.md acceptance 명세 7건과 파일/시나리오 1:1 대응 ✓
- 기존 68건 회귀 0 ✓

### 운영 고려 (3/3)

- `useNotification.ts:6-8` — lazy initializer `typeof Notification === "undefined" ? "denied" : Notification.permission`로 jsdom/SSR 환경 안전 ✓
- `useNotification.ts:10-20` — `requestPermission` try/catch로 `Notification.requestPermission()` 실패 시 `"denied"` 안전 폴백 ✓
- `useNotification.ts:27-32` — `new Notification()` try/catch + `fallback(body)` 안전 폴백 ✓
- `Toast.tsx:7-8` — `useEffect` cleanup(`return () => clearTimeout(id)`)으로 컴포넌트 unmount 시 타이머 메모리 누수 방지 ✓
- `notify(title, body, fallback)` 의존 주입(fallback 콜백) 설계로 Toast 큐와의 직접 결합 없음 — M5-1b 통합 시 유연하게 연결 가능 ✓
- IMPL.md 자체 결정 사항 1건 기록 (`vi.fn() as any` 캐스팅으로 TS 에러 0건 유지) ✓

---

## 다음 사이클로 넘기는 메모

본 사이클은 PASS이므로 블로킹 이슈 없음. 다음 사이클(M5-1b) Planner를 위한 참고 메모:

1. **M5-1b 연결 포인트**: `useNotification` 훅은 `notify(title, body, fallback)` 시그니처를 노출. `fallback` 인자에 `showToast(body)` 함수를 주입하면 됨. App.tsx에 `toasts` state + `showToast` 함수 추가 예상.
2. **requestPermission 자동 호출**: M5-1b에서 App.tsx 마운트 시 `useEffect`로 `requestPermission()` 1회 호출 처리. 이미 `granted`/`denied`이면 브라우저가 noop 처리하므로 중복 호출 안전.
3. **백로그 잔존**: `TaskFilters.tsx` 태그 입력 trailing comma 점프(M3-2b-followup-A), ESLint flat config(M1-2-followup-A) 여전히 미처리.

---

# REVIEW — M4-4c

## 평가 대상

**M4-4c**: 프론트 break 만료 시 "다음 집중 시작할까요?" 다이얼로그

## 테스트 실행 결과

```
# 백엔드
cd backend && uv run pytest -q
→ 71 passed, 0 failed  (M4-4b 대비 변경 없음)

# 프론트엔드
cd frontend && npm test -- --reporter=verbose
→ 68 passed (11 test files), 0 failed
   기존 63 + 신규 5 (App 통합 4건 + 컴포넌트 단위 1건)

# 타입체크
cd frontend && npx tsc --noEmit
→ pre-existing 11건 유지, 본 사이클 신규 에러 0건
```

---

## 점수

| 축 | 점수 | 근거 |
|----|------|------|
| 사양 충족 | 3 | acceptance 전 항목 통과, 다이얼로그 spec 코드와 1:1 일치, App.tsx 수정 spec 완전 부합 |
| 모듈 경계 | 3 | `features/pomodoro/` 컨벤션 준수, 비즈니스 로직 App.tsx 집중, 컴포넌트는 순수 UI |
| 테스트 충실도 | 3 | 신규 5건, acceptance 4가지 시나리오 + 컴포넌트 단위 1건, getNextPhase 미호출 검증 포함 |
| 운영 고려 | 3 | finally 가드, null 가드, focus early return 유지, 비목표 명시 |
| **합계** | **12** | |

## 판정: **PASS**

---

## 세부 평가

### 사양 충족 (3/3)

- `frontend/src/features/pomodoro/NextFocusPromptDialog.tsx:1-11` — acceptance spec 코드와 완전 일치: `role="dialog" aria-modal="true" data-testid="next-focus-prompt-dialog"`, `data-testid="next-focus-yes"/"next-focus-no"`, named export ✓
- `App.tsx:18` — `const [nextFocusPromptTask, setNextFocusPromptTask] = useState<number | null>(null)` 상태 신규 ✓
- `App.tsx:9` — `NextFocusPromptDialog` named import 추가 ✓
- `App.tsx:91-116` — `handlePomodoroExpire` break 분기 acceptance 코드 블록과 1:1 일치: focus early return 유지, `setActivePomodoro(null)` 이후 `if (expired.phase !== "focus") setNextFocusPromptTask(expired.task_id)` ✓
- `App.tsx:149-170` — `handleNextFocusYes`: null 가드, `getNextPhase` → focus 확인 → `startPomodoro` → `setActivePomodoro`, finally에서 항상 `setNextFocusPromptTask(null)` ✓
- `App.tsx:172-174` — `handleNextFocusNo`: `setNextFocusPromptTask(null)` 단순 처리, 추가 API 호출 없음 ✓
- `App.tsx:226-232` — `nextFocusPromptTask !== null && <NextFocusPromptDialog ...>` JSX 마운트 ✓

### 모듈 경계 (3/3)

- `frontend/src/features/pomodoro/NextFocusPromptDialog.tsx` — PLAN.md:89 `features/pomodoro/: 다이얼로그` 책임 준수 ✓
- 비즈니스 로직(`getNextPhase` + `startPomodoro` 호출)은 `App.tsx:149-169` 핸들러에 집중 ✓
- 컴포넌트는 `{ taskId, onYes, onNo }` props 기반 순수 UI — `PomodoroConflictDialog` 패턴과 일관 ✓
- `frontend/src/api/pomodoros.ts` 미변경(touch 목록 준수) ✓
- 백엔드 전체 무수정 ✓

### 테스트 충실도 (3/3)

| # | 파일 | 테스트 케이스 | 검증 범위 | 위치 |
|---|------|-------------|---------|------|
| 1 | `App.test.tsx` | break 만료 → 다이얼로그 표시 + endPomodoro 호출 + getNextPhase 미호출 | 핵심 흐름 + `/next-phase` URL 미호출 단언 | :722 |
| 2 | `App.test.tsx` | "예" 클릭 → getNextPhase + startPomodoro(focus) + 다이얼로그 닫힘 + 배너 교체 | 예 분기 전체 + task_id 검증 | :771 |
| 3 | `App.test.tsx` | "아니오" 클릭 → 다이얼로그 닫힘 + 추가 API 미호출 | `callsBeforeNo` 패턴으로 API 횟수 직접 검증 | :857 |
| 4 | `App.test.tsx` | focus 만료 분기 회귀: 자동 break 시작 + 다이얼로그 미노출 | M4-4b 동작 보존 + `queryByTestId` null 검증 | :909 |
| 5 | `NextFocusPromptDialog.test.tsx` | taskId 텍스트 표시 + 예/아니오 콜백 | 컴포넌트 단위 — 렌더 + callback 각 1회 | :7 |

- 테스트 1의 `allCalls.some(url => url.includes("/next-phase"))` 단언(`App.test.tsx:766`)으로 "다이얼로그가 닫힐 때까지 getNextPhase 보류" acceptance 조건을 직접 검증 ✓
- 테스트 3의 `callsBeforeNo` 패턴(`App.test.tsx:895`)으로 "아니오 이후 추가 API 미호출" 정밀 검증 ✓

### 운영 고려 (3/3)

- `App.tsx:167` — `finally { setNextFocusPromptTask(null) }` — 성공/실패/비정상 phase 응답 모든 경로에서 다이얼로그 닫힘 보장 ✓
- `App.tsx:150` — `if (nextFocusPromptTask === null) return` 가드 ✓
- `App.tsx:164-166` — catch에서 `setError + setActivePomodoro(null)` ✓
- `App.tsx:104-105` — focus 만료 분기 early return 유지 → M4-4b 자동 break 동작 회귀 없음 ✓
- `IMPL.md:23` — 마운트 복원 만료 분기 비변경 의도 명시 ✓
- `IMPL.md:21` — M5-3 자동 시작 토글 연결점 명시 ✓

---

## 다음 사이클로 넘기는 메모

본 사이클은 PASS이므로 블로킹 이슈 없음. M4 전 단계(M4-1/2a/2b/2c/3a/3b/3c/3d/4a/4b/4c) 완료. 다음 사이클(M5) Planner를 위한 참고 메모:

1. **마운트 복원 만료 분기**: `App.tsx:28-35` — 새로고침 후 break 만료 시 다이얼로그 없이 `endPomodoro + setActivePomodoro(null)` 처리. M5-3 settings 도입 시 자동 시작 토글 설정값 기반으로 이 분기도 확장 검토.
2. **자동 시작 토글 연결 포인트**: `App.tsx:108-111` `if (expired.phase !== "focus")` 분기 앞에 settings 조회 분기 삽입으로 M5-3 확장 가능.
3. **백로그 잔존**: `TaskFilters.tsx` 태그 입력 trailing comma 점프(M3-2b-followup-A), ESLint flat config(M1-2-followup-A) 여전히 미처리.

---

# REVIEW — M4-4b

## 평가 대상

**M4-4b**: 프론트 focus 만료 시 자동 break 시작 + `getNextPhase` API 클라이언트 신설 + 백엔드 카운트 리셋 회귀 테스트 흡수

## 테스트 실행 결과

```
cd backend && uv run pytest -q
71 passed in 0.79s  (기존 70 + 신규 1, 0 실패)

cd frontend && npm test
63 passed (10 files)  (기존 58 + 신규 5, 0 실패)

cd frontend && npx tsc --noEmit
11개 에러 전부 pre-existing (M3-2b TaskFilters 식별자 충돌 3건, .at() 4건, onStartPomodoro 누락 4건)
본 사이클 신규 tsc 에러 0건
```

---

## 점수

| 축 | 점수 | 근거 |
|----|------|------|
| 사양 충족 | 3 | acceptance 전 항목 통과, `handlePomodoroExpire` 골격이 TASKS.md 코드와 1:1 일치 |
| 모듈 경계 | 3 | API 클라이언트 `api/pomodoros.ts` 단일 파일 유지, 백엔드 라우터/스키마/모델 무수정 |
| 테스트 충실도 | 3 | 신규 6건(프론트 5 + 백엔드 1), 의무 4건 초과, 경계값·에러 케이스 포함 |
| 운영 고려 | 3 | early return 패턴으로 setActivePomodoro(null) 중복 방지, catch 폴백 완비 |
| **합계** | **12** | |

## 판정: **PASS**

---

## 세부 평가

### 사양 충족 (3/3)

- `frontend/src/api/pomodoros.ts:18` — `export type PomodoroNextPhase = { phase: PomodoroPhase; planned_duration_sec: number }` TASKS.md acceptance 타입과 정확히 일치 ✓
- `frontend/src/api/pomodoros.ts:51-55` — `getNextPhase()` 함수 구현: URL `/api/pomodoros/next-phase`, `!res.ok → throw`, `res.json() as PomodoroNextPhase` 반환. TASKS.md acceptance 코드 블록과 1:1 ✓
- 기존 5개 export(`PomodoroPhase`/`PomodoroEndReason`/`PomodoroSession`/`StartPomodoroInput`/`PomodoroConflictError` + 4개 함수) 변경 없음 ✓
- `frontend/src/App.tsx:89-111` — `handlePomodoroExpire` 골격이 TASKS.md 코드 블록과 정확히 일치: `expired = activePomodoro` 스냅샷 → `endPomodoro` → `if (focus)` → `getNextPhase` → break 응답 시 `startPomodoro` + `return` early exit, 나머지는 `setActivePomodoro(null)` ✓
- `frontend/src/App.tsx:25-41` — 마운트 만료 분기(line 28-35) M4-3d 동작 그대로 유지 ✓
- `backend/tests/test_pomodoros_api.py:295-314` — `test_next_phase_after_long_break_resets_count`: focus 4회→long_break→focus 4회→GET /pomodoros/next-phase → `{"phase":"long_break","planned_duration_sec":900}` 검증 ✓
- 검증: 백엔드 71 passed, 프론트 63 passed, 0 failed ✓

### 모듈 경계 (3/3)

- API 클라이언트 함수는 `frontend/src/api/pomodoros.ts` 단일 파일에 추가 — import 단일화 원칙 유지 ✓
- `frontend/src/App.tsx` — 오케스트레이션 레이어에서 `getNextPhase` 호출. 컴포넌트/훅 레이어는 무수정 ✓
- 백엔드 라우터/스키마/모델/서비스 무수정(테스트 1건 추가만) ✓
- `PomodoroTimer`/`ActivePomodoroBanner`/`PomodoroConflictDialog`/`useTimer` 등 기존 프론트 컴포넌트 무수정 ✓
- PLAN.md `frontend/src/api/` 모듈 책임("fetch 래퍼 + 엔드포인트별 함수") 준수 ✓

### 테스트 충실도 (3/3)

신규 6건이 TASKS.md acceptance 4가지 시나리오 + 권장 1건 모두 커버:

| # | 파일 | 테스트명 | 검증 브랜치 | 위치 |
|---|---|---|---|---|
| 1 | `App.test.tsx` | focus 만료 → short_break 자동 시작 | focus → short_break(300) | :539 |
| 2 | `App.test.tsx` | focus 만료 → long_break 자동 시작 | focus → long_break(900) | :608 |
| 3 | `App.test.tsx` | break 만료 → 자동 시작 없음 | break → endPomodoro만, /next-phase 미호출 | :673 |
| 4 | `pomodorosApi.test.ts` | getNextPhase 200 매핑 | URL + 응답 객체 매핑 | :88 |
| 5 | `pomodorosApi.test.ts` | getNextPhase 500 throw | `!ok` → throw | :102 |
| 6 | `test_pomodoros_api.py` | test_next_phase_after_long_break_resets_count | long_break 후 카운트 리셋 | :295 |

- 테스트 3(`App.test.tsx:714-715`)에서 `fetchMock.mock.calls.map(c => c[0]).some(url => url.includes("/next-phase"))` 로 호출 자체가 없음을 직접 단언 ✓
- 테스트 1·2는 fake timer `vi.advanceTimersByTime(3000)`으로 onExpire 발화 후 배너 텍스트까지 검증하여 UI 연동까지 포함 ✓

### 운영 고려 (3/3)

- `App.tsx:96-103` — 자동 시작 성공 path에서 `setActivePomodoro(session)` 직후 `return` early exit → `setActivePomodoro(null)` 폴백이 실행되지 않아 새 break 세션 덮어쓰기 방지 ✓
- `App.tsx:107-110` — catch 블록에서 항상 `setError + setActivePomodoro(null)` — endPomodoro/getNextPhase/startPomodoro 어느 단계에서 throw되어도 만료 세션이 UI에 잔존하지 않음 ✓
- `App.tsx:94` — `expired.phase === "focus"` 체크로 break 만료 시 `getNextPhase` 호출 자체를 방지 — M4-4c 비포함 범위 준수 ✓
- `App.tsx:90-91` — `if (!activePomodoro) return; const expired = activePomodoro;` — stale closure로 인한 null 접근 방지 ✓
- 타입체크: pre-existing 11건, 본 사이클 신규 0건 ✓

---

## 다음 사이클로 넘기는 메모

본 사이클은 PASS이므로 블로킹 이슈 없음. 다음 사이클(M4-4c) Planner를 위한 참고 메모:

1. **M4-4c 범위 명확화**: `handlePomodoroExpire`에서 `expired.phase !== "focus"` 분기(현재 `setActivePomodoro(null)` 단순 처리)에 `NextFocusPromptDialog` 노출 로직을 추가해야 함. `App.tsx`에 신규 상태 변수(`showNextFocusPrompt`, `expiredBreakTask`) 추가 예상. 기존 `handlePomodoroExpire` try/catch 구조를 유지한 채 break 분기만 확장하면 됨.

2. **마운트 복원 만료 자동 break 전환 미포함 확인**: `App.tsx:28-35` 마운트 분기는 여전히 단순 `endPomodoro + setActivePomodoro(null)`만 수행. 설정 도입(M5-3) 후 이 분기도 자동 break 전환을 지원하는지 검토 필요.

3. **UX 백로그**: `TaskFilters.tsx` 태그 입력 trailing comma 점프(M3-2b-followup-A), ESLint flat config(M1-2-followup-A) 여전히 미처리. M4-4c 이후 UX 사이클 권장.

---

# REVIEW — M4-4a

## 평가 대상

**M4-4a**: 백엔드 `GET /pomodoros/next-phase` 엔드포인트 (다음 단계 phase + 길이 계산)

## 테스트 실행 결과

```
cd backend && uv run pytest -x tests/test_pomodoros_api.py -q
24 passed in 0.31s

cd backend && uv run pytest -q
70 passed in 0.71s  (기존 65 + 신규 5, 0 실패)
```

---

## 점수

| 축 | 점수 | 근거 |
|----|------|------|
| 사양 충족 | 3 | 스키마·상수·라우트·핸들러 로직·테스트 수 전부 acceptance 충족 |
| 모듈 경계 | 3 | 스키마→schemas/, 핸들러→routers/, 테스트→tests/ 정위치, main.py 무수정 |
| 테스트 충실도 | 3 | 의무 5건 전부 통과, 모든 브랜치(없음/1회/4회/break 후/폐기 후) 완전 커버 |
| 운영 고려 | 3 | /next-phase 정적 라우트 동적 /{id} 앞에 배치, 항상 200, id 기반 카운트 단순화 |
| **합계** | **12** | |

## 판정: **PASS**

---

## 세부 평가

### 사양 충족 (3/3)

- `backend/app/schemas/pomodoro.py:6-8`: `PomodoroNextPhase(BaseModel)` — `phase: Literal["focus","short_break","long_break"]`, `planned_duration_sec: int` 두 필드 모두 정확히 일치.
- `backend/app/routers/pomodoros.py:12-14`: 상수 `_FOCUS_SEC=1500`, `_SHORT_BREAK_SEC=300`, `_LONG_BREAK_SEC=900` 모듈 상단 위치 ✓.
- `backend/app/routers/pomodoros.py:50-78`: 핸들러 로직이 TASKS.md 명세 pseudocode와 1:1 일치 — (a) 세션 없음 → focus, (b) focus+completed → last_long_id 이후 완주 count % 4==0이면 long_break, 아니면 short_break, (c) 그 외 → focus.
- 활성 세션 유무 무관 항상 200 응답: 404 분기 없음 ✓.
- 신규 테스트 5건 + 기존 65건 회귀 0 ✓.

### 모듈 경계 (3/3)

- `backend/app/schemas/pomodoro.py` — 신규 Pydantic 스키마 정위치(schemas 레이어) ✓.
- `backend/app/routers/pomodoros.py` — 라우트·핸들러 집중(routers 레이어) ✓.
- `backend/tests/test_pomodoros_api.py` — 테스트 정위치 ✓.
- `backend/app/main.py` 무수정(router 이미 등록됨) ✓.
- 프론트엔드 전체 무수정(M4-4b/c로 이월) ✓.
- 다른 백엔드 라우터/모델/서비스 무수정 ✓.

### 테스트 충실도 (3/3)

의무 5건이 TASKS.md 명세 브랜치를 완전 커버:

| # | 테스트 함수 | 검증 브랜치 | 위치 |
|---|---|---|---|
| 20 | `test_next_phase_empty_db` | 세션 없음 → focus(1500) | :232 |
| 21 | `test_next_phase_after_one_focus_completed` | focus 완주 1회 → short_break(300) | :240 |
| 22 | `test_next_phase_after_four_focus_completed` | focus 완주 4회 → long_break(900) | :253 |
| 23 | `test_next_phase_after_break_completed` | break 완주 후 → focus(1500) | :267 |
| 24 | `test_next_phase_after_focus_abandoned` | focus 폐기(abandoned) 후 → focus(1500) | :282 |

- `test_next_phase_empty_db`가 라우트 등록 순서 회귀(next-phase를 정수 pomodoro_id로 오매핑하면 422가 아닌 200)도 자연 검증 ✓.
- 권장(강제 아님) 회귀 테스트 "long_break 후 다시 focus 4회 → long_break" 미포함. TASKS.md에서 "추가(권장 — 강제 아님)"으로 명시했으므로 감점 없음.

### 운영 고려 (3/3)

- `routers/pomodoros.py:50` — `/next-phase` 정적 라우트가 `/{pomodoro_id}/end`(line 81)보다 먼저 등록 → FastAPI 매칭 순서 안전 ✓.
- 핸들러 내부 DB 조회 2~3회 targeted select + count. lazy load N+1 없음 ✓.
- `scalar_one_or_none() or 0` 패턴(line 66)으로 long_break 없는 경우 0 처리 간결 ✓.
- `_FOCUS_SEC/_SHORT_BREAK_SEC/_LONG_BREAK_SEC` 상수가 모듈 상단 집중 → M5-3 settings 테이블 도입 시 이 세 상수만 DB 조회로 교체하면 됨 ✓.
- SQLite 단일 프로세스 환경에서 id 기반 카운트 단순화는 race 안전 ✓.

---

## 다음 사이클로 넘기는 메모

본 사이클은 PASS이므로 블로킹 이슈 없음. 다음 사이클(M4-4b) Planner를 위한 참고 메모:

1. **권장 회귀 테스트 추가 권고**: `test_next_phase_after_long_break_resets_count` — long_break 종료 후 다시 focus 4회 완주 시 long_break 응답이 나오는지 검증. `last_long_id` 기준 카운트 리셋 작동을 직접 증명. M4-4b acceptance에 흡수 권장.
2. **API 클라이언트 신규 함수 필요**: `frontend/src/api/pomodoros.ts`에 `getNextPhase(): Promise<{phase, planned_duration_sec}>` 함수 추가 필요(현재 미존재). M4-4b 시작 시 이 함수를 먼저 추가.
3. **확장 포인트 명시**: M5-3 settings 테이블 도입 시 `routers/pomodoros.py`의 `_FOCUS_SEC/_SHORT_BREAK_SEC/_LONG_BREAK_SEC` 세 상수를 DB 조회로 교체하면 됨. 별도 서비스 레이어 분리는 그 시점에 검토.

---

# REVIEW — M4-3d

**사이클**: M4-3d — 새로고침 복원 만료 자동 처리 + handleStartPomodoro catch 블록 보강
**평가일**: 2026-05-06
**테스트 결과**: 58 passed / 0 failed (vitest)
**빌드**: vite build → 0 에러 (154 kB)

---

## 점수

| 축 | 점수 | 근거 |
|----|------|------|
| 사양 충족 | 3 | 모든 acceptance 항목 통과 |
| 모듈 경계 | 3 | 레이어 경계 위반 없음 |
| 테스트 충실도 | 3 | 신규 4건, 엣지케이스 누락 없음 |
| 운영 고려 | 3 | finally 보장, unhandled rejection 해소 |
| **합계** | **12** | |

## 판정: **PASS**

---

## 세부 평가

### 사양 충족 (3/3)

TASKS.md M4-3d acceptance 전 항목 확인됨.

- `PomodoroTimer.tsx:7` — `onExpire?: () => void` prop 추가 ✓
- `PomodoroTimer.tsx:12` — `const firedRef = useRef(false)` 신설 ✓
- `PomodoroTimer.tsx:18-23` — `useEffect([remainingSec, onExpire])` 내부에서 조건 충족 시 1회만 발화 ✓
- `ActivePomodoroBanner.tsx:14` — `<PomodoroTimer key={active.id} … onExpire={onExpire} />` 패스스루 + 리마운트 보장 ✓
- `App.tsx:28-35` — 마운트 만료 분기(`Date.parse + planned_duration_sec * 1000 <= Date.now()`) 구현 ✓
- `App.tsx:89-98` — `handlePomodoroExpire` 핸들러 신규, `finally`에서 `setActivePomodoro(null)` ✓
- `App.tsx:144` — `<ActivePomodoroBanner onExpire={handlePomodoroExpire} />` 연결 ✓
- `App.tsx:68-86` — `handleStartPomodoro` catch 블록 inner try/catch 보강 완료 ✓
- `App.test.tsx:416-449` — 마운트 만료 자동 종료 통합 테스트 ✓
- `App.test.tsx:451-498` — 진행 중 만료 통합 테스트 ✓
- `App.test.tsx:500-537` — catch 블록 보강 통합 테스트 ✓
- `PomodoroTimer.test.tsx:47-68` — `onExpire` 1회 발화 테스트 ✓

### 모듈 경계 (3/3)

- `frontend/src/features/pomodoro/PomodoroTimer.tsx` — 순수 표시 컴포넌트 유지. API 호출 없음 ✓
- `frontend/src/features/pomodoro/ActivePomodoroBanner.tsx` — props 패스스루만 담당, 비즈니스 로직 없음 ✓
- `App.tsx` — 도메인 오케스트레이션(`endPomodoro` 호출)을 상위 컴포넌트에서 일관되게 처리 ✓
- 백엔드 변경 없음 — touch 목록과 일치 ✓
- PLAN.md 모듈 책임 구조(`frontend/src/features/pomodoro/`, `frontend/src/hooks/`) 준수 ✓

### 테스트 충실도 (3/3)

신규 4건이 acceptance의 모든 시나리오를 커버함:

1. **`PomodoroTimer.test.tsx:47`** — `remaining <= 0` 도달 후 추가 tick에도 `onExpire` 1회만 호출. `vi.useFakeTimers()` + `act` 조합으로 비동기 훅 동작 정확 검증.
2. **`App.test.tsx:416`** — 마운트 시 31분 전 세션(1500초 초과) → `POST /api/pomodoros/20/end` 자동 호출 + 배너 미표시 검증.
3. **`App.test.tsx:451`** — `vi.useFakeTimers({ toFake: ['Date', 'setInterval', 'clearInterval'] })`로 `setTimeout` 제외하여 `findByTestId`가 정상 동작하도록 구성. 3초 advance → onExpire 발화 → 배너 unmount 검증.
4. **`App.test.tsx:500`** — 409 후 `GET /api/pomodoros/active` 500 실패 → `task-error` 표시 + 다이얼로그 미표시 검증.

기존 54건 회귀 0.

### 운영 고려 (3/3)

M4-3c REVIEW에서 지적한 catch 블록 unhandled rejection 경로가 완전히 해소됨:

- `App.tsx:29-35` — 마운트 만료 `endPomodoro` 호출을 try/catch로 감싸고, `finally`에서 항상 `setActivePomodoro(null)` 수행. 서버 실패 시에도 만료 세션이 계속 표시되는 상황 방지 ✓
- `App.tsx:89-98` — `handlePomodoroExpire`도 동일 패턴(`finally`에서 `setActivePomodoro(null)`) ✓
- `App.tsx:69-82` — `handleStartPomodoro` 내부 중첩 await(`getActivePomodoro`/재시도 `startPomodoro`)를 단일 try/catch 블록으로 감싸 실패 시 `setError` + 상태 초기화 ✓
- `App.tsx:90` — `if (!activePomodoro) return;` 가드로 stale closure 방지 ✓
- `PomodoroTimer.tsx:12` — `firedRef.current = true` 중복 발화 방지 ✓
- `ActivePomodoroBanner.tsx:14` — `key={active.id}`로 새 세션 시작 시 `firedRef` 자연 리마운트·초기화 ✓

---

## 다음 사이클로 넘기는 메모

본 사이클은 PASS이므로 블로킹 이슈는 없습니다. 다음 사이클 Planner를 위한 참고 메모:

1. **M4-4 분리 처리**: `handlePomodoroExpire`는 현재 단순 종료(`endPomodoro` + `setActivePomodoro(null)`)까지만 구현됨. focus→short_break 자동 전환, 4세션마다 long_break, 휴식 후 "다음 집중 묻기" 다이얼로그는 M4-4에서 `handlePomodoroExpire`를 확장하는 방식으로 구현하는 것이 자연스러움.

2. **백로그 잔존 UX 이슈**: `TaskFilters.tsx` 태그 입력 trailing comma 점프(M3-2b-followup-A)는 여전히 미처리. M4 이후 UX 사이클에서 처리 권장.

3. **ESLint 미설정**: `M1-2-followup-A`(`frontend/eslint.config.js`) 백로그 잔존. 빌드/테스트에는 영향 없으나, 코드 품질 자동화를 위해 M5 이전 처리 권장.
