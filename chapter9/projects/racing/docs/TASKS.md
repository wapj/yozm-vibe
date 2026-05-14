# TASKS

## 현재 사이클

M5(영속화 & 게임 오버 & 마감) **마감 사이클**. T14 IMPL 완료 — `test_main.py` 59/59 +
`test_static_skeleton.py` 12/12, 회귀 144/144 PASS. 이번 사이클의 활성 TASK는 1개
(T15: 마감 — 레인 순서 검증 보강 + `validateBet` 실패 UX). T15는 (1)
`tests/test_static_skeleton.py`에 신규 `test_lane_data_horse_order` 1케이스를 추가해
`#track .lane`의 `data-horse` 시퀀스가 PRD 9.1의 `Thunder/Mystic/Golden/Emerald/Shadow`
순서를 정확히 따르는지 단언하고(T1 REVIEW 권고 흡수), (2) `index.html` `#bet-panel`에
`#bet-hint` 요소를 추가한 뒤 `src/main.js`의 `onStart`에서 `validateBet` 실패 시
`#bet-hint` 텍스트를 `formatBetHint(reason)`로 갱신해 사용자 피드백을 노출한다
(silent return 정책 종결). `formatBetHint` 순수 함수는 `src/ui.js`에 추가한다.
T15 완료 시 M5 마감 → 모든 PRD 섹션이 코드/테스트에 반영된 상태이므로 `docs/DONE`
생성 → 사이클 종료.

## 활성

- [x] **T15: 마감 — 레인 순서 검증 보강 + `validateBet` 실패 UX (`#bet-hint`/`formatBetHint`)** (2026-05-05, 155/155 PASS)
  - acceptance:
    - **(A) `tests/test_static_skeleton.py` — 레인 순서 검증 신규 1케이스 추가**:
      - 신규 함수명: `test_lane_data_horse_order` (기존 12케이스 → 13).
      - 검증 내용: `index.html`의 `#track` 영역 내 `<div class="lane">` 요소들의
        `data-horse` 속성이 정확히
        `["Thunder", "Mystic", "Golden", "Emerald", "Shadow"]` 순서로 등장한다.
      - 구현 힌트: 기존 `_Collector.tags`에서 `(tag, attrs)` 시퀀스를 순회하며
        `tag == "div"` AND `class` 속성에 `"lane"` 토큰을 포함하는 요소만 골라
        `data-horse` 값을 리스트로 모은 뒤 정확 시퀀스 비교. 또는 더 단순하게
        `re.findall(r'data-horse="([A-Za-z]+)"', html)`로 추출 후 비교.
      - 기존 `test_five_lanes`(개수 검증)는 변경하지 않는다(회귀 위험 최소).
      - 기존 12케이스(T1 9 + T14 3)는 동작·메시지 변경 금지.
    - **(B) `src/ui.js` — `formatBetHint(reason)` 순수 함수 추가**:
      - 신규 named export 1종 추가(기존 6종 → 7종):
        `positionPercent`, `formatBalance`, `formatOddsLabel`, `formatResultMessage`,
        `setDisabled`, `applyHorsePositions`, **`formatBetHint`** (신규).
      - 시그니처: `formatBetHint(reason: string): string`.
      - 매핑(자체 결정 — 가장 단순한 한국어 한 줄 안내):
        - `"NO_BALANCE"` → `"잔고가 부족합니다."`
        - `"INVALID_HORSE"` → `"베팅할 말을 선택하세요."`
        - `"INVALID_AMOUNT"` → `"베팅 금액을 정수로 입력하세요."`
        - `"BELOW_MIN"` → `"최소 베팅 금액은 10입니다."`
        - `"EXCEEDS_BALANCE"` → `"베팅 금액이 현재 잔고를 초과합니다."`
        - 그 외(미정의 reason 포함, 방어적 fallback) → `"베팅 정보를 확인해주세요."`
      - 본문은 단순 `switch` 또는 객체 lookup 한 줄로 충분(가장 단순한 모범 사례).
      - DOM 접근 / `import` 추가 금지(순수 함수 — T5 정책 유지).
    - **(C) `index.html` — `#bet-panel`에 `#bet-hint` 요소 1줄 추가**:
      - 위치: `#start-btn` 직후, `#bet-panel` 닫는 `</div>` 직전(가장 단순한 인접 배치).
      - 마크업:
        ```html
        <p id="bet-hint" hidden></p>
        ```
      - 초기 `hidden` 속성으로 비표시. textContent는 비어 있다.
      - 기존 `#balance`/`#mute-btn`/`#track`/`.lane`/`#horse-select`/`#bet-amount`/
        `#start-btn`/`#result-modal`/`#game-over-modal`/`<script type="module">`
        마크업은 **변경 금지**.
    - **(D) `src/main.js` — `onStart`에 `validateBet` 실패 UX 와이어링**:
      - 상단 import 변경: `import { formatBalance, formatOddsLabel, formatResultMessage, applyHorsePositions } from "./ui.js";`
        에 **`formatBetHint`**를 추가하여 5종 import.
        ```js
        import { formatBalance, formatOddsLabel, formatResultMessage, applyHorsePositions, formatBetHint } from "./ui.js";
        ```
      - 기존 5개 import(`bet.js`/`model.js`/`race.js`/`sound.js`/`storage.js`)는 변경 금지.
      - 기존 4종 named export(`computeFramePositions`, `roundDelta`, `runOneRace`, `initApp`)와
        `initApp(document, deps = {})` 시그니처는 변경 금지. 신규 export 추가 금지.
      - `onStart` 본문 변경(추가 + 1줄 교체):
        - **진입 직후 hint 클리어**(`if (state.running) return;` **이후**, 첫 검증
          전에 1줄 추가):
          ```js
          const hintEl = document.querySelector("#bet-hint");
          hintEl.hidden = true;
          hintEl.textContent = "";
          ```
        - **기존 5개 silent return을 hint 노출 분기로 교체**. 기존 흐름:
          ```js
          const selectedRadio = document.querySelector('input[name="horse"]:checked');
          if (!selectedRadio) return;
          const horseIndex = state.horses.findIndex(h => h.name === selectedRadio.value);
          if (horseIndex === -1) return;
          const amount = parseInt(document.querySelector("#bet-amount").value, 10);
          const betResult = validateBet({ horseIndex, amount, balance: state.balance });
          if (!betResult.ok) return;
          ```
          - **변경**: 라디오 미선택 / horseIndex == -1 두 케이스는 `validateBet` 호출
            전에 hint를 띄우지 않고 silent return 유지(라디오 미선택은 사용자가
            아직 선택하지 않은 상태이므로 노이즈 없는 안내). `parseInt` NaN은
            `validateBet`이 `INVALID_AMOUNT`로 잡는다.
          - **`validateBet` 실패 시**(기존 `if (!betResult.ok) return;` 라인을 다음 4줄로 교체):
            ```js
            if (!betResult.ok) {
              hintEl.textContent = formatBetHint(betResult.error);
              hintEl.hidden = false;
              return;
            }
            ```
        - 이외의 모든 흐름(`#start-btn.disabled = true` 이하, simulateRace, rAF 루프,
          finishRace 분기, onRestart, mute 핸들러)은 **변경 금지**.
      - **금지 사항**:
        - `#bet-hint`를 `#start-btn` 클릭 외 다른 이벤트(라디오 변경 / `#bet-amount`
          input 등)와 결합 금지(가장 단순한 라이프사이클 — 매 onStart에서 reset).
        - 라디오 미선택(`!selectedRadio`)에 대한 hint 메시지 추가 금지(silent
          유지 — 베팅 시도 전 노이즈 회피).
        - `formatBetHint` 외에 reason→메시지 매핑 헬퍼 추가 금지.
        - `formatResultMessage` 시그니처 변경 / 결과 메시지에 reason 노출 금지
          (기존 결과 모달 포맷 유지).
        - `aria-live`/`role="alert"`/키보드 단축키 추가 금지.
        - 토스트/알럿/별도 모달 도입 금지(PRD 비목표).
        - `#bet-hint` 외 신규 DOM 요소 추가 금지.
        - `state` 객체에 새 필드 추가 금지(기존 4종: `balance`/`horses`/`running`/`lanes`).
        - 신규 named export 추가 금지(기존 4종 유지).
        - `validateBet` 본문 / 시그니처 변경 금지(`src/bet.js` 무수정).
        - `onRestart`에서 `#bet-hint` 클리어 추가 금지(가장 단순 — onStart 진입에서
          매번 reset되므로 재시작 직후 잔여 hint는 다음 onStart 진입에서 자연 정리).
      - 기존 `src/model.js`, `src/race.js`, `src/bet.js`, `src/sound.js`,
        `src/storage.js`, `styles.css`는 변경하지 않는다.
  - 테스트 보강:
    - **`tests/test_static_skeleton.py`** — 신규 1케이스 추가(기존 12 + 신규 1 = 13 PASS 목표):
      1. `test_lane_data_horse_order`: 위 (A) 명세 그대로.
    - **`tests/test_ui.py`** — `formatBetHint` 단위 테스트 신규 6케이스 추가
      (기존 14 + 신규 6 = 20 PASS 목표):
      1. `test_format_bet_hint_no_balance`: `formatBetHint("NO_BALANCE")` →
         `"잔고가 부족합니다."`.
      2. `test_format_bet_hint_invalid_horse`: `formatBetHint("INVALID_HORSE")` →
         `"베팅할 말을 선택하세요."`.
      3. `test_format_bet_hint_invalid_amount`: `formatBetHint("INVALID_AMOUNT")` →
         `"베팅 금액을 정수로 입력하세요."`.
      4. `test_format_bet_hint_below_min`: `formatBetHint("BELOW_MIN")` →
         `"최소 베팅 금액은 10입니다."`.
      5. `test_format_bet_hint_exceeds_balance`: `formatBetHint("EXCEEDS_BALANCE")` →
         `"베팅 금액이 현재 잔고를 초과합니다."`.
      6. `test_format_bet_hint_unknown_fallback`: `formatBetHint("UNKNOWN_REASON")` /
         `formatBetHint(undefined)` 양쪽 모두 `"베팅 정보를 확인해주세요."`.
      - 기존 14케이스는 동작 변경 금지.
    - **`tests/test_main.py`** — onStart 와이어링 케이스 신규 4건 추가
      (기존 59 + 신규 4 = 63 PASS 목표):
      1. `test_t15_below_min_shows_bet_hint`: 라디오 선택 O, `#bet-amount.value = "5"`
         (`BELOW_MIN`), start 클릭 → `#bet-hint.hidden === false` AND
         `#bet-hint.textContent === "최소 베팅 금액은 10입니다."` AND
         `#start-btn.disabled === false`(레이스 시작 안 함) AND
         `state.running === false`.
      2. `test_t15_exceeds_balance_shows_bet_hint`: `initialBalance: 100`, 라디오 O,
         `#bet-amount.value = "200"`(`EXCEEDS_BALANCE`), start → hint
         `"베팅 금액이 현재 잔고를 초과합니다."` 노출 + 레이스 미시작.
      3. `test_t15_invalid_amount_shows_bet_hint`: 라디오 O, `#bet-amount.value = "abc"`
         → `parseInt` NaN → `validateBet` `INVALID_AMOUNT` → hint
         `"베팅 금액을 정수로 입력하세요."` 노출.
      4. `test_t15_hint_clears_on_next_valid_start`: 1차 시도(`BELOW_MIN`)로 hint
         노출. 이후 `#bet-amount.value = "10"`로 변경 + start 클릭 →
         `#bet-hint.hidden === true` AND `#bet-hint.textContent === ""`(onStart 진입에서
         reset) AND `state.running === true`(유효 베팅 진입). rAF 큐 비우기까지
         돌리지 않아도 검증 가능(레이스 시작 직후 시점에서 hint 상태만 확인).
      - mock document 확장: `makeDoc.querySelector` 분기에 `#bet-hint` 추가:
        ```js
        if (sel === "#bet-hint") return el("bet-hint");
        ```
        `el` 기본값은 기존대로(`hidden: key === "result-modal" || key === "game-over-modal"`)
        — `bet-hint`의 초기 hidden 상태는 마크업에서만 보장하면 충분하며, 테스트에선
        onStart 진입 시 명시적으로 `hidden = true`로 reset되므로 mock 기본값은 불요.
        다만 케이스 1·2·3에서 `el("bet-hint")`의 `hidden` 초기 truthy 여부와 무관하게
        분기 후 `hidden === false` 단언이 통과해야 하므로 mock의 `hidden` 기본값은
        `false`로 두어도 무관(가장 단순).
      - 기존 59케이스는 동작 변경 금지(라디오 선택 + 유효 amount → start 흐름은 이미
        `validateBet.ok === true` 경로이므로 신규 hint 분기에 영향 없음).
  - touch:
    - `src/ui.js` (수정 — `formatBetHint` 순수 함수 1종 추가. 기존 6종 export 시그니처/본문 유지.).
    - `src/main.js` (수정 — `formatBetHint` import 추가 + `onStart` 진입에 hint clear 3줄 +
      `validateBet` 실패 분기를 silent return → hint 노출 4줄로 교체. 기존 4개 export
      시그니처 유지.).
    - `index.html` (수정 — `#bet-panel` 내부 `#start-btn` 직후에 `<p id="bet-hint" hidden></p>`
      1줄 추가. 그 외 마크업 변경 금지.).
    - `tests/test_static_skeleton.py` (수정 — 신규 1케이스 `test_lane_data_horse_order` 추가.
      기존 12케이스 변경 금지.).
    - `tests/test_ui.py` (수정 — 신규 6케이스 추가. 기존 14케이스 변경 금지.).
    - `tests/test_main.py` (수정 — `makeDoc`에 `#bet-hint` 셀렉터 1줄 추가, 신규 4케이스 추가.
      기존 59케이스 변경 금지.).
    - 그 외 파일은 일체 수정하지 않는다.

