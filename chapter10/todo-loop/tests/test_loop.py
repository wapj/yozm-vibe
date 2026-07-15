import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))
import loop
import workers


PROJECT_FILES = (
    "checks",
    "seed",
    "loop.py",
    "workers.py",
    "fixture_worker.py",
    "loop.toml",
    "tasks.toml",
    "pyproject.toml",
)


@pytest.fixture
def project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    source = Path(__file__).parents[1]
    root = tmp_path / "todo-loop"
    root.mkdir()
    for name in PROJECT_FILES:
        origin = source / name
        destination = root / name
        if origin.is_dir():
            shutil.copytree(origin, destination)
        else:
            shutil.copy2(origin, destination)
    monkeypatch.delenv("EXPECTED_USD_RATE", raising=False)
    return root


def run(
    project: Path,
    *args: str,
    env: dict | None = None,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "loop.py", *args],
        cwd=project,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        input=input_text,
    )


def state(project: Path) -> dict:
    return json.loads((project / ".loop" / "state.json").read_text(encoding="utf-8"))


def test_simulation_reproduces_book_flow(project: Path) -> None:
    result = run(project, "simulate")

    assert result.returncode == 0
    assert "worker=fixture: LLM 호출 없는 결정적 재현" in result.stdout
    assert "CALC-002 -> retry" in result.stdout
    assert "CALC-003 -> needs_human" in result.stdout
    assert "[requeue] CALC-003 -> pending" in result.stdout
    assert "[done] 4/4건 완료" in result.stdout
    assert "4 passed" in result.stdout
    current = state(project)
    assert current["tasks"]["CALC-002"]["attempts"] == 2
    assert current["tasks"]["CALC-003"]["status"] == "passed"
    assert current["tasks"]["CALC-004"]["status"] == "passed"
    assert current["calls"] == 6
    assert not (project / ".loop" / "handoff" / "CALC-003.md").exists()

    cancelled = run(project, "simulate", input_text="n\n")
    assert cancelled.returncode == 2
    assert "[simulate] 취소했습니다." in cancelled.stdout
    assert state(project) == current


def test_failed_change_is_restored_before_retry(project: Path) -> None:
    assert run(project, "reset").returncode == 0
    assert run(project, "run", "--once", "--worker", "fixture").returncode == 0
    failed = run(project, "run", "--once", "--worker", "fixture")

    source = (project / "workspace" / "app" / "calc.py").read_text(encoding="utf-8")
    assert failed.returncode == 2
    assert "TODO[CALC-002]" in source
    assert state(project)["tasks"]["CALC-002"]["status"] == "retry"


def test_last_allowed_call_can_finish_all_tasks(
    project: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("EXPECTED_USD_RATE", "1325.5")
    assert run(project, "reset", env=os.environ.copy()).returncode == 0
    result = run(
        project,
        "run",
        "--worker",
        "fixture",
        "--max-calls",
        "5",
        env=os.environ.copy(),
    )

    assert result.returncode == 0
    assert "[done] 4/4건 완료" in result.stdout
    assert state(project)["calls"] == 5


def test_removing_only_todo_does_not_pass(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(loop, "ROOT", project)
    monkeypatch.setattr(loop, "WORKSPACE", project / "workspace")
    monkeypatch.setattr(loop, "TARGET", project / "workspace" / "app" / "calc.py")
    monkeypatch.setattr(loop, "RUNTIME", project / ".loop")
    monkeypatch.setattr(loop, "STATE", project / ".loop" / "state.json")
    monkeypatch.setattr(loop, "EVENTS", project / ".loop" / "events.jsonl")
    monkeypatch.setattr(loop, "BACKUP", project / ".loop" / "before.py")
    monkeypatch.setattr(loop, "EVIDENCE", project / ".loop" / "evidence")
    monkeypatch.setattr(loop, "HANDOFF", project / ".loop" / "handoff")
    tasks = loop.load_toml("tasks.toml", "tasks")
    config = loop.load_toml("loop.toml", "loop")
    loop.reset(tasks)
    path = project / "workspace" / "app" / "calc.py"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            "    # TODO[CALC-001]: WELCOME10은 10% 할인 후 100원 단위로 내린다.\n",
            "",
        ),
        encoding="utf-8",
    )

    passed, output = loop.verify(tasks[0], loop.load_state(), tasks, config)
    assert not passed
    assert "test_calc_001_coupon" in output
    assert (project / ".loop" / "evidence" / "CALC-001-0.txt").exists()


