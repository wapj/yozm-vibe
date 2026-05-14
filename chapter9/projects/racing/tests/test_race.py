"""T3 acceptance tests: src/race.js — tickSpeed + simulateRace."""
import json
import subprocess
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
RACE = ROOT / "src" / "race.js"

HORSES_JS = """
const horses = [
  { name:"A", color:"#f00", meanSpeed:100, odds:2.0 },
  { name:"B", color:"#0f0", meanSpeed:95,  odds:2.1 },
  { name:"C", color:"#00f", meanSpeed:110, odds:1.8 },
  { name:"D", color:"#ff0", meanSpeed:85,  odds:2.35 },
  { name:"E", color:"#0ff", meanSpeed:105, odds:1.9 },
];
"""

EQUAL_HORSES_JS = """
const horses = [
  { name:"A", color:"#f00", meanSpeed:100, odds:2.0 },
  { name:"B", color:"#0f0", meanSpeed:100, odds:2.0 },
  { name:"C", color:"#00f", meanSpeed:100, odds:2.0 },
  { name:"D", color:"#ff0", meanSpeed:100, odds:2.0 },
  { name:"E", color:"#0ff", meanSpeed:100, odds:2.0 },
];
"""


def _run_js(script: str) -> str:
    full = (
        f'import {{ tickSpeed, simulateRace }} from "{RACE.as_posix()}";\n'
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


def test_race_file_exists():
    assert RACE.exists(), "src/race.js가 없습니다"


def test_tick_speed_midpoint():
    out = _run_js("console.log(tickSpeed(100, () => 0.5));")
    assert float(out) == 100.0


def test_tick_speed_min():
    out = _run_js("console.log(tickSpeed(100, () => 0));")
    assert float(out) == 80.0


def test_tick_speed_max():
    out = _run_js("console.log(tickSpeed(100, () => 1 - 1e-9));")
    assert abs(float(out) - 120.0) < 1e-6


def test_simulate_race_deterministic():
    script = EQUAL_HORSES_JS + """
function makeCounter() {
  let n = 0;
  const seq = [];
  for (let i = 0; i < 10000; i++) seq.push((Math.sin(i * 1.234) + 1) / 2);
  return () => seq[n++ % seq.length];
}
const r1 = simulateRace(horses, { rng: makeCounter() });
const r2 = simulateRace(horses, { rng: makeCounter() });
const same = r1.every((h, i) =>
  Math.abs(h.finishTime - r2[i].finishTime) < 1e-12 && h.rank === r2[i].rank
);
console.log(same);
"""
    assert _run_js(script) == "true"


def test_simulate_race_structure():
    script = HORSES_JS + "console.log(JSON.stringify(simulateRace(horses)));"
    result = json.loads(_run_js(script))
    assert len(result) == 5
    for h in result:
        for key in ("name", "color", "meanSpeed", "odds", "finishTime", "rank"):
            assert key in h, f"missing key: {key}"


def test_simulate_race_ranks_are_permutation():
    script = HORSES_JS + "console.log(JSON.stringify(simulateRace(horses).map(h => h.rank)));"
    ranks = json.loads(_run_js(script))
    assert sorted(ranks) == [1, 2, 3, 4, 5]


def test_simulate_race_unique_winner():
    script = HORSES_JS + "console.log(simulateRace(horses).filter(h => h.rank === 1).length);"
    assert _run_js(script) == "1"


def test_simulate_race_finish_time_range():
    script = EQUAL_HORSES_JS + """
const result = simulateRace(horses);
const winner = result.find(h => h.rank === 1);
console.log(winner.finishTime);
"""
    val = float(_run_js(script))
    assert 6 < val < 16, f"finishTime {val} out of range (6, 16)"


def test_simulate_race_equal_speed_unique_winner():
    script = EQUAL_HORSES_JS + "console.log(simulateRace(horses).filter(h => h.rank === 1).length);"
    assert _run_js(script) == "1"
