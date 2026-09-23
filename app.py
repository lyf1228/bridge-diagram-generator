# -*- coding: utf-8 -*-
"""
🍁 牌局與叫牌排版工作台 / Bridge Deal & Auction Studio
Autumn Maple Editorial Edition — 多語系版本 (zh-Hant / zh-Hans / en / it / fr)

開放給大眾使用、免登入、即時預覽、一鍵下載出版級 PNG。
視覺語彙：秋風、紅楓葉、羊皮紙、出版級編排。
"""

from __future__ import annotations

import json
import re

import streamlit as st

# ---------------------------------------------------------------------------
# 秋季楓葉色彩計畫 (Autumn Palette)
# ---------------------------------------------------------------------------
PALETTE = {
    "crimson_deep": "#9E2A2B",   # 楓葉赤紅 · 主標題
    "crimson": "#BA181B",        # 楓葉赤紅 · 花色
    "suit_red": "#C1121F",       # ♥ ♦ 高飽和亮麗楓紅
    "walnut": "#2B231F",         # ♠ ♣ 深胡桃炭黑
    "amber": "#D4A373",          # 琥珀落葉金 · 邊框流線
    "ember": "#E76F51",          # 落葉橘 · 微光高亮
    "parchment": "#FAF8F5",      # 羊皮紙米白
    "parchment_hi": "#FDFBF7",   # 羊皮紙高光
    "tea": "#F9F6F0",            # 秋茶色 · 斑馬紋
    "maple_wood": "#FDE68A",     # 楓木金黃 · 表頭
    "header_ink": "#5B3A29",     # 深褐文字
    "outer": "#EFE6D8",          # 溫暖外緣底
    "hairline": "#E7D8C3",       # 細線
}

# 精緻內嵌 SVG 楓葉圖騰（真實五裂糖楓輪廓，Canada-leaf 家族）----------------------
MAPLE_PATH = (
    "M50 6 L53.7 23.1 C54.3 25.5 56 25.9 58.1 24.7 L67.6 19.4 "
    "L65.2 31.9 C64.8 34.1 66 35 68 34.7 L79.8 33 L74.4 43.7 "
    "C73.4 45.7 74 47 76 47.6 L84.7 50.3 L70.8 62.2 "
    "C69.1 63.6 69.4 65.1 71.2 66 L75.7 68.3 L60.4 71.9 "
    "C58.3 72.4 57.6 73.9 58.3 76 L61.2 85.9 L51.8 80.4 "
    "C50.6 79.7 49.4 79.7 48.2 80.4 L38.8 85.9 L41.7 76 "
    "C42.4 73.9 41.7 72.4 39.6 71.9 L24.3 68.3 L28.8 66 "
    "C30.6 65.1 30.9 63.6 29.2 62.2 L15.3 50.3 L24 47.6 "
    "C26 47 26.6 45.7 25.6 43.7 L20.2 33 L32 34.7 "
    "C34 35 35.2 34.1 34.8 31.9 L32.4 19.4 L41.9 24.7 "
    "C44 25.9 45.7 25.5 46.3 23.1 Z"
)


def maple_svg(fill: str, opacity: float = 1.0, stem: bool = True) -> str:
    stem_el = (
        f'<path d="M50 79 C49.7 88 49.2 96 47.8 104" stroke="{fill}" '
        f'stroke-width="3" fill="none" stroke-linecap="round"/>'
        if stem
        else ""
    )
    return (
        f'<svg viewBox="0 0 100 108" xmlns="http://www.w3.org/2000/svg" '
        f'style="opacity:{opacity}">'
        f'<path d="{MAPLE_PATH}" fill="{fill}"/>{stem_el}</svg>'
    )


def wind_divider(color: str) -> str:
    """秋風吹拂的動態流暢分隔線。"""
    return (
        f'<svg class="wind" viewBox="0 0 480 24" xmlns="http://www.w3.org/2000/svg" '
        f'preserveAspectRatio="none">'
        f'<path d="M4 16 C 70 2, 120 26, 190 14 S 320 2, 388 15 S 452 22, 476 12" '
        f'fill="none" stroke="{color}" stroke-width="2.4" stroke-linecap="round"/>'
        f'<path d="M40 21 C 110 12, 180 24, 250 17 S 380 12, 448 19" '
        f'fill="none" stroke="{color}" stroke-width="1.1" stroke-linecap="round" '
        f'opacity="0.55"/>'
        f'<circle cx="466" cy="9" r="2.3" fill="{color}"/>'
        f'</svg>'
    )


# ---------------------------------------------------------------------------
# 花色工具
# ---------------------------------------------------------------------------
SUITS = [
    ("S", "♠"),  # ♠
    ("H", "♥"),  # ♥
    ("D", "♦"),  # ♦
    ("C", "♣"),  # ♣
]
RED_SUITS = {"H", "D"}

# 出版級花色圖案（內嵌 SVG，永遠清晰、跨平台一致）----------------------------------
SUIT_PIP = {
    "S": '<path d="M50 6C50 6 16 34 16 58c0 13 10 21 21 18 1 7-4 15-12 20h50c-8-5-13-13-12-20 11 3 21-5 21-18C84 34 50 6 50 6Z"/>',
    "H": '<path d="M50 88S12 60 12 33C12 20 22 10 35 10c8 0 14 5 15 13 1-8 7-13 15-13 13 0 23 10 23 23 0 27-38 55-38 55Z"/>',
    "D": '<path d="M50 4 88 50 50 96 12 50Z"/>',
    "C": ('<circle cx="50" cy="26" r="18"/><circle cx="28" cy="54" r="18"/>'
          '<circle cx="72" cy="54" r="18"/><path d="M42 50h16l7 44H35Z"/>'),
}


def suit_pip(key: str, cls: str = "pip") -> str:
    color = PALETTE["suit_red"] if key in RED_SUITS else PALETTE["walnut"]
    return (
        f'<svg class="{cls}" viewBox="0 0 100 100" fill="{color}" '
        f'xmlns="http://www.w3.org/2000/svg">{SUIT_PIP[key]}</svg>'
    )


# ---------------------------------------------------------------------------
# 座位 / 語系
# ---------------------------------------------------------------------------
SEATS = ["W", "N", "E", "S"]  # 內部代碼，所有語系共用，牌桌上國際通用

LANGS = [
    ("zh-Hant", "繁體中文"),
    ("zh-Hans", "简体中文"),
    ("en", "English"),
    ("it", "Italiano"),
    ("fr", "Français"),
]
LANG_CODES = [c for c, _ in LANGS]

SEAT_NAME = {
    "zh-Hant": {"W": "西", "N": "北", "E": "東", "S": "南"},
    "zh-Hans": {"W": "西", "N": "北", "E": "东", "S": "南"},
    "en": {"W": "West", "N": "North", "E": "East", "S": "South"},
    "it": {"W": "Ovest", "N": "Nord", "E": "Est", "S": "Sud"},
    "fr": {"W": "Ouest", "N": "Nord", "E": "Est", "S": "Sud"},
}

# ---------------------------------------------------------------------------
# 牌號 → 發牌者 / 身價（標準複式橋牌 16 副循環表）
# ---------------------------------------------------------------------------
VULN_KEYS = ["none", "ns", "ew", "both"]
VULN_SEATS = {
    "none": set(),
    "ns": {"N", "S"},
    "ew": {"E", "W"},
    "both": {"N", "S", "E", "W"},
}
VULN_LABEL = {
    "zh-Hant": {"none": "雙無", "ns": "南北", "ew": "東西", "both": "雙方"},
    "zh-Hans": {"none": "双无", "ns": "南北", "ew": "东西", "both": "双方"},
    "en": {"none": "None", "ns": "N-S", "ew": "E-W", "both": "Both"},
    "it": {"none": "Nessuno", "ns": "N-S", "ew": "E-O", "both": "Entrambi"},
    "fr": {"none": "Aucune", "ns": "N-S", "ew": "E-O", "both": "Les deux"},
}
# 「無王」的書寫慣例依語系而不同：中英通用 NT，義/法慣用 SA（Senza/Sans Atout）
NT_LABEL = {"zh-Hant": "NT", "zh-Hans": "NT", "en": "NT", "it": "SA", "fr": "SA"}

# 第 1~16 副的標準身價循環；超過 16 副（17, 18, …）依 1~16 重新循環
_VULN_CYCLE_16 = [
    "none", "ns", "ew", "both", "ns", "ew", "both", "none",
    "ew", "both", "none", "ns", "both", "none", "ns", "ew",
]
_DEALER_CYCLE_4 = ["N", "E", "S", "W"]


def board_to_dealer(board_num: int) -> str:
    return _DEALER_CYCLE_4[(board_num - 1) % 4]


def board_to_vuln_key(board_num: int) -> str:
    return _VULN_CYCLE_16[(board_num - 1) % 16]


def parse_board_number(raw: str) -> int | None:
    raw = (raw or "").strip()
    return int(raw) if raw.isdigit() and int(raw) > 0 else None


def clean_holding(raw: str) -> str:
    """整理單一花色字串；-- 或空 => 缺門。"""
    raw = (raw or "").strip()
    if raw in {"", "-", "--", "—", "void", "VOID"}:
        return "—"  # —
    raw = raw.upper().replace("10", "T")
    raw = re.sub(r"[^AKQJT2-9]", "", raw)
    if not raw:
        return "—"
    order = "AKQJT98765432"
    cards = sorted(raw, key=lambda c: order.index(c) if c in order else 99)
    return " ".join(cards)


_RANK_CHARS = "AKQJT98765432"
_VOID_TOKENS = {"", "-", "--", "—", "VOID"}


def _parse_holding_strict(raw: str) -> tuple[list[str], list[str]]:
    """回傳 (有效點數字元, 無法辨識的字元)；不處理排序、不去重複。"""
    raw = (raw or "").strip()
    if raw.upper() in _VOID_TOKENS:
        return [], []
    raw = raw.upper().replace("10", "T")
    valid, invalid = [], []
    for ch in raw:
        if ch in _RANK_CHARS:
            valid.append(ch)
        elif ch in " ,\t":
            continue
        else:
            invalid.append(ch)
    return valid, invalid