## 완료

- [x] **T14: 게임 오버 화면 + 재시작 (`#game-over-modal`/`#restart-btn`, `state.balance < 10` 분기)** (2026-05-05, 59/59 PASS)
  - acceptance:
    - **`index.html` 마크업 추가** — 기존 `#result-modal` 블록 **직후**, `<script type="module">`
      태그 **이전** 위치에 다음 마크업을 추가한다(가장 단순한 인접 배치):
      ```html
      <div id="game-over-modal" hidden>
        <p id="game-over-message"></p>
        <button id="restart-btn" type="button">다시 시작</button>
      </div>
      ```
      - `hidden` 속성은 초기 비표시. `#restart-btn`은 `type="button"`(form submit 회피, T6 정책 유지).
      - 기존 `#result-modal`/`#balance`/`#mute-btn`/`#bet-panel`/`#track`/레인 마크업은 변경 금지.
    - **`src/main.js` 변경** — 기존 5개 import(`bet.js`/`model.js`/`race.js`/`ui.js`/`sound.js`/
      `storage.js`)와 `initApp(document, deps = {})` 시그니처, 기존 4종 named export
      (`computeFramePositions`, `roundDelta`, `runOneRace`, `initApp`)는 변경 금지.
      신규 export 추가 금지.
    - **`finishRace` 분기 추가** — 기존 `finishRace` 본문에서 다음 위치를 명시적으로 변경한다:
      - 기존 흐름(변경 금지):
        1. `applyHorsePositions(finalHorses, state.lanes)` — 시각 위치 100% 고정.
        2. `sound.playFinish();` + `if (result.won) sound.playWin(); else sound.playLoss();`.
        3. `state.balance = result.newBalance;`
        4. `saveBalance(storage, state.balance);`
        5. `document.querySelector("#balance").textContent = formatBalance(state.balance);`
      - **변경**: 기존 `#result-modal` 표시 단계(현재 `document.querySelector("#result-message")` →
        `#result-modal.hidden = false`)를 다음 분기로 교체한다:
        ```js
        const message = formatResultMessage({ won: result.won, delta: result.delta, winner: result.winner });
        if (state.balance < 10) {
          document.querySelector("#game-over-message").textContent = message;
          document.querySelector("#game-over-modal").hidden = false;
        } else {
          document.querySelector("#result-message").textContent = message;
          document.querySelector("#result-modal").hidden = false;
        }
        ```
      - 의미:
        - `state.balance < 10`이면 `#game-over-modal`만 표시(`#result-modal`은 표시하지 않음 —
          사용자 동선 단일화).
        - 그 외에는 기존과 동일하게 `#result-modal`만 표시(회귀 방지).
        - 두 경우 모두 동일 `formatResultMessage` 결과를 노출(메시지 포맷은 T5 정책 유지).
      - `state.running = false`는 분기 이후(또는 분기 전, 둘 다 가능) 호출. 기존 위치 유지.
    - **`#restart-btn` 클릭 핸들러 등록** — `onNextRace` 핸들러 등록 근처(또는 mute-btn
      등록 직후)에 다음 핸들러를 추가한다:
      ```js
      function onRestart() {
        state.balance = 1000;
        saveBalance(storage, state.balance);
        document.querySelector("#balance").textContent = formatBalance(state.balance);
        document.querySelector("#result-modal").hidden = true;
        document.querySelector("#game-over-modal").hidden = true;
        state.horses = createHorses(rng);
        renderLaneLabels();
        state.lanes = state.horses.map(horse => ({
          name: horse.name,
          horseEl: document.querySelector(`.lane[data-horse="${horse.name}"] .horse`),
        }));
        document.querySelector("#start-btn").disabled = false;
      }
      document.querySelector("#restart-btn").addEventListener("click", onRestart);
      ```
      - 6단계: 잔고 리셋 → 영속화 → UI 잔고 갱신 → 두 모달 hidden → 말 재추첨·라벨·lanes 재구성 → start 활성화.
      - `#result-modal.hidden = true` 도 함께 처리(혹시 표시된 상태에서 재시작 호출 대비).
      - 등록 위치는 기존 핸들러 등록 순서를 변경하지 않는 한 자유. 단 `initApp` 내부에서
        `state`/`renderLaneLabels`/`storage`/`rng`에 접근 가능한 클로저 안에서 등록되어야 함.
    - **금지 사항**:
      - `#game-over-modal` 안에 `#next-race-btn`을 노출하지 않는다(잔고 < 10이면 다음 경주
        자체가 불가능하므로 단일 진입점만).
      - 게임 오버 시 자동 재시작 / 카운트다운 / 추가 효과음 도입 금지(PRD 비목표).
      - `state` 객체에 새 필드 추가 금지(기존 `balance`/`horses`/`running`/`lanes` 4종 유지).
      - 신규 named export 추가 금지(기존 4종만).
      - 게임 오버 분기에서 `playStart`/`playFinish`/`playWin`/`playLoss` 외 추가 사운드 금지.
      - `validateBet` 실패 UX 추가 금지(T15 책임).
      - 레인 순서 검증 보강 금지(T15 책임).
      - storage에 추가 키 저장 금지(`gamesPlayed`/`hits` 등 — PRD 9.5).
      - `aria-pressed`/`aria-label`/키보드 단축키 추가 금지.
      - try/catch wrapping 금지(T12 정책 유지).
      - `#restart-btn` 클릭 시 `simulateRace`/`runOneRace` 호출 금지(다음 경주는
        `#start-btn` 클릭이 진입점).
      - 게임 오버 임계값을 `state.balance <= 0`로 변경 금지(자체 결정: < 10).
    - 기존 `src/model.js`, `src/race.js`, `src/bet.js`, `src/ui.js`,
      `src/sound.js`, `src/storage.js`, `styles.css`는 변경하지 않는다.
      (`tests/test_main.py`/`tests/test_static_skeleton.py`만 케이스 추가 허용.
      기존 53케이스 + 9케이스(static_skeleton) 동작 변경 금지.)
  - 테스트 보강:
    - **`tests/test_static_skeleton.py`** — 신규 케이스 3건 추가(기존 9 + 신규 3 = 12 PASS 목표):
      1. **`test_game_over_modal_exists`**: `#game-over-modal` 요소가 존재하고 `hidden` 속성이 있다.
      2. **`test_game_over_message_exists`**: `#game-over-modal` 내부에 `#game-over-message` 요소가 있다.
      3. **`test_restart_btn_exists`**: `#restart-btn` 요소가 존재하고 `type="button"`이다.
    - **`tests/test_main.py`** — `_run_js_init` 헬퍼의 `makeDoc`에 `#game-over-modal`,
      `#game-over-message`, `#restart-btn` 셀렉터 3개를 추가한다(기존 53케이스 영향 없음 —
      기존 케이스는 이 셀렉터를 사용하지 않음). 신규 케이스 6건 추가(기존 53 + 신규 6 = 59 PASS 목표):

      1. **`test_t14_normal_finish_shows_result_modal_only`**: 승리 베팅 + finishRace 종료 후
         `state.balance >= 10`인 경우(예: 1000 → 1150) `#result-modal.hidden === false` AND
         `#game-over-modal.hidden === true`. 회귀 방지(기존 흐름).
      2. **`test_t14_low_balance_shows_game_over_modal_only`**: `initialBalance: 100`,
         100 베팅 패배 → 잔고 0 → `#game-over-modal.hidden === false` AND
         `#result-modal.hidden === true`. `#game-over-message.textContent`는
         `formatResultMessage({won:false, delta:-100, winner:...})` 결과와 일치.
      3. **`test_t14_balance_below_threshold_triggers_game_over`**: `initialBalance: 109`,
         100 베팅 패배 → 잔고 9(< 10) → 게임 오버 모달만 표시(임계값 검증).
      4. **`test_t14_balance_at_threshold_no_game_over`**: `initialBalance: 110`,
         100 베팅 패배 → 잔고 10(== 10, < 10 거짓) → `#result-modal.hidden === false`,
         `#game-over-modal.hidden === true`. 경계값 검증.
      5. **`test_t14_restart_resets_state`**: `initialBalance: 100`, 100 베팅 패배 후
         `#restart-btn._fire("click")` 호출 → 다음 모두 검증:
         - `#balance.textContent === formatBalance(1000)`
         - `#result-modal.hidden === true` AND `#game-over-modal.hidden === true`
         - `#start-btn.disabled === false`
         - `storage._data.balance === "1000"` (saveBalance 호출 확인)
         - 레인 라벨이 재렌더(라벨 textContent 비어있지 않음 또는 새 odds 형식 매치).
      6. **`test_t14_restart_clears_storage_consistently`**: `makeStorage({ balance: "5" })`,
         `deps.initialBalance: undefined` → `initApp` 직후 잔고 5(< 10이지만 게임 시작 전이라
         모달 표시 X — 모달 표시는 `finishRace`만의 책임, 회귀 방지). 이어서
         `#restart-btn._fire("click")` 호출 → `storage._data.balance === "1000"` AND
         `#balance.textContent === formatBalance(1000)`.

    - mock document 확장:
      ```js
      // makeDoc.querySelector switch에 다음 추가
      if (sel === "#game-over-modal") return el("game-over-modal");
      if (sel === "#game-over-message") return el("game-over-message");
      if (sel === "#restart-btn") return el("restart-btn");
      ```
      `el(key)`의 `hidden` 기본값은 기존대로 `key === "result-modal"`이지만, T14에서는
      `#game-over-modal`도 초기 hidden=true여야 하므로 다음과 같이 보강:
      ```js
      hidden: key === "result-modal" || key === "game-over-modal",
      ```
      이 한 줄 변경은 기존 53케이스에 영향 없음(기존 케이스는 `#game-over-modal`을 참조하지 않음).
    - 케이스 5의 "레인 라벨 재렌더" 검증은 `formatOddsLabel(state.horses[i])`와 일치 또는
      "비어있지 않음" 중 단순한 쪽을 택한다. 가장 단순한 검증은 라벨 textContent가
      `name` 문자열을 포함하는 것(예: `"Thunder"`).
  - touch:
    - `index.html` (수정 — `#result-modal` 직후에 `#game-over-modal` 블록 7줄 추가.
      그 외 마크업 변경 금지.)
    - `src/main.js` (수정 — `finishRace` 본문에 `state.balance < 10` 분기 추가
      (기존 `#result-message`/`#result-modal` 갱신을 분기로 교체), `#restart-btn` 클릭
      핸들러 `onRestart` 등록. 기존 4개 export 시그니처 유지.).
    - `tests/test_main.py` (수정 — `makeDoc`에 셀렉터 3개 + `hidden` 기본값 보강 1줄,
      신규 6케이스 추가. 기존 53케이스 변경 금지.).
    - `tests/test_static_skeleton.py` (수정 — 신규 3케이스 추가. 기존 9케이스 변경 금지.).
    - 그 외 파일은 일체 수정하지 않는다.

