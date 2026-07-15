# Show GN: gh-attach – CLI로 GitHub 이슈/PR에 이미지, 파일 첨부하기

- 원문: [https://news.hada.io/topic?id=31216](https://news.hada.io/topic?id=31216)
- 발행일: 2026-07-08
- 피드: GeekNews - 개발/기술/스타트업 뉴스 서비스

**요약**

gh-attach는 GitHub 이슈나 PR에 이미지·파일을 CLI에서 바로 첨부할 수 있게 해 주는 gh CLI 확장입니다. GitHub는 첨부 파일 업로드를 위한 공식 API를 제공하지 않기 때문에, 이 도구는 로컬 브라우저에 저장된 로그인 쿠키를 읽어 웹 UI와 동일한 업로드 API를 호출하는 방식으로 동작합니다. Chrome, Firefox, Safari 등 주요 브라우저의 쿠키를 지원하며, 로그인된 GitHub 계정과 일치하는 세션을 자동으로 선택합니다. 스크린샷 수동 첨부의 번거로움을 해결하기 위해 만들어졌으며, AI 에이전트가 PR 생성 시 다이어그램이나 스크린샷을 자동 업로드하는 용도로도 활용할 수 있습니다.

**핵심 포인트**

- GitHub에는 첨부 파일 업로드 공식 API가 없어, 기존에는 웹 UI에서 직접 업로드해야 했습니다.
- `gh extension install sudosubin/gh-attach`로 설치하고 `gh attach ./image.png -R owner/repo` 형태로 사용하며, 업로드된 파일의 URL을 반환합니다.
- 브라우저의 Profile/Container 지정이 가능하고, 로그인 계정과 일치하는 세션을 자동 선택합니다.
- `--json`, `--jq`, `--template` 옵션을 제공하여 스크립트 연동이 용이합니다.
- Go로 작성되었으며, gh 확장 또는 standalone 바이너리(Homebrew/GitHub)로 배포됩니다.
- 에이전트 기반 자동화 워크플로(PR 생성 시 이미지 자동 첨부 등)에 특히 유용합니다.
