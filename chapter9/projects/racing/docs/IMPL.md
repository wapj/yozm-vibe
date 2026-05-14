# IMPL — T15 마감

## 처리 항목

**T15: 마감 — 레인 순서 검증 보강 + `validateBet` 실패 UX (`#bet-hint`/`formatBetHint`)**

## 변경 파일

| 파일 | 변경 내용 |
|------|-----------|
| `src/ui.js` | `formatBetHint(reason)` 순수 함수 추가 (7번째 named export). switch로 5종 reason + fallback 한국어 매핑. |
| `src/main.js` | `formatBetHint` import 추가. `onStart` 진입에 hint clear 3줄 추가. `if (!betResult.ok) return;` → 4줄 hint 노출 분기로 교체. |
| `index.html` | `#start-btn` 직후, `#bet-panel` 닫는 태그 직전에 `<p id="bet-hint" hidden></p>` 1줄 추가. |
| `tests/test_static_skeleton.py` | `test_lane_data_horse_order` 신규 1케이스 추가 (기존 12 → 13). |
| `tests/test_ui.py` | `formatBetHint` 신규 6케이스 추가 (기존 14 → 20). import 라인에 `formatBetHint` 추가. |
| `tests/test_main.py` | `makeDoc.querySelector`에 `#bet-hint` 셀렉터 1줄 추가. 신규 4케이스 추가 (기존 59 → 63). |

## 자체 결정

- 라디오 미선택(`!selectedRadio`) 케이스는 hint 미노출·silent return 유지 — 베팅 시도 전 노이즈 회피.
- `test_lane_data_horse_order`는 `_Collector.tags`를 순회해 `div.lane`의 `data-horse` 속성을 추출하는 방식(hint 옵션 중 더 정확한 쪽 선택).
- `docs/DONE` 파일 생성 — M5 마감, 모든 PRD 섹션 코드/테스트 반영 완료.

## 검증 결과

```
uv run pytest -x
155 passed in 8.79s
```

- `tests/test_static_skeleton.py`: 13/13 PASS
- `tests/test_ui.py`: 20/20 PASS
- `tests/test_main.py`: 63/63 PASS
- 전체 회귀: 155/155 PASS
