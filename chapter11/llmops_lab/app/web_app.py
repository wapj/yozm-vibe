# app/web_app.py
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from .prompting import SupportTicket
from .service import process_ticket

load_dotenv()

app = FastAPI(title="고객 문의 답변 도우미")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "form.html")


@app.post("/run", response_class=HTMLResponse)
async def run(
    request: Request,
    ticket_id: str = Form(...),
    customer_id: str = Form(...),
    subject: str = Form(...),
    message: str = Form(...),
    product: str = Form(...),
    priority: str = Form("normal"),
    required_keywords: str = Form(""),
):
    ticket = SupportTicket(
        ticket_id=ticket_id,
        customer_id=customer_id,
        subject=subject,
        message=message,
        product=product,
        priority=priority,
        required_keywords=[
            k.strip() for k in required_keywords.split(",") if k.strip()
        ],
    )
    result = process_ticket(ticket)
    return templates.TemplateResponse(
        request,
        "result.html",
        {
            "ticket": ticket,
            "result": result,
        },
    )