- [x] **T13: `src/main.js`의 `initApp`에 storage 와이어링 (잔고/음소거 양방향 영속화)** (2026-05-05, 53/53 PASS)
  - acceptance:
    - `src/main.js` 상단에 `import { loadBalance, saveBalance, loadMuted, saveMuted } from "./storage.js";`를
      추가한다(기존 `bet.js`/`model.js`/`race.js`/`ui.js`/`sound.js` 5종 import는 그대로 유지).
    - `initApp(document, deps = {})` 시그니처와 기존 4종 named export
      (`computeFramePositions`, `roundDelta`, `runOneRace`, `initApp`)는 변경하지 않는다.
      신규 export는 추가하지 않는다.
    - `initApp`의 deps 시그니처에 다음 1개 항목을 추가한다:
      - `deps.storage`: 기본값
        `typeof globalThis.localStorage !== "undefined" ? globalThis.localStorage : null`.
        주입된 값이 `undefined`이면 위 기본값 평가, `null`이면 `null` 그대로 사용
        (T12 4종 함수가 falsy 처리: `loadBalance(null)`→1000, `saveBalance(null,x)`→no-op,
        `loadMuted(null)`→false, `saveMuted(null,x)`→no-op).
    - **storage 해석 위치**: `const sound = createSoundEngine(audioContext);` 라인 **직후**에
      다음 1줄을 추가한다:
      ```js
      const storage = deps.storage !== undefined ? deps.storage : (typeof globalThis.localStorage !== "undefined" ? globalThis.localStorage : null);
      ```
    - **잔고 초기 복원**: `state` 객체의 `balance` 필드를 다음과 같이 변경한다:
      - 기존: `balance: deps.initialBalance ?? 1000,`
      - 변경: `balance: deps.initialBalance ?? loadBalance(storage),`
      - 의미: `deps.initialBalance`가 명시되면 그 값을 사용(기존 46개 테스트 호환),
        그렇지 않으면 `loadBalance(storage)`로 복원. storage 자체가 falsy이면
        T12 fallback으로 1000 반환.
    - **음소거 초기 복원**: `storage` 해석 직후, `state` 객체 정의보다 앞에 다음 1줄을 추가한다:
      ```js
      sound.setMuted(loadMuted(storage));
      ```
    - **음소거 아이콘 초기 동기화**: `renderLaneLabels()` 호출 직후(또는 동등한
      "DOM 초기 렌더 직후" 위치)에 다음 1줄을 추가한다:
      ```js
      document.querySelector("#mute-btn").textContent = sound.isMuted() ? "🔇" : "🔊";
      ```
      - 이유: index.html이 정적으로 "🔊"을 설정하지만, storage에 `muted="1"`이 저장된
        경우 즉시 "🔇"로 갱신되어 사운드 상태와 시각이 일관되도록 한다.
        mute=false인 경우 문자열은 동일하지만 idempotent 한 줄로 충분.
    - **루프 종료 시 잔고 저장**: `finishRace` 함수 본문에서
      `state.balance = result.newBalance;` 라인 **직후**에 다음 1줄을 추가한다:
      ```js
      saveBalance(storage, state.balance);
      ```
      - 위치: `state.balance = result.newBalance;` 와
        `document.querySelector("#balance").textContent = ...` 사이.
    - **음소거 토글 시 영속화**: `#mute-btn` 클릭 핸들러 본문에서, 기존 2줄
      (`sound.setMuted(...)` + 아이콘 갱신) **직후**에 다음 1줄을 추가한다:
      ```js
      saveMuted(storage, sound.isMuted());
      ```
      - 핸들러 최종 본문 (총 3줄):
        ```js
        sound.setMuted(!sound.isMuted());
        document.querySelector("#mute-btn").textContent = sound.isMuted() ? "🔇" : "🔊";
        saveMuted(storage, sound.isMuted());
        ```
    - **금지 사항**:
      - 게임 오버 분기 추가 금지(`state.balance < 10` 분기는 T14 책임).
      - `validateBet` 실패 UX 추가 금지(silent return 유지 — T15 책임).
      - `aria-pressed`/`aria-label` 갱신 금지(가장 단순한 토글 — 추후).
      - 키보드 단축키(M / Space 등) 추가 금지.
      - storage에 추가 키(예: `gamesPlayed`/`hits`) 저장 금지(PRD 9.5 — 1차는 잔고/음소거만).
      - try/catch로 storage 예외(quota 초과 등)를 wrapping 금지(T12 정책 유지).
      - `onNextRace`에서 `saveBalance` 추가 호출 금지(잔고가 변하지 않음).
      - `state` 객체에 새 필드 추가 금지(기존 `balance`/`horses`/`running`/`lanes` 4종만).
      - 신규 named export 추가 금지(기존 4종만).
    - 기존 `src/model.js`, `src/race.js`, `src/bet.js`, `src/ui.js`,
      `src/sound.js`, `src/storage.js`, `index.html`, `styles.css`는 변경하지 않는다.
      (`tests/test_main.py`만 케이스 추가 + `_run_js_init` 헬퍼에 storage import 추가 허용.
      기존 46케이스는 동작 변경 금지 — 모두 `initialBalance: 1000` 명시 + `storage` 미주입이라
      T13 변경에 영향 없음.)
  - 테스트 보강: `tests/test_main.py`에 T13용 케이스 7개를 **추가**한다
    (기존 46 + 신규 7 = 53 PASS 목표). `_run_js_init` 헬퍼에 `storage.js` import는
    필요하지 않다(initApp 내부에서만 사용). 다만 mock storage 헬퍼를 인라인 JS로 작성:

    ```js
    function makeStorage(initial) {
      const data = Object.assign({}, initial || {});
      const calls = [];
      return {
        getItem(key) {
          calls.push(["get", key]);
          return Object.prototype.hasOwnProperty.call(data, key) ? data[key] : null;
        },
        setItem(key, value) {
          calls.push(["set", key, String(value)]);
          data[key] = String(value);
        },
        _data: data,
        _calls: calls,
      };
    }
    ```

    검증 케이스(총 7개) — 모두 `_run_js_init`로 실행, 각 케이스는 `makeDoc`/`makeAudioCtx`/
    `makeStorage` mock 조합 + `initApp` + 상호작용 후 결과 직렬화:

    1. **storage 잔고 복원**: `makeStorage({ balance: "750" })`, `deps.initialBalance` 미주입,
       `deps.storage: storage` 주입. `initApp` 호출 직후
       `doc._el("balance").textContent === formatBalance(750)` (예: `"잔고: 750"`).
    2. **storage muted="1" → 초기 아이콘 🔇 + 사운드 mute**: `makeStorage({ muted: "1" })`,
       `deps.initialBalance: 1000`, `deps.audioContext: ctx`, `deps.storage: storage`.
       `initApp` 직후 `doc._el("mute-btn").textContent === "🔇"`.
       이어서 유효 베팅 + start 클릭 + rAF 큐 비우기 시 events에 `freq` 호출 0건
       (모든 사운드 mute).
    3. **storage muted="0" → 초기 아이콘 🔊**: `makeStorage({ muted: "0" })`,
       `deps.storage: storage` 주입. `initApp` 직후
       `doc._el("mute-btn").textContent === "🔊"`.
    4. **루프 종료 시 saveBalance 호출**: `makeStorage()`(빈), `deps.initialBalance: 1000`,
       유효 베팅 + start 클릭 + rAF 큐 비우기 후 `storage._data.balance` 가
       `String(state.balance)` 와 일치(승리/패배 어느 경우든). 더불어
       `storage._calls` 에 `["set", "balance", String(newBalance)]` 항목이 1건 이상 포함.
    5. **mute 클릭 시 saveMuted 호출**: `makeStorage()`(빈), `deps.audioContext: ctx`,
       `deps.storage: storage` 주입. `mute-btn` 1회 클릭 후 `storage._data.muted === "1"`,
       2회 클릭 후 `storage._data.muted === "0"`.
    6. **deps.initialBalance 우선**: `makeStorage({ balance: "999" })`,
       `deps.initialBalance: 500` 주입. `initApp` 직후
       `doc._el("balance").textContent === formatBalance(500)` (storage 값 무시).
    7. **storage 미주입 → 1000 fallback + throw 없음**: `deps.storage: null` 명시,
       `deps.initialBalance` 미주입. `initApp` 직후
       `doc._el("balance").textContent === formatBalance(1000)`.
       이어서 유효 베팅 + start 클릭 + rAF 큐 비우기 + `mute-btn` 클릭 모두 throw 없이 완료
       (T12 falsy 가드 회귀 방지).

    - mock document에는 추가 셀렉터 변경 불필요(기존 `#mute-btn`/`#balance`/`#start-btn` 등 그대로).
    - 케이스 1·6은 `formatBalance` 결과 문자열을 직접 비교하기 위해 `_run_js_init` 인라인 JS에서
      `formatBalance(N)`을 호출해 기댓값을 산출하는 방식이 단순(테스트가 ui.js 포맷에 결합되지 않도록).
    - 케이스 2의 `freq 0건` 검증은 T11 케이스 2와 동일 패턴이며 본 케이스의 차이는
      "사용자 클릭 없이 storage 복원만으로 mute가 활성화되어야 함"이다.
  - touch:
    - `src/main.js` (수정 — 4종 storage 함수 import 추가, `deps.storage` 해석 1줄,
      초기 `sound.setMuted(loadMuted(storage))` 1줄, 잔고 초기화에 `?? loadBalance(storage)`
      합산, `#mute-btn` 아이콘 초기 동기화 1줄, `finishRace`에 `saveBalance` 1줄,
      mute 클릭 핸들러에 `saveMuted` 1줄. 기존 4개 export 시그니처 유지.).
    - `tests/test_main.py` (수정 — `makeStorage` 헬퍼 + 신규 7케이스 추가.
      기존 46케이스는 변경 금지.).
    - 그 외 파일은 일체 수정하지 않는다.

