# 개인용 대시보드 구현 계획 (PLAN)

PRD를 6개 마일스톤으로 분해한다. 각 마일스톤은 검증 가능한 산출물 단위다.
TASKS.md는 본 PLAN의 순서를 따른다.

## 마일스톤

### M1. 프로젝트 골격 / 그리드 레이아웃
- React + Vite + TypeScript 프로젝트 초기화
- 디렉터리 구조: `src/widgets/`, `src/lib/`, `src/App.tsx`, `public/`
- 4열 × 2행 고정 그리드 + 위젯 7개 placeholder + 여백 1칸
- CSS Modules 적용 (PRD §12: 스타일링 결정)
- 검증: `npm run dev`로 페이지 진입 시 7개 빈 카드 + 1칸 여백이 정확히 보인다.

### M2. 코어 라이브러리 (storage / api)
- `useLocalStorage<T>` 훅 — JSON 직렬화, SSR-safe, 미지원 환경(시크릿 모드 등)
  감지 시 인메모리 폴백
- 키 네이밍 헬퍼: `dashboard.<widget>.<field>`
- `fetchWithCache(url, ttlMs, cacheKey)` — 메모리 캐시 + `localStorage` 백업
- 외부 API 클라이언트: `api/openMeteo.ts`, `api/exchangerateHost.ts`
- 검증: 단위 테스트(스토리지 폴백, fetchWithCache 캐시 적중) 통과.

### M3. 로컬 데이터 위젯 (시계 / 메모 / 링크 / 일정 / 명언)
- Clock 위젯: 1초 갱신, `YYYY-MM-DD (요일) HH:MM:SS`
- Memo 위젯: 추가/삭제/완료 토글, 정렬(최신 위, 완료 하단), `localStorage` 영속
- Links 위젯: 섹션 + 링크 CRUD, URL 정규화 + 중복 차단 토스트
- Schedule 위젯: 오늘 일정만, 시각 오름차순, 5분 폴링으로 다른 탭 변경 반영
- Quote 위젯: 정적 JSON(`quotes.ko.json`) + 날짜 기반 인덱스 회전(자정 통과
  시 새 명언)
- 검증: 새로고침 후 메모/일정/링크 데이터가 복원된다. URL 정규화·일정 필터·
  명언 인덱스 단위 테스트 통과.

### M4. 외부 API 위젯 (날씨 / 환율)
- Weather 위젯: Open-Meteo, 성남 좌표 상수, 10분 갱신, 캐시 폴백 + "갱신 실패"
  표시
- Exchange 위젯: exchangerate.host `timeseries`로 전일·당일 동시 조회, USD/JPY/
  EUR → KRW, 30분 갱신, 등락 화살표/차이 표시, 캐시 폴백
- 검증: 네트워크 차단 상태에서도 페이지가 깨지지 않고 캐시 또는 빈 상태가
  뜬다. 환율 등락 계산 단위 테스트 통과.

### M5. 에러 / 입력 정책 마무리
- 외부 API 실패 시 "갱신 실패 · 마지막 갱신 HH:MM" 표시 (Weather/Exchange 공용
  컴포넌트)
- `localStorage` 미지원 환경에서 페이지 상단 1회 경고 배너
- 빈 제목/잘못된 URL 등 입력 검증: 인라인 에러 + 추가 차단
- 첫 콘텐츠 1초 내 렌더 확인(Suspense 없이도 placeholder→데이터 전환)
- 검증: PRD §11 성공 기준 4가지가 모두 충족된다.

### M6. 테스트 / 빌드 마감
- Vitest 설정 (jsdom 환경)
- 핵심 단위 테스트 보강: `useLocalStorage`, URL 정규화, 일정 필터, 명언 인덱스,
  환율 등락 계산
- `npm run build` 산출물이 에러 없이 생성, `npm run preview`에서 동작 확인
- 검증: 테스트 전 항목 통과 + 빌드 성공.

## 모듈 책임 요약

| 영역 | 위치 | 책임 |
|---|---|---|
| App 셸 / 그리드 | `src/App.tsx`, `src/grid/*` | 4×2 레이아웃, 위젯 슬롯 배치 |
| 위젯 | `src/widgets/<name>/*` | 위젯별 UI + 로컬 상태 |
| 스토리지 | `src/lib/storage.ts` | `useLocalStorage`, 키 네이밍, 폴백 |
| HTTP / 캐시 | `src/lib/fetchWithCache.ts` | 메모리+`localStorage` 캐시 |
| 외부 API | `src/lib/api/*.ts` | Open-Meteo, exchangerate.host 어댑터 |
| 정적 자산 | `src/widgets/quote/quotes.ko.json` | 명언 번들 |
| 테스트 | `*.test.ts` (코로케이션) | Vitest 단위 테스트 (대상 파일 옆에 배치) |

## 진행 상태

