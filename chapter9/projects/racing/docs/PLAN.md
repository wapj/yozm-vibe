# PLAN

PRD를 5개 마일스톤으로 분해한다. 한 번에 한 마일스톤만 진행하며,
각 마일스톤은 1~3개의 작은 TASK로 쪼갠다.

## 마일스톤

### M1. 정적 골격 — HTML/CSS 레이아웃 (완료)
- 단일 페이지 마크업과 스타일.
- PRD 6장(UI 흐름) / 9.1(레인 색상) / 9.3(트랙 시각) / 9.4(음소거 토글 UI)에 대응.
- 책임 모듈: `index.html`, `styles.css`.
- 결과: T1 완료, REVIEW 11/12 PASS.

### M2. 모델 & 시뮬레이션 (완료)
- 말 객체 추첨, 오즈 산정, 경주 틱 시뮬레이터, 1등 결정.
- PRD 5.1 / 5.2 / 5.3 / 9.2에 대응.
- 책임 모듈: `src/model.js`, `src/race.js`.
- 결과:
  - **T2** (완료): `src/model.js` — 5마리 말 추첨(평균속도) + 오즈 산정. REVIEW 12/12 PASS.
  - **T3** (완료): `src/race.js` — 경주 틱 시뮬레이터, 결승선 통과 노이즈, 1등 결정. REVIEW 12/12 PASS.

### M3. 베팅 / 정산 / UI 연동 (완료)
- 베팅 입력 검증, 출발 버튼, 경주 애니메이션, 결과 모달, 잔고 갱신.
- PRD 3 / 5.4 / 5.5 / 6에 대응.
- 책임 모듈: `src/bet.js`, `src/ui.js`, `src/main.js`.
- 결과: T4·T5·T6·T7·T8·T9 모두 REVIEW 12/12 PASS. 전체 회귀 92/92 PASS.
  - **T4**: `src/bet.js` — `validateBet` + `settleBet` (순수 함수).
  - **T5**: `src/ui.js` — DOM 보조 함수(포맷/위치/패널 토글).
  - **T6**: `src/main.js` 순수 헬퍼(`computeFramePositions`, `roundDelta`) +
    `index.html` 진입점 보강(`#start-btn type="button"`, `<script type="module">`,
    결과 모달 마크업).
  - **T7**: `src/main.js`에 통합 헬퍼 `runOneRace` 추가.
  - **T8**: `src/main.js`에 `initApp(document, deps?)` DOM 진입점 추가.
  - **T9**: `initApp`에 rAF 애니메이션 루프 도입(`deps.requestAnimationFrame`/`deps.now`,
    `state.lanes`/`state.running`, `finishTime` 최대값 기준 등속 보간, 종료 시
    `progress = trackLength` 1회 재호출). M3 마감.

### M4. 사운드 (완료)
- WebAudio API 효과음 4종(출발/도착/적중/실패), 음소거 토글.
- PRD 7 / 9.4에 대응.
- 책임 모듈: `src/sound.js`, `src/main.js` (와이어링 추가).
- 결과:
  - **T10** (완료): `src/sound.js` — `createSoundEngine(audioContext)` 팩토리.
    `playStart` / `playFinish` / `playWin` / `playLoss` 4종 메서드 + `setMuted` /
    `isMuted` 상태 제어. WebAudio 노드 합성으로 짧은 톤 발생, mute/falsy ctx 시 no-op.
    REVIEW 12/12 PASS, `tests/test_sound.py` 13/13, 회귀 105/105.
  - **T11** (완료): `initApp`에 사운드 와이어링. `deps.audioContext` 해석 +
    `createSoundEngine` 인스턴스화, `onStart`에 `playStart`, `finishRace`에
    `playFinish` + `playWin`/`playLoss`, `#mute-btn` 클릭 토글 + 아이콘 갱신.
    REVIEW 12/12 PASS, `tests/test_main.py` 46/46, 회귀 113/113.

