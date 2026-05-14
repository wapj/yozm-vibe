"""T4 acceptance tests: src/bet.js — validateBet + settleBet."""
import json
import subprocess
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
BET = ROOT / "src" / "bet.js"


def _run_js(script: str) -> str:
    full = (
        f'import {{ validateBet, settleBet }} from "{BET.as_posix()}";\n'
        + script
    )
    result = subprocess.run(
        ["node", "--input-type=module"],
        input=full,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, f"node error:\n{result.stderr}"
    return result.stdout.strip()


def test_bet_file_exists():
    assert BET.exists(), "src/bet.js가 없습니다"


def test_validate_bet_ok():
    out = _run_js("console.log(JSON.stringify(validateBet({ horseIndex: 2, amount: 50, balance: 1000 })));")
    assert json.loads(out) == {"ok": True}


def test_validate_bet_no_balance():
    out = _run_js("console.log(JSON.stringify(validateBet({ horseIndex: 2, amount: 50, balance: 0 })));")
    assert json.loads(out) == {"ok": False, "error": "NO_BALANCE"}


def test_validate_bet_invalid_horse_over():
    out = _run_js("console.log(JSON.stringify(validateBet({ horseIndex: 5, amount: 50, balance: 1000 })));")
    assert json.loads(out) == {"ok": False, "error": "INVALID_HORSE"}


def test_validate_bet_invalid_horse_negative():
    out = _run_js("console.log(JSON.stringify(validateBet({ horseIndex: -1, amount: 50, balance: 1000 })));")
    assert json.loads(out) == {"ok": False, "error": "INVALID_HORSE"}


def test_validate_bet_below_min():
    out = _run_js("console.log(JSON.stringify(validateBet({ horseIndex: 0, amount: 9, balance: 1000 })));")
    assert json.loads(out) == {"ok": False, "error": "BELOW_MIN"}


def test_validate_bet_exceeds_balance():
    out = _run_js("console.log(JSON.stringify(validateBet({ horseIndex: 0, amount: 1500, balance: 1000 })));")
    assert json.loads(out) == {"ok": False, "error": "EXCEEDS_BALANCE"}


def test_validate_bet_invalid_amount_float():
    out = _run_js("console.log(JSON.stringify(validateBet({ horseIndex: 0, amount: 10.5, balance: 1000 })));")
    assert json.loads(out) == {"ok": False, "error": "INVALID_AMOUNT"}


def test_validate_bet_invalid_amount_nan():
    out = _run_js("console.log(JSON.stringify(validateBet({ horseIndex: 0, amount: NaN, balance: 1000 })));")
    assert json.loads(out) == {"ok": False, "error": "INVALID_AMOUNT"}


def test_settle_bet_win():
    script = """
const horses = [
  { name:"A", color:"#f00", meanSpeed:100, odds:2.5, rank:2, finishTime:10.5 },
  { name:"B", color:"#0f0", meanSpeed:95,  odds:2.0, rank:1, finishTime:9.8 },
  { name:"C", color:"#00f", meanSpeed:110, odds:1.8, rank:3, finishTime:11.0 },
  { name:"D", color:"#ff0", meanSpeed:85,  odds:2.35,rank:4, finishTime:12.0 },
  { name:"E", color:"#0ff", meanSpeed:105, odds:1.9, rank:5, finishTime:13.0 },
];
const r = settleBet({ horseIndex: 1, amount: 100, horses });
console.log(JSON.stringify({ won: r.won, delta: r.delta, payout: r.payout }));
"""
    out = json.loads(_run_js(script))
    assert out == {"won": True, "delta": 100, "payout": 200}


def test_settle_bet_lose():
    script = """
const horses = [
  { name:"A", color:"#f00", meanSpeed:100, odds:2.5, rank:1, finishTime:9.0 },
  { name:"B", color:"#0f0", meanSpeed:95,  odds:2.0, rank:2, finishTime:10.0 },
  { name:"C", color:"#00f", meanSpeed:110, odds:1.8, rank:3, finishTime:11.0 },
  { name:"D", color:"#ff0", meanSpeed:85,  odds:2.35,rank:4, finishTime:12.0 },
  { name:"E", color:"#0ff", meanSpeed:105, odds:1.9, rank:5, finishTime:13.0 },
];
const r = settleBet({ horseIndex: 1, amount: 150, horses });
console.log(JSON.stringify({ won: r.won, delta: r.delta, payout: r.payout, winnerName: r.winner.name }));
"""
    out = json.loads(_run_js(script))
    assert out["won"] is False
    assert out["delta"] == -150
    assert out["payout"] == 0
    assert out["winnerName"] == "A"


def test_settle_bet_delta_formula():
    script = """
const horses = [
  { name:"A", color:"#f00", meanSpeed:100, odds:3.5, rank:1, finishTime:9.0 },
  { name:"B", color:"#0f0", meanSpeed:95,  odds:2.0, rank:2, finishTime:10.0 },
  { name:"C", color:"#00f", meanSpeed:110, odds:1.8, rank:3, finishTime:11.0 },
  { name:"D", color:"#ff0", meanSpeed:85,  odds:2.35,rank:4, finishTime:12.0 },
  { name:"E", color:"#0ff", meanSpeed:105, odds:1.9, rank:5, finishTime:13.0 },
];
const r = settleBet({ horseIndex: 0, amount: 200, horses });
console.log(r.delta);
"""
    assert float(_run_js(script)) == 500.0
