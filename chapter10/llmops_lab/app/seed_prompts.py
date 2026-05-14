# app/seed_prompts.py
from pathlib import Path
from dotenv import load_dotenv

from .langfuse_ops import get_client

load_dotenv()


def main():
    client = get_client()
    template = Path("prompts/support_answer.md").read_text(encoding="utf-8")

    client.create_prompt(
        name="support-answer-v1",
        prompt=template,
        labels=["production"],
        type="text",
    )
    client.flush()
    print("등록 완료: support-answer-v1 (production)")


if __name__ == "__main__":
    main()