def validate_hands(hands: dict, lang: str) -> list[str]:
    """檢查三件事：花色輸入含無法辨識字元、同一張牌被輸入超過一次、
    單一家總張數超過 13 張。訊息依語系翻譯。"""
    S = STR[lang]
    seat_name = SEAT_NAME[lang]
    errors: list[str] = []
    occurrences: dict[tuple[str, str], list[str]] = {}
    seat_totals: dict[str, int] = {seat: 0 for seat in SEATS}
    for seat in SEATS:
        for suit_key, suit_sym in SUITS:
            raw = (hands.get(seat, {}) or {}).get(suit_key, "")
            valid_chars, invalid_chars = _parse_holding_strict(raw)
            if invalid_chars:
                bad = "".join(sorted(set(invalid_chars)))
                errors.append(S["err_invalid_char"].format(
                    seat=seat_name[seat], suit=suit_sym, raw=raw, bad=bad
                ))
            seat_totals[seat] += len(valid_chars)
            for rank in valid_chars:
                occurrences.setdefault((suit_key, rank), []).append(seat)

    for (suit_key, rank), seats in occurrences.items():
        if len(seats) <= 1:
            continue
        suit_sym = dict(SUITS)[suit_key]
        if len(set(seats)) == 1:
            errors.append(S["err_dup_same_seat"].format(
                seat=seat_name[seats[0]], suit=suit_sym, rank=rank, n=len(seats)
            ))
        else:
            names = S["seat_join_sep"].join(
                S["seat_with_suffix"].format(seat=seat_name[s]) for s in seats
            )
            errors.append(S["err_dup_cross_seat"].format(suit=suit_sym, rank=rank, names=names))

    for seat, total in seat_totals.items():
        if total > 13:
            errors.append(S["err_over13"].format(seat=seat_name[seat], n=total))
    return errors


def hand_html(hand: dict) -> str:
    rows = []
    for key, _sym in SUITS:
        holding = clean_holding(hand.get(key, ""))
        rows.append(
            f'<div class="hrow">'
            f'{suit_pip(key, "pip pip-hand")}'
            f'<span class="cards">{holding}</span>'
            f'</div>'
        )
    return f'<div class="hand">{"".join(rows)}</div>'


# ---------------------------------------------------------------------------
# 叫牌解析
# ---------------------------------------------------------------------------
CALL_ALIASES = {
    "P": "Pass", "PASS": "Pass", "-": "Pass",
    "X": "Dbl", "DBL": "Dbl", "DOUBLE": "Dbl",
    "XX": "Rdbl", "RDBL": "Rdbl", "REDOUBLE": "Rdbl",
}


def fmt_call(token: str, lang: str) -> str:
    t = token.strip()
    if not t:
        return ""
    up = t.upper()
    if up in CALL_ALIASES:
        label = CALL_ALIASES[up]
        cls = "call-pass" if label == "Pass" else "call-x"
        return f'<span class="{cls}">{label}</span>'
    # 無王同時接受 NT / SA（義、法慣用 SA=Senza/Sans Atout）
    m = re.match(r"^([1-7])\s*(NT|SA|N)$", up)
    if m:
        level = m.group(1)
        return f'<span class="call-bid">{level}<span class="nt">{NT_LABEL[lang]}</span></span>'
    m = re.match(r"^([1-7])\s*(S|H|D|C)$", up)
    if m:
        level, strain = m.group(1), m.group(2)
        return (
            f'<span class="call-bid">{level}{suit_pip(strain, "pip pip-call")}</span>'
        )
    return f'<span class="call-bid">{t}</span>'


def parse_bidding(text: str, first_seat: str, lang: str) -> list[list[str]]:
    """回傳以 W,N,E,S 欄位順序排列的每一輪叫牌（HTML）。"""
    start = SEATS.index(first_seat)
    flat: list[str] = []
    for line in (text or "").splitlines():
        for tok in re.split(r"[\s,]+", line.strip()):
            if tok:
                flat.append(tok)
    # 前置空白，讓開叫者對齊正確欄位
    cells = [""] * start + [fmt_call(t, lang) for t in flat]
    rows: list[list[str]] = []
    for i in range(0, len(cells), 4):
        chunk = cells[i : i + 4]
        chunk += [""] * (4 - len(chunk))
        rows.append(chunk)
    if not rows:
        rows = [["", "", "", ""]]
    return rows


# ---------------------------------------------------------------------------
# 牌圖 HTML 組裝
# ---------------------------------------------------------------------------
def build_diagram_html(
    data: dict,
    lang: str,
    *,
    scale: float = 1.0,
    for_export: bool = False,
    interactive: bool = False,
    webhook: str = "",
    secret: str = "",
    meta: str = "",
    errors: list[str] | None = None,
) -> str:
    p = PALETTE
    S = STR[lang]
    seat_name = SEAT_NAME[lang]
    vuln = data["vuln_seats"]
    dealer = data["dealer"]

    def compass_cell(seat: str) -> str:
        is_dealer = seat == dealer
        is_vuln = seat in vuln
        cls = "cc"
        if is_vuln:
            cls += " cc-vuln"
        if is_dealer:
            cls += " cc-dealer"
        tag = '<span class="cc-d">D</span>' if is_dealer else ""
        return f'<div class="{cls}">{seat}{tag}</div>'

    compass = (
        '<div class="compass">'
        f'  <div class="compass-bg">{maple_svg(p["amber"], 0.16, stem=False)}</div>'
        f'  <div class="cc-row cc-top">{compass_cell("N")}</div>'
        f'  <div class="cc-row cc-mid">{compass_cell("W")}'
        f'    <div class="cc-hub">{data["board"] or "&nbsp;"}</div>'
        f'    {compass_cell("E")}</div>'
        f'  <div class="cc-row cc-bot">{compass_cell("S")}</div>'
        '</div>'
    )

    def seat_tag(seat: str) -> str:
        if lang in ("zh-Hant", "zh-Hans"):
            return f"{seat_name[seat]} {seat}"
        return f"{seat_name[seat]} {seat}"

    grid = (
        '<div class="diagram">'
        f'  <div class="wm">{maple_svg(p["crimson"], 0.06, stem=False)}</div>'
        f'  <div class="seat seat-n"><div class="seat-tag">{seat_tag("N")}</div>{hand_html(data["hands"]["N"])}</div>'
        f'  <div class="seat seat-w"><div class="seat-tag">{seat_tag("W")}</div>{hand_html(data["hands"]["W"])}</div>'
        f'  <div class="mid">{compass}</div>'
        f'  <div class="seat seat-e"><div class="seat-tag">{seat_tag("E")}</div>{hand_html(data["hands"]["E"])}</div>'
        f'  <div class="seat seat-s"><div class="seat-tag">{seat_tag("S")}</div>{hand_html(data["hands"]["S"])}</div>'
        '</div>'
    )

    # 叫牌表 ---------------------------------------------------------------
    if lang in ("zh-Hant", "zh-Hans"):
        head_cols = "".join(
            f'<th>{seat_name[s]}<span class="th-en">{SEAT_NAME["en"][s]}</span></th>'
            for s in SEATS
        )
    else:
        head_cols = "".join(f'<th>{seat_name[s]}</th>' for s in SEATS)

    def bidding_section(room_val: str, names_d: dict, bidding_text: str, notes_text: str) -> str:
        name_row = "".join(
            f'<td class="nm">{(names_d.get(s) or "").strip() or "—"}</td>' for s in SEATS
        )
        body_rows = ""
        for i, row in enumerate(parse_bidding(bidding_text, data["first_seat"], lang)):
            zc = "zebra" if i % 2 else ""
            body_rows += (
                f'<tr class="{zc}">' + "".join(f"<td>{c or ''}</td>" for c in row) + "</tr>"
            )
        note_block = ""
        if (notes_text or "").strip():
            note_lines = "".join(
                f"<li>{ln.strip()}</li>" for ln in notes_text.splitlines() if ln.strip()
            )
            note_block = (
                f'<div class="notes"><div class="notes-h">{S["card_notes_title"]}</div>'
                f'<ul>{note_lines}</ul></div>'
            )
        room_line = ""
        if (room_val or "").strip():
            room_line = f'<div class="room">{room_val.strip()}</div>'
        return (
            '<div class="bidsec">'
            f'  <div class="bidsec-h"><span class="bh-leaf">{maple_svg(p["crimson"], 1)}</span>'
            f'     {S["card_bidding_title"]} {room_line}</div>'
            f'  <table class="bidtable">'
            f'     <thead><tr>{head_cols}</tr>'
            f'     <tr class="names">{name_row}</tr></thead>'
            f'     <tbody>{body_rows}</tbody>'
            f'  </table>'
            f'  {note_block}'
            '</div>'
        )

    bidding = bidding_section(data.get("room", ""), data["names"], data["bidding"], data["notes"])
    if data.get("room2_enabled") and data.get("room2"):
        r2 = data["room2"]
        bidding += bidding_section(
            r2.get("room", ""), r2.get("names", {}), r2.get("bidding", ""), r2.get("notes", "")
        )

    # 頁首 ---------------------------------------------------------------
    subtitle_bits = []
    if data.get("session"):
        subtitle_bits.append(data["session"])
    if data.get("board"):
        subtitle_bits.append(S["card_board"].format(n=data["board"]))
    subtitle_bits.append(S["card_dealer"].format(seat=dealer))
    subtitle_bits.append(S["card_vuln"].format(vuln=data["vuln_label"]))
    subtitle = " · ".join(subtitle_bits)

    header = (
        '<header class="hdr">'
        f'  <span class="hdr-leaf l">{maple_svg(p["crimson"], 0.95)}</span>'
        f'  <div class="hdr-mid">'
        f'    <h1>{data["title"] or S["card_title_fallback"]}</h1>'
        f'    <div class="subtitle">{subtitle}</div>'
        f'  </div>'
        f'  <span class="hdr-leaf r">{maple_svg(p["crimson"], 0.95)}</span>'
        '</header>'
    )

    footer = (
        '<footer class="ftr">'
        f'  {wind_divider(p["amber"])}'
        f'  <span>金牌橋藝教室</span>'
        '</footer>'
    )

    css = _diagram_css(scale, lang)

    export_ui = ""
    if interactive and errors:
        err_items = "".join(f"<li>{e}</li>" for e in errors)
        export_ui = f"""
  <div class="xbar">
    <div class="xerr">
      <div class="xerr-h">{S['js_error_panel_title']}</div>
      <ul>{err_items}</ul>
    </div>
  </div>"""
    elif interactive:
        cfg = json.dumps({
            "webhook": webhook or "", "secret": secret or "", "meta": meta or "",
            "prefix": "Bridge_Diagram_",
            "generating": S["js_generating"],
            "successPrefix": S["js_success_prefix"],
            "successSuffix": S["js_success_suffix"],
            "cloudSaved": S["js_cloud_saved"],
            "cloudUnconfirmed": S["js_cloud_unconfirmed"],
            "failedPrefix": S["js_failed_prefix"],
        })
        export_ui = f"""
  <div class="xbar">
    <button id="dlbtn" type="button">{S['js_export_btn']}</button>
    <div id="xstat" class="xstat"></div>
    <img id="ximg" class="ximg" alt="">
  </div>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/html-to-image/1.11.11/html-to-image.min.js"></script>
  <script>
  (function() {{
    var CFG = {cfg};
    var btn = document.getElementById('dlbtn');
    var stat = document.getElementById('xstat');
    var img = document.getElementById('ximg');
    if (!btn) return;
    btn.addEventListener('click', async function() {{
      btn.disabled = true;
      stat.textContent = CFG.generating;
      img.removeAttribute('src');
      try {{
        if (document.fonts && document.fonts.ready) {{ try {{ await document.fonts.ready; }} catch (e) {{}} }}
        var card = document.querySelector('.card');
        var url = await htmlToImage.toPng(card, {{
          pixelRatio: 3, backgroundColor: '#EFE6D8', cacheBust: true
        }});
        var d = new Date(), p = function(n) {{ return (n < 10 ? '0' : '') + n; }};
        var ts = d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate()) + '_'
               + p(d.getHours()) + p(d.getMinutes()) + p(d.getSeconds());
        var name = CFG.prefix + ts + '.png';
        var a = document.createElement('a');
        a.href = url; a.download = name;
        document.body.appendChild(a); a.click(); a.remove();
        img.src = url;
        stat.textContent = CFG.successPrefix + name + CFG.successSuffix;
        if (CFG.webhook) {{
          try {{
            await fetch(CFG.webhook, {{
              method: 'POST',
              headers: {{ 'Content-Type': 'text/plain;charset=utf-8' }},
              body: JSON.stringify({{
                filename: name, mimeType: 'image/png',
                data: url.split(',')[1], secret: CFG.secret, description: CFG.meta
              }})
            }});
            stat.textContent += CFG.cloudSaved;
          }} catch (e) {{
            stat.textContent += CFG.cloudUnconfirmed;
          }}
        }}
      }} catch (err) {{
        stat.textContent = CFG.failedPrefix + err;
      }}
      btn.disabled = false;
    }});
  }})();
  </script>"""

    body_cls = "export" if for_export else "preview"
    html_lang = S["html_lang"]
    return f"""<!doctype html><html lang="{html_lang}"><head><meta charset="utf-8">
<style>{css}</style></head>
<body class="{body_cls}">
  <div class="card">
    {header}
    {wind_divider(PALETTE['amber'])}
    {grid}
    {bidding}
    {footer}
  </div>{export_ui}
</body></html>"""


