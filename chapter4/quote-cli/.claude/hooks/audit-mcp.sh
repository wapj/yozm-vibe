#!/bin/bash
set -euo pipefail
input="$(cat)"  # ① stdin으로 들어온 JSON 읽기
tool="$(printf '%s' "$input" | jq -r '.tool_name // ""')"  # ② 호출된 도구 이름 추출
payload="$(printf '%s' "$input" | jq -c '.tool_input // {}')"  # ③ 도구 입력값 추출
# ④ 시각, 도구 이름, 입력값을 한 줄로 로그 파일에 추가
printf '%s\t%s\t%s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$tool" "$payload" \
  >> "${CLAUDE_PROJECT_DIR:-.}/.claude/mcp-audit.log"
exit 0
