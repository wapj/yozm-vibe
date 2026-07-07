# REVIEW (사이클: M6 / T20 — 재평가)

## 대상

T20. `timerState` 필드 단위 검증 정밀화 + `nextBreakType(0)`·음수 경계
계약 고정(PLAN.md M6 마지막 항목). (1) `storage.isValidStorageData`의
`timerState` 검증이 `typeof === 'object'`만 확인해 배열·필드 누락 객체도
통과하던 결함과 `useTimer.isValidTimerState`가 `startedAt`만 검증하던
문제를 `todoId`/`type`/`startedAt` 필드 단위로 정밀화하고, `nextBreakType`
의 0·음수 입력 계약을 테스트로 고정하는 항목이다. 신규/변경 화면이 없고
(순수 함수·저장 계층·훅 내부 검증 로직만 변경) `lib/timer.ts` 프로덕션
코드는 무변경이므로 화면 완성도 축은 적용하지 않고 화면 없는 항목 기준
(합계 9점 이상 PASS)으로 채점한다.

## 직접 실행한 검증

- `npx vitest run src/storage/storage.test.ts src/hooks/useTimer.test.ts
  src/lib/timer.test.ts` — 3파일 50케이스 통과(acceptance 개별 재실행).
- `npx vitest run` 전체 — 15파일 145케이스 통과, 회귀 없음.
- `npx tsc --noEmit` — 종료 0.

IMPL.md의 보고(개별 3파일 PASS·전체 145케이스·tsc 0·build 0)를 재실행으로
재현했다. `lib/timer.ts:15-17`은 IMPL 주장대로 프로덕션 무변경(계약 고정
테스트만 추가)이며, `storage/index.ts:22-34`·`useTimer.ts:8-20`에 필드
단위 검증이 실제로 반영되어 있음을 직접 대조로 확인했다.

## 평가 표

| 축 | 점수 | 근거 |
|---|---|---|
| 사양 충족 | 3 | acceptance 전부 통과 + 시나리오 검증. (1) `storage/index.ts:26-34` `isValidTimerStateShape`가 `Array.isArray` 배제 + `todoId`(string)·`type`(`isValidSessionType`)·`startedAt`(string) 필드 검증으로 배열 통과 결함을 제거하고, `storage.test.ts:115-168`이 배열·`todoId` 누락·유효하지 않은 `type`·`startedAt` 타입 불일치 4개 거부와 정상 통과 1개를 실증. `useTimer.ts:12-20`도 동일 필드 검증 + 기존 NaN 검사로 정밀화. (2) `nextBreakType`의 0·음수 계약은 `lib/timer.ts` 무변경 상태로 `timer.test.ts:31-42`가 `nextBreakType(0)→longBreak`, `-1~-3→shortBreak`, `-4/-8→longBreak`를 고정. PLAN M6 T20의 (1)(2) 모두 충족. |
| 모듈 경계 | 3 | 변경이 저장 계층(`storage/index.ts`)·훅(`useTimer.ts`)·순수 함수 테스트(`timer.test.ts`)와 각 테스트 파일에만 있고 PLAN이 명시한 "순수/저장 계층, 화면 무" 범위 안(touch 준수). `types.ts`·컴포넌트·`App.tsx`·`App.css` 무변경. 저장 계층은 전체 구조 무결성 판정(무효 시 `sessions`/`todos`까지 초기화), 훅 계층은 복원 폐기 방어선으로 책임이 분리되어 있고, `lib/timer.ts`는 계약 고정만으로 프로덕션 코드를 건드리지 않아 순수 함수 경계가 유지됨. `isValidSessionType`이 두 계층에 중복 정의되나 이는 PLAN이 명시한 훅 계층 독립 방어선 의도(경계 위반 아님). |
| 테스트 충실도 | 2 | 저장 계층 테스트가 거부 경로 4종 + 정상 통과 1종을 커버하고 실패 시 `createEmptyData()` 대체·`corrupted === true`까지 assert(`storage.test.ts:115-168`), `nextBreakType` 경계는 `it.each`로 0·양수·음수 배수/비배수를 망라(`timer.test.ts:31-42`)해 대체로 충실하다. 다만 `useTimer.ts:15-17`에 새로 추가된 `todoId`/`type` 검증 분기는 어떤 테스트로도 격리 실증되지 않는다(아래 메모1). 프로덕션에 신규 방어 코드를 넣었는데 그 코드 경로를 태우는 테스트가 없다는 점은 명백한 충실도 공백이므로, 절차 2번(부실하면 충실도 점수를 낮춘다)에 따라 2점으로 조정한다. |
| 운영 고려 | 3 | 신규 의존성 없음, `npm run build` 종료 0(IMPL 보고, 이번 재평가는 tsc·vitest로 대체 확인). PLAN M6 T20을 문서(IMPL·JOURNAL·TASKS) 갱신과 함께 반영하고 IMPL "결정 사항"에 계약 채택 근거(JS 나머지 연산 부호 규칙)와 이중 방어선 유지 이유를 명시. 스키마·저장 형식 무변경으로 되돌리기 쉬움. |

