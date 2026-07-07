# IMPL: T20 — `timerState` 필드 단위 검증 정밀화 + `nextBreakType` 경계 계약 고정

## 처리한 항목

T20 (docs/TASKS.md, M6 잔여). REVIEW T15·T16 메모 이월 건.

## 변경 파일

- `src/storage/index.ts` — `isValidSessionType`(신설)·`isValidTimerStateShape`
  (신설)를 추가해 `isValidStorageData`의 `timerState` 검증을
  `typeof === 'object'`(배열도 통과하던 결함)에서 `todoId`(string)·
  `type`(유효 `SessionType`)·`startedAt`(string) 필드 단위 검증으로 정밀화.
- `src/storage/storage.test.ts` — timerState 배열·todoId 누락·유효하지 않은
  type·startedAt 타입 불일치 4개 거부 케이스, 필드를 모두 갖춘 정상
  timerState 통과 케이스 1개 추가.
- `src/hooks/useTimer.ts` — `isValidSessionType`(신설, storage 계층과 동일
  로직을 훅 계층에서도 독립적으로 방어) 추가. `isValidTimerState`가
  `startedAt` NaN 검사만 하던 것을 `todoId`/`type`/`startedAt` 필드 단위
  검증 + 기존 NaN 검사로 정밀화.
- `src/hooks/useTimer.test.ts` — todoId 누락, 유효하지 않은 type 2개 복원
  폐기 케이스 추가.
- `src/lib/timer.test.ts` — `nextBreakType(0)`(longBreak), 음수 입력(-1~-3
  → shortBreak, -4/-8 → longBreak) 계약 고정 케이스 추가. `lib/timer.ts`
  프로덕션 코드는 변경 없음(현재 동작이 이미 일관적이라 방어 코드 불필요).

## 결정 사항

- `nextBreakType`은 코드를 바꾸지 않고 현재 동작을 테스트로 계약 고정만
  했다. 현 호출부(`App.tsx`)는 항상 1 이상의 완료 카운트만 전달해 0/음수
  입력에 실질적으로 도달하지 않으며, PLAN.md도 "코드 변경은 최소로 한다"를
  명시했다. JS 나머지 연산 규칙(`n % 4`가 음수 배당이면 0 또는 음수를
  반환)을 그대로 계약으로 채택했다: 0과 -4/-8(절댓값이 `LONG_BREAK_INTERVAL`
  의 배수)은 `longBreak`, -1~-3은 `shortBreak`.
- storage 계층의 `isValidStorageData`는 기존 설계(todos/schemaVersion 등
  단일 필드라도 무효면 전체 구조를 corrupted로 판정)와 동일하게, timerState
  필드 검증도 실패 시 전체 `StorageData`를 무효로 판정하도록 유지했다(개별
  필드만 골라내는 부분 복구는 하지 않음 — 기존 정책과 일관).
- `useTimer.ts`의 `isValidTimerState`는 storage 계층 검증과 로직이
  겹치지만, PLAN이 명시한 대로 훅 계층에서 독립적인 방어선을 유지했다.
  실제로 두 계층의 역할은 다르다: storage 계층은 JSON 구조 전체의 무결성을
  판정(무효 시 `sessions`/`todos`까지 초기화)하고, 훅 계층은 구조적으로는
  유효하지만 의미적으로 무효한 값(`startedAt`이 파싱 불가한 날짜 문자열)을
  잡아 `timerState`만 폐기하고 `sessions`는 보존한다. 새로 추가한
  todoId/type 검증은 두 계층 모두에서 같은 결함 유형(필드 누락·타입 불일치)
  을 잡지만, 방어 실패 시 안전망이 이중화된다는 점에서 의미가 있다.

## 검증 결과

- `npx vitest run src/storage/storage.test.ts` — PASS
- `npx vitest run src/hooks/useTimer.test.ts` — PASS
- `npx vitest run src/lib/timer.test.ts` — PASS
- `npx vitest run` 전체 — PASS(145케이스), 종료 0
- `npx tsc --noEmit` — 종료 0
- `npm run build` — 종료 0

화면 변경 없음(순수 함수·저장 계층·훅 내부 검증 로직만 정밀화). 실행 화면
확인 불필요.
