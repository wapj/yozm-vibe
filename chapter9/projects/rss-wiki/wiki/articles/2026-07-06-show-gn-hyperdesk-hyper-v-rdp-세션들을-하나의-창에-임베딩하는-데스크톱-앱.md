# Show GN: HyperDesk - Hyper-V/RDP 세션들을 하나의 창에 임베딩하는 데스크톱 앱

- 원문 링크: https://news.hada.io/topic?id=31180
- 발행일: 2026-07-06
- 피드: GeekNews - 개발/기술/스타트업 뉴스 서비스

## 요약

HyperDesk는 Hyper-V(VMConnect)와 RDP 세션을 하나의 데스크톱 앱 안에 임베딩하는 Windows 전용 도구입니다. 개발자가 회사 유지보수 업무 중 고객사별 원격 데스크톱, 개발 환경 VM, VDI 등 여러 창을 오가는 불편을 해소하기 위해 사이드 프로젝트로 제작했습니다. 미리보기나 탭 방식이 아니라 `SetParent` 기반 Win32 Window Swallowing으로 실제 세션 창을 앱 내부에 흡수하며, 최대 4개 세션을 단축키(Alt+1~4)로 즉시 전환할 수 있습니다. Tauri v2, Rust, React 19 스택으로 구현되었으며, 제작자는 Window Swallowing 방식의 한계와 실무 안정성에 대한 피드백을 요청하고 있습니다.

## 핵심 포인트

- **동작 방식**: Hyper-V/RDP 세션 창을 `SetParent`로 앱 내부에 직접 임베딩하는 Win32 Window Swallowing 방식
- **세션 전환**: 활성 세션 하나를 전체 화면으로 표시하고, Alt+1~4 또는 헤더 탭으로 최대 4개 세션을 즉시 전환. 백그라운드 세션은 연결이 유지됨
- **키보드 라우팅**: 활성 세션에 포커스가 있으면 Win 키, Alt+Tab 같은 시스템 단축키가 VM 내부로 전달됨
- **안정성 처리**: `AttachThreadInput` 대신 독립 메시지 큐를 구성해 외부 클라이언트의 인증 모달로 인한 UI 데드락을 방지하고, 리사이즈 시 `requestAnimationFrame`과 백엔드 델타 필터링으로 임베딩 창 위치를 추적
- **부가 기능**: 스냅샷, 원격 자산별 별명/메모, 커맨드 팔레트, RDP 및 Hyper-V On/Off
- **기술 스택 및 제약**: Tauri v2 + Rust + React 19, Windows 전용. VMware/Omnissa Horizon은 실사용 검증이 되지 않았고, Omnissa는 대시보드 형태라 임베딩이 비활성 상태