### M5. 영속화 & 게임 오버 & 마감 (활성)
- `localStorage` 잔고/음소거 보존, 게임 오버 화면, 재시작.
- 엣지 케이스 마감(전액 베팅 흐름은 T9 출발 연타 방지로 일부 흡수, 잔고 0 게임오버는 T14에서 처리).
- PRD 5.6 / 6(게임 오버 화면) / 8 / 9.4(음소거 영속화) / 9.5 에 대응.
- 책임 모듈: `src/storage.js`(신규), `src/main.js`(와이어링), `index.html`(게임오버 모달 + bet-hint),
  `tests/test_static_skeleton.py`(레인 순서 검증 보강).
- 분할:
  - **T12** (완료): `src/storage.js` — 순수 함수 4종 (`loadBalance` / `saveBalance` /
    `loadMuted` / `saveMuted`). duck-typed storage mock(`{ getItem, setItem }`) 정책.
    PRD 8 명시 키 사용(`balance` 정수 문자열, `muted` `"1"`/`"0"`).
    `getItem` 결과가 `null`/형식 위반이면 `loadBalance`는 기본값 `1000`,
    `loadMuted`는 기본값 `false` 반환(가장 단순한 fallback).
    REVIEW 12/12 PASS, `tests/test_storage.py` 15/15, 회귀 128/128.
  - **T13** (완료): `initApp`에 storage 와이어링.
    `deps.storage` 주입(기본: `typeof globalThis.localStorage !== "undefined" && typeof globalThis.localStorage.getItem === "function" ? globalThis.localStorage : null` —
    Node 25 부분 구현 환경 회귀 방지 자체 결정 추가).
    초기 `state.balance = deps.initialBalance ?? loadBalance(storage)`로 복원,
    초기 mute는 `loadMuted(storage)`로 `sound.setMuted(...)` + `#mute-btn` 아이콘 갱신.
    루프 종료(`finishRace`) 시 `saveBalance(storage, state.balance)`,
    `#mute-btn` 클릭 핸들러에 `saveMuted(storage, sound.isMuted())` 추가.
    REVIEW 12/12 PASS, `tests/test_main.py` 53/53, 회귀 135/135.
  - **T14** (완료): 게임 오버 화면.
    `index.html`에 `#game-over-modal`/`#game-over-message`/`#restart-btn` 마크업 추가.
    `src/main.js` finishRace 종료 시 `state.balance < 10` 분기로 게임오버 모달 표시
    (잔고 1~9 데드락 회피). `onRestart` 핸들러: 잔고 1000 리셋 → `saveBalance(1000)` →
    `#balance` 갱신 → result-modal·game-over-modal hidden → `createHorses(rng)` 재추첨 +
    `renderLaneLabels()` + `state.lanes` 재구성 → `#start-btn.disabled = false`.
    IMPL 검증: `test_main.py` 59/59 + `test_static_skeleton.py` 12/12, 회귀 144/144 PASS.
  - **T15** (활성): 마감.
    (1) `tests/test_static_skeleton.py`에 레인 `data-horse` 시퀀스 순서 검증 보강
    (T1 REVIEW 권고 — 5개 레인이 PRD 9.1의 Thunder/Mystic/Golden/Emerald/Shadow
    순서로 마크업되어 있는지 단언). (2) `index.html` `#bet-panel`에 `#bet-hint`
    요소 추가 + `src/main.js` onStart에서 `validateBet` 실패 시 `#bet-hint`에 짧은
    안내 메시지 노출(silent return → 사용자 피드백, 자체 결정 — 별도 hint 영역이
    가장 단순. `#result-message`는 `#result-modal` 내부라 hidden 상태에서 노출
    불가). 다음 onStart 진입 시 `#bet-hint.hidden = true`로 클리어. 전체 회귀
    점검 후 M5 마감 → DONE.

## 자체 결정 로그

