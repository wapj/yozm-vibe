# TASKS

## 현재 사이클

- 마일스톤: **M6. 테스트 / 빌드 마감 — 테스트 인프라 + UI 컴포넌트
  단위/통합 테스트**
- 활성 항목: **T-21**
- 비고: T-20 PASS 12/12로 M6 이월 1·2번 처리 완료(누적 79/79, build
  성공). 본 사이클은 M6 이월 3·6·7번을 단일 사이클로 묶어 처리한다.
  세 항목 모두 `src/components/` 영역 또는 테스트 인프라(vite.config.ts)에
  국한되어 위젯/그리드/lib 본체 무수정으로 진행 가능. 신규 테스트 파일은
  `StaleIndicator.test.tsx`, `StorageWarningBanner.test.tsx` 두 개로
  코로케이션 배치(`src/components/`). stderr 경고 해소는 `vite.config.ts`
  의 `test` 블록 보강 1~3줄 수준. 본 사이클 완료 시 M6 잔여
  2건(T-22·T-23) 진행.

## 활성 항목

### [x] T-21. 테스트 인프라 + UI 컴포넌트 단위/통합 테스트 (M6 이월 3·6·7)

- 목적: M6 이월 메모 3·6·7번을 한 사이클에 처리한다.
  - (3) Vitest 실행 시 발생하는 `--localstorage-file` 류 stderr 경고를
    해소한다(T-4 도입 후 지속 노이즈). `vite.config.ts`의 `test` 블록에
    `environmentOptions.jsdom` 또는 `setupFiles` 등 jsdom 관련 옵션을
    조정해 경고를 제거하되, `--silent` 같은 우회는 사용하지 않는다.
    Generator가 실측으로 정확한 경고 문자열을 확인한 뒤 가장 단순한
    공식 옵션을 적용하고, 결정 사유를 IMPL.md에 1줄 기록.
  - (7) `StaleIndicator` 단위 테스트 — `src/components/StaleIndicator.tsx`
    의 4 분기를 `@testing-library/react`로 고정한다.
    - `failed=false` → `null` 반환(`container.firstChild === null`)
    - `failed=true, lastUpdated=null` → `갱신 실패` 텍스트만 렌더, 시각
      suffix 없음
    - `failed=true, lastUpdated=number` → `갱신 실패 · 마지막 갱신 HH:MM`
      형식으로 렌더(예: `1700000000000` 같은 고정 ts → 2자리 패딩 검증)
    - `failed=true, lastUpdated=number` 추가 케이스 — 한 자리 시/분이
      `0`으로 패딩되는지 검증(예: `09:05` 형태)
  - (6) `StorageWarningBanner` 통합 테스트 — `src/components/Storage
    WarningBanner.tsx`의 두 분기를 `@testing-library/react`로 검증한다.
    `StorageWarningBanner.tsx:5`가 모듈 상수(`available =
    isLocalStorageAvailable()`)로 1회만 호출되어 직접 stub 주입이 어려우므로
    `vi.mock('../lib/storage', () => ({ isLocalStorageAvailable: () =>
    false }))`로 모듈 모킹 후 `await import(...)` 패턴을 채택한다.
    - 미가용 분기 — `vi.mock(...false)` 상태에서 배너 텍스트
      `현재 브라우저에서 데이터 저장이 비활성화되어 있어` 렌더 검증 +
      `aria-label="배너 닫기"` 버튼 존재 검증
    - 닫기 클릭 후 `null` — 닫기 버튼 클릭 시 `container.firstChild ===
      null`로 인메모리 dismiss 검증
