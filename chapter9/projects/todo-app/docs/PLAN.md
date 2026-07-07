# PLAN: todo-app (뽀모도로 할일 관리 웹 도구)

PRD.md를 기준으로 한 구현 계획이다. 현재 코드는 없으며(문서만 존재),
스캐폴딩부터 시작한다.

## 아키텍처 개요

- Vite + React + TypeScript 정적 앱. 백엔드 없음.
- 상태는 React 내장 기능(useState/useReducer/useEffect)만 사용.
- 저장은 `localStorage` 단일 계층. 저장/로드는 전용 모듈로 격리하여
  파싱 실패·용량 초과를 한곳에서 처리한다.
- 순수 로직(정렬, 필터, 경과 시간 계산, 포맷)은 컴포넌트에서 분리해
  Vitest로 단위 테스트한다.

### 모듈 책임 (초안)

- `src/types.ts` — Todo, Session, TimerState, 저장 스키마 타입
- `src/storage/` — localStorage 로드/저장, 스키마 버전, 손상 처리
- `src/constants.ts` — 타이머 시간(25/5/15분), 스키마 버전
- `src/hooks/` — 타이머 진행·복원, 데이터 상태 훅
- `src/components/` — 할일 목록/입력, 타이머, 알림, 타임라인, 저장 경고 배너
- `src/lib/` — 순수 함수(필터, 포맷, 경과 계산)
- `src/lib/timer.ts` — 타이머 순수 로직(경과·남은 시간 계산, mm:ss 포맷,
  완료 판정). `constants.ts`의 FOCUS/BREAK 시간 상수를 재사용

## 마일스톤

### M1. 프로젝트 스캐폴딩 & 저장 계층

- [x] Vite + React + TS + Vitest 초기화, 빌드/테스트 파이프라인 구동
- [x] 데이터 모델 타입 정의(`types.ts`), 상수(`constants.ts`)
- [x] localStorage 로드/저장 모듈: 스키마 버전 필드, 파싱 실패 시 손상
      항목 무시, 쓰기 실패 감지

### M2. 할일 관리

- [x] 저장 계층 테스트 충실도 보강(REVIEW 메모: 구조 불일치 케이스, 스키마
      버전 보존 실질 검증) — T3 PASS(12/12)
- [x] 할일 상태 훅(`useTodos`): localStorage 로드/저장 연동, 추가/수정/삭제/완료 체크
- [x] 할일 목록/입력 UI 컴포넌트(`useTodos` 연결). `@testing-library/react`
      도입, `useTodos` wiring 회귀 테스트 추가 — T5 PASS(30케이스)
- [x] 태그 다중 부착·제거(할일별 태그 편집 UI, 순수 함수·훅 액션) — T6
      PASS(13/15). 순수 함수·훅 액션·`TodoItem` 태그 UI 완성, REVIEW 메모1
      (인라인 편집 분기 회귀)·메모2(`persist` 부수효과 `useEffect` 분리) 해소.
      단 실제 앱 배선이 없어 실행 화면에서는 태그 부착·제거가 미동작 → T8로 이관.
- [x] 태그 액션 앱 배선(`App`→`TodoList`→`TodoItem`), optional props 필수화,
      `App` 통합 시나리오 테스트 — T8 PASS(15/15, 46케이스). `TodoItem`의
      `onAddTag`/`onRemoveTag`를 required로 전환하고 기존 테스트 케이스를 보정,
      실행 앱에서 태그 부착·제거가 통합 테스트로 실증됨.
- [x] 태그 기준 필터링(선택 태그의 할일만 표시) — T7 PASS(58케이스). `TagFilter`
      컴포넌트와 `filterByTags`/`collectTags` 순수 함수(OR 방식)로 `App`에서
      필터 상태를 관리, 표시에만 영향(저장 데이터 불변).
- [x] 할일별 완료 뽀모도로 누적 횟수 표시(T12). T10의 `countCompletedPomodoros`와
      T11이 `App`에 배선하는 `sessions`를 소비해 각 할일 옆에 완료 횟수를 표시
- [x] 기본 정렬은 생성 순서(`createdAt`) — `sortByCreatedAt`으로 T4에서 확정

### M3. 뽀모도로 타이머

- [x] 타이머 순수 로직(`lib/timer.ts`): 경과·남은 시간 계산, mm:ss 포맷,
      완료 판정. 남은 시간은 0으로 클램프, 완료는 경과 ≥ duration — T9 PASS(11케이스)
- [x] `useTimer` 훅(T10): 할일 클릭 시 집중 타이머 시작, 동시 1개만 진행
      (다른 할일 클릭 시 확인 후 기존 타이머 중단), `timerState` 저장·복원.
      복원 시 `startedAt` 비유효(NaN) 검증으로 폐기 — T10 PASS(9케이스).
      저장 일관성은 `persist`가 매번 `loadData()` 최신 스냅숏을 읽어 `timerState`/
      `sessions`만 교체하는 방식으로 확보(자체 결정).
