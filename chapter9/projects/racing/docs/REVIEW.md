# REVIEW — T15 마감

## 개요

- 사이클: T15 (M5 마감 — 레인 순서 검증 보강 + `validateBet` 실패 UX)
- 평가일: 2026-05-05
- 테스트 실행: `uv run pytest -x`
- 결과: **155/155 PASS (전체 회귀 포함)**

---

## 판정: PASS

합계 **12/12** — 4축 전부 만점.

---

## 4축 평가

### 1. 사양 충족 — 3/3

| 항목 | 위치 | 결과 |
|------|------|------|
| (A) `test_lane_data_horse_order` 1케이스 추가 | `tests/test_static_skeleton.py:152-164` | ✓ 12→13, `data-horse` 시퀀스 정확 순서 단언 |
| (B) `formatBetHint(reason)` 순수 함수 추가 | `src/ui.js:37-46` | ✓ 5종 reason + fallback 한국어 매핑, DOM 접근 없음 |
| (C) `#bet-hint` 요소 1줄 추가 | `index.html:99` | ✓ `#start-btn` 직후, `#bet-panel` 닫는 태그 직전, `hidden` 초기 속성 |
| (D) `onStart` hint 클리어 + validateBet 실패 UX 와이어링 | `src/main.js:61-75` | ✓ 진입 시 3줄 클리어, 실패 시 4줄 분기, 라디오 미선택 silent 유지 |
| 금지 사항 준수 | 전체 | ✓ 기존 4종 export 유지, `src/bet.js` 무수정, 토스트/모달 미도입 |

TASKS.md acceptance (A)~(D) 전 항목이 코드에 반영되었고, 금지 사항 위반 없음.

### 2. 모듈 경계 — 3/3

- `formatBetHint` (`src/ui.js:37`)는 DOM 접근·`import` 문 없는 순수 함수. T5 duck-typed 정책 연속성 ✓
- `src/main.js:4` — `formatBetHint`를 `ui.js`에서 import하여 사용. 단방향 의존(ui.js → main.js) 유지 ✓
- `src/bet.js`, `src/race.js`, `src/model.js`, `src/sound.js`, `src/storage.js`, `styles.css` 무수정 ✓
- `src/main.js`의 기존 4종 named export 시그니처 유지 ✓

### 3. 테스트 충실도 — 3/3

| 파일 | 케이스 변화 | 내용 |
|------|------------|------|
| `tests/test_static_skeleton.py` | 12→13 | `test_lane_data_horse_order`: 레인 순서 정확 단언 |
| `tests/test_ui.py` | 14→20 | `formatBetHint` 5종 reason + `undefined` fallback(양쪽) |
| `tests/test_main.py` | 59→63 | `BELOW_MIN`·`EXCEEDS_BALANCE`·`INVALID_AMOUNT` hint 노출 + 유효 베팅 시 hint 클리어·`state.running === true` |

- TASKS.md 목표 케이스 수(13/20/63)와 정확히 일치 ✓
- `formatBetHint(undefined)` fallback 검증(`tests/test_ui.py:148`) — 방어적 엣지케이스 ✓
- `test_t15_hint_clears_on_next_valid_start`(`tests/test_main.py:1382`) — 실패→클리어→레이스 시작 전체 흐름 검증 ✓

### 4. 운영 고려 — 3/3

- `#bet-hint` 초기 `hidden` 속성(`index.html:99`) — 정적 마크업 단계에서 비표시 보장 ✓
- 매 `onStart` 진입 시 `hintEl.hidden = true; hintEl.textContent = ""`(`src/main.js:62-63`) — hint 잔류 없음 ✓
- 라디오 미선택(`!selectedRadio`) 케이스는 hint 미노출 silent return(`src/main.js:66`) — 베팅 시도 전 노이즈 회피 ✓
- `docs/DONE` 파일 생성으로 M5 마감·PRD 전 섹션 반영 완료 명시 ✓
- 토스트/알럿/별도 모달 미도입 — PRD "한 화면 즉시 플레이" 정책 준수 ✓

---

## 종합

| 축 | 점수 |
|----|------|
| 사양 충족 | 3 |
| 모듈 경계 | 3 |
| 테스트 충실도 | 3 |
| 운영 고려 | 3 |
| **합계** | **12 / 12** |

## M5 마감 선언

