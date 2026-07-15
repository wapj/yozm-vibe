# app/service.py
from dataclasses import dataclass
from .prompting import SupportTicket, compile_prompt
from .claude_runner import run_claude, ClaudeResult
from .evaluator import evaluate, EvalResult
from .langfuse_ops import (
    get_client,
    support_ticket_trace,
    claude_generation,
    quality_evaluator,
    record_scores,
)
from .history import append_run


@dataclass
class RunResult:
    answer: str
    claude_result: ClaudeResult
    eval_result: EvalResult


def process_ticket(ticket: SupportTicket) -> RunResult:
    client = get_client()
    prompt_obj = client.get_prompt("support-answer-v1", label="production")
    rendered = compile_prompt(prompt_obj, ticket)
    model = "sonnet"
    with support_ticket_trace(ticket) as root:
        with claude_generation(rendered, model=model, prompt=prompt_obj) as gen:
            claude_result = run_claude(rendered)
            usage = claude_result.raw_payload.get("usage", {})
            gen.update(
                output=claude_result.answer,
                model=claude_result.model,
                cost_details={"total": claude_result.cost_usd},
                usage_details={
                    "input": usage.get("input_tokens", 0),
                    "output": usage.get("output_tokens", 0),
                    "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0),
                    "cache_creation_input_tokens": usage.get(
                        "cache_creation_input_tokens", 0
                    ),
                },
            )

        with quality_evaluator(ticket.required_keywords) as ev:
            eval_result = evaluate(
                answer=claude_result.answer,
                required_keywords=ticket.required_keywords,
            )
            ev.update(
                output={
                    "keyword_coverage": eval_result.keyword_coverage,
                    "format_ok": eval_result.format_ok,
                    "response_length_ok": eval_result.length_ok,
                },
            )

        record_scores(root, claude_result, eval_result)
        root.update(output=claude_result.answer)

    append_run(ticket, claude_result, eval_result)

    return RunResult(
        answer=claude_result.answer,
        claude_result=claude_result,
        eval_result=eval_result,
    )