- [x] **T12: `src/storage.js` — localStorage 순수 함수 4종** (2026-05-05, 15/15 PASS)
  - acceptance:
    - `src/storage.js` 신규. named export 4종: `loadBalance`, `saveBalance`,
      `loadMuted`, `saveMuted`. 추가 export 금지(가장 단순한 표면적).
    - 키 명세(PRD 8 그대로):
      - 잔고 키: 문자열 `"balance"` (값은 정수 문자열, 예: `"1000"`).
      - 음소거 키: 문자열 `"muted"` (값은 `"1"`(true) 또는 `"0"`(false)).
    - `loadBalance(storage)` 시그니처:
      - 인자: `storage` — duck-typed object(`{ getItem(key) → string|null, setItem(key, value) }`)
        또는 falsy(`null`/`undefined`).
      - 반환: 정수.
      - 동작:
        1. `storage`가 falsy면 `1000` 반환(no-op fallback).
        2. `storage.getItem("balance")` 호출 결과를 `raw`로 받는다.
        3. `raw`가 `null`이면 `1000` 반환.
        4. `Number.parseInt(raw, 10)` 결과가 `NaN`이거나 음수이면 `1000` 반환.
        5. 그 외에는 파싱된 정수를 반환.
    - `saveBalance(storage, value)` 시그니처:
      - 인자: `storage`(위와 동일), `value`(number).
      - 반환값 없음(`undefined`).
      - 동작:
        1. `storage`가 falsy면 즉시 return(no-op).
        2. `storage.setItem("balance", String(Math.trunc(value)))` 호출.
           (정수만 저장 — PRD 5.4 잔고는 정수 단위 정책. 부동소수 입력은 절삭.)
    - `loadMuted(storage)` 시그니처:
      - 인자: `storage`(위와 동일).
      - 반환: boolean.
      - 동작:
        1. `storage`가 falsy면 `false` 반환.
        2. `storage.getItem("muted")` 결과가 `"1"`이면 `true`, 그 외(포함 `null`,
           `"0"`, 임의 문자열)는 `false` 반환.
    - `saveMuted(storage, value)` 시그니처:
      - 인자: `storage`(위와 동일), `value`(임의 — `!!value`로 boolean 강제).
      - 반환값 없음.
      - 동작:
        1. `storage`가 falsy면 즉시 return(no-op).
        2. `storage.setItem("muted", value ? "1" : "0")` 호출.
    - **금지 사항**:
      - DOM 접근(`document`/`window`) 금지.
      - `globalThis.localStorage` 직접 참조 금지(인자로만 받음 — 테스트 가능성 확보).
      - `setTimeout` / `setInterval` / `requestAnimationFrame` 사용 금지.
      - `import` 문 사용 금지(다른 src 모듈에 의존하지 않음).
      - try/catch로 `setItem` 예외(예: 쿼터 초과)를 삼키는 wrapping 금지 — 가장 단순.
        실제 브라우저 quota 초과는 PRD 비목표.
      - 4종 외 함수(예: `clearAll`/`exportState`) 추가 금지.
      - 통계 영속화 키(예: `gamesPlayed`) 추가 금지(PRD 9.5 — 1차는 잔고만).
    - 기존 `src/model.js`, `src/race.js`, `src/bet.js`, `src/ui.js`,
      `src/main.js`, `src/sound.js`, `index.html`, `styles.css`, `tests/test_*.py`
      전부 변경 금지.
  - 테스트 보강: `tests/test_storage.py` 신규 작성.
    `pytest`+`node` subprocess 패턴(T2~T11과 동일). duck-typed storage mock:

    ```js
    function makeStorage(initial = {}) {
      const data = { ...initial };
      const calls = [];
      return {
        getItem(key) {
          calls.push(["get", key]);
          return Object.prototype.hasOwnProperty.call(data, key) ? data[key] : null;
        },
        setItem(key, value) {
          calls.push(["set", key, value]);
          data[key] = String(value);
        },
        _data: data,
        _calls: calls,
      };
    }
    ```

    검증 케이스(총 14개):
    1. **export 표면**: `loadBalance` / `saveBalance` / `loadMuted` / `saveMuted`
       4종 named export 존재.
    2. **`loadBalance` 키 부재**: 빈 storage에서 `1000` 반환.
    3. **`loadBalance` 정수 복원**: `{ balance: "750" }`에서 `750` 반환.
    4. **`loadBalance` NaN 방어**: `{ balance: "abc" }`에서 `1000` 반환.
    5. **`loadBalance` 음수 방어**: `{ balance: "-50" }`에서 `1000` 반환.
    6. **`loadBalance` falsy storage**: `loadBalance(null)` → `1000`,
       `loadBalance(undefined)` → `1000`(throw 없음).
    7. **`saveBalance` 정상 저장**: `saveBalance(storage, 750)` 후
       `storage._data.balance === "750"`.
    8. **`saveBalance` 정수 절삭**: `saveBalance(storage, 750.9)` 후
       `storage._data.balance === "750"` (부동소수 → `Math.trunc`).
    9. **`saveBalance` falsy storage**: `saveBalance(null, 500)` 호출 시 throw 없음
       (no-op).
    10. **`loadMuted` 키 부재**: 빈 storage에서 `false` 반환.
    11. **`loadMuted` `"1"` → true**: `{ muted: "1" }`에서 `true`.
    12. **`loadMuted` 그 외 false**: `{ muted: "0" }` → `false`,
        `{ muted: "true" }` → `false`(엄격 비교), `{ muted: "" }` → `false`.
    13. **`saveMuted` 저장 형식**: `saveMuted(storage, true)` 후
        `storage._data.muted === "1"`, `saveMuted(storage, false)` 후
        `storage._data.muted === "0"`. 그리고 `saveMuted(storage, 1)` → `"1"`,
        `saveMuted(storage, "")` → `"0"` (truthy/falsy 강제).
    14. **`saveMuted` falsy storage**: `saveMuted(undefined, true)` 호출 시
        throw 없음(no-op).
  - touch:
    - `src/storage.js` (신규).
    - `tests/test_storage.py` (신규 — 14케이스).
    - 그 외 파일은 일체 수정하지 않는다.

