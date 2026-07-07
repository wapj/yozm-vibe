# Anthropic이 개발자 호감을 잃는 몇 가지 방법

- 원문: [https://news.hada.io/topic?id=31201](https://news.hada.io/topic?id=31201)
- 발행일: 2026-07-07
- 피드: GeekNews - 개발/기술/스타트업 뉴스 서비스

## 요약

Anthropic이 Claude 구독의 사용처를 자사 도구(Claude Code CLI/Desktop, Claude CoWork, Slack의 @Claude)로 제한하고 제3자 에이전트 하네스 사용에 별도 과금을 적용하려 하면서 개발자 커뮤니티의 반발을 사고 있다는 비판 글입니다. 2026년 6월 15일 예정이었던 과금 변경은 구독 한도와 별개의 Agent SDK 크레딧을 두고 초과분을 API 요금으로 청구하는 구조였으나, 소비자 반발 이후 일시 중지된 상태입니다. 글쓴이는 Claude Code의 품질 문제(약 9,100개의 GitHub 이슈, 장기 미해결 버그)와 락인 전략을 동시에 지적하며, Qwen·GLM·Deepseek 같은 오픈소스 모델과 OpenRouter 등 AI 게이트웨이 기반의 개방적 워크플로로 전환할 것을 제안합니다. Hacker News 토론에서는 "자사 도구 사용 시 토큰을 보조하는 것은 공정한 교환"이라는 옹호론과 "종속을 유도하는 설계"라는 비판론이 맞섰습니다.

## 핵심 포인트

- **구독 락인 구조**: Claude 구독은 Anthropic 1차 도구에서만 사용 가능하고, Vertex AI·AWS Bedrock·Azure 경로는 더 비싼 API 크레딧이 필요합니다.
- **과금 변경 시도와 철회**: 2026년 6월 15일부터 제3자 에이전트/SDK 사용을 별도 크레딧 풀(Pro $20, Max 5x $100, Max 20x $200)로 분리하고 초과분을 API 요금으로 청구하려 했으나, 반발 이후 "일시 중지"되었습니다. 기존 구독은 API 가격 대비 약 15~30배 수준으로 에이전트 사용을 보조하던 구조였습니다.
- **품질 논란**: Claude Code CLI에는 약 9,100개의 GitHub 이슈가 열려 있으며, 완전 중단 문제는 6개월 이상, 화면 깜빡임 문제는 1년 이상 미해결 상태입니다.
- **감지 방식 논란**: 세션 디렉터리의 특정 파일 존재 여부로 제3자 도구 사용을 추정해 extra usage를 부과한 사례가 비판받았습니다.
- **대안 제시**: 글쓴이는 자동완성 중심의 agent-assisted development로 회귀했으며, Qwen·GLM(오케스트레이션), Deepseek(검색), Minimax(파일 편집) 조합과 OpenRouter·Requesty·Portkey·Vercel 같은 AI 게이트웨이를 통한 라우팅을 권장합니다.
- **커뮤니티 반응**: 통신사 보조금 비유로 정책을 옹호하는 의견과, `claude -p` 같은 자사 도구 호출까지 제3자 사용으로 재분류한 점·사전 공지 없는 조건 변경을 비윤리적이라고 보는 의견이 갈렸습니다. 일부 사용자는 이미 Pi, OpenCode, Codex 등으로 이전을 진행 중입니다.
