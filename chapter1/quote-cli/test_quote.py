"""quote.py의 동작을 검증하는 테스트."""
import json
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
QUOTE_SCRIPT = BASE_DIR / "quote.py"
QUOTES_FILE = BASE_DIR / "quotes.json"


def run_quote(*args):
    """quote.py를 서브프로세스로 실행하고 완료된 프로세스를 반환한다."""
    return subprocess.run(
        [sys.executable, str(QUOTE_SCRIPT), *args],
        capture_output=True,
        text=True,
        check=True,
    )


def load_quotes():
    with QUOTES_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def test_no_args_prints_single_quote():
    """인수 없이 실행하면 명언 한 건(텍스트 + 저자 두 줄)만 출력한다."""
    result = run_quote()
    lines = result.stdout.strip().splitlines()

    # 명언 한 건은 텍스트 줄과 저자 줄로 구성된다.
    assert len(lines) == 2
    # 저자 줄은 "  - " 접두사로 시작한다.
    assert lines[1].lstrip().startswith("- ")


def test_no_args_quote_is_from_dataset():
    """무작위로 출력된 명언이 quotes.json 안의 항목과 일치한다."""
    result = run_quote()
    output = result.stdout.strip()

    quotes = load_quotes()
    authors = [q["author"] for q in quotes]
    assert any(author in output for author in authors)


def test_list_prints_all_quotes():
    """--list는 quotes.json의 모든 항목을 번호와 함께 출력한다."""
    result = run_quote("--list")
    output = result.stdout
    quotes = load_quotes()

    # 항목 수만큼 번호 표시(1. ~ N.)가 존재한다.
    for i in range(1, len(quotes) + 1):
        assert f"{i}. " in output

    # 모든 명언 텍스트와 저자가 출력에 포함된다.
    for quote in quotes:
        assert quote["text"] in output
        assert quote["author"] in output


def test_list_line_count():
    """--list 출력 줄 수는 항목당 2줄(텍스트+저자)이다."""
    result = run_quote("--list")
    lines = result.stdout.strip().splitlines()
    quotes = load_quotes()
    assert len(lines) == len(quotes) * 2
