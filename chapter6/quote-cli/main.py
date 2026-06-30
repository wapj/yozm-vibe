import argparse
import json
import random
import sqlite3
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("quote")  # ① 서버 객체 생성

QUOTES_FILE = Path(__file__).parent / "quotes.json"  # 시드 원본


def _db_path() -> Path:
    # 시드 원본(QUOTES_FILE)과 같은 디렉터리에 quotes.db를 둔다.
    # 테스트가 QUOTES_FILE을 tmp_path로 바꾸면 DB도 tmp_path로 따라간다.
    return QUOTES_FILE.parent / "quotes.db"


def _connect() -> sqlite3.Connection:  # ② DB 연결 + 최초 1회 시드
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE IF NOT EXISTS quotes ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "text TEXT NOT NULL, author TEXT NOT NULL)"
    )
    # DB가 비어 있으면 quotes.json을 시드 데이터로 적재한다.
    count = conn.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
    if count == 0 and QUOTES_FILE.exists():
        seed = json.loads(QUOTES_FILE.read_text(encoding="utf-8"))
        conn.executemany(
            "INSERT INTO quotes (text, author) VALUES (?, ?)",
            [(q["text"], q["author"]) for q in seed],
        )
        conn.commit()
    return conn


def load_quotes() -> list:  # ③ 전체 명언 조회
    conn = _connect()
    rows = conn.execute("SELECT text, author FROM quotes ORDER BY id").fetchall()
    conn.close()
    return [{"text": r["text"], "author": r["author"]} for r in rows]


def search_quotes(keyword: str) -> list:
    """명언 본문(text)에 keyword가 포함된 항목만 반환합니다."""
    return [quote for quote in load_quotes() if keyword in quote["text"]]


@mcp.tool()  # ④ 무작위 명언 반환 도구
def get_random_quote() -> str:
    """무작위 명언 한 개를 반환합니다."""
    quote = random.choice(load_quotes())
    return f'{quote["text"]} - {quote["author"]}'


@mcp.tool()  # ⑤ 명언 추가 도구(쓰기)
def add_quote(text: str, author: str) -> str:
    """새 명언을 명언 목록에 추가합니다."""
    conn = _connect()
    conn.execute(
        "INSERT INTO quotes (text, author) VALUES (?, ?)", (text, author)
    )
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM quotes").fetchone()[0]
    conn.close()
    return f"명언을 추가했습니다. 현재 {count}개입니다."


@mcp.resource("quote://all")  # ⑥ 리소스
def all_quotes() -> str:
    """전체 명언 목록을 반환합니다."""
    return json.dumps(load_quotes(), ensure_ascii=False, indent=2)


@mcp.prompt()  # ⑦ 프롬프트
def quote_post(topic: str) -> str:
    """명언을 인용한 짧은 글을 작성합니다."""
    return (
        f"등록된 명언 중 '{topic}' 주제와 가장 어울리는 것을 quote://all에서 고르고, "
        "그 명언을 인용한 세 문단 분량의 짧은 글을 작성해주세요."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="명언 CLI / MCP 서버")
    parser.add_argument(
        "--search",
        metavar="키워드",
        help="명언 본문에 키워드가 포함된 항목만 출력합니다.",
    )
    args = parser.parse_args()

    if args.search is not None:  # ⑧ 검색 모드
        results = search_quotes(args.search)
        if not results:
            print(f"'{args.search}'을(를) 포함하는 명언이 없습니다.")
            sys.exit(1)
        for quote in results:
            print(f'{quote["text"]} - {quote["author"]}')
        return

    mcp.run()  # ⑨ stdio 전송으로 서버 실행


if __name__ == "__main__":
    main()
