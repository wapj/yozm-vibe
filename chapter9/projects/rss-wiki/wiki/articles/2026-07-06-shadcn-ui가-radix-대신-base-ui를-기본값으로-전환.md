# Shadcn/UI가 Radix 대신 Base UI를 기본값으로 전환

- 원문: [https://news.hada.io/topic?id=31163](https://news.hada.io/topic?id=31163)
- 발행일: 2026-07-06
- 피드: GeekNews - 개발/기술/스타트업 뉴스 서비스

## 요약

shadcn/ui가 2026년 7월부터 새 프로젝트의 기본 컴포넌트 라이브러리를 Radix에서 Base UI로 전환했습니다. Base UI는 Radix 제작진이 새로 개발한 헤드리스 라이브러리로, 1.6.0 안정 버전과 주간 600만 회 이상의 다운로드를 기록했으며, shadcn/create에서 Radix보다 2:1 비율로 더 많이 선택되는 흐름을 공식 기본값에 반영한 것입니다. Radix는 지원 중단되지 않으며 기존 앱은 마이그레이션 없이 유지할 수 있고, 원할 경우 codemod 대신 에이전트 skill 방식으로 컴포넌트 단위 점진 이전이 가능합니다. 이번 발표에는 채팅 UI 컴포넌트, GitHub 저장소 registry, `shadcn eject`, 새 스타일 Rhea 등도 포함되어 shadcn/ui의 범위가 제품 UI 구성 전반으로 확장되었습니다.

## 핵심 포인트

- **기본값 전환**: `npx shadcn init`과 shadcn/create에서 Base UI가 기본 선택지가 되고, 문서도 Base UI 탭을 기본으로 표시합니다. Radix를 유지하려면 `-b radix` 플래그를 사용하면 됩니다.
- **Radix 지원 유지**: Base UI 전용 컴포넌트를 제외한 모든 업데이트와 새 컴포넌트는 두 라이브러리 모두에 제공되며, shadcn/ui 자체 프로젝트도 Radix를 계속 사용합니다.
- **skill 기반 마이그레이션**: 사용자가 수정한 컴포넌트에서 codemod가 실패할 수 있어, 에이전트가 변경 사항을 파악해 점진 이전하는 skill 방식을 채택했습니다. 실행마다 타입체크·빌드 검증, `.migration/` 리포트, 컴포넌트당 1커밋의 git 이력을 남깁니다. 실제 테스트에서는 Radix 컴포넌트 36개를 약 25분에 이전했습니다.
- **채팅 UI 컴포넌트 추가**: MessageScroller, Message, Bubble, Attachment, Marker와 `scroll-fade`·`shimmer` CSS 유틸리티가 추가되었고, 헤드리스 로직은 새 패키지 `@shadcn/react`로 분리되어 Radix와 Base UI 양쪽에서 사용 가능합니다. AI Elements를 대체하지는 않습니다.
- **생태계 확장**: 공개 GitHub 저장소를 빌드·배포 없이 registry로 사용할 수 있게 되었고, `shadcn` 패키지 의존을 제거하는 `shadcn eject`, Luma보다 조밀한 새 스타일 Rhea가 추가되었습니다.
- **커뮤니티 반응**: Hacker News에서는 발표 글의 AI 작성 문체 논란, 복사·붙여넣기 방식 대 전통적 UI 라이브러리(Mantine 등) 비교, codemod에서 LLM 기반 마이그레이션으로의 전환에 대한 논의가 오갔습니다.
