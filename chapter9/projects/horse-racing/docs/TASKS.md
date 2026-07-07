# TASKS: 브라우저 경마 베팅 게임

이번 세션에서 진행할 작업. 각 항목은 한 세션(약 10~20분) 크기다.
완료 시 `[x]`로 표시한다.

## 진행

(현재 진행 중인 항목 없음. 다음 Planner 사이클이 PRD 전체를 재대조해 `docs/DONE` 여부를 판정한다.)

## 완료

### T25. 전체 루프 통합 검증 + PRD 9번 성공 기준 확인 (M6 마감) — [x] 완료

**구현 결정(IMPL.md 요약)**: 대조 결과 프로덕션 코드 간극은 발견되지 않아 새 기능·수정 없이 통합
테스트만 추가했다. `App.test.tsx`에 (1) 전체 루프 연속 2회 순환, (2) 잔고<100 경로에서 올인 베팅으로
파산 자동 재충전 후 루프 지속을 신규로 고정했고, 새로고침 라운드트립은 T22가 이미 종단 테스트로
고정하고 있어 인용으로 대체했다. PRD 9번 4개 축 대조 표와 픽셀 전용 미검증 항목은 `docs/IMPL.md`에
기록했다.

M6의 마지막이자 프로젝트 마감 태스크. M1~M6의 개별 태스크로 렌더·시뮬레이션·스토어·저장·
React UI·효과음·스타일이 모두 구현되었으나, **PRD 9번 성공 기준 4개 축이 하나의 통합 지점에서
실제로 함께 동작함을 확인하는 종단(end-to-end) 검증**과, **PRD 전체를 다시 대조해 남은 간극이
없음을 판정**하는 절차는 아직 없다. 이 태스크는 (1) 베팅→경주→정산→로비의 전체 루프를 **연속 2회
이상 반복** 구동하는 통합 테스트로 오류 없는 순환을 고정하고, (2) PRD 9번 성공 기준 각 항목이
기존 테스트 또는 신규 통합 테스트로 대응됨을 확인하며, (3) 픽셀 화면으로만 확인 가능한 항목을
미검증으로 명시한다. 새로운 프로덕션 기능은 추가하지 않는다 — 이미 구현된 경로가 PRD를 충족함을
증명하고, 대조 중 발견되는 간극만 최소 변경으로 메운다.

소비할 모듈은 모두 기정의돼 있으며 재구현하지 않는다. 전체 루프 오케스트레이션은
`useGameController`(`src/ui/useGameController.tsx`)와 `App.tsx`(phase별 컴포지션·자동 저장 구독)가,
정산은 `calculateSettlement`, 전적 갱신은 `records.ts`·`gameStore.recordRaceResult`, 파산 재충전은
`adjustBalance`(`gameStore.ts`), 지속 저장은 `toSavedState`+`persistence.save`, 역전 빈도는
`driver.test.ts`가 이미 고정한 밴드를 소비한다. 통합 테스트는 기존 `App.test.tsx`의 결정적 구동
방식(주입 driver·주입 `controllerOptions`·주입 `raceCanvasOverrides`·시드 rng·가짜 loop/타이머)을
재사용한다.

- **PRD 9번 성공 기준 대조 표(이 태스크가 확인할 대상)**
  1. **베팅→경주→정산 전체 루프가 오류 없이 반복 가능** — 신규 통합 테스트로 2회 이상 연속 순환.
  2. **역전 우승 빈도(약 5~10회차당 1회)** — `driver.test.ts`의 기존 다회 시뮬레이션 밴드로 이미
     고정됨을 확인·인용(픽셀 체감은 미검증, 하네스 수단 없음).
  3. **피니시 슬로모션·폭죽·스킬 이펙트·실황 중계 동작** — 각각 `loop.test.ts`(슬로모션 timescale)·
     `particles.test.ts`/`finishFx.test.ts`(폭죽·스포트라이트)·`effects.test.ts`(스킬 이펙트)·
     `commentary.test.ts`/`App.test.tsx`(실황 자막) 등 기존 테스트로 대응됨을 확인·인용. 실화면
     시인성(밀도·체감·색 대비)은 미검증 항목으로 명시.
  4. **새로고침 후 잔고·전적 유지 + 파산 자동 재충전** — 신규 통합 테스트로 (a) 라이프사이클 후
     같은 driver로 새 `persistence.load()`가 잔고·전적을 복원함, (b) 잔고가 최소 베팅액(100) 미만이
     되는 경로에서 `adjustBalance`가 기본 잔고(10,000)로 재충전하고 파산 횟수가 증가함을 고정.

- **acceptance**
  - **전체 루프 반복 통합 테스트(신규)**: jsdom + `@testing-library/react`로 `App`을 주입 driver·
    `controllerOptions`·`raceCanvasOverrides`(시드 rng·가짜 raf/타이머)로 마운트해, 베팅 확정→
    카운트다운→경주 구동→완주→정산→로비 복귀의 전체 순환을 **연속 2회 이상** 오류 없이 구동한다.
    두 번째 회차에서도 phase가 `lobby`로 정상 복귀하고 베팅이 다시 가능함을 값으로 단언한다(1회차
    정산 결과가 2회차 시작을 막지 않음). 기존 오케스트레이션(정산·전적 갱신·실황 emit·탭 일시정지)이
    회귀 없이 유지됨을 확인한다.
  - **새로고침 라운드트립(PRD 9번 핵심, 신규 또는 T22 확장)**: 위 라이프사이클을 1회 이상 구동한 뒤
    같은 driver로 새 `createPersistence(...).load()`를 호출하면 정산 후 잔고와 갱신된 전적(`records`의
    출전 수·우승 수·최근 성적)이 복원됨을 값으로 단언한다. store 재구성 없이 driver에 저장된 JSON을
    파싱해 직접 확인한다(T22가 고정한 저장 경로를 재확인·강화).
  - **파산 자동 재충전(PRD 4.4·9번)**: 잔고가 최소 베팅액(100) 미만으로 떨어지는 경로에서
    `gameStore.adjustBalance`가 기본 잔고(10,000)로 재충전하고 파산 횟수(`bankruptcyCount`)가 1
    증가함을 값으로 단언한다(기존 `gameStore.test.ts` 파산 경계 테스트가 이를 이미 고정하고 있으면
    인용으로 대체 가능하되, 통합 경로에서 재충전 후에도 루프가 이어짐을 확인한다).
  - **PRD 9번 대조 문서화**: 위 대조 표의 4개 축 각각을 어떤 테스트가 고정하는지 IMPL.md에 목록으로
    남기고, 픽셀 화면으로만 확인 가능한 미검증 항목(슬로모션·폭죽 밀도 체감, 색 대비·여백 체감)을
    명시적으로 분리 기록한다(감점 아님, PRD 9번 성공 기준의 일부는 실브라우저 `npm run dev` 수동
    확인 몫).
  - `npx vitest run` → 전체 통과(현재 36 files / 280 tests 기준, 신규 통합 테스트 포함 회귀 없음).
  - `npx tsc --noEmit` → 종료 코드 0.
  - `npm run build` → 성공(종료 코드 0).
- **touch**
  - `src/App.test.tsx`(전체 루프 2회 반복 통합 테스트·새로고침 라운드트립·파산 재충전 통합 테스트
    추가). 별도 통합 테스트 파일이 더 단순하면 `src/ui/` 또는 루트에 신규 파일로 두어도 무방하다
    (되돌리기 쉬운 배치 결정, 근거는 IMPL.md).
  - `docs/IMPL.md`(PRD 9번 대조 표·미검증 항목 기록). 프로덕션 소스는 대조 중 발견되는 간극이
    있을 때만 최소 변경한다. 간극이 없으면 프로덕션 코드는 변경하지 않는다.
  - 프로덕션 모듈(`src/domain`·`src/sim`·`src/render`·`src/store`·`src/persistence`·`src/audio`·
    오케스트레이션 훅)은 **읽기 전용으로 소비**하며 재구현하지 않는다. 대조 중 실제 기능 간극이
    발견되면 그것을 이 태스크에서 최소 변경으로 메우되, 규모가 한 세션을 초과하면 후속 태스크로
    분리하고 PLAN.md·TASKS.md에 남긴다.
- **참고**
  - 이 태스크는 검증·마감 중심이다. 기존 테스트가 PRD 9번 각 축을 이미 고정하고 있으면 신규 테스트를
    최소화하고 인용으로 대체하되, "전체 루프 2회 반복"과 "새로고침 라운드트립"은 종단 관점에서 반드시
    신규(또는 확장) 통합 테스트로 고정한다. 개별 축이 흩어진 단위 테스트로만 검증돼 있고 종단 순환이
    한 번도 함께 돌지 않았기 때문이다.
  - 하네스 제약: jsdom은 `canvas.getContext("2d")` 실제 그리기와 픽셀 시인성을 확인할 수 없다.
    슬로모션 체감·폭죽 밀도·색 대비·여백은 미검증 항목으로 남기며 감점 대상이 아니다(PRD 9번 성공
    기준의 일부는 실브라우저 수동 확인 몫).
  - 종료 판정: 이 태스크가 PASS로 완료되면 다음 Planner 사이클이 PRD 전체를 처음부터 재대조해
    남은 간극이 없음을 확인한 뒤 종료(`docs/DONE`)를 판정한다. T25 자체는 DONE을 만들지 않는다.

## 완료

### T24. 시각 완성도 기준선 (CSS 도입, 접근성 유지) (M6, 화면 있는 항목) — [x] 완료

**구현 결정(IMPL.md 요약)**: 전역 단일 CSS(`src/index.css` + `main.tsx` import)를 택했다. 공용
`.card` 클래스로 HorseCard·BetPanel·SettingsPanel·SettlementResult의 패널 스타일을 공유했다.

M6의 다섯 번째 태스크. 현재 `src/` 전체에 CSS·`className`·인라인 스타일이 전무하다
(코드 대조 확인: `grep -rl "className|\.css|style="` src → 없음). 로비·경주·정산·설정
화면에 여백·타이포그래피·색 대비를 정돈하는 **스타일 기준선**을 도입한다. 픽셀 완벽함이
아니라, 회귀 없이 시맨틱 클래스·전역 스타일을 확립하는 것이 목표다.

- **범위**: `App.tsx`가 조립하는 화면(로비: `HorseCard` 목록·`BetPanel`·`SettingsPanel`,
  경주: `RaceCanvas`·`CommentaryFeed`, 정산: `SettlementResult`, 공통: `BalanceDisplay`·
  `StorageBanner`, 루트 `<main>`·제목)에 시맨틱 클래스를 부여하고, 전역 리셋·타이포·색
  토큰을 세우는 수준으로 한정한다. 모든 컴포넌트를 픽셀 단위로 완성하는 것은 범위 밖이며,
  세부 시인성 마감은 T25 통합·실브라우저 수동 확인 몫이다.
- **접근성 유지(PRD 5번·13번)**: 색상만으로 말을 구분하지 않도록 번호·이름 병기를
  유지한다. 기존 `HorseCard`·렌더러의 번호/이름 출력 테스트가 회귀 없이 통과해야 한다.
- **CSS 방식 결정(되돌리기 쉬움)**: 전역 단일 CSS(`src/index.css` + `main.tsx`에서 import)를
  기본 후보로 두되, CSS Modules 등 다른 방식을 택해도 무방하다. Generator가 가장 단순한
  방식을 골라 IMPL.md에 근거를 남긴다.
- **하네스 한계**: jsdom은 실제 렌더링 픽셀·색 대비를 확인할 수 없다. 따라서 실제 색·여백
  체감은 미검증 항목으로 남기고 감점 대상이 아니다. 자동 검증은 (1) 스타일 파일 존재와
  import, (2) 주요 컨테이너에 클래스가 부여됨(DOM 단언), (3) 빌드·전체 회귀 무결로 한정한다.

**acceptance**

- `npx vitest run` → 전체 통과(현재 36 files / 278 tests 기준, 신규/변경 테스트 포함 회귀
  없음). 특히 번호·이름 병기 관련 기존 테스트가 그대로 통과한다.
- `npx tsc --noEmit` → 종료 코드 0.
- `npm run build` → 성공(종료 코드 0). `tsc --noEmit && vite build`가 CSS import를 포함해
  번들을 생성함을 확인한다(전역 CSS·CSS Modules 어느 방식이든 vite 번들에 반영).
- 스타일 적용 자체를 DOM으로 단언하는 테스트를 최소 1건 추가한다. 예: `App`(또는 대표
  컴포넌트) 렌더 시 루트 컨테이너·`HorseCard`에 지정한 시맨틱 클래스가 존재한다
  (`@testing-library/react`의 `container.querySelector(".<클래스>")` 또는 `toHaveClass`).
- 색 대비·여백 등 실제 픽셀 시인성은 `npm run dev` 수동 확인 몫으로 남긴다(하네스 수단
  없음·감점 아님, PRD 9번 성공 기준의 일부).

**touch**

- `src/index.css`(신규, 전역 방식 선택 시) 또는 컴포넌트별 `*.module.css`(Modules 선택 시).
- `src/main.tsx`(전역 CSS import 추가) 또는 각 컴포넌트 파일의 module import.
- `src/App.tsx` 및 스타일을 부여할 `src/ui/` 화면 컴포넌트(`HorseCard`·`BetPanel`·
  `SettingsPanel`·`CommentaryFeed`·`SettlementResult`·`BalanceDisplay`·`StorageBanner`)에
  `className` 부여. 컴포넌트의 로직·props·접근성 마크업(번호·이름·`aria-label`·`role`)은
  변경하지 않는다.
- 위 클래스 존재를 단언하는 테스트 파일(대표 1~2개면 충분).
- `src/domain`·`src/sim`·`src/render`·`src/store`·`src/persistence`·`src/audio`는 변경하지
  않는다(스타일은 React UI 계층에만 부착).

## 완료

### T23b. 게임 이벤트에 사운드 연결 + 음소거 토글 실반영 배선 (M6, 배선) — [x] 완료

M6의 네 번째 태스크. T23a가 세운 사운드 엔진(`createSoundEngine`, `src/audio/soundEngine.ts`)을
오케스트레이션 훅 `useGameController`(`src/ui/useGameController.tsx`)에 배선해 PRD 4.8(효과음·
음소거·자동재생 정책)을 완성했다. 기존 모듈(`SoundEngine` 표면·`deriveRaceEvents`·
`calculateSettlement`)은 재구현하지 않고 소비만 했다.

배선 지점: `handleBetConfirm`에서 `sound.enable()`을 1회 호출(자동재생 게이팅, PRD 4.8)하고,
`handleFrame`의 실황 이벤트 루프에서 `start`→`play("start-fanfare")`+`startLoop("hoofbeat")`,
`skill-activation`→`play("skill-activation")`, `finish`→`play("finish-cheer")`+
`stopLoop("hoofbeat")`를 호출했다. `lead-change`·`final-stretch`·`close-race`는 전용 사운드를
두지 않았다(범위 명시대로). 정산 경로에서는 `calculateSettlement` 결과의 `won` 여부로
`play("settlement-win"/"settlement-lose")`를 호출했다. 음소거는 `useEffect([sound,
storeState.settings.muted])`로 초기값 포함 매 변경마다 `sound.setMuted`에 반영했다.

**엔진 기본값·DI 결정(IMPL.md 요약과 동일)**: 기본 엔진은 `useGameController` 내부에서
`useRef` 지연 초기화로 1회만 생성한다(`options.sound ?? defaultSoundRef.current`).
`App.tsx`는 `props.controllerOptions`를 그대로 `useGameController`에 전달하는 기존 구조라
`sound` 필드가 옵션 타입에 추가되는 것만으로 테스트 DI(`controllerOptions={{ sound: mock
}}`)가 이미 성립해, `App.tsx` 자체에는 추가 배선이 필요하지 않았다(계획된 touch 대비
축소). **jsdom crash 방지**: 이 하네스(jsdom)는 전역 `AudioContext`가 없어(`typeof
AudioContext === "undefined"` 확인됨) 기본 엔진의 `enable()`이 실제 `new AudioContext()`를
시도하면 예외가 발생한다. 다수의 기존 회귀 테스트(`App.test.tsx` 등)가 `sound`를 주입하지
않고 베팅 확정을 구동하므로, `handleBetConfirm`의 `sound.enable()` 호출을 `try/catch`로
감쌌다(백엔드 생성 실패 시 `backend`가 `null`로 남아 이후 `play`/`startLoop`가 조용히
no-op되는 기존 `soundEngine.ts` 계약을 그대로 활용). 실브라우저에서는 `AudioContext`가
있으므로 정상 동작한다.

**T23a REVIEW 갭 흡수**: `soundEngine.ts`의 `ONE_SHOT_TONES`·`ATTACK_SECONDS`를 로직 변경
없이 `export`만 추가해 노출했다. `soundEngine.test.ts`에 `skill-activation`·`finish-cheer`·
`settlement-win`·`settlement-lose` 4종의 `osc.type`·`osc.frequency.value`·엔벨로프
(`setValueAtTime`/`linearRampToValueAtTime`) 스케줄링을 스펙 값으로 단언하는 `it.each` 테스트를
추가했다.

- **acceptance 충족**: 위 acceptance 5개 항목 모두 `useGameController.test.tsx`의 신규
  `describe("T23b: ...")` 블록(5개 테스트: enable 순서, skill-activation, finish+
  settlement-win, settlement-lose, muted 초기값+양방향 토글)과 `soundEngine.test.ts`의
  4종 톤·엔벨로프 단언으로 검증했다. `npx vitest run` 전체 278개(기존 269 + 신규 9) 통과,
  `npx tsc --noEmit` 종료 코드 0.
- **touch**: `src/ui/useGameController.tsx`·`src/ui/useGameController.test.tsx`·
  `src/audio/soundEngine.ts`(export 추가만)·`src/audio/soundEngine.test.ts`. `App.tsx`는
  변경하지 않았다(위 결정 참조).

### T23a. Web Audio 신시사이즈 사운드 엔진 + 음소거 실반영 + 자동재생 게이팅 (M6, 화면 없는 로직) — [x] 완료

M6의 세 번째 태스크. `src/audio/`에 사운드 엔진 팩토리 `createSoundEngine(backendFactory?, options?)`
(`src/audio/soundEngine.ts`)를 만들었다. Web Audio oscillator/gain으로 5종 효과음(출발
팡파르·스킬 발동·피니시 함성·정산 승/패의 1회성 `play(name)` + 발굽 루프의 `startLoop`/
`stopLoop`)을 신시사이즈한다. `AudioContext`·노드 생성·스케줄링은 주입 가능한 `AudioBackend`
인터페이스(`src/audio/types.ts`)와 기본 브라우저 구현(`src/audio/webAudioBackend.ts`, 외부 미노출)
뒤에 감췄다. `enable()` 호출 전에는 백엔드가 생성되지 않고 `play`/`startLoop`는 무시됨을
mock 백엔드로 단언했다(자동재생 게이팅, PRD 4.8). 모든 사운드는 마스터 게인을 거쳐 destination에
연결되고, 음소거 시 마스터 게인을 0으로 낮춰 출력을 차단하며 생성 옵션(`muted`)·`setMuted`
세터로 반영된다. 게임 이벤트·store·React 배선(`useGameController` 연결)은 T23b의 몫으로
남겼다.

### T22. 지속적 자동 저장 배선 (store 변경 → persistence.save) (M6) — [x] 완료

