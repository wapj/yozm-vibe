"""T5 acceptance tests: src/ui.js — DOM 보조 함수."""
import json
import subprocess
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
UI = ROOT / "src" / "ui.js"


def _run_js(script: str) -> str:
    full = (
        f'import {{ positionPercent, formatBalance, formatOddsLabel, '
        f'formatResultMessage, setDisabled, applyHorsePositions, formatBetHint }} from "{UI.as_posix()}";\n'
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


def test_ui_file_exists():
    assert UI.exists(), "src/ui.js가 없습니다"


def test_position_percent_zero():
    out = _run_js("console.log(positionPercent(0, 1000));")
    assert float(out) == 0.0


def test_position_percent_mid():
    out = _run_js("console.log(positionPercent(500, 1000));")
    assert float(out) == 50.0


def test_position_percent_over_clamp():
    out = _run_js("console.log(positionPercent(1500, 1000));")
    assert float(out) == 100.0


def test_position_percent_negative_clamp():
    out = _run_js("console.log(positionPercent(-10, 1000));")
    assert float(out) == 0.0


def test_position_percent_zero_track_length():
    out = _run_js("console.log(positionPercent(100, 0));")
    assert float(out) == 0.0


def test_format_balance():
    out = _run_js("console.log(JSON.stringify([formatBalance(1000), formatBalance(0)]));")
    assert json.loads(out) == ["잔고: 1000", "잔고: 0"]


def test_format_odds_label_thunder():
    out = _run_js('console.log(formatOddsLabel({ name: "Thunder", odds: 2.5 }));')
    assert out == "Thunder (2.50배)"


def test_format_odds_label_mystic():
    out = _run_js('console.log(formatOddsLabel({ name: "Mystic", odds: 1.83 }));')
    assert out == "Mystic (1.83배)"


def test_format_result_message_win():
    script = 'console.log(formatResultMessage({ won: true, delta: 100, payout: 200, winner: { name: "Mystic" } }));'
    out = _run_js(script)
    assert out == "적중! Mystic 1등 — +100"


def test_format_result_message_lose():
    script = 'console.log(formatResultMessage({ won: false, delta: -150, payout: 0, winner: { name: "Thunder" } }));'
    out = _run_js(script)
    assert out == "실패. Thunder 1등 — -150"


def test_set_disabled_true():
    script = """
const els = [{disabled: false}, {disabled: false}];
setDisabled(els, true);
console.log(JSON.stringify(els.map(e => e.disabled)));
"""
    out = json.loads(_run_js(script))
    assert out == [True, True]


def test_set_disabled_false():
    script = """
const els = [{disabled: true}, {disabled: true}];
setDisabled(els, false);
console.log(JSON.stringify(els.map(e => e.disabled)));
"""
    out = json.loads(_run_js(script))
    assert out == [False, False]


def test_apply_horse_positions():
    script = """
const horses = [{progress: 500}, {progress: 1000}, {progress: 0}];
const lanes = [
  {horseEl: {style: {}}},
  {horseEl: {style: {}}},
  {horseEl: {style: {}}},
];
applyHorsePositions(horses, lanes, 1000);
console.log(JSON.stringify(lanes.map(l => l.horseEl.style.left)));
"""
    out = json.loads(_run_js(script))
    assert out == ["50%", "100%", "0%"]


# ── T15: formatBetHint ────────────────────────────────────────────────────────

def test_format_bet_hint_no_balance():
    out = _run_js('console.log(formatBetHint("NO_BALANCE"));')
    assert out == "잔고가 부족합니다."


def test_format_bet_hint_invalid_horse():
    out = _run_js('console.log(formatBetHint("INVALID_HORSE"));')
    assert out == "베팅할 말을 선택하세요."


def test_format_bet_hint_invalid_amount():
    out = _run_js('console.log(formatBetHint("INVALID_AMOUNT"));')
    assert out == "베팅 금액을 정수로 입력하세요."


def test_format_bet_hint_below_min():
    out = _run_js('console.log(formatBetHint("BELOW_MIN"));')
    assert out == "최소 베팅 금액은 10입니다."


def test_format_bet_hint_exceeds_balance():
    out = _run_js('console.log(formatBetHint("EXCEEDS_BALANCE"));')
    assert out == "베팅 금액이 현재 잔고를 초과합니다."


def test_format_bet_hint_unknown_fallback():
    out1 = _run_js('console.log(formatBetHint("UNKNOWN_REASON"));')
    assert out1 == "베팅 정보를 확인해주세요."
    out2 = _run_js('console.log(formatBetHint(undefined));')
    assert out2 == "베팅 정보를 확인해주세요."