- 현재 사이클: **M6 두 번째 사이클 — 테스트 인프라 + UI 컴포넌트 단위/
  통합 테스트(T-21)** — M6 이월 메모 7건 중 3·6·7번을 한 세션에 처리.
  대상: (1) Vitest 실행 시 발생하는 `--localstorage-file` 류 stderr 경고
  해소 — `vite.config.ts` `test` 블록의 `environmentOptions.jsdom` 또는
  관련 설정으로 jsdom 노이즈 제거, (2) `StaleIndicator` 단위 테스트 —
  `failed=true/false` × `lastUpdated=null/number` 4 조합으로 렌더 분기
  고정(`@testing-library/react`), (3) `StorageWarningBanner` 통합 테스트 —
  `isLocalStorageAvailable=false` 모킹 후 배너 렌더 + 닫기 버튼 클릭 후
  `null` 반환을 `@testing-library/react`로 검증. 본 사이클 완료 시 M6
  이월 잔여 2건(4·5번) + 빌드/preview 검증 + PRD 최종 점검이 후속.
- 직전 사이클: T-20 PASS 12/12 (2026-05-06) — lib/api/exchangerateHost
  단위 테스트 보강. `getYesterdayAndToday` 실측 검증 2케이스(2026-05-06
  noon 기본·2026-06-01 noon 월 경계) + `parseTimeseriesResponse` 빈 rates
  정책 (a) 0 폴백 유지 채택·2케이스(빈 rates·단일 날짜) 단위 테스트
  추가. 본체 무수정, 누적 79/79 통과, `npm run build` 성공. 결정 1건
  (빈 rates 정책 (a) 0 폴백 유지) IMPL.md 기록. **M6 이월 1·2번 처리
  완료.**
- 다음 사이클: T-22 (Links UI 통합 테스트 + editLink URL 정규화 저장
  정책, M6 이월 4·5번) — `@testing-library/react` 기반 LinksWidget 통합
  테스트(섹션·링크 CRUD, 중복 토스트, 편집 자기 자신 제외) + `editLink`
  가 저장 시 정규화 URL을 사용하도록 정책 변경 + 단위 테스트 고정.
  이후 T-23(빌드/preview 검증 + PRD 최종 점검 → DONE).

## M6 이월 메모 (REVIEW 권장)

> M2~M5 완료 사이클에서 도출된 minor 항목. M6 사이클에서 분할 처리한다.
> 각 항목 끝의 `→ T-NN`은 본 사이클 분할 매핑. ✅는 처리 완료.

1. ✅ `getYesterdayAndToday` 실측 검증 — 고정 `now`에 대해 실제 yesterday/
   today 문자열을 검증하는 테스트 추가. 타임존 영향이 없는 시각(예:
   12:00 로컬)을 선택해 환경 의존성 회피. (T-8 REVIEW) → **T-20 완료**
2. ✅ `parseTimeseriesResponse` 빈 rates 정책 — 현재 `rateKRW=0` silent
   폴백. (a) 0 폴백 유지를 명시 정책으로 채택, 빈 rates·단일 날짜 2케이스
   단위 테스트 고정. (T-8 REVIEW) → **T-20 완료**
3. Vitest 실행 시 `--localstorage-file` stderr 경고 해소 — `vite.config.ts`
   `test` 블록 또는 jsdom 옵션 조정. (T-4 이후 지속) → **T-21 (활성)**
4. Links UI 통합 테스트 — 중복 검사 2경로(addLink/editLink)·토스트 타이머
   정리·편집 자기 자신 제외 로직은 현재 단위 테스트 없음. M6에서
   `@testing-library/react` 기반 통합 테스트 보강. (T-13 REVIEW) → **T-22**
5. `editLink` URL 변경 감지 엣지 케이스 — `link.url`이 정규화 이전 값으로
   저장되어 같은 URL의 다른 표현 입력 시 재검증 없이 통과 가능. 저장 시
   정규화 URL 사용 정책 검토. (T-13 REVIEW) → **T-22**
6. `StorageWarningBanner` 통합 테스트 — `available=false` 조건에서 배너
   텍스트 렌더 + 닫기 버튼 클릭 후 `null` 반환 여부를 `@testing-library/
   react`로 검증. (T-17 REVIEW 권장 1번) → **T-21 (활성)**
7. `StaleIndicator` 단위 테스트 — `failed=true`/`false` × `lastUpdated
   null/number` 3~4 조합으로 분기 고정. `@testing-library/react`로 span
   렌더 여부 검증. (T-18 REVIEW 권장 1번) → **T-21 (활성)**

추가 마감 항목:
- `npm run build` 산출물 검증, `npm run preview` 동작 확인 → **T-23**
- PRD 모든 섹션이 코드/문서/테스트에 반영되었는지 최종 점검,
  신규 TASK 0건이면 `docs/DONE` 생성 → **T-23**
