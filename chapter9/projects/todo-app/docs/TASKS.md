# TASKS

각 항목은 한 세션(약 10~20분) 크기다. M1(스캐폴딩 & 저장 계층)은 T1/T2
PASS로 완료되었다. T3~T14b까지 완료되어 M2(할일 관리)·M3(뽀모도로 타이머)·
M4(휴식 타이머 & 알림) 마일스톤이 모두 완료되었다. T15·T16으로 M5(기록/
타임라인) 마일스톤도 모두 완료되었다. T17~T20으로 M6(실패 정책 & 복원)도
모두 완료되었다. PLAN.md에 정의된 마일스톤 항목은 모두 완료 상태다.

## 다음 (진행 대상)

(없음. PLAN.md의 마일스톤 항목이 모두 완료되었다. "대기 (후속 사이클)"
섹션은 REVIEW에서 이월된 선택 항목으로, 필수 항목이 아니다.)

## 완료

- T20. `timerState` 필드 단위 검증 정밀화 + `nextBreakType(0)`·음수 경계
  계약 고정(REVIEW T15·T16 메모 이월) — 완료, PASS(145케이스). `storage/
  index.ts`의 `isValidStorageData`가 `timerState`를 `typeof === 'object'`로만
  확인해 배열·필드 누락 객체도 통과하던 문제를 `isValidTimerStateShape`
  (신설)로 정밀화: `todoId`(string)·`type`(유효 `SessionType`, `isValidSessionType`
  신설)·`startedAt`(string) 필드를 단위로 검증(배열은 `Array.isArray` 배제로
  거부). `useTimer.ts`의 `isValidTimerState`도 동일한 필드 단위 검증(todoId/
  type/startedAt 타입)에 기존 `startedAt` NaN 검사를 더해 정밀화(storage
  계층과 별개로 복원 폐기 경로의 방어를 이중화). `lib/timer.ts`의
  `nextBreakType`은 코드 변경 없이 현재 동작(`0 % 4 === 0` → `longBreak`,
  음수는 JS 나머지 연산 부호를 그대로 따름)을 테스트로 계약 고정.
  `storage.test.ts`에 timerState 배열·필드 누락(todoId)·유효하지 않은
  `type`·startedAt 타입 불일치 4개 거부 케이스와 정상 통과 1개 케이스 추가.
  `useTimer.test.ts`에 todoId 누락·유효하지 않은 type 2개 복원 폐기 케이스
  추가(이 두 경우는 storage 계층에서 이미 전체 구조가 corrupted 처리되어
  `sessions`까지 빈 배열로 시작함을 확인 — 기존 startedAt-NaN 케이스는
  storage 계층 필드 타입 검사를 통과하는 값이라 useTimer 자체 검증이
  실제로 동작해 `sessions`는 보존됨). `timer.test.ts`에 `nextBreakType(0)`
  및 음수(-1~-3 shortBreak, -4/-8 longBreak) 계약 케이스 추가. 전체
  `npx vitest run`(145케이스)·`npx tsc --noEmit`·`npm run build` 모두 종료 0.

- T17. 새로고침/종료 시 `startedAt` 기반 경과 복원 App 통합 검증(PRD 5
  첫째 항목, M6) — 완료, PASS(132케이스). 복원 판정 로직(`useTimer.ts:52-73`)은
  이미 존재해 프로덕션 코드 변경 없이 `App.test.tsx`에 통합 테스트 2건만
  추가. `vi.useFakeTimers()` + `vi.setSystemTime`으로 기준 시각을 고정한 뒤
  localStorage에 `todos`·`timerState`(`startedAt`)를 직접 심고 마운트해
  (a) 10분 경과(25분 미경과)면 남은 시간 "15:00"이 이어서 표시되고 "중단"
  버튼이 나타남을, (b) 26분 경과(25분 초과)면 마운트 시 즉시 완료 세션이
  기록되고("완료 1회") 종료 알림 배너("집중 타이머가 종료되었습니다.")가
  표시되며 저장소의 `timerState`가 `null`로, `sessions`에 `result:
  'completed'` 세션이 추가됨을 검증(REVIEW T14a 메모 해소).
