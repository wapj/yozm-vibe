# app/service.py
from dataclasses import dataclass
from .prompting import SupportTicket, render_prompt
from .claude_runner import run_claude, ClaudeResult
from .evaluator import evaluate, EvalResult
from .langfuse_ops import record_support_run
from .history import append_run


@dataclass
class RunResult:
    answer: str
    claude_result: ClaudeResult
    eval_result: EvalResult


def process_ticket(ticket: SupportTicket) -> RunResult:
    prompt = render_prompt(ticket)
    claude_result = run_claude(prompt)
    eval_result = evaluate(
        answer=claude_result.answer,
        required_keywords=ticket.required_keywords,
    )

    # 두 곳에 기록
    record_support_run(ticket, prompt, claude_result, eval_result)
    append_run(ticket, claude_result, eval_result)

    return RunResult(
        answer=claude_result.answer,
        claude_result=claude_result,
        eval_result=eval_result,
    )