- 2026-05-05: PRD 9번(미해결 의사결정)의 6개 항목을 1차 구현 기본값으로
  PRD에 반영했다. 사용자 미개입(정책: 자체 판단). 변경된 결정은
  PRD 9.1~9.5와 8장에 명시.
- 2026-05-05: 모듈 구조를 단일 `index.html` + `src/*.js` 분리 방식으로 정한다.
  단일 파일보다 테스트/리뷰가 용이하다는 일반적 모범 사례를 따른다.
  PRD "단일 HTML 파일 수준의 경량 구현" 목표는 외부 라이브러리 미사용으로
  충족하며, 정적 파일 다중화는 허용 범위로 본다.
- 2026-05-05: M2를 두 TASK(T2: model.js, T3: race.js)로 분할한다.
  한 사이클에 한 모듈씩 정리하여 회귀 위험을 줄이는 일반적 모범 사례.
- 2026-05-05: JS 모듈 단위 테스트는 기존 `pytest` 러너를 유지하되,
  필요 시 Python에서 `subprocess`로 `node`를 호출해 JS 함수의 출력을 검증한다.
  테스트 인프라 일관성(`pytest` 단일 진입점)을 우선하는 모범 사례.
  외부 npm 패키지는 도입하지 않는다(PRD "외부 라이브러리 없음" 정책 유지).
- 2026-05-05: T3의 시뮬레이션 단위(`dt`)는 기본 `0.05`초로 둔다.
  평균속도 80~120 정규화 단위/초, 트랙 길이 1000일 때 선두 기준 약 10초
  도달이라는 PRD 9.2 의도와 일치하면서, 200틱 내외로 부드럽게 시뮬레이션
  된다. UI 애니메이션 통합(M3) 시 동일 dt를 frame step으로 사용 가능.
- 2026-05-05: T3은 결정적 시뮬레이션(`simulateRace`) + 단위 함수
  (`tickSpeed`)만 노출하고, frame-by-frame 애니메이션 API는 M3에서
  분할 도입한다. 한 사이클을 작게 유지하기 위함.
- 2026-05-05: M3을 T4(bet.js) / T5(ui.js) / T6(main.js)로 3분할한다.
  순수 함수(T4) → DOM 함수(T5) → 통합 진입점(T6) 순으로, 의존 방향을
  단방향(아래에서 위)으로 유지하여 한 사이클 회귀 위험을 최소화한다.
- 2026-05-05: T4(bet.js)는 DOM과 무관한 순수 함수 두 개(`validateBet`,
  `settleBet`)만 노출한다. T2/T3와 동일한 `pytest` + `node` subprocess
  방식으로 단위 테스트한다. 정산 산식은 PRD 5.5의 "잔고 += 베팅액 × 배당률"
  / "잔고 -= 베팅액" 그대로 따르며 부동소수 오차는 호출 측에서 라운딩 책임.
- 2026-05-05: T5(ui.js)는 jsdom·브라우저 의존을 도입하지 않고
  **duck-typed 인자**로 DOM mutator를 작성한다. 즉 함수가 받는 element는
  `style`/`textContent`/`disabled` 등의 속성만 가진 plain object여도 동작하므로,
  `node` subprocess에서 `{ style: {} }` 같은 mock으로 검증 가능하다.
  PRD "외부 라이브러리 없음" 정책을 유지하면서 단위 테스트 가능성을 확보하는
  가장 단순한 선택. 실제 DOM 통합은 T6에서 흡수.
- 2026-05-05: T5는 포맷팅 헬퍼(잔고/오즈/결과 메시지)와 위치 계산
  (`positionPercent`)을 순수 함수로 분리하여 가독성·테스트 격리를
  높인다. 결과 메시지 포맷은 PRD 6장(결과 모달)에 명시된 "1~5위 순위 +
  베팅 결과(획득/손실)" 중 사용자 베팅 결과 줄만 담당한다(순위 표는 T6에서).