- T19. localStorage 쓰기 실패(용량 초과 등) 시 경고 표시 + 메모리 상태 지속
  (PRD 5 셋째 항목, M6) — 완료, PASS(130케이스). `useTodos`의 마운트 후
  `saveData(data)` 호출과 `useTimer`의 `persist` 내부 `saveData(next)` 호출
  모두 `SaveResult.ok`를 소비해 각 훅이 `saveFailed` boolean을 반환하도록
  확장. `App`은 두 훅의 `saveFailed`를 OR로 합쳐 `writeFailed`로 구독한다.
  설계 판단(자체 결정, 되돌리기 쉬움): `StorageWarningBanner`를 `variant:
  'corrupted' | 'writeFailure'` required prop으로 일반화(별도 배너 분리
  대신 문구 테이블 방식 선택 — 배너 구조·스타일이 완전히 동일해 컴포넌트
  중복이 불필요). 두 배너(읽기 손상·쓰기 실패)는 동시에 뜰 수 있으며 배치는
  `corrupted` 배너를 먼저, `writeFailure` 배너를 그다음에 순서대로 표시(자체
  결정, 되돌리기 쉬움). `App.test.tsx`에 `localStorage.setItem`을 스텁해
  예외를 던지도록 한 뒤(기존 `storage.test.ts`와 동일한 방식) 할일 추가 시
  쓰기 실패 배너 표시 + 추가한 할일이 화면에 계속 표시됨(메모리 상태 유지)을
  검증하는 통합 테스트, 정상 저장 시 배너 미표시 회귀 테스트를 추가.
  `StorageWarningBanner.test.tsx`에 두 variant의 문구가 서로 다름을 검증하는
  케이스를 추가.
- T18. localStorage 읽기·파싱 실패 시 경고 배너 + 빈 상태 시작(PRD 5 둘째
  항목, M6) — 완료, PASS(127케이스). `useTodos`가 마운트 시 `loadData()`의
  전체 `LoadResult`를 `useState` 초기값으로 한 번만 캡처해 `corrupted`
  플래그를 훅 반환값으로 노출(이후 `persist`의 재조회 `loadData().data`는
  무변경). `App`이 `corrupted === true`일 때만 신규
  `components/StorageWarningBanner.tsx`를 렌더링하며, 배너는 자체
  `dismissed` state로 닫기 버튼 클릭 시 스스로 사라진다(부모 상태 불필요).
  `storage.test.ts`에 빈 상태(raw `null`)에서 `corrupted`가 `false`임을
  검증하는 케이스를 추가해 acceptance 공백을 메움. `App.test.tsx`에 JSON
  파싱 실패·스키마 불일치(`todos`가 배열 아님) 두 경로 모두 경고 배너 표시
  + 빈 상태 시작(체크박스 없음)을 검증하는 통합 테스트, 정상 데이터에서는
  배너가 뜨지 않는 회귀 테스트를 추가.
- T16. 타임라인 화면 시간순 조회 + "중단" 표시(PRD 3.4 둘째 항목, M5 잔여)

- T16. 타임라인 화면 시간순 조회 + "중단" 표시(PRD 3.4 둘째 항목, M5 잔여)
  — 완료, PASS(121케이스). `lib/sessions.ts`에 `sortSessionsByStartedAtDesc`
  (시작 시각 내림차순, 안정 정렬) 추가. 신규 `components/Timeline.tsx`가
  각 세션의 시작~종료 시각(`HH:mm`)·대상 할일 제목·타입(집중/휴식)·결과를
  목록으로 표시하며, 완료는 "완료", 중단은 "중단"으로 구분. 대상 할일 제목은
  `todos`에서 `todoId`로 매핑하고 삭제된 할일은 "(삭제된 할일)" 폴백 라벨로
  표시. `App`은 `sessions`·`todos`를 `Timeline`에 전달만 하고 집계·정렬
  로직은 갖지 않음. `App.test.tsx`에 focus 자동 완료 후 "완료" 항목, 진행
  중 `stop()` 중단 후 "중단" 항목이 타임라인에 나타남을 검증하는 통합
  테스트를 추가해 REVIEW T15 메모1을 해소.

- T15. 세션 시작/종료 시각, 대상 할일, 결과(완료/중단) 기록(PRD 3.4) — 완료,
  PASS(110케이스). `useTimer.ts`의 `createSession`이 T10/T11에서 이미
  완료·전환중단·`stop()` 중단 세 경로 모두에서 `startedAt`/`endedAt`/
  `todoId`/`type`/`result`를 기록하고 있어 신규 프로덕션 코드 변경은
  없음. `useTimer.test.ts`의 완료 케이스와 `stop()` 중단 케이스가
  `result`/`todoId`만 검증하고 `startedAt`/`endedAt` 값은 직접 검증하지
  않던 공백을 메워, 두 테스트에 `startedAt`/`endedAt` 값 assertion을
  추가해 PRD 3.4 요구를 직접 실증했다.
- T14a. 타이머 종료 시 화면 내 알림 배너 + `App` duration 일반화 — 완료,
  PASS(15/15, 102케이스). `useTimer`에 `lastCompletedSession` 신호를 추가해
  완료 시에만 배너를 띄우고(aborted 경로 무영향), `components/TimerAlert.tsx`로
  타입별 한글 라벨 종료 배너·닫기 버튼을 렌더링. `App.tsx`의 남은 시간·탭
  제목 계산에서 `FOCUS_DURATION_MS` 하드코딩을 제거하고
  `durationForType(timerState.type)` 기반으로 일반화. REVIEW T12 메모3(aborted가
  완료 카운트에 미포함)은 신규 App 통합 테스트로 해소.
