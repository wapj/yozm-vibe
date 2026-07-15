# no-mistakes - git push 할 때 실수를 방지하기

- 원문: [https://news.hada.io/topic?id=31223](https://news.hada.io/topic?id=31223)
- 발행일: 2026-07-08
- 피드: GeekNews - 개발/기술/스타트업 뉴스 서비스

## 요약

`no-mistakes`는 `git push` 과정에서 발생하는 실수를 방지하기 위해 실제 remote 앞에 로컬 Git 프록시를 두는 도구입니다. `origin` 대신 `no-mistakes`로 push하면 일회용 worktree에서 AI 기반 검증 파이프라인(review → test → docs → lint → push → PR → CI)이 실행되고, 모든 검사를 통과한 경우에만 브랜치가 실제 push 대상에 전달되어 PR이 자동으로 생성됩니다. 검증은 격리된 worktree에서 논블로킹으로 실행되므로 진행 중인 작업을 방해하지 않으며, 안전한 기계적 수정은 자동 적용되고 의도 판단이 필요한 항목만 사용자에게 에스컬레이션됩니다. `claude`, `codex`, `copilot` 등 여러 코딩 에이전트를 지원하는 에이전트 비종속 구조이며, MIT 라이선스로 공개되어 있습니다.

## 핵심 포인트

- **동작 원리**: 실제 remote 앞에 로컬 Git 프록시를 배치하고, push 시 일회용 worktree에서 검증 파이프라인을 실행합니다. 모든 검사가 통과하기 전까지는 어떤 것도 push 대상에 도달하지 않습니다.
- **검증 파이프라인**: review → test → docs → lint → push → PR → CI 순서로 진행되며, 각 단계는 통과하거나 사용자가 처리해야 할 finding과 함께 중단됩니다.
- **논블로킹 구조**: 검증이 격리된 worktree에서 실행되어 진행 중인 작업에 영향을 주지 않습니다.
- **자동 수정과 에스컬레이션**: 안전한 기계적 수정은 자동 적용하고, 의도 판단이 필요한 항목만 approve / fix / skip 방식으로 사용자에게 확인을 요청합니다.
- **에이전트 비종속**: `claude`, `codex`, `opencode`, `pi`, `copilot` 등을 지원하며 순서 지정 폴백을 제공합니다.
- **세 가지 실행 방식**: `git push no-mistakes`(명시적 Git 경로), `no-mistakes`(TUI 마법사, `-y`로 자동 수행), `/no-mistakes`(에이전트 skill, 비대화형 TOON 인터페이스)를 지원합니다.
- **자동 PR 생성**: 검사 통과 시 게이트가 브랜치를 전달하고 PR을 열어주므로 수동 `git push origin`이나 PR 본문 작성이 필요 없습니다.