- [x] **T11: `src/main.js`의 `initApp`에 사운드 와이어링 + `#mute-btn` 토글** (2026-05-05, 46/46 PASS)
  - acceptance:
    - `src/main.js` 상단에 `import { createSoundEngine } from "./sound.js";`를 추가한다
      (기존 5개 import: `bet.js` 2종, `model.js`, `race.js`, `ui.js` 4종은 그대로 유지).
    - `initApp(document, deps = {})` 시그니처와 기존 4종 named export
      (`computeFramePositions`, `roundDelta`, `runOneRace`, `initApp`)는 변경하지 않는다.
      신규 export는 추가하지 않는다.
    - `initApp`의 deps 시그니처에 다음 1개 항목을 추가한다:
      - `deps.audioContext`: 기본값
        `typeof globalThis.AudioContext === "function" ? new globalThis.AudioContext() : null`.
        주입된 값이 `undefined`이면 위 기본값 평가, `null`이면 `null` 그대로 사용
        (`createSoundEngine`이 falsy 처리).
    - `initApp` 본문에서 deps 처리 직후(rng/raf/now 라인 이후) 다음을 수행한다:
      - `const audioContext = deps.audioContext !== undefined ? deps.audioContext : (typeof globalThis.AudioContext === "function" ? new globalThis.AudioContext() : null);`
      - `const sound = createSoundEngine(audioContext);`
    - `onStart` 흐름 변경(추가만):
      1. 기존 silent return 검증(running / radio / horseIndex / amount / validateBet) **이후**.
      2. `#start-btn.disabled = true` (기존).
      3. `state.running = true` (기존).
      4. **신규: `sound.playStart();`** (이 위치에 1줄 추가).
      5. 이후 흐름(`simulateRace` → `runOneRace` → rAF 루프) 동일 유지.
    - `finishRace` 흐름 변경(추가만, 순서 명시):
      1. `applyHorsePositions(finalHorses, state.lanes)` (기존, 시각 위치 100% 고정).
      2. **신규: `sound.playFinish();`**.
      3. **신규: `if (result.won) sound.playWin(); else sound.playLoss();`**.
      4. 이후 잔고/메시지/모달 갱신 + `state.running = false` 동일 유지.
    - **신규: `#mute-btn` 클릭 핸들러를 등록한다.**
      - 핸들러 본문은 다음 2줄로 한정:
        ```js
        sound.setMuted(!sound.isMuted());
        document.querySelector("#mute-btn").textContent = sound.isMuted() ? "🔇" : "🔊";
        ```
      - 등록 위치: `onNextRace` 등록 근처(가장 단순한 위치). 기존 핸들러
        등록 순서는 변경 가능하지만, 기존 동작에 영향이 없어야 한다.
    - `#mute-btn`의 초기 텍스트는 `index.html`이 이미 "🔊"로 설정하고 있으므로
      `initApp`에서 초기 textContent를 다시 설정하지 않는다(가장 단순). 단,
      `engine.isMuted()` 초기값(`false`)과 자연스럽게 일치.
    - **금지 사항**:
      - `localStorage` / `globalThis.localStorage` 호출 금지(M5 책임).
      - `aria-pressed`/`aria-label` 갱신 금지(가장 단순한 토글 — 추후).
      - 키보드 단축키(M / Space 등) 추가 금지.
      - `deps.soundEngine` 별도 주입 옵션 도입 금지(표면적 최소화).
      - 새로운 named export 추가 금지(기존 4종만).
      - 잔고 0 게임오버 분기 추가 금지(M5).
      - `validateBet` 실패 시 사운드 재생 금지(silent return은 유지 —
        무효 클릭에 사운드가 따라붙지 않도록).
      - BGM/발굽 리듬 / 추가 효과음 도입 금지(PRD 9.4).
    - 기존 `src/model.js`, `src/race.js`, `src/bet.js`, `src/ui.js`,
      `src/sound.js`, `index.html`, `styles.css`는 변경하지 않는다.
      (`tests/test_main.py`만 케이스 추가 허용. 기존 38케이스는 변경 금지.)
  - 테스트 보강: `tests/test_main.py`에 T11용 케이스 8개를 **추가**한다
    (기존 38 + 신규 8 = 46 PASS 목표). `_run_js_init` 헬퍼는 유지하되,
    필요 시 audioContext mock을 인라인 JS로 작성:

    ```js
    function makeAudioCtx() {
      const events = [];
      const ctx = {
        currentTime: 0,
        destination: { __tag: "destination" },
        createOscillator() {
          events.push(["createOscillator"]);
          return {
            type: null,
            frequency: { setValueAtTime: (v, t) => events.push(["freq", v]) },
            connect: () => {},
            start: () => {},
            stop: () => {},
          };
        },
        createGain() {
          events.push(["createGain"]);
          return {
            __tag: "gain",
            gain: {
              setValueAtTime: () => {},
              linearRampToValueAtTime: () => {},
            },
            connect: () => {},
          };
        },
      };
      return { ctx, events };
    }
    ```

    검증 케이스 — 기존 `_run_js_init` mock(라디오/베팅/start-btn/result-modal/lanes 등)에
    `mute-btn` 셀렉터 추가 + audioContext 주입을 결합:

    1. **mute-btn 셀렉터 mock 보강 검증**: `initApp` 호출 직후 `#mute-btn`
       textContent가 변경되지 않음(기존 "🔊" 유지 또는 빈 문자열 — 후자는 mock
       기본값). 더 정확하게는 mute-btn 핸들러가 등록되었는지(`_handlers.click`
       존재) 확인.
    2. **mute 클릭 1회 → 아이콘 🔇 + isMuted true 효과**: mute-btn 클릭 후
       `#mute-btn.textContent === "🔇"`. 이어서 start 클릭(유효 베팅) +
       rAF 큐 비우기 시 audioContext events에 `freq` 호출이 0건(모든 사운드 mute).
    3. **mute 클릭 2회 → 아이콘 🔊 복귀**: mute-btn 두 번 클릭 후
       `#mute-btn.textContent === "🔊"`. 이어서 start + rAF 종료 후
       events에 `freq` 호출이 ≥ 3건(start 880, finish 660, win/loss 한 종).
    4. **start 클릭 → playStart 880 호출**: 유효 베팅 + start 클릭 직후
       (rAF 큐 비우기 전) events에 `["freq", 880]`이 정확히 1건 포함.
    5. **win 경로 → playFinish 660 + playWin 988**: 승리 베팅 + start 클릭 +
       fakeTime을 totalDuration 이상으로 + 큐 비우기 후 events에서
       freq 880(playStart), 660(playFinish), 988(playWin)이 각 1건 이상.
       220(playLoss)은 0건.
    6. **loss 경로 → playFinish 660 + playLoss 220**: 패배 베팅 + start +
       큐 비우기 후 events에서 880, 660, 220이 각 1건 이상. 988은 0건.
    7. **invalid bet → 사운드 미발생**: 라디오 미선택 상태에서 start 클릭 시
       events에 `freq` 호출 0건(silent return이 사운드를 트리거하지 않음).
    8. **audioContext 미주입 시 throw 없음**: `deps.audioContext: null`로 init
       후 start 클릭 + rAF 큐 비우기 + mute-btn 클릭 모두 throw 없이 완료
       (`createSoundEngine(null)`의 no-op 보장 — 회귀 방지).

    - mock document에 `#mute-btn` 셀렉터를 추가해야 한다(`querySelector("#mute-btn")` →
      `el("mute-btn")`). 이 한 줄 추가는 기존 38케이스에 영향 없음(기존 케이스는
      mute-btn을 사용하지 않음).
    - audioContext 주입 시 `deps.audioContext: ctx`를 명시. 미주입 케이스
      (케이스 8)는 `deps.audioContext: null`로 명시(테스트 환경에서
      `globalThis.AudioContext`가 없어도 동작 보장).
  - touch:
    - `src/main.js` (수정 — `createSoundEngine` import 추가, `deps.audioContext`
      해석 + `sound` 인스턴스 생성, `onStart`에 `playStart` 1줄, `finishRace`에
      `playFinish`/`playWin`/`playLoss` 3줄, `#mute-btn` 클릭 핸들러 등록).
    - `tests/test_main.py` (수정 — `makeDoc`에 `#mute-btn` 셀렉터 추가,
      `makeAudioCtx` 헬퍼 + 신규 8케이스 추가. 기존 38케이스 변경 금지).
    - 그 외 파일은 일체 수정하지 않는다.