M6의 두 번째 태스크. T21이 경주 완주 시 store 내 `records`(전적)를 갱신하도록 세웠으나,
그 변경은 **메모리에만 남고 저장되지 않는다**. 마찬가지로 정산 시 `adjustBalance`로 바뀌는
잔고·파산 횟수도 저장되지 않는다. `App.tsx`는 부트스트랩에서 `persistence.load()`로 초기
상태를 읽고(`App.tsx:49`), 설정 변경·초기화 경로에서만 `persistence.save`를 수동 호출할 뿐
(`App.tsx:84`·`95`), **진행 중 store 변경을 지속 저장하는 구독 배선이 없다**. 그 결과 경주를
마쳐 잔고·전적이 바뀌어도 새로고침하면 부트스트랩 시점(또는 마지막 설정 변경 시점)의 값으로
되돌아간다. 이 태스크는 store 변경(잔고·전적·설정)을 `persistence.save`로 지속 저장하는
배선을 세워 PRD 4.4·4.7·9번("새로고침 후에도 잔고와 전적이 유지")을 완성한다.

소비할 모듈은 모두 기정의돼 있으며 재구현하지 않는다. 지속 저장 대상은 `SavedState`
(`src/persistence/schema.ts:17`, `version`·`balance`·`bankruptcyCount`·`records`·`settings`)이며,
store 구독은 `GameStore.subscribe(listener)`(`src/store/gameStore.ts:58`)가, 저장은
`PersistenceController.save(state): SaveResult`(`src/persistence/storage.ts:87`, `disabled` 노출)가
제공한다. `store.getState()`가 반환하는 `GameStoreState`는 저장 대상이 아닌 필드(상태 머신
`phase`·`paused`, `horses`)를 포함하므로, 이를 `SavedState`로 투영하는 소형 순수 함수가 필요하다
(`version`은 `SAVE_SCHEMA_VERSION`으로 채운다). 저장 실패 시 세션 메모리 폴백·`disabled` 판정은
`createPersistence` 내부(`storage.ts:54-65`)가 이미 처리하므로 재구현하지 않고 소비만 한다.

배선 지점은 `App.tsx`다. store는 부트스트랩과 설정 변경·초기화에서 인스턴스가 교체되므로
(`App.tsx:63`·`86`·`96`), 자동 저장 구독은 현재 `store`에 재부착돼야 한다(store 교체 시
이전 구독 해제·새 인스턴스 구독). 저장 결과(`SaveResult.disabled`)로 `storageDisabled`를
갱신해, 진행 중 저장이 실패로 전환되면 안내 배너(`StorageBanner`)가 노출되게 한다(PRD 4.4·6번).

- **acceptance**
  - `GameStoreState`(또는 저장에 필요한 필드)를 입력받아 `SavedState`로 투영하는 순수 함수가
    존재한다. `version`을 `SAVE_SCHEMA_VERSION`으로 채우고 `balance`·`bankruptcyCount`·`records`·
    `settings`를 그대로 옮기며, 상태 머신 필드(`phase`·`paused`)와 `horses`는 결과에 포함되지
    않음을 값으로 단언한다. `src/sim`·`src/render`·React를 import하지 않는 순수 함수로 둔다.
  - `App`이 현재 `store`에 자동 저장 구독을 부착한다. jsdom + `@testing-library/react`로 주입
    driver(또는 주입 persistence)를 넘겨, 베팅 확정→경주 구동→완주→정산의 전체 라이프사이클을
    결정적으로 구동한 뒤(주입 rng·가짜 loop/타이머, 기존 `App.test.tsx` 구동 방식 재사용),
    정산 후 `persistence.save`가 갱신된 잔고·전적을 담은 `SavedState`로 호출되었음을 값으로
    단언한다(예: driver `setItem`에 저장된 JSON을 파싱해 `balance`·`records`가 정산 결과와 일치).
  - **새로고침 라운드트립(PRD 9번 핵심)**: 위 라이프사이클 후 같은 driver로 새 `persistence`를
    만들어 `load()`하면 정산 후 잔고·전적이 복원됨을 값으로 단언한다(진행 중 변경이 실제로
    지속 저장됨을 store 재구성 없이 driver 상태로 직접 확인).
  - store 교체 후에도 자동 저장이 유지된다. 설정 변경(`onSettingsChange`)으로 store 인스턴스가
    교체된 뒤 발생하는 잔고·전적 변경이 새 store에서도 `persistence.save`로 지속됨을 단언한다
    (이전 store 구독 누수로 잘못된 인스턴스를 저장하지 않음).
  - 저장 실패 반영: driver `setItem`이 예외를 던지는(저장소 미가용) 경우, 진행 중 저장 시도가
    `SaveResult.disabled=true`로 전환되고 `StorageBanner`가 노출됨을 단언한다. 세션 메모리 폴백·
    배너 표시 로직을 재구현하지 않고 기존 `PersistenceController`·`StorageBanner`를 소비한다.
  - 기존 회귀 없음: T20b·T20c·T21이 고정한 오케스트레이션·화면 컴포지션·전적 갱신 동작이
    유지되고, 설정 변경·초기화 경로의 기존 저장·store 교체 동작이 깨지지 않음을 단언한다.
    (설정 변경·초기화 경로의 수동 `persistence.save`가 자동 저장 구독과 중복되면, 중복 제거
    여부는 되돌리기 쉬운 결정으로 generator가 정하고 근거를 IMPL.md에 남긴다.)
  - `npx vitest run`으로 위 단위/통합 테스트가 통과하고 기존 회귀가 없다.
  - `npx tsc --noEmit`가 종료 코드 0으로 통과한다.
- **touch**
  - `SavedState` 투영 순수 함수 파일(`src/persistence/`의 신규 소형 모듈 권장; `src/store`·
    `src/ui`도 가능한 되돌리기 쉬운 배치 결정, 근거는 IMPL.md에 남긴다)과 그 테스트.
  - `src/App.tsx`(현재 store에 자동 저장 구독 부착 + `SaveResult.disabled`로 `storageDisabled`
    갱신; 기존 부트스트랩·설정 변경·초기화 경로는 최소 변경), `src/App.test.tsx`
  - `src/store/gameStore.ts`는 **읽기 전용으로 소비**한다. `subscribe`·`getState`·`adjustBalance`·
    `recordRaceResult`·`dispatch`의 기존 로직은 변경하지 않는다. 별도 파일이 불필요하면 투영
    함수를 기존 파일에 둔다(T15~T21 판단과 동일, 위반 아님).
- **참고**
  - 모듈 경계: 투영 함수는 `src/persistence/schema` 타입과 store 상태 타입만 의존하는 순수
    로직으로 부수효과가 없다. 저장 부수효과(구독·`save` 호출·배너 상태 갱신)는 `App.tsx`에
    격리한다. localStorage 폴백·손상 리셋·`disabled` 판정은 `createPersistence`를 재구현하지
    않고 소비한다. 전적 갱신·정산 계산·상태 전이·파산 재충전은 T20b·T21이 고정한 경로를 그대로
    쓰고 재작성하지 않는다.
  - 저장 빈도: store는 `dispatch`(phase·paused 전이)에서도 emit하므로 매 emit마다 저장하면
    경주 진행 중에도 저장이 잦아질 수 있다. 매 emit 저장(단순) vs 투영 결과가 바뀔 때만 저장
    (불필요한 write 억제)의 선택은 되돌리기 쉬운 결정으로 generator가 정하고 근거를 IMPL.md에
    남긴다. 어느 쪽이든 저장 대상 필드가 바뀌면 반드시 지속되어야 한다는 acceptance를 충족한다.
  - 실화면 시인성(새로고침 후 로비 말 카드의 전적·잔고가 실제로 보이는지)은 T24 스타일·T25
    통합 검증과 실브라우저 `npm run dev` 수동 확인 몫이다. T22는 "store 변경이 저장에 지속되고
    새로고침 시점의 `load()`가 그 값을 복원한다"까지 자동 검증으로 고정한다.
  - **구현 결정(IMPL.md 요약)**: 투영 함수는 `src/persistence/projection.ts`에 신설했다(store를
    import하지 않고 구조적 타이핑으로 `GameStoreState`를 그대로 받는다). 저장 빈도는 "매 emit
    저장(단순)"을 택했다 — store emit은 `dispatch`/`adjustBalance`/`recordRaceResult` 호출
    시점에만 발생해 애니메이션 프레임마다 발생하지 않으므로 write 빈도가 문제되지 않고, 투영
    결과 비교(dedup) 로직이 store 교체 시 이전 인스턴스의 저장 이력과 뒤섞이는 복잡성을 피할 수
    있다. 설정 변경·초기화 경로의 기존 수동 `persistence.save`는 제거하지 않고 그대로 유지했다
    — 자동 저장 구독은 store에 **부착된 이후**의 emit부터만 반응하므로(부착 시점 자체는 저장하지
    않음), store 교체 직전 수동 저장과 겹치지 않는다.

### T21. 경주 완주 시 전적(records) 갱신 (순수 함수 + store 반영 + 정산 경로 연결) (M6) — [x] 완료

