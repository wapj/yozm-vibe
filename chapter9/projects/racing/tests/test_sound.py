"""T10 acceptance tests: src/sound.js — createSoundEngine factory."""
import json
import subprocess
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SOUND = ROOT / "src" / "sound.js"

MOCK_CTX = """
function makeAudioContext() {
  const events = [];
  const ctx = {
    currentTime: 0,
    destination: { __tag: "destination" },
    createOscillator() {
      const osc = {
        type: null,
        frequency: {
          setValueAtTime: (v, t) => events.push(["osc.frequency.setValueAtTime", v, t]),
        },
        connect: (node) => events.push(["osc.connect", node.__tag ?? "gain"]),
        start: (t) => events.push(["osc.start", t]),
        stop: (t) => events.push(["osc.stop", t]),
      };
      events.push(["createOscillator"]);
      return osc;
    },
    createGain() {
      const gain = {
        __tag: "gain",
        gain: {
          setValueAtTime: (v, t) => events.push(["gain.gain.setValueAtTime", v, t]),
          linearRampToValueAtTime: (v, t) => events.push(["gain.gain.linearRamp", v, t]),
        },
        connect: (node) => events.push(["gain.connect", node.__tag ?? "destination"]),
      };
      events.push(["createGain"]);
      return gain;
    },
  };
  return { ctx, events };
}
"""


def _run_js(script: str) -> str:
    full = (
        f'import {{ createSoundEngine }} from "{SOUND.as_posix()}";\n'
        + MOCK_CTX
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


def test_sound_file_exists():
    assert SOUND.exists(), "src/sound.js가 없습니다"


# 1. export 표면
def test_export_surface():
    out = _run_js("""
import * as mod from "%s";
console.log(JSON.stringify(Object.keys(mod)));
""".replace("%s", SOUND.as_posix()))
    keys = json.loads(out)
    assert keys == ["createSoundEngine"], f"export 키 목록 불일치: {keys}"


# 2. 반환 객체 표면
def test_return_surface():
    out = _run_js("""
const { ctx } = makeAudioContext();
const engine = createSoundEngine(ctx);
console.log(JSON.stringify(Object.keys(engine).sort()));
""")
    keys = json.loads(out)
    expected = sorted(["playStart", "playFinish", "playWin", "playLoss", "setMuted", "isMuted"])
    assert keys == expected, f"반환 객체 키 불일치: {keys}"


# 3. 초기 mute 상태
def test_initial_mute_false():
    out = _run_js("""
const { ctx } = makeAudioContext();
const engine = createSoundEngine(ctx);
console.log(engine.isMuted());
""")
    assert out == "false"


# 4. setMuted 토글
def test_set_muted_toggle():
    out = _run_js("""
const { ctx } = makeAudioContext();
const engine = createSoundEngine(ctx);
engine.setMuted(true);
const a = engine.isMuted();
engine.setMuted(false);
const b = engine.isMuted();
engine.setMuted(1);
const c = engine.isMuted();
engine.setMuted("");
const d = engine.isMuted();
console.log(JSON.stringify([a, b, c, d]));
""")
    assert json.loads(out) == [True, False, True, False]


# 5. playStart 합성 시퀀스
def test_play_start_sequence():
    out = _run_js("""
const { ctx, events } = makeAudioContext();
const engine = createSoundEngine(ctx);
engine.playStart();
console.log(JSON.stringify(events));
""")
    events = json.loads(out)
    event_names = [e[0] for e in events]
    expected_order = [
        "createOscillator",
        "createGain",
        "osc.frequency.setValueAtTime",
        "gain.gain.setValueAtTime",
        "gain.gain.linearRamp",
        "gain.gain.linearRamp",
        "osc.connect",
        "gain.connect",
        "osc.start",
        "osc.stop",
    ]
    # check frequency value is 880
    freq_events = [e for e in events if e[0] == "osc.frequency.setValueAtTime"]
    assert len(freq_events) == 1 and freq_events[0][1] == 880
    # check partial order
    indices = []
    for name in expected_order:
        for i, e in enumerate(events):
            if e[0] == name and i not in indices:
                indices.append(i)
                break
    assert indices == sorted(indices), f"이벤트 순서 불일치: {event_names}"
    # check osc.connect goes to gain
    osc_connects = [e for e in events if e[0] == "osc.connect"]
    assert osc_connects[0][1] == "gain"
    # check gain.connect goes to destination
    gain_connects = [e for e in events if e[0] == "gain.connect"]
    assert gain_connects[0][1] == "destination"


# 6. playFinish 주파수
def test_play_finish_freq():
    out = _run_js("""
const { ctx, events } = makeAudioContext();
const engine = createSoundEngine(ctx);
engine.playFinish();
const freq_event = events.find(e => e[0] === "osc.frequency.setValueAtTime");
console.log(freq_event[1]);
""")
    assert float(out) == 660.0


# 7. playWin 주파수
def test_play_win_freq():
    out = _run_js("""
const { ctx, events } = makeAudioContext();
const engine = createSoundEngine(ctx);
engine.playWin();
const freq_event = events.find(e => e[0] === "osc.frequency.setValueAtTime");
console.log(freq_event[1]);
""")
    assert float(out) == 988.0


# 8. playLoss 주파수
def test_play_loss_freq():
    out = _run_js("""
const { ctx, events } = makeAudioContext();
const engine = createSoundEngine(ctx);
engine.playLoss();
const freq_event = events.find(e => e[0] === "osc.frequency.setValueAtTime");
console.log(freq_event[1]);
""")
    assert float(out) == 220.0


# 9. mute 시 no-op
def test_muted_no_op():
    out = _run_js("""
const { ctx, events } = makeAudioContext();
const engine = createSoundEngine(ctx);
engine.setMuted(true);
const before = events.length;
engine.playStart();
const after = events.length;
console.log(JSON.stringify([before, after, after === before]));
""")
    data = json.loads(out)
    assert data[2] is True, f"mute 상태에서 events가 늘었음: {data}"


# 10. audioContext null 시 no-op
def test_null_audio_context():
    out = _run_js("""
const engine = createSoundEngine(null);
engine.playStart();
engine.setMuted(true);
const m = engine.isMuted();
engine.setMuted(false);
const m2 = engine.isMuted();
console.log(JSON.stringify([m, m2]));
""")
    assert json.loads(out) == [True, False]


# 11. audioContext undefined 시 no-op
def test_undefined_audio_context():
    out = _run_js("""
const engine = createSoundEngine();
engine.playStart();
engine.playFinish();
console.log(engine.isMuted());
""")
    assert out == "false"


# 12. 연속 호출 독립성
def test_consecutive_calls_independence():
    out = _run_js("""
const { ctx, events } = makeAudioContext();
const engine = createSoundEngine(ctx);
engine.playStart();
engine.playFinish();
const freqs = events
  .filter(e => e[0] === "osc.frequency.setValueAtTime")
  .map(e => e[1]);
console.log(JSON.stringify(freqs));
""")
    freqs = json.loads(out)
    assert freqs.count(880) == 1, f"880Hz 호출 횟수 불일치: {freqs}"
    assert freqs.count(660) == 1, f"660Hz 호출 횟수 불일치: {freqs}"
