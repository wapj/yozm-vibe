"""T6/T7/T8 acceptance tests: src/main.js — computeFramePositions + roundDelta + runOneRace + initApp."""
import json
import subprocess
import pathlib
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).parent.parent
MAIN = ROOT / "src" / "main.js"
INDEX = ROOT / "index.html"


def _run_js(script: str) -> str:
    full = (
        f'import {{ computeFramePositions, roundDelta }} from "{MAIN.as_posix()}";\n'
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


def _run_js_race(script: str) -> str:
    full = (
        f'import {{ runOneRace }} from "{MAIN.as_posix()}";\n'
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


class _AttrCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements: list[dict] = []

    def handle_starttag(self, tag, attrs):
        self.elements.append({"tag": tag, "attrs": dict(attrs)})


def _parse_html():
    collector = _AttrCollector()
    collector.feed(INDEX.read_text(encoding="utf-8"))
    return collector.elements


def test_main_file_exists():
    assert MAIN.exists(), "src/main.js가 없습니다"


def test_compute_frame_positions_at_zero():
    out = _run_js(
        "console.log(JSON.stringify(computeFramePositions([{finishTime:10},{finishTime:5}], 0, 1000)));"
    )
    assert json.loads(out) == [0, 0]


def test_compute_frame_positions_mid():
    out = _run_js(
        "console.log(JSON.stringify(computeFramePositions([{finishTime:10},{finishTime:5}], 5, 1000)));"
    )
    assert json.loads(out) == [500, 1000]


def test_compute_frame_positions_at_end():
    out = _run_js(
        "console.log(JSON.stringify(computeFramePositions([{finishTime:10},{finishTime:5}], 10, 1000)));"
    )
    assert json.loads(out) == [1000, 1000]


def test_compute_frame_positions_negative_elapsed():
    out = _run_js(
        "console.log(JSON.stringify(computeFramePositions([{finishTime:10}], -1, 1000)));"
    )
    assert json.loads(out) == [0]


def test_compute_frame_positions_zero_finish_time():
    out = _run_js(
        "console.log(JSON.stringify(computeFramePositions([{finishTime:0}], 5, 1000)));"
    )
    assert json.loads(out) == [0]


def test_compute_frame_positions_infinite_finish_time():
    out = _run_js(
        "console.log(JSON.stringify(computeFramePositions([{finishTime:Infinity}], 5, 1000)));"
    )
    assert json.loads(out) == [0]


def test_compute_frame_positions_custom_track_length():
    out = _run_js(
        "console.log(JSON.stringify(computeFramePositions([{finishTime:8}], 4, 500)));"
    )
    assert json.loads(out) == [250]


def test_round_delta_integer():
    out = _run_js("console.log(roundDelta(150));")
    assert int(out) == 150


def test_round_delta_round_down():
    out = _run_js("console.log(roundDelta(149.4));")
    assert int(out) == 149


def test_round_delta_round_up():
    out = _run_js("console.log(roundDelta(149.5));")
    assert int(out) == 150


def test_round_delta_negative():
    out = _run_js("console.log(roundDelta(-149.4));")
    assert int(out) == -149


def test_index_html_start_btn_type():
    elements = _parse_html()
    btns = [e for e in elements if e["tag"] == "button" and e["attrs"].get("id") == "start-btn"]
    assert len(btns) == 1, "#start-btn 버튼이 없거나 중복됩니다"
    assert btns[0]["attrs"].get("type") == "button", '#start-btn에 type="button"이 없습니다'


def test_index_html_script_module():
    elements = _parse_html()
    scripts = [
        e for e in elements
        if e["tag"] == "script"
        and e["attrs"].get("type") == "module"
        and e["attrs"].get("src") == "src/main.js"
    ]
    assert len(scripts) >= 1, 'type="module" src="src/main.js" script 태그가 없습니다'


def test_index_html_result_modal():
    html = INDEX.read_text(encoding="utf-8")
    elements = _parse_html()

    modal = [e for e in elements if e["attrs"].get("id") == "result-modal"]
    assert len(modal) == 1, "#result-modal 요소가 없습니다"
    assert "hidden" in modal[0]["attrs"], "#result-modal에 hidden 속성이 없습니다"

    msg = [e for e in elements if e["attrs"].get("id") == "result-message"]
    assert len(msg) == 1, "#result-message 요소가 없습니다"

    btn = [e for e in elements if e["attrs"].get("id") == "next-race-btn"]
    assert len(btn) == 1, "#next-race-btn 요소가 없습니다"


# ── T7: runOneRace ────────────────────────────────────────────────────────────

def test_run_one_race_export_exists():
    out = _run_js_race("console.log(typeof runOneRace);")
    assert out == "function"


def test_run_one_race_win():
    script = """
const horses = [{rank:1,odds:2.5,name:"Thunder"},{rank:2,odds:3.0,name:"Mystic"}];
const r = runOneRace({balance:1000, horses, bet:{horseIndex:0, amount:100}});
console.log(JSON.stringify(r));
"""
    r = json.loads(_run_js_race(script))
    assert r["won"] is True
    assert r["delta"] == 150
    assert r["newBalance"] == 1150
    assert r["winner"]["name"] == "Thunder"


def test_run_one_race_loss():
    script = """
const horses = [{rank:1,odds:2.5,name:"Thunder"},{rank:2,odds:3.0,name:"Mystic"}];
const r = runOneRace({balance:1000, horses, bet:{horseIndex:1, amount:100}});
console.log(JSON.stringify(r));
"""
    r = json.loads(_run_js_race(script))
    assert r["won"] is False
    assert r["delta"] == -100
    assert r["newBalance"] == 900
    assert r["winner"]["name"] == "Thunder"


def test_run_one_race_float_rounding():
    script = """
const horses = [{rank:1,odds:1.51,name:"A"},{rank:2,odds:5.0,name:"B"}];
const r = runOneRace({balance:1000, horses, bet:{horseIndex:0, amount:99}});
console.log(JSON.stringify({
  delta: r.delta,
  newBalance: r.newBalance,
  won: r.won,
  deltaIsInt: Number.isInteger(r.delta),
  balanceIsInt: Number.isInteger(r.newBalance)
}));
"""
    r = json.loads(_run_js_race(script))
    assert r["won"] is True
    assert r["delta"] == 50
    assert r["newBalance"] == 1050
    assert r["deltaIsInt"] is True
    assert r["balanceIsInt"] is True


def test_run_one_race_float_rounding_boundary():
    script = """
const horses = [{rank:1,odds:2.005,name:"A"},{rank:2,odds:5.0,name:"B"}];
const r = runOneRace({balance:1000, horses, bet:{horseIndex:0, amount:100}});
const expected = Math.round(100 * (2.005 - 1));
console.log(JSON.stringify({match: r.delta === expected}));
"""
    r = json.loads(_run_js_race(script))
    assert r["match"] is True


def test_run_one_race_balance_zero():
    script = """
const horses = [{rank:1,odds:2.0,name:"A"},{rank:2,odds:3.0,name:"B"}];
const r = runOneRace({balance:100, horses, bet:{horseIndex:1, amount:100}});
console.log(JSON.stringify(r));
"""
    r = json.loads(_run_js_race(script))
    assert r["won"] is False
    assert r["delta"] == -100
    assert r["newBalance"] == 0


def test_run_one_race_winner_identity():
    script = """
const horses = [{rank:1,odds:2.5,name:"Thunder"},{rank:2,odds:3.0,name:"Mystic"}];
const r = runOneRace({balance:1000, horses, bet:{horseIndex:1, amount:100}});
console.log(JSON.stringify({name:r.winner.name, odds:r.winner.odds, rank:r.winner.rank}));
"""
    r = json.loads(_run_js_race(script))
    assert r["name"] == "Thunder"
    assert r["odds"] == 2.5
    assert r["rank"] == 1


# ── T8: initApp ───────────────────────────────────────────────────────────────

def _run_js_init(script: str) -> str:
    MAIN_P = MAIN.as_posix()
    MODEL_P = (ROOT / "src" / "model.js").as_posix()
    UI_P = (ROOT / "src" / "ui.js").as_posix()
    RACE_P = (ROOT / "src" / "race.js").as_posix()

    preamble = (
        f'import {{ initApp }} from "{MAIN_P}";\n'
        f'import {{ createHorses }} from "{MODEL_P}";\n'
        f'import {{ formatBalance, formatOddsLabel, formatResultMessage }} from "{UI_P}";\n'
        f'import {{ simulateRace }} from "{RACE_P}";\n'
    )

    helpers = r"""
function makeRng(seed) {
  let s = seed;
  return () => { s = (s * 9301 + 49297) % 233280; return s / 233280; };
}

function makeDoc(options) {
  options = options || {};
  const store = {};
  function el(key) {
    if (!store[key]) {
      store[key] = { textContent: "", disabled: false, hidden: key === "result-modal" || key === "game-over-modal", value: "", checked: false, _handlers: {}, style: {} };
      store[key].addEventListener = (t, fn) => { store[key]._handlers[t] = fn; };
      store[key]._fire = (t) => { if (store[key]._handlers[t]) store[key]._handlers[t](); };
    }
    return store[key];
  }
  return {
    _el: el,
    querySelector(sel) {
      if (sel === "#balance") return el("balance");
      if (sel === "#start-btn") return el("start-btn");
      if (sel === "#bet-amount") return el("bet-amount");
      if (sel === "#result-message") return el("result-message");
      if (sel === "#result-modal") return el("result-modal");
      if (sel === "#next-race-btn") return el("next-race-btn");
      if (sel === "#mute-btn") return el("mute-btn");
      if (sel === "#game-over-modal") return el("game-over-modal");
      if (sel === "#game-over-message") return el("game-over-message");
      if (sel === "#restart-btn") return el("restart-btn");
      if (sel === "#bet-hint") return el("bet-hint");
      if (sel === 'input[name="horse"]:checked') return options.checkedHorse || null;
      const m = sel.match(/\.lane\[data-horse="([^"]+)"\] \.lane-label/);
      if (m) return el("ll-" + m[1]);
      const m2 = sel.match(/\.lane\[data-horse="([^"]+)"\] \.horse/);
      if (m2) return el("horse-" + m2[1]);
      return null;
    }
  };
}
"""

    storageHelper = r"""
function makeStorage(initial) {
  const data = Object.assign({}, initial || {});
  const calls = [];
  return {
    getItem(key) {
      calls.push(["get", key]);
      return Object.prototype.hasOwnProperty.call(data, key) ? data[key] : null;
    },
    setItem(key, value) {
      calls.push(["set", key, String(value)]);
      data[key] = String(value);
    },
    _data: data,
    _calls: calls,
  };
}
"""

    audioCtxHelper = r"""
function makeAudioCtx() {
  const events = [];
  const ctx = {
    currentTime: 0,
    destination: { __tag: "destination" },
    createOscillator() {
      events.push(["createOscillator"]);
      return {
        type: null,
        frequency: { setValueAtTime: (v, t) => events.push(["freq", v]) },
        connect: () => {},
        start: () => {},
        stop: () => {},
      };
    },
    createGain() {
      events.push(["createGain"]);
      return {
        __tag: "gain",
        gain: {
          setValueAtTime: () => {},
          linearRampToValueAtTime: () => {},
        },
        connect: () => {},
      };
    },
  };
  return { ctx, events };
}
"""
    full = preamble + helpers + storageHelper + audioCtxHelper + "\n" + script
    result = subprocess.run(
        ["node", "--input-type=module"],
        input=full,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, f"node error:\n{result.stderr}"
    return result.stdout.strip()


def test_init_app_export_exists():
    out = _run_js_init("console.log(typeof initApp);")
    assert out == "function"


def test_init_app_initial_balance():
    script = """
const doc = makeDoc();
initApp(doc, { rng: makeRng(42), initialBalance: 1000 });
console.log(doc._el("balance").textContent);
"""
    out = _run_js_init(script)
    assert out == "잔고: 1000"


def test_init_app_initial_lane_labels():
    script = """
const rng1 = makeRng(42);
const rng2 = makeRng(42);
const doc = makeDoc();
initApp(doc, { rng: rng1, initialBalance: 1000 });
const horses = createHorses(rng2);
const names = ["Thunder", "Mystic", "Golden", "Emerald", "Shadow"];
const allMatch = names.every((name, i) => {
  return doc._el("ll-" + name).textContent === formatOddsLabel(horses[i]);
});
console.log(allMatch ? "ok" : "fail");
"""
    out = _run_js_init(script)
    assert out == "ok"


def test_init_app_start_win():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const winner = simulated.find(h => h.rank === 1);
const expectedBalance = 1000 + Math.round(100 * (winner.odds - 1));

const doc = makeDoc({ checkedHorse: { value: winner.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), initialBalance: 1000, requestAnimationFrame: fakeRaf, now: fakeNow });
doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");
fakeTime = 1000;
while (queue.length > 0) { queue.shift()(); }

console.log(JSON.stringify({
  modalVisible: doc._el("result-modal").hidden === false,
  message: doc._el("result-message").textContent,
  balanceText: doc._el("balance").textContent,
  expectedBalance
}));
"""
    r = json.loads(_run_js_init(script))
    assert r["modalVisible"] is True
    assert "적중!" in r["message"]
    assert r["balanceText"] == f"잔고: {r['expectedBalance']}"


def test_init_app_start_btn_disabled():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const winner = simulated.find(h => h.rank === 1);

const doc = makeDoc({ checkedHorse: { value: winner.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), initialBalance: 1000, requestAnimationFrame: fakeRaf, now: fakeNow });
doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");
fakeTime = 1000;
while (queue.length > 0) { queue.shift()(); }
console.log(doc._el("start-btn").disabled ? "ok" : "fail");
"""
    out = _run_js_init(script)
    assert out == "ok"


def test_init_app_invalid_bet_silent():
    script = """
// Case A: no radio selected
const doc1 = makeDoc();
initApp(doc1, { rng: makeRng(42), initialBalance: 1000 });
doc1._el("bet-amount").value = "100";
doc1._el("start-btn")._fire("click");
const noRadio = doc1._el("result-modal").hidden === true && doc1._el("balance").textContent === "잔고: 1000";

// Case B: amount below minimum
const predRng = makeRng(42);
const horses = createHorses(predRng);
const doc2 = makeDoc({ checkedHorse: { value: horses[0].name } });
initApp(doc2, { rng: makeRng(42), initialBalance: 1000 });
doc2._el("bet-amount").value = "5";
doc2._el("start-btn")._fire("click");
const belowMin = doc2._el("result-modal").hidden === true && doc2._el("balance").textContent === "잔고: 1000";

console.log(noRadio && belowMin ? "ok" : "fail");
"""
    out = _run_js_init(script)
    assert out == "ok"


def test_init_app_start_loss():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const loser = simulated.find(h => h.rank !== 1);

const doc = makeDoc({ checkedHorse: { value: loser.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), initialBalance: 1000, requestAnimationFrame: fakeRaf, now: fakeNow });
doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");
fakeTime = 1000;
while (queue.length > 0) { queue.shift()(); }

console.log(JSON.stringify({
  message: doc._el("result-message").textContent,
  balanceText: doc._el("balance").textContent,
  expectedBalance: 900
}));
"""
    r = json.loads(_run_js_init(script))
    assert "실패." in r["message"]
    assert r["balanceText"] == "잔고: 900"
    assert r["expectedBalance"] == 900


def test_init_app_next_race_modal_close():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const winner = simulated.find(h => h.rank === 1);

const doc = makeDoc({ checkedHorse: { value: winner.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), initialBalance: 1000, requestAnimationFrame: fakeRaf, now: fakeNow });
doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");
fakeTime = 1000;
while (queue.length > 0) { queue.shift()(); }
doc._el("next-race-btn")._fire("click");

console.log(JSON.stringify({
  modalHidden: doc._el("result-modal").hidden,
  startEnabled: !doc._el("start-btn").disabled
}));
"""
    r = json.loads(_run_js_init(script))
    assert r["modalHidden"] is True
    assert r["startEnabled"] is True


def test_init_app_next_race_labels_updated():
    script = """
const seqRng = makeRng(42);
const horses1 = createHorses(seqRng);
const simulated = simulateRace(horses1, { rng: seqRng });
const horses2 = createHorses(seqRng);

const winner = simulated.find(h => h.rank === 1);
const doc = makeDoc({ checkedHorse: { value: winner.name } });
initApp(doc, { rng: makeRng(42), initialBalance: 1000 });
doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");
doc._el("next-race-btn")._fire("click");

const names = ["Thunder", "Mystic", "Golden", "Emerald", "Shadow"];
const allMatch = names.every((name, i) => {
  return doc._el("ll-" + name).textContent === formatOddsLabel(horses2[i]);
});
const anyDiff = names.some((name, i) => {
  return formatOddsLabel(horses1[i]) !== formatOddsLabel(horses2[i]);
});
console.log(JSON.stringify({ allMatch, anyDiff }));
"""
    r = json.loads(_run_js_init(script))
    assert r["allMatch"] is True
    assert r["anyDiff"] is True


# ── T9: rAF 애니메이션 루프 ──────────────────────────────────────────────────────

def test_t9_modal_hidden_before_raf():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const winner = simulated.find(h => h.rank === 1);

const doc = makeDoc({ checkedHorse: { value: winner.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), initialBalance: 1000, requestAnimationFrame: fakeRaf, now: fakeNow });
doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");

console.log(doc._el("result-modal").hidden === true ? "ok" : "fail");
"""
    out = _run_js_init(script)
    assert out == "ok"


def test_t9_raf_initial_queue():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const winner = simulated.find(h => h.rank === 1);

const doc = makeDoc({ checkedHorse: { value: winner.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), initialBalance: 1000, requestAnimationFrame: fakeRaf, now: fakeNow });
doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");

console.log(queue.length === 1 ? "ok" : "fail:" + queue.length);
"""
    out = _run_js_init(script)
    assert out == "ok"


def test_t9_position_updated_mid_race():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const winner = simulated.find(h => h.rank === 1);
const totalDuration = Math.max(...simulated.map(h => h.finishTime));

const doc = makeDoc({ checkedHorse: { value: winner.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), initialBalance: 1000, requestAnimationFrame: fakeRaf, now: fakeNow });
doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");

fakeTime = totalDuration / 2;
queue.shift()();

const names = ["Thunder", "Mystic", "Golden", "Emerald", "Shadow"];
const allInRange = names.every(name => {
  const pct = parseFloat(doc._el("horse-" + name).style.left);
  return pct > 0 && pct <= 100;
});
console.log(allInRange ? "ok" : "fail");
"""
    out = _run_js_init(script)
    assert out == "ok"


def test_t9_modal_shown_after_loop():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const winner = simulated.find(h => h.rank === 1);
const totalDuration = Math.max(...simulated.map(h => h.finishTime));

const doc = makeDoc({ checkedHorse: { value: winner.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), initialBalance: 1000, requestAnimationFrame: fakeRaf, now: fakeNow });
doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");

fakeTime = totalDuration + 1;
while (queue.length > 0) { queue.shift()(); }

const msg = doc._el("result-message").textContent;
console.log(JSON.stringify({
  modalVisible: doc._el("result-modal").hidden === false,
  hasResult: msg.includes("적중!") || msg.includes("실패.")
}));
"""
    r = json.loads(_run_js_init(script))
    assert r["modalVisible"] is True
    assert r["hasResult"] is True


def test_t9_balance_updated_after_loop():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const winner = simulated.find(h => h.rank === 1);
const totalDuration = Math.max(...simulated.map(h => h.finishTime));

const doc = makeDoc({ checkedHorse: { value: winner.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), initialBalance: 1000, requestAnimationFrame: fakeRaf, now: fakeNow });
doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");

const balanceBefore = doc._el("balance").textContent;

fakeTime = totalDuration + 1;
while (queue.length > 0) { queue.shift()(); }

const balanceAfter = doc._el("balance").textContent;
console.log(JSON.stringify({ balanceBefore, changed: balanceBefore !== balanceAfter }));
"""
    r = json.loads(_run_js_init(script))
    assert r["balanceBefore"] == "잔고: 1000"
    assert r["changed"] is True


def test_t9_no_double_start():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const winner = simulated.find(h => h.rank === 1);

const doc = makeDoc({ checkedHorse: { value: winner.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), initialBalance: 1000, requestAnimationFrame: fakeRaf, now: fakeNow });
doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");

const queueAfterFirst = queue.length;
doc._el("start-btn")._fire("click");
const queueAfterSecond = queue.length;

console.log(JSON.stringify({
  queueAfterFirst,
  queueAfterSecond,
  notDoubled: queueAfterSecond === queueAfterFirst
}));
"""
    r = json.loads(_run_js_init(script))
    assert r["queueAfterFirst"] == 1
    assert r["notDoubled"] is True


def test_t9_next_race_after_loop():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const winner = simulated.find(h => h.rank === 1);
const totalDuration = Math.max(...simulated.map(h => h.finishTime));

const doc = makeDoc({ checkedHorse: { value: winner.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), initialBalance: 1000, requestAnimationFrame: fakeRaf, now: fakeNow });
doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");

fakeTime = totalDuration + 1;
while (queue.length > 0) { queue.shift()(); }

doc._el("next-race-btn")._fire("click");
doc._el("start-btn")._fire("click");

console.log(queue.length >= 1 ? "ok" : "fail:" + queue.length);
"""
    out = _run_js_init(script)
    assert out == "ok"


# ── T11: 사운드 와이어링 ──────────────────────────────────────────────────────────

def test_t11_mute_btn_handler_registered():
    script = """
const { ctx, events } = makeAudioCtx();
const doc = makeDoc();
initApp(doc, { rng: makeRng(42), initialBalance: 1000, audioContext: ctx });
console.log(typeof doc._el("mute-btn")._handlers.click === "function" ? "ok" : "fail");
"""
    out = _run_js_init(script)
    assert out == "ok"


def test_t11_mute_once_icon_and_no_sound():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const winner = simulated.find(h => h.rank === 1);
const totalDuration = Math.max(...simulated.map(h => h.finishTime));

const { ctx, events } = makeAudioCtx();
const doc = makeDoc({ checkedHorse: { value: winner.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), initialBalance: 1000, requestAnimationFrame: fakeRaf, now: fakeNow, audioContext: ctx });

doc._el("mute-btn")._fire("click");
const iconAfterMute = doc._el("mute-btn").textContent;

doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");
fakeTime = totalDuration + 1;
while (queue.length > 0) { queue.shift()(); }

const freqCount = events.filter(e => e[0] === "freq").length;
console.log(JSON.stringify({ iconAfterMute, freqCount }));
"""
    r = json.loads(_run_js_init(script))
    assert r["iconAfterMute"] == "🔇"
    assert r["freqCount"] == 0


def test_t11_mute_twice_icon_restored_and_sound_plays():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const winner = simulated.find(h => h.rank === 1);
const totalDuration = Math.max(...simulated.map(h => h.finishTime));

const { ctx, events } = makeAudioCtx();
const doc = makeDoc({ checkedHorse: { value: winner.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), initialBalance: 1000, requestAnimationFrame: fakeRaf, now: fakeNow, audioContext: ctx });

doc._el("mute-btn")._fire("click");
doc._el("mute-btn")._fire("click");
const iconAfterDouble = doc._el("mute-btn").textContent;

doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");
fakeTime = totalDuration + 1;
while (queue.length > 0) { queue.shift()(); }

const freqCount = events.filter(e => e[0] === "freq").length;
console.log(JSON.stringify({ iconAfterDouble, enoughFreq: freqCount >= 3 }));
"""
    r = json.loads(_run_js_init(script))
    assert r["iconAfterDouble"] == "🔊"
    assert r["enoughFreq"] is True


def test_t11_play_start_on_click():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const winner = simulated.find(h => h.rank === 1);

const { ctx, events } = makeAudioCtx();
const doc = makeDoc({ checkedHorse: { value: winner.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), initialBalance: 1000, requestAnimationFrame: fakeRaf, now: fakeNow, audioContext: ctx });
doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");

const freq880Count = events.filter(e => e[0] === "freq" && e[1] === 880).length;
console.log(JSON.stringify({ freq880Count }));
"""
    r = json.loads(_run_js_init(script))
    assert r["freq880Count"] == 1


def test_t11_win_path_sounds():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const winner = simulated.find(h => h.rank === 1);
const totalDuration = Math.max(...simulated.map(h => h.finishTime));

const { ctx, events } = makeAudioCtx();
const doc = makeDoc({ checkedHorse: { value: winner.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), initialBalance: 1000, requestAnimationFrame: fakeRaf, now: fakeNow, audioContext: ctx });
doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");
fakeTime = totalDuration + 1;
while (queue.length > 0) { queue.shift()(); }

const freqs = events.filter(e => e[0] === "freq").map(e => e[1]);
console.log(JSON.stringify({
  has880: freqs.filter(f => f === 880).length >= 1,
  has660: freqs.filter(f => f === 660).length >= 1,
  has988: freqs.filter(f => f === 988).length >= 1,
  no220: freqs.filter(f => f === 220).length === 0
}));
"""
    r = json.loads(_run_js_init(script))
    assert r["has880"] is True
    assert r["has660"] is True
    assert r["has988"] is True
    assert r["no220"] is True


def test_t11_loss_path_sounds():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const loser = simulated.find(h => h.rank !== 1);
const totalDuration = Math.max(...simulated.map(h => h.finishTime));

const { ctx, events } = makeAudioCtx();
const doc = makeDoc({ checkedHorse: { value: loser.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), initialBalance: 1000, requestAnimationFrame: fakeRaf, now: fakeNow, audioContext: ctx });
doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");
fakeTime = totalDuration + 1;
while (queue.length > 0) { queue.shift()(); }

const freqs = events.filter(e => e[0] === "freq").map(e => e[1]);
console.log(JSON.stringify({
  has880: freqs.filter(f => f === 880).length >= 1,
  has660: freqs.filter(f => f === 660).length >= 1,
  has220: freqs.filter(f => f === 220).length >= 1,
  no988: freqs.filter(f => f === 988).length === 0
}));
"""
    r = json.loads(_run_js_init(script))
    assert r["has880"] is True
    assert r["has660"] is True
    assert r["has220"] is True
    assert r["no988"] is True


def test_t11_invalid_bet_no_sound():
    script = """
const { ctx, events } = makeAudioCtx();
const doc = makeDoc();
initApp(doc, { rng: makeRng(42), initialBalance: 1000, audioContext: ctx });
doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");

const freqCount = events.filter(e => e[0] === "freq").length;
console.log(freqCount === 0 ? "ok" : "fail:" + freqCount);
"""
    out = _run_js_init(script)
    assert out == "ok"


def test_t11_null_audio_context_no_throw():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const winner = simulated.find(h => h.rank === 1);
const totalDuration = Math.max(...simulated.map(h => h.finishTime));

const doc = makeDoc({ checkedHorse: { value: winner.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), initialBalance: 1000, requestAnimationFrame: fakeRaf, now: fakeNow, audioContext: null });
doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");
fakeTime = totalDuration + 1;
while (queue.length > 0) { queue.shift()(); }
doc._el("mute-btn")._fire("click");

console.log("ok");
"""
    out = _run_js_init(script)
    assert out == "ok"


# ── T13: storage 와이어링 ─────────────────────────────────────────────────────────

def test_t13_storage_balance_restored():
    script = """
const storage = makeStorage({ balance: "750" });
const doc = makeDoc();
initApp(doc, { rng: makeRng(42), storage });
console.log(doc._el("balance").textContent);
"""
    out = _run_js_init(script)
    assert out == "잔고: 750"


def test_t13_storage_muted_icon_and_no_sound():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const winner = simulated.find(h => h.rank === 1);
const totalDuration = Math.max(...simulated.map(h => h.finishTime));

const storage = makeStorage({ muted: "1" });
const { ctx, events } = makeAudioCtx();
const doc = makeDoc({ checkedHorse: { value: winner.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), initialBalance: 1000, requestAnimationFrame: fakeRaf, now: fakeNow, audioContext: ctx, storage });

const iconAfterInit = doc._el("mute-btn").textContent;

doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");
fakeTime = totalDuration + 1;
while (queue.length > 0) { queue.shift()(); }

const freqCount = events.filter(e => e[0] === "freq").length;
console.log(JSON.stringify({ iconAfterInit, freqCount }));
"""
    r = json.loads(_run_js_init(script))
    assert r["iconAfterInit"] == "🔇"
    assert r["freqCount"] == 0


def test_t13_storage_muted_zero_icon():
    script = """
const storage = makeStorage({ muted: "0" });
const doc = makeDoc();
initApp(doc, { rng: makeRng(42), initialBalance: 1000, storage });
console.log(doc._el("mute-btn").textContent);
"""
    out = _run_js_init(script)
    assert out == "🔊"


def test_t13_save_balance_on_finish():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const winner = simulated.find(h => h.rank === 1);
const totalDuration = Math.max(...simulated.map(h => h.finishTime));

const storage = makeStorage();
const doc = makeDoc({ checkedHorse: { value: winner.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), initialBalance: 1000, requestAnimationFrame: fakeRaf, now: fakeNow, storage });
doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");
fakeTime = totalDuration + 1;
while (queue.length > 0) { queue.shift()(); }

const balanceText = doc._el("balance").textContent;
const storedBalance = storage._data.balance;
const hasSetCall = storage._calls.some(c => c[0] === "set" && c[1] === "balance");
console.log(JSON.stringify({ balanceText, storedBalance, hasSetCall }));
"""
    r = json.loads(_run_js_init(script))
    assert r["balanceText"] == f"잔고: {r['storedBalance']}"
    assert r["hasSetCall"] is True


def test_t13_save_muted_on_click():
    script = """
const storage = makeStorage();
const { ctx, events } = makeAudioCtx();
const doc = makeDoc();
initApp(doc, { rng: makeRng(42), initialBalance: 1000, audioContext: ctx, storage });

doc._el("mute-btn")._fire("click");
const afterOne = storage._data.muted;

doc._el("mute-btn")._fire("click");
const afterTwo = storage._data.muted;

console.log(JSON.stringify({ afterOne, afterTwo }));
"""
    r = json.loads(_run_js_init(script))
    assert r["afterOne"] == "1"
    assert r["afterTwo"] == "0"


def test_t13_initial_balance_takes_priority():
    script = """
const storage = makeStorage({ balance: "999" });
const doc = makeDoc();
initApp(doc, { rng: makeRng(42), initialBalance: 500, storage });
console.log(doc._el("balance").textContent);
"""
    out = _run_js_init(script)
    assert out == "잔고: 500"


def test_t13_null_storage_fallback_no_throw():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const winner = simulated.find(h => h.rank === 1);
const totalDuration = Math.max(...simulated.map(h => h.finishTime));

const doc = makeDoc({ checkedHorse: { value: winner.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), requestAnimationFrame: fakeRaf, now: fakeNow, storage: null });
const balanceText = doc._el("balance").textContent;

doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");
fakeTime = totalDuration + 1;
while (queue.length > 0) { queue.shift()(); }
doc._el("mute-btn")._fire("click");

console.log(JSON.stringify({ balanceText }));
"""
    r = json.loads(_run_js_init(script))
    assert r["balanceText"] == "잔고: 1000"


# ── T14: 게임 오버 화면 + 재시작 ─────────────────────────────────────────────────

def test_t14_normal_finish_shows_result_modal_only():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const winner = simulated.find(h => h.rank === 1);
const totalDuration = Math.max(...simulated.map(h => h.finishTime));

const doc = makeDoc({ checkedHorse: { value: winner.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), initialBalance: 1000, requestAnimationFrame: fakeRaf, now: fakeNow });
doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");
fakeTime = totalDuration + 1;
while (queue.length > 0) { queue.shift()(); }

console.log(JSON.stringify({
  resultVisible: doc._el("result-modal").hidden === false,
  gameOverHidden: doc._el("game-over-modal").hidden === true
}));
"""
    r = json.loads(_run_js_init(script))
    assert r["resultVisible"] is True
    assert r["gameOverHidden"] is True


def test_t14_low_balance_shows_game_over_modal_only():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const loser = simulated.find(h => h.rank !== 1);
const totalDuration = Math.max(...simulated.map(h => h.finishTime));

const doc = makeDoc({ checkedHorse: { value: loser.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), initialBalance: 100, requestAnimationFrame: fakeRaf, now: fakeNow });
doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");
fakeTime = totalDuration + 1;
while (queue.length > 0) { queue.shift()(); }

const expectedMsg = formatResultMessage({ won: false, delta: -100, winner: simulated.find(h => h.rank === 1) });
console.log(JSON.stringify({
  gameOverVisible: doc._el("game-over-modal").hidden === false,
  resultHidden: doc._el("result-modal").hidden === true,
  msgMatch: doc._el("game-over-message").textContent === expectedMsg
}));
"""
    r = json.loads(_run_js_init(script))
    assert r["gameOverVisible"] is True
    assert r["resultHidden"] is True
    assert r["msgMatch"] is True


def test_t14_balance_below_threshold_triggers_game_over():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const loser = simulated.find(h => h.rank !== 1);
const totalDuration = Math.max(...simulated.map(h => h.finishTime));

const doc = makeDoc({ checkedHorse: { value: loser.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), initialBalance: 109, requestAnimationFrame: fakeRaf, now: fakeNow });
doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");
fakeTime = totalDuration + 1;
while (queue.length > 0) { queue.shift()(); }

console.log(JSON.stringify({
  gameOverVisible: doc._el("game-over-modal").hidden === false,
  resultHidden: doc._el("result-modal").hidden === true
}));
"""
    r = json.loads(_run_js_init(script))
    assert r["gameOverVisible"] is True
    assert r["resultHidden"] is True


def test_t14_balance_at_threshold_no_game_over():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const loser = simulated.find(h => h.rank !== 1);
const totalDuration = Math.max(...simulated.map(h => h.finishTime));

const doc = makeDoc({ checkedHorse: { value: loser.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), initialBalance: 110, requestAnimationFrame: fakeRaf, now: fakeNow });
doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");
fakeTime = totalDuration + 1;
while (queue.length > 0) { queue.shift()(); }

console.log(JSON.stringify({
  resultVisible: doc._el("result-modal").hidden === false,
  gameOverHidden: doc._el("game-over-modal").hidden === true
}));
"""
    r = json.loads(_run_js_init(script))
    assert r["resultVisible"] is True
    assert r["gameOverHidden"] is True


def test_t14_restart_resets_state():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const loser = simulated.find(h => h.rank !== 1);
const totalDuration = Math.max(...simulated.map(h => h.finishTime));

const storage = makeStorage();
const doc = makeDoc({ checkedHorse: { value: loser.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), initialBalance: 100, requestAnimationFrame: fakeRaf, now: fakeNow, storage });
doc._el("bet-amount").value = "100";
doc._el("start-btn")._fire("click");
fakeTime = totalDuration + 1;
while (queue.length > 0) { queue.shift()(); }

doc._el("restart-btn")._fire("click");

const names = ["Thunder", "Mystic", "Golden", "Emerald", "Shadow"];
const labelsNonEmpty = names.every(name => doc._el("ll-" + name).textContent.length > 0);

console.log(JSON.stringify({
  balanceText: doc._el("balance").textContent,
  resultHidden: doc._el("result-modal").hidden === true,
  gameOverHidden: doc._el("game-over-modal").hidden === true,
  startEnabled: doc._el("start-btn").disabled === false,
  storageBalance: storage._data.balance,
  labelsNonEmpty
}));
"""
    r = json.loads(_run_js_init(script))
    assert r["balanceText"] == "잔고: 1000"
    assert r["resultHidden"] is True
    assert r["gameOverHidden"] is True
    assert r["startEnabled"] is True
    assert r["storageBalance"] == "1000"
    assert r["labelsNonEmpty"] is True


def test_t14_restart_clears_storage_consistently():
    script = """
const storage = makeStorage({ balance: "5" });
const doc = makeDoc();
initApp(doc, { rng: makeRng(42), storage });

const balanceAfterInit = doc._el("balance").textContent;
const gameOverAfterInit = doc._el("game-over-modal").hidden;

doc._el("restart-btn")._fire("click");

console.log(JSON.stringify({
  balanceAfterInit,
  gameOverAfterInit,
  storageAfterRestart: storage._data.balance,
  balanceAfterRestart: doc._el("balance").textContent
}));
"""
    r = json.loads(_run_js_init(script))
    assert r["balanceAfterInit"] == "잔고: 5"
    assert r["gameOverAfterInit"] is True
    assert r["storageAfterRestart"] == "1000"
    assert r["balanceAfterRestart"] == "잔고: 1000"


# ── T15: validateBet 실패 UX (#bet-hint / formatBetHint) ─────────────────────────

def test_t15_below_min_shows_bet_hint():
    script = """
const predRng = makeRng(42);
const horses = createHorses(predRng);

const doc = makeDoc({ checkedHorse: { value: horses[0].name } });
initApp(doc, { rng: makeRng(42), initialBalance: 1000 });
doc._el("bet-amount").value = "5";
doc._el("start-btn")._fire("click");

console.log(JSON.stringify({
  hintHidden: doc._el("bet-hint").hidden,
  hintText: doc._el("bet-hint").textContent,
  startDisabled: doc._el("start-btn").disabled,
  running: false
}));
"""
    r = json.loads(_run_js_init(script))
    assert r["hintHidden"] is False
    assert r["hintText"] == "최소 베팅 금액은 10입니다."
    assert r["startDisabled"] is False


def test_t15_exceeds_balance_shows_bet_hint():
    script = """
const predRng = makeRng(42);
const horses = createHorses(predRng);

const doc = makeDoc({ checkedHorse: { value: horses[0].name } });
initApp(doc, { rng: makeRng(42), initialBalance: 100 });
doc._el("bet-amount").value = "200";
doc._el("start-btn")._fire("click");

console.log(JSON.stringify({
  hintHidden: doc._el("bet-hint").hidden,
  hintText: doc._el("bet-hint").textContent,
  startDisabled: doc._el("start-btn").disabled
}));
"""
    r = json.loads(_run_js_init(script))
    assert r["hintHidden"] is False
    assert r["hintText"] == "베팅 금액이 현재 잔고를 초과합니다."
    assert r["startDisabled"] is False


def test_t15_invalid_amount_shows_bet_hint():
    script = """
const predRng = makeRng(42);
const horses = createHorses(predRng);

const doc = makeDoc({ checkedHorse: { value: horses[0].name } });
initApp(doc, { rng: makeRng(42), initialBalance: 1000 });
doc._el("bet-amount").value = "abc";
doc._el("start-btn")._fire("click");

console.log(JSON.stringify({
  hintHidden: doc._el("bet-hint").hidden,
  hintText: doc._el("bet-hint").textContent
}));
"""
    r = json.loads(_run_js_init(script))
    assert r["hintHidden"] is False
    assert r["hintText"] == "베팅 금액을 정수로 입력하세요."


def test_t15_hint_clears_on_next_valid_start():
    script = """
const predRng = makeRng(42);
const predHorses = createHorses(predRng);
const simulated = simulateRace(predHorses, { rng: predRng });
const winner = simulated.find(h => h.rank === 1);

const doc = makeDoc({ checkedHorse: { value: winner.name } });
let queue = [];
const fakeRaf = cb => { queue.push(cb); return queue.length; };
let fakeTime = 0;
const fakeNow = () => fakeTime;
initApp(doc, { rng: makeRng(42), initialBalance: 1000, requestAnimationFrame: fakeRaf, now: fakeNow });

// 1차 시도: BELOW_MIN -> hint 노출
doc._el("bet-amount").value = "5";
doc._el("start-btn")._fire("click");
const hintAfterFail = doc._el("bet-hint").textContent;

// 2차 시도: 유효 베팅 -> hint 클리어 + 레이스 시작
doc._el("bet-amount").value = "10";
doc._el("start-btn")._fire("click");

console.log(JSON.stringify({
  hintAfterFail,
  hintHiddenAfterValid: doc._el("bet-hint").hidden,
  hintTextAfterValid: doc._el("bet-hint").textContent,
  running: queue.length >= 1
}));
"""
    r = json.loads(_run_js_init(script))
    assert r["hintAfterFail"] == "최소 베팅 금액은 10입니다."
    assert r["hintHiddenAfterValid"] is True
    assert r["hintTextAfterValid"] == ""
    assert r["running"] is True