- 2026-05-05: 원래 단일 T6으로 잡혔던 `src/main.js`(순수 헬퍼 + DOM
  와이어링 + 애니메이션 + 결과 모달 + index.html 보강)는 한 세션
  10~20분 한도를 벗어난다. **T6 / T7로 2분할**한다. T6은 테스트 가능한
  순수 헬퍼 + 정적 마크업 보강만, T7은 DOM/이벤트 와이어링 + rAF 통합.
  순수→DOM 의존 방향은 T4/T5와 동일하게 단방향 유지.
- 2026-05-05: T6의 애니메이션 모델은 `simulateRace` 결과의 `finishTime`만
  사용한 **등속 보간**(`min(elapsedSec / finishTime, 1) * trackLength`)으로
  결정한다. `simulateRace`(T3 완결)를 수정하지 않고도 결정적 순위와 일치하는
  시각화를 얻을 수 있다. 정확한 틱별 위치 히스토리는 PRD 비목표.
- 2026-05-05: 부동소수 라운딩 정책은 `roundDelta = Math.round`로 정한다.
  PRD 5.4(시작 잔고 1000 / 최소 베팅 10)는 잔고/베팅을 정수 단위로 다룸을
  전제로 한다. `amount × odds`(odds 소수 둘째 자리)에서 발생하는 소수는
  정수로 반올림하여 잔고를 항상 정수로 유지한다(가장 단순한 모범 사례).
- 2026-05-05: M3 잔여를 T7(`runOneRace` 순수 헬퍼) / T8(`initApp` DOM
  진입점) / T9(rAF 애니메이션 루프) 3분할한다. T6과 동일하게 한 세션
  10~20분 한도와 jsdom 미도입(duck-typed mutator) 정책을 유지하기 위함.
  T7은 DOM 의존이 일체 없는 순수 함수만 추가하므로 회귀 위험이 가장 낮다.
  의존 방향은 T4/T5/T6과 동일하게 단방향(아래에서 위)으로 유지된다.
- 2026-05-05: T7의 `runOneRace`는 1등 결정 책임을 `settleBet`(T4)에 위임한다.
  `settleBet`이 이미 `winner = horses.find(h => h.rank === 1)`을 반환하므로
  중복 헬퍼(`chooseWinner` 등)를 신설하지 않는 가장 단순한 선택. T7은
  `settleBet` + `roundDelta`를 묶어 정수 newBalance까지 한 번에 산출하는
  얇은 통합 함수다(ranking/모달 메시지는 T8에서 흡수).
- 2026-05-05: T8의 `initApp(document, deps = {})`은 `DOMContentLoaded` 이벤트
  의존을 도입하지 않는다. `<script type="module">`(T6에서 추가됨)은 defer 동작이
  기본이라 호출 시점에 DOM이 이미 준비되어 있다. 모듈 끝의 부트스트랩은
  `if (typeof document !== "undefined") initApp(document);` 한 줄로 한정하고,
  Node subprocess(테스트) 환경에서는 `document`가 없어 자동 호출되지 않는다.
  가장 단순한 와이어링.
- 2026-05-05: T8에서 `validateBet` 실패 시 처리는 **silent ignore**로 한다.
  PRD에 입력 검증 실패 UX가 명시되지 않았고, 모달/토스트 도입은 한 사이클
  한도를 키운다. M5 마감 단계에서 사용자 피드백에 따라 보강 가능.
- 2026-05-05: T8은 트랙 시각(말 위치) 갱신·rAF·잔고 0 게임 오버·음소거 토글
  와이어링을 일체 포함하지 않는다. 각각 T9 / M5 / M5 / M4 책임. T8은
  "비즈니스 로직 와이어링(베팅→정산→모달→재시작)"만 담당하여 한 사이클
  10~20분 한도를 유지한다.