M6의 첫 태스크. PRD 4.7(말 전적/성장 기록)과 9번 성공 기준("새로고침 후에도 잔고와 전적이
유지")의 코드 공백 중 **전적(`records`) 갱신** 부분을 세운다. 지금까지 어떤 태스크도 경주
결과로 `records`를 갱신한 적이 없어(`gameStore.ts`의 `records`는 저장에서 로드만 될 뿐 경주가
끝나도 변하지 않는다), 로비 말 카드의 출전 수·우승 수·최근 5경기·연승 배지가 항상 초기값으로
표시된다. 이 태스크는 완주 순위로 전적을 갱신하는 **순수 함수**와, 그것을 store에 반영하는
**갱신 표면**, 그리고 정산 경로에서 그 표면을 호출하는 **배선**까지 다룬다. 새로고침 후에도
전적이 유지되게 하는 지속 저장(store 변경 → `persistence.save`)은 T22의 몫이다.

갱신 대상 타입은 이미 정의돼 있다. `RaceRecord`(`src/domain/types.ts:28`)는 `racesRun`·`wins`·
`recentResults`(최신이 배열 맨 앞) 세 필드다. 완주 순위는 `RankedRunner[]`(`src/sim/types.ts:35`,
`{ id, position, rank }`)로 주어지며 `rank === 1`이 우승이다. `records`의 키와 `rankings`의 `id`는
모두 말 id로 정합한다(T20b가 이미 이 정합에 의존해 정산 승패를 판정한다). 정산 경로는
`useGameController`의 `handleFrame`에서 `state.finished && !finishHandledRef.current`일 때
(`useGameController.tsx:180`) `rankings`를 확보하는 지점이다. 이 지점에 전적 갱신 호출을 붙인다.

최근 성적 유지 개수(최근 5경기)는 PRD 4.7에 "최근 5경기 성적"으로 명시돼 있고, 연승 판정에
쓰는 `lobbyEntries.ts`(T17)가 이미 이 배열을 소비하므로 상한 5로 고정한다. 상한 상수의 배치
(도메인 상수 vs 순수 함수 인자 기본값)는 되돌리기 쉬운 결정으로 generator가 정하고 근거를
IMPL.md에 남긴다.

- **acceptance**
  - `src/domain/`에 완주 순위와 기존 `records`를 입력받아 갱신된 `records`를 반환하는 순수 함수가
    존재한다. `src/sim`·`src/store`·React를 import하지 않고 `src/domain` 타입과 순위 배열만 의존한다.
    입력 `records`를 변경하지 않고 새 객체를 반환한다(방어 복사, 기존 `gameStore` 관례와 정합).
  - 갱신 규칙을 값으로 단언한다. 순위에 포함된 각 말에 대해 `racesRun`이 1 증가하고, `rank === 1`
    이면 `wins`가 1 증가하며(그 외 0), `recentResults` 맨 앞에 이번 `rank`가 추가되고 최근 5개만
    유지된다(6번째부터 오래된 항목이 밀려난다). 해당 말 키가 `records`에 없으면(신규 출전)
    `racesRun=1`·`wins`=우승 여부·`recentResults=[rank]`로 새로 생성됨을 단언한다.
  - `gameStore`에 완주 순위로 내부 `records`를 갱신하고 구독자에게 emit하는 표면(예:
    `recordRaceResult(rankings)`)이 존재한다. 호출 후 `getState().records`가 갱신 순수 함수의
    결과와 일치하고, 재충전·잔고·설정 등 다른 상태를 변경하지 않음을 값으로 단언한다. 순위 산출·
    전적 규칙을 store에서 재구현하지 않고 순수 함수를 소비한다.
  - `useGameController`의 정산 경로(`state.finished` 최초 진입)에서 이 표면이 완주 순위로 1회
    호출된다. jsdom + `@testing-library/react`로 주입 store·가짜 loop/타이머·시드 rng로 전체
    라이프사이클을 구동해, 완주 후 store `records`에 출전마들의 전적이 반영되고(출전 수 증가,
    우승마 `wins` 증가, `recentResults` 갱신), 정산·실황 emit·탭 일시정지 등 기존 T20b 오케스트레이션
    동작이 회귀 없이 유지됨을 단언한다. 갱신 호출이 완주당 정확히 1회임을(중복 갱신 없음) 단언한다.
  - `npx vitest run`으로 위 단위/통합 테스트가 통과하고 기존 회귀가 없다.
  - `npx tsc --noEmit`가 종료 코드 0으로 통과한다.
- **touch**
  - `src/domain/records.ts`(완주 순위→`records` 갱신 순수 함수; 파일명·배치는 되돌리기 쉬운 결정),
    `src/domain/records.test.ts`
  - `src/store/gameStore.ts`(`records` 갱신 표면 추가; 기존 `adjustBalance`·`dispatch`·재충전
    로직은 변경하지 않는다), `src/store/gameStore.test.ts`
  - `src/ui/useGameController.tsx`(정산 경로에서 갱신 표면 호출 배선; T20b가 고정한 정산 계산·
    상태 전이·실황 emit·탭 일시정지 로직은 재작성하지 않고 전적 갱신 호출만 추가),
    `src/ui/useGameController.test.tsx`
  - 필요 시 `src/store/gameStore.ts`의 `GameStore` 인터페이스 확장. 별도 파일이 불필요하면 기존
    파일에 둔다(T15~T20c 판단과 동일, 위반 아님).
- **참고**
  - 모듈 경계: 전적 갱신 순수 함수는 `src/domain` 타입과 순위 배열만 의존하는 순수 로직으로
    `src/store`·`src/sim`·React를 참조하지 않는다. store 표면은 순수 함수를 소비만 하고 규칙을
    재구현하지 않는다. 컨트롤러는 표면을 호출하는 배선만 추가한다.
  - 지속 저장(store 변경마다 `persistence.save`로 새로고침 후 유지)은 T22의 몫이다. T21은
    "경주가 끝나면 store 내 `records`가 갱신된다"까지만 고정한다. T21만으로는 새로고침 시 전적이
    사라지는 것이 정상이며, T22가 이를 완성한다.
  - 파산 재충전(`adjustBalance` 내부, `gameStore.ts:45-50`)은 전적 갱신과 독립적이다. 전적 갱신
    표면은 잔고·재충전을 건드리지 않는다.
  - 실화면 시인성(로비 말 카드에 갱신된 전적·연승 배지가 실제로 보이는지)은 T24 스타일·T25 통합
    검증과 실브라우저 수동 확인 몫이다. T21은 전적 갱신 로직·store 반영·배선까지 고정한다.

### T20c. 로비/경주/정산 화면 컴포지션 + `App.tsx` 실마운트 + T15·T18·T19 이월 메모 해소 (M5, T20 마지막) — [x] 완료

M5 마일스톤 T20의 마지막 하위 항목이다. T20a에서 렌더 통합(`RaceCanvas`가 `<canvas>`를
마운트해 `createRenderLoop`↔`renderScene`을 실연결)이, T20b에서 라이프사이클 오케스트레이션
훅(`useGameController`, 베팅 확정→선차감→카운트다운→경주 구동→정산→로비 복귀 + 실황 emit +
탭 자동 일시정지)이 완성되었으나, **이들과 로비 UI(말 카드·베팅 패널·잔고·설정)·정산 표시를
phase에 따라 실제 화면으로 조립해 `App.tsx`에 마운트하는 지점**이 아직 없다. `App.tsx`는 현재
제목 한 줄과 `StorageBanner`·`BalanceDisplay`만 렌더한다. 이 태스크는 그 화면 컴포지션과
`App.tsx` 실마운트, 그리고 이전 UI 태스크가 T20으로 미룬 세 이월 메모(T15·T18·T19)를 해소한다.

소비할 모듈은 모두 기정의돼 있으며 재구현하지 않는다. 오케스트레이션은
`useGameController(store, options)`(`src/ui/useGameController.tsx:81`)가 노출하는 값
(`phase`·`balance`·`bankruptcyCount`·`settings`·`horses`·`lobbyEntries`·`raceState`·`machine`·
`settlement`·`commentaryMessages`·`handleBetConfirm`·`handleFrame`)을 그대로 소비한다. 표시
컴포넌트는 `HorseCard`(`HorseCardProps { entry }`)·`BetPanel`(`{ horses, balance, onConfirm }`)·
`BalanceDisplay`(`{ store }`)·`SettingsPanel`(`{ settings, bankruptcyCount, onSettingsChange,
onReset }`)·`RaceCanvas`(`{ initialState, horses, machine, onFrame, ... }`)·`CommentaryFeed`
(`{ messages }`)·`SettlementResult`(`{ won, payout, balanceAfter }`)·`StorageBanner`
(`{ visible }`)가 모두 기존재한다. GamePhase는 `lobby`·`countdown`·`racing`·`finish`·
`settlement` 5종이다(`src/domain/types.ts:44`, `src/store/machine.ts`).

App은 `bootstrap`에서 `createPersistence`→`load`→`createGameStore`로 store와 `storageDisabled`를
얻고, `useGameController`로 오케스트레이션을 배선한 뒤 phase에 따라 화면을 조립한다.

- **acceptance**
  - `App.tsx`가 phase에 따라 화면을 조립해 실마운트한다. jsdom + `@testing-library/react`로 아래를
    단언한다(주입 driver 또는 미리 구성한 store를 넘겨 결정적으로 검증).
    - `lobby`: 말 카드 목록(`lobbyEntries` 각 항목당 `HorseCard`)·`BetPanel`·`BalanceDisplay`·
      `SettingsPanel`이 렌더된다. `BetPanel.onConfirm`은 `handleBetConfirm`에 연결된다.
    - `countdown`/`racing`/`finish`: `RaceCanvas`(`onFrame`=`handleFrame`, `machine`=컨트롤러
      `machine`)와 `CommentaryFeed`(`messages`=`commentaryMessages`)가 렌더된다. `RaceCanvas`는
      `raceState`가 준비된 뒤에만 마운트한다(카운트다운 중 `raceState===null`이면 미마운트).
    - `settlement`: `SettlementResult`(`settlement`의 `won`·`payout`·`balanceAfter`)가 렌더된다.
    - `StorageBanner`는 phase와 무관하게 저장 비활성 상태를 반영해 노출된다.
  - **T15 이월 메모 해소**: `App`의 `props.store` 주입 경로가 `storageDisabled`를 항상 `false`로
    고정하던 테스트 DI 전용 분기를 실제 저장 상태를 반영하는 경로로 통합한다. 저장 상태(비활성
    여부)를 store와 분리해 주입 가능하게 하거나 `props.store`와 함께 저장 상태를 넘길 수 있는
    표면을 두어, store를 직접 주입하면서도 `StorageBanner.visible`이 실제 저장 비활성 여부를
    반영함을 값으로 단언한다(저장 비활성 driver 주입 시 배너 노출, 정상 driver 시 미노출).
    부트스트랩 1회 결정이 아니라 현재 저장 상태를 반영하는지 단언한다.
  - **T18 이월 메모 해소**: 베팅 패널 실마운트 시 (1) 미입력 상태(`amount === null`)에서
    `role="alert"` 검증 메시지가 노출되지 않음, (2) `type="number"` 직접 입력의 소수(예: `100.5`)
    에서 "정수 아님" 사유가 노출됨을 고정하는 테스트를 둔다.
  - **T19 이월 메모 해소**: 설정 화면 실마운트 시 아래를 단언·실연결한다.
    - 초기화 "확인" 경로에서 인라인 확인 영역이 닫히고 "데이터 초기화" 버튼이 복귀하는 회귀 단언.
    - `onSettingsChange`를 store `settings` 반영으로 실연결한다. 출전마 수 변경 시 카탈로그
      재생성이 반영되어 로비 말 카드 수가 변경된 출전마 수와 일치함을 값으로 단언한다.
    - `onReset`을 잔고·전적·설정 리셋과 저장 계층 리셋으로 실연결한다. 리셋 후 잔고가 기본값
      (10,000)으로 복귀함을 단언한다.
    - 음소거 `true→false` 반전 경로가 store `settings.muted`에 반영됨을 값으로 단언한다.
  - **T20b REVIEW 이월(권장) 흡수**: 컨트롤러를 통과한 `commentaryMessages`의 문자열에
    `{horseName}`·`{skillName}` 리터럴이 남지 않음을 실화면 자막(`CommentaryFeed`)을 통과한
    통합 스냅샷으로 직접 단언한다. 실황 이벤트가 발생하는 경주 프레임을 주입 rng·가짜 loop으로
    구동해 확인한다.
  - `npx vitest run`으로 위 단위/통합 테스트가 통과하고 기존 회귀가 없다.
  - `npx tsc --noEmit`가 종료 코드 0으로 통과한다.
- **touch**
  - `src/App.tsx`(phase별 화면 컴포지션·`useGameController` 배선·저장 상태 반영 경로 통합),
    `src/App.test.tsx`
  - 필요 시 phase별 화면 조립을 분리한 컴포넌트(예: `src/ui/LobbyScreen.tsx`·`RaceScreen.tsx`·
    App 내부 함수). 별도 파일이 불필요하면 `App.tsx` 내부에 둔다(T15~T20b 판단과 동일, 위반 아님).
  - `src/ui/SettingsPanel.tsx`·`src/ui/SettingsPanel.test.tsx`, `src/ui/BetPanel.test.tsx`는
    이월 메모 해소에 필요한 최소 변경·단언 추가에 한한다(표시 컴포넌트 자체 로직 재작성 금지).
  - 저장 상태 반영 통합에 필요하면 `useGameController`/부트스트랩 표면을 최소 확장할 수 있으나,
    T20b가 고정한 오케스트레이션 로직(라이프사이클·정산·실황 emit·탭 일시정지)은 재작성하지 않는다.
- **참고**
  - 모듈 경계: `App.tsx`/화면 컴포넌트는 오케스트레이션(`useGameController`)과 표시 컴포넌트를
    조립하는 컴포지션 계층에 한정한다. 정산 계산·순위 산출·회차 변동·배당·실황 문구 선택·상태
    전이는 재구현하지 않고 기존 함수/훅을 소비한다.
  - 아키텍처 결정: phase별 조건부 렌더의 형태(단일 App 내 분기 vs 화면 컴포넌트 분리)는 되돌리기
    쉬운 설계 결정으로 가장 단순한 형태를 택하고 근거를 IMPL.md에 남긴다.
  - 저장 상태 반영 표면(store와 별도 주입 vs 부트스트랩 결과에 포함): jsdom에서 결정적으로
    단언 가능한 가장 단순한 형태를 택하되, `props.store` 주입 시에도 실제 저장 비활성 여부가
    배너에 반영되어야 한다는 acceptance를 충족한다.
  - 실화면 시인성(슬로모션 체감·실황 자막 타이밍·전환 부드러움·폭죽 밀도·색 대비)과 역전 빈도
    밴드 좁히기(T9 REVIEW 메모 1)는 픽셀 확인 수단이 없어 미검증 항목으로 남긴다(감점 아님).
    실브라우저 `npm run dev` 수동 확인 몫이며, M6 마감에서 PRD 9번 성공 기준과 함께 재확인한다.
  - **구현 결정(IMPL.md 요약)**: phase별 조건부 렌더는 별도 화면 컴포넌트 없이 `App.tsx` 내부
    분기로 처리했다(단순, T15~T20b와 동일 기준). 설정 변경·초기화는 `gameStore.ts`를 건드리지
    않고(touch 범위 밖) App이 `store` 자체를 새 인스턴스로 교체하는 방식으로 구현했다. 저장
    상태는 store 주입 여부와 무관하게 항상 `persistence`를 만들어 반영한다(부트스트랩 1회 고정
    탈피). 지속적 자동 저장(매 상태 변경마다 `persistence.save`)과 `records`(전적) 갱신 로직은
    T20c acceptance 범위 밖이라(기존 어떤 태스크도 `records` 갱신을 구현한 적 없음) 다루지
    않았다 — PRD 9번의 "저장 지속" 확인 시점(M6 마감)에 재검토가 필요한 기존 공백으로 남긴다.

### T20b. 전체 게임 루프 오케스트레이션 (베팅 확정→경주 생성→상태 전이→정산→실황 emit + 탭 일시정지 실연결) (M5) — [x] 완료

M5 마지막 마일스톤 T20의 두 번째 하위 항목. T20a까지 렌더 통합(`RaceCanvas`가 `<canvas>`를
마운트해 `createRenderLoop`↔`renderScene`을 실연결)이 끝났으나, **베팅 확정에서 정산·로비
복귀까지의 라이프사이클을 실제 store·경주 엔진·실황 문구와 배선하는 지점**이 아직 없었다. 이
태스크는 그 오케스트레이션 컨트롤러/훅과 순수 헬퍼까지만 다뤘다. 로비/경주/정산 화면 컴포지션과
`App.tsx` 실마운트, T15·T18·T19 이월 메모 해소는 T20c의 몫이다.

소비할 모듈은 모두 기정의돼 있으며 재구현하지 않는다. 상태 전이는
`createGameStore.dispatch`(`src/store/gameStore.ts:58`)와 상태 머신 이벤트(`START_COUNTDOWN`·
`START_RACE`·`FINISH`·`SETTLE`·`RESET`·`PAUSE`·`RESUME`, `src/store/machine.ts:3-10`), 잔고
증감·파산 재충전은 `adjustBalance`(`gameStore.ts:62`), 회차 변동 스탯·배당 스냅샷 조립은
`buildLobbyEntries`(`src/ui/lobbyEntries.ts:30`), 경주 초기화·구동은 `createRaceState`/`step`을
감싼 `createRenderLoop`(`src/render/loop.ts:17`, `RenderLoopMachine`=`isPaused`/`dispatch`
어댑터 소비), 정산은 `calculateSettlement`(`src/domain/settlement.ts:20`), 실황 문구는
`pickCommentaryLine`(`src/ui/commentary.ts:58`)이다. 탭 자동 일시정지는 `createRenderLoop`가
이미 `VisibilitySource`→`machine.dispatch("PAUSE"/"RESUME")`로 처리하므로(`loop.ts:30-39`),
T20b는 store를 감싼 `RenderLoopMachine` 어댑터와 실 `document` visibility 소스를 주입해
PAUSE/RESUME이 실제 store `paused`에 반영되게 연결한다.

카운트다운 지속 시간(로비→경주 진입 지연)처럼 PRD에 수치가 명시되지 않은 값은 되돌리기 쉬운
결정으로 generator가 정하고, 결정적 테스트가 가능하도록 타이머·rng·raf·visibility를 주입
가능하게 감싼다. 근거는 IMPL.md에 남긴다.

- **acceptance**
  - `src/ui/`에 라이프사이클 오케스트레이션 컨트롤러/훅이 존재하고, 아래 전체 흐름을 배선한다.
    베팅 확정(선택 말 id·금액) → 선차감 `adjustBalance(-betAmount)` → `dispatch("START_COUNTDOWN")`
    → (주입 타이머 경과 후) `dispatch("START_RACE")` → 경주 구동(`createRenderLoop`) → 완주
    (`state.finished`) 시 `dispatch("FINISH")` → 정산(`calculateSettlement`로 지급액 산출 후
    `adjustBalance(+balanceChange)`) → `dispatch("SETTLE")` → `dispatch("RESET")`로 로비 복귀.
    jsdom + `@testing-library/react`로 주입 store·가짜 loop/raf·주입 타이머로 배선을 검증한다.
  - 경주 생성은 로비 스냅샷을 재사용한다. `buildLobbyEntries`로 얻은 `HorseRaceEntry[]`(회차
    변동 `currentStats`·`odds` 포함)를 `RaceParticipant[]`(`{ id, stats: currentStats, skillId }`,
    `src/sim/types.ts:7`)로 변환해 경주를 초기화하고, **같은 스냅샷의 `odds`로 정산**한다. 베팅
    스탯 변동·배당을 정산 시점에 다시 굴려 로비 표시와 어긋나지 않게 함을 값으로 단언한다(변환·
    정산이 소비하는 `currentStats`/`odds`가 로비에 표시된 스냅샷과 동일).
  - 정산 승패 판정은 완주 순위(`rankings`의 `rank === 1`)의 말 id가 베팅 말 id와 같으면 적중이다.
    적중 시 `calculateSettlement({ betAmount, odds: 베팅 말 스냅샷 odds, won: true }).balanceChange`
    (=지급액)만큼 `adjustBalance`로 증가하고, 미적중 시 증감 0임을 값으로 단언한다. 정산 계산·
    파산 재충전을 재구현하지 않고 `calculateSettlement`·`adjustBalance` 내부(`gameStore.ts:45-50`)를
    소비한다.
  - 탭 자동 일시정지 실연결: store `dispatch`/`getState().paused`를 감싼 `RenderLoopMachine`
    어댑터(`isPaused`/`dispatch`)와 실 `document` visibility 소스를 loop에 주입해, racing 중
    visibility hidden에서 store `paused=true`, 복귀 시 `paused=false`로 전이됨을 단언한다. 복귀
    직후 큰 dt 점프가 시뮬레이션에 소비되지 않는 `loop.ts`의 기존 재동기화 전제를 깨지 않는다.
  - 실황 문구 emit: 프레임 간 경주 상태에서 실황 이벤트(출발·선두 교체·스킬 발동·최종 직선
    진입·접전·결승선 통과)를 도출하는 순수 함수와, 도출된 이벤트를 `pickCommentaryLine`으로
    문구화해 중계 피드에 쌓는 배선이 존재한다. 선두 교체는 `rank===1` 말 id가 프레임 간 바뀔 때,
    스킬 발동은 러너의 `skillActivated`가 false→true로 바뀔 때(`skillActivatedAt` 설정) 도출됨을
    단언한다.
  - **T16 이월 메모 해소**: 대상이 있는 이벤트(`lead-change`·`skill-activation`·`finish`)에서
    필수 파라미터(`horseName`·`skillName`)를 항상 채운다. 말 이름은 카탈로그(`HorseProfile.name`)에서,
    스킬 표시명은 `SKILL_CATALOG`(`src/domain/horses.ts`) 한글 표시명에서 가져와, `pickCommentaryLine`
    결과에 `{horseName}`·`{skillName}` 리터럴이 남지 않음을 값으로 단언한다(누락 시 폴백 선택 포함).
  - **T20a 이월 메모 해소**: 컨트롤러가 `RaceCanvas`에 넘기는 `initialState`·`machine`·`horses`
    참조를 `useMemo`/`useRef` 등으로 안정화해, 무관한 리렌더에서 `RaceCanvas`의 `useEffect`가
    loop을 재시작하지 않음을 렌더 횟수 또는 loop start 호출 횟수로 단언한다(`RaceCanvas.tsx:126`
    의존성 배열 재시작 방지, T20a REVIEW 이월).
  - `npx vitest run`으로 위 단위/통합 테스트가 통과하고 기존 회귀가 없다.
  - `npx tsc --noEmit`가 종료 코드 0으로 통과한다.
- **touch**
  - `src/ui/raceLifecycle.ts`(순수 헬퍼: `HorseRaceEntry[]`→`RaceParticipant[]` 변환, 프레임 간
    실황 이벤트 도출, 베팅 말 id·순위·스냅샷 odds→`SettlementInput` 조립), `src/ui/raceLifecycle.test.ts`
  - `src/ui/useGameController.tsx`(store·loop·타이머·visibility를 배선하는 오케스트레이션 훅/컨트롤러),
    `src/ui/useGameController.test.tsx`
  - `src/ui/RaceCanvas.tsx`(컨트롤러가 완주·프레임 상태를 관찰할 콜백 prop 추가 및 참조 안정화 연동에
    한함. 단일 loop 유지 — 두 번째 loop을 만들지 않는다), `src/ui/RaceCanvas.test.tsx`(콜백 단언 추가)
  - 필요 시 `src/ui/types.ts`(컨트롤러·헬퍼 인자/이벤트 타입). 별도 파일이 불필요하면 기존 파일에
    둔다(T15~T20a 판단과 동일, 위반 아님).
- **참고**
  - 모듈 경계: 순수 헬퍼(`raceLifecycle.ts`)는 `src/domain`·`src/sim`·`src/ui`의 타입/문구
    모듈과 rng만 의존하는 순수 로직으로 두고, store·loop 부수효과는 훅(`useGameController.tsx`)에
    격리한다. 정산 계산·파산 재충전·회차 변동·배당·순위 산출·슬로모션 판정은 재구현하지 않고
    기존 함수를 소비한다.
  - 아키텍처 결정: `RaceCanvas`가 loop을 소유(T20a)하므로 컨트롤러는 두 번째 loop을 만들지 않고,
    `RaceCanvas`가 노출하는 완주/프레임 콜백으로 라이프사이클을 관찰한다. 콜백 표면(onFinish 단일
    콜백 vs onFrame 전달)은 되돌리기 쉬운 설계 결정으로 가장 단순한 형태를 택하고 근거를 IMPL.md에
    남긴다.
  - 로비/경주/정산 **화면 조립**(말 카드 목록·베팅 패널·잔고·설정·`SettlementResult`·`RaceCanvas`
    실배치)과 `App.tsx` 실마운트, T15·T18·T19 이월 메모 해소는 T20c의 몫이다. T20b는 "이벤트를
    받아 상태를 전이하고 값을 계산·emit하는" 오케스트레이션 로직까지만 고정한다.
  - 카운트다운 지속 시간·정산 후 로비 복귀 트리거(자동 지연 vs 사용자 확인)는 되돌리기 쉬운 결정이다.
    PRD 3장 게임 루프에 부합하는 가장 단순한 기준을 택하고 주입 타이머로 결정적 테스트가 가능하게
    하며 근거를 IMPL.md에 남긴다.
  - 실화면 시인성(슬로모션 체감·실황 자막 타이밍·전환 부드러움)과 역전 빈도 밴드 좁히기(T9 REVIEW
    메모 1)는 픽셀 확인 수단이 없어 미검증 항목으로 남긴다(감점 아님). T20c에서 `npm run dev` 수동
    확인 몫이다.
  - **구현 결정(IMPL.md 요약)**: 콜백 표면은 `onFrame` 단일 콜백을 택했다(완주만 알리는
    `onFinish`보다 경주 중 실황 이벤트까지 같은 핸들러에서 관찰 가능해 더 단순함). 카운트다운
    3000ms·정산 표시 4000ms를 기본값으로 정하고 둘 다 주입 가능하게 했다. 정산 후 로비 복귀는
    자동 지연을 택했다(PRD 3장이 순환을 전제, 사용자 확인 UI 불필요). 경주 생성·정산은 베팅
    확정 시점에 고정한 로비 스냅샷(`activeBet.entries`)을 그대로 재사용한다.

### T20a. 주입식 RenderContext 어댑터 + `renderScene` 조합 함수 + `<canvas>` 마운트 컴포넌트 (M5, 렌더 통합) — [x] 완료

M5의 마지막 마일스톤 T20의 첫 하위 항목. M4까지 렌더 함수(트랙·말·스킬 이펙트·순위표·
피니시 배너·우승마 스포트라이트·폭죽 파티클)와 주입식 렌더 루프(`createRenderLoop`,
`src/render/loop.ts`)가 모두 순수/주입식으로 완성되었으나, 이들을 **한 프레임 전체를
그리는 하나의 경로로 묶어 실제 `<canvas>`에 연결하는 지점**이 아직 없다. 이 태스크는
(1) `loop.onFrame`이 소비할 순수 조합 함수 `renderScene`과, (2) 브라우저
`CanvasRenderingContext2D`를 M4 `RenderContext`로 위임하는 어댑터 + `<canvas>`를 마운트해
loop↔`renderScene`을 실연결하는 React 컴포넌트까지만 다룬다. 베팅 확정→경주 생성→상태
전이→정산→실황 emit의 라이프사이클 오케스트레이션은 T20b, 로비/경주/정산 화면 컴포지션과
`App.tsx` 실마운트는 T20c의 몫이다.

하네스 제약: jsdom은 `canvas.getContext("2d")`를 구현하지 않고 이 하네스는 Canvas 픽셀을
화면으로 확인할 수단이 없다. 따라서 ctx·raf·visibility 소스를 주입 가능하게 감싸(M4가 이미
`RenderContext`·`RafSource`·`VisibilitySource`를 주입식으로 정의) mock ctx·가짜 raf로 배선을
검증하고, 실화면 시인성(폭죽 밀도·슬로모션 체감·색 대비)은 미검증 항목으로 명시한다(감점
아님, PRD 9번 성공 기준의 일부는 실브라우저 수동 확인 몫).

- **acceptance**
  - `src/render/`에 한 프레임 전체를 그리는 순수 조합 함수 `renderScene`이 존재한다.
    `computeRaceLayout`(`src/render/layout.ts`)으로 좌표를 얻어 `renderRace`(트랙·말·스킬
    이펙트·순위표)를 호출하고, 완주 상태(`state.finished`)에서는 `drawFinishBanner`·
    `drawWinnerSpotlight`·`drawFireworkParticles`를 정해진 순서로 함께 호출한다. 좌표·순위·
    발동 이력·파티클 물리를 재구현하지 않고 기존 M4 함수(`renderRace`·`finishFx`·`particles`)를
    소비한다. `runnersMeta`(번호·이름·색, PRD 5번)와 `skillRunners`(`SkillActivationInfo[]`)는
    각각 말 카탈로그(`HorseProfile[]`)와 `state.runners`에서 파생하는 소형 순수 헬퍼로 만든다
    (`src/render`가 `src/store`·`src/sim` 엔진을 직접 import하지 않도록 타입·도메인만 의존).
  - `renderScene`은 여러 그리기를 한 프레임에 호출할 때 상태가 전이되지 않도록 격리한다.
    이 태스크에서 `drawFinishBanner`에 `save()`/`restore()`를 추가해(T13/T14 REVIEW 이월 메모)
    배너 그리기가 이후 그리기의 `fillStyle`·`font` 등에 누수되지 않음을 값으로 고정한다.
    hidden(일시정지) 프레임에서 재그리기를 건너뛸지 유지할지의 렌더 정책을 확정하고, 그
    경계 동작을 테스트로 고정한다(T10 REVIEW 메모 2).
  - `src/ui/`(또는 `src/render/`, 되돌리기 쉬운 배치 결정)에 브라우저
    `CanvasRenderingContext2D`를 M4 `RenderContext`로 얇게 위임하는 어댑터와, `<canvas>`를
    마운트해 ctx를 얻어 `createRenderLoop`를 구동하고 `onFrame`을 `renderScene`에 연결하는
    React 컴포넌트가 존재한다. ctx·raf·visibility 소스를 주입 가능하게 감싸 테스트에서
    mock ctx·가짜 raf로 대체할 수 있다. `getState()`/`onFrame`이 매 프레임 넘기는 `RaceState`
    참조가 교체되어도(gameStore·loop 계약) 렌더 경로가 그 프레임 값만 안전하게 소비함을
    확인한다(T10 REVIEW 메모 3, 상태 보관·비교 없이 소비).
  - `npx vitest run`으로 아래 단위 테스트가 통과한다. 최소 검증 항목:
    - **미완주 프레임**: `state.finished=false`인 상태로 `renderScene`을 호출하면 트랙·말·
      순위표 그리기 명령이 나오고, 피니시 배너·스포트라이트·폭죽 그리기 명령은 나오지 않음을
      mock ctx로 단언한다.
    - **완주 프레임**: `state.finished=true`인 상태로 호출하면 피니시 배너·스포트라이트·폭죽
      그리기가 함께 호출되고, 우승마(1위) 좌표가 `computeRaceLayout` 결과와 일치함을 단언한다.
    - **상태 격리**: `drawFinishBanner` 호출 전후로 ctx 상태가 격리됨(`save`/`restore` 쌍
      호출, 배너의 `fillStyle`·`font` 설정이 이후 그리기로 누수되지 않음)을 값으로 단언한다.
    - **hidden 프레임 렌더 정책**: 확정한 정책(건너뛰기 또는 유지)대로 hidden(paused) 프레임에서
      그리기 명령 발생 여부가 결정됨을 단언한다.
    - **canvas 컴포넌트 배선**: `RaceCanvas`를 mock ctx·가짜 raf로 마운트한 뒤 프레임을
      진행시키면 `renderScene`(→mock ctx 그리기)이 호출됨을, 언마운트 시 `loop.stop()`으로
      raf가 취소되고 그리기가 멎음을 `@testing-library/react`로 단언한다.
  - `npx tsc --noEmit`가 종료 코드 0으로 통과한다.
- **touch**
  - `src/render/renderScene.ts`(한 프레임 조합 함수 + runnersMeta·skillRunners 파생 헬퍼),
    `src/render/renderScene.test.ts`
  - `src/render/finishFx.ts`(`drawFinishBanner`에 `save()`/`restore()` 상태 격리 추가에 한함),
    `src/render/finishFx.test.ts`(격리 단언 추가)
  - `src/ui/RaceCanvas.tsx`(브라우저 ctx→`RenderContext` 어댑터 + `<canvas>` 마운트 + loop
    구동·`onFrame`↔`renderScene` 연결), `src/ui/RaceCanvas.test.tsx`
  - 필요 시 `src/render/types.ts`(어댑터·조합 함수 인자 타입). 별도 파일이 불필요하면 기존
    파일에 둔다(T15~T19b 판단과 동일, 위반 아님).
- **참고**
  - 모듈 경계: `renderScene`은 `src/render`의 기존 함수와 도메인 타입만 소비하고 `src/store`·
    `src/sim` 엔진을 직접 import하지 않는다(loop이 이미 `advanceWithAccumulator`로 sim을
    소비하므로 렌더 조합 함수는 상태를 그리기만 한다). 파티클 생성·갱신(`createFireworkParticles`·
    `updateParticles`)의 상태 관리는 렌더 소유의 관심사이므로 `RaceCanvas` 프레임 처리 또는
    `renderScene` 인자로 다루되, 물리 규칙은 재구현하지 않고 `src/render/particles.ts`를 소비한다.
  - 베팅 확정·경주 생성·상태 전이·정산·실황 emit·`visibilitychange` 실 `document` 연결은
    T20b, 로비/경주/정산 화면 조립과 `App.tsx` 실마운트는 T20c의 몫이다. T20a는 "한 프레임을
    그려 canvas에 붙이는" 렌더 통합까지만 고정한다.
  - ctx 어댑터·`RaceCanvas` 배치(`src/ui` vs `src/render`)와 hidden 프레임 렌더 정책은
    되돌리기 쉬운 결정이다. 가장 단순하고 테스트 가능한 형태를 택하고 근거를 IMPL.md에 남긴다.
  - 실화면 시인성(폭죽 밀도·슬로모션 체감·배너 가독성·색 대비)과 역전 빈도 밴드 좁히기
    (T9 REVIEW 메모 1)는 픽셀 확인 수단이 없어 미검증 항목으로 남긴다(감점 아님).
  - **구현 결정(IMPL.md 요약)**: hidden 프레임 렌더 정책은 "계속 그린다"를 택했다(loop이
    hidden 중에도 매 프레임 `onFrame`을 호출하고 상태가 변하지 않아 재그리기 비용이
    낮으며, 별도 visibility 이중 구독을 피할 수 있다). ctx 어댑터·`RaceCanvas`는
    `src/ui/RaceCanvas.tsx`에 두었다(구조적으로 이미 호환되는 캐스팅뿐이라 별도 파일
    불필요). 폭죽 파티클 상태는 `RaceCanvas`가 소유하며 `state.elapsedTime` 차이를
    dt로 삼아 갱신한다.

### T19b. 정산 결과 표시 + 순수 정산 계산 함수 (M5) — [x] 완료

M5의 여섯 번째 태스크. 한 회차 경주가 끝난 뒤의 **정산**(PRD 4.3·3장 정산)을 두 조각으로
세운다. (1) 베팅액·배당률·적중 여부를 받아 지급액과 잔고 증감을 산출하는 **순수 정산 계산
함수**, (2) 그 결과(적중/미적중·지급액·잔고 갱신)를 표시하는 **React 컴포넌트**. 이 태스크는
순수 계산과 표시 UI까지만 다룬다. 실제 경주 결과에서 정산 뷰모델을 조립하고 `adjustBalance`로
잔고에 반영하는 배선은 전체 게임 루프를 오케스트레이션하는 T20의 몫이다(T15~T19와 동일한
순수 헬퍼·표시 컴포넌트 경계).

정산 규칙은 PRD 4.3에 명시돼 있다. 베팅은 **베팅 시점에 선차감**되므로(PRD 4.3), 정산
시점의 잔고 증감은 적중 시 `베팅액 × 배당률`(지급액)만큼 증가, 미적중 시 추가 증감 없음(0)이다.
지급액은 소수 잔액이 생기지 않도록 반올림 정책을 계산 함수 안에서 확정하고 근거를 IMPL.md에
남긴다(되돌리기 쉬운 표시·계산 결정). 배당률은 `src/domain/odds.ts`의
`calculateOdds` 결과(소수점 1자리 노출, PRD 4.3)를 소비하는 값으로 받는다.

- **acceptance**
  - 순수 정산 계산 함수가 존재하고, 베팅액·배당률·적중 여부를 입력받아 지급액과 잔고 증감을
    반환한다. 적중 시 지급액 = `round(베팅액 × 배당률)`, 잔고 증감 = 지급액(선차감 전제);
    미적중 시 지급액 = 0, 잔고 증감 = 0을 값으로 단언한다. 렌더·React·store에 의존하지 않는
    순수 함수로 두어 결정적 테스트가 가능하게 한다.
  - 경계·검증: 베팅액이 최소 베팅액(100) 미만이거나 배당률이 1 미만인 비정상 입력에 대한
    동작(방어적 처리 또는 명시적 계약)을 테스트로 고정한다. 반올림 경계(예: `100 × 3.25 = 325`
    또는 소수 배당률 곱의 반올림)를 값으로 단언한다.
  - 정산 결과 표시 컴포넌트가 존재하고, 정산 계산 결과(적중/미적중·지급액·정산 후 잔고)를
    props로 받아 렌더링한다. 적중과 미적중 각각에서 표시 문구·지급액이 값으로 구분됨을
    jsdom + `@testing-library/react`로 단언한다. 색상만으로 결과를 구분하지 않도록 텍스트로
    적중/미적중을 병기한다(PRD 5번 접근성).
  - `npx vitest run`으로 위 단위 테스트가 통과한다.
  - `npx tsc --noEmit`가 종료 코드 0으로 통과한다.
- **touch**
  - 순수 정산 계산 함수 파일(`src/domain/settlement.ts` 권장; `src/ui/`도 가능한 되돌리기 쉬운
    배치 결정, 근거는 IMPL.md에 남긴다)과 그 테스트.
  - `src/ui/SettlementResult.tsx`(정산 결과 표시 컴포넌트), `src/ui/SettlementResult.test.tsx`.
  - 필요 시 `src/ui/`의 소형 순수 헬퍼. 별도 파일이 불필요하면 컴포넌트 내부로 둔다(T15~T19
    판단과 동일, 위반 아님).
- **참고**
  - 모듈 경계: 정산 계산 함수는 순수 로직이며 `src/render`·`src/store`·React를 참조하지 않는다.
    표시 컴포넌트는 계산 결과와 도메인 타입만 소비하고 `src/sim`을 참조하지 않는다. 실제 경주
    결과에서 정산 뷰모델을 조립하고 `adjustBalance(delta)`로 잔고에 반영하는 배선은 T20에서
    store와 연결한다. 파산 자동 재충전(PRD 4.4)은 `adjustBalance` 내부(`gameStore.ts:46-48`)가
    이미 처리하므로 정산 계산 함수는 재충전을 재구현하지 않는다.
  - 배당률·최소 베팅액 등 기존 상수는 재정의하지 않고 `src/domain/odds.ts`·
    `src/store/gameStore.ts`(`MIN_BET_AMOUNT`)에서 재사용한다.
  - 반올림 정책(내림/반올림/버림)과 정산 결과 표시 문구·레이아웃은 되돌리기 쉬운 표시 결정이다.
    가장 단순하고 사용자에게 잔액 왜곡이 적은 형태를 택하고 근거를 IMPL.md에 남긴다.
  - 시각 완성도(정산 화면 배치·색 대비·여백 등 실브라우저 시인성)와 로비/경주/정산 화면 전환
    배선은 T20/M6에서 다룬다. T19b는 시맨틱 마크업·정산 계산 로직까지 고정한다.

### T19. 설정 화면 (출전마 수 4~8 + 음소거 토글 + 데이터 초기화 확인 대화상자) (M5) — [x] 완료

M5의 다섯 번째 태스크. 로비에서 접근하는 **설정 화면**을 만든다(PRD 4.9). 이 태스크는
설정 값의 표시·변경 UI와 데이터 초기화 확인 대화상자까지의 **React 컴포넌트와 상호작용
게이팅**만 다룬다. 설정 변경이 실제 store `settings`에 반영되어 말 카탈로그를 재생성하거나,
초기화가 실제 잔고·전적·설정을 리셋하고 저장에 반영되는 배선은 전체 게임 루프를
오케스트레이션하는 T20의 몫이다. T19는 그 오케스트레이션이 소비할 "검증된 설정 변경"과
"초기화 확정" 이벤트를 콜백(props)으로 위로 전달하는 지점까지 세운다(T15~T18과 동일한
UI·순수 헬퍼 경계).

설정 항목은 PRD 4.9에 명시돼 있다. 출전마 수는 `MIN_HORSE_COUNT`(4)~`MAX_HORSE_COUNT`(8),
기본 `DEFAULT_HORSE_COUNT`(5)를 `src/persistence/schema.ts`에서 재사용하고 상수를
재정의하지 않는다. 음소거는 boolean 토글이며, 이 태스크는 상태 표시·변경 콜백까지만
다루고 실제 오디오 제어는 M6이다. 데이터 초기화는 확인 대화상자를 반드시 거친 뒤에만
초기화 콜백을 호출한다(PRD 4.9: 확인 대화상자 필수). `GameSettings` 타입은
`src/persistence/schema.ts`의 기정의 타입을 재사용한다.

- **acceptance**
  - `src/ui/`에 설정 화면 컴포넌트가 존재한다. 현재 설정(`GameSettings`: `horseCount`,
    `muted`)과 파산 횟수 등 표시에 필요한 값을 props로 받아, (1) 출전마 수를 4~8 범위에서
    선택할 수 있고(범위 밖 값은 선택 불가), (2) 음소거 on/off를 토글할 수 있으며,
    (3) 데이터 초기화 버튼을 제공한다. 값 변경 시 변경된 설정을 콜백(props)으로 전달한다.
    jsdom + `@testing-library/react`로 마운트·상호작용을 검증한다.
  - 데이터 초기화는 확인 대화상자를 거친다. 초기화 버튼을 눌러도 곧바로 초기화 콜백이
    호출되지 않고, 확인 단계에서 "확인"을 선택했을 때만 초기화 콜백이 1회 호출되며,
    "취소"를 선택하면 초기화 콜백이 호출되지 않음을 `@testing-library/react`로 단언한다.
    (확인 대화상자는 `window.confirm` 대신 jsdom에서 상호작용을 직접 검증할 수 있는
    컴포넌트 내부 UI로 구현한다. 되돌리기 쉬운 표시 결정으로 근거는 IMPL.md에 남긴다.)
  - 출전마 수 변경 시 변경 콜백이 새 `horseCount` 값(4~8)으로 호출되고, 음소거 토글 시
    변경 콜백이 반전된 `muted` 값으로 호출됨을 값으로 단언한다.
  - `npx vitest run`으로 위 단위 테스트가 통과한다.
  - `npx tsc --noEmit`가 종료 코드 0으로 통과한다.
- **touch**
  - `src/ui/SettingsPanel.tsx`(설정 화면 컴포넌트), `src/ui/SettingsPanel.test.tsx`
  - 필요 시 `src/ui/`의 소형 순수 헬퍼(예: 출전마 수 옵션 목록 생성). 별도 파일 생성이
    불필요하면 컴포넌트 내부로 둔다(T15~T18 판단과 동일, 위반 아님).
- **참고**
  - 모듈 경계: 설정 화면은 `src/persistence/schema.ts`의 `GameSettings` 타입과
    `MIN_HORSE_COUNT`·`MAX_HORSE_COUNT`·`DEFAULT_HORSE_COUNT` 상수만 재사용하고
    `src/sim`을 참조하지 않는다. 설정의 실제 store 반영(카탈로그 재생성·저장)과
    초기화의 실제 리셋 배선은 T20에서 store `dispatch`/저장 계층과 연결한다. T19는
    변경·초기화 이벤트를 콜백으로 위로 넘기는 지점까지만 고정한다.
  - 확인 대화상자 구현 방식(2단계 인라인 확인 vs 모달)과 출전마 수 입력 UI(select
    드롭다운 vs 라디오 vs 스텝퍼)는 되돌리기 쉬운 표시 결정이다. 가장 단순하고 jsdom에서
    상호작용 검증이 가능한 형태를 택하고 근거를 IMPL.md에 남긴다.
  - 시각 완성도(설정 화면 배치·버튼 대비·여백 등 실브라우저 시인성)와 로비/설정 화면 간
    전환 배선은 T20/M6에서 다룬다. T19는 시맨틱 마크업·상호작용 게이팅·확인 대화상자
    로직까지 고정한다.
  - 실제 오디오 제어는 M6이다. T19의 음소거 토글은 설정 상태 표시·변경 콜백까지만 다룬다.

### T18. 베팅 패널 (프리셋 100/500/1,000/올인 + 직접입력 + 검증) (M5) — [x] 완료

M5의 네 번째 태스크. 로비에서 사용자가 **한 마리를 선택하고 베팅 금액을 설정해
베팅을 확정**하는 베팅 패널을 만든다(PRD 4.3). 이 태스크는 선택·금액 입력·검증·
확정 이벤트 발신까지의 **UI와 순수 검증 로직**만 다룬다. 확정 이후의 상태 전이
(카운트다운 시작)·잔고 선차감(`adjustBalance`)·경주 생성 배선은 전체 게임 루프를
오케스트레이션하는 T20의 몫이다. T18은 그 오케스트레이션이 소비할 "검증된 베팅
확정"을 콜백으로 위로 전달하는 지점까지 세운다.

베팅 규칙은 PRD 4.3·4.4에 명시돼 있다. 최소 베팅액은 `MIN_BET_AMOUNT`
(`src/store/gameStore.ts`, 값 100)를 재사용하고 재정의하지 않는다. 상한은 현재
잔고다. 프리셋은 100/500/1,000/올인(=현재 잔고 전액)이며, 잔고보다 큰 프리셋
버튼은 비활성 또는 잔고로 클램프한다(되돌리기 쉬운 표시 결정으로 generator가
정하고 근거를 IMPL.md에 남긴다). 직접 입력은 정수만 허용하고 범위를 벗어나면
확정 버튼을 비활성화하고 사유를 노출한다.

- **acceptance**
  - `src/ui/`에 베팅 금액을 검증하는 순수 함수가 존재한다. 입력(금액·잔고)을 받아
    유효/무효와 무효 사유(최소 미만·잔고 초과·정수 아님 등)를 반환하며,
    `MIN_BET_AMOUNT`를 `src/store/gameStore.ts`에서 import해 재사용하고 상수를
    재정의하지 않는다. `src/sim`을 import하지 않는다.
  - `src/ui/`에 베팅 패널 컴포넌트가 존재한다. 출전마 목록에서 한 마리를 선택하고
    (선택 상태가 DOM에 드러남), 프리셋 버튼(100/500/1,000/올인)과 직접 입력으로
    금액을 설정하며, 유효한 선택·금액일 때만 베팅 확정 버튼이 활성화된다. 확정 시
    선택한 말 id와 금액을 콜백(props)으로 전달한다. jsdom + `@testing-library/react`로
    마운트·상호작용을 검증한다.
  - `npx vitest run`으로 아래 단위 테스트가 통과한다. 최소 검증 항목:
    - **검증 함수**: 100 미만이면 무효(최소 미만), 잔고 초과면 무효(잔고 초과),
      정수가 아니면 무효, 100 이상·잔고 이하 정수면 유효임을 값으로 단언한다.
      경계값(정확히 100, 정확히 잔고)에서 유효임을 단언한다.
    - **올인 프리셋**: 올인 선택 시 금액이 현재 잔고와 일치함을 단언한다.
    - **확정 게이팅**: 말 미선택 또는 무효 금액이면 확정 버튼이 비활성(또는 확정
      콜백이 호출되지 않음)이고, 유효한 선택·금액이면 확정 콜백이 선택 말 id·금액
      인자로 1회 호출됨을 `@testing-library/react`로 단언한다.
    - **무효 사유 노출**: 잔고를 초과하는 직접 입력 시 사유 문구가 DOM에 노출됨을
      단언한다.
  - `npx tsc --noEmit`가 종료 코드 0으로 통과한다.
- **touch**
  - `src/ui/betValidation.ts`(베팅 금액 검증 순수 모듈), `src/ui/betValidation.test.ts`
  - `src/ui/BetPanel.tsx`(베팅 패널 컴포넌트), `src/ui/BetPanel.test.tsx`
- **참고**
  - 모듈 경계: 검증 순수 모듈은 `src/store`의 `MIN_BET_AMOUNT` 상수와 도메인 타입만
    의존하고 `src/sim`을 참조하지 않는다. 베팅 확정 후의 상태 전이·선차감·경주 생성은
    T20 오케스트레이션에서 store `dispatch`/`adjustBalance`와 연결한다. T18은 확정
    이벤트를 콜백으로 위로 넘기는 지점까지만 고정한다.
  - 프리셋 클램프/비활성 정책(잔고보다 큰 프리셋 버튼 처리)과 직접 입력의 즉시 검증
    시점은 되돌리기 쉬운 표시 결정이다. 가장 단순한 기준을 택하고 근거를 IMPL.md에
    남긴다.
  - 시각 완성도(패널 배치·버튼 대비·입력 필드 여백 등 실브라우저 시인성)와 로비
    전체 레이아웃(HorseCard 목록 + 베팅 패널 + 잔고의 배치)은 T20/M6에서 다룬다.
    T18은 시맨틱 마크업·검증 로직·확정 게이팅까지 고정한다.
  - **구현 결정(IMPL.md 요약)**: 프리셋 클램프/비활성 정책은 "비활성화"를 택했다
    (클램프보다 사용자 의도가 분명하고, 잘못된 값이 amount 상태에 들어오지 않아
    구현이 단순함). 직접 입력의 즉시 검증은 값이 바뀔 때마다 즉시 재검증해 사유를
    노출한다(디바운스 없음, 가장 단순한 기준).

### T17. 로비 말 카드 (스탯·컨디션·배당률·전적·연승 배지) (M5) — [x] 완료

M5의 세 번째 태스크. 로비에서 각 출전마의 정보를 확인하고 베팅 판단 자료로
삼을 **말 카드**를 만든다(PRD 4.1·4.3·4.7·5번). 이 태스크는 (1) 카드가 소비할
`HorseRaceEntry`(도메인에 이미 정의된 타입)를 카탈로그·회차 변동 스탯·저장
`records`에서 조립하는 **순수 뷰모델 모듈**과, (2) 그 결과 한 건을 렌더링하는
**말 카드 컴포넌트**까지만 다룬다. 실제 로비 전체 레이아웃에 여러 카드를 배치하고
회차 진행에 맞춰 회차 변동을 다시 굴리는 배선(로비 화면 오케스트레이션)은 T18·T20의
몫이며, T17은 그 화면이 소비할 순수 조립 함수와 카드 한 장을 먼저 세운다.

조립에 필요한 도메인 함수는 이미 존재한다. 회차 변동은 `applyStatVariance`
(`src/domain/stats.ts`), 컨디션 5단계는 `getConditionLevel`(같은 파일), 추정 승률은
`estimateWinProbabilities`, 배당률은 `calculateOdds`(`src/domain/odds.ts`)다. T17은
이들을 재구현하지 않고 조립·표시만 담당한다. 연승 판정(연속 1위 수 산출)은 신규
순수 함수로 추가하고, "연승 배지"의 기준(연속 1위 2회 이상)은 되돌리기 쉬운 결정으로
generator가 정하고 근거를 IMPL.md에 남긴다.

- **acceptance**
  - `src/ui/`에 출전마 카탈로그(`HorseProfile[]`)·저장 `records`(`Record<string, RaceRecord>`)·
    주입 rng를 입력받아 각 말의 `HorseRaceEntry`(회차 변동 `currentStats`·`condition`·
    `winProbability`·`odds`·`record` 포함) 배열을 조립하는 순수 함수가 존재한다.
    `src/sim`·`src/store`를 import하지 않고 `src/domain`과 rng만 의존한다.
  - 연속 1위 수를 `recentResults`(최신이 앞)에서 산출하는 순수 함수와, 그것을 기준으로
    한 연승 배지 판정이 존재한다.
  - `src/ui/`에 `HorseRaceEntry` 한 건을 받아 렌더링하는 말 카드 컴포넌트가 존재하며,
    번호와 이름을 함께 표시(색상만으로 구분하지 않음, PRD 5번·13번)하고, 배당률을
    소수점 1자리(예: `3.2배`)로, 최근 5경기 성적과 전적(출전 수·우승 수·승률), 5단계
    컨디션 지표를 노출한다. 연승 조건을 만족하면 연승 배지를 표시한다.
    jsdom + `@testing-library/react`로 마운트·검증한다.
  - `npx vitest run`으로 아래 단위 테스트가 통과한다. 최소 검증 항목:
    - **뷰모델 조립 결정론**: 동일 rng 시퀀스로 같은 카탈로그·records를 조립하면 같은
      `currentStats`·`odds`가 나옴을 값으로 단언한다. 배당률이 `calculateOdds` 결과와
      일치함(약체 고배당·강자 저배당의 대소 관계)을 단언한다.
    - **연승 판정**: `recentResults`가 `[1,1,3,...]`이면 연속 1위 2회로 연승으로,
      `[3,1,1,...]`이면 최신이 1위 아님이라 연승이 아님으로 판정됨을 단언한다.
      빈 전적(`racesRun=0`)에서 예외 없이 비연승으로 처리됨을 단언한다.
    - **카드 표시**: 번호·이름이 함께 DOM에 노출되고, 배당률이 소수점 1자리 형식으로,
      최근 5경기 성적이 노출됨을 `@testing-library/react`로 단언한다. 연승 카드에서
      배지가 노출되고 비연승 카드에서는 노출되지 않음을 단언한다.
    - **빈/부족 전적 카드**: `records`에 해당 말 키가 없거나 최근 성적이 5경기 미만인
      말도 예외 없이 렌더됨을 단언한다.
  - `npx tsc --noEmit`가 종료 코드 0으로 통과한다.
- **touch**
  - `src/ui/lobbyEntries.ts`(카탈로그·records·rng → `HorseRaceEntry[]` 조립 + 연승 판정
    순수 모듈), `src/ui/lobbyEntries.test.ts`
  - `src/ui/HorseCard.tsx`(말 카드 한 장 표시 컴포넌트), `src/ui/HorseCard.test.tsx`
  - 필요 시 `src/ui/types.ts`(카드 props·뷰모델 파생 타입)
- **참고**
  - 모듈 경계: 조립 순수 모듈은 `src/domain`과 rng만 의존하고 `src/sim`·`src/store`를
    직접 참조하지 않는다. `records` 데이터는 `RaceRecord` 도메인 타입으로 받으며, 실제
    store에서 이 데이터를 꺼내 조립 함수에 넘기는 배선은 T18·T20에서 다룬다.
  - 회차 변동을 몇 번 굴릴지(회차 진입 시 1회)와 그 결과를 언제 갱신할지는 로비
    오케스트레이션(T18·T20)의 몫이다. T17의 조립 함수는 주입 rng로 1회 변동을 적용한
    스냅샷을 반환하는 순수 함수까지만 고정한다.
  - 연승 배지의 임계값(연속 1위 몇 회 이상)은 되돌리기 쉬운 구현 결정이다. PRD 4.7의
    "연승"에 부합하는 가장 단순한 기준(연속 1위 2회 이상 권장)을 택하고 근거를 IMPL.md에
    남긴다.
  - 시각 완성도(여백·타이포그래피·카드 배치·색 대비 등 실브라우저 시인성)는 T20/M6에서
    다룬다. T17은 시맨틱 마크업·표시 필드·상태 파생 로직까지 고정한다.

### T16. 실황 중계 문구 모듈 + 중계 피드 컴포넌트 (M5) — [x] 완료

M5의 두 번째 태스크. 경주 중 주요 이벤트를 자막형 중계 텍스트로 표시하기 위한
기반을 만든다(PRD 4.6). 이 태스크는 (1) 이벤트 타입별 문구 풀에서 주입 rng로
랜덤 선택하는 **순수 문구 모듈**과, (2) 최근 2~3줄만 유지하는 **중계 피드
컴포넌트**까지만 다룬다. 실제 경주 이벤트(출발·선두 교체·스킬 발동 등)를
시뮬레이션에서 감지해 문구를 emit하는 배선은 T20 전체 게임 루프 오케스트레이션의
몫이며, T16은 그 배선이 소비할 순수 모듈과 표시 컴포넌트를 먼저 세운다.

문구 선택의 무작위성은 주입 가능한 rng로 감싸 단위 테스트가 결정적이게 한다.
T9가 추가한 `src/sim/rng.ts`(mulberry32 시드 PRNG)를 소비하거나, 0~1 난수를
반환하는 함수를 인자로 받는 형태 중 되돌리기 쉬운 쪽을 generator가 선택하고
근거를 IMPL.md에 남긴다. 문구 풀은 반복 플레이 시 단조로움을 피하도록 이벤트
타입별 2개 이상 두며, 선두 교체·스킬 발동처럼 대상이 있는 이벤트는 말 이름 등
치환 파라미터를 문구에 주입할 수 있게 한다.

- **acceptance**
  - `src/ui/`에 이벤트 타입별 문구 풀에서 주입 rng로 한 줄을 선택하는 순수 모듈이
    존재한다. 이벤트 타입은 PRD 4.6의 여섯 종(출발·선두 교체·스킬 발동·최종 직선
    진입·접전·결승선 통과)을 포함한다. 각 이벤트 타입의 문구 풀은 2개 이상이다.
  - `src/ui/`에 최근 2~3줄(상한 상수)만 유지하는 중계 피드 컴포넌트가 존재하고,
    전달된 중계 메시지 목록 중 최신 항목만 상한 개수까지 노출한다. jsdom +
    `@testing-library/react`로 DOM 없이 마운트·검증한다.
  - `npx vitest run`으로 아래 단위 테스트가 통과한다. 최소 검증 항목:
    - **문구 선택 결정론**: 동일 rng 시퀀스(같은 시드)로 같은 이벤트 타입에 대해
      같은 문구가 선택됨을 값으로 단언한다. 서로 다른 rng 값이 서로 다른 문구를
      고를 수 있음(풀이 2개 이상이라 선택지가 실재함)을 최소 1건 단언한다.
    - **치환 파라미터**: 대상이 있는 이벤트(예: 선두 교체·스킬 발동)에서 말
      이름/스킬명 등 파라미터가 결과 문구에 실제로 반영됨을 단언한다.
    - **모든 이벤트 타입 커버**: 여섯 이벤트 타입 각각에 대해 문구 선택이 예외
      없이 문자열을 반환함을 단언한다(문구 풀 누락 방지).
    - **피드 상한 유지**: 상한(2~3)을 초과하는 메시지 목록을 넘겨도 최신
      상한 개수만 DOM에 노출됨을, 그리고 최신 항목이 포함됨을 `@testing-library/react`로
      단언한다. 빈 목록에서 예외 없이 렌더됨도 단언한다.
  - `npx tsc --noEmit`가 종료 코드 0으로 통과한다.
- **touch**
  - `src/ui/commentary.ts`(이벤트 타입·문구 풀·주입 rng 선택 순수 모듈),
    `src/ui/commentary.test.ts`
  - `src/ui/CommentaryFeed.tsx`(최근 2~3줄 유지 피드 컴포넌트),
    `src/ui/CommentaryFeed.test.tsx`
  - 필요 시 `src/ui/types.ts`(중계 이벤트 타입·메시지·컴포넌트 props 타입)
- **참고**
  - 실제 경주 이벤트 감지(선두 교체·최종 직선 진입 등 시뮬레이션 상태로부터의
    이벤트 도출)와 문구 emit 배선은 T20 전체 게임 루프 오케스트레이션의 몫이다.
    T16은 순수 문구 모듈과 표시 컴포넌트까지만 다루며, 시뮬레이션·스토어를 직접
    참조하지 않는다(모듈 경계: `commentary.ts`는 rng·문구 데이터만 의존).
  - 문구 풀 데이터를 어디에 둘지(모듈 상수 vs 별도 데이터 파일)는 되돌리기 쉬운
    구현 결정이다. 가장 단순한 형태를 택하고 근거를 IMPL.md에 남긴다.
  - 시각 완성도(여백·타이포그래피·피드 페이드 등)는 실브라우저 확인이 필요한
    부분은 T20/M6에서 다룬다. T16은 시맨틱 마크업·상한 유지 로직까지 고정한다.

### T15. React↔store 구독 브리지 훅 + 잔고·파산 표시 + 저장 비활성 안내 배너 (M5) — [x] 완료

M5의 첫 태스크. M4까지 렌더·시뮬레이션·저장·스토어가 모두 순수/주입식 모듈로
완성되었으나 React UI는 `App.tsx`의 제목 한 줄뿐이다(`src/App.tsx:1-9`). 이 태스크는
이후 모든 UI 컴포넌트가 의존할 **React↔store 구독 브리지**를 먼저 세우고, 가장 단순한
소비자인 잔고·파산 횟수 표시와 저장 비활성 안내 배너를 붙인다. 실황 중계·말 카드·
베팅·설정·Canvas 실연결은 T16 이후의 몫이며, 이 태스크는 부트스트랩(저장 로드→스토어
생성)과 브리지·표시·배너까지만 다룬다.

브리지 설계 유의점: `GameStore.getState()`는 매 emit마다 새 객체를 반환한다
(`gameStore.ts:37`, `{ ...machineState, ... }`). `useSyncExternalStore`의 `getSnapshot`에
이를 그대로 넘기면 스냅샷 불안정으로 무한 리렌더가 발생하므로, 브리지는 구독 시점의
스냅샷을 캐싱하거나 `subscribe`+`useState` 패턴으로 안정성을 확보한다(되돌리기 쉬운
구현 결정, generator가 선택하고 근거를 IMPL.md에 기록).

- **acceptance**
  - `src/ui/`에 `createGameStore`(`subscribe`/`getState`, `gameStore.ts:17-23`)를 React로
    잇는 구독 브리지 훅이 존재하고, 스토어 상태 변경(`dispatch`/`adjustBalance`)이 구독
    컴포넌트의 리렌더로 반영된다. jsdom + `@testing-library/react`로 DOM 없이 마운트·검증한다.
  - `src/ui/`에 잔고·파산 횟수 표시 컴포넌트가 존재하고, 스토어의 `balance`·
    `bankruptcyCount`를 노출한다(PRD 4.4).
  - `src/ui/`에 저장 비활성 안내 배너 컴포넌트가 존재하고, `PersistenceController.load()`의
    `status`가 `"disabled"`이거나 `isDisabled()`가 true일 때만 안내를 노출한다
    (PRD 4.4·6번, `storage.ts:9-24`).
  - `App.tsx`가 `createPersistence`→`load`→`createGameStore` 부트스트랩을 수행하여
    스토어를 UI에 제공한다. 프로덕션 경로는 `createLocalStorageDriver`(`storage.ts:26`)를,
    테스트는 주입 driver를 쓸 수 있도록 스토어/드라이버 주입 가능하게 구성한다.
  - `npx vitest run`으로 아래 단위 테스트가 통과한다. 최소 검증 항목:
    - **브리지 반영**: 브리지 훅을 쓰는 컴포넌트를 마운트한 뒤 스토어에서 `adjustBalance`
      또는 `dispatch`를 호출하면, 변경된 값이 DOM에 반영됨을 `@testing-library/react`로
      단언한다(구독→리렌더 경로 검증).
    - **스냅샷 안정성**: 스토어 상태가 바뀌지 않은 리렌더에서 무한 루프·중복 구독 없이
      안정적으로 동작함을 확인한다(예: `getState`가 매번 새 객체라도 훅이 안정 스냅샷을
      유지함을 렌더 횟수 또는 예외 부재로 단언).
    - **잔고·파산 표시**: 초기 잔고(예: 10,000)와 파산 횟수(0)가 노출되고, 파산 발생
      (`adjustBalance`로 잔고를 `MIN_BET_AMOUNT` 미만으로 만든 뒤 재충전) 후 파산 횟수
      증가가 DOM에 반영됨을 단언한다.
    - **저장 비활성 배너**: `status="disabled"`(또는 `isDisabled()` true)일 때 배너가
      노출되고, `"ok"`/`"empty"`일 때 노출되지 않음을 각각 단언한다.
  - `npx tsc --noEmit`가 종료 코드 0으로 통과한다.
- **touch**
  - `src/ui/useGameStore.ts`(구독 브리지 훅), `src/ui/useGameStore.test.tsx`
  - `src/ui/BalanceDisplay.tsx`(잔고·파산 표시), `src/ui/BalanceDisplay.test.tsx`
  - `src/ui/StorageBanner.tsx`(저장 비활성 배너), `src/ui/StorageBanner.test.tsx`
  - `src/App.tsx`(부트스트랩·조립에 한함)·`src/App.test.tsx`(스모크 갱신)
  - 필요 시 `src/ui/types.ts`(브리지·컴포넌트 props 타입)
- **참고**
  - 실제 브라우저 마운트·수동 조작은 이 하네스에서 확인할 수 없다. T15는 jsdom +
    `@testing-library/react`로 DOM 출력·구독 반영까지만 검증한다.
  - Canvas 마운트·`renderRace` 실연결·전체 게임 루프 오케스트레이션은 T20의 몫이다.
    T15는 로비 진입 전 잔고·파산·저장 상태를 React로 노출하는 최소 골격까지다.
  - 스냅샷 안정성 확보를 위해 `gameStore.ts`에 캐싱을 도입할지 여부는 되돌리기 쉬운
    구현 결정이다. 스토어 계약(T5로 고정된 테스트)을 깨지 않는 선에서 generator가
    선택하고 근거를 IMPL.md에 남긴다.

### T14. 폭죽 파티클 + 우승마 스포트라이트 연출 (M4 마지막) — [x] 완료

M4의 여섯 번째이자 마지막 태스크. 결승선 통과 순간의 폭죽 파티클 효과와 우승마
스포트라이트를 그린다(PRD 4.5). T9~T13과 동일한 하네스 제약(실제 canvas 마운트·
React 연결·픽셀 확인 수단 없음)에서, 파티클 물리는 주입 rng로 결정적인 순수 함수로
두어 vitest로 검증하고, 실제 그리기는 T11·T12·T13과 동일하게 주입 `RenderContext`
(mock ctx) 위 순수 함수로 스모크 검증한다. 스포트라이트는 우승마의 layout 좌표를
소비해 강조하며, 순위·좌표 계산을 재구현하지 않는다. 실제 canvas 마운트·
`renderRace`/`loop.onFrame` 실연결·실화면 시인성은 M5의 몫이다.

- **acceptance**
  - `src/render/`에 폭죽 파티클의 생성·갱신을 담당하는 순수 함수가 존재한다.
    - 생성은 주입 rng(예: T9 `src/sim/rng.ts`의 결정적 PRNG)로 파티클 집합을
      만들며, 같은 시드·같은 인자면 같은 파티클 집합을 반환함(결정론)을 값으로
      단언한다. 각 파티클은 최소 위치(x·y)·속도(vx·vy)·수명(remaining/max)을 갖는다.
    - 갱신은 dt만큼 위치를 전진시키고(속도·중력 등 결정적 규칙) 수명을 감소시키며,
      수명이 소진된 파티클을 제거한다. dt 누적에 따른 위치 전진과 수명 소진 후
      제거를 값으로 단언한다. rng 없이 dt만으로 결정되는 순수 갱신이어야 한다.
  - `src/render/`에 폭죽 파티클과 우승마 스포트라이트를 그리는 순수 함수가 존재하고,
    T11·T12·T13과 동일하게 주입 `RenderContext`(mock ctx)로 DOM 없이 테스트할 수 있다.
    - 스포트라이트는 우승마(완주 시 1위)의 좌표를 `computeRaceLayout`의
      `runners`/`leaderboard`에서만 가져와 그 위치를 강조하며, 좌표·순위를
      재구현하지 않는다. 우승마 좌표와 스포트라이트 그리기 좌표가 일치함을 단언한다.
    - 미완주 상태(우승마 미확정)에서는 스포트라이트·폭죽이 그려지지 않음을 단언한다.
    - 새로 추가하는 그리기 함수는 `save()`/`restore()`로 ctx 상태를 격리한다
      (T13 REVIEW 비차단 메모 흡수: 신규 함수라 저비용이며, M5 실연결 시 다른
      그리기 명령과 한 프레임에 함께 호출돼도 상태가 전이되지 않도록 한다).
  - `npx vitest run`으로 아래 단위 테스트가 통과한다. 최소 검증 항목:
    - **파티클 결정론**: 같은 시드 rng로 생성한 두 파티클 집합이 동일함(개수·초기
      위치·속도)을 값으로 단언한다.
    - **파티클 갱신**: 한 스텝 dt 갱신 후 위치가 속도에 따라 전진하고 수명이
      감소함을, 여러 스텝 후 수명 소진 파티클이 집합에서 제거됨을 단언한다.
    - **스포트라이트 좌표**: 완주 상태에서 스포트라이트가 우승마 layout 좌표를
      중심으로 그려짐(`arc`/`fillRect` 등의 좌표 인자가 우승마 `runners` 좌표와
      일치)을 단언한다.
    - **미완주 미노출**: 미완주 상태에서 폭죽·스포트라이트 그리기가 ctx 명령을
      내지 않음(또는 조기 반환)을 단언한다.
  - `npx tsc --noEmit`가 종료 코드 0으로 통과한다.
- **touch**
  - `src/render/particles.ts`(폭죽 파티클 생성·갱신 순수 함수 + 파티클 그리기),
    `src/render/particles.test.ts`
  - `src/render/finishFx.ts`(우승마 스포트라이트 그리기 순수 함수 추가에 한함),
    `src/render/finishFx.test.ts`(스포트라이트 단언 추가)
  - 필요 시 `src/render/types.ts`(파티클 타입·연출 상수)
- **참고**
  - 실제 canvas element 마운트·React 컴포넌트·`renderRace`↔`loop.onFrame` 실연결과
    실화면 시인성(폭죽 밀도·스포트라이트 대비)은 M5에서 확인한다. 이 하네스는
    Canvas 픽셀을 화면으로 확인할 수단이 없으므로, T14는 파티클 물리의 결정론과
    그리기 좌표의 정확성까지만 vitest로 고정한다.
  - `drawFinishBanner`의 `save()`/`restore()` 부재(T13 REVIEW 비차단 메모)는
    기존 프로덕션 코드 변경을 최소화하기 위해 T14에서 손대지 않고, 여러 그리기가
    한 프레임에 함께 호출되는 실연결 시점(M5)에서 배너·스포트라이트·폭죽의 호출
    순서·상태 격리와 함께 일괄 확정한다. T14는 신규 그리기 함수의 상태 격리만
    선제 적용한다.
  - T14 완료 시 M4(Canvas 렌더링 & 연출)의 모든 태스크가 끝난다. 다음 사이클은
    M5(React UI 레이어 & 실황 중계)로 진입한다.

## 완료

### T13. 피니시 슬로모션 timescale + 렌더 루프 통합 + 포토 피니시 연출 (M4) — [x] 완료

M4의 다섯 번째 태스크. T10이 만든 주입식 렌더 루프(`createRenderLoop`,
`src/render/loop.ts`)와 T8이 만든 피니시 판정(`isSlowMotionTriggered`·
`isPhotoFinish`, `src/sim/finish.ts`)을 소비해, 선두가 결승선에 근접하면 전체
게임 속도를 슬로모션(0.3배속)으로 감속하고, 완주 시 포토 피니시(접전) 또는 우승
배너를 그린다(PRD 4.5). 감속은 렌더 루프가 시뮬레이션에 넘기는 dt에 배율을 곱하는
방식으로 구현하며, 판정 로직을 재구현하지 않고 sim `finish.ts`를 그대로 소비한다.
폭죽 파티클·우승마 스포트라이트는 T14, 실제 canvas 마운트·React 연결은 M5의 몫이며,
이 태스크는 배너 그리기는 T11·T12와 동일하게 주입 mock ctx 위 순수 함수로, 슬로모션
timescale은 순수 함수 + 주입식 루프 통합으로 다룬다.

- **acceptance**
  - `src/render/`에 슬로모션 timescale을 산출하는 순수 함수가 존재한다. 선두
    진행률이 슬로모션 임계값 이상(`isSlowMotionTriggered`가 true)이면 배율
    `SLOW_MOTION_TIME_SCALE`(예: 0.3), 아니면 1.0을 반환하며, 판정은 sim
    `finish.ts`를 소비하고 진행률 계산을 재구현하지 않는다. 완주 후 슬로모션을
    유지/해제하는 정책을 확정하고 그 경계 동작을 값으로 고정한다(T8 REVIEW 메모 1).
  - 이 timescale이 T10 `createRenderLoop`에 통합되어, 슬로모션 상태에서 시뮬레이션에
    전달되는 dt가 배율만큼 축소된다. 주입식 raf·시간 소스로 이를 통합 테스트로
    고정한다(loop이 `advanceWithAccumulator`에 넘기는 dt 또는 전진량이 슬로모션
    구간에서 비슬로모션 구간 대비 배율만큼 작음을 결정적으로 단언).
  - `src/render/`에 포토 피니시/우승 결과 배너를 그리는 순수 함수가 존재하고,
    T11·T12와 동일하게 주입 `RenderContext`(mock ctx)로 DOM 없이 테스트할 수 있다.
    완주 상태에서 `isPhotoFinish`가 true면 포토 피니시(접전) 문구를, false면 우승마
    표시(번호·이름 병기)를 `fillText`로 노출한다. 판정은 sim `finish.ts`를 소비하고
    좌표·순위는 `computeRaceLayout`/`RunnerMeta`에서만 가져온다(재구현 금지).
  - `npx vitest run`으로 아래 단위/통합 테스트가 통과한다. 최소 검증 항목:
    - **슬로모션 timescale 판정**: 선두 진행률이 임계값 미만이면 배율 1.0, 이상이면
      `SLOW_MOTION_TIME_SCALE`임을 값으로 단언한다. 임계값 경계값 동작을 고정한다.
    - **완주 후 유지/해제 정책**: `finished=true` 상태에서 확정한 정책(유지 또는
      해제)대로 배율이 결정됨을 단언한다.
    - **루프 통합**: 동일한 raf 타임스탬프 시퀀스에 대해, 슬로모션이 트리거된
      경우 시뮬레이션 전진량(위치 증가 또는 소비 dt)이 비트리거 경우 대비 배율만큼
      작음을 결정적으로 단언한다.
    - **포토 피니시 배너**: 완주 + 접전(`isPhotoFinish` true)이면 포토 피니시
      문구가 `fillText`로 노출되고, 접전이 아니면 우승마 번호·이름이 노출됨을
      각각 단언한다. 미완주 상태에서는 결과 배너가 그려지지 않음을 단언한다.
    - **effects.ts 방어 분기(T12 REVIEW 테스트 충실도 메모 흡수)**: `drawSkillBanner`의
      `if (!runner.skillId) return`(`effects.ts:103`), 미지 skillId 폴백
      `?? runner.skillId`(`effects.ts:106`), `drawSkillEffects`의 layout 좌표 부재
      `if (!position) return`(`effects.ts:82`) 세 분기에 단언을 1건씩 추가한다.
  - `npx tsc --noEmit`가 종료 코드 0으로 통과한다.
- **touch**
  - `src/render/finishFx.ts`(슬로모션 timescale 순수 함수 + 포토 피니시/우승 배너
    순수 그리기), `src/render/finishFx.test.ts`
  - `src/render/loop.ts`(슬로모션 timescale을 dt에 적용하는 통합에 한함),
    `src/render/loop.test.ts`(루프 통합 단언 추가)
  - 필요 시 `src/render/types.ts`(`SLOW_MOTION_TIME_SCALE` 등 상수·배너 인자 타입)
  - `src/render/effects.test.ts`(방어 분기 단언 3건 추가에 한함, `effects.ts` 로직 무변경)
- **참고**
  - 폭죽 파티클·우승마 스포트라이트 연출은 T14의 몫이다. 이 태스크는 슬로모션
    감속·포토 피니시/우승 배너까지만 다룬다.
  - 실제 canvas element 마운트·React 컴포넌트·`renderRace`↔`loop.onFrame` 실연결과
    실화면 시인성(슬로모션 체감·배너 가독성)은 M5에서 확인한다(이 하네스는 Canvas
    픽셀을 화면으로 확인할 수단이 없다). T9 REVIEW 메모 1(역전 빈도 밴드 좁히기)도
    실제 연출을 눈으로 확인하는 M5 시점으로 유지한다.
  - 완주 직후 슬로모션 유지/해제는 되돌리기 쉬운 연출 정책이므로 planner가 자체
    결정하지 않고, 트리거 조건(`isSlowMotionTriggered`)의 자연스러운 귀결을 따르되
    generator가 경계 테스트로 고정한다. 정책 근거는 IMPL.md에 기록한다.

### T12. 스킬 발동 이펙트 + 스킬명 배너 (M4) — [x] 완료

M4의 네 번째 태스크. T11이 만든 실제 Canvas 2D 렌더러(`src/render/renderer.ts`)
위에, 스킬 발동을 시각적으로 드러내는 이펙트와 스킬명 배너를 추가한다.
시뮬레이션 엔진이 이미 노출하는 발동 이력(`RunnerState.skillActivated`·
`skillActivatedAt`, `src/sim/types.ts:23-25`)과 현재 `elapsedTime`을 소비해,
발동 직후 일정 시간 동안 해당 말에 오라/잔상/스피드라인/플래시 계열의 시각
효과를 그리고, 스킬명(도메인 `SKILL_CATALOG`의 한글 표시명: 라스트 스퍼트·
슬립스트림·스타트 대시·흔들기·무아지경, `src/domain/horses.ts:7-11`)을 배너로
표시한다(PRD 4.2). 효과음은 M6, 실제 canvas 마운트·React 연결은 M5의 몫이며,
이 태스크는 T11과 동일하게 주입 mock ctx 위에서 순수 그리기 함수만 다룬다.

- **acceptance**
  - `src/render/`에 스킬 이펙트·스킬명 배너를 그리는 순수 함수가 존재하고,
    T11과 동일하게 `RenderContext`(주입 mock ctx)로 DOM 없이 테스트할 수 있다.
    발동 여부·경과 시간 판정은 `skillActivated`·`skillActivatedAt`과 현재
    `elapsedTime`을 인자로 소비하며(발동 이력 계산을 재구현하지 않음), 러너 화면
    좌표는 T10 `computeRaceLayout` 결과(`layout.runners`)에서만 가져온다(좌표
    재구현 금지). 스킬 id→표시명 매핑은 도메인 카탈로그를 소비하고, 렌더러가
    표시명 문자열을 하드코딩하지 않는다(모듈 경계: `renderer`는 sim·store·DOM을
    직접 참조하지 않는다).
  - `npx vitest run`으로 아래 단위 테스트가 통과한다. 최소 검증 항목:
    - **발동 창 판정**: 어떤 말이 `skillActivated=true`이고 현재 `elapsedTime`이
      `skillActivatedAt`으로부터 이펙트 지속 창(상수) 이내이면 그 말 좌표에
      이펙트 그리기 명령이 호출되고, 지속 창을 벗어나거나 미발동
      (`skillActivated` 아님/`skillActivatedAt=null`)이면 호출되지 않는다.
      경계값(창 시작·끝) 동작을 값으로 고정한다.
    - **이펙트 좌표 일치**: 이펙트가 그려지는 좌표가 `layout.runners`의 해당
      말 (x, y)와 일치함을 `arc`/`moveTo`/`lineTo` 등 인자로 단언한다(별도
      좌표를 재계산하지 않음).
    - **스킬명 배너**: 발동 창 안의 말에 대해 `fillText` 인자로 도메인
      표시명(예: `라스트 스퍼트`)이 노출됨을 단언한다. 서로 다른 스킬 id가
      서로 다른 표시명으로 렌더됨을 최소 2종으로 확인한다.
    - **폴백 분기(T11 REVIEW 메모 1 흡수)**: `runnersMeta`와 `layout.runners`가
      불일치(누락 id)일 때 `drawRunners`의 `?? DEFAULT_RUNNER_COLOR` 폴백
      (`renderer.ts:76`)과 `drawLeaderboard`의 meta 부재 시 축약 라벨 분기
      (`renderer.ts:117`)가 각각 예외 없이 동작함을 단언 1건씩 추가한다.
  - `npx tsc --noEmit`가 종료 코드 0으로 통과한다.
- **touch**
  - `src/render/effects.ts`(스킬 이펙트·스킬명 배너 순수 그리기), `src/render/effects.test.ts`
  - 필요 시 `src/render/renderer.ts`(진입점 `renderRace`에서 이펙트 레이어
    호출 연결에 한함)·`src/render/renderer.test.ts`(폴백 분기 단언 추가)
  - 필요 시 `src/render/types.ts`(이펙트 인자 타입·지속 창 상수)
- **참고**
  - 실제 canvas element 마운트·React 컴포넌트·`loop.onFrame` 실연결은 이
    태스크에서 만들지 않는다(M5). T12는 순수 ctx 그리기 함수와 mock ctx 스모크
    검증까지다.
  - **T7 REVIEW 메모 3 재검토**: 흔들기(shake-off)의 "주변 말" 범위를 거리
    기반으로 제한할지 이 단계에서 재검토한다. 현재 `skills.ts`의 shake-off는
    `othersMultiplier`로 전체 말에 영향을 준다. 이펙트를 시각화하며 거리 제한이
    필요하다고 판단되면 sim 로직 변경 여부·범위를 IMPL.md에 근거와 함께 기록하고,
    변경이 크면 후속 태스크로 분리한다(이번 태스크의 범위를 넘기지 않는다).
  - 피니시 슬로모션·폭죽·우승마 스포트라이트·포토 피니시 연출은 T13의 몫이다.

### T11. Canvas 2D 실제 렌더러 (트랙·말 도형+다리 모션·순위표·번호/이름 병기) (M4) — [x] 완료

M4의 세 번째 태스크. T10이 고정한 순수 레이아웃 좌표(`computeRaceLayout`)와
루프 오케스트레이터를 소비해, 이번엔 실제 Canvas 2D 그리기를 구현한다. 고정
화면 트랙(좌 출발 게이트·우 결승선), 도형+다리 모션의 말(합의: 미니멀 도형),
실시간 순위표를 그리고, 색상만이 아니라 번호·이름을 병기한다(PRD 5번·13번).
이 하네스는 Canvas 픽셀을 화면으로 확인할 수단이 없으므로, ctx를 주입 가능한
인터페이스로 감싸 mock ctx로 호출 순서·좌표·텍스트 인자를 스모크 검증한다.
스킬 이펙트·배너는 T12, 피니시 슬로모션·폭죽 연출은 T13의 몫이다.

- **acceptance**
  - `src/render/`에 실제 Canvas 2D 렌더러가 존재하고, `CanvasRenderingContext2D`를
    주입 가능한 최소 인터페이스로 감싸(실제 브라우저 ctx를 얇게 위임) DOM 없이도
    mock ctx로 테스트할 수 있다. 렌더 함수는 T10 `computeRaceLayout` 좌표를 소비하며
    좌표 계산을 재구현하지 않는다.
  - `npx vitest run`으로 아래 단위 테스트가 통과한다. 최소 검증 항목:
    - **트랙 렌더**: mock ctx로 렌더를 호출하면 트랙 배경·출발 게이트·결승선
      그리기 명령이 호출되고, 출발선 x가 결승선 x보다 작다(좌 출발·우 결승).
    - **말 렌더(다리 모션 포함)**: 각 러너가 T10 layout의 (x, y) 좌표에 그려지고,
      다리 모션이 프레임(진행률 또는 시간)에 따라 달라진다(서로 다른 프레임에서
      다리 관련 그리기 인자가 달라짐을 값으로 단언; 정지 화면이 아님을 고정).
    - **순위표 렌더 + 번호·이름 병기**: leaderboard 순서대로 항목이 그려지고,
      각 말에 번호와 이름 텍스트(`fillText` 인자)가 함께 노출된다. 색상만으로
      구분하지 않음(번호·이름 텍스트 존재)을 단언한다(PRD 13번).
    - **레인 밴드 폭 ≥ 도형 높이(T10 REVIEW 메모 1)**: 말 도형 높이 상수를
      확정하고, 러너 4~8마리에서 각 레인 밴드 폭이 도형 높이 이상이라 인접
      말 도형이 세로로 겹치지 않음을 값으로 고정한다.
  - `npx tsc --noEmit`가 종료 코드 0으로 통과한다.
- **touch**
  - `src/render/renderer.ts`(트랙·말·순위표 Canvas 2D 그리기), `src/render/renderer.test.ts`
  - 필요 시 `src/render/types.ts`(ctx 주입 인터페이스, 말 도형 치수 상수)
  - 필요 시 `src/render/layout.test.ts`(레인 밴드 폭 ≥ 도형 높이 단언 추가에 한함)
- **참고**
  - 실제 canvas element 마운트·React 컴포넌트·`loop.onFrame` 실연결은 이
    태스크에서 만들지 않는다(M5). T11은 순수 ctx 그리기 함수와 mock ctx 스모크
    검증까지다.
  - hidden(일시정지) 프레임의 재그리기 건너뛰기 렌더 정책(T10 REVIEW 메모 2)은
    렌더 함수를 `loop.onFrame`에 연결하는 통합 시점(T13/M5)에서 확정한다. T11
    렌더 함수는 순수 ctx 그리기만 담당한다.
  - `onFrame`이 넘기는 `RaceState`는 매 프레임 교체되는 참조다(T10 REVIEW 메모 3).
    렌더 함수는 상태를 보관·비교하지 않고 해당 프레임 값만 소비한다.

### T10. 렌더 레이아웃 순수 함수 + raf 렌더 루프 + 탭 자동 일시정지 연결 (M4, 화면 없는 로직) — [x] 완료

M4의 두 번째 태스크. 실제 Canvas 그리기(T11)에 앞서, 렌더러가 소비할 좌표
계산과 루프·상태 연결을 화면 없는 순수/주입식 로직으로 먼저 고정한다. 이
하네스는 vitest 자동 검증 중심이라 Canvas 픽셀을 화면으로 확인할 수단이 없으므로,
아키텍처 원칙(로직과 렌더 분리)에 맞춰 (1) 시뮬레이션 상태를 화면 좌표로 매핑하는
순수 레이아웃 함수, (2) 주입 가능한 raf·시간·이벤트 소스 위에서 도는 렌더 루프
오케스트레이터, (3) 탭 비활성화 자동 일시정지 연결을 이 태스크에서 만든다. 실제
ctx 그리기는 T11에서 이 좌표를 소비한다.

- **acceptance**
  - `src/render/`에 렌더 레이아웃 순수 함수와 raf 렌더 루프 오케스트레이터가
    존재하고, 실제 ctx 그리기와 분리된다(레이아웃은 DOM·ctx 미참조, 루프는
    `requestAnimationFrame`·시간·`document`를 주입 가능한 인터페이스로 감싼다).
  - `npx vitest run`으로 아래 단위/통합 테스트가 통과한다. 최소 검증 항목:
    - **레이아웃 매핑**: 시뮬레이션 상태(각 말의 진행률/위치)와 캔버스 치수를
      넣으면 각 말의 화면 x가 출발선~결승선 사이로 단조 매핑되고(진행률 0=출발선
      x, 완주=결승선 x, 경계값 포함), 러너 수에 따라 레인 y가 겹치지 않게 배분되며,
      순위표 항목이 현재 순위 순서로 산출된다.
    - **루프 전진**: 주입한 가짜 raf·시간 소스로 여러 프레임을 돌리면 시뮬레이션이
      T9 accumulator 경로(`advanceWithAccumulator`)로 전진하고, 매 프레임 그리기
      콜백이 호출된다. 동일 프레임 타임스탬프 시퀀스에서 결과가 결정적이다.
    - **탭 자동 일시정지**: 주입한 visibility 이벤트 소스가 hidden=true를 통지하면
      상태 머신이 `PAUSE`로 전이하고 그 동안 시뮬레이션이 전진하지 않으며, hidden=
      false 통지 시 `RESUME`으로 전이하고 재개된다. 복귀 직후 큰 dt 점프가 한 번에
      소비되지 않음(누적 시간 왜곡 방지)을 검증한다.
    - **maxTime 미완주 분기(T9 REVIEW 메모 2)**: 극단 스탯(예: 매우 낮은 speed)
      입력으로 `runRaceToCompletion`을 구동하면 `finished=false`이고 `finishTime`이
      `maxTime`에 도달해 안전 종료함을 고정한다(무한 루프·타임아웃 회귀 조기 차단).
  - `npx tsc --noEmit`가 종료 코드 0으로 통과한다.
- **touch**
  - `src/render/layout.ts`(시뮬레이션 상태→화면 좌표 순수 함수), `src/render/layout.test.ts`
  - `src/render/loop.ts`(주입식 raf·시간·visibility 위의 렌더 루프 오케스트레이터,
    T9 구동기·M2 상태 머신 연결), `src/render/loop.test.ts`
  - `src/sim/driver.test.ts`(maxTime 미완주 분기 테스트 추가에 한함)
  - 필요 시 `src/render/types.ts`(주입 인터페이스·레이아웃 결과 타입)
- **참고**
  - 실제 Canvas ctx 그리기(트랙·말 도형·다리 모션·순위표 픽셀)·번호/이름 병기·
    React 컴포넌트 마운트는 이 태스크에서 만들지 않는다. T11이 T10의 레이아웃
    좌표와 루프를 소비한다.
  - 프레임레이트 독립성 전제(T9 REVIEW 메모 3)를 유지한다. 루프는 실제 dt를
    accumulator에 넘겨 fixedStep 단위로만 소비하며, 스텝 적분 자체를 재구현하지 않는다.
  - DOM·raf·`document.hidden`은 주입 가능한 인터페이스로 감싸 jsdom 없이도
    결정적으로 테스트할 수 있게 한다(부작용은 얇은 어댑터로 격리).

### T9. 시뮬레이션 전체 구동기 & 연출 상수 실측·조정 (M4 진입, 순수 로직) — [x] 완료

M4의 첫 태스크. 실제 Canvas 그리기(T10~T12)를 쌓기 전에, 렌더 루프가 소비할
시뮬레이션을 전체 완주 구간에서 PRD에 맞게 검증·조정한다. 화면 없는 순수
로직만 다루며, raf 기반 실시간 루프·탭 이벤트 연결·Canvas 렌더링은 T10 이후다.

지금까지 엔진(`src/sim/engine.ts`)의 `step`은 단일 dt로만 검증됐고(프레임레이트
독립성 테스트가 진행률 ~0.056 초반 구간에만 적용, T6 REVIEW 메모 2), `SPEED_SCALE`·
발동 확률 계수는 전체 완주 기준으로 실측된 적이 없다(T6 메모 3, T7 메모 2).
이 태스크는 (1) 원시 dt를 고정 서브스텝으로 분할하는 accumulator와 (2) 경주를
완주까지 진행하는 구동 순수 함수를 추가하고, 이를 이용해 전체 구간에서
프레임레이트 독립성·완주 시간·역전 우승 빈도를 테스트로 고정하며 상수를 조정한다.

- **acceptance**
  - `src/sim/`에 고정 스텝 accumulator와 전체 경주 구동 순수 함수가 존재하고,
    렌더·React에 의존하지 않는다(`requestAnimationFrame`·DOM 미참조).
  - `npx vitest run`으로 아래 단위/통합 테스트가 통과한다. 최소 검증 항목:
    - **프레임레이트 독립성(전체 완주 구간)**: 동일 초기 상태·동일 rng에서,
      큰 dt로 완주까지 진행한 결과와 작은 dt(서브스텝 분할)로 같은 총 경과
      시간까지 진행한 결과의 최종 순위가 일치하고 각 말의 위치·완주 시각 차가
      허용 오차 내다. 스킬 발동이 일어나는 후반 구간을 포함한다(초반만 아님).
    - **완주 시간 범위**: 기본 카탈로그 스탯(회차 변동 미적용 또는 시드 고정)으로
      경주를 완주까지 구동하면 완주 시간이 PRD 4.5의 15~30초 범위에 든다.
      (범위를 벗어나면 `SPEED_SCALE` 등 상수를 조정해 맞춘다.)
    - **역전 우승 빈도**: 결정적 시드 rng로 다수 회차(예: 100회차 이상)를
      구동했을 때, 출발 초반 하위권(예: 초기 순위 하위 절반) 말이 우승하는
      회차 비율이 PRD 9번의 대략 5~10회차당 1회(약 10~20%) 근방 범위에 든다.
      (벗어나면 발동 확률 계수를 조정한다. 정확히 특정 값이 아니라 목표 범위에
      드는지를 검증한다.)
    - **zone·slipstream 엔진 위치 반영(통합)**: 실제 rng로 완주 구동 시 zone·
      slipstream이 발동해 해당 말의 위치가 미발동 대비 실제로 증가함을 통합
      테스트로 확인한다(T7 REVIEW 메모 1 해소).
    - **러너 수 하한 유지(통합)**: 실제 카탈로그(4~8마리)를 구동기에 주입하는
      경로에서 러너 수가 항상 2 이상이라 `isPhotoFinish`·선두 진행률 계산이
      안전함을 확인한다(T8 REVIEW 메모 2 해소).
  - `npx tsc --noEmit`가 종료 코드 0으로 통과한다.
- **touch**
  - `src/sim/driver.ts`(고정 스텝 accumulator·전체 경주 구동), `src/sim/driver.test.ts`
  - `src/sim/engine.ts`·`src/sim/skills.ts`(상수 실측 조정에 한함: `SPEED_SCALE`,
    발동 확률 계수 등. 로직 구조 변경은 최소화)
  - 필요 시 `src/sim/finish.ts`의 임계값 상수 재조정(실측 결과에 한함)
  - 테스트용 결정적 rng가 필요하면 `src/sim/rng.ts`(시드 PRNG) 추가 허용
- **참고**
  - 상수 조정은 "정확한 특정 값"이 아니라 PRD가 정한 목표 범위(완주 15~30초,
    역전 5~10회차당 1회)에 드는지를 기준으로 한다. 테스트도 단일 값이 아닌
    범위 단언으로 작성해 이후 미세 조정에 취약하지 않게 한다.
  - 구동 순수 함수는 T10의 raf 렌더 루프가 매 프레임의 실제 경과 시간을 넣어
    호출할 형태를 상정한다(실시간·DOM 결합은 T10). 이 태스크에서는 시간을
    인자로 받는 순수 형태만 만든다.

### T8. 피니시 근접 판정(슬로모션 트리거) + 포토 피니시(접전) 판정 (M3) — [x] 완료

T7 이후 진행. 경주 연출을 위한 순수 판정 함수를 `src/sim/`에 추가했다.
선두 말이 결승선에 근접하면 슬로모션 트리거를 노출하고(PRD 4.5), 완주 시
1~2위가 근소 차이면 포토 피니시(접전) 판정을 노출한다. 판정은 렌더·React와
분리된 순수 함수이며, 실제 슬로모션 감속·폭죽 연출은 M4의 몫이다.

- **acceptance**
  - `src/sim/`에 피니시 근접 판정과 포토 피니시 판정 순수 함수가 존재한다.
  - `npx vitest run`으로 아래 단위 테스트가 통과한다. 최소 검증 항목:
    - **피니시 근접**: 선두 말 진행률이 임계값(예: 0.9) 이상이면 슬로모션
      트리거 플래그가 true, 미만이면 false. 임계값 경계값 동작이 정의된다.
    - **포토 피니시**: 완주 상태에서 1위와 2위의 위치 차가 임계값 이내면
      접전 판정 true, 초과면 false. 임계값 경계값에서의 동작을 검증한다.
    - 미완주 상태에서는 포토 피니시 판정이 false다.
  - `npx tsc --noEmit`가 종료 코드 0으로 통과한다.
- **touch**
  - `src/sim/finish.ts`(피니시 근접·포토 피니시 판정), `src/sim/finish.test.ts`
  - 필요 시 `src/sim/types.ts` 확장

### T7. 스킬 시스템 5종 + 발동 확률(luck·하위권 보정) + 경주당 1회 발동 (M3) — [x] 완료

M3 후반. T6이 만든 순수 시뮬레이션 엔진(`src/sim/`)에 스킬 시스템을 통합한다.
각 말은 고유 스킬 1개를 보유하며(도메인 `HorseProfile.skill`은 이미 5종 정의),
경주당 최대 1회 자동(확률 기반) 발동한다(PRD 4.2). 발동 확률은 `luck`과 현재
순위에 영향받고, **하위권일수록 보정을 받아 역전 가능성을 확보**한다. 발동은
순간 속도(또는 상태)에 실제 효과를 준다. 발동 판정에 쓰는 무작위성은 주입
가능한 RNG로 감싸 단위 테스트가 결정적이게 한다. 피니시 근접·포토 피니시
판정은 T8로 분리한다. 시각 이펙트·배너는 렌더 단계(M4)의 몫이며 이번 태스크는
순수 로직만 다룬다.

- **acceptance**
  - `src/sim/`에 스킬 효과 정의와 발동 판정, 시뮬레이션 통합이 존재한다.
    스킬 5종 이상이 각각 순간 속도(또는 러너 상태)에 서로 구분되는 효과를 준다.
    발동 판정은 순수 함수로, 엔진 상태에 발동 이력(어떤 말이 어떤 스킬을 언제
    발동했는지)을 노출해 M4 이펙트/배너가 소비할 수 있게 한다.
  - `npx vitest run`으로 아래 단위 테스트가 통과한다. 최소 검증 항목:
    - **하위권 보정**: 동일 `luck`·동일 조건에서 하위 순위 말의 발동 확률이
      상위 순위 말보다 높다(하위권 보정이 실제로 확률을 높임을 검증).
    - **luck 영향**: `luck`이 높을수록 발동 확률이 높다(같은 순위 기준).
    - **경주당 1회 제한**: 한 번 발동한 말은 이후 스텝에서 발동 조건이 다시
      충족돼도 재발동하지 않는다.
    - **스킬 효과 반영**: 발동한 말의 순간 속도(또는 위치 증가분)가 미발동
      대비 스킬 정의대로 변화한다(대표 스킬 유형별 검증).
    - **burst 효과 직접 검증**(T6 REVIEW 메모 1 해소): `burst`가 큰 말의
      순간 속도 변동 진폭이 `burst=0` 대비 크다(사인파 진폭이 순간 속도에
      실제 반영됨을 직접 검증).
    - **결정론**: 동일 RNG 시퀀스에서 발동/미발동과 효과가 완전히 재현된다.
  - `npx tsc --noEmit`가 종료 코드 0으로 통과한다.
- **touch**
  - `src/sim/types.ts`(러너 상태에 스킬 발동 상태·이력 필드 확장)
  - `src/sim/skills.ts`(스킬 효과·발동 확률·발동 판정), `src/sim/skills.test.ts`
  - `src/sim/engine.ts`(step에 스킬 발동 판정·효과 통합)
  - 필요 시 `src/domain/types.ts`의 `SkillDefinition`에 효과 식별자 확장
- **참고**
  - 발동 확률·하위권 보정 계수는 PRD 9번(역전 우승 대략 5~10회차당 1회)에
    맞추되, 실측·조정은 M4/M5 통합 단계에서 수행한다. 이번 태스크는 보정이
    방향성(하위권일수록↑, luck 높을수록↑)을 실제로 갖는지만 테스트로 고정한다.
  - 스킬 5종은 도메인 정의(라스트 스퍼트·슬립스트림·스타트 대시·흔들기·
    무아지경)에 대응한다. "흔들기"처럼 주변 말에 영향을 주는 스킬은 발동자
    외 러너 상태도 변경하므로, step이 러너 배열 전체를 함께 처리하는 형태를
    유지한다.

### T6. 경주 시뮬레이션 코어: delta-time 적분 + 실시간 순위 + 완주 판정 (M3) — [x] 완료

M3에 진입해 렌더링·React와 분리된 순수 시뮬레이션 엔진을 `src/sim/`에
구현했다. 기본 주행 물리·순위·완주 판정에 집중했다. 진행은 시간 기반
(delta-time) 적분으로만 이뤄져 프레임레이트와 무관하게 결정된다(PRD 5번).
RNG는 초기화 시 1회만 소비(burst 위상 결정)하여 이후 step은 순수하게 진행한다.
(평가: PASS 11/12)

- **acceptance**
  - `src/sim/`에 시뮬레이션 상태 초기화와 스텝 진행 순수 함수 모듈이 존재한다.
  - `npm run test`로 프레임레이트 독립성·결정론·순위 산출(동률)·완주 판정·
    후반 감속 단위 테스트가 통과한다.
  - `npx tsc --noEmit`가 종료 코드 0으로 통과한다.
- **touch**
  - `src/sim/types.ts`, `src/sim/engine.ts`, `src/sim/engine.test.ts`
- **비차단 메모(이관)**: burst 효과 직접 검증 부재 → T7 acceptance로 흡수.
  프레임레이트 독립성 전체 구간 재확인·연출 상수 실측 → M4/M5 통합 단계.

### T5. M2 테스트 완결: 저장 계층 방어 케이스 + 스토어 계약 (M2) — [x] 완료

M2의 두 테스트 부채를 한 세션에서 함께 해소해 M2를 완결한다. 모두 비차단
(코드 로직 변경 없이 테스트만 추가)이며, 프로덕션 코드는 수정하지 않는다.
(1) T3 REVIEW 후속 메모 1·2(저장 계층 방어 경로), (2) T4 REVIEW 메모 1·2·3
(gameStore 계약). M5에서 잔고·전적 UI가 스토어를 구독하기 전에 스토어 계약을
테스트로 고정하는 의미가 있다.

- **acceptance**
  - `npm run test`로 아래 저장 계층 케이스가 추가되어 통과한다.
    - save 단독 실패: `load()` 선행 없이 `save()`만 호출하고 setItem이 예외를
      던지는(쿼터 초과 등) 스토리지 주입 시, `safeSet`이 `disabled=true`로
      전환하고 이후 메모리로 우회함을 검증(`storage.ts:61-64`).
    - 스키마 분기: `records`의 개별 항목 손상(`isRaceRecord` false)과
      `settings.horseCount` 범위 위반이 각각 `corrupted`로 리셋됨을 검증
      (`schema.ts:39-58`).
  - `npm run test`로 아래 gameStore 계약 케이스가 추가되어 통과한다.
    - 파산 경계값: `adjustBalance`로 잔고가 정확히 `MIN_BET_AMOUNT(100)`가 되는
      경우 미파산(잔고 100 유지, `bankruptcyCount` 불변), 99가 되는 경우 파산
      (잔고 `DEFAULT_BALANCE(10000)`, `bankruptcyCount` +1)임을 검증해
      `<` 경계(`gameStore.ts:46`)를 고정한다.
    - `adjustBalance` 알림: `adjustBalance` 호출 시 구독자에게 변경된 잔고가
      emit됨을 검증한다(`gameStore.ts:63-65`).
    - 방어 복사: `createGameStore`에 넘긴 `saved.records`/`saved.settings`가
      스토어 조작(`dispatch`/`adjustBalance`) 이후에도 변형되지 않음을 검증한다
      (`gameStore.ts:30-31`).
  - `npx tsc --noEmit`가 종료 코드 0으로 통과한다.
- **touch**
  - `src/persistence/storage.test.ts`
  - `src/store/gameStore.test.ts`

### T4. 게임 상태 스토어 & 상태 머신 + 말 카탈로그 (M2) — [x] 완료

로비→카운트다운→경주→피니시→정산 상태 머신과 게임 상태 스토어를 구현했다.
탭 비활성화 대응(자체 결정: 합의, 자동 일시정지)을 위해 pause/resume 전이를
포함했다. 파산 자동 재충전 로직과, 로비에 출전할 말 카탈로그·팩토리를
정의했다. 말 팩토리는 스탯 하한을 보장하여 도메인 모듈의 0-스탯 NaN 경로를
차단한다(T2 REVIEW 메모 2 해소). 말 팩토리가 부여하는 id 규칙이 저장 계층의
`records` 키(`SavedState.records: Record<string, RaceRecord>`)와 정합하도록
보장했다(T3 REVIEW 메모 3 해소).

- **acceptance**
  - `src/store/`에 상태 스토어와 상태 머신 모듈이 존재하고, `src/domain/`에
    말 카탈로그·팩토리 모듈이 존재한다. 외부 상태 라이브러리 없이 가장 단순한
    구성(구독 기반 커스텀 스토어)으로 구현한다.
  - `npm run test`로 단위 테스트가 통과한다. 최소 검증 항목:
    - 상태 전이가 정의된 순서(로비→카운트다운→경주→피니시→정산→로비)로만
      진행되고, 정의되지 않은 전이는 거부/무시된다.
    - `pause`/`resume` 전이가 존재하고, 경주 중에만 유효하다.
    - 파산 처리: 잔고가 최소 베팅액(100) 미만이 되면 기본 잔고(10,000)로
      재충전되고 파산 횟수가 1 증가한다.
    - 말 팩토리가 생성한 모든 말의 각 스탯이 하한(> 0) 이상이며,
      `estimateWinProbabilities`·`applyRoundVariance`에 넣어도 NaN이 없다.
    - 말 팩토리가 생성한 말 id가 고유하고, 그 id를 키로 `SavedState.records`에
      넣어 `validateSavedState`를 통과한다(저장 계층과 id 규칙 정합, T3 메모 3).
  - `npx tsc --noEmit`가 종료 코드 0으로 통과한다.
- **touch**
  - `src/store/gameStore.ts`, `src/store/machine.ts`, `src/store/*.test.ts`
  - `src/domain/horses.ts`(말 카탈로그·팩토리), `src/domain/horses.test.ts`

### T3. 저장 계층 (persistence) (M2) — [x] 완료

`localStorage`에 잔고·전적·설정을 저장/로드하는 계층을 렌더링·React와 분리된
모듈로 구현한다. 저장 스키마를 정의하고, 손상 데이터와 저장소 미가용 상황을
안전하게 폴백한다. 부작용(실제 `localStorage` 접근)은 주입 가능한 인터페이스로
감싸 단위 테스트가 가능하게 한다. (평가: PASS 11/12)

- **acceptance**
  - `src/persistence/`에 저장 스키마·save/load·검증 모듈이 존재한다.
  - `npm run test`로 저장 계층 단위 테스트가 통과한다. 최소 검증 항목:
    - 정상 라운드트립: `save` 후 `load`가 동일한 상태를 복원한다.
    - 손상 데이터(JSON 파싱 실패, 스키마 불일치) 입력 시 예외 없이 초기값을
      반환하고, 손상 감지 플래그(또는 결과 구분)를 노출한다.
    - 저장소 미가용(접근 시 예외 발생하는 스토리지 주입) 시 세션 메모리로
      폴백하고, "저장 비활성" 상태를 노출한다.
  - `npx tsc --noEmit`가 종료 코드 0으로 통과한다.
- **touch**
  - `src/persistence/schema.ts` (저장 데이터 타입·검증), 또는 `src/domain/`의
    저장 타입을 참조
  - `src/persistence/storage.ts`, `src/persistence/storage.test.ts`

### T2. 도메인 타입 & 스탯 변동·배당 순수 모듈 (M1) — [x] 완료

말·스탯·스킬·게임 상태의 핵심 타입을 정의하고, 회차별 스탯 변동(±10%),
승률 추정, 배당 계산을 렌더링과 분리된 순수 함수로 구현한다. 단위 테스트로
경계 동작을 검증한다.

- **acceptance**
  - `src/domain/`에 타입·스탯 변동·배당 모듈이 존재한다.
  - `npm run test`로 도메인 단위 테스트가 통과한다. 최소 검증 항목:
    - 스탯 변동 결과가 기준값의 ±10% 범위 내에 있다.
    - 배당률이 `1 / 추정승률 × 하우스계수` 규칙을 따르고, 추정승률이 높은 말일수록 배당률이 낮다.
    - 모든 말의 추정승률 합이 1로 정규화된다.
  - `npx tsc --noEmit`가 통과한다.
- **touch**
  - `src/domain/types.ts`
  - `src/domain/stats.ts`, `src/domain/stats.test.ts`
  - `src/domain/odds.ts`, `src/domain/odds.test.ts`

### T1. 프로젝트 스캐폴딩 (M1) — [x] 완료

Vite + React 18 + TypeScript 프로젝트를 초기화하고 vitest 테스트 러너를
구성한다. 최소한의 App 컴포넌트가 렌더되고, 빌드·타입체크·테스트가
동작하는 상태를 만든다.

- **acceptance**
  - `npm install`이 종료 코드 0으로 완료된다.
  - `npx tsc --noEmit`가 종료 코드 0으로 통과한다.
  - `npm run build`가 종료 코드 0으로 성공한다.
  - `npm run test`가 vitest를 실행하여 종료 코드 0으로 통과한다(예시 테스트 1개 포함 허용).
- **touch**
  - `package.json`, `vite.config.ts`, `tsconfig.json`, `tsconfig.node.json`
  - `index.html`, `src/main.tsx`, `src/App.tsx`
  - `vitest` 설정(vite.config.ts의 test 필드 또는 별도 설정), `src/App.test.tsx`(예시)
  - `.gitignore`(node_modules, dist 등)

## 비고

- **이번 사이클(계획)**: T17(로비 말 카드)이 PASS(11/12, 화면 없는 항목 기준)로
  완료됐다. PLAN.md M5의 T17 체크박스가 미완료로 남아 있던 불일치를 완료로
  정정했다. M5의 네 번째 태스크 T18(베팅 패널)을 이번 세션에 진행한다. T18은
  `src/ui/`에 베팅 금액 검증 순수 함수(`betValidation.ts`, `MIN_BET_AMOUNT`
  재사용)와 베팅 패널 컴포넌트(`BetPanel.tsx`, 말 선택·프리셋/직접입력·확정
  게이팅)를 세우고, 확정 이벤트를 콜백으로 위로 넘기는 지점까지만 다룬다. 확정
  이후의 상태 전이·선차감(`adjustBalance`)·경주 생성 배선은 T20의 몫이다. T17
  REVIEW 메모 1(결정론 rng 소비 순서 검증 강화)은 시드 PRNG 실배선이 붙는 T20으로
  유지했고(PLAN T18·T20 참고에 반영), 메모 2(시각 완성도)는 T20/M6 이관을 유지했다.
- **T14(폭죽 파티클 + 우승마 스포트라이트 연출) 완료**. `src/render/particles.ts`에
  `createFireworkParticles`(주입 rng로 각도·속력을 결정해 원점에서 퍼지는 파티클
  집합 생성, 같은 시드면 같은 집합)·`updateParticles`(dt로 위치 전진 + 중력 가속,
  수명 소진 파티클 제거, rng 미사용 순수 갱신)·`drawFireworkParticles`(완주 상태에서만
  그리며 save/restore로 상태 격리)를 작성했다. `src/render/finishFx.ts`에
  `drawWinnerSpotlight`를 추가해 `layout.leaderboard`의 1위 id로 `layout.runners`
  좌표를 찾아 그 위치에 스포트라이트를 그리도록 했다(좌표·순위 재구현 없음, 좌표
  불일치 시 예외 없이 조기 반환). 파티클 타입(`FireworkParticle`)과 연출 상수
  (`FIREWORK_PARTICLE_COUNT`·`FIREWORK_PARTICLE_LIFESPAN`·`FIREWORK_GRAVITY`·
  `FIREWORK_SPEED_MIN/MAX`·`FIREWORK_PARTICLE_RADIUS`·`WINNER_SPOTLIGHT_RADIUS`·
  `WINNER_SPOTLIGHT_COLOR`)은 `src/render/types.ts`에 추가했다. `drawFinishBanner`의
  `save()`/`restore()` 부재(T13 REVIEW 비차단 메모)는 기존 함수라 이번 태스크에서
  손대지 않고 M5 실연결 시점으로 유지했다(신규 함수인 파티클·스포트라이트만 상태
  격리 적용). `npx vitest run`(17 files, 142 tests, 2회 반복 안정)·`npx tsc --noEmit`
  모두 통과. T14 완료로 M4(Canvas 렌더링 & 연출)가 모두 끝났다. 다음 사이클은
  M5(React UI 레이어 & 실황 중계)로 진입한다.
- **이전 사이클(완료)**: T13(피니시 슬로모션 timescale + 렌더 루프 통합 + 포토 피니시 연출) 완료.
  `src/render/finishFx.ts`에 `computeSlowMotionTimeScale`(sim `isSlowMotionTriggered`
  소비, 임계값 이상이면 `SLOW_MOTION_TIME_SCALE=0.3`·미만이면 1.0)과
  `drawFinishBanner`(sim `isPhotoFinish` 소비, 접전이면 포토 피니시 문구, 아니면
  1위 러너 번호·이름 병기 우승 배너, 미완주면 미노출)를 순수 함수로 작성했다.
  `src/render/loop.ts`의 `frame()`에서 `rawDt`에 이 timescale을 곱해
  `advanceWithAccumulator`에 넘기도록 통합해, 동일 raf 타임스탬프 시퀀스에서
  슬로모션 구간의 경과 시간 전진량이 비트리거 구간 대비 배율만큼 작음을
  `loop.test.ts` 통합 테스트로 고정했다(T8 REVIEW 메모 1: 완주 후에도 선두 위치가
  트랙 길이라 진행률이 임계값을 넘으므로 별도 해제 로직 없이 슬로모션이 자연히
  유지되는 정책으로 확정, `finishFx.test.ts`에 경계 테스트로 고정). `effects.test.ts`에
  T12 REVIEW 테스트 충실도 메모 3건(스킬 배너 `skillId` 부재 조기 반환, 미지
  skillId id 폴백, 스킬 이펙트 layout 좌표 부재 조기 반환)을 프로덕션 코드 변경
  없이 단언으로 흡수했다. `drawFinishBanner`는 순수 함수로만 존재하며
  `renderRace`/실제 canvas 연결(M5)에는 아직 연결하지 않았다(touch 범위 밖).
  `npx vitest run`(16 files, 130 tests, 3회 반복 안정)·`npx tsc --noEmit` 모두
  통과. 다음은 T14(폭죽 파티클 + 우승마 스포트라이트).
- **이전 사이클(계획)**: T12(스킬 발동 이펙트+스킬명 배너)가 PASS(13/15, 화면
  있는 항목 기준 12점 이상)로 완료됐다. M4의 남은 피니시 연출(원래 T13)이
  슬로모션·포토 피니시·폭죽·스포트라이트 네 요소로 한 세션 크기를 초과하므로
  T13(슬로모션 timescale + 렌더 루프 통합 + 포토 피니시 연출)과 T14(폭죽 파티클 +
  우승마 스포트라이트)로 분해했다. 이번 세션은 T13 — `isSlowMotionTriggered`를
  소비하는 dt 배율(0.3배속) 순수 함수를 주입식 `createRenderLoop`에 통합해 통합
  테스트로 고정하고, `isPhotoFinish` 소비 포토 피니시/우승 배너를 mock ctx로 그린다.
  T8 REVIEW 메모 1(완주 후 슬로모션 유지/해제 정책)을 T13 acceptance로 흡수했고,
  T12 REVIEW 테스트 충실도 메모(effects.ts 방어 분기 3종)도 T13이 렌더러/이펙트를
  다시 손대므로 흡수했다. T12 REVIEW 화면 완성도 메모(실화면 시인성)와 T9 REVIEW
  메모 1(역전 빈도 밴드 좁히기)은 실제 canvas 마운트가 필요하므로 M5로 유지한다.
- **이전 사이클(계획)**: T11(Canvas 2D 실제 렌더러)이 PASS(10/12)로 완료됐다.
  M4의 네 번째 태스크 T12(스킬 발동 이펙트+스킬명 배너)를 이번 세션에 진행한다.
  T12는 T11 렌더러 위에 발동 이력(`skillActivated`·`skillActivatedAt`)과 현재
  `elapsedTime`을 소비하는 이펙트·배너 순수 그리기 함수를 `src/render/effects.ts`에
  추가하고, mock ctx로 발동 창 판정·좌표 일치·스킬명 노출을 검증한다. 스킬명은
  도메인 `SKILL_CATALOG`의 한글 표시명을 소비한다. T11 REVIEW 비차단 메모 1(폴백
  분기 테스트)은 렌더러를 다시 손대는 T12 acceptance로 흡수했다. 메모 2(트랙 시각
  여백 상수 이원화)·메모 3(다리 모션 시각 적정성)은 실제 canvas 마운트가 필요하므로
  M5/T13으로 유지한다. T7 REVIEW 메모 3(흔들기 범위)은 T12에서 재검토하되, sim
  로직 변경이 크면 후속 태스크로 분리한다.
- **T11(Canvas 2D 실제 렌더러) 완료**. `src/render/renderer.ts`에 T10 `computeRaceLayout`
  좌표를 소비하는 `drawTrack`(트랙 배경·출발 게이트·결승선)·`drawRunners`(도형+
  다리 모션, frameTime에 따라 다리 스윙 각 변화)·`drawLeaderboard`(순위·번호·이름
  병기)와 진입점 `renderRace`를 작성했다. ctx는 `src/render/types.ts`의
  `RenderContext` 최소 인터페이스로 주입받아 mock ctx로 테스트한다. 말 도형 치수
  상수(`HORSE_BODY_RADIUS`·`HORSE_LEG_LENGTH`·`HORSE_SHAPE_HEIGHT=26`)를 확정하고,
  `layout.test.ts`에 러너 4~8마리에서 레인 밴드 폭이 `HORSE_SHAPE_HEIGHT` 이상임을
  단언하는 테스트를 추가해 T10 REVIEW 메모 1을 흡수했다. `npx vitest run`(14 files,
  106 tests, 3회 반복 안정)·`npx tsc --noEmit` 모두 통과. 다음은 T12(스킬 발동
  이펙트+배너).
- **T10(렌더 레이아웃 순수 함수+raf 렌더 루프+탭 자동 일시정지 연결) 완료**.
  `src/render/layout.ts`(computeRaceLayout, DOM·ctx 미참조)와 `src/render/loop.ts`
  (createRenderLoop, raf/visibility 주입식 오케스트레이터)를 신규 작성했다.
  `driver.test.ts`에 maxTime 미완주 분기 테스트 1개를 추가해 T9 REVIEW 메모 2를
  흡수했다. `npx vitest run`(13 files, 96 tests, 3회 반복 안정)·`npx tsc --noEmit`
  모두 통과. 다음은 T11(Canvas 2D 실제 렌더러).
- **이전 사이클(계획)**: T9가 PASS(12/12)로 완료됐다. M4의 실제 그리기(원래 T10)가
  한 세션 크기를 초과하고, 이 하네스는 Canvas 픽셀을 화면으로 확인할 수단이 없어
  아키텍처 원칙(로직·렌더 분리)에 맞춰 원래 T10을 둘로 분해했다 — **T10(렌더
  레이아웃 순수 함수 + raf 렌더 루프 + 탭 자동 일시정지 연결, 화면 없는 로직)**과
  T11(Canvas 2D 실제 렌더러). 기존 스킬 이펙트·피니시 연출은 T12·T13으로 이동했다.
  이번 세션은 T10 진행 — 시뮬레이션 상태를 화면 좌표로 매핑하는 순수 함수, 주입식
  raf·시간·visibility 위의 렌더 루프, 탭 자동 일시정지(합의: B, PRD 6번) 연결을
  vitest로 고정한다. T9 REVIEW 비차단 메모 2(maxTime 미완주 분기)를 이 태스크
  acceptance로 흡수했고, 메모 3(프레임레이트 독립성 전제)은 루프 설계 전제로
  유지한다. 메모 1(역전 빈도 밴드 좁히기)은 실제 연출로 눈으로 확인 가능한
  T13으로 이관했다.
- **이전 사이클(완료)**: T9(시뮬레이션 전체 구동기 & 연출 상수 실측·조정)를
  완료했다. `src/sim/driver.ts`에 고정 스텝 accumulator(`advanceWithAccumulator`)와
  전체 경주 완주 구동기(`runRaceToCompletion`)를 추가했다. 실측 결과 기존
  상수는 완주 시간이 범위 하단에 치우치고(무변동 기준 중앙값 약 16초, 일부
  시드에서 15초 미만) 역전 우승 빈도가 목표에 크게 못 미쳐(약 5%, 스킬은
  대부분의 말이 거의 항상 발동해 순위 차별화가 없었음) `SPEED_SCALE`(0.7→0.55),
  스킬 발동 확률 계수(`BASE_ACTIVATION_HAZARD`·`LUCK_HAZARD_WEIGHT`를 낮추고
  `RANK_HAZARD_WEIGHT`를 높여 상위권은 거의 발동하지 않고 하위권은 자주
  발동하도록 격차를 벌림), 스킬별 `selfMultiplier`(발동 시 효과가 실제
  역전으로 이어지도록 상향)를 함께 조정했다. 조정 후 완주 시간은 5마리
  기준 약 18.6~24.6초(여러 시드·4~8마리에서도 15~30초 범위 유지), 역전
  우승 빈도는 약 12~16%로 PRD 9번 목표에 들었다. `npx vitest run`(신규 7개
  포함 82개 전체 통과), `npx tsc --noEmit` 통과.
- **이전 사이클(완료)**: T8(피니시 근접 슬로모션 트리거·포토 피니시 판정)을
  `src/sim/finish.ts`에 순수 함수로 구현했다. 선두 진행률 임계값(기본 0.9)
  이상이면 슬로모션 트리거, 완주 시 1·2위 위치 차가 임계값(기본 트랙 길이의
  2%) 이하면 포토 피니시로 판정한다. 임계값은 함수 인자로도 받을 수 있어
  경계값 테스트와 이후 M4 실측 조정이 쉽다. `npx vitest run`(8개 신규 포함
  75개 전체 통과), `npx tsc --noEmit` 통과로 M3의 마지막 태스크를 완결했다.
  다음 사이클은 M4(Canvas 렌더링 & 연출)로 진입한다.
- **직전 사이클(계획)**: T7(스킬 시스템 5종·발동 확률·경주당 1회)이 PASS
  (12/12)로 완료됐다. M3의 마지막 태스크인 T8(피니시 근접 슬로모션 트리거·
  포토 피니시 판정)을 이번 세션에 진행한다. T8은 렌더·React와 분리된 순수
  판정 함수를 `src/sim/finish.ts`에 추가하며, 실제 슬로모션 감속·폭죽 연출은
  M4의 몫이다. T7 REVIEW 비차단 메모 3건(zone·slipstream 엔진 위치 반영 통합
  테스트, 발동 확률 계수 실측, 흔들기 범위 제한)은 모두 M4 통합 단계로 이관해
  PLAN M4 "T7 REVIEW 메모 흡수"에 반영했다.
- **직전 사이클(계획)**: T6(시뮬레이션 코어)가 PASS(11/12)로 완료됐다. M3
  후반으로 진입하며, 원래 T7으로 묶여 있던 "스킬 5종+발동 확률+피니시 근접+
  포토 피니시"가 한 세션 크기를 초과하므로 T7(스킬 시스템·발동 확률·경주당
  1회)과 T8(피니시 근접·포토 피니시 판정)로 분해했다. 그 세션은 T7을
  진행했다. T6 REVIEW 비차단 메모 1(burst 효과 직접 검증)을 T7 acceptance로
  흡수했다. 메모 2·3(프레임레이트 독립성 전체 구간·연출 상수 실측)은 M4/M5
  통합 단계로 이관한다.
