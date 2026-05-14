# REVIEW — T-21: 테스트 인프라 + UI 컴포넌트 단위/통합 테스트 (M6 이월 3·6·7)

- 사이클: T-21
- 평가일: 2026-05-06
- 결과: **PASS (12/12)**

---

## Acceptance 테스트 실행 결과

```
npm test -- --run (Evaluator 직접 실행)

 RUN  v4.1.5 /Users/gyus/yozm-ai-agentic/chapter9/projects/dashboard

 Test Files  12 passed (12)
       Tests  85 passed (85)   ← 기존 79 + 신규 6, 회귀 없음
   Duration  1.18s

npm run build (Evaluator 직접 실행)
✓ 48 modules transformed.
dist/assets/index-BvPiZfm2.js   211.17 kB │ gzip: 66.86 kB
✓ built in 73ms
```

stderr에 `--localstorage-file` 류 경고 출력 없음 (Evaluator 실행 기준).

---

## Acceptance 항목별 결과

| # | 조건 | 위치 | 결과 |
|---|---|---|---|
| 1 | `npm test -- --run`: 85/85 통과 (기존 79 + 신규 6, 회귀 없음) | 직접 실행 | ✅ |
| 2 | `--localstorage-file` 류 stderr 경고 미출력 | 직접 실행 | ✅ |
| 3 | `npm run build`: 성공 (타입 에러 없음) | 직접 실행 | ✅ |
| 4 | `StaleIndicator.tsx` · `StorageWarningBanner.tsx` 본체 무수정 | 파일 직접 확인 | ✅ |
| 5 | `src/widgets` · `src/grid` · `src/App.tsx` · `src/lib` 무수정 | 테스트 회귀 없음 + 파일 확인 | ✅ |
| 6 | IMPL.md "처리 항목"에 신규 테스트 6케이스 + 결정 2건 기록 | `docs/IMPL.md` | ✅ |
| 7 | REVIEW.md 사양 충족 절에 M6 이월 3·6·7번 처리 완료 기록 | 아래 사양 충족 절 | ✅ |

---

## 4축 평가

### 1. 사양 충족 — 3/3

TASKS.md T-21 acceptance 전 항목 충족. 3가지 이월 항목(이월 3·6·7) 모두 처리 완료.

| # | 요구 | 위치 | 결과 |
|---|---|---|---|
| T-21-A | StaleIndicator 4케이스 — `failed=false` null 반환 | `StaleIndicator.test.tsx:5-8` | ✅ |
| T-21-B | StaleIndicator — `failed=true, lastUpdated=null` 텍스트만 | `StaleIndicator.test.tsx:10-13` | ✅ |
| T-21-C | StaleIndicator — `failed=true, lastUpdated=number` HH:MM 형식 | `StaleIndicator.test.tsx:15-22` | ✅ |
| T-21-D | StaleIndicator — 한 자리 시/분 0-패딩 검증 (09:05) | `StaleIndicator.test.tsx:24-31` | ✅ |
| T-21-E | StorageWarningBanner — 배너 텍스트 + aria-label 버튼 렌더 | `StorageWarningBanner.test.tsx:8-13` | ✅ |
| T-21-F | StorageWarningBanner — 닫기 클릭 후 `container.firstChild === null` | `StorageWarningBanner.test.tsx:15-20` | ✅ |
| T-21-G | stderr `--localstorage-file` 경고 해소 (`vite.config.ts` execArgv) | `vite.config.ts:12` | ✅ |

### 2. 모듈 경계 — 3/3

- `StaleIndicator.test.tsx` · `StorageWarningBanner.test.tsx` 두 파일 모두 `src/components/` 코로케이션 배치 (PLAN.md 모듈 책임 표 `*.test.ts` 정책 준수) ✅
- `vite.config.ts` 변경은 `test` 블록 내 `execArgv` 1줄 + 설명 주석 3줄로 최소화; plugins / build / resolve 블록 무수정 ✅
- `StaleIndicator.tsx` (`src/components/StaleIndicator.tsx:1-20`) · `StorageWarningBanner.tsx` (`src/components/StorageWarningBanner.tsx:1-19`) 본체 완전 무수정 확인 ✅
- `src/widgets` · `src/grid` · `src/App.tsx` · `src/lib` 무수정; 테스트 85/85 회귀 없음으로 간접 확인 ✅
- `vi.mock` 패턴이 `StorageWarningBanner.test.tsx` 파일 내에 자체 완결 — lib/storage 실 구현에 영향 없음 ✅