T15 완료로 M5(T12~T15) 전 TASK 완결. PRD 모든 섹션(3/5.1~5.6/6/7/8/9.1~9.5)이
코드·테스트에 반영된 상태이므로 전체 프로젝트를 **DONE**으로 선언한다.

다음 사이클로 넘기는 메모: **해당 없음 (프로젝트 완료).**

---

# REVIEW — T13: `src/main.js` storage 와이어링

## 평가 대상

- IMPL.md 처리 항목: **T13** (`src/main.js`에 storage 와이어링 — 잔고/음소거 양방향 영속화)
- 변경 파일: `src/main.js`, `tests/test_main.py`

## 테스트 실행 결과

```
uv run pytest -x tests/test_main.py -q
53 passed in 3.11s

uv run pytest -q
135 passed in 7.27s
```

- T13 acceptance: 53/53 PASS
- 전체 회귀: 135/135 PASS

## 4축 평가

### 1. 사양 충족 — **3점**

TASKS.md acceptance의 모든 항목이 구현됨.

| 항목 | 위치 | 결과 |
|---|---|---|
| `storage.js` import 추가 | `src/main.js:6` | ✅ |
| `deps.storage` 해석 | `src/main.js:33` | ✅ |
| `sound.setMuted(loadMuted(storage))` | `src/main.js:34` | ✅ |
| `state.balance: deps.initialBalance ?? loadBalance(storage)` | `src/main.js:37` | ✅ |
| `#mute-btn` 아이콘 초기 동기화 (`renderLaneLabels()` 직후) | `src/main.js:51` | ✅ |
| `saveBalance` 호출 (`state.balance = result.newBalance` 직후) | `src/main.js:86` | ✅ |
| `saveMuted` 호출 (핸들러 마지막) | `src/main.js:126` | ✅ |

금지 사항 전항목 준수:
- 게임 오버 분기(`state.balance < 10`) 없음 ✅
- `validateBet` 실패 UX 없음 (silent return 유지) ✅
- `aria-pressed`/`aria-label` 없음 ✅
- 키보드 단축키 없음 ✅
- 추가 storage 키 없음 ✅
- try/catch wrapping 없음 ✅
- `onNextRace`에서 `saveBalance` 추가 없음 ✅
- `state` 새 필드 없음 (기존 4종 유지) ✅
- 신규 named export 없음 (기존 4종 유지) ✅

IMPL.md 자체 결정: `deps.storage` 기본값 평가 시 `typeof globalThis.localStorage.getItem === "function"` duck-type 검증 추가(`src/main.js:33`). TASKS.md 스펙 대비 방어적 확장이며 IMPL.md에 명시됨 — 사양 이탈로 보지 않음.

### 2. 모듈 경계 — **3점**

- `storage` 변수가 `initApp` 클로저 내부에만 scoped, 외부 노출 없음 (`src/main.js:33~126`)
- 단방향 의존 방향 유지: `src/storage.js` → `src/main.js` (역방향 없음)
- touch 파일이 `src/main.js`와 `tests/test_main.py`로 제한 — 나머지 8파일 무변경 확인
  - `src/storage.js`, `src/sound.js`, `src/bet.js`, `src/ui.js`, `src/model.js`, `src/race.js`, `index.html`, `styles.css` 모두 미수정

### 3. 테스트 충실도 — **3점**

- 기존 46케이스 변경 없이 전부 PASS
- T13 신규 7케이스 추가 — TASKS.md 7개 검증 시나리오와 1:1 대응

| 케이스 | 검증 대상 | 결과 |
|---|---|---|
| `test_t13_storage_balance_restored` | storage에서 잔고 750 복원 | ✅ |
| `test_t13_storage_muted_icon_and_no_sound` | muted="1" 복원 → 아이콘 🔇 + 사운드 0건 | ✅ |
| `test_t13_storage_muted_zero_icon` | muted="0" → 아이콘 🔊 | ✅ |
| `test_t13_save_balance_on_finish` | 루프 종료 후 storage._data.balance == UI 잔고 + `_calls`에 set 기록 | ✅ |
| `test_t13_save_muted_on_click` | 클릭 1회 → "1", 2회 → "0" | ✅ |
| `test_t13_initial_balance_takes_priority` | `deps.initialBalance: 500` > `storage.balance: 999` | ✅ |
| `test_t13_null_storage_fallback_no_throw` | `storage: null` → 잔고 1000 fallback + 전 흐름 throw 없음 | ✅ |