- [x] **T10: `src/sound.js` — WebAudio 효과음 4종 + mute 토글 (순수 팩토리)** (2026-05-05, 13/13 PASS)
  - acceptance:
    - `src/sound.js` 신규. named export 1종: `createSoundEngine`.
      추가 export 금지(가장 단순한 표면적).
    - `createSoundEngine(audioContext)` 시그니처:
      - 인자: `audioContext` — WebAudio `AudioContext` 인스턴스, 또는
        falsy(`null`/`undefined`/생략).
      - 반환값: 다음 6개 메서드/속성을 가진 객체.
        - `playStart()` — 출발 신호음.
        - `playFinish()` — 결승선 도착음.
        - `playWin()` — 적중 효과음.
        - `playLoss()` — 실패 효과음.
        - `setMuted(value)` — `value`를 boolean으로 강제(`!!value`)해 내부 상태에 반영.
        - `isMuted()` — 현재 mute 상태(boolean) 반환.
    - 초기 mute 상태: `false`. (음소거 영속화는 M5에서 흡수.)
    - `play*` 메서드 동작:
      - 다음 두 조건 중 하나라도 참이면 즉시 `return`(no-op):
        1. `audioContext`가 falsy.
        2. 내부 mute 상태가 `true`.
      - 그 외에는 다음 순서로 짧은 톤 1개를 합성한다:
        1. `osc = audioContext.createOscillator()`.
        2. `gain = audioContext.createGain()`.
        3. `osc.type = "sine"` 설정(기본 파형).
        4. `osc.frequency.setValueAtTime(freq, audioContext.currentTime)` 호출.
        5. `gain.gain.setValueAtTime(0.0001, audioContext.currentTime)` 호출
           (envelope 시작점).
        6. `gain.gain.linearRampToValueAtTime(peak, audioContext.currentTime + attack)`
           호출(attack envelope).
        7. `gain.gain.linearRampToValueAtTime(0.0001, audioContext.currentTime + duration)`
           호출(release envelope).
        8. `osc.connect(gain)` 호출.
        9. `gain.connect(audioContext.destination)` 호출.
        10. `osc.start(audioContext.currentTime)` 호출.
        11. `osc.stop(audioContext.currentTime + duration)` 호출.
    - 효과별 합성 파라미터(가장 단순한 톤):
      | 메서드 | freq (Hz) | duration (초) | attack (초) | peak (gain) |
      |---|---|---|---|---|
      | `playStart` | 880 | 0.15 | 0.01 | 0.2 |
      | `playFinish` | 660 | 0.20 | 0.01 | 0.2 |
      | `playWin` | 988 | 0.25 | 0.01 | 0.2 |
      | `playLoss` | 220 | 0.30 | 0.01 | 0.2 |
      - 위 값을 모듈 상단 `const SOUND_PARAMS = { ... }` 객체로 정의해
        4 메서드가 동일 헬퍼(`playTone(name)`)를 통해 호출하도록 한다(중복 제거).
        헬퍼는 export하지 않는다(내부 함수).
    - **금지 사항**:
      - DOM 접근(`document`/`window`) 금지.
      - `localStorage` / `globalThis.localStorage` 호출 금지(M5).
      - `setTimeout` / `setInterval` / `requestAnimationFrame` 사용 금지.
      - `import` 문 사용 금지(다른 src 모듈에 의존하지 않음).
      - 사운드 효과 파라미터를 함수 인자로 받지 않음(외부에서 톤 변경 금지 — 단순화).
      - 4종 외 효과 추가 금지(BGM/발굽 리듬은 PRD 9.4 미사용 결정).
    - 기존 `src/model.js`, `src/race.js`, `src/bet.js`, `src/ui.js`,
      `src/main.js`, `index.html`, `styles.css`, `tests/test_*.py` 전부 변경 금지.
  - 테스트 보강: `tests/test_sound.py` 신규 작성.
    `pytest`+`node` subprocess 패턴(T2~T9와 동일). duck-typed AudioContext mock:

    ```js
    function makeAudioContext() {
      const events = [];
      const ctx = {
        currentTime: 0,
        destination: { __tag: "destination" },
        createOscillator() {
          const osc = {
            type: null,
            frequency: {
              setValueAtTime: (v, t) => events.push(["osc.frequency.setValueAtTime", v, t]),
            },
            connect: (node) => events.push(["osc.connect", node.__tag ?? "gain"]),
            start: (t) => events.push(["osc.start", t]),
            stop: (t) => events.push(["osc.stop", t]),
          };
          // tag the gain returned by createGain so connect events are identifiable
          events.push(["createOscillator"]);
          return osc;
        },
        createGain() {
          const gain = {
            __tag: "gain",
            gain: {
              setValueAtTime: (v, t) => events.push(["gain.gain.setValueAtTime", v, t]),
              linearRampToValueAtTime: (v, t) => events.push(["gain.gain.linearRamp", v, t]),
            },
            connect: (node) => events.push(["gain.connect", node.__tag ?? "destination"]),
          };
          events.push(["createGain"]);
          return gain;
        },
      };
      return { ctx, events };
    }
    ```

    검증 케이스(총 12개):
    1. **export 표면**: `createSoundEngine` 함수가 export되며, 그 외에는 export
       되지 않는다(`Object.keys(import * as)` 길이 1).
    2. **반환 객체 표면**: `createSoundEngine(ctx)` 반환값이 `playStart` /
       `playFinish` / `playWin` / `playLoss` / `setMuted` / `isMuted` 6개 키를
       모두 가진다(추가 키 없음 검증은 생략 — 단순한 비교).
    3. **초기 mute 상태**: `engine.isMuted() === false`.
    4. **`setMuted` 토글**: `setMuted(true)` 후 `isMuted() === true`,
       `setMuted(false)` 후 `isMuted() === false`. truthy/falsy 강제 검증
       (`setMuted(1)` → `true`, `setMuted("")` → `false`).
    5. **`playStart` 합성 시퀀스**: mock ctx로 `playStart()` 호출 후 events에
       `createOscillator` / `createGain` / `osc.frequency.setValueAtTime(880, ...)` /
       `gain.gain.setValueAtTime(0.0001, ...)` / `gain.gain.linearRamp(0.2, ...)` /
       `gain.gain.linearRamp(0.0001, ...)` / `osc.connect("gain")` /
       `gain.connect("destination")` / `osc.start(...)` / `osc.stop(...)` 가
       순서대로 포함됨을 검증(부분 순서 검증).
    6. **`playFinish` 주파수**: `playFinish()` 후 events에서 `osc.frequency.setValueAtTime`
       의 첫 인자가 660.
    7. **`playWin` 주파수**: 988.
    8. **`playLoss` 주파수**: 220.
    9. **mute 시 no-op**: `setMuted(true)` 후 `playStart()` 호출해도 events.length
       가 mute 직전 상태에서 변하지 않음(`createOscillator` 미호출).
    10. **audioContext null 시 no-op**: `createSoundEngine(null)` 으로 생성한
        engine은 `playStart()` 호출에도 throw하지 않으며 정상 반환. `isMuted` 등
        다른 메서드도 정상 동작.
    11. **audioContext undefined 시 no-op**: `createSoundEngine()` (인자 생략)도
        같은 방식으로 동작(throw 없음).
    12. **연속 호출 독립성**: `playStart()` → `playFinish()` 연속 호출 시
        주파수 880 호출과 660 호출이 각각 1회씩 events에 기록.
  - touch:
    - `src/sound.js` (신규).
    - `tests/test_sound.py` (신규 — 12케이스).
    - 그 외 파일은 일체 수정하지 않는다.