- **직전 사이클(계획)**: T5(M2 테스트 완결)가 PASS(11/12)로 완료되어 M2를
  완결했다. M2의 모든 항목이 완료되어 M3(경주 시뮬레이션 엔진)에 진입했고,
  M3를 T6(시뮬레이션 코어)와 T7(스킬·피니시)로 분해했다.
- **T7(예정, M3 후반)**: 스킬 시스템 5종 이상의 효과를 시뮬레이션에 통합하고,
  luck·현재 순위 기반 발동 확률(하위권일수록 보정)을 경주당 최대 1회로
  적용한다. 피니시 근접 판정(슬로모션 트리거)과 1~2위 접전 포토 피니시 판정을
  엔진 상태에 노출한다. T6이 남긴 엔진 상태 타입을 확장한다. acceptance에는
  하위권 보정이 실제로 발동 확률을 높이는지, 스킬이 경주당 1회로 제한되는지,
  포토 피니시 임계값 경계 동작을 포함한다.
- **T5(M2 테스트 완결) 완료(PASS 11/12)**. 프로덕션 코드 변경 없이
  `storage.test.ts`·`gameStore.test.ts`에 저장 계층 방어 케이스(save 단독
  실패, records 항목 손상, horseCount 범위 위반)와 gameStore 계약(파산
  경계값, `adjustBalance` 알림, 방어 복사)을 추가해 M2의 테스트 부채를 모두
  정리했다(`npm run test` 43개 통과, `tsc --noEmit` 통과).