- 작업:
  - `src/components/StaleIndicator.test.tsx` 신규 생성 — 위 4케이스 작성.
    `import { render } from '@testing-library/react'` + `import StaleIndicator
    from './StaleIndicator'` 구조. lastUpdated 시각 검증은 `new Date(ts).
    getHours()/getMinutes()`로 expected 문자열을 동적 생성하여 타임존 의존
    회피.
  - `src/components/StorageWarningBanner.test.tsx` 신규 생성 — 2케이스 작성.
    `vi.mock` + `await import` + `fireEvent.click` 또는 `userEvent.click`
    조합. 같은 모듈 상수 캐시 영향을 받지 않도록 각 테스트에서 동적
    import.
  - `vite.config.ts` `test` 블록에 jsdom 옵션 보강(또는 `pool`/`environment
    Options` 조정)으로 stderr 경고 해소. 경고 원인이 jsdom 자체가 아니라
    Vitest CLI 옵션이라면 `package.json` `test` 스크립트는 변경하지 않고
    설정 파일에서 처리.
  - `src/components/StaleIndicator.tsx`·`StorageWarningBanner.tsx` 본체는
    변경하지 않는다(현재 동작 그대로 검증).
  - IMPL.md에 결정 사항 기록(2건 예상): (a) StorageWarningBanner 모듈
    상수 회피를 위한 `vi.mock` + 동적 import 패턴 채택 / (b) stderr 경고
    해소 방식과 사유.
- acceptance:
  - `npm test -- --run`: 누적 ≥ 85/85 통과(기존 79 + StaleIndicator 4 +
    StorageWarningBanner 2 = 신규 6). 회귀 없음.
  - `npm test -- --run` 실행 시 `--localstorage-file` 류 stderr 경고가
    출력되지 않는다(혹은 명시적으로 해소 불가 사유가 IMPL.md에 기록되고
    REVIEW가 동의).
  - `npm run build`: 성공(타입 에러 없음).
  - `src/components/StaleIndicator.tsx`·`StorageWarningBanner.tsx` 본체
    무수정.
  - `src/widgets`·`src/grid`·`src/App.tsx`·`src/lib` 무수정.
  - IMPL.md "처리 항목"에 신규 테스트 6케이스 + 결정 2건 기록.
  - REVIEW.md 사양 충족 절에 M6 이월 3·6·7번 처리 완료 기록.
- touch:
  - `dashboard/src/components/StaleIndicator.test.tsx` (신규, 4케이스)
  - `dashboard/src/components/StorageWarningBanner.test.tsx` (신규, 2케이스)
  - `dashboard/vite.config.ts` (test 블록 보강 1~3줄)
  - `dashboard/docs/IMPL.md` (처리 항목 + 결정 2건)

## 백로그 (다음 사이클 이후)

> 자세한 분해는 해당 사이클에서 한다. 여기서는 마일스톤별 후보 항목만 메모.

- T-22. Links UI 통합 테스트 + editLink URL 정규화 저장 정책 (M6 이월
  4·5) — `@testing-library/react` 기반 LinksWidget 통합 테스트(섹션·
  링크 CRUD, 중복 토스트, 편집 자기 자신 제외) + `editLink`가 저장 시
  정규화 URL을 사용하도록 정책 변경 + 단위 테스트로 고정.
- T-23. 빌드/preview 검증 + PRD 최종 점검 + DONE 판정 — `npm run build`
  산출물 정상성 확인, `npm run preview` 동작 확인. PRD 12개 섹션을
  순회하며 각 요구가 코드/문서/테스트에 반영되었는지 최종 점검.
  신규 TASK 0건이면 `docs/DONE` 빈 파일 생성.

## 완료 항목

- [x] T-20. lib/api/exchangerateHost 단위 테스트 보강 (M6 이월 1·2) —
  2026-05-06 PASS (REVIEW 12/12). `src/lib/api/exchangerateHost.test.ts`
  에 신규 4케이스 추가 — `getYesterdayAndToday` 실측 검증 2건(2026-05-06
  noon 기본 → `yesterday='2026-05-05', today='2026-05-06'`, 2026-06-01
  noon 월 경계 → `yesterday='2026-05-31', today='2026-06-01'`) +
  `parseTimeseriesResponse` 빈 rates 정책 (a) 0 폴백 유지 채택·2케이스
  (빈 rates `{rates:{}}` → `rateKRW=0/previousRateKRW=0/delta=0/direction
  ='flat'`, 단일 날짜 `{rates:{'2026-05-06':{KRW:1300}}}` → `rateKRW
  =1300/previousRateKRW=1300/delta=0/direction='flat'`). 본체 무수정,
  누적 79/79 통과(기존 75 + 신규 4), `npm run build` 성공(48 modules
  transformed). 결정 1건(빈 rates 정책 (a) 0 폴백 유지 — PRD §7 외부
  API 실패 폴백 경로가 보정) IMPL.md 기록. 감점 항목 없음. **M6 이월
  1·2번 처리 완료**, 다음은 T-21(테스트 인프라 + UI 컴포넌트 단위/
  통합 테스트, M6 이월 3·6·7).
