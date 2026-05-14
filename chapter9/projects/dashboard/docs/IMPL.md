# IMPL — T-21 테스트 인프라 + UI 컴포넌트 단위/통합 테스트 (M6 이월 3·6·7)

## 처리 항목

**T-21**: M6 이월 메모 3·6·7번을 한 사이클에 처리.
- 이월 3: Vitest stderr `--localstorage-file` 경고 해소 — `vite.config.ts` `test` 블록에 `execArgv` 옵션 추가.
- 이월 7: `StaleIndicator` 단위 테스트 4케이스 — `src/components/StaleIndicator.test.tsx` 신규.
- 이월 6: `StorageWarningBanner` 통합 테스트 2케이스 — `src/components/StorageWarningBanner.test.tsx` 신규.

## 변경 파일

- `vite.config.ts` — `test` 블록에 `execArgv: ['--localstorage-file=/dev/null']` 1줄 추가
- `src/components/StaleIndicator.test.tsx` — 신규 생성 (4케이스)
- `src/components/StorageWarningBanner.test.tsx` — 신규 생성 (2케이스)
- `docs/IMPL.md` — 본 파일 (처리 항목 + 결정 사항)

## 테스트 케이스 (신규 6건)

### StaleIndicator (4케이스)

1. `failed=false` → `container.firstChild === null` (null 반환 분기)
2. `failed=true, lastUpdated=null` → `갱신 실패` 텍스트만, 시각 suffix 없음
3. `failed=true, lastUpdated=1700000000000` → `갱신 실패 · 마지막 갱신 HH:MM` 형식 (동적 expected로 타임존 회피)
4. `failed=true, lastUpdated=09:05 해당 ts` → `09:05` 포함 (0-패딩 검증)

### StorageWarningBanner (2케이스)

1. `vi.mock('../lib/storage', { isLocalStorageAvailable: () => false })` 후 동적 import → 배너 텍스트 렌더 + `aria-label="배너 닫기"` 버튼 존재
2. 닫기 버튼 `fireEvent.click` 후 `container.firstChild === null`

## 결정 사항

**결정 A: StorageWarningBanner 모듈 상수 캐시 회피 패턴**
`StorageWarningBanner.tsx:5`의 `const available = isLocalStorageAvailable()`는 모듈 로드 시 1회만 평가된다.
`vi.mock()` + `await import(...)` 동적 import 패턴을 채택하여 각 테스트에서 모킹 후 컴포넌트를 로드함으로써 모듈 상수가 항상 mocked 값으로 초기화되도록 보장했다.

**결정 B: stderr 경고 해소 방식**
Node.js 25는 worker threads에서 `localStorage` 속성 접근 시 `--localstorage-file` 플래그가 설정되지 않으면 `process.emitWarning()`으로 경고를 발생시킨다. jsdom 환경이 글로벌을 덮어쓰기 전에 이 접근이 발생하므로 경고가 누출된다. `vite.config.ts`의 `test.execArgv: ['--localstorage-file=/dev/null']`을 추가하여 Node.js가 `localStorage`를 유효한 상태로 초기화하도록 했다. `/dev/null`은 쓰기가 무시되므로 경쟁 조건 없이 모든 worker에 안전하게 적용된다. `--silent` 같은 우회나 suppressWarnings 패치 없이 공식 Node.js CLI 플래그로 해소.

## 검증 결과

- `npm test -- --run`: **85/85 통과** (기존 79 + 신규 6, 회귀 없음)
- stderr `--localstorage-file` 경고: **출력 없음**
- `npm run build`: **성공** (48 modules transformed, 타입 에러 없음)
- `src/components/StaleIndicator.tsx`·`StorageWarningBanner.tsx` 본체: **무수정**
- `src/widgets`·`src/grid`·`src/App.tsx`·`src/lib`: **무수정**