- 2026-05-05: T8 테스트는 별도 파일을 신설하지 않고 `tests/test_main.py`에
  9케이스를 추가한다(총 31케이스). T7과 동일한 응집도 우선 정책. mock은
  `querySelector`/`querySelectorAll`/`addEventListener`/element 속성만 가진
  plain object로, T5 duck-typed 정책의 자연스러운 확장.
- 2026-05-05: T9는 rAF/시간 의존을 외부에서 주입(`deps.requestAnimationFrame`,
  `deps.now`)하여 jsdom·브라우저 의존 없이 결정적으로 테스트한다. 기본값은
  각각 `globalThis.requestAnimationFrame`(브라우저)·`() => Date.now()/1000`.
  Node 테스트에서는 가짜 rAF가 큐에 쌓인 콜백을 한 번에 한 개씩 실행하면서
  `now()`를 명시적 step으로 진행시킨다. 가장 단순한 결정성 확보 방식.
- 2026-05-05: T9의 총 재생 시간은 `simulated[].finishTime`의 **최대값**으로 한다
  (선두가 결승선에 도착해도 모든 말이 도달할 때까지 시각화). PRD 5.1
  "1회 경주 소요 시간 약 10초(선두 기준)"는 평균속도 분포 기준으로 충족되며,
  꼴찌까지 표시하는 쪽이 시각적 자연스러움 우선의 가장 단순한 모범 사례.
- 2026-05-05: T9의 lane DOM 캐시는 `initApp` 시작 시 1회 수집한 다음
  `state.lanes = [{ horseEl, name }]` 형태로 보관한다. 매 프레임마다
  `querySelector`를 다시 호출하지 않아 단순/효율 모두 유리.
  duck-typed mock에서도 `lane.querySelector(".horse")` 한 번만 호출하면 충분.
- 2026-05-05: T9 종료 시 `applyHorsePositions`를 `progress = trackLength`
  상태로 한 번 더 호출한 뒤 모달을 표시한다. PRD 5.2 "동률 방지"는 결정 책임이
  `simulateRace` finishTime의 미세 노이즈로 이미 충족되었으므로, 시각 위치는
  단순히 100%로 고정.
- 2026-05-05: M4를 T10(`src/sound.js`)/T11(`initApp` 사운드 와이어링)로 2분할한다.
  T10은 DOM/`initApp` 의존이 일체 없는 순수 팩토리(`createSoundEngine(audioContext)`)
  만 노출하여 한 사이클 10~20분 한도와 단방향 의존(아래에서 위)을 유지한다.
  T11은 T10 모듈을 `initApp`에 주입(`deps.audioContext`)하여 출발/도착/적중/실패
  타이밍에 호출하고 `#mute-btn` 토글을 와이어링한다. T4/T5/T6와 동일한
  순수→DOM 분할 정책의 자연스러운 확장.
- 2026-05-05: T10은 jsdom·브라우저 의존을 도입하지 않고 **duck-typed
  AudioContext mock**으로 단위 테스트한다(T5 정책의 자연스러운 확장).
  mock은 `createOscillator`/`createGain`/`destination`/`currentTime`만 가진
  plain object로 충분하다. WebAudio 합성 산식은 가장 단순한 1-osc + envelope
  구조(주파수/지속시간만 효과별로 다름)로 구현한다.
- 2026-05-05: T10은 `audioContext`가 falsy(`null`/`undefined`)이거나 mute
  상태이면 모든 `play*` 메서드를 즉시 no-op으로 처리한다. PRD "외부 라이브러리
  없음" 정책 + Node 테스트 환경에서 자연스러운 fallback이며, 사운드 미지원
  브라우저에서도 게임 진행을 가로막지 않는 가장 단순한 모범 사례.
- 2026-05-05: T10은 `localStorage.muted` 영속화를 포함하지 않는다. PLAN.md M5
  책임이며, M4 T11은 in-memory 상태만 다룬다. 분할 원칙(한 사이클 한 책임)
  유지를 위함.
