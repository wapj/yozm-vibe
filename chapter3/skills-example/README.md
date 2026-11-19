# 3장 에이전트 스킬

책은 `chapter3/skills-example`에서 [task-keeper](https://github.com/wapj/task-keeper)를 클론한 뒤, 그 프로젝트 안의 `.claude/skills/`에 스킬을 만듭니다.

이 저장소의 완성본 경로는 다음과 같습니다.

```text
chapter3/skills-example/task-keeper/.claude/skills/
├── create-issue/
│   ├── SKILL.md
│   └── resources/issue_templates.md
├── git-commit/SKILL.md
├── create-pr/
│   ├── SKILL.md
│   └── resources/pr_template.md
├── review-pr/
│   ├── SKILL.md
│   └── resources/review_checklist.md
├── apply-pr-review/SKILL.md
└── commit-and-pr/SKILL.md
```

애플리케이션 코드는 이 디렉터리에 포함하지 않았습니다. 실습할 때는 포크한 task-keeper를 별도 폴더에 클론하고, 위 스킬 디렉터리를 그 저장소의 `.claude/skills/`로 복사하거나 책을 따라 직접 작성합니다. 이 디렉터리 자체에 `git clone`을 실행하면 이미 있는 스킬 파일과 겹칩니다.