- T13. 타이머 타입별 지속시간 처리 확장 (휴식 타이머 기반 마련) — 완료,
  PASS(97케이스). `lib/timer.ts`에 `durationForType(type)`(focus/shortBreak/
  longBreak→`constants.ts` 값), `nextBreakType(completedFocusCount)`
  (`LONG_BREAK_INTERVAL`의 배수면 longBreak, 아니면 shortBreak) 추가.
  `useTimer`의 tick·복원 완료 판정을 `durationForType(timerState.type)`
  기반으로 일반화(FOCUS 하드코딩 제거), `start(todoId, type: SessionType =
  'focus')`로 확장해 기존 focus 호출부는 무변경으로 동작. 휴식 완료 세션은
  `completed`로 기록되지만 `sessions.ts`의 `countCompletedPomodoros`가 이미
  `type === 'focus'`만 집계해 추가 변경 없이 카운트에서 제외됨을 테스트로
  실증. `App`·컴포넌트·`constants.ts`·`sessions.ts`는 변경 없음(화면 배선은
  T14).
- T1. 프로젝트 스캐폴딩 (Vite + React + TS + Vitest) — 완료
- T2. 데이터 모델 타입 & localStorage 저장 계층 — 완료
- T3. 저장 계층 테스트 충실도 보강 (직전 REVIEW 메모 해소) — 완료
- T4. 할일 상태 훅 & CRUD (`useTodos`) — 완료
- T5. 할일 목록/입력 UI 컴포넌트 (`useTodos` 연결 + 테스트 라이브러리 도입)
  — 완료, PASS(14/15, 30케이스)
- T6. 태그 다중 부착·제거 (`useTodos` 태그 액션 + `TodoItem` 태그 UI)
  — 완료, PASS(13/15, 45케이스). 실제 앱 배선은 T8로 이관.
- T8. 태그 액션 앱 배선(`App`→`TodoList`→`TodoItem`) + optional props 필수화
  + `App` 통합 시나리오 — 완료, PASS(46케이스). `TodoItem`의 `onAddTag`/
  `onRemoveTag`를 required로 전환, `TodoList`·`App`이 실제로 전달하도록 배선.
- T7. 태그 기준 필터링 UI (선택 태그의 할일만 표시) — 완료, PASS(58케이스).
  `filterByTags`/`collectTags` 순수 함수, `TagFilter` 컴포넌트, `App` 필터
  상태 배선을 추가. 기존 App 테스트 1건이 태그 필터 버튼과 태그 칩의 텍스트
  중복으로 깨져 `getByRole('button', { name: '집중 태그 제거' })` 기반으로
  보정(회귀 아님, 새 UI 요소로 인한 선택자 충돌).
- T9. 타이머 순수 로직(`lib/timer.ts`) — 완료, PASS(11케이스). `elapsedMs`/
  `remainingMs`(0 클램프)/`isComplete`/`formatRemaining`("MM:SS", 음수 0 처리)
  구현. `constants.ts`의 기존 `FOCUS_DURATION_MS` 등을 재사용하고 신규 상수는
  추가하지 않음. 화면·훅 변경 없음(순수 함수만).
- T10. `useTimer` 훅(`timerState`/`sessions` 관리, `start`/`stop`, 마운트 복원·
  NaN 폐기·1초 `setInterval` 자동 완료, `countCompletedPomodoros`) — 완료,
  PASS(11/15, 화면無 기준). 신규 `useTimer.*`·`sessions.*`, `useTodos.ts`의
  `persist`를 `loadData()` 최신 스냅숏 기준 `todos` 교체로 최소 수정. 전체 81케이스
  종료 0. 저장 일관성 직접 검증 테스트 부재·마운트 경쟁 조건 리스크는 T11로 이관.
- T11. 타이머 UI 배선 + 진행 중 탭 제목 — 완료, PASS(84케이스). `App`에 `useTimer`
  배선, `TodoList`/`TodoItem`에 "집중 시작"/"중단" 조작과 남은 시간(`MM:SS`) 표시
  props 추가, 진행 중 `document.title`을 `(MM:SS) todo-app`로 표시 후 중단·완료
  시 `todo-app`로 복원. 선결 과제였던 마운트 경쟁 조건은 `useTodos`에 `useTimer`와
  동일한 `initialized` ref 패턴을 적용해 초기 마운트 시 `saveData` 호출을 건너뛰는
  방식으로 해소(REVIEW T10 메모2 해소). 저장 일관성 검증 테스트(REVIEW T10 메모1)를
  `App.test.tsx`에 추가. `TodoItem.test.tsx`/`TodoList.test.tsx`는 신규 필수 props
  보정만 반영(회귀 아님). 테스트에서 `vi.useFakeTimers()`와 `@testing-library/
  user-event`의 클릭을 함께 쓰면 타임아웃이 발생해, fake timer 구간 클릭은
  `fireEvent.click`으로 대체(자체 결정, 테스트 코드 한정).