- 2026-05-05: T11의 `deps.audioContext` 기본값은
  `typeof globalThis.AudioContext === "function" ? new globalThis.AudioContext() : null`
  로 정한다. WebAudio 미지원 환경(Node 테스트)에서는 자연스럽게 `null` →
  `createSoundEngine(null)`이 모든 `play*` 호출을 no-op으로 처리(T10에서 보장).
  브라우저 자동재생 정책상 사용자 제스처 전 AudioContext가 suspended일 수
  있으나, T10 합성 자체는 throw하지 않으므로 게임 진행에 영향 없음.
- 2026-05-05: T11은 사운드 엔진 인스턴스를 외부로 노출하지 않는다.
  테스트는 `deps.audioContext`에 duck-typed mock(events 배열)을 주입하여
  주파수(880/660/988/220)로 어떤 효과음이 호출됐는지 간접 검증한다(T10
  단위 테스트와 동일 정책의 자연스러운 확장). `deps.soundEngine` 별도
  주입 옵션은 도입하지 않는다 — 표면적 최소화.
- 2026-05-05: T11의 `#mute-btn` 클릭 핸들러는 `engine.setMuted(!engine.isMuted())`
  + 아이콘 textContent 갱신("🔊"/"🔇")만 담당한다. `localStorage` 영속화·키보드
  단축키·`aria-pressed` 갱신은 일체 도입하지 않는다(M5/추후). 가장 단순한 토글.
- 2026-05-05: T11의 사운드 호출 순서는 onStart에서 `playStart` 1회
  (state.running=true 직후, simulateRace 직전), `finishRace`에서
  `applyHorsePositions(final)` 직후 `playFinish` → 결과에 따라
  `playWin`/`playLoss` → 잔고/모달 갱신 순으로 한다. 사운드는 시각 상태가
  최종 위치로 고정된 직후 한 번만 재생되도록 직렬화하여 결정성 유지.
- 2026-05-05: M5를 T12(`src/storage.js` 순수 함수)/T13(`initApp` storage 와이어링)/
  T14(게임 오버 화면 + 재시작)/T15(레인 순서 검증 보강 + validateBet 실패 UX 마감)로
  4분할한다. T4/T5/T6/T10/T11과 동일한 순수→DOM→마감 분할 정책의 자연스러운 확장.
  T12는 DOM/`initApp` 의존이 일체 없는 순수 함수 4종만 노출하여 한 사이클 한도와
  단방향 의존(아래에서 위)을 유지한다.
- 2026-05-05: T12는 jsdom·브라우저 의존을 도입하지 않고 **duck-typed storage mock**으로
  단위 테스트한다(T5/T10 정책의 자연스러운 확장). mock은 `getItem(key)`/`setItem(key, value)`
  두 메서드만 가진 plain object로 충분하다. PRD 8장의 키 명세(`balance`/`muted`)와
  값 형식(정수 문자열 / `"1"`·`"0"`)을 그대로 따른다.
- 2026-05-05: T12 fallback 정책은 `loadBalance`가 키 부재 또는 정수 파싱 실패 시
  기본값 `1000`(시작 잔고)을, `loadMuted`가 키 부재 또는 `"1"`/`"0"` 외의 값일 때
  기본값 `false`를 반환하도록 한다. PRD 5.4(시작 잔고 1000) + 9.4(음소거 초기 false)와
  자연스럽게 일치하는 가장 단순한 모범 사례.
- 2026-05-05: T13의 `deps.storage` 기본값은
  `typeof globalThis.localStorage !== "undefined" ? globalThis.localStorage : null`로
  정한다. Node 테스트 환경에서는 자연스럽게 `null` → 모든 storage 호출은
  T12 함수가 이미 `null` 가드를 갖도록 설계됐는지 확인 필요(자체 결정: T12가 storage
  자체에 대한 falsy 가드도 책임지면 단순. `loadBalance(null)` → 1000, `saveBalance(null, x)`
  → no-op, `loadMuted(null)` → false, `saveMuted(null, x)` → no-op. T13에서 분기 코드 제거).