`makeStorage` 헬퍼(`_data`/`_calls`)로 단순 mock이 아닌 호출 추적까지 검증(`test_t13_save_balance_on_finish`의 `hasSetCall` 단언).

### 4. 운영 고려 — **3점**

- **환경 호환성**: `globalThis.localStorage.getItem` duck-type 검증으로 Node.js 25 등 부분 구현 환경에서 예외 방지 (`src/main.js:33`). IMPL.md 자체 결정으로 명시됨.
- **기존 테스트 호환**: `deps.initialBalance ?? loadBalance(storage)` 우선순위로 기존 46케이스(`initialBalance: 1000` 명시) 회귀 없음 (`src/main.js:37`).
- **UI 즉시 일관성**: 초기 아이콘 동기화(`src/main.js:51`)로 `muted="1"` 복원 시 사용자 인지 지연 없음.
- **최소 저장 시점**: `saveBalance`는 `finishRace` 1회만, `onNextRace`에서 중복 없음.
- **graceful degradation**: `storage: null` 시 T12의 falsy 가드로 흡수 — `initApp` 전체 흐름 정상 작동.

## 종합

| 축 | 점수 |
|---|---|
| 사양 충족 | 3 |
| 모듈 경계 | 3 |
| 테스트 충실도 | 3 |
| 운영 고려 | 3 |
| **합계** | **12 / 12** |

## 판정: **PASS**

합계 12점 (≥ 9). T13 완료.

## 다음 사이클로 넘기는 메모

해당 없음 (완전 PASS).

다음 활성 TASK: **T14** — 게임 오버 화면.
- `index.html`에 `#game-over-modal` + `#restart-btn` 마크업 추가
- `finishRace` 종료 시 `state.balance < 10` 분기로 게임오버 모달 표시
- `restart-btn` 클릭 → `state.balance = 1000` + `saveBalance(storage, 1000)` + 두 모달 hidden + horses 재생성 + 라벨 재렌더 + `#start-btn.disabled = false`

---

# REVIEW — T12: `src/storage.js` — localStorage 순수 함수 4종

**평가일**: 2026-05-05
**평가 대상**: T12 (IMPL.md 기준)
**테스트 실행**: `uv run pytest -x tests/test_storage.py` → **15/15 PASSED**
**회귀 확인**: `uv run pytest` (전체) → **128/128 PASSED**

---

## 점수

| 축 | 점수 | 근거 요약 |
|---|---|---|
| 사양 충족 | 3/3 | acceptance 15케이스 전부 통과, 금지 사항 미도입, 4종 함수 명세 완전 일치 |
| 모듈 경계 | 3/3 | import 문 0개, named export 정확히 4종, DOM/globalThis 미접촉, touch 2파일 |
| 테스트 충실도 | 3/3 | TASKS.md 14케이스 1:1 대응, null/undefined/NaN/음수/절삭/truthy-falsy 강제 엣지케이스 망라 |
| 운영 고려 | 3/3 | fallback 체인으로 손상 storage 무크래시, Math.trunc 절삭 명세 준수, T13 null 처리 단순화 |
| **합계** | **12/12** | |

## 판정: PASS

합계 12점 ≥ 9점 기준 충족. T13 진입 준비 완료.

---

## 상세 근거

### 사양 충족 (3/3)

1. **`loadBalance`** — `src/storage.js:1-8`
   - `!storage` → 1000 (line 2) ✓
   - `getItem("balance") === null` → 1000 (line 4) ✓
   - `Number.parseInt(raw, 10)`가 NaN 또는 음수 → 1000 (line 6, `parsed < 0` 엄격 적용) ✓
   - 그 외 파싱된 정수 반환 (line 7) ✓

2. **`saveBalance`** — `src/storage.js:10-13`
   - `!storage` → 즉시 return no-op (line 11) ✓
   - `String(Math.trunc(value))` — 부동소수 절삭 후 문자열 저장 (line 12) ✓

3. **`loadMuted`** — `src/storage.js:15-18`
   - `!storage` → false (line 16) ✓
   - 엄격 비교 `storage.getItem("muted") === "1"` (line 17) — "0"/"true"/"" 등을 false로 처리 ✓