- **T5 REVIEW 비차단 메모 처리 예정**:
  - 메모 1(방어 복사 중첩 깊이): M5에서 정산 결과로 스토어가 `records`를 직접
    갱신하기 시작할 때 깊은 복사(또는 불변 갱신)와 검증 테스트를 함께 도입한다.
    해당 M5 항목 정의 시 acceptance에 반영한다.
  - 메모 2(save 정상 경로 disabled 미전환 확인): M4/M5에서 실제 저장을 스토어에
    연결할 때 정상·실패 혼재 시나리오(save 성공 후 setItem 뒤늦게 실패)를 통합
    경로로 한 번 더 확인한다.
- T4(상태 스토어·상태 머신·말 카탈로그) 완료(PASS 10/12). 다음은 T5(M2 테스트
  완결, 비차단)다. T5는 T3 REVIEW 메모 1·2(저장 계층)와 T4 REVIEW 메모 1·2·3
  (gameStore 계약)을 한 세션에서 함께 흡수해 M2의 테스트 부채를 정리한다.
  프로덕션 코드 변경 없이 테스트만 추가하는 작업이다.
- T5 완료 후 다음 사이클에 M3(경주 시뮬레이션 엔진, delta-time 고정 스텝 적분·
  스킬 5종·순위·포토 피니시)로 진입한다.