- [x] T-19. 첫 콘텐츠 1초 내 렌더 확인 (PRD §11 성공 기준 4) —
  2026-05-06 PASS (REVIEW 11/12). 정적 코드 점검 7개를 IMPL.md
  체크리스트로 기록 + REVIEW.md 사양 충족 절에 PRD §11 4가지 성공
  기준 충족 요약. `App.tsx`/`DashboardGrid.tsx` `lazy(`/`Suspense`
  토큰 0건, Clock/Quote `useState<Date>` lazy init, Memo/Schedule/
  Links `useLocalStorage` 동기 read-on-mount, Weather/Exchange
  `snap===null` empty 슬롯, `StorageWarningBanner` 모듈 상수 캐시.
  코드 변경 0, 누적 75/75 통과, `npm run build` 성공. 결정 1건
  (Suspense/lazy 미도입 사유) IMPL.md 기록. 신규 테스트 없음
  (정적 점검 사이클 합의)으로 테스트 충실도 2점. **M5 종결.**
- [x] T-18. 공용 `StaleIndicator` 컴포넌트 추출 (Weather/Exchange 중복
  제거) — 2026-05-06 PASS (REVIEW 11/12). `src/components/StaleIndicator
  .tsx`/`.module.css` 신규(props `failed`/`lastUpdated`, 모듈 내부
  `formatHHMM` 1곳, `failed===false`→`null`, `.indicator` 클래스 1개로
  font-size 0.75rem/color #c66/font-weight 400/margin-left auto).
  `WeatherWidget.tsx`/`ExchangeWidget.tsx` 두 파일에서 인라인
  `function formatHHMM(...)` 함수 정의를 제거하고 헤더 JSX를
  `<StaleIndicator failed={failed} lastUpdated={lastUpdated} />` 한 줄로
  교체. 두 위젯 `.module.css`에서 `.staleIndicator` 클래스 정의 제거.
  `clock`/`schedule`/`memo`/`quote`/`links` · `src/grid` · `src/lib`
  무수정 확인. 누적 75/75 통과(회귀 없음, 신규 테스트 없음 — 동작 변화
  없는 순수 리팩터링), `npm run build` 성공(48 modules transformed).
  결정 2건(컴포넌트 위치 `src/components/` / 신규 테스트 부재 근거)
  IMPL.md 기록. UI 컴포넌트 단위 테스트 부재(PRD §12 합의)로 테스트
  충실도 2점. M6 권장 1건 추가(`StaleIndicator` 단위 테스트). **M5
  공용 컴포넌트 추출 완료**, 다음은 T-19(첫 콘텐츠 1초 내 렌더 확인,
  PRD §11 성공 기준 4).
- [x] T-17. `localStorage` 미지원 경고 배너 (PRD §7) — 2026-05-06 PASS
  (REVIEW 11/12). `src/lib/storage.ts`의 `isStorageAvailable`을
  `isLocalStorageAvailable`로 rename + named export, `useLocalStorage`
  내부 호출 경로 동일 함수 사용. `src/lib/index.ts`에 재노출 1줄 추가.
  `src/lib/storage.test.ts`에 `describe('isLocalStorageAvailable')` 블록
  2케이스(가용 true / setItem throw 시 false, `vi.stubGlobal` 주입). 신규
  `src/components/StorageWarningBanner.tsx`(모듈 상수 캐시로 1회 호출,
  미지원 시 `useState<boolean>(true)` 인메모리 dismiss + 닫기 버튼,
  `role="alert"` + `aria-label="배너 닫기"`) + `.module.css`(`.banner`
  flex/`#fff4d6` 배경/`#664d03` 텍스트/`border-bottom: 1px solid #ffe7a8`
  + `.text` flex 1 + `.dismiss` background none/1.1rem). `App.tsx`가
  `<StorageWarningBanner />`를 Fragment로 `<DashboardGrid />` 위에 렌더.
  누적 75/75 통과, `npm run build` 성공. 위젯 디렉터리 + `src/grid` 무수정.
  결정 2건("1회 경고" 정의 / 배너 위치 + 신규 디렉터리) IMPL.md 기록. UI
  통합 테스트 부재(PRD §12 합의)로 테스트 충실도 2점. M6 권장 1건 추가
  (`StorageWarningBanner` 통합 테스트). **M5 배너 완료**, 다음은 T-18
  (공용 `StaleIndicator` 추출).
- [x] T-1. Vite + React + TypeScript 프로젝트 초기화 — 2026-05-05 PASS
  (REVIEW 10/12). 권장사항 2건은 T-3로 흡수.
- [x] T-2. 4×2 고정 그리드 + 위젯 placeholder 7개 — 2026-05-05 PASS
  (REVIEW 9/12). PRD §3 배치 정확, CSS Modules 적용, build 통과.
  운영 고려 1점은 T-3 미해결이 원인.
- [x] T-3. 리포지토리 위생 정리(.gitignore / dist 정리) — 2026-05-05 PASS
  (REVIEW 9/12). `.gitignore` 존재 + `node_modules/`·`dist/` ignore 적중 +
  build 후 git status 깨끗. `dist/.gitkeep` 물리적 미삭제 잔재는 T-4에서
  부수 정리 시도(미이행, T-5로 이월).
- [x] T-4. Vitest 설정 (jsdom) + dist/.gitkeep 잔재 정리 — 2026-05-05 PASS
  (REVIEW 10/12). `vitest`+`jsdom`+`@testing-library/react` devDependency,
  `vitest/config` 기반 `test` 블록, `vitest/globals` 타입 보강, 스모크 테스트
  통과. `dist/.gitkeep` 물리 삭제는 IMPL 오보로 T-3·T-4 연속 미이행 →
  T-5 부수 단계로 이월.
- [x] T-5. `useLocalStorage<T>` 훅 + 키 네이밍 헬퍼 + 단위 테스트 —
  2026-05-05 PASS (REVIEW 10/12). `storageKey`·`useLocalStorage<T>` 구현
  + 11케이스 단위 테스트 + `index.ts` 재노출, `__sanity__.test.ts` 정리,
  `npm run build` 성공. `dist/.gitkeep` IMPL 오보 3사이클 연속 → T-6
  착수 조건으로 이월(REVIEW 권장).
- [x] T-6. `fetchWithCache(url, ttlMs, cacheKey)` 구현 + 단위 테스트 —
  2026-05-05 PASS (REVIEW 10/12). `fetchWithCache<T>` + `getCacheMeta`
  구현(메모리+localStorage 이중 캐시, 만료/실패 폴백 분기 4단계), 7케이스
  단위 테스트 전통과(누적 18/18), `index.ts` 재노출, `npm run build` 성공.
  `dist/.gitkeep` IMPL 오보 4사이클 연속 → T-7 착수 조건으로 이월
  (REVIEW 지시: 다음 사이클 재발 시 `docs/HALT`).
- [x] T-7. `api/openMeteo.ts` (성남 날씨 어댑터) + 단위 테스트 —
  2026-05-05 PASS (REVIEW 9/12). `SEONGNAM` 좌표 상수,
  `buildOpenMeteoUrl`·`parseOpenMeteoResponse`·`getWeather`(TTL 10분),
  `WeatherSnapshot` 7필드, 8케이스 테스트(URL 구성·매핑·daily 폴백·
  통합·캐시 적중) 전통과(누적 26/26), `index.ts` 재노출, `npm run build`
  성공. `dist/.gitkeep` 5사이클 연속 IMPL 오보(IMPL.md `ls` 출력이
  실제 파일시스템과 불일치) → 본 사이클에 `docs/HALT` 생성, 인간 개입
  요청. M2 잔여 1항목(T-8) 기술적 선행조건은 모두 충족.
- [x] T-8. `api/exchangerateHost.ts` (USD/JPY/EUR → KRW 어댑터,
  `timeseries` 기반 등락) + 단위 테스트 — 2026-05-05 PASS (REVIEW 10/12).
  `TARGET_CURRENCIES`/`BASE_CURRENCY` 상수, `buildExchangerateUrl`·
  `getYesterdayAndToday`·`computeDirection`·`parseTimeseriesResponse`·
  `getExchange`(TTL 30분, `Promise.all` 병렬 3호출), `ExchangePairSnapshot`/
  `ExchangeSnapshot` 인터페이스, 9케이스 테스트(URL 구성·날짜 헬퍼·등락 3
  케이스·응답 매핑·단일 날짜 폴백·통합·캐시 적중) 전통과(누적 35/35),
  `index.ts` 6개 심볼 재노출, `npm run build` 성공. 권장 3건(날짜 헬퍼
  실측 검증·빈 rates 정책·localstorage 경고)은 M6 이월. **M2 종결**.
- [x] T-9. `ClockWidget` 구현 (1초 갱신, `YYYY-MM-DD (요일) HH:MM:SS`)
  + 포맷터 단위 테스트 — 2026-05-05 PASS (REVIEW 12/12).
  `format.ts`(`formatDateLine`/`formatTimeLine` 순수 함수) +
  `format.test.ts`(6케이스 + 요일 7 assert) + `ClockWidget.tsx`
  (`useState<Date>` lazy init + 1초 `setInterval` + `clearInterval`
  cleanup) + `ClockWidget.module.css`(`.date`/`.time` 추가, monospace).
  누적 41/41 통과, `npm run build` 성공. 감점 항목 없음. **M3 Clock 완료**.
- [x] T-10. `QuoteWidget` 구현 (정적 JSON + 날짜→인덱스 매핑, 자정 회전)
  + 인덱스 매핑 단위 테스트 — 2026-05-05 PASS (REVIEW 12/12).
  `quotes.ko.json`(35개 퍼블릭 도메인 한국어 명언, 속담 19/공자 6/노자 3/
  손자 1/작자 미상 6) + `dateIndex.ts`(`computeQuoteIndex(date,total) =
  (YYYY*10000+MM*100+DD) % total`, `total<=0`이면 `0`) +
  `dateIndex.test.ts`(5케이스 — 기본 매핑·인접 일자·`total=1`·`total<=0`
  방어·연도 경계) + `QuoteWidget.tsx`(JSON import + `useState<Date>` lazy
  init + 60초 `setInterval` + 동일 날짜면 prev 참조 유지 + `clearInterval`
  cleanup) + `QuoteWidget.module.css`(`.text`/`.author` 추가) +
  `tsconfig.app.json`(`resolveJsonModule: true` 추가). 누적 46/46 통과,
  `npm run build` 성공. 감점 항목 없음. **M3 Quote 완료**.
- [x] T-11. `MemoWidget` 구현 (`useLocalStorage<MemoItem[]>` CRUD + 정렬 +
  빈 입력 차단) + 정렬 단위 테스트 — 2026-05-06 PASS (REVIEW 12/12).
  `types.ts`(`MemoItem` 4필드: id/text/done/createdAt) + `sort.ts`
  (`sortMemos` 순수 함수 — 미완료 최신 위 → 완료 하단, `[...items].sort`로
  불변 반환) + `sort.test.ts`(5케이스 — 빈 배열·전부 미완료·전부 완료·
  혼합·불변성) + `MemoWidget.tsx`(`useLocalStorage<MemoItem[]>` 영속화 +
  추가/삭제/완료 토글 + 빈 입력 인라인 에러 + 렌더 시점 `sortMemos` 재
  적용 + `crypto.randomUUID` 폴백 `${Date.now()}-${random36}`) +
  `MemoWidget.module.css`(`.form`/`.input`/`.error`/`.list`/`.item`/
  `.done`/`.deleteBtn`). 누적 51/51 통과, `npm run build` 성공. 감점
  항목 없음. **M3 Memo 완료**.
- [x] T-12. `normalizeUrl` 순수 함수 + `LinkItem`/`LinkSection` 타입 +
  정규화 단위 테스트 — 2026-05-06 PASS (REVIEW 12/12). `types.ts`
  (`LinkItem` id/title/url + `LinkSection` sectionId/name/links) +
  `normalize.ts`(`normalizeUrl(input)` 순수 함수, import 구문 0 — trim
  → `new URL` → `protocol.toLowerCase()` + `host.toLowerCase()` →
  path 끝 슬래시 제거(`/` 단독은 빈 문자열) → search/hash 보존, 잘못된
  입력은 `new URL` TypeError throw 위임) + `normalize.test.ts`(9케이스
  — 호스트 소문자/스킴 소문자/끝슬래시 제거(path)/루트 슬래시/쿼리
  보존/해시 보존/조합/공백 트림/throw). 누적 60/60 통과, `npm run build`
  성공. `LinksWidget.tsx`/`.module.css` 무수정 확인. 감점 항목 없음.
  **M3 Links 정규화 완료**, 다음은 T-13(LinksWidget CRUD UI).
- [x] T-13. `LinksWidget` CRUD UI (섹션·링크 + 중복 차단 토스트 + 잘못된
  URL 인라인 차단) — 2026-05-06 PASS (REVIEW 11/12). `LinksWidget.tsx`
  (placeholder → CRUD UI 전체) + `LinksWidget.module.css`(position:relative
  + 신규 클래스 11개). PRD §4.5 6개 작업(섹션 추가/이름변경/삭제 + 링크
  추가/편집/삭제) 통합 + 같은 섹션 정규화 URL 중복 차단 토스트(3000ms
  자동 소멸, `useRef<number|null>` + `clearTimeout`) + 빈 제목/잘못된
  URL 인라인 에러 + `useLocalStorage<LinkSection[]>('dashboard.links.
  sections', [])` 영속화 + `normalizeUrl` 3위치 호출(추가 검증/중복 검사
  /편집 검증) + `crypto.randomUUID` 폴백 + `rel="noreferrer"`. 결정 3건
  (window.prompt 사용/3000ms/같은 이름 섹션 허용) IMPL.md 기록. 60/60
  통과, build 성공. UI 상호작용 단위 테스트 부재(PRD §12 합의 계획 결정)
  로 테스트 충실도 2점. M6 이월 메모 4·5번에 권장 2건 추가. **M3 Links
  CRUD UI 완료**, 다음은 T-14(Schedule).
- [x] T-15. `WeatherWidget` 구현 (10분 폴링 + 캐시 폴백 + "갱신 실패"
  인디케이터) + WMO 코드 매핑 단위 테스트 — 2026-05-06 PASS (REVIEW 12/12).
  `weatherCode.ts`(WMO 7그룹 + 폴백 매핑 순수 함수 `describeWeather`,
  import 0) + `weatherCode.test.ts`(6케이스 — 맑음 0/대체로맑음·흐림 1·2·3
  서로 다른 라벨/이슬비비 51·63 `includes('비')`/눈 71 `includes('눈')`/
  뇌우 95 `includes('뇌우')`/알수없는코드 999 `❓ 알 수 없음` 폴백) +
  `WeatherWidget.tsx`(placeholder → 본체: `useState<WeatherSnapshot|null>` +
  `useState<boolean>` failed + `useState<number|null>` lastUpdated +
  `useRef<ReturnType<typeof setInterval>|null>` timerRef + `loadOnce`
  async try/catch + 마운트 1회 + `setInterval(loadOnce, 10*60*1000)` +
  `clearInterval` cleanup + 인라인 `formatHHMM` + 헤더(title +
  staleIndicator) + empty/메인(이모지·기온·체감)/설명/메타(최고·최저·강수)
  슬롯 + `CACHE_KEY = \`weather.${SEONGNAM.latitude}.${SEONGNAM.longitude}\``
  ) + `WeatherWidget.module.css`(`.header`/`.staleIndicator`/`.empty`/`.main`/
  `.feelsLike`/`.description`/`.meta` 보강). 결정 3건(WMO 7그룹 단순화·
  `lastUpdated` 위젯 자체 상태로 단일 경로 관리·`useRef` interval ID 보관)
  IMPL.md 기록. 누적 73/73 통과, `npm run build` 성공. 감점 항목 없음.
  **M4 Weather UI 완료**, 다음은 T-16(Exchange UI).
- [x] T-14. `ScheduleWidget` 구현 (오늘 일정 필터 + 시각 정렬 + 5분 폴링)
  + 필터 단위 테스트 — 2026-05-06 PASS (REVIEW 12/12).
  `types.ts`(`ScheduleItem` 5필드: id/date/time/title/done) +
  `filter.ts`(`formatToday`/`filterToday`/`sortByTime` 순수 함수, import
  구문 0 — 로컬 `Item` 인터페이스로 자체 완결, TypeScript 구조적 타이핑
  으로 `ScheduleItem` 호환) + `filter.test.ts`(7케이스 — formatToday 기본/
  zero-pad·filterToday 기본/빈 배열·sortByTime 오름차순/null 후위/불변성)
  + `ScheduleWidget.tsx`(placeholder → 본체: `useLocalStorage<ScheduleItem
  []>('dashboard.schedule.items', [])` 영속화 + 추가/삭제/완료 토글 + 빈
  제목 인라인 에러 + 5분 `setInterval` polled-read[`window.localStorage.
  getItem(KEY)` + `setItems(ext)`] + `clearInterval` cleanup + 시각
  미지정 일정은 `time: null` 저장 + `crypto.randomUUID` 폴백) +
  `ScheduleWidget.module.css`(form/input/list/item/time/deleteBtn 등
  보강). 결정 2건(time null 저장 / 직접 polled-read 채택) IMPL.md 기록.
  누적 67/67 통과, `npm run build` 성공. 감점 항목 없음.
  **M3 Schedule 완료, M3 로컬 데이터 위젯 전 항목(Clock/Quote/Memo/
  Links/Schedule) 종결.** 다음은 T-15(Weather UI).
- [x] T-16. `ExchangeWidget` 구현 (USD/JPY/EUR → KRW, 30분 폴링 + 캐시
  폴백 + 등락 ↑/↓ + "갱신 실패" 인디케이터) — 2026-05-06 PASS
  (REVIEW 11/12). `ExchangeWidget.tsx`(placeholder → 본체:
  `useState<ExchangeSnapshot|null>` snap + `useState<boolean>` failed +
  `useState<number|null>` lastUpdated + `useRef<ReturnType<typeof
  setInterval>|null>` timerRef + `loadOnce` async try/catch + 마운트
  1회 + `setInterval(loadOnce, 30*60*1000)` + `clearInterval` cleanup +
  인라인 `formatHHMM`/`arrowFor`/`formatRate` 헬퍼 + 헤더(title +
  staleIndicator) + empty 슬롯 + `snap.pairs.map`로 USD/JPY/EUR 3행
  (`base`/`rateKRW.toFixed(2)`/등락 ▲/▼/–·`Math.abs(delta).toFixed(2)`) +
  `META_KEY = 'exchange.USD.KRW'`로 `getCacheMeta` 호출) +
  `ExchangeWidget.module.css`(`.header`/`.staleIndicator`/`.empty`/
  `.list`/`.row`/`.base`/`.rate`/`.dir_up`(#c33)/`.dir_down`(#3a3)/
  `.dir_flat`(#888) 보강). 결정 3건(USD 캐시 키 메타 단일 대표·소수
  2자리 통일·한국 금융 관행 등락 색) IMPL.md 기록. 누적 73/73 통과,
  `npm run build` 성공. 신규 테스트 없음(PRD §12 합의)으로 테스트
  충실도 2점. **M4 Exchange UI 완료, M4 종결.** 다음은 T-17(M5).
