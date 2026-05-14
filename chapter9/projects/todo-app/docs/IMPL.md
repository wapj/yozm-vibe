# IMPL — M5-1b: App.tsx에 useNotification 통합 + 만료 시점 notify 발화 + 토스트 마운트

## 처리 항목

**M5-1b** — App.tsx에 `useNotification` 훅 연결, 만료 시점 `notify` 호출, `<Toast>` 다중 마운트

## 변경 파일

### `frontend/src/App.tsx`
1. `useRef` React import 추가
2. `import { useNotification } from "./hooks/useNotification"` 추가
3. `import { Toast } from "./components/Toast"` 추가
4. 컴포넌트 최상단에 `const { notify, requestPermission } = useNotification()` 호출
5. `const [toasts, setToasts] = useState<{ id: number; message: string }[]>([])` 상태 추가
6. `const toastIdRef = useRef(0)` 추가
7. `showToast(message)` / `removeToast(id)` 헬퍼 추가 (toastIdRef 카운터 사용)
8. `useEffect(() => { requestPermission(); }, [])` 마운트 시 1회 권한 요청
9. 마운트 복원 만료 분기(getActivePomodoro useEffect)에 `notify(title, body, showToast)` 삽입 — endPomodoro 호출 전
10. `handlePomodoroExpire` 진입 직후 `notify(title, body, showToast)` 삽입 — endPomodoro 호출 전
11. JSX 마지막에 `data-testid="toast-container"` div 추가 (position: fixed, top/right 16, flex-column)

### `frontend/tests/App.test.tsx`
- `beforeEach`에 `vi.unstubAllGlobals()` 추가 (Notification 전역 mock 격리)
- 신규 테스트 4건 추가:
  1. 마운트 시 `requestPermission` 1회 호출
  2. focus 만료 → permission granted → `new Notification` 1회 + 토스트 미노출
  3. break 만료 → permission granted → `new Notification` 1회 + NextFocusPromptDialog 동시 노출
  4. focus 만료 → permission denied → 토스트 폴백 노출 + Notification 미생성

## 자체 결정 사항

- **id 발급 방식**: `useRef(0)` 카운터 사용 — fake timer 환경에서 `Date.now()` 충돌 회피
- **notify 호출 위치**: `endPomodoro` 호출 전 — API 실패 시에도 사용자가 만료를 인지하도록
- **ESLint 예외**: requestPermission/notify/showToast를 useEffect 의존성 배열에서 제외 (각각 stable ref 또는 1회 실행 의도)
- **toast 문구**: fallback 시 body(`"task #${task_id}"`)만 표시
- **MockNotification 패턴**: `vi.fn().mockImplementation` + 타입 캐스팅으로 static 프로퍼티 추가

## 검증 결과

- 프론트엔드: **79 passed, 0 failed** (기존 75 + 신규 4)
- 백엔드: **71 passed, 0 failed** (변경 없음)
- 타입 체크: 신규 에러 0건 (기존 11건 유지)
