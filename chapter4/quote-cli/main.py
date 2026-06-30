import json
import random
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("quote")  # ① 서버 객체 생성

QUOTES_FILE = Path(__file__).parent / "quotes.json"


def load_quotes() -> list:
    return json.loads(QUOTES_FILE.read_text(encoding="utf-8"))


@mcp.tool()  # ② 무작위 명언 반환 도구
def get_random_quote() -> str:
    """무작위 명언 한 개를 반환합니다."""
    quote = random.choice(load_quotes())
    return f'{quote["text"]} - {quote["author"]}'


@mcp.tool()  # ③ 명언 추가 도구(쓰기)
def add_quote(text: str, author: str) -> str:
    """새 명언을 명언 목록에 추가합니다."""
    quotes = load_quotes()
    quotes.append({"text": text, "author": author})
    QUOTES_FILE.write_text(
        json.dumps(quotes, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return f"명언을 추가했습니다. 현재 {len(quotes)}개입니다."


@mcp.resource("quote://all")  # ④ 리소스
def all_quotes() -> str:
    """전체 명언 목록을 반환합니다."""
    return QUOTES_FILE.read_text(encoding="utf-8")


@mcp.prompt()  # ⑤ 프롬프트
def quote_post(topic: str) -> str:
    """명언을 인용한 짧은 글을 작성합니다."""
    return (
        f"등록된 명언 중 '{topic}' 주제와 가장 어울리는 것을 quote://all에서 고르고, "
        "그 명언을 인용한 세 문단 분량의 짧은 글을 작성해주세요."
    )


if __name__ == "__main__":
    mcp.run()  # ⑥ stdio 전송으로 서버 실행