def _diagram_css(scale: float, lang: str) -> str:
    p = PALETTE
    s = scale
    if lang == "zh-Hant":
        font_stack = ("'Noto Serif TC','Songti TC','Source Han Serif TC',"
                      "'Hiragino Mincho ProN','PingFang TC',Georgia,'Times New Roman',serif")
    elif lang == "zh-Hans":
        font_stack = ("'Noto Serif SC','Songti SC','Source Han Serif SC',"
                      "'Hiragino Sans GB','PingFang SC',Georgia,'Times New Roman',serif")
    else:
        font_stack = "Georgia,'Times New Roman','Noto Serif TC',serif"
    return f"""
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@500;700;900&family=Noto+Serif+SC:wght@500;700;900&display=swap');
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  font-family:{font_stack};
  background:{p['outer']};
  padding:{18*s}px;
  -webkit-font-smoothing:antialiased;
}}
body.export {{ background:{p['outer']}; }}
.card {{
  width:{620*s}px;
  background:linear-gradient(180deg,{p['parchment_hi']} 0%,{p['parchment']} 60%,#F4EFE7 100%);
  border:{1*s}px solid {p['hairline']};
  border-radius:{14*s}px;
  padding:{22*s}px {22*s}px {14*s}px;
  position:relative;
  box-shadow:0 {2*s}px {5*s}px rgba(91,58,41,.10),
             0 {14*s}px {34*s}px rgba(91,58,41,.16);
  overflow:hidden;
}}
.card::before {{
  content:""; position:absolute; inset:{5*s}px;
  border:{1.4*s}px solid {p['amber']};
  border-radius:{10*s}px; opacity:.55; pointer-events:none;
}}
.card::after {{
  content:""; position:absolute; left:0; right:0; top:0; height:{5*s}px;
  background:linear-gradient(90deg,{p['crimson_deep']},{p['ember']},{p['amber']},{p['crimson']});
}}

/* ---------- 頁首 ---------- */
.hdr {{ display:flex; align-items:center; justify-content:center;
  gap:{16*s}px; padding:{6*s}px 0 {4*s}px; }}
.hdr-leaf {{ width:{40*s}px; height:{40*s}px; flex:0 0 auto; display:block; }}
.hdr-leaf.l {{ transform:rotate(-18deg); }}
.hdr-leaf.r {{ transform:rotate(16deg) scaleX(-1); }}
.hdr-mid {{ text-align:center; }}
.hdr h1 {{
  font-size:{32*s}px; line-height:1.15; color:{p['crimson_deep']};
  font-weight:800; letter-spacing:{.5*s}px; margin:{2*s}px 0 {6*s}px;
  text-shadow:0 {1*s}px 0 rgba(255,255,255,.6);
}}
.subtitle {{ font-size:{17*s}px; color:{p['header_ink']}; letter-spacing:{.3*s}px; }}

/* ---------- 秋風分隔線 ---------- */
.wind {{ display:block; width:100%; height:{18*s}px; margin:{4*s}px 0 {8*s}px; }}

/* ---------- 牌圖 ---------- */
.diagram {{
  position:relative;
  display:grid;
  grid-template-columns:1fr {176*s}px 1fr;
  grid-template-areas:". n ." "w mid e" ". s .";
  gap:{4*s}px {6*s}px;
  align-items:center; justify-items:center;
  padding:{6*s}px 0 {8*s}px;
}}
.wm {{ position:absolute; left:50%; top:50%; width:{188*s}px; height:{188*s}px;
  transform:translate(-50%,-50%); pointer-events:none; }}
.seat-n {{ grid-area:n; }} .seat-w {{ grid-area:w; justify-self:end; }}
.seat-e {{ grid-area:e; justify-self:start; }} .seat-s {{ grid-area:s; }}
.mid {{ grid-area:mid; }}
.seat {{ min-width:{188*s}px; max-width:{215*s}px; }}
.seat-tag {{
  font-size:{17*s}px; letter-spacing:{1*s}px; color:{p['ember']};
  font-weight:700; margin-bottom:{3*s}px; text-align:left; white-space:nowrap;
}}
.seat-w .seat-tag, .seat-e .seat-tag {{ text-align:left; }}
.hand {{
  background:{p['parchment_hi']};
  border:{1*s}px solid {p['hairline']};
  border-left:{4*s}px solid {p['amber']};
  border-radius:{7*s}px;
  padding:{7*s}px {10*s}px;
  box-shadow:0 {1*s}px {3*s}px rgba(91,58,41,.08);
}}
.hrow {{ display:flex; align-items:center; gap:{8*s}px;
  font-size:{18*s}px; line-height:1.55; }}
.pip {{ display:inline-block; flex:0 0 auto; }}
.pip-hand {{ width:{22*s}px; height:{22*s}px; }}
.cards {{ color:{p['walnut']}; letter-spacing:{1*s}px; font-weight:600;
  font-variant-numeric:tabular-nums; white-space:nowrap; }}

/* ---------- 指南針羅盤 ---------- */
.compass {{
  position:relative; width:{176*s}px; height:{176*s}px;
  background:radial-gradient(circle at 38% 30%,#F5EAD6,#E7D2AF 68%,#D6BA8D);
  border:{1.5*s}px solid {p['amber']};
  border-radius:{16*s}px;
  box-shadow:inset 0 {2*s}px {6*s}px rgba(255,255,255,.55),
             0 {2*s}px {6*s}px rgba(91,58,41,.16);
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  gap:{7*s}px;
  padding:{12*s}px;
}}
.compass-bg {{ position:absolute; inset:{28*s}px; opacity:.4; }}
.cc-row {{ display:flex; align-items:center; justify-content:center;
  gap:{12*s}px; width:100%; }}
.cc-mid {{ gap:{9*s}px; }}
.cc {{
  position:relative;
  font-size:{18*s}px; font-weight:800; color:{p['header_ink']};
  width:{28*s}px; height:{25*s}px; display:flex; align-items:center;
  justify-content:center; border-radius:{6*s}px;
}}
.cc-dealer {{ box-shadow:0 0 0 {1.5*s}px {p['header_ink']}; }}
.cc-vuln {{
  background:linear-gradient(180deg,{p['crimson']},{p['crimson_deep']});
  color:#FFF3E6; box-shadow:0 {1*s}px {3*s}px rgba(158,42,43,.5);
}}
.cc-vuln.cc-dealer {{ box-shadow:0 0 0 {1.5*s}px {p['header_ink']},
  0 {1*s}px {3*s}px rgba(158,42,43,.5); }}
.cc-d {{ position:absolute; top:{-7*s}px; right:{-9*s}px;
  width:{14*s}px; height:{14*s}px; border-radius:50%;
  background:{p['ember']}; color:#FFF4E8;
  font-size:{9*s}px; font-weight:800; line-height:{14*s}px; text-align:center;
  box-shadow:0 {1*s}px {2*s}px rgba(91,58,41,.35); }}
.cc-hub {{
  min-width:{40*s}px; height:{34*s}px; padding:0 {8*s}px;
  background:linear-gradient(180deg,{p['parchment_hi']},#EFE2CB);
  border:{1*s}px solid {p['amber']}; border-radius:{6*s}px;
  display:flex; align-items:center; justify-content:center;
  font-size:{20*s}px; font-weight:800; color:{p['crimson_deep']};
  box-shadow:inset 0 {1*s}px {2*s}px rgba(255,255,255,.6);
}}

/* ---------- 叫牌表 ---------- */
.bidsec {{ margin-top:{8*s}px; }}
.bidsec-h {{
  display:flex; align-items:center; gap:{8*s}px;
  font-size:{17*s}px; font-weight:800; color:{p['crimson_deep']};
  padding-bottom:{7*s}px;
}}
.bh-leaf {{ width:{20*s}px; height:{20*s}px; display:inline-block; }}
.room {{
  margin-left:auto; font-size:{14*s}px; font-weight:700; letter-spacing:{.5*s}px;
  color:{p['header_ink']}; background:{p['maple_wood']};
  border:{1*s}px solid {p['amber']}; border-radius:{20*s}px;
  padding:{3*s}px {12*s}px;
}}
.bidtable {{ width:100%; border-collapse:separate; border-spacing:0;
  border:{1*s}px solid {p['amber']}; border-radius:{8*s}px; overflow:hidden;
  font-size:{17*s}px; }}
.bidtable th {{
  background:linear-gradient(180deg,{p['maple_wood']},#F6D976);
  color:{p['header_ink']}; font-weight:800;
  padding:{7*s}px {4*s}px {6*s}px; text-align:center;
  border-bottom:{1*s}px solid {p['amber']};
  letter-spacing:{.5*s}px;
}}
.th-en {{ display:block; font-size:{11*s}px; font-weight:600; letter-spacing:{1*s}px;
  opacity:.7; }}
.bidtable td {{
  padding:{7*s}px {4*s}px; text-align:center; color:{p['walnut']};
  border-bottom:{1*s}px solid {p['hairline']};
  font-variant-numeric:tabular-nums;
}}
.bidtable tr:last-child td {{ border-bottom:none; }}
.bidtable td + td, .bidtable th + th {{ border-left:{1*s}px solid {p['hairline']}; }}
tr.zebra td {{ background:{p['tea']}; }}
tr.names td {{
  background:#FBEFD9; font-size:{15*s}px; font-weight:700; color:{p['header_ink']};
  padding:{5*s}px {4*s}px; border-bottom:{1.4*s}px solid {p['amber']};
}}
td.nm {{ letter-spacing:{.5*s}px; }}
.call-bid {{ font-weight:800; color:{p['walnut']}; display:inline-flex;
  align-items:center; gap:{2*s}px; }}
.pip-call {{ width:{17*s}px; height:{17*s}px; }}
.call-bid .nt {{ font-size:{13*s}px; letter-spacing:{.5*s}px; }}
.call-pass {{ color:#8A7A63; font-style:italic; }}
.call-x {{ color:{p['suit_red']}; font-weight:800; }}

/* ---------- 註解 ---------- */
.notes {{
  margin-top:{8*s}px; background:{p['tea']};
  border:{1*s}px solid {p['hairline']}; border-left:{3*s}px solid {p['ember']};
  border-radius:{6*s}px; padding:{7*s}px {12*s}px;
}}
.notes-h {{ font-size:{14*s}px; font-weight:800; letter-spacing:{1*s}px;
  color:{p['ember']}; margin-bottom:{4*s}px; }}
.notes ul {{ margin:0; padding-left:{20*s}px; }}
.notes li {{ font-size:{17*s}px; line-height:1.6; color:{p['header_ink']}; }}

/* ---------- 頁尾 ---------- */
.ftr {{ text-align:center; padding-top:{6*s}px; }}
.ftr span {{ font-size:{13*s}px; letter-spacing:{4*s}px; color:{p['amber']}; }}

/* ---------- 匯出列（互動預覽用） ---------- */
.xbar {{ width:{620*s}px; max-width:100%; margin:{14*s}px auto 0; text-align:center;
  font-family:-apple-system,'Noto Sans TC','Microsoft JhengHei',sans-serif; }}
#dlbtn {{
  width:100%; border:none; border-radius:12px; padding:14px 16px;
  font-size:15px; font-weight:800; letter-spacing:.5px; color:#FFF4E8; cursor:pointer;
  background:linear-gradient(120deg,{p['crimson_deep']},{p['ember']});
  box-shadow:0 6px 16px rgba(158,42,43,.30); transition:filter .15s,transform .15s;
}}
#dlbtn:hover {{ filter:brightness(1.06); transform:translateY(-1px); }}
#dlbtn:disabled {{ filter:grayscale(.4) brightness(.9); cursor:progress; }}
.xstat {{ margin-top:8px; font-size:12.5px; line-height:1.5; color:{p['header_ink']};
  min-height:1.2em; }}
.ximg {{ display:block; margin:10px auto 0; max-width:300px; width:100%;
  border:1px solid {p['hairline']}; border-radius:8px; }}
.ximg:not([src]) {{ display:none; }}
.xerr {{
  text-align:left; background:#FDEDEC;
  border:1.5px solid {p['suit_red']}; border-radius:12px;
  padding:12px 16px; font-family:-apple-system,'Noto Sans TC','Microsoft JhengHei',sans-serif;
}}
.xerr-h {{ font-weight:800; color:{p['suit_red']}; margin-bottom:6px; font-size:14px; }}
.xerr ul {{ margin:0; padding-left:18px; }}
.xerr li {{ font-size:12.5px; line-height:1.7; color:{p['header_ink']}; }}
"""