- [x] 집중 완료 시 `Session`(result='completed') 기록·카운트 +1,
      중단 시 `Session`(result='aborted') 기록·카운트 미포함 — T10에 통합, PASS.
      완료 판정은 훅 내부 1초 `setInterval`+`isComplete`로 자동 처리,
      완료 세션 카운트 집계 순수 함수(`countCompletedPomodoros`)로 실증.
      화면 표시는 M2 잔여(T12)로 분리.
- [x] 타이머 UI 배선(T11, 할일 클릭 시작, 진행 표시, 중단 확인) 및 진행 중
      탭 제목에 남은 시간 표시(`(12:34) todo-app`). `useTimer`를 `App`에
      배선하는 통합 항목이므로, REVIEW T10 메모2의 마운트 경쟁 조건(현재
      `useTodos.ts:17-19`가 마운트 시 무조건 `saveData(data)`를 수행해
      `useTimer`의 복원·자동완료 기록을 덮어써 completed 세션이 유실될 수 있음)을
      함께 해소한다. 저장 일관성(두 훅이 같은 트리에서 마운트돼도 `todos`와
      `sessions`가 서로를 훼손하지 않음)을 직접 검증하는 테스트(REVIEW T10
      메모1)를 추가한다.

### M4. 휴식 타이머 & 알림

- [x] T13. 타이머 타입별 지속시간 처리 확장(휴식 타이머 기반 마련). 현재
      `useTimer`는 tick·복원 완료 판정에 `FOCUS_DURATION_MS`를 하드코딩해
      focus만 처리한다. 순수 함수 `durationForType(type)`·`nextBreakType(
      completedFocusCount)`를 추가하고, `useTimer`의 완료 판정을 타입별
      duration으로 일반화하며 `start(todoId, type)`로 휴식 타이머 시작을
      지원한다. 휴식 완료 세션은 기록하되 완료 뽀모도로 카운트에는 영향이
      없어야 한다(`sessions.ts`가 focus만 집계). 화면 무(로직·훅).
- [x] T14a. 타이머 종료 시 화면 내 알림 배너 + `App` duration 일반화.
      타이머(focus 또는 이후 휴식)가 완료되면 화면에 종료 알림 배너를 표시하고
      사용자가 닫을 수 있게 한다. 완료 신호는 `useTimer`가 노출하지 않으므로,
      `sessions`에 새 `completed` 세션이 추가된 것을 관찰하거나 `useTimer`에
      최소 신호를 추가해 감지한다(방식은 Generator 자체 결정). 아울러
      `App.tsx`의 남은 시간·탭 제목 계산이 `FOCUS_DURATION_MS`를 하드코딩한
      부분(`App.tsx:27`)을 `durationForType(timerState.type)` 기반으로
      일반화해 T14b의 휴식 배선을 선제 대비한다(focus 회귀 없음). REVIEW T12
      메모3(aborted 세션이 통합 레벨에서 완료 카운트에 포함되지 않음을 직접
      assert)을 이 항목의 중단 흐름 통합 테스트로 해소한다.
- [x] T14b. 집중 완료 후 휴식 제안 UI(짧은 휴식 5분, 4회마다 긴 휴식 15분)와
      건너뛰기(강제하지 않음). T13이 마련한 `nextBreakType`로 다음 휴식 타입을
      정하고 `start(todoId, type)`(focus/휴식 공용)를 `App`에 배선해 focus
      완료 시 제안 상태를 표시하며, 사용자가 휴식 시작 또는 건너뛰기를 선택한다.
      REVIEW T13 메모1(완료 0회에는 휴식 제안이 뜨지 않음을 호출부가 보장)과
      메모2(longBreak 훅/통합 경로)를 통합 테스트로 함께 검증한다. REVIEW T14a
      메모2(휴식 시작/건너뛰기 시 이전 완료 배너 `alertSession` 잔존 방지)도
      전이 시 초기화로 해소한다. `nextBreakType`에 넘길 완료 횟수는 전체 focus
      완료 세션 수로 집계한다(PRD 3.3 "뽀모도로 4회 완료마다"의 전역 해석,
      자체 결정·되돌리기 쉬움).

### M5. 기록 / 타임라인

