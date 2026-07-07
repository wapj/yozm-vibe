# Fable이 reMarkable을 Harry Potter의 Tom Riddle 일기장으로 바꿈

- 원문: [https://news.hada.io/topic?id=31208](https://news.hada.io/topic?id=31208)
- 발행일: 2026-07-07
- 피드: GeekNews - 개발/기술/스타트업 뉴스 서비스

## 요약

riddle은 reMarkable Paper Pro 태블릿을 해리 포터의 Tom Riddle 일기장처럼 만들어주는 오픈소스 앱입니다. 펜으로 글을 쓰고 2.8초간 멈추면 페이지가 PNG로 변환되어 비전 LLM에 전달되고, 답변이 손글씨 획 애니메이션으로 페이지에 나타났다가 사라집니다. 화면 빛이나 키보드, 채팅 UI 없이 "종이에 잉크가 스며드는" 경험을 목표로 하며, Rust로 작성된 본체와 C/C++ 기반 takeover 디스플레이 호스트(quill)로 구성됩니다. 다만 기기를 root 권한으로 수정하고 vendor UI를 중지하는 방식이라 지원 범위가 좁고, 모든 위험은 사용자가 감수해야 합니다. Hacker News에서는 기술적 완성도에 대한 감탄과 함께 "저주받은 유물"에 비유한 점의 아이러니, AI 챗봇의 안전 문제에 대한 논쟁이 오갔습니다.

## 핵심 포인트

- **동작 방식**: raw evdev로 펜 입력을 받아 2.8초 유휴 시 페이지를 PNG로 커밋 → 비전 LLM(oracle 프로세스)이 손글씨를 읽고 문장 단위로 스트리밍 → Dancing Script 폰트를 Zhang-Suen thinning으로 단일 픽셀 펜 경로로 변환해 획 단위 애니메이션으로 답변을 표시합니다.
- **두 가지 표시 백엔드**: xochitl 내부에서 창 모드로 동작하는 `qtfb`와, vendor UI를 중지하고 e-ink 엔진을 직접 구동하는 full takeover 모드 `quill`이 있습니다.
- **설치**: `remagic install riddle`이 가장 간단하며, 사전 빌드 번들이나 소스 빌드도 가능합니다. 개발자 모드와 런처(xovi + AppLoad)가 선행 조건입니다.
- **LLM 백엔드**: OpenAI 호환 `/chat/completions` API(기본 모델 `gpt-4o-mini`) 또는 상주형 `pi --mode rpc` 프로세스를 선택할 수 있고, 기기에서 첫 잉크까지 약 0.9~1.1초가 걸립니다.
- **제스처**: 펜을 쉬면 답변 시작, 마커 뒤집기는 지우개, 큰 `?`는 가이드 호출, 다섯 손가락 탭은 종료, 전원 버튼은 suspend입니다.
- **제약과 위험**: 테스트 환경은 reMarkable Paper Pro(ferrari, aarch64, OS 3.26~3.27)로 한정되며, root 실행과 기기 수정이 필요하므로 복구를 위해 SSH 접근을 반드시 확보해야 합니다. 코드는 MIT, 폰트는 SIL OFL 1.1 라이선스이고 vendor 라이브러리는 사용자가 직접 준비해야 합니다.
- **커뮤니티 반응**: "결국 채팅 UI 아니냐"는 지적, 저주받은 유물 비유의 적절성 논쟁, 완전 로컬 모델이었다면 더 인상적이었을 것이라는 의견, 그리고 AI 챗봇 관련 사망 사례를 둘러싼 안전성 논의가 있었습니다.