# ---------------------------------------------------------------------------
# 雲端硬碟收集（Google Apps Script Web App）— 上傳改在瀏覽器端做，這裡只取設定值
# ---------------------------------------------------------------------------
def _secret(name: str, default: str = "") -> str:
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:  # noqa: BLE001  (本機沒 secrets.toml 時)
        pass
    import os

    return os.environ.get(name.upper(), default)


def drive_enabled() -> bool:
    return bool(_secret("drive_webhook_url"))


# ---------------------------------------------------------------------------
# 語系字串
# ---------------------------------------------------------------------------
STR: dict[str, dict] = {
    "zh-Hant": {
        "html_lang": "zh-Hant",
        "page_title": "牌局與叫牌排版工作台",
        "banner_h1": "🍁 牌局與叫牌排版工作台",
        "banner_p": "免登入 · 即時預覽 · 一鍵下載出版級 PNG",
        "guide_title": "📖 輸入說明 · 快速對照鍵（第一次使用請先看）",
        "guide_md": """
| 區塊 | 怎麼填 |
| --- | --- |
| **① 基本資訊** | 賽事名稱、場次、發牌編號。**勾選「依牌號自動帶入」後不用選發牌者／身價**——標準複式橋牌 16 副循環表會自動算好，超過 16 副會自動重新循環（17=1、18=2…） |
| **② 四家手牌** | 每家 ♠♥♦♣ 各一格，直接打點數如 `AKQ` 或 `A K Q`；`10` 自動轉 `T`；**缺門打 `--`** |
| **③ 叫牌區** | 室別標題、四席選手姓名、叫牌序列（**每行一輪**、空白分隔、`P`=Pass `X`=Dbl `XX`=Rdbl）、叫牌註解；可勾選「顯示第二段叫牌記錄」再加一份（例如公開室 / 關閉室對照） |

叫牌永遠從「**發牌者**」開始，系統會自動把叫品對齊正確欄位。改好任一欄位，右側預覽即時更新 → 按「📸 匯出」下載 PNG。
""",
        "btn_load_sample": "🎴 載入範例牌局",
        "btn_clear_all": "🧹 全部清空",
        "edit_hint": "👇 下面每一格都可以點進去輸入 / 修改；空白處的淺灰字只是範例提示。",
        "h_section1": "### ① 基本資訊",
        "f_title": "賽事名稱", "ph_title": "例：2026 中華橋協秋季公開賽",
        "f_session": "場次", "ph_session": "例：第 3 循環",
        "f_board": "發牌編號", "ph_board": "例：18",
        "auto_dv_label": "🔢 依牌號自動帶入發牌者與身價（標準 16 副循環）",
        "auto_dv_result": "✅ 第 {n} 副　→　發牌者 **{seat}（{code}）**　·　身價 **{vuln}**{wrap}",
        "auto_dv_wrap": "　（= 第 {m} 副的標準循環）",
        "auto_dv_invalid": "尚未輸入有效牌號，請先輸入發牌編號，或取消勾選改手動選擇。",
        "f_dealer": "發牌者 (Dealer)",
        "f_vuln": "身價 (Vulnerability)",
        "h_section2": "### ② 四家手牌　·　缺門請輸入 `--`",
        "seat_hand_heading": "{seat}家 {en}",
        "h_section3": "### ③ 叫牌區",
        "f_room": "室別標題", "ph_room": "例：公開室 Open Room",
        "first_seat_caption": "開叫席位跟著發牌者：{seat}（{code}）先叫",
        "names_caption": "選手席位姓名",
        "f_name": "{seat} 選手", "ph_name": "選填",
        "f_bidding": "多行文字叫牌序列（每行一輪；空白分隔；P=Pass、X=Dbl、XX=Rdbl）",
        "ph_bidding": "1NT  P  3NT  P\nP  P",
        "f_notes": "叫牌註解備註（每行一則）",
        "ph_notes": "1NT：15–17 大牌點，平均牌型\n3NT：北家有把握的一擊到位",
        "show_room2_label": "➕ 顯示第二段叫牌記錄（例如公開室 / 關閉室各一份）",
        "room2_heading": "**第二段叫牌記錄**",
        "f_room2": "室別標題２", "ph_room2": "例：關閉室 Closed Room",
        "names2_caption": "選手席位姓名２",
        "f_name2": "{seat} 選手２",
        "f_bidding2": "多行文字叫牌序列２（同一副牌，第二段各自的叫牌）",
        "ph_bidding2": "P  P  1S  P\n2H  P  4H  P\nP  P",
        "f_notes2": "叫牌註解備註２（每行一則）",
        "h_preview": "### 🍁 即時預覽 · 下載",
        "export_caption": "圖在你的瀏覽器直接產生（pixelRatio 3 ≈ 300DPI 級），不需伺服器。",
        "export_cloud_on": "　☁️ 每張圖也會自動送進「金牌橋藝教室」的雲端硬碟收藏。",
        "export_cloud_off": "　（未設定雲端收集，只會下載到你的裝置。）",
        "footer": "🍁 金牌橋藝教室🍁",
        # 驗證錯誤
        "err_banner_prefix": "⚠️ 牌局有誤，請修正後才能匯出：\n\n",
        "err_invalid_char": "{seat}家 {suit} 輸入「{raw}」含無法辨識的字元「{bad}」，請修正",
        "err_dup_same_seat": "{seat}家 {suit} 的 {rank} 重複輸入了 {n} 次",
        "err_dup_cross_seat": "{suit} {rank} 同時出現在 {names}，同一張牌只能屬於一家",
        "err_over13": "{seat}家 目前共 {n} 張牌，超過 13 張上限，請刪掉多的牌",
        "seat_join_sep": "、",
        "seat_with_suffix": "{seat}家",
        # 卡片
        "card_title_fallback": "橋牌牌局",
        "card_board": "第 {n} 副",
        "card_dealer": "發牌 {seat}",
        "card_vuln": "身價 {vuln}",
        "card_bidding_title": "叫牌記錄 · Bidding",
        "card_notes_title": "叫牌註解",
        # 互動匯出 JS 文案
        "js_export_btn": "📸 產生並下載牌局叫牌圖 (PNG)",
        "js_generating": "產生中…（首次約需數秒）",
        "js_success_prefix": "✅ 已產生 ",
        "js_success_suffix": "　（沒自動下載的話，長按 / 右鍵下方縮圖另存）",
        "js_cloud_saved": "　·　☁️ 已送入雲端硬碟收藏",
        "js_cloud_unconfirmed": "　·　☁️ 已送出（雲端狀態無法確認）",
        "js_failed_prefix": "產生失敗：",
        "js_error_panel_title": "⚠️ 請先修正牌局才能匯出",
        # 範例牌局
        "ex_title": "2026 中華橋協秋季公開賽",
        "ex_session": "第 3 循環",
        "ex_room": "公開室 Open Room",
        "ex_n": "王小明", "ex_s": "李大華",
        "ex_bidding": "1NT  P  3NT  P\nP  P",
        "ex_notes": "1NT：15–17 大牌點，平均牌型\n3NT：北家有把握的一擊到位",
    },
    "zh-Hans": {
        "html_lang": "zh-Hans",
        "page_title": "牌局与叫牌排版工作台",
        "banner_h1": "🍁 牌局与叫牌排版工作台",
        "banner_p": "免登录 · 即时预览 · 一键下载出版级 PNG",
        "guide_title": "📖 输入说明 · 快速对照键（第一次使用请先看）",
        "guide_md": """
| 区块 | 怎么填 |
| --- | --- |
| **① 基本信息** | 赛事名称、场次、发牌编号。**勾选「依牌号自动带入」后不用选发牌者／局况**——标准双人赛 16 副循环表会自动算好，超过 16 副会自动重新循环（17=1、18=2…） |
| **② 四家手牌** | 每家 ♠♥♦♣ 各一格，直接打点数如 `AKQ` 或 `A K Q`；`10` 自动转 `T`；**缺门打 `--`** |
| **③ 叫牌区** | 室别标题、四席选手姓名、叫牌序列（**每行一轮**、空白分隔、`P`=Pass `X`=Dbl `XX`=Rdbl）、叫牌注解；可勾选「显示第二段叫牌记录」再加一份（例如公开室 / 结果室对照） |

叫牌永远从「**发牌者**」开始，系统会自动把叫品对齐正确栏位。改好任一栏位，右侧预览即时更新 → 按「📸 导出」下载 PNG。
""",
        "btn_load_sample": "🎴 载入范例牌局",
        "btn_clear_all": "🧹 全部清空",
        "edit_hint": "👇 下面每一格都可以点进去输入 / 修改；空白处的浅灰字只是范例提示。",
        "h_section1": "### ① 基本信息",
        "f_title": "赛事名称", "ph_title": "例：2026 中华桥协秋季公开赛",
        "f_session": "场次", "ph_session": "例：第 3 循环",
        "f_board": "发牌编号", "ph_board": "例：18",
        "auto_dv_label": "🔢 依牌号自动带入发牌者与身价（标准 16 副循环）",
        "auto_dv_result": "✅ 第 {n} 副　→　发牌者 **{seat}（{code}）**　·　身价 **{vuln}**{wrap}",
        "auto_dv_wrap": "　（= 第 {m} 副的标准循环）",
        "auto_dv_invalid": "尚未输入有效牌号，请先输入发牌编号，或取消勾选改手动选择。",
        "f_dealer": "发牌者 (Dealer)",
        "f_vuln": "身价 (Vulnerability)",
        "h_section2": "### ② 四家手牌　·　缺门请输入 `--`",
        "seat_hand_heading": "{seat}家 {en}",
        "h_section3": "### ③ 叫牌区",
        "f_room": "室别标题", "ph_room": "例：公开室 Open Room",
        "first_seat_caption": "开叫席位跟着发牌者：{seat}（{code}）先叫",
        "names_caption": "选手席位姓名",
        "f_name": "{seat} 选手", "ph_name": "选填",
        "f_bidding": "多行文字叫牌序列（每行一轮；空白分隔；P=Pass、X=Dbl、XX=Rdbl）",
        "ph_bidding": "1NT  P  3NT  P\nP  P",
        "f_notes": "叫牌注解备注（每行一则）",
        "ph_notes": "1NT：15–17 大牌点，平均牌型\n3NT：北家有把握的一击到位",
        "show_room2_label": "➕ 显示第二段叫牌记录（例如公开室 / 结果室各一份）",
        "room2_heading": "**第二段叫牌记录**",
        "f_room2": "室别标题２", "ph_room2": "例：结果室 Closed Room",
        "names2_caption": "选手席位姓名２",
        "f_name2": "{seat} 选手２",
        "f_bidding2": "多行文字叫牌序列２（同一副牌，第二段各自的叫牌）",
        "ph_bidding2": "P  P  1S  P\n2H  P  4H  P\nP  P",
        "f_notes2": "叫牌注解备注２（每行一则）",
        "h_preview": "### 🍁 即时预览 · 下载",
        "export_caption": "图在你的浏览器直接产生（pixelRatio 3 ≈ 300DPI 级），不需服务器。",
        "export_cloud_on": "　☁️ 每张图也会自动送进「金牌桥艺教室」的云端硬盘收藏。",
        "export_cloud_off": "　（未设定云端收集，只会下载到你的装置。）",
        "footer": "🍁 金牌橋藝教室🍁",
        "err_banner_prefix": "⚠️ 牌局有误，请修正后才能导出：\n\n",
        "err_invalid_char": "{seat}家 {suit} 输入「{raw}」含无法识别的字符「{bad}」，请修正",
        "err_dup_same_seat": "{seat}家 {suit} 的 {rank} 重复输入了 {n} 次",
        "err_dup_cross_seat": "{suit} {rank} 同时出现在 {names}，同一张牌只能属于一家",
        "err_over13": "{seat}家 目前共 {n} 张牌，超过 13 张上限，请删掉多的牌",
        "seat_join_sep": "、",
        "seat_with_suffix": "{seat}家",
        "card_title_fallback": "桥牌牌局",
        "card_board": "第 {n} 副",
        "card_dealer": "发牌 {seat}",
        "card_vuln": "身价 {vuln}",
        "card_bidding_title": "叫牌记录 · Bidding",
        "card_notes_title": "叫牌注解",
        "js_export_btn": "📸 生成并下载牌局叫牌图 (PNG)",
        "js_generating": "生成中…（首次约需数秒）",
        "js_success_prefix": "✅ 已生成 ",
        "js_success_suffix": "　（没自动下载的话，长按 / 右键下方缩图另存）",
        "js_cloud_saved": "　·　☁️ 已送入云端硬盘收藏",
        "js_cloud_unconfirmed": "　·　☁️ 已送出（云端状态无法确认）",
        "js_failed_prefix": "生成失败：",
        "js_error_panel_title": "⚠️ 请先修正牌局才能导出",
        "ex_title": "2026 中华桥协秋季公开赛",
        "ex_session": "第 3 循环",
        "ex_room": "公开室 Open Room",
        "ex_n": "王小明", "ex_s": "李大华",
        "ex_bidding": "1NT  P  3NT  P\nP  P",
        "ex_notes": "1NT：15–17 大牌点，平均牌型\n3NT：北家有把握的一击到位",
    },
    "en": {
        "html_lang": "en",
        "page_title": "Bridge Deal & Auction Studio",
        "banner_h1": "🍁 Bridge Deal & Auction Studio",
        "banner_p": "No login · Live preview · One-click publication-grade PNG",
        "guide_title": "📖 Quick input guide (read this first)",
        "guide_md": """
| Section | How to fill it in |
| --- | --- |
| **① Basics** | Event name, session, board number. **Check "Auto-fill from board number"** and you won't need to pick dealer/vulnerability — the standard 16-board duplicate cycle is calculated for you, wrapping past 16 (17=1, 18=2, …) |
| **② The four hands** | One box per suit ♠♥♦♣ for each hand; type ranks like `AKQ` or `A K Q`; `10` becomes `T`; **use `--` for a void** |
| **③ Auction** | Room label, player names, the auction (**one round per line**, space-separated, `P`=Pass `X`=Dbl `XX`=Rdbl), and notes; check "Show a second auction record" to add one more (e.g. Open Room / Closed Room) |

The auction always starts with the **dealer** — the app lines up calls under the right seat automatically. Edit any field and the preview updates live → click **📸 Export** to download the PNG.
""",
        "btn_load_sample": "🎴 Load sample deal",
        "btn_clear_all": "🧹 Clear all",
        "edit_hint": "👇 Every box below is editable — the faint grey text is just an example hint.",
        "h_section1": "### ① Basics",
        "f_title": "Event name", "ph_title": "e.g. 2026 Autumn Open Teams",
        "f_session": "Session", "ph_session": "e.g. Round 3",
        "f_board": "Board number", "ph_board": "e.g. 18",
        "auto_dv_label": "🔢 Auto-fill dealer & vulnerability from board number (standard 16-board cycle)",
        "auto_dv_result": "✅ Board {n} → Dealer **{seat} ({code})** · Vul **{vuln}**{wrap}",
        "auto_dv_wrap": "  (= same as standard board {m})",
        "auto_dv_invalid": "No valid board number yet — enter one above, or uncheck this to choose manually.",
        "f_dealer": "Dealer",
        "f_vuln": "Vulnerability",
        "h_section2": "### ② The four hands  ·  use `--` for a void",
        "seat_hand_heading": "{seat}",
        "h_section3": "### ③ Auction",
        "f_room": "Room label", "ph_room": "e.g. Open Room",
        "first_seat_caption": "Opening seat follows the dealer: {seat} ({code}) bids first",
        "names_caption": "Player names by seat",
        "f_name": "{seat} player", "ph_name": "optional",
        "f_bidding": "Auction — one round per line; space-separated; P=Pass, X=Dbl, XX=Rdbl",
        "ph_bidding": "1NT  P  3NT  P\nP  P",
        "f_notes": "Auction notes (one per line)",
        "ph_notes": "1NT: 15–17 HCP, balanced\n3NT: to play",
        "show_room2_label": "➕ Show a second auction record (e.g. Open Room / Closed Room)",
        "room2_heading": "**Second auction record**",
        "f_room2": "Room label 2", "ph_room2": "e.g. Closed Room",
        "names2_caption": "Player names by seat (2)",
        "f_name2": "{seat} player 2",
        "f_bidding2": "Auction 2 (same deal, second room's own auction)",
        "ph_bidding2": "P  P  1S  P\n2H  P  4H  P\nP  P",
        "f_notes2": "Auction notes 2 (one per line)",
        "h_preview": "### 🍁 Live preview · Download",
        "export_caption": "Rendered right in your browser (pixelRatio 3 ≈ 300 DPI-class) — no server needed.",
        "export_cloud_on": "  ☁️ Every export is also saved to the shared Drive collection.",
        "export_cloud_off": "  (Cloud collection isn't configured — this only downloads to your device.)",
        "footer": "🍁 金牌橋藝教室🍁",
        "err_banner_prefix": "⚠️ The deal has errors — please fix before exporting:\n\n",
        "err_invalid_char": "{seat} {suit}: \"{raw}\" has an unrecognized character \"{bad}\" — please fix",
        "err_dup_same_seat": "{seat} {suit}: {rank} was entered {n} times",
        "err_dup_cross_seat": "{suit} {rank} appears in both {names} — a card can only belong to one hand",
        "err_over13": "{seat} currently has {n} cards — over the 13-card limit, please remove the extras",
        "seat_join_sep": " and ",
        "seat_with_suffix": "{seat}",
        "card_title_fallback": "Bridge Deal",
        "card_board": "Board {n}",
        "card_dealer": "Dealer {seat}",
        "card_vuln": "Vul {vuln}",
        "card_bidding_title": "Auction",
        "card_notes_title": "Notes",
        "js_export_btn": "📸 Generate & Download Deal Image (PNG)",
        "js_generating": "Generating… (first time may take a few seconds)",
        "js_success_prefix": "✅ Generated ",
        "js_success_suffix": "  (if it didn't auto-download, long-press / right-click the thumbnail below to save)",
        "js_cloud_saved": "  ·  ☁️ Saved to the cloud collection",
        "js_cloud_unconfirmed": "  ·  ☁️ Sent (cloud status unconfirmed)",
        "js_failed_prefix": "Generation failed: ",
        "js_error_panel_title": "⚠️ Please fix the deal before exporting",
        "ex_title": "2026 Autumn Open Teams",
        "ex_session": "Round 3",
        "ex_room": "Open Room",
        "ex_n": "A. Smith", "ex_s": "B. Jones",
        "ex_bidding": "1NT  P  3NT  P\nP  P",
        "ex_notes": "1NT: 15–17 HCP, balanced\n3NT: to play",
    },
    "it": {
        "html_lang": "it",
        "page_title": "Studio Smazzate e Licitazioni",
        "banner_h1": "🍁 Studio Smazzate e Licitazioni",
        "banner_p": "Senza login · Anteprima live · PNG di livello editoriale in un clic",
        "guide_title": "📖 Guida rapida (leggi prima di iniziare)",
        "guide_md": """
| Sezione | Cosa inserire |
| --- | --- |
| **① Dati base** | Nome del torneo, turno, numero di smazzata. **Spunta "Compila automaticamente da numero smazzata"** e non serve scegliere mazziere/vulnerabilità: vengono calcolati secondo il ciclo standard a 16 smazzate, che si ripete oltre la 16ª (17=1, 18=2, …) |
| **② Le quattro mani** | Una casella per seme ♠♥♦♣ per ogni mano; scrivi le carte come `AKQ` o `A K Q`; `10` diventa `T`; **usa `--` per lo smazzo vuoto (void)** |
| **③ Licitazione** | Titolo della sala, nomi dei giocatori, licitazione (**una battuta per riga**, separata da spazi, `P`=Passo `X`=Contro `XX`=Ricontro), e note; spunta "Mostra una seconda licitazione" per aggiungerne un'altra (es. Sala Open / Sala Chiusa) |

La licitazione parte sempre dal **mazziere** — l'app allinea automaticamente le chiamate sotto la mano giusta. Modifica un campo qualsiasi e l'anteprima si aggiorna subito → premi **📸 Esporta** per scaricare il PNG.
""",
        "btn_load_sample": "🎴 Carica smazzata di esempio",
        "btn_clear_all": "🧹 Cancella tutto",
        "edit_hint": "👇 Ogni casella qui sotto è modificabile — il testo grigio chiaro è solo un esempio.",
        "h_section1": "### ① Dati base",
        "f_title": "Nome del torneo", "ph_title": "es. Campionato Autunnale 2026",
        "f_session": "Turno", "ph_session": "es. Turno 3",
        "f_board": "Numero smazzata", "ph_board": "es. 18",
        "auto_dv_label": "🔢 Compila automaticamente mazziere e vulnerabilità (ciclo standard a 16 smazzate)",
        "auto_dv_result": "✅ Smazzata {n} → Mazziere **{seat} ({code})** · Vulnerabilità **{vuln}**{wrap}",
        "auto_dv_wrap": "  (= come la smazzata standard {m})",
        "auto_dv_invalid": "Nessun numero di smazzata valido — inseriscine uno sopra, oppure deseleziona per scegliere manualmente.",
        "f_dealer": "Mazziere",
        "f_vuln": "Vulnerabilità",
        "h_section2": "### ② Le quattro mani  ·  usa `--` per il void",
        "seat_hand_heading": "{seat}",
        "h_section3": "### ③ Licitazione",
        "f_room": "Titolo della sala", "ph_room": "es. Sala Open",
        "first_seat_caption": "Apre chi è mazziere: {seat} ({code}) dichiara per primo",
        "names_caption": "Nomi dei giocatori",
        "f_name": "Giocatore {seat}", "ph_name": "facoltativo",
        "f_bidding": "Licitazione — una battuta per riga; separata da spazi; P=Passo, X=Contro, XX=Ricontro",
        "ph_bidding": "1SA  P  3SA  P\nP  P",
        "f_notes": "Note sulla licitazione (una per riga)",
        "ph_notes": "1SA: 15–17 PO, mano bilanciata\n3SA: contratto di manche",
        "show_room2_label": "➕ Mostra una seconda licitazione (es. Sala Open / Sala Chiusa)",
        "room2_heading": "**Seconda licitazione**",
        "f_room2": "Titolo della sala 2", "ph_room2": "es. Sala Chiusa",
        "names2_caption": "Nomi dei giocatori (2)",
        "f_name2": "Giocatore {seat} 2",
        "f_bidding2": "Licitazione 2 (stessa smazzata, licitazione della seconda sala)",
        "ph_bidding2": "P  P  1S  P\n2H  P  4H  P\nP  P",
        "f_notes2": "Note sulla licitazione 2 (una per riga)",
        "h_preview": "### 🍁 Anteprima live · Download",
        "export_caption": "Immagine generata direttamente nel browser (pixelRatio 3 ≈ qualità 300 DPI) — nessun server richiesto.",
        "export_cloud_on": "  ☁️ Ogni esportazione viene salvata anche nella raccolta cloud condivisa.",
        "export_cloud_off": "  (Raccolta cloud non configurata — viene solo scaricata sul tuo dispositivo.)",
        "footer": "🍁 金牌橋藝教室🍁",
        "err_banner_prefix": "⚠️ La smazzata contiene errori, correggi prima di esportare:\n\n",
        "err_invalid_char": "{seat} {suit}: «{raw}» contiene un carattere non riconosciuto «{bad}», correggilo",
        "err_dup_same_seat": "{seat} {suit}: {rank} è stato inserito {n} volte",
        "err_dup_cross_seat": "{suit} {rank} risulta in più mani ({names}): una carta può appartenere a una sola mano",
        "err_over13": "{seat} ha attualmente {n} carte, oltre il limite di 13: rimuovi quelle in eccesso",
        "seat_join_sep": " e ",
        "seat_with_suffix": "{seat}",
        "card_title_fallback": "Smazzata di Bridge",
        "card_board": "Smazzata {n}",
        "card_dealer": "Mazziere {seat}",
        "card_vuln": "Vul {vuln}",
        "card_bidding_title": "Licitazione",
        "card_notes_title": "Note",
        "js_export_btn": "📸 Genera e Scarica l'Immagine (PNG)",
        "js_generating": "Generazione in corso… (la prima volta richiede qualche secondo)",
        "js_success_prefix": "✅ Generato ",
        "js_success_suffix": "  (se non si scarica automaticamente, tieni premuto / clic destro sulla miniatura qui sotto per salvare)",
        "js_cloud_saved": "  ·  ☁️ Salvato nella raccolta cloud",
        "js_cloud_unconfirmed": "  ·  ☁️ Inviato (stato cloud non confermato)",
        "js_failed_prefix": "Generazione fallita: ",
        "js_error_panel_title": "⚠️ Correggi la smazzata prima di esportare",
        "ex_title": "Campionato Autunnale 2026",
        "ex_session": "Turno 3",
        "ex_room": "Sala Open",
        "ex_n": "M. Rossi", "ex_s": "L. Bianchi",
        "ex_bidding": "1SA  P  3SA  P\nP  P",
        "ex_notes": "1SA: 15–17 PO, mano bilanciata\n3SA: contratto di manche",
    },
    "fr": {
        "html_lang": "fr",
        "page_title": "Atelier de Donnes et Enchères",
        "banner_h1": "🍁 Atelier de Donnes et Enchères",
        "banner_p": "Sans connexion · Aperçu en direct · PNG qualité éditoriale en un clic",
        "guide_title": "📖 Guide rapide (à lire avant de commencer)",
        "guide_md": """
| Section | Comment remplir |
| --- | --- |
| **① Informations de base** | Nom du tournoi, séance, numéro de donne. **Cochez « Remplissage automatique par numéro de donne »** et vous n'aurez pas à choisir le donneur/la vulnérabilité — le cycle standard à 16 donnes est calculé automatiquement, et recommence après la 16ᵉ (17=1, 18=2, …) |
| **② Les quatre mains** | Une case par couleur ♠♥♦♣ pour chaque main ; tapez les cartes comme `AKQ` ou `A K Q` ; `10` devient `T` ; **utilisez `--` pour une chicane (void)** |
| **③ Enchères** | Titre de la salle, noms des joueurs, les enchères (**une donne par ligne**, séparées par des espaces, `P`=Passe `X`=Contre `XX`=Surcontre), et les notes ; cochez « Afficher une deuxième série d'enchères » pour en ajouter une (ex. Salle Ouverte / Salle Fermée) |

Les enchères commencent toujours par le **donneur** — l'application aligne automatiquement les annonces sous la bonne main. Modifiez n'importe quel champ et l'aperçu se met à jour en direct → cliquez sur **📸 Exporter** pour télécharger le PNG.
""",
        "btn_load_sample": "🎴 Charger une donne d'exemple",
        "btn_clear_all": "🧹 Tout effacer",
        "edit_hint": "👇 Chaque case ci-dessous est modifiable — le texte gris clair n'est qu'un exemple.",
        "h_section1": "### ① Informations de base",
        "f_title": "Nom du tournoi", "ph_title": "ex. Championnat d'Automne 2026",
        "f_session": "Séance", "ph_session": "ex. Tour 3",
        "f_board": "Numéro de donne", "ph_board": "ex. 18",
        "auto_dv_label": "🔢 Remplissage automatique du donneur et de la vulnérabilité (cycle standard à 16 donnes)",
        "auto_dv_result": "✅ Donne {n} → Donneur **{seat} ({code})** · Vulnérabilité **{vuln}**{wrap}",
        "auto_dv_wrap": "  (= identique à la donne standard {m})",
        "auto_dv_invalid": "Aucun numéro de donne valide — saisissez-en un ci-dessus, ou décochez pour choisir manuellement.",
        "f_dealer": "Donneur",
        "f_vuln": "Vulnérabilité",
        "h_section2": "### ② Les quatre mains  ·  utilisez `--` pour une chicane",
        "seat_hand_heading": "{seat}",
        "h_section3": "### ③ Enchères",
        "f_room": "Titre de la salle", "ph_room": "ex. Salle Ouverte",
        "first_seat_caption": "Le donneur ouvre : {seat} ({code}) parle en premier",
        "names_caption": "Noms des joueurs",
        "f_name": "Joueur {seat}", "ph_name": "facultatif",
        "f_bidding": "Enchères — une donne par ligne ; séparées par des espaces ; P=Passe, X=Contre, XX=Surcontre",
        "ph_bidding": "1SA  P  3SA  P\nP  P",
        "f_notes": "Notes sur les enchères (une par ligne)",
        "ph_notes": "1SA : 15–17 points d'honneur, main régulière\n3SA : contrat de manche",
        "show_room2_label": "➕ Afficher une deuxième série d'enchères (ex. Salle Ouverte / Salle Fermée)",
        "room2_heading": "**Deuxième série d'enchères**",
        "f_room2": "Titre de la salle 2", "ph_room2": "ex. Salle Fermée",
        "names2_caption": "Noms des joueurs (2)",
        "f_name2": "Joueur {seat} 2",
        "f_bidding2": "Enchères 2 (même donne, enchères propres à la seconde salle)",
        "ph_bidding2": "P  P  1S  P\n2H  P  4H  P\nP  P",
        "f_notes2": "Notes sur les enchères 2 (une par ligne)",
        "h_preview": "### 🍁 Aperçu en direct · Téléchargement",
        "export_caption": "Image générée directement dans votre navigateur (pixelRatio 3 ≈ qualité 300 DPI) — aucun serveur requis.",
        "export_cloud_on": "  ☁️ Chaque export est aussi enregistré dans la collection cloud partagée.",
        "export_cloud_off": "  (Collection cloud non configurée — téléchargement local uniquement.)",
        "footer": "🍁 金牌橋藝教室🍁",
        "err_banner_prefix": "⚠️ La donne contient des erreurs, merci de corriger avant d'exporter :\n\n",
        "err_invalid_char": "{seat} {suit} : « {raw} » contient un caractère non reconnu « {bad} », merci de corriger",
        "err_dup_same_seat": "{seat} {suit} : {rank} a été saisi {n} fois",
        "err_dup_cross_seat": "{suit} {rank} apparaît à la fois chez {names} : une carte ne peut appartenir qu'à une seule main",
        "err_over13": "{seat} a actuellement {n} cartes, au-delà de la limite de 13 : merci de retirer les cartes en trop",
        "seat_join_sep": " et ",
        "seat_with_suffix": "{seat}",
        "card_title_fallback": "Donne de Bridge",
        "card_board": "Donne {n}",
        "card_dealer": "Donneur {seat}",
        "card_vuln": "Vul {vuln}",
        "card_bidding_title": "Enchères",
        "card_notes_title": "Notes",
        "js_export_btn": "📸 Générer et Télécharger l'Image (PNG)",
        "js_generating": "Génération en cours… (la première fois prend quelques secondes)",
        "js_success_prefix": "✅ Généré ",
        "js_success_suffix": "  (si le téléchargement automatique ne fonctionne pas, appui long / clic droit sur la miniature ci-dessous pour enregistrer)",
        "js_cloud_saved": "  ·  ☁️ Enregistré dans la collection cloud",
        "js_cloud_unconfirmed": "  ·  ☁️ Envoyé (état du cloud non confirmé)",
        "js_failed_prefix": "Échec de la génération : ",
        "js_error_panel_title": "⚠️ Corrigez la donne avant d'exporter",
        "ex_title": "Championnat d'Automne 2026",
        "ex_session": "Tour 3",
        "ex_room": "Salle Ouverte",
        "ex_n": "P. Martin", "ex_s": "J. Dubois",
        "ex_bidding": "1SA  P  3SA  P\nP  P",
        "ex_notes": "1SA : 15–17 points d'honneur, main régulière\n3SA : contrat de manche",
    },
}