- 세 미해결 의사결정은 모두 합의 완료되어 PRD 8번에 반영되었다. 탭 자동
  일시정지(합의: B)는 T4에서 상태 머신의 pause/resume 전이(phase는 유지하고
  paused 플래그만 토글)로 준비했고, 실제 탭 이벤트 연결은 M3 시뮬레이션
  루프에서 다룬다.
- 직전 REVIEW(T4 PASS 10/12) 메모 처리 현황:
  - 메모 1(파산 경계값)·메모 2(`adjustBalance` 알림)·메모 3(방어 복사): 모두
    T5 acceptance의 gameStore 계약 케이스로 흡수했다. 프로덕션 코드는 이미
    올바르게 동작하므로 테스트 고정만 남았다.
  - 메모 4(T5 이월 유지): T5로 유지하되 저장 계층·gameStore 테스트를 한
    세션으로 묶어 M2를 완결하는 형태로 확장했다.
- T3 REVIEW(PASS 11/12) 메모 처리 현황:
  - 메모 3(말 id ↔ `records` 키 정합): T4에서 해소했다. `createHorseCatalog`가
    부여하는 `horse-{순번}` id가 `validateSavedState`를 통과하는 케이스로
    검증했다.
  - 메모 1(save 단독 실패 경로 테스트)·메모 2(schema 분기 테스트): T4에서
    흡수하지 못해 T5로 이월한다.
- T2 REVIEW(PASS 10/12) 메모 처리 현황:
  - 메모 2(0-스탯 입력 계약): T4에서 해소했다. `createHorseCatalog`가 모든
    스탯을 `MIN_BASE_STAT(1)` 이상으로 클램프하고, 변동·승률 추정에 넣어도
    NaN이 없음을 테스트로 검증했다.
  - 메모 1(컨디션 중간 밴드 테스트 보강): 컨디션 지표가 화면에 노출되는 M5
    로비 카드 작업 전에 보강한다. 해당 M5 항목 정의 시 acceptance에 포함한다.
  - 메모 3(가중치·하우스계수 값 재점검): M3 시뮬레이션의 역전 우승 빈도
    (PRD 9번)와 정합하는지 통합 검증 단계에서 재점검한다.