## 합격 여부

합계 **11 / 12** → **PASS** (화면 없는 항목 기준 9점 이상).

점수와 판정이 일치한다(9점 이상 PASS). 직전 사이클 REVIEW의 12/12에서
테스트 충실도를 3→2로 조정했으나 판정(PASS)은 동일하다. 조정 사유는
메모1에 있다.

## 다음 사이클로 넘기는 메모

- 메모1(테스트 충실도, 선택): `useTimer.ts`의 신규 `todoId`/`type` 검증
  분기(`useTimer.ts:15-17`)는 `useTimer.test.ts:182-204`의 두 케이스로는
  실제로 도달되지 않는다. `loadData()`의 `isValidStorageData`가 이제
  `todoId`/`type`/`startedAt`를 훅과 **동일하게** 검사하므로(`storage/index.ts:29-32`),
  훅 검증에서 실패할 `timerState`는 저장 계층에서 먼저 무효 처리되어
  `latest.timerState`가 `null`이 되고 `useTimer.ts:71`의 조기 반환에
  걸린다. 즉 훅의 신규 `todoId`/`type` 분기는 두 계층 검사가 동일한 한
  사실상 도달 불가한 방어선이며(유일하게 훅 전용인 것은 `startedAt` NaN
  검사로, 기존 `useTimer.test.ts:169-180` NaN 케이스가 이를 커버), 두 신규
  테스트는 통과하나 실제로 검증하는 동작은 저장 계층 거부다. IMPL·TASKS
  (29-32행)가 이 점을 정직하게 공시했으나, 신규 프로덕션 분기가 미실증인
  것은 충실도 공백이므로 이번 재평가에서 테스트 충실도에 반영했다. 저장
  계층 검사를 통과하면서 훅 검사에서만 걸리는 입력을 심어 훅의 신규 분기를
  직접 실증하는 케이스 1건을 보강하면 이중 방어선의 통합 계약이 명확해지고
  충실도 점수도 회복된다.
- 이월(변동 없음): REVIEW T19 메모1(`App.tsx:22` `writeFailed` OR 결합 중
  `timerSaveFailed` 분기 통합 미커버, 실질 결함 아님), T17 메모1(정확히
  25분 경계값 통합 복원 케이스), 타임라인 `HH:mm` 다일 구분(선택)은 TASKS
  대기 섹션에 그대로 유지된다. PLAN.md의 마일스톤 항목은 T20으로 모두
  완료되었으므로 다음 사이클의 필수 진행 대상은 없다.

## 판단 기준 메모

- 화면 완성도 축 제외: T20은 신규/변경 화면이 없는 순수/저장 계층 항목
  이므로 일반적 모범 사례에 비추어 화면 없는 항목 기준으로 채점했다.
- decisions 2건(`timer-durations`·`todo-reorder`)은 `*.evaluator.md`가
  이미 존재해 신규 기록 대상 없음.
