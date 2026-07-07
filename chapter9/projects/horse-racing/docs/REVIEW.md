# REVIEW: T25. 전체 루프 통합 검증 + PRD 9번 성공 기준 확인 (M6 마감)

## 항목 분류

T25는 검증·마감 태스크입니다. touch는 테스트 파일과 문서(`src/App.test.tsx`,
`docs/IMPL.md`)에 한정되며 신규 화면 산출물이 없으므로 **화면 없는 항목**으로 채점합니다
(PASS 기준 합계 9점 이상, 4개 축). 화면 완성도 축은 적용하지 않습니다. 실화면 시인성은
PRD 9번의 일부이나 하네스로 검증 불가하여 IMPL.md에 미검증 항목으로 분리 기록됨을 확인했으며
감점 대상이 아닙니다.

## 직접 실행 결과 (IMPL.md 보고 대조)

- `npx tsc --noEmit` → 종료 코드 0.
- `npx vitest run` → **36 files / 282 tests 전부 통과**(기존 280 + 신규 2, 회귀 없음). IMPL 보고와 일치.
- `npx vite build` → 성공(71 modules, `dist/assets/index-MpucUPLp.js` 168.90kB gzip 56.45kB). IMPL 보고와 일치.
- 프로덕션 소스 변경 없음 확인: 변경 파일은 `src/App.test.tsx`·`docs/IMPL.md`뿐으로 touch 범위 준수, 간극 없음(대조 결과) 주장과 일치.

## 평가 표

| 축 | 점수 | 근거 |
|---|---|---|
| 사양 충족 | 3 | acceptance 3개 명령(vitest·tsc·build) 직접 실행 전부 통과. 신규 통합 테스트가 요구를 실제 검증: `src/App.test.tsx:571-617`이 주입 driver·시드 rng로 베팅→카운트다운→경주→정산→로비 순환을 **연속 2회** 구동하고, 매 회차 후 베팅 패널 재노출(`getByLabelText("베팅 패널")`)·정산 결과 소멸(`queryByLabelText("정산 결과")` → null)을 값으로 단언(`:610-611`, `:614-615`). 새로고침 라운드트립은 기존 T22 테스트(`:360-393`)가 같은 driver로 새 `createPersistence(driver).load()` 호출해 잔고·전적 복원을 실제 단언하여 acceptance 4a를 종단으로 충족 — 인용 대체는 touch 노트가 허용한 결정으로 타당. |
| 모듈 경계 | 3 | 변경이 `src/App.test.tsx`·`docs/IMPL.md`로 정확히 touch 범위 안. 프로덕션 6개 디렉터리(`domain`/`sim`/`render`/`store`/`persistence`/`audio`)·오케스트레이션 훅 무변경(읽기 전용 소비 원칙 준수). 신규 파일을 만들지 않고 기존 헬퍼(`createInMemoryDriver`·`createManualTimer`·`createManualRaf`·`createMockCtx`·`driveRaceToCompletion`)를 재사용한 배치는 IMPL.md에 근거 기록됨. |
| 테스트 충실도 | 3 | 통과 여부뿐 아니라 상태 전이를 값으로 단언(긍정·부정 양방향). 파산 재충전 테스트(`:619-663`)는 잔고 150 시드 store에 올인 확정 시 선차감 즉시 잔고 10,000 재충전(`:644`)·파산 횟수 1 증가(`:645`)를 화면 텍스트로 단언하고, 이어 경주→정산→로비 복귀까지 구동해 재충전 후 루프 지속(`:660-661`)을 확인 — 실패 경로(잔고<100)를 실제로 재현. 인용 근거 테스트(`driver.test.ts:86-87` 역전 빈도 밴드, `loop`/`particles`/`finishFx`/`effects`/`commentary`)가 모두 실재하며 전체 스위트에서 통과함을 확인. |
| 운영 고려 | 3 | 의존성 변경 없음, build 번들 실측 반영. IMPL.md가 PRD 9번 4개 축 대조 표(각 축을 고정하는 테스트 목록)와 픽셀 전용 미검증 항목을 명시적으로 분리 기록(`IMPL.md:33-79`). 대조 표의 인용 테스트가 실재함을 개별 확인. |

**합계: 12 / 12**

## 합격 여부

**PASS** (화면 없는 항목, 합계 12점 ≥ 9점 기준). 합계와 판정 일치 확인.

## decisions 처리

`docs/decisions/`의 3개 주제(`canvas-rendering-library`·`horse-graphics`·`tab-inactive-handling`) 모두
`.evaluator.md`가 기존재하여 절차 5번의 신규 독립 기록 대상이 없습니다.

## 다음 사이클 메모

- FAIL·조건부 PASS가 아니므로 필수 메모 없음. 참고 사항만 남깁니다.
- T25 PASS로 PLAN.md M6의 모든 태스크가 완료되었습니다. 다음 Planner 사이클이 PRD 전체를
  처음부터 재대조해 남은 간극이 없음을 확인한 뒤 `docs/DONE` 생성 여부를 판정하는 것이 남은 절차입니다.
- 미검증 항목(역전 육안 체감 빈도, 슬로모션 감속 부드러움, 폭죽 밀도·화려함, 스킬 이펙트 색·타이밍,
  실황 자막 노출 타이밍·가독성, 전반적 색 대비·여백)은 jsdom 한계로 자동 검증 불가하여 `npm run dev`
  실브라우저 수동 확인 몫으로 남습니다(감점 아님, PRD 9번 성공 기준의 일부). DONE 판정 전 수동 통과가 권장됩니다.
- 참고(감점 아님): 신규 2회 순환 테스트는 실황 emit·탭 일시정지의 회귀 없음을 자체 단언하지 않고
  전체 스위트의 개별 테스트(`commentary.test.ts`·탭 관련 테스트)에 의존합니다. 종단 테스트 내에서 실황
  피드 렌더를 직접 단언하면 통합 관점의 커버리지가 더 견고해집니다.
