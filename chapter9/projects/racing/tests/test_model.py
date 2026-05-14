"""T2 acceptance tests: src/model.js — computeOdds + createHorses."""
import json
import subprocess
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
MODEL = ROOT / "src" / "model.js"


def _run_js(script: str) -> str:
    """Run inline JS that imports from src/model.js and prints JSON result."""
    full = (
        f'import {{ computeOdds, createHorses }} from "{MODEL.as_posix()}";\n'
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


def test_model_file_exists():
    assert MODEL.exists(), "src/model.js가 없습니다"


def test_compute_odds_80():
    out = _run_js("console.log(computeOdds(80));")
    assert float(out) == 2.5


def test_compute_odds_100():
    out = _run_js("console.log(computeOdds(100));")
    assert float(out) == 2.0


def test_compute_odds_120():
    out = _run_js("console.log(computeOdds(120));")
    assert float(out) == 1.67


def test_compute_odds_clamp_upper():
    out = _run_js("console.log(computeOdds(10));")
    assert float(out) == 10.0


def test_compute_odds_clamp_lower():
    out = _run_js("console.log(computeOdds(1000));")
    assert float(out) == 1.5


def test_create_horses_rng_zero():
    out = _run_js("console.log(JSON.stringify(createHorses(() => 0)));")
    horses = json.loads(out)
    assert len(horses) == 5
    names = [h["name"] for h in horses]
    assert names == ["Thunder", "Mystic", "Golden", "Emerald", "Shadow"]
    for h in horses:
        assert h["meanSpeed"] == 80.0
        assert h["odds"] == 2.5


def test_create_horses_rng_near_one():
    out = _run_js("console.log(JSON.stringify(createHorses(() => 1 - 1e-9)));")
    horses = json.loads(out)
    for h in horses:
        assert 119.9 < h["meanSpeed"] < 120.0
        assert h["odds"] == 1.67


def test_create_horses_default_rng_ranges():
    out = _run_js("console.log(JSON.stringify(createHorses()));")
    horses = json.loads(out)
    assert len(horses) == 5
    for h in horses:
        assert 80 <= h["meanSpeed"] < 120, f"meanSpeed out of range: {h['meanSpeed']}"
        assert 1.5 <= h["odds"] <= 10.0, f"odds out of range: {h['odds']}"
