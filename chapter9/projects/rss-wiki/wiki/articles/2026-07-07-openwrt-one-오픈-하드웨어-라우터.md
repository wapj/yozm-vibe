# OpenWrt One – 오픈 하드웨어 라우터

- 원문: [https://news.hada.io/topic?id=31193](https://news.hada.io/topic?id=31193)
- 발행일: 2026-07-07
- 피드: GeekNews - 개발/기술/스타트업 뉴스 서비스

## 요약

OpenWrt One은 OpenWrt 프로젝트가 내놓은 오픈 하드웨어 라우터로, MediaTek Filogic 820 SoC에 WiFi 6, 2.5Gbit WAN, 1GB RAM을 탑재하고 OpenWrt 릴리스 펌웨어와 LuCI GUI가 설치된 상태로 출고됩니다. 가장 큰 특징은 복구 체계입니다. USB 업그레이드, initramfs 기반 NAND 복구, NOR 전체 복구가 단계적으로 제공되며, NAND가 손상되어도 16MiB 복구용 NOR로 재플래시할 수 있고, NOR 자체가 손상된 경우에도 UART 부팅과 TFTP 서버, WP 점퍼 작업으로 복원이 가능합니다. 내장 USB-C 시리얼 콘솔까지 갖춰 펌웨어 실험 중 부트로더가 손상되어도 복구 여지가 남아 있어, 실사용 라우터와 개발·복구 장비 역할을 동시에 노립니다. 가격은 케이스·안테나 포함 약 106달러이며, Hacker News 반응은 대체로 긍정적이고 WiFi 7을 지원하는 OpenWrt Two도 개발 중입니다.

## 핵심 포인트

- **하드웨어**: MediaTek Filogic 820, WiFi 6 듀얼밴드(3×3/2×2), 2.5Gbit WAN + 1Gbit LAN, 1GB DDR4, 256MiB NAND + 복구용 16MiB NOR, M.2 SSD 슬롯, PoE(802.3af/at) 지원
- **출고 상태**: 최신 OpenWrt 릴리스 펌웨어와 LuCI GUI가 설치되어 있어 `192.168.1.1`로 웹 UI 또는 SSH 접속이 바로 가능
- **다층 복구 구조**: USB 기반 sysupgrade → initramfs NAND 복구 모드 → NOR 전체 복구 순으로 복구 수단이 제공되며, 부팅 스위치와 버튼 조합으로 경로를 선택
- **NOR 자체 복구**: `mtk_uartboot`를 이용한 UART 부팅과 TFTP 플래싱으로 가능하나, NOR WP 점퍼 장착과 수동 네트워크 설정(192.168.11.x 대역)이 필요
- **시리얼 콘솔 내장**: USB-C 포트에 USB-to-serial 변환기가 통합되어 있어 별도 드라이버 없이 유지보수·복구 작업이 가능
- **커뮤니티 반응**: 완전 지원 하드웨어라는 점과 가격(84~106달러)에 만족하는 사용자가 많으며, 일부는 OPNSense + 별도 AP 조합이나 x86 미니 PC를 대안으로 제시. WRT라는 이름이 25년 전 Linksys WRT54G 대체 펌웨어에서 유래했다는 점도 화제