4. **`saveMuted`** — `src/storage.js:20-23`
   - `!storage` → 즉시 return no-op (line 20) ✓
   - `value ? "1" : "0"` — truthy/falsy 강제 (line 21) ✓

5. **금지 사항 전부 준수**:
   - `import` 문 없음 (다른 src 모듈 의존 없음) ✓
   - `document`/`window` 접근 없음 ✓
   - `globalThis.localStorage` 직접 참조 없음 ✓
   - `setTimeout`/`setInterval`/`requestAnimationFrame` 없음 ✓
   - try/catch on setItem 없음 ✓
   - 4종 외 export 없음 (`test_export_surface`에서 `Object.keys(mod).sort()` 검증 통과) ✓

### 모듈 경계 (3/3)

- `src/storage.js` 전체 24줄, import 0개 — 완전한 무의존 순수 모듈 ✓
- TASKS.md touch 목록(`src/storage.js` 신규, `tests/test_storage.py` 신규) 정확히 준수 ✓
- 기존 8파일(`src/model.js`, `src/race.js`, `src/bet.js`, `src/ui.js`, `src/main.js`, `src/sound.js`, `index.html`, `styles.css`) 전부 미수정 — 회귀 113케이스 그대로 통과 ✓
- 인자 주입(duck-typed storage) 방식: 브라우저 전역과 결합 없이 T13에서 `deps.storage = null` 분기 없이 바로 호출 가능하도록 설계됨 ✓

### 테스트 충실도 (3/3)

TASKS.md 14케이스 + 파일 존재 확인 = 15케이스 전부 구현(tests/test_storage.py).

- **케이스 6** (falsy storage): `loadBalance(null)`, `loadBalance(undefined)` 양쪽 모두 검증 (`test_load_balance_falsy_storage:99-105`) ✓
- **케이스 12** (loadMuted 그 외 false): `"0"`, `"true"`, `""` 3가지 값 모두 검증 (`test_load_muted_others_false:162-169`) ✓
- **케이스 13** (saveMuted 형식): `true`→`"1"`, `false`→`"0"`, `1`→`"1"`, `""`→`"0"` — truthy/falsy 강제 4가지 검증 (`test_save_muted_format:173-194`) ✓
- **케이스 8** (saveBalance 절삭): `750.9 → "750"` — `Math.trunc` vs `Math.round` 구분 검증 (`test_save_balance_trunc:119-125`) ✓

### 운영 고려 (3/3)

- **fallback 체인**: `storage` falsy → 기본값, `raw` null → 기본값, NaN → 기본값, 음수 → 기본값 — 손상 storage 상태에서도 앱 크래시 없음 ✓
- **PRD 정합**: `loadBalance` 기본값 1000(PRD 5.4 시작 잔고), `loadMuted` 기본값 false(PRD 9.4 음소거 초기 비활성)와 자연스럽게 일치 ✓
- **`Math.trunc` 선택**: `Math.floor`는 음수 입력 시 동작 상이, `Math.round`는 "절삭"이 아닌 "반올림" — `Math.trunc`가 PRD "부동소수 절삭" 명세를 가장 정확히 구현 ✓
- **try/catch 미포함**: PRD 비목표(quota 초과 처리 불필요) — 예기치 않은 setItem 예외가 호출 스택으로 전파되어 silent failure를 방지하는 단순하고 안전한 선택 ✓

---

## 다음 사이클로 넘기는 메모

*(완전 PASS — 필수 수정 없음. 이하는 후속 사이클 Planner 참고용)*

1. **T12 완료. 다음은 T13(`initApp`에 storage 와이어링) 진입.**

2. **T13 구현 시 유의 사항**:
   - `deps.storage` 기본값: `typeof globalThis.localStorage !== "undefined" ? globalThis.localStorage : null`
   - `loadBalance(null)` → 1000, `saveBalance(null, x)` → no-op은 T12에서 이미 보장됨 — T13에서 null 분기 코드 불필요.
   - 초기 `state.balance = loadBalance(storage)` + 초기 `sound.setMuted(loadMuted(storage))` + 아이콘 갱신.
   - 루프 종료 시 `saveBalance(storage, state.balance)`, `#mute-btn` 토글 시 `saveMuted(storage, engine.isMuted())`.
   - 게임오버 분기는 T14 책임 — T13은 포함하지 않는다.
