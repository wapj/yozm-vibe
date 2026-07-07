# Show GN: Jetendard 폰트 (JetBrains Mono Nerd Font + Pretendard)

- 원문: [https://news.hada.io/topic?id=31174](https://news.hada.io/topic?id=31174)
- 발행일: 2026-07-06
- 피드: GeekNews - 개발/기술/스타트업 뉴스 서비스

## 요약

Jetendard는 JetBrains Mono Nerd Font와 Pretendard를 결합한 코딩용 고정폭 폰트입니다. 여밀 폰트의 소스코드를 기반으로 하되, Geist Mono 대신 JetBrains Mono Nerd Font Mono를 사용한 점이 다릅니다. 코딩용 폰트에 한글이 없으면 fallback 처리로 box-drawing 문자가 밀리고, 한글을 포함하면 영문 2자 대비 한글 1자가 작아 불필요한 공백이 생겨 가독성이 떨어지는 상충 문제를 해결하고자 제작되었습니다. 한글 글리프의 스케일을 키워 자간 공백을 줄이는 방식으로 두 문제를 절충했으며, 그 결과 띄어쓰기 구분이 명확해지고 한글이 더 선명하게 표시됩니다.

## 핵심 포인트

- **구성**: JetBrains Mono Nerd Font(영문) + Pretendard(한글), 여밀 폰트 소스코드 기반
- **문제 1**: 코딩용 고정폭 폰트에 한글이 없으면 fallback 문자 대체로 Unicode box-drawing 문자의 정렬이 어긋남
- **문제 2**: 한글 폰트를 포함하면 영문 2자보다 한글 1자가 현저히 작아 글자 주변 공백이 띄어쓰기와 혼동되어 읽기 피로도가 증가함
- **해결 방식**: 한글 스케일을 확대해 버려지는 공백 공간을 글자로 채움 — 한글이 다소 커 보이지만 띄어쓰기 구분과 선명도가 개선됨
- **댓글 반응**: 기존에는 구름 산스 코드를 폴백으로 두는 방식(영:한 1:1.5)을 사용했으나, 폴백 설정이 불가능하거나 1:2 문자폭이 필요한 환경에서 이 폰트가 유용하다는 긍정적 평가
