# app/prompting.py
from dataclasses import dataclass, field


@dataclass
class SupportTicket:
    ticket_id: str
    customer_id: str
    subject: str
    message: str
    product: str
    priority: str = "normal"
    required_keywords: list[str] = field(default_factory=list)


def compile_prompt(prompt, ticket: SupportTicket) -> str:
    """Langfuse Prompt 객체와 티켓을 받아 렌더링된 문자열을 반환"""
    return prompt.compile(
        ticket_id=ticket.ticket_id,
        customer_id=ticket.customer_id,
        product=ticket.product,
        priority=ticket.priority,
        subject=ticket.subject,
        required_keywords=", ".join(ticket.required_keywords),
        message=ticket.message,
    )