- [x] **T9: `src/main.js`의 `initApp`에 rAF 애니메이션 루프 도입** (2026-05-05, REVIEW 38/38 PASS)
  - acceptance:
    - `src/main.js`의 기존 named export 4종(`computeFramePositions`,
      `roundDelta`, `runOneRace`, `initApp`)는 그대로 유지한다. 신규 export는
      추가하지 않는다. 기존 import 5종(`bet.js` 2종, `model.js`, `race.js`,
      `ui.js` 3종)도 유지한다.
    - `src/main.js` 상단에 `import { applyHorsePositions } from "./ui.js";`를
      추가한다(기존 `formatBalance`/`formatOddsLabel`/`formatResultMessage` import에
      병합 또는 별도 import 둘 다 허용 — 단순한 쪽 선택).
    - `initApp(document, deps = {})`의 deps 시그니처에 다음 두 항목을 추가한다:
      - `deps.requestAnimationFrame`: 기본 `globalThis.requestAnimationFrame`
        (없으면 fallback으로 `cb => setTimeout(cb, 16)` 등을 두지 말고,
        주입이 안 되었고 전역도 없는 경우는 즉시 종료 처리하는 가장 단순한 분기.
        실제로 브라우저에는 항상 존재, Node 테스트는 항상 주입함).
      - `deps.now`: 기본 `() => Date.now() / 1000` (초 단위).
    - `initApp` 초기화 시 lane DOM을 1회 수집해 보관한다:
      - `state.lanes = state.horses.map(horse => ({ name: horse.name, horseEl: document.querySelector(`.lane[data-horse="${horse.name}"] .horse`) }))`.
      - lane 수집은 초기 1회 + `onNextRace`에서 horses 재생성 후 horse name이 동일하므로
        재수집 불필요(name 키가 PRD 9.1에서 고정). 단, 안전을 위해 `state.lanes`는
        `state.horses` 재생성 시 동일 name 매핑을 유지하도록 그대로 둔다.
    - `state.running` 플래그(`boolean`, 기본 `false`)를 도입한다.
    - `onStart` 흐름 변경:
      1. `state.running === true`이면 silent return (출발 연타 방지).
      2. 기존 검증(라디오 / horseIndex / amount / validateBet) 동일 유지. 실패 시 silent return.
      3. `#start-btn.disabled = true` (기존과 동일).
      4. `state.running = true`.
      5. `simulated = simulateRace(state.horses, { rng })`.
      6. `result = runOneRace({ balance: state.balance, horses: simulated, bet })` 미리 산출(잔고/메시지는 루프 종료 후 표시).
      7. `state.horses = simulated` (루프가 사용할 horses 갱신).
      8. `state.balance = result.newBalance`는 **루프 종료 후 표시 시점에 적용**.
         실제 변수 갱신은 루프 시작 전에 해도 되지만, `#balance.textContent` 갱신은
         모달 표시와 동시(루프 종료 후)에 한다. 상태 일관성을 위해 변수 갱신도
         루프 종료 후로 통일한다(가장 단순).
      9. `totalDuration = Math.max(...simulated.map(h => h.finishTime))`.
      10. `startTime = now()`.
      11. rAF 콜백 `frame()` 정의:
          - `elapsedSec = now() - startTime`.
          - `positions = computeFramePositions(simulated, elapsedSec)`.
          - `horsesWithProgress = simulated.map((h, i) => ({ ...h, progress: positions[i] }))`.
          - `applyHorsePositions(horsesWithProgress, state.lanes)`.
          - `elapsedSec < totalDuration`이면 `requestAnimationFrame(frame)` 재호출.
          - `elapsedSec >= totalDuration`이면 종료 처리:
            - 종료 시점에 `progress = trackLength`(기본 1000)로 한 번 더
              `applyHorsePositions`(자체 결정 — PLAN 자체결정 로그 참조).
            - `state.balance = result.newBalance`.
            - `document.querySelector("#balance").textContent = formatBalance(state.balance)`.
            - `document.querySelector("#result-message").textContent = formatResultMessage({ won: result.won, delta: result.delta, winner: result.winner })`.
            - `document.querySelector("#result-modal").hidden = false`.
            - `state.running = false`.
      12. `requestAnimationFrame(frame)` 1회 호출로 루프 시작.
    - `onNextRace`는 변경하지 않는다(모달 닫기 + 새 horses + 라벨 재렌더 +
      `#start-btn.disabled = false`). 단, 새 horses 생성 후 `state.lanes`의
      name 매핑이 일치해야 하므로 재수집은 불필요. 추가 작업 없음.
    - **금지 사항**:
      - `setTimeout` / `setInterval` 사용 금지(rAF만 사용).
      - 사운드 재생 / `localStorage` / `window.localStorage` 호출 금지(M4·M5).
      - `#mute-btn` 와이어링 금지(M4).
      - 잔고 0 게임오버 분기 금지(M5).
      - `validateBet` 실패 UX 추가 금지(silent return 유지).
      - 새로운 named export 추가 금지(기존 4종만).
    - 기존 `src/model.js`, `src/race.js`, `src/bet.js`, `src/ui.js`,
      `index.html`, `styles.css`는 변경하지 않는다.
      (단 `tests/test_main.py`만 케이스 추가 허용. 기존 31케이스는 변경 금지.)
  - 테스트 보강: `tests/test_main.py`에 T9용 케이스 7개를 **추가**한다(기존 31 + 신규 7 = 38 PASS 목표).
    헬퍼 `_run_js_init`은 그대로 재사용하되, mock document에 `.lane[data-horse=X] .horse`
    엘리먼트(`{ style: {} }`)를 추가한다. 가짜 rAF 큐 + 가짜 `now()`를 인라인 JS로 작성:
    - `let queue = [];`
    - `const fakeRaf = cb => { queue.push(cb); return queue.length; };`
    - `let fakeTime = 0; const fakeNow = () => fakeTime;`
    - 테스트는 `fakeTime`을 step으로 진행시키면서 `queue.shift()()`로 한 프레임씩 실행.

    검증 케이스 — 각 케이스는 `_run_js_init` 인라인 JS로 mock + `initApp` + 상호작용 후 결과 직렬화:
    1. **start 클릭 — 즉시 모달 미표시**: 클릭 직후 (rAF 콜백 실행 전) `#result-modal.hidden === true`.
       기존 T8 케이스 4(즉시 모달 표시)는 본 케이스로 대체되지 않으며 케이스 4는
       **루프 종료 후 표시 검증**으로 의미가 보존되어야 한다 — 따라서 케이스 4를 수정하지 않고,
       본 케이스(7-1)는 루프 시작 직후 시점만 별도로 검증한다.
       *주의*: 기존 케이스 4(`test_init_app_start_win`)는 클릭 후 모달이 즉시
       `hidden === false`임을 단언한다. T9에서 동작이 바뀌므로 기존 케이스 4는
       "rAF 큐를 끝까지 비운 뒤" 검증하도록 **수정이 필요**하다.
       이 수정은 본 태스크에서 **허용**한다(기존 31케이스 변경 금지 원칙의 예외 — T8 acceptance 케이스 4·5·7·8는
       T9 흐름 변경에 맞춰 "rAF 큐 비우기" 후 시점 단언으로 갱신).
       나머지 27케이스(케이스 1·2·3·6·9 + T6/T7 22케이스)는 변경 금지.
    2. **rAF 첫 호출**: start 클릭 후 `queue.length === 1` (한 콜백 등록).
    3. **프레임 진행 — 위치 갱신**: `fakeTime`을 totalDuration 절반으로 진행시킨 뒤 한 콜백 실행.
       모든 lane의 `horseEl.style.left`가 `"0%"`보다 크고 `"100%"`보다 작거나 같다(부동소수 문자열 비교는 숫자 파싱).
    4. **루프 종료 — 모달 표시**: `fakeTime`을 totalDuration 이상으로 설정 후 큐를 끝까지 비우면
       `#result-modal.hidden === false` 그리고 `#result-message.textContent`가
       `"적중!"` 또는 `"실패."` 중 하나를 포함.
    5. **루프 종료 — 잔고 갱신 시점**: 루프 진행 중 `#balance.textContent`는 초기값에서 변하지 않다가,
       마지막 프레임 이후 갱신된 값으로 표시.
    6. **출발 연타 방지**: 첫 클릭 후 큐가 남아 있는 상태에서 두 번째 클릭을 호출해도
       `queue.length`가 두 배로 늘어나지 않는다(혹은 `simulateRace`가 다시 호출되지 않는다).
       검증은 `queue.length === 1`이거나 `state.running === true`인 동안 두 번째 onStart의
       조기 return으로 결과 모달 메시지가 변하지 않음을 확인.
    7. **루프 종료 후 다음 경주 가능**: 루프 종료 → next-race 클릭 → start 클릭이 정상 진행되어
       다시 큐에 콜백이 쌓인다(`state.running`이 false로 리셋됨을 간접 검증).
  - touch:
    - `src/main.js` (수정 — `applyHorsePositions` import 추가, `initApp`에
      `deps.requestAnimationFrame`/`deps.now` 주입·`state.lanes`/`state.running` 도입·
      `onStart` 흐름을 rAF 루프로 변경. 기존 4개 export 시그니처 유지.)
    - `tests/test_main.py` (수정 — T8 acceptance 케이스 4·5·7·8 흐름을 "rAF 큐 비우기 후" 시점으로 갱신,
      신규 7케이스 추가. 그 외 27케이스는 변경 금지.)
    - 그 외 파일은 수정하지 않는다.