- 2026-05-05: T14의 게임 오버 임계값은 `state.balance < 10`로 정한다. PRD 5.6은
  "잔고가 0이 되면" 명시했으나, PRD 5.4(최소 베팅 10) 제약으로 잔고 1~9는 데드락
  상태가 된다. 데드락 회피를 위한 자체 결정(가장 단순한 모범 사례). PRD 5.6의
  의도(더 이상 베팅 불가능 시 게임 오버)와도 정합.
- 2026-05-05: T14의 게임 오버 모달은 `#result-modal`과 분리된 `#game-over-modal`로
  마크업한다. 단일 책임/단순한 닫기 로직(서로 다른 버튼·텍스트). 재시작 시
  `state.balance = 1000` + `saveBalance(storage, 1000)` + 두 모달 모두 hidden true +
  horses 재생성·라벨 재렌더 + `#start-btn.disabled = false`.
- 2026-05-05: T15의 `validateBet` 실패 UX는 `#result-message`(또는 별도 hint 영역)에
  한 줄 안내("베팅 금액을 확인해주세요." 정도)를 노출하는 가장 단순한 방식.
  토스트/별도 모달은 도입하지 않는다(PRD 비목표 — 한 화면 즉시 플레이).
  자세한 형식은 T15 acceptance 정의 시점에 확정.
- 2026-05-05: T13의 `state.balance` 초기화는 `deps.initialBalance ?? loadBalance(storage)`
  순서로 한다. T7~T11의 모든 기존 테스트는 `deps.initialBalance: 1000`을 명시적으로
  주입하므로 이 fallback 순서가 회귀를 일으키지 않는다. 브라우저에서는 `deps.initialBalance`
  미지정이므로 자연스럽게 `loadBalance(storage)`가 적용된다(가장 단순한 우선순위).
- 2026-05-05: T13에서 초기 mute 상태 복원은 `sound.setMuted(loadMuted(storage))` +
  `#mute-btn.textContent = sound.isMuted() ? "🔇" : "🔊"` 한 쌍으로 처리한다.
  index.html이 이미 "🔊"을 정적으로 설정하므로 mute=false인 경우 문자열은 동일하지만,
  mute=true(저장된 음소거 상태)인 경우 아이콘이 즉시 "🔇"로 갱신되어 사용자 인지 일관성
  유지. 가장 단순한 양방향 동기화.
- 2026-05-05: T13의 `saveBalance` 호출 시점은 `finishRace`에서 `state.balance = result.newBalance`
  직후로 통일한다. `onNextRace`에서는 잔고가 변하지 않으므로 추가 저장 불필요.
  Game-over 분기(T14)에서 잔고 리셋 시점의 `saveBalance(1000)`은 T14 책임.
- 2026-05-05: T13의 `saveMuted` 호출은 `#mute-btn` 클릭 핸들러 본문 마지막에 1줄
  추가한다(`setMuted` + 아이콘 갱신 직후). 영속화 실패(예: storage=null)는 T12
  no-op 가드로 흡수되므로 분기 코드 불필요.
- 2026-05-05: T13 구현 시 `deps.storage` 기본값에 duck-type 가드를 추가했다.
  `typeof globalThis.localStorage !== "undefined" && typeof globalThis.localStorage.getItem === "function"`
  로 평가하여 Node.js 25 환경에서 `globalThis.localStorage`가 존재하지만 표준
  Web Storage API를 구현하지 않는 경우(`getItem` 미존재) `null` fallback을 보장한다.
  IMPL.md 자체 결정으로 명시(가장 단순한 회귀 방지). 브라우저 동작에는 영향 없음.
- 2026-05-05: T14의 게임 오버 모달 위치는 `#result-modal` 마크업 **직후**로 한다.
  CSS·JS 모두 `#result-modal`을 기준으로 작성됐으므로 동일 영역에 인접 배치하면
  스타일 추가 비용이 최소(가장 단순한 모범 사례). `index.html` 변경 범위는
  `#result-modal`과 `<script type="module">` 사이 7줄 내외.
