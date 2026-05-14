"""T1 acceptance tests: HTML/CSS static skeleton."""
import pathlib
from html.parser import HTMLParser

ROOT = pathlib.Path(__file__).parent.parent


class _Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.texts: list[str] = []
        self.tags: list[tuple[str, list]] = []  # (tag, attrs)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, attrs))

    def handle_data(self, data):
        stripped = data.strip()
        if stripped:
            self.texts.append(stripped)

    def attr(self, tag, name):
        """Collect all values of `name` attribute from matching tags."""
        return [
            v
            for t, attrs in self.tags
            if t == tag
            for k, v in attrs
            if k == name
        ]

    def classes(self, tag):
        return self.attr(tag, "class")


def _parse() -> _Collector:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    p = _Collector()
    p.feed(html)
    return p


def test_files_exist():
    assert (ROOT / "index.html").exists(), "index.html이 없습니다"
    assert (ROOT / "styles.css").exists(), "styles.css가 없습니다"


def test_no_external_cdn():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "http" not in html.lower() or all(
        url.startswith("http") is False
        for url in html.split()
        if "cdn" in url.lower() or "jsdelivr" in url.lower() or "unpkg" in url.lower()
    ), "외부 CDN 링크가 포함되어 있습니다"


def test_balance_displayed():
    p = _parse()
    assert any("1000" in t for t in p.texts), "잔고 1000이 표시되지 않습니다"
    assert any("잔고" in t for t in p.texts), "'잔고' 텍스트가 없습니다"


def test_mute_button_exists():
    p = _parse()
    buttons = [(t, attrs) for t, attrs in p.tags if t == "button"]
    assert buttons, "button 요소가 없습니다"
    has_mute = any(
        "🔊" in t or "🔇" in t
        for t in p.texts
    ) or any(
        v in ("mute-btn",)
        for _, attrs in buttons
        for k, v in attrs
        if k == "id"
    )
    assert has_mute, "음소거 토글 버튼(🔊/🔇)이 없습니다"


def test_five_lanes():
    p = _parse()
    lane_classes = [c for c in p.classes("div") if "lane" in c]
    assert len(lane_classes) >= 5, f"레인이 5개 미만입니다 (발견: {len(lane_classes)})"


def test_horse_names_present():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    for name in ("Thunder", "Mystic", "Golden", "Emerald", "Shadow"):
        assert name in html, f"말 이름 {name}이 HTML에 없습니다"


def test_horse_emoji_present():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert html.count("🐎") >= 5, "🐎 이모지가 5개 미만입니다"


def test_finish_line_present():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "finish" in html.lower(), "결승선 관련 요소(finish)가 없습니다"


def test_bet_panel_elements():
    p = _parse()
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    # horse selection: radio inputs or buttons
    radio_inputs = [
        (t, attrs) for t, attrs in p.tags
        if t == "input" and any(k == "type" and v == "radio" for k, v in attrs)
    ]
    assert len(radio_inputs) >= 5, "말 선택 라디오가 5개 미만입니다"

    # bet amount input
    number_inputs = [
        (t, attrs) for t, attrs in p.tags
        if t == "input" and any(k == "type" and v == "number" for k, v in attrs)
    ]
    assert number_inputs, "베팅 금액 input(type=number)이 없습니다"

    # start button
    assert "출발" in html, "'출발' 버튼 텍스트가 없습니다"


# ── T14: 게임 오버 모달 ──────────────────────────────────────────────────────────

def test_game_over_modal_exists():
    p = _parse()
    modals = [e for _, attrs in p.tags if dict(attrs).get("id") == "game-over-modal"
              for e in [dict(attrs)]]
    elements = [{"tag": t, "attrs": dict(attrs)} for t, attrs in p.tags]
    modal = [e for e in elements if e["attrs"].get("id") == "game-over-modal"]
    assert len(modal) == 1, "#game-over-modal 요소가 없습니다"
    assert "hidden" in modal[0]["attrs"], "#game-over-modal에 hidden 속성이 없습니다"


def test_game_over_message_exists():
    elements = [{"tag": t, "attrs": dict(attrs)} for t, attrs in _parse().tags]
    modal = [e for e in elements if e["attrs"].get("id") == "game-over-modal"]
    assert len(modal) == 1, "#game-over-modal 요소가 없습니다"
    msg = [e for e in elements if e["attrs"].get("id") == "game-over-message"]
    assert len(msg) == 1, "#game-over-message 요소가 없습니다"


def test_restart_btn_exists():
    elements = [{"tag": t, "attrs": dict(attrs)} for t, attrs in _parse().tags]
    btn = [e for e in elements if e["attrs"].get("id") == "restart-btn"]
    assert len(btn) == 1, "#restart-btn 요소가 없습니다"
    assert btn[0]["attrs"].get("type") == "button", '#restart-btn에 type="button"이 없습니다'


# ── T15: 레인 순서 검증 보강 ──────────────────────────────────────────────────────

def test_lane_data_horse_order():
    p = _parse()
    lane_horses = []
    for tag, attrs in p.tags:
        if tag == "div":
            attrs_dict = dict(attrs)
            cls = attrs_dict.get("class", "")
            if "lane" in cls.split():
                horse = attrs_dict.get("data-horse")
                if horse:
                    lane_horses.append(horse)
    assert lane_horses == ["Thunder", "Mystic", "Golden", "Emerald", "Shadow"], \
        f"레인 data-horse 순서가 PRD 9.1과 다릅니다: {lane_horses}"