- [x] **T8: `src/main.js`에 DOM 진입점 `initApp(document, deps?)` 추가** (2026-05-05, REVIEW 12/12 PASS)
  - 결과: `initApp` named export + 부트스트랩 가드, 4종 import 추가,
    `tests/test_main.py` 31/31 PASS(기존 22 + 신규 9), 전체 회귀 85/85 PASS.

- [x] **T7: `src/main.js`에 통합 헬퍼 `runOneRace` 추가** (2026-05-05, REVIEW 12/12 PASS)
  - 결과: `import { settleBet }` + `runOneRace` named export 추가,
    `tests/test_main.py` 22/22 PASS(기존 15 + 신규 7), 전체 회귀 76/76 PASS.

- [x] **T6: `src/main.js` 순수 헬퍼 + `index.html` 진입점 보강** (2026-05-05, REVIEW 12/12 PASS)
  - 결과: `src/main.js`(`computeFramePositions` + `roundDelta`) 신규,
    `tests/test_main.py` 15케이스 통과, `index.html`에 `#start-btn type="button"` /
    결과 모달 마크업 / `<script type="module">` 추가, 전체 회귀 69/69 통과.

- [x] **T5: `src/ui.js` — DOM 보조 함수 (포맷/위치/패널 토글)** (2026-05-05, REVIEW 12/12 PASS)
  - 결과: `src/ui.js`(6개 named export) 신규, `tests/test_ui.py` 14케이스 통과,
    전체 회귀 54/54 통과.

- [x] **T4: `src/bet.js` — 베팅 입력 검증 + 정산 계산 (순수 함수)** (2026-05-05, REVIEW 12/12 PASS)
  - 결과: `src/bet.js`(validateBet+settleBet) 신규, `tests/test_bet.py` 12케이스 통과,
    전체 회귀 40/40 통과.

- [x] **T3: `src/race.js` — 경주 틱 시뮬레이터 + 1등 결정** (2026-05-05, REVIEW 12/12 PASS)
  - 결과: `src/race.js`(tickSpeed + simulateRace) 신규, `tests/test_race.py` 10케이스 통과,
    전체 회귀 28/28 통과. M2 완결.

- [x] **T2: `src/model.js` — 말 추첨 + 오즈 산정** (2026-05-05, REVIEW 12/12 PASS)
  - 결과: `src/model.js`(computeOdds + createHorses) 신규,
    `tests/test_model.py` 신규 9케이스 통과, 회귀 9/9 통과.

- [x] **T1: HTML/CSS 정적 골격 작성** (2026-05-05, REVIEW 11/12 PASS)
  - 결과: `index.html`, `styles.css` 신규. 5레인 트랙·베팅 패널·음소거 토글 마크업,
    `pytest` 9/9 통과.
  - 후속 권고(다음 사이클들에서 흡수):
    - 레인 `data-horse` 시퀀스 순서 검증 보강 → M5 마감 단계로 이월.
    - `#start-btn`에 `type="button"` 명시 → **T6에서 처리됨**.