- T12. 할일별 완료 뽀모도로 누적 횟수 표시 — 완료, PASS(87케이스). `TodoList`에
  `sessions` prop을 추가해 `countCompletedPomodoros(sessions, todoId)`로 할일별
  완료 횟수를 계산, `TodoItem`에 `completedCount`(required) prop으로 전달해
  "완료 N회" 텍스트로 표시. `App`은 `useTimer`의 `sessions`를 `TodoList`로
  전달만 하고 집계 로직은 갖지 않음.

- T14a. 타이머 종료 시 화면 내 알림 배너 + `App` duration 일반화 — 완료,
  PASS(102케이스). `useTimer`에 `lastCompletedSession`(완료 시에만 갱신되는
  `Session | null`) 신호를 추가해 `completeTimer` 내부에서 세션을 먼저 만든
  뒤 `persist`와 `setLastCompletedSession`에 각각 전달(aborted 경로인 `stop`/
  강제 전환은 건드리지 않아 배너가 뜨지 않음). `App`은 이 신호를 관찰해
  `alertSession` 상태에 반영하고, 신규 `components/TimerAlert.tsx`(및 테스트)
  로 종료 안내 배너와 "닫기" 버튼을 렌더링한다. `App.tsx`의 남은 시간 계산은
  `FOCUS_DURATION_MS` 하드코딩을 제거하고 `durationForType(timerState.type)`
  기반으로 일반화(T14b 휴식 배선 선결 대비). REVIEW T12 메모3(aborted 통합
  assert)은 신규 App 테스트("중단하면 배너 미표시 + 완료 0회 유지")로 해소.

- T14b. 집중 완료 후 휴식 제안 UI(짧은 휴식 5분, 4회마다 긴 휴식 15분) +
  건너뛰기 — 완료, PASS(110케이스). 신규 `components/BreakSuggestion.tsx`(+
  테스트)로 "휴식 시작"/"건너뛰기" 조작이 있는 제안 UI를 신설(기존
  `TimerAlert`는 무변경). `App`에서 `alertSession.type === 'focus'`일 때만
  `nextBreakType(completedFocusCount)`(전체 focus 완료 세션 수, `sessions`를
  App에서 직접 filter — `lib/sessions.ts` 무변경)로 다음 휴식 타입을 계산해
  제안을 표시. "휴식 시작"은 `start(alertSession.todoId, breakType)`을 호출하고
  `alertSession`을 `null`로 초기화(제안·이전 완료 배너 동시에 사라짐, REVIEW
  T14a 메모2 해소), "건너뛰기"는 `alertSession`만 초기화해 새 타이머를 시작하지
  않음. `nextBreakType`/`durationForType`은 기존 export를 그대로 소비.

## 대기 (후속 사이클)

- 선택(REVIEW T19 메모1 이월): `App.tsx:22`의 `writeFailed = todosSaveFailed ||
  timerSaveFailed` 중 `timerSaveFailed`(`useTimer.persist`의 `saveData` 실패)
  분기가 통합 레벨에서 직접 커버되지 않는다(현재 쓰기 실패 통합 테스트는
  `useTodos`의 저장 실패 경로만 경유). 두 훅 배선이 동일 패턴이라 실질 결함은
  없으나, 타이머 진행 중 `saveData` 실패 시 쓰기 실패 배너가 표시되는지
  확인하는 App 통합 케이스 1건을 보강하면 OR 결합의 나머지 분기까지 실증된다.
- 선택(REVIEW 이월): 필터 활성 중 마지막 태그 제거 시 `selectedTags` 잔존으로
  목록이 빈 상태 고정되는 데드 상태 정리(사양 밖), App 통합 다중 태그 OR 케이스 보강.
- 선택(REVIEW T16 메모1 이월): 타임라인 시각 `HH:mm` 날짜 생략으로 다일
  누적 시 구분 어려움. 날짜 헤더 또는 상대 표기 검토(사양 밖).
- 선택(REVIEW T17 메모1 이월): App 통합에서 정확히 25분 경과 경계값
  (`elapsed === duration`) 마운트 복원 케이스 미포함. `isComplete` 경계는
  `lib/timer.ts` 단위 테스트로 커버되어 실질 공백은 아니나, 통합 경계 케이스
  1건을 보강하면 복원 완료 판정의 통합 계약이 더 명확해진다.
