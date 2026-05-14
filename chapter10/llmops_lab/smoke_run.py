# smoke_run.py
from dotenv import load_dotenv
from app.prompting import SupportTicket
from app.service import process_ticket

load_dotenv()


ticket = SupportTicket(
    ticket_id="smoke_001",
    customer_id="c_smoke",
    subject="환불 문의",
    message="지난주에 결제한 연간 구독을 환불하고 싶습니다.",
    product="LangOps Pro",
    priority="high",
    required_keywords=["환불", "결제일", "영업일"],
)

result = process_ticket(ticket)
print("답변:", result.answer[:200])
print(f"키워드 커버리지: {result.eval_result.keyword_coverage:.2f}")
print(f"형식 통과: {result.eval_result.format_ok}")
print(f"지연: {result.claude_result.duration_ms:.0f}ms")
print(f"비용: ${result.claude_result.cost_usd:.4f}")
