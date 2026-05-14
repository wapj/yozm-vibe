# app/prompting.py
from pathlib import Path
from dataclasses import dataclass, field

PROMPT_PATH = Path("prompts/support_answer.md")


@dataclass
class SupportTicket:
    ticket_id: str
    customer_id: str
    subject: str
    message: str
    product: str
    priority: str = "normal"
    required_keywords: list[str] = field(default_factory=list)


def render_prompt(ticket: SupportTicket) -> str:
    template = PROMPT_PATH.read_text(encoding="utf-8")
    return template.format(
        ticket_id=ticket.ticket_id,
        customer_id=ticket.customer_id,
        product=ticket.product,
        priority=ticket.priority,
        subject=ticket.subject,
        message=ticket.message,
        required_keywords=", ".join(ticket.required_keywords),
    )
