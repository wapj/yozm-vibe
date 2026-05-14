# tests/test_prompting.py
from app.prompting import SupportTicket, render_prompt


def test_render_prompt_fills_placeholders():
    ticket = SupportTicket(
        ticket_id="t1",
        customer_id="c1",
        subject="환불 문의",
        message="환불 가능한가요?",
        product="LangOps Pro",
        required_keywords=["환불", "결제일"],
    )
    rendered = render_prompt(ticket)

    assert "t1" in rendered
    assert "c1" in rendered
    assert "환불 문의" in rendered
    assert "환불 가능한가요?" in rendered
    assert "LangOps Pro" in rendered
    assert "환불, 결제일" in rendered


def test_render_prompt_handles_empty_keywords():
    ticket = SupportTicket(
        ticket_id="t1",
        customer_id="c1",
        subject="제목",
        message="문의 내용",
        product="LangOps Pro",
    )
    rendered = render_prompt(ticket)
    assert "필수 키워드: " in rendered