### 3. 테스트 충실도 — 3/3

**StaleIndicator 4케이스 — 분기 완전 커버:**

| 케이스 | 테스트 위치 | 검증 방식 | 평가 |
|---|---|---|---|
| `failed=false` → null | `:5-8` | `container.firstChild === null` | `if (!failed) return null` 분기 ✅ |
| `failed=true, lastUpdated=null` | `:10-13` | `container.textContent === '갱신 실패'` 정확 일치 | suffix 없는 분기 ✅ |
| `failed=true, lastUpdated=1700000000000` | `:15-22` | `d.getHours()/getMinutes()` 동적 생성 expected로 타임존 회피 | HH:MM 형식 분기 ✅ |
| 0-패딩 검증 | `:24-31` | `base.setHours(9, 5, 0, 0)` 후 `toContain('09:05')` | `padStart(2,'0')` 경로 ✅ |

타임존 전략: `new Date(ts).getHours()/getMinutes()`로 expected를 동적 생성하므로 UTC±14 전 환경에서 CI 의존성 없음.

**StorageWarningBanner 2케이스 — 인터랙션 포함:**

| 케이스 | 테스트 위치 | 검증 방식 | 평가 |
|---|---|---|---|
| 배너 렌더 | `:8-13` | `textContent.toContain(...)` + `getByLabelText('배너 닫기')` | 모듈 상수 mock 후 렌더 확인 ✅ |
| 닫기 클릭 → null | `:15-20` | `fireEvent.click(...)` + `container.firstChild === null` | `useState` dismiss 경로 ✅ |

`vi.mock('../lib/storage', () => ({ isLocalStorageAvailable: () => false }))` 가 파일 최상단에 위치하여 컴포넌트 import 이전에 평가 — `StorageWarningBanner.tsx:5`의 `const available = isLocalStorageAvailable()` 모듈 상수가 `false`로 초기화됨을 보장. `await import('./StorageWarningBanner')` 동적 import 패턴 적절 ✅

### 4. 운영 고려 — 3/3

- `execArgv: ['--localstorage-file=/dev/null']` 적용 근거가 `vite.config.ts:9-12` 주석과 IMPL.md 결정 B에 이중 기록 — Node.js 25+ worker thread localStorage 초기화 경고의 원인과 해결 방식이 명확히 문서화 ✅
- `/dev/null`은 쓰기가 무시되므로 모든 worker thread에서 경쟁 조건 없이 적용 가능, 테스트 데이터 오염 없음 ✅
- `--silent` · `suppressWarnings` · 환경변수 우회 등 은폐 방식 미사용; 공식 Node.js CLI 플래그로 근본 해소 (TASKS.md 제약 준수) ✅
- 결정 A (StorageWarningBanner 모듈 상수 캐시 회피를 위한 `vi.mock` + 동적 import 패턴) IMPL.md에 기록 ✅
- 결정 B (stderr 경고 해소 방식과 사유) IMPL.md에 기록 ✅
- 두 신규 테스트 파일 모두 타임존 독립 전략 적용(StaleIndicator) 및 모킹 격리(StorageWarningBanner) — CI 환경에서도 안정적으로 동작 가능 ✅

---

## 사양 충족 절 — M6 이월 3·6·7번 처리 완료

| 이월 번호 | 항목 | 처리 내용 | 위치 |
|---|---|---|---|
| M6 이월 3 | Vitest stderr `--localstorage-file` 경고 해소 | `vite.config.ts` `test` 블록에 `execArgv: ['--localstorage-file=/dev/null']` 1줄 추가 | `vite.config.ts:12` |
| M6 이월 6 | `StorageWarningBanner` 통합 테스트 | `vi.mock` + 동적 import로 모듈 상수 캐시 회피, 미가용 분기 렌더 + 닫기 인터랙션 2케이스 | `src/components/StorageWarningBanner.test.tsx` |
| M6 이월 7 | `StaleIndicator` 단위 테스트 | `failed/lastUpdated` 4조합 분기 완전 커버, 0-패딩 검증 포함 | `src/components/StaleIndicator.test.tsx` |

M6 잔여: 이월 4(T-22) · 5(T-22) + 빌드/preview 검증(T-23) + PRD 최종 점검(T-23).

---

## 합계

| 축 | 점수 |
|---|---|
| 사양 충족 | 3 |
| 모듈 경계 | 3 |
| 테스트 충실도 | 3 |
| 운영 고려 | 3 |
| **합계** | **12/12** |

**결과: PASS**
