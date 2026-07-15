import json
import os
import subprocess
import time
from pathlib import Path


def manual_worker(task: dict, root: Path, attempt: int, config: dict) -> dict:  # ① 사람이 구현하고 컨트롤러가 검증
    """독자가 코드를 직접 수정할 때 사용하는 작업자."""
    print(f"\n{task['id']}: {task['description']}")
    if task["id"] == "CALC-003":
        print(f"EXPECTED_USD_RATE={os.environ.get('EXPECTED_USD_RATE', '(없음)')}")
    answer = input(
        "workspace/app/calc.py를 수정한 뒤 Enter를 누르세요. "
        "사람에게 넘기려면 b를 입력합니다: "
    ).strip().lower()
    if answer == "b":
        reason = input("이관 이유: ").strip() or "외부 결정이 필요합니다."
        return {"status": "blocked", "reason": reason}
    return {"status": "completed", "reason": "수동 작업을 마쳤습니다."}


def run_worker(name: str, task: dict, root: Path, attempt: int, config: dict) -> dict:
    if name == "manual":
        return manual_worker(task, root, attempt, config)
    if name == "fixture":
        from fixture_worker import fixture_worker

        return fixture_worker(task, root, attempt, config)
    if name == "claude":
        return claude_worker(task, root, attempt, config)
    raise ValueError(f"알 수 없는 작업자: {name}")


def claude_worker(task: dict, root: Path, attempt: int, config: dict) -> dict:
    """Claude Code로 작업 한 건을 처리한다."""
    approved = os.environ.get("EXPECTED_USD_RATE", "없음")
    feedback = str(task.get("feedback", ""))[-4_000:]
    feedback_text = f"\n직전 검증 결과:\n{feedback}\n" if feedback else ""
    # ② 작업 계약과 직전 검증 결과 전달
    prompt = f"""다음 작업 한 건만 처리하세요.

작업 ID: {task['id']}
작업: {task['title']}
완료 조건: {task['description']}
승인된 USD 기준 환율: {approved}
{feedback_text}

규칙:
- app/calc.py만 수정합니다.
- 현재 작업과 관련 없는 TODO는 건드리지 않습니다.
- 완료하면 {task['marker']} 주석을 삭제합니다.
- 정보가 부족하면 코드를 바꾸지 말고 blocked로 보고합니다.
- 테스트와 완료 판정은 바깥의 컨트롤러가 담당합니다.
"""
    schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["completed", "blocked"]},
            "reason": {"type": "string"},
        },
        "required": ["status", "reason"],
        "additionalProperties": False,
    }
    command = [
        "claude",
        "-p",
        prompt,
        "--setting-sources",
        "project,local",
        "--tools",
        "Read,Edit",
        "--allowedTools",
        "Read(app/calc.py),Edit(app/calc.py)",  # ③ 대상 파일만 읽고 편집
        "--permission-mode",
        "dontAsk",
        "--disallowedTools",
        "mcp__*",
        "--strict-mcp-config",
        "--max-turns",
        str(config["max_turns"]),
        "--max-budget-usd",
        str(config["max_cost_usd"]),  # ④ 턴 수와 비용 상한
        "--no-session-persistence",
        "--output-format",
        "json",
        "--json-schema",
        json.dumps(schema, ensure_ascii=False, separators=(",", ":")),  # ⑤ 반환 형식 고정
    ]

    try:
        print(f"[llm] Claude Code 요청 시작: {task['id']}", flush=True)
        started = time.monotonic()
        process = subprocess.run(
            command,
            cwd=root / "workspace",
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=float(config["worker_timeout_seconds"]),
        )
        payload = json.loads(process.stdout)
        if process.returncode or payload.get("is_error"):
            reason = payload.get("result") or process.stderr.strip() or "Claude Code 실행 오류"
            return {"status": "error", "reason": str(reason)}
        result = payload.get("structured_output")
        if not isinstance(result, dict):
            return {"status": "error", "reason": "구조화된 작업 결과가 없습니다."}
        elapsed = time.monotonic() - started
        print(
            f"[llm] Claude Code 응답 수신: {elapsed:.1f}초, "
            f"추정 비용 ${payload.get('total_cost_usd', 0):.4f}"
        )
        return {"status": result["status"], "reason": str(result["reason"])}
    except FileNotFoundError:
        return {"status": "error", "reason": "claude 실행 파일을 찾지 못했습니다."}
    except subprocess.TimeoutExpired:
        return {"status": "error", "reason": "작업자 실행 시간이 상한을 넘었습니다."}
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        return {"status": "error", "reason": str(error)}
