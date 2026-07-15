# tests/test_claude_runner.py
import pytest
from dotenv import load_dotenv
from app.claude_runner import run_claude

load_dotenv()


@pytest.mark.integration
def test_run_claude_returns_answer():
    result = run_claude("간단히 'pong'이라고만 답해주세요.")
    assert result.answer
    assert result.duration_ms > 0
    assert result.model