def test_worker_error_stops_without_spending_task_attempt(project: Path) -> None:
    assert run(project, "reset").returncode == 0
    path = project / "workspace" / "app" / "calc.py"
    path.write_text(
        path.read_text(encoding="utf-8").replace("    return total\n", "    return -1\n", 1),
        encoding="utf-8",
    )

    result = run(project, "run", "--once", "--worker", "fixture")
    item = state(project)["tasks"]["CALC-001"]
    assert result.returncode == 4
    assert "[halt] 작업자 실행 오류" in result.stdout
    assert item["status"] == "pending"
    assert item["attempts"] == 0


def test_status_recovers_interrupted_change(project: Path) -> None:
    assert run(project, "reset").returncode == 0
    target = project / "workspace" / "app" / "calc.py"
    shutil.copy2(target, project / ".loop" / "before.py")
    target.write_text("검증되지 않은 변경\n", encoding="utf-8")
    current = state(project)
    current["tasks"]["CALC-001"].update(status="running", attempts=1)
    current["active"] = "CALC-001"
    (project / ".loop" / "state.json").write_text(
        json.dumps(current, ensure_ascii=False), encoding="utf-8"
    )

    result = run(project, "status")
    assert result.returncode == 0
    assert "[recover] CALC-001" in result.stdout
    assert "TODO[CALC-001]" in target.read_text(encoding="utf-8")
    assert state(project)["tasks"]["CALC-001"]["status"] == "retry"


def test_claude_worker_limits_tools_and_budget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    called = {}

    def fake_run(command, **kwargs):
        called.update(command=command, **kwargs)
        payload = {
            "total_cost_usd": 0.1,
            "structured_output": {"status": "completed", "reason": "완료"},
        }
        return subprocess.CompletedProcess(command, 0, json.dumps(payload), "")

    monkeypatch.setattr(subprocess, "run", fake_run)
    result = workers.claude_worker(
        {
            "id": "CALC-001",
            "title": "쿠폰",
            "description": "쿠폰 적용",
            "marker": "TODO[CALC-001]",
            "feedback": "부동소수점 오차",
        },
        tmp_path,
        1,
        {"max_turns": 6, "max_cost_usd": 0.5, "worker_timeout_seconds": 30},
    )

    assert result["status"] == "completed"
    command = called["command"]
    assert command[command.index("--tools") + 1] == "Read,Edit"
    assert command[command.index("--allowedTools") + 1] == (
        "Read(app/calc.py),Edit(app/calc.py)"
    )
    assert command[command.index("--max-budget-usd") + 1] == "0.5"
    assert "직전 검증 결과:\n부동소수점 오차" in command[2]
    assert "--plugin-dir" not in command
    assert "env" not in called
    output = capsys.readouterr().out
    assert "[llm] Claude Code 요청 시작: CALC-001" in output
    assert "[llm] Claude Code 응답 수신:" in output


def test_claude_worker_keeps_cli_error_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = {"is_error": True, "result": "인증 실패"}
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda command, **kwargs: subprocess.CompletedProcess(
            command, 1, json.dumps(payload), ""
        ),
    )
    result = workers.claude_worker(
        {
            "id": "CALC-001",
            "title": "쿠폰",
            "description": "쿠폰 적용",
            "marker": "TODO[CALC-001]",
        },
        tmp_path,
        1,
        {"max_turns": 6, "max_cost_usd": 0.5, "worker_timeout_seconds": 30},
    )

    assert result == {"status": "error", "reason": "인증 실패"}