# ---------------------------------------------------------------------------
# Streamlit 介面
# ---------------------------------------------------------------------------
st.session_state.setdefault("lang", "zh-Hant")
lang: str = st.session_state["lang"]
if lang not in STR:
    lang = "zh-Hant"
S = STR[lang]

st.set_page_config(page_title=S["page_title"], page_icon="🍁", layout="wide")

UI_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@500;700;900&family=Noto+Serif+SC:wght@500;700;900&display=swap');

.stApp {{
  background:
    radial-gradient(1100px 520px at 12% -8%, #F6E4CE 0%, rgba(246,228,206,0) 60%),
    radial-gradient(900px 480px at 108% 4%, #F3D7C2 0%, rgba(243,215,194,0) 55%),
    linear-gradient(180deg, {PALETTE['parchment']} 0%, {PALETTE['outer']} 100%);
}}
.block-container {{ padding-top:1.4rem; max-width:1400px; }}

/* 語言切換列 */
.st-key-langbar {{ margin-bottom:.6rem; }}
.st-key-langbar .stButton > button {{
  font-family:-apple-system,'Noto Sans TC',sans-serif;
  font-weight:600; font-size:.82rem; letter-spacing:.3px;
  padding:.35rem .5rem; border-radius:8px;
  background:{PALETTE['parchment_hi']}; color:{PALETTE['header_ink']};
  border:1px solid {PALETTE['hairline']}; box-shadow:none;
}}
.st-key-langbar .stButton > button:hover {{
  background:{PALETTE['tea']}; transform:none; box-shadow:none; filter:none;
}}
.st-key-langbar .stButton > button[kind="primary"] {{
  background:linear-gradient(120deg,{PALETTE['crimson_deep']},{PALETTE['ember']});
  color:#FFF4E8; border-color:transparent;
}}

/* 沉浸式橫幅 */
.autumn-banner {{
  position:relative; border-radius:18px; overflow:hidden;
  padding:26px 30px 24px;
  background:linear-gradient(120deg,{PALETTE['crimson_deep']} 0%,{PALETTE['crimson']} 42%,{PALETTE['ember']} 100%);
  box-shadow:0 12px 30px rgba(158,42,43,.28);
  color:#FFF4E8; margin-bottom:1.2rem;
}}
.autumn-banner::after {{
  content:"🍁"; position:absolute; right:-8px; bottom:-18px;
  font-size:120px; opacity:.16; transform:rotate(-12deg);
}}
.autumn-banner h1 {{
  font-family:'Noto Serif TC',serif; font-weight:900;
  font-size:1.7rem; margin:0 0 .3rem; letter-spacing:.5px;
}}
.autumn-banner p {{ margin:0; font-size:.95rem; opacity:.92; letter-spacing:.3px; }}

section[data-testid="stSidebar"] {{
  background:linear-gradient(180deg,{PALETTE['parchment_hi']},{PALETTE['tea']});
  border-right:1px solid {PALETTE['hairline']};
}}
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {{ color:{PALETTE['crimson_deep']}; }}

h2, h3 {{ font-family:'Noto Serif TC',serif; color:{PALETTE['crimson_deep']}; }}

.stButton > button, .stDownloadButton > button {{
  font-family:'Noto Serif TC',serif; font-weight:700; letter-spacing:1px;
  border:none; border-radius:12px; padding:.6rem 1.1rem;
  color:#FFF4E8;
  background:linear-gradient(120deg,{PALETTE['crimson_deep']},{PALETTE['ember']});
  box-shadow:0 6px 16px rgba(158,42,43,.30); transition:all .18s ease;
}}
.stDownloadButton > button {{ width:100%; font-size:1.02rem; padding:.8rem 1rem; }}
.stButton > button:hover, .stDownloadButton > button:hover {{
  transform:translateY(-2px);
  box-shadow:0 10px 24px rgba(231,111,81,.45),0 0 0 3px rgba(212,163,115,.35);
  filter:brightness(1.05);
}}
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {{
  border-radius:10px !important;
}}
.stTextInput input:focus, .stTextArea textarea:focus {{
  border-color:{PALETTE['ember']} !important;
  box-shadow:0 0 0 2px rgba(231,111,81,.25) !important;
}}
div[data-testid="stExpander"] {{
  border:1px solid {PALETTE['hairline']}; border-radius:12px;
  background:{PALETTE['parchment_hi']};
}}
.preview-wrap {{
  position:sticky; top:1rem;
  background:{PALETTE['outer']};
  border:1px solid {PALETTE['hairline']};
  border-radius:16px; padding:10px;
  box-shadow:inset 0 2px 8px rgba(91,58,41,.10);
}}
hr {{ border-color:{PALETTE['hairline']}; }}
</style>
"""
st.markdown(UI_CSS, unsafe_allow_html=True)

# ---- 語言切換 --------------------------------------------------------------
with st.container(key="langbar"):
    lang_cols = st.columns(len(LANGS))
    for i, (code, label) in enumerate(LANGS):
        with lang_cols[i]:
            if st.button(
                label, key=f"langbtn_{code}", use_container_width=True,
                type="primary" if code == lang else "secondary",
            ):
                st.session_state["lang"] = code
                st.rerun()

st.markdown(
    f"""
<div class="autumn-banner">
  <h1>{S['banner_h1']}</h1>
  <p>{S['banner_p']}</p>
</div>
""",
    unsafe_allow_html=True,
)

# ---- 預設牌局 -------------------------------------------------------------
DEFAULT_HANDS = {
    "N": {"S": "A K Q", "H": "K J 7 4", "D": "A 6 3", "C": "Q 8 2"},
    "E": {"S": "J 9 5", "H": "A Q 9", "D": "K T 9 8", "C": "K 7 5"},
    "S": {"S": "T 8 6 4 2", "H": "T 6 5", "D": "7 4", "C": "A J 3"},
    "W": {"S": "7 3", "H": "8 3 2", "D": "Q J 5 2", "C": "T 9 6 4"},
}
SEAT_ZH = SEAT_NAME[lang]  # 供本頁使用的目前語系座位名稱

with st.expander(S["guide_title"], expanded=False):
    st.markdown(S["guide_md"])

# ---- 範例牌局（僅供「載入範例」按鈕填入，預設欄位一律留空）------------------
# 用 board=1 讓「依牌號自動帶入」算出發牌者=北，與範例叫牌（北開 1NT）一致
EXAMPLE = {
    "f_title": S["ex_title"],
    "f_session": S["ex_session"],
    "f_board": "1",
    "f_dealer": "N",
    "f_vuln": "none",
    "f_room": S["ex_room"],
    "nm_W": "", "nm_N": S["ex_n"], "nm_E": "", "nm_S": S["ex_s"],
    "f_bidding": S["ex_bidding"],
    "f_notes": S["ex_notes"],
    # 第二段叫牌記錄預設留空（載入範例 / 全部清空都會把它歸零，不影響顯示與否的勾選）
    "f_room2": "", "nm2_W": "", "nm2_N": "", "nm2_E": "", "nm2_S": "",
    "f_bidding2": "", "f_notes2": "",
}
for _seat, _holds in DEFAULT_HANDS.items():
    for _k, _v in _holds.items():
        EXAMPLE[f"h_{_seat}_{_k}"] = _v

# 選擇鈕仍需一個預設選項（不是空白文字框，不影響「可修改」的辨識度）
st.session_state.setdefault("f_dealer", "N")
st.session_state.setdefault("f_vuln", "ns")
st.session_state.setdefault("f_auto_dv", True)
st.session_state.setdefault("f_show_room2", False)

form_col, preview_col = st.columns([1, 1], gap="large")

# ======================= 左：輸入鍵 =======================
with form_col:
    eb1, eb2 = st.columns(2)
    if eb1.button(S["btn_load_sample"], use_container_width=True):
        for _key, _val in EXAMPLE.items():
            st.session_state[_key] = _val
        st.rerun()
    if eb2.button(S["btn_clear_all"], use_container_width=True):
        for _key in EXAMPLE:
            if not _key.startswith("f_dealer") and not _key.startswith("f_vuln"):
                st.session_state[_key] = ""
        st.rerun()
    st.caption(S["edit_hint"])

    # ---- ① 基本資訊 ----
    st.markdown(S["h_section1"])
    title = st.text_input(S["f_title"], key="f_title", placeholder=S["ph_title"])
    session = st.text_input(S["f_session"], key="f_session", placeholder=S["ph_session"])
    board = st.text_input(S["f_board"], key="f_board", placeholder=S["ph_board"])

    auto_dv = st.checkbox(S["auto_dv_label"], key="f_auto_dv")
    board_num = parse_board_number(board)

    if auto_dv and board_num:
        dealer = board_to_dealer(board_num)
        vuln_key = board_to_vuln_key(board_num)
        # 同步存回 session_state，若之後取消勾選改手動，選項會接續這個值
        st.session_state["f_dealer"] = dealer
        st.session_state["f_vuln"] = vuln_key
        wrap_note = (
            S["auto_dv_wrap"].format(m=((board_num - 1) % 16) + 1) if board_num > 16 else ""
        )
        st.caption(S["auto_dv_result"].format(
            n=board_num, seat=SEAT_ZH[dealer], code=dealer,
            vuln=VULN_LABEL[lang][vuln_key], wrap=wrap_note,
        ))
    else:
        if auto_dv:
            st.caption(S["auto_dv_invalid"])
        d1, d2 = st.columns(2)
        with d1:
            dealer = st.radio(S["f_dealer"], SEATS, key="f_dealer", horizontal=True,
                              format_func=lambda x: SEAT_ZH[x])
        with d2:
            vuln_key = st.radio(
                S["f_vuln"], VULN_KEYS, key="f_vuln", horizontal=True,
                format_func=lambda k: VULN_LABEL[lang][k],
            )

    # ---- ② 四家手牌 ----
    st.markdown(S["h_section2"])
    hands: dict = {}
    for seat in ["W", "N", "E", "S"]:
        heading = S["seat_hand_heading"].format(seat=SEAT_ZH[seat], en=SEAT_NAME["en"][seat])
        st.markdown(f"**{heading}**")
        hands[seat] = {}
        scols = st.columns(4)
        for i, (key, sym) in enumerate(SUITS):
            with scols[i]:
                hands[seat][key] = st.text_input(
                    sym, key=f"h_{seat}_{key}",
                    placeholder=DEFAULT_HANDS[seat][key].replace(" ", ""),
                )

    hand_errors = validate_hands(hands, lang)
    if hand_errors:
        st.error(S["err_banner_prefix"] + "\n".join(f"- {e}" for e in hand_errors))

    # ---- ③ 叫牌區 ----
    st.markdown(S["h_section3"])
    room = st.text_input(S["f_room"], key="f_room", placeholder=S["ph_room"])
    st.caption(S["first_seat_caption"].format(seat=SEAT_ZH[dealer], code=dealer))
    st.caption(S["names_caption"])
    n1, n2 = st.columns(2)
    names = {}
    with n1:
        names["W"] = st.text_input(S["f_name"].format(seat=SEAT_ZH["W"]), key="nm_W", placeholder=S["ph_name"])
        names["N"] = st.text_input(S["f_name"].format(seat=SEAT_ZH["N"]), key="nm_N", placeholder=S["ph_name"])
    with n2:
        names["E"] = st.text_input(S["f_name"].format(seat=SEAT_ZH["E"]), key="nm_E", placeholder=S["ph_name"])
        names["S"] = st.text_input(S["f_name"].format(seat=SEAT_ZH["S"]), key="nm_S", placeholder=S["ph_name"])
    bidding = st.text_area(
        S["f_bidding"], key="f_bidding", height=120, placeholder=S["ph_bidding"],
    )
    notes = st.text_area(
        S["f_notes"], key="f_notes", height=90, placeholder=S["ph_notes"],
    )

    show_room2 = st.checkbox(S["show_room2_label"], key="f_show_room2")
    room2 = None
    if show_room2:
        st.markdown(S["room2_heading"])
        room_b = st.text_input(S["f_room2"], key="f_room2", placeholder=S["ph_room2"])
        st.caption(S["names2_caption"])
        n1b, n2b = st.columns(2)
        names_b = {}
        with n1b:
            names_b["W"] = st.text_input(S["f_name2"].format(seat=SEAT_ZH["W"]), key="nm2_W", placeholder=S["ph_name"])
            names_b["N"] = st.text_input(S["f_name2"].format(seat=SEAT_ZH["N"]), key="nm2_N", placeholder=S["ph_name"])
        with n2b:
            names_b["E"] = st.text_input(S["f_name2"].format(seat=SEAT_ZH["E"]), key="nm2_E", placeholder=S["ph_name"])
            names_b["S"] = st.text_input(S["f_name2"].format(seat=SEAT_ZH["S"]), key="nm2_S", placeholder=S["ph_name"])
        bidding_b = st.text_area(
            S["f_bidding2"], key="f_bidding2", height=120, placeholder=S["ph_bidding2"],
        )
        notes_b = st.text_area(S["f_notes2"], key="f_notes2", height=90)
        room2 = {"room": room_b, "names": names_b, "bidding": bidding_b, "notes": notes_b}

data = {
    "title": title,
    "session": session,
    "board": (board or "").strip(),
    "dealer": dealer,
    "vuln_label": VULN_LABEL[lang][vuln_key],
    "vuln_seats": VULN_SEATS[vuln_key],
    "hands": hands,
    "room": room,
    "first_seat": dealer,  # 叫牌永遠從發牌者開始
    "names": names,
    "bidding": bidding,
    "notes": notes,
    "room2_enabled": show_room2,
    "room2": room2,
}

# ======================= 右：即時預覽 + 下載（瀏覽器端產圖） =======================
with preview_col:
    st.markdown(S["h_preview"])
    meta = " · ".join(
        x for x in [
            data.get("title", ""), data.get("session", ""),
            (S["card_board"].format(n=data["board"]) if data.get("board") else ""),
            (data.get("room") or ""),
            f"[{lang}]",
        ] if x
    )
    preview_html = build_diagram_html(
        data, lang, scale=1.0, interactive=True,
        webhook=_secret("drive_webhook_url"),
        secret=_secret("drive_webhook_secret"),
        meta=meta,
        errors=hand_errors,
    )
    n_rows = len(parse_bidding(data["bidding"], data["first_seat"], lang))
    n_notes = len([x for x in (notes or "").splitlines() if x.strip()])
    if data["room2_enabled"] and data["room2"]:
        n_rows += len(parse_bidding(data["room2"]["bidding"], data["first_seat"], lang))
        n_notes += len([x for x in data["room2"]["notes"].splitlines() if x.strip()])
    height = 640 + 44 * n_rows + 28 * n_notes + 320 + (140 if data["room2_enabled"] else 0)
    if hand_errors:
        height += 40 + 24 * len(hand_errors)
    st.markdown('<div class="preview-wrap">', unsafe_allow_html=True)
    st.components.v1.html(preview_html, height=height, scrolling=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.caption(
        S["export_caption"]
        + (S["export_cloud_on"] if drive_enabled() else S["export_cloud_off"])
    )

st.divider()
st.caption(S["footer"])