- 2026-05-05: T14의 finishRace 분기 처리는 `result.newBalance < 10`이면
  `#game-over-modal`만 표시하고 `#result-modal`은 표시하지 않는다(둘 다 띄우면
  사용자 동선이 꼬임). 결과 메시지(승/패 + 잔고 변동)는 게임 오버 모달 내부에
  별도 `#game-over-message`로 노출한다(`formatResultMessage` 결과를 그대로 사용).
  잔고 표시는 두 흐름 모두 `#balance` 갱신을 공유한다.
- 2026-05-05: T14의 `#restart-btn` 클릭 핸들러는 다음 6단계로 한다(가장 단순).
  1) `state.balance = 1000` 2) `saveBalance(storage, 1000)` 3) `#balance` textContent 갱신
  4) `#result-modal.hidden = true`(혹시 떠 있을 경우 대비) + `#game-over-modal.hidden = true`
  5) `state.horses = createHorses(rng)` + `renderLaneLabels()` + `state.lanes` 재구성
  6) `#start-btn.disabled = false`. `state.lanes` 재구성은 horse 이름이 변하지 않으면
  엄밀히는 불필요하지만, 일관성과 향후 horse 이름 동적화 가능성을 위해 1회 수행한다.
- 2026-05-05: T14는 게임 오버 모달 내부에서 `#next-race-btn`을 노출하지 않는다.
  잔고 < 10이면 다음 경주 자체가 불가능하므로 단일 진입점(`#restart-btn`)만 둔다.
  사용자 흐름이 가장 단순.
- 2026-05-05: T15의 `validateBet` 실패 UX는 `#bet-panel` 내부의 신규
  `#bet-hint` 요소(`<p id="bet-hint" hidden></p>`)에 텍스트를 표시하는 방식으로
  결정한다. PLAN 초안의 "result-message 영역" 옵션은 `#result-message`가
  `#result-modal` 내부에 위치하여 hidden 상태에선 노출 불가하므로 폐기.
  토스트/알럿/별도 모달은 PRD 비목표(한 화면 즉시 플레이) 위반이므로 도입하지
  않는다. 가장 단순한 인라인 hint.
- 2026-05-05: T15의 hint 메시지는 `validateBet`이 반환하는 `reason`(`"invalid_horse"` /
  `"invalid_amount"` / `"insufficient_balance"`)에 따라 분기된 한 줄 한국어
  안내로 정한다. `formatResultMessage`를 확장하지 않고 `src/main.js` 내부의
  작은 mapping(또는 ui.js의 신규 `formatBetHint`)로 처리. 가장 단순한 쪽은
  `src/ui.js`에 `formatBetHint(reason)` 순수 함수를 추가하여 ui.js의 기존
  포맷터들과 같은 결을 유지하는 것. T5 정책(duck-typed mutator·pytest+node
  단위 테스트)의 자연스러운 확장.
- 2026-05-05: T15의 hint 클리어 정책은 onStart 진입 시 1회 `#bet-hint.hidden = true`
  + textContent 비우기로 한다. validateBet 통과 후 시뮬레이션 중에 hint를
  숨기고, 실패 시 다시 노출. 가장 단순한 라이프사이클(매 onStart에서 reset).
- 2026-05-05: T15의 레인 순서 검증은 `tests/test_static_skeleton.py`에 신규
  `test_lane_data_horse_order` 케이스 1개를 추가하는 방식으로 한다(기존
  12케이스 → 13). 기존 `test_five_lanes`는 변경하지 않는다(회귀 위험 최소).
  검증 내용: `#track .lane`의 `data-horse` 속성 시퀀스가 정확히
  `["Thunder", "Mystic", "Golden", "Emerald", "Shadow"]`(PRD 9.1) 순서.
