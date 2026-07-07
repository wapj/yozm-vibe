# GPT-5.6 Sol Ultra는 Codex에 탑재될 것임

- 원문: [https://news.hada.io/topic?id=31195](https://news.hada.io/topic?id=31195)
- 발행일: 2026-07-07
- 피드: GeekNews - 개발/기술/스타트업 뉴스 서비스

요약은 단일 처리로 충분한 작업이므로 워크플로 없이 바로 작성합니다.

## 요약

OpenAI의 Codex 담당자 Tibo가 트위터에서 GPT-5.6 Sol Ultra를 Codex에 탑재할 것이라고 밝혔습니다. GPT-5.5 Pro가 Codex에서 제외된 것에 대한 지적에 답하는 과정에서 나온 발언으로, 질문자는 Codex의 넉넉한 사용량 한도를 근거로 Claude Max 20x 플랜을 결제할 이유가 없다고 주장했습니다. Hacker News에서는 Ultra 모드의 실체(별도 백엔드 구현이 아니라 max effort 설정에 subagent 활용 프롬프트를 더한 수준이라는 분석), Claude Code의 동적 워크플로와의 비교, 기업의 AI 토큰 비용 급증 문제 등이 함께 논의되었습니다. 최상위 모델을 구독 요금제에 포함할지 여부가 Anthropic과 OpenAI 간 이용자 이동의 관건이 될 것이라는 반응도 다수였습니다.

## 핵심 포인트

- **Ultra의 Codex 탑재 확정**: Codex 담당 Tibo가 "Ultra will be in codex"라고 언급하여 GPT-5.6 Sol Ultra의 Codex 탑재를 예고했습니다.
- **Ultra 모드의 실체 논쟁**: Codex 소스 기준으로 Ultra는 별도의 백엔드 기능이 아니라 max effort 설정의 별칭에 subagent 활용을 권장하는 프롬프트를 추가한 정도라는 분석이 제기되었습니다. 반면 Claude Code의 ultracode는 JavaScript 오케스트레이션 스크립트를 동적으로 생성해 subagent를 결정적으로 제어한다는 점에서 차이가 있다는 반론도 있었습니다.
- **Pro와 Ultra의 차이**: Pro는 에이전트들이 독립 작업 후 결과를 병합하는 방식이고, 새 Ultra 모드는 subagent들이 중간에 서로 통신하며 협력하도록 훈련된 방식으로 보인다는 설명이 있었습니다.
- **기업 비용 문제**: 토큰 사용량을 장려하던 기업들이 최근에는 더 저렴한 모델 사용을 권고하는 방향으로 선회하고 있으며, 보조금이 반영된 현재 가격이 지속 불가능하다는 우려가 나왔습니다.
- **추론 비용 절감 소식**: The Information에 따르면 OpenAI가 추론 비용을 절반으로 줄이는 방법을 찾았다는 보도가 있으며, 이러한 효율 최적화(compute multiplier)를 각 연구소가 영업비밀로 취급하는 관행에 대한 비판도 제기되었습니다.
- **구독 요금제 경쟁**: 최고 모델을 구독 등급에 포함하는지가 사용자 이탈·유입의 핵심 변수로 지목되었으며, Anthropic이 Fable 모델의 제공을 확대하도록 압박이 되기를 바라는 의견이 있었습니다.
