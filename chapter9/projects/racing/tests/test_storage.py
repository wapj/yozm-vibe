"""T12 acceptance tests: src/storage.js — localStorage 순수 함수 4종."""
import json
import subprocess
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
STORAGE = ROOT / "src" / "storage.js"

MOCK_STORAGE = """
function makeStorage(initial = {}) {
  const data = { ...initial };
  const calls = [];
  return {
    getItem(key) {
      calls.push(["get", key]);
      return Object.prototype.hasOwnProperty.call(data, key) ? data[key] : null;
    },
    setItem(key, value) {
      calls.push(["set", key, value]);
      data[key] = String(value);
    },
    _data: data,
    _calls: calls,
  };
}
"""


def _run_js(script: str) -> str:
    full = (
        f'import {{ loadBalance, saveBalance, loadMuted, saveMuted }} from "{STORAGE.as_posix()}";\n'
        + MOCK_STORAGE
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


def test_storage_file_exists():
    assert STORAGE.exists(), "src/storage.js가 없습니다"


# 1. export 표면
def test_export_surface():
    out = _run_js("""
import * as mod from "%s";
console.log(JSON.stringify(Object.keys(mod).sort()));
""".replace("%s", STORAGE.as_posix()))
    keys = json.loads(out)
    expected = sorted(["loadBalance", "saveBalance", "loadMuted", "saveMuted"])
    assert keys == expected, f"export 키 목록 불일치: {keys}"


# 2. loadBalance 키 부재
def test_load_balance_missing_key():
    out = _run_js("""
const storage = makeStorage();
console.log(loadBalance(storage));
""")
    assert int(out) == 1000


# 3. loadBalance 정수 복원
def test_load_balance_restore_integer():
    out = _run_js("""
const storage = makeStorage({ balance: "750" });
console.log(loadBalance(storage));
""")
    assert int(out) == 750


# 4. loadBalance NaN 방어
def test_load_balance_nan_defense():
    out = _run_js("""
const storage = makeStorage({ balance: "abc" });
console.log(loadBalance(storage));
""")
    assert int(out) == 1000


# 5. loadBalance 음수 방어
def test_load_balance_negative_defense():
    out = _run_js("""
const storage = makeStorage({ balance: "-50" });
console.log(loadBalance(storage));
""")
    assert int(out) == 1000


# 6. loadBalance falsy storage
def test_load_balance_falsy_storage():
    out = _run_js("""
const a = loadBalance(null);
const b = loadBalance(undefined);
console.log(JSON.stringify([a, b]));
""")
    data = json.loads(out)
    assert data == [1000, 1000], f"falsy storage 반환값 불일치: {data}"


# 7. saveBalance 정상 저장
def test_save_balance_normal():
    out = _run_js("""
const storage = makeStorage();
saveBalance(storage, 750);
console.log(storage._data.balance);
""")
    assert out == "750"


# 8. saveBalance 정수 절삭
def test_save_balance_trunc():
    out = _run_js("""
const storage = makeStorage();
saveBalance(storage, 750.9);
console.log(storage._data.balance);
""")
    assert out == "750"


# 9. saveBalance falsy storage
def test_save_balance_falsy_storage():
    out = _run_js("""
let threw = false;
try {
  saveBalance(null, 500);
} catch (e) {
  threw = true;
}
console.log(threw);
""")
    assert out == "false"


# 10. loadMuted 키 부재
def test_load_muted_missing_key():
    out = _run_js("""
const storage = makeStorage();
console.log(loadMuted(storage));
""")
    assert out == "false"


# 11. loadMuted "1" → true
def test_load_muted_one_is_true():
    out = _run_js("""
const storage = makeStorage({ muted: "1" });
console.log(loadMuted(storage));
""")
    assert out == "true"


# 12. loadMuted 그 외 false
def test_load_muted_others_false():
    out = _run_js("""
const a = loadMuted(makeStorage({ muted: "0" }));
const b = loadMuted(makeStorage({ muted: "true" }));
const c = loadMuted(makeStorage({ muted: "" }));
console.log(JSON.stringify([a, b, c]));
""")
    data = json.loads(out)
    assert data == [False, False, False], f"loadMuted 그 외 값 불일치: {data}"


# 13. saveMuted 저장 형식
def test_save_muted_format():
    out = _run_js("""
const s1 = makeStorage();
saveMuted(s1, true);
const a = s1._data.muted;

const s2 = makeStorage();
saveMuted(s2, false);
const b = s2._data.muted;

const s3 = makeStorage();
saveMuted(s3, 1);
const c = s3._data.muted;

const s4 = makeStorage();
saveMuted(s4, "");
const d = s4._data.muted;

console.log(JSON.stringify([a, b, c, d]));
""")
    data = json.loads(out)
    assert data == ["1", "0", "1", "0"], f"saveMuted 형식 불일치: {data}"


# 14. saveMuted falsy storage
def test_save_muted_falsy_storage():
    out = _run_js("""
let threw = false;
try {
  saveMuted(undefined, true);
} catch (e) {
  threw = true;
}
console.log(threw);
""")
    assert out == "false"
