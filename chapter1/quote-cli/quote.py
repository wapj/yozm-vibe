#!/usr/bin/env python3
"""무작위 명언 출력 CLI.

인수 없이 실행하면 무작위 명언 하나를, --list를 주면 전체 목록을 출력한다.
"""
import argparse
import json
import random
import sys
from pathlib import Path

QUOTES_FILE = Path(__file__).resolve().parent / "quotes.json"


def load_quotes():
    """quotes.json에서 명언 목록을 읽어 반환한다."""
    try:
        with QUOTES_FILE.open(encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        sys.exit(f"명언 파일을 찾을 수 없습니다: {QUOTES_FILE}")
    except json.JSONDecodeError as e:
        sys.exit(f"명언 파일을 해석할 수 없습니다: {e}")


def format_quote(quote):
    """명언 한 건을 출력용 문자열로 변환한다."""
    return f"\"{quote['text']}\"\n  - {quote['author']}"


def main():
    parser = argparse.ArgumentParser(description="무작위 명언을 출력합니다.")
    parser.add_argument(
        "--list", action="store_true", help="전체 명언 목록을 출력합니다."
    )
    args = parser.parse_args()

    quotes = load_quotes()
    if not quotes:
        sys.exit("출력할 명언이 없습니다.")

    if args.list:
        for i, quote in enumerate(quotes, start=1):
            print(f"{i}. {format_quote(quote)}")
    else:
        print(format_quote(random.choice(quotes)))


if __name__ == "__main__":
    main()