- [x] 세션 시작/종료 시각, 대상 할일, 결과(완료/중단) 기록 — T15
- [x] T16. 타임라인 화면 시간순 조회 + "중단" 표시(PRD 3.4 둘째 항목).
      `App`이 이미 보유한 `sessions`를 시작 시각 기준 최신순(내림차순, 자체
      결정·되돌리기 쉬움)으로 정렬하는 순수 함수(`lib/sessions.ts`에
      `sortSessionsByStartedAtDesc` 추가)와 `components/Timeline.tsx`를 신설해
      각 세션의 시작/종료 시각·대상 할일 제목·타입(집중/휴식)·결과(완료/중단)를
      목록으로 표시한다. 대상 할일 제목은 `todos`에서 `todoId`로 매핑하되
      삭제된 할일은 폴백 라벨("(삭제된 할일)")로 표시해 조회가 깨지지 않게
      한다. `App`에서 `sessions`·`todos`를 `Timeline`에 전달만 하고 집계·정렬
      로직은 순수 함수에 둔다. focus 세션 tick 자동 완료의 완료(`completed`)와
      중단(`aborted`)이 각각 "완료"/"중단"으로 구분 표시됨을 통합 테스트로
      실증한다(REVIEW T15 메모1 해소).

### M6. 실패 정책 & 복원

PRD 5장(실패 정책)을 세션 크기로 분해한다. 복원 로직은 이미
`useTimer.ts:52-73`에 존재하나 App 통합 검증이 없고, 읽기/쓰기 실패
경고 배너는 미구현이다. `storage/index.ts`는 이미 `corrupted` 플래그와
`SaveResult.ok`를 반환하지만 어떤 훅도 소비하지 않는다.

- [x] T18. localStorage 읽기·파싱 실패 시 경고 배너 + 빈 상태 시작(PRD 5
      둘째 항목). `storage.loadData`가 이미 반환하는 `corrupted` 플래그를
      `useTodos`가 노출하고, `App`이 이를 구독해 신규
      `components/StorageWarningBanner.tsx`로 경고 배너를 표시한다. 손상
      데이터는 `loadData`가 이미 `createEmptyData()`로 대체하므로 빈 상태
      시작은 보장되며, 통합 테스트로 실증한다. 이 항목에서 세우는 경고
      배너 인프라(App 경고 상태 + 배너 컴포넌트)를 T19가 재사용한다.
- [x] T19. localStorage 쓰기 실패(용량 초과 등) 시 경고 표시 + 메모리 상태
      지속(PRD 5 셋째 항목). `saveData`가 반환하는 `SaveResult.ok`를 두 쓰기
      경로(`useTodos.ts:24`의 `useEffect([data])` `saveData(data)`,
      `useTimer.ts:35`의 `persist` 콜백 `saveData(next)`)가 모두 소비해
      실패를 `App` 경고 상태로 전파하고, T18의 배너 인프라로 표시한다. 저장
      실패해도 메모리 상태(React state)로 계속 동작함을 통합 테스트로
      실증한다. REVIEW T18 메모1대로 `StorageWarningBanner`는 문구가
      하드코딩되어 있으므로, 쓰기 실패용 문구("저장에 실패했으나 현재
      상태는 유지됩니다" 계열)를 위해 `variant`/`message` props로 일반화하거나
      별도 배너로 분리한다(Generator 자체 결정, 되돌리기 쉬움). 읽기 손상
      배너와 쓰기 실패 배너의 동시 표시 배치도 함께 결정한다.
- [x] T17. 새로고침/종료 시 `startedAt` 기반 경과 복원 App 통합 검증(PRD 5
      첫째 항목). 복원 판정 로직은 `useTimer.ts:52-73`에 이미 존재하고
      단위 테스트로 커버되나, 손상된 localStorage에 진행 중 `timerState`를
      심고 `App` 마운트 시 (a) 25분 미경과면 남은 시간을 이어서 표시,
      (b) 25분 초과면 완료 처리 후 종료 배너 표시(REVIEW T14a 메모: 마운트
      복원 완료 시 배너 경로 미검증 해소)를 App 통합 테스트로 실증한다.
- [x] T20. `timerState` 필드 단위 검증 정밀화 + `nextBreakType(0)`·음수
      경계 계약 고정(화면 무, 순수/저장 계층). (1) `storage.isValidStorageData`
      의 `timerState` 검증이 `typeof === 'object'`만 확인해 배열도 통과하는
      문제와 `useTimer.isValidTimerState`가 `startedAt`만 검증하는 문제를
      `todoId`/`type`/`startedAt` 필드 단위로 정밀화한다. (2) `nextBreakType`
      의 0·음수 입력 계약을 명시하고 테스트로 고정한다(REVIEW T15·T16 메모
      이월. 현재 호출부에서 도달 불가라 실질 결함은 없으나 계약 명시로 정리).

## 미해결 의사결정

run.py의 합의를 대기 중인 항목이다. 이번 사이클에는 PRD에 반영하지 않는다.

- 할일 순서 변경 방식: `docs/decisions/todo-reorder.md` (Planner 선택: A, v1 제외)
- 집중/휴식 시간 커스터마이즈: `docs/decisions/timer-durations.md` (Planner 선택: A, 고정)
