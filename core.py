# -*- coding: utf-8 -*-
"""
共用引擎 · Shared engine for the Chinese and English apps.

app.py     → run_app("zh")   繁體中文（原始版本，行為不變）
app_en.py  → run_app("en")   全英文版本

兩個版本共用同一支 Google Apps Script webhook（drive_webhook_url / drive_webhook_secret），
匯出的 PNG 會存進同一個雲端硬碟資料夾。
"""

from __future__ import annotations

import base64
import io
import re
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------------------------
# 秋季楓葉色彩計畫 (Autumn Palette)
# ---------------------------------------------------------------------------
PALETTE = {
    "crimson_deep": "#9E2A2B",
    "crimson": "#BA181B",
    "suit_red": "#C1121F",
    "walnut": "#2B231F",
    "amber": "#D4A373",
    "ember": "#E76F51",
    "parchment": "#FAF8F5",
    "parchment_hi": "#FDFBF7",
    "tea": "#F9F6F0",
    "maple_wood": "#FDE68A",
    "header_ink": "#5B3A29",
    "outer": "#EFE6D8",
    "hairline": "#E7D8C3",
}

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
SUITS = [("S", "♠"), ("H", "♥"), ("D", "♦"), ("C", "♣")]
RED_SUITS = {"H", "D"}

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


SEATS = ["W", "N", "E", "S"]

VULN_KEYS = ["none", "ns", "ew", "both"]
VULN_SEATS = {
    "none": set(),
    "ns": {"N", "S"},
    "ew": {"E", "W"},
    "both": {"N", "S", "E", "W"},
}

SEAT_NAME = {
    "zh": {"W": "西", "N": "北", "E": "東", "S": "南"},
    "en": {"W": "West", "N": "North", "E": "East", "S": "South"},
}

# ---------------------------------------------------------------------------
# 語系字串
# ---------------------------------------------------------------------------
STR: dict[str, dict] = {
    "zh": {
        "html_lang": "zh-Hant",
        "page_title": "牌局與叫牌排版工作台",
        "banner_h1": "\U0001f341 牌局與叫牌排版工作台",
        "banner_p": "免登入 · 即時預覽 · 一鍵下載出版級 PNG",
        "guide_title": "\U0001f4d6 輸入說明 · 快速對照鍵（第一次使用請先看）",
        "guide_md": """
| 區塊 | 怎麼填 |
| --- | --- |
| **① 基本資訊** | 賽事名稱、副數與發牌、發牌者、身價（雙無 / 南北 / 東西 / 雙方） |
| **② 四家手牌** | 每家 ♠♥♦♣ 各一格，直接打點數如 `AKQ` 或 `A K Q`；`10` 自動轉 `T`；**缺門打 `--`** |
| **③ 叫牌區** | 室別標題、四席選手姓名、叫牌序列（**每行一輪**、空白分隔、`P`=Pass `X`=Dbl `XX`=Rdbl）、叫牌註解 |

先在「**開叫席位**」選第一個叫牌的人，系統會自動把叫品對齊正確欄位。改好任一欄位，右側預覽即時更新 → 按「\U0001f4f8 匯出」下載 PNG。
""",
        "btn_sample": "\U0001f3b4 載入範例牌局",
        "btn_clear": "\U0001f9f9 全部清空",
        "edit_hint": "\U0001f447 下面每一格都可以點進去輸入 / 修改；空白處的淡灰字只是範例提示。",
        "h_basics": "### ① 基本資訊",
        "f_title": "賽事名稱",
        "ph_title": "例：2026 中華橋協秋季公開賽",
        "f_session": "副數與發牌",
        "ph_session": "例：第 3 循環",
        "f_board": "發牌編號",
        "ph_board": "例：18",
        "f_dealer": "發牌者 (Dealer)",
        "f_vuln": "身價 (Vulnerability)",
        "vuln": {"none": "雙無", "ns": "南北", "ew": "東西", "both": "雙方"},
        "h_hands": "### ② 四家手牌　·　缺門請輸入 `--`",
        "seat_form": {"W": "西家 West", "N": "北家 North", "E": "東家 East", "S": "南家 South"},
        "h_auction": "### ③ 叫牌區",
        "f_room": "室別標題",
        "ph_room": "例：公開室 Open Room",
        "f_first": "開叫席位（第一個叫牌的人）",
        "cap_names": "選手席位姓名",
        "f_name": {"W": "西 選手", "N": "北 選手", "E": "東 選手", "S": "南 選手"},
        "ph_name": "選填",
        "f_bidding": "多行文字叫牌序列（每行一輪；空白分隔；P=Pass、X=Dbl、XX=Rdbl）",
        "ph_bidding": "1NT  P  3NT  P\nP  P",
        "f_notes": "叫牌註解備註（每行一則）",
        "ph_notes": "1NT：15–17 大牌點，平均牌型\n3NT：北家有把握的一擊到位",
        "h_preview": "### \U0001f341 即時預覽",
        "h_export": "#### 匯出",
        "cap_export": "寬 620px、300DPI 級（3×）高解析度照片，自動裁切留白。",
        "cap_cloud": "☁️ 產出後除了可下載，也會自動存入雲端硬碟收藏。",
        "btn_export": "\U0001f4f8 匯出牌局叫牌圖",
        "sp_render": "正在以楓葉油墨印製…",
        "sp_upload": "同步到雲端硬碟收藏…",
        "err_export": "匯出失敗：{}",
        "info_export": "若在雲端，請確認 packages.txt 已安裝 chromium，並 Reboot app 一次。",
        "dl_prefix": "⬇️ 下載 ",
        "ok_cloud": "☁️ 已存入雲端硬碟收藏。",
        "ok_cloud_link": "　[開啟]({})",
        "warn_cloud": "雲端硬碟同步未成功（下載不受影響）：{}",
        "cap_final": "最終產出（已下載檔）",
        "footer": "\U0001f341 金牌橋藝教室\U0001f341",
        "card_title_fallback": "橋牌牌局",
        "card_board": "第 {} 副",
        "card_dealer": "發牌 {}",
        "card_vuln": "身價 {}",
        "card_bidding": "叫牌記錄 · Bidding",
        "card_notes": "叫牌註解",
        "card_brand": "金牌橋藝教室",
        "ex_title": "2026 中華橋協秋季公開賽",
        "ex_session": "第 3 循環",
        "ex_room": "公開室 Open Room",
        "ex_n": "王小明",
        "ex_s": "李大華",
        "ex_notes": "1NT：15–17 大牌點，平均牌型\n3NT：北家有把握的一擊到位",
    },
    "en": {
        "html_lang": "en",
        "page_title": "Bridge Deal & Auction Layout",
        "banner_h1": "\U0001f341 Bridge Deal & Auction Studio",
        "banner_p": "No login · Live preview · One-click publication-grade PNG",
        "guide_title": "\U0001f4d6 Quick input guide (please read first)",
        "guide_md": """
| Section | How to fill it |
| --- | --- |
| **① Basics** | Event name, session & board, dealer, vulnerability (None / N-S / E-W / Both) |
| **② The four hands** | One box per suit ♠♥♦♣; type ranks like `AKQ` or `A K Q`; `10` becomes `T`; **use `--` for a void** |
| **③ Auction** | Room label, player names, the auction (**one round per line**, space-separated, `P`=Pass `X`=Dbl `XX`=Rdbl), and notes |

Pick the **opening seat** first so the calls line up under the right column. Edit any field and the preview updates live → click **\U0001f4f8 Export** to download the PNG.
""",
        "btn_sample": "\U0001f3b4 Load sample deal",
        "btn_clear": "\U0001f9f9 Clear all",
        "edit_hint": "\U0001f447 Every box below is editable — the faint grey text is just an example hint.",
        "h_basics": "### ① Basics",
        "f_title": "Event name",
        "ph_title": "e.g. 2026 Autumn Open Teams",
        "f_session": "Session & board",
        "ph_session": "e.g. Round 3",
        "f_board": "Board no.",
        "ph_board": "e.g. 18",
        "f_dealer": "Dealer",
        "f_vuln": "Vulnerability",
        "vuln": {"none": "None", "ns": "N-S", "ew": "E-W", "both": "Both"},
        "h_hands": "### ② The four hands　·　use `--` for a void",
        "seat_form": {"W": "West", "N": "North", "E": "East", "S": "South"},
        "h_auction": "### ③ Auction",
        "f_room": "Room label",
        "ph_room": "e.g. Open Room",
        "f_first": "Opening seat (who bids first)",
        "cap_names": "Player names by seat",
        "f_name": {"W": "West player", "N": "North player", "E": "East player", "S": "South player"},
        "ph_name": "optional",
        "f_bidding": "Auction — one round per line; space-separated; P=Pass, X=Dbl, XX=Rdbl",
        "ph_bidding": "1NT  P  3NT  P\nP  P",
        "f_notes": "Auction notes (one per line)",
        "ph_notes": "1NT: 15–17 HCP, balanced\n3NT: to play",
        "h_preview": "### \U0001f341 Live preview",
        "h_export": "#### Export",
        "cap_export": "620px wide, 300 DPI-class (3×), whitespace auto-trimmed.",
        "cap_cloud": "☁️ Exports are also saved to the shared Google Drive collection.",
        "btn_export": "\U0001f4f8 Export deal & auction image",
        "sp_render": "Printing with maple ink…",
        "sp_upload": "Saving to the Drive collection…",
        "err_export": "Export failed: {}",
        "info_export": "On the cloud, make sure packages.txt installs chromium, then Reboot the app once.",
        "dl_prefix": "⬇️ Download ",
        "ok_cloud": "☁️ Saved to the Drive collection.",
        "ok_cloud_link": "　[open]({})",
        "warn_cloud": "Drive sync failed (your download is unaffected): {}",
        "cap_final": "Exported file",
        "footer": "",
        "card_title_fallback": "Bridge Deal",
        "card_board": "Board {}",
        "card_dealer": "Dealer {}",
        "card_vuln": "Vul {}",
        "card_bidding": "Auction",
        "card_notes": "Auction notes",
        "card_brand": "",
        "ex_title": "2026 Autumn Open Teams",
        "ex_session": "Round 3",
        "ex_room": "Open Room",
        "ex_n": "A. Smith",
        "ex_s": "B. Jones",
        "ex_notes": "1NT: 15–17 HCP, balanced\n3NT: to play",
    },
}


# ---------------------------------------------------------------------------
# 手牌 / 叫牌解析
# ---------------------------------------------------------------------------
def clean_holding(raw: str) -> str:
    raw = (raw or "").strip()
    if raw in {"", "-", "--", "—", "void", "VOID"}:
        return "—"
    raw = raw.upper().replace("10", "T")
    raw = re.sub(r"[^AKQJT2-9]", "", raw)
    if not raw:
        return "—"
    order = "AKQJT98765432"
    cards = sorted(raw, key=lambda c: order.index(c) if c in order else 99)
    return " ".join(cards)


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


CALL_ALIASES = {
    "P": "Pass", "PASS": "Pass", "-": "Pass",
    "X": "Dbl", "DBL": "Dbl", "DOUBLE": "Dbl",
    "XX": "Rdbl", "RDBL": "Rdbl", "REDOUBLE": "Rdbl",
}


def fmt_call(token: str) -> str:
    t = token.strip()
    if not t:
        return ""
    up = t.upper()
    if up in CALL_ALIASES:
        label = CALL_ALIASES[up]
        cls = "call-pass" if label == "Pass" else "call-x"
        return f'<span class="{cls}">{label}</span>'
    m = re.match(r"^([1-7])\s*(NT|N|S|H|D|C)$", up)
    if m:
        level, strain = m.group(1), m.group(2)
        if strain in {"NT", "N"}:
            return f'<span class="call-bid">{level}<span class="nt">NT</span></span>'
        return f'<span class="call-bid">{level}{suit_pip(strain, "pip pip-call")}</span>'
    return f'<span class="call-bid">{t}</span>'


def parse_bidding(text: str, first_seat: str) -> list[list[str]]:
    start = SEATS.index(first_seat)
    flat: list[str] = []
    for line in (text or "").splitlines():
        for tok in re.split(r"[\s,]+", line.strip()):
            if tok:
                flat.append(tok)
    cells = [""] * start + [fmt_call(t) for t in flat]
    rows: list[list[str]] = []
    for i in range(0, len(cells), 4):
        chunk = cells[i: i + 4]
        chunk += [""] * (4 - len(chunk))
        rows.append(chunk)
    if not rows:
        rows = [["", "", "", ""]]
    return rows


# ---------------------------------------------------------------------------
# 牌圖 HTML 組裝
# ---------------------------------------------------------------------------
def build_diagram_html(data: dict, *, scale: float = 1.0, for_export: bool = False) -> str:
    p = PALETTE
    lang = data.get("lang", "zh")
    S = STR[lang]
    vuln = data["vuln_seats"]
    dealer = data["dealer"]

    def seat_tag(seat: str) -> str:
        if lang == "en":
            return SEAT_NAME["en"][seat]
        return f'{SEAT_NAME["zh"][seat]} {seat}'

    def compass_cell(seat: str) -> str:
        cls = "cc"
        if seat in vuln:
            cls += " cc-vuln"
        if seat == dealer:
            cls += " cc-dealer"
        tag = '<span class="cc-d">D</span>' if seat == dealer else ""
        return f'<div class="{cls}">{seat}{tag}</div>'

    compass = (
        '<div class="compass">'
        f'  <div class="compass-bg">{maple_svg(p["amber"], 0.16, stem=False)}</div>'
        f'  <div class="cc-row cc-top">{compass_cell("N")}</div>'
        f'  <div class="cc-row cc-mid">{compass_cell("W")}'
        f'    <div class="cc-hub">{data["board"] or "&nbsp;"}</div>'
        f'    {compass_cell("E")}</div>'
        f'  <div class="cc-row cc-bot">{compass_cell("S")}</div>'
        f'  <div class="cc-vlabel">{data["vuln_label"]}</div>'
        '</div>'
    )

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

    if lang == "en":
        head_cols = "".join(f"<th>{SEAT_NAME['en'][s]}</th>" for s in SEATS)
    else:
        head_cols = "".join(
            f'<th>{SEAT_NAME["zh"][s]}<span class="th-en">{SEAT_NAME["en"][s]}</span></th>'
            for s in SEATS
        )
    names = data["names"]
    name_row = "".join(
        f'<td class="nm">{(names.get(s) or "").strip() or "—"}</td>' for s in SEATS
    )
    body_rows = ""
    for i, row in enumerate(parse_bidding(data["bidding"], data["first_seat"])):
        zc = "zebra" if i % 2 else ""
        body_rows += f'<tr class="{zc}">' + "".join(f"<td>{c or ''}</td>" for c in row) + "</tr>"

    note_block = ""
    if (data.get("notes") or "").strip():
        note_lines = "".join(
            f"<li>{ln.strip()}</li>" for ln in data["notes"].splitlines() if ln.strip()
        )
        note_block = (
            f'<div class="notes"><div class="notes-h">{S["card_notes"]}</div>'
            f'<ul>{note_lines}</ul></div>'
        )

    room_line = ""
    if (data.get("room") or "").strip():
        room_line = f'<div class="room">{data["room"].strip()}</div>'

    bidding = (
        '<div class="bidsec">'
        f'  <div class="bidsec-h"><span class="bh-leaf">{maple_svg(p["crimson"], 1)}</span>'
        f'     {S["card_bidding"]} {room_line}</div>'
        f'  <table class="bidtable">'
        f'     <thead><tr>{head_cols}</tr>'
        f'     <tr class="names">{name_row}</tr></thead>'
        f'     <tbody>{body_rows}</tbody>'
        f'  </table>'
        f'  {note_block}'
        '</div>'
    )

    subtitle_bits = []
    if data.get("session"):
        subtitle_bits.append(data["session"])
    if data.get("board"):
        subtitle_bits.append(S["card_board"].format(data["board"]))
    subtitle_bits.append(S["card_dealer"].format(dealer))
    subtitle_bits.append(S["card_vuln"].format(data["vuln_label"]))
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

    brand = S["card_brand"]
    footer = (
        '<footer class="ftr">'
        f'  {wind_divider(p["amber"])}'
        f'{f"<span>{brand}</span>" if brand else ""}'
        '</footer>'
    )

    css = _diagram_css(scale)
    return f"""<!doctype html><html lang="{S['html_lang']}"><head><meta charset="utf-8">
<style>{css}</style></head>
<body class="{'export' if for_export else 'preview'}">
  <div class="card">
    {header}
    {wind_divider(PALETTE['amber'])}
    {grid}
    {bidding}
    {footer}
  </div>
</body></html>"""


def _diagram_css(scale: float) -> str:
    p = PALETTE
    s = scale
    return f"""
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
  font-family:'Noto Serif TC','Songti TC','Source Han Serif TC',
    'Hiragino Mincho ProN','PingFang TC',Georgia,'Times New Roman',serif;
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

.hdr {{ display:flex; align-items:center; justify-content:center;
  gap:{16*s}px; padding:{6*s}px 0 {4*s}px; }}
.hdr-leaf {{ width:{40*s}px; height:{40*s}px; flex:0 0 auto; display:block; }}
.hdr-leaf.l {{ transform:rotate(-18deg); }}
.hdr-leaf.r {{ transform:rotate(16deg) scaleX(-1); }}
.hdr-mid {{ text-align:center; }}
.hdr h1 {{
  font-size:{34*s}px; line-height:1.15; color:{p['crimson_deep']};
  font-weight:800; letter-spacing:{1*s}px; margin:{2*s}px 0 {6*s}px;
  text-shadow:0 {1*s}px 0 rgba(255,255,255,.6);
}}
.subtitle {{ font-size:{18*s}px; color:{p['header_ink']}; letter-spacing:{.5*s}px; }}

.wind {{ display:block; width:100%; height:{18*s}px; margin:{4*s}px 0 {8*s}px; }}

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
.seat {{ min-width:{188*s}px; max-width:{210*s}px; }}
.seat-tag {{
  font-size:{18*s}px; letter-spacing:{2*s}px; color:{p['ember']};
  font-weight:700; margin-bottom:{3*s}px; text-align:left;
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
.cc-vlabel {{
  position:absolute; bottom:{5*s}px; left:0; right:0; text-align:center;
  font-size:{11*s}px; font-weight:700; letter-spacing:{1.5*s}px;
  color:{p['header_ink']}; opacity:.7;
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

.bidsec {{ margin-top:{8*s}px; }}
.bidsec-h {{
  display:flex; align-items:center; gap:{8*s}px;
  font-size:{18*s}px; font-weight:800; color:{p['crimson_deep']};
  padding-bottom:{7*s}px;
}}
.bh-leaf {{ width:{20*s}px; height:{20*s}px; display:inline-block; }}
.room {{
  margin-left:auto; font-size:{15*s}px; font-weight:700; letter-spacing:{1*s}px;
  color:{p['header_ink']}; background:{p['maple_wood']};
  border:{1*s}px solid {p['amber']}; border-radius:{20*s}px;
  padding:{3*s}px {12*s}px;
}}
.bidtable {{ width:100%; border-collapse:separate; border-spacing:0;
  border:{1*s}px solid {p['amber']}; border-radius:{8*s}px; overflow:hidden;
  font-size:{18*s}px; }}
.bidtable th {{
  background:linear-gradient(180deg,{p['maple_wood']},#F6D976);
  color:{p['header_ink']}; font-weight:800;
  padding:{7*s}px {4*s}px {6*s}px; text-align:center;
  border-bottom:{1*s}px solid {p['amber']};
  letter-spacing:{1*s}px;
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
  background:#FBEFD9; font-size:{16*s}px; font-weight:700; color:{p['header_ink']};
  padding:{5*s}px {4*s}px; border-bottom:{1.4*s}px solid {p['amber']};
}}
td.nm {{ letter-spacing:{.5*s}px; }}
.call-bid {{ font-weight:800; color:{p['walnut']}; display:inline-flex;
  align-items:center; gap:{2*s}px; }}
.pip-call {{ width:{17*s}px; height:{17*s}px; }}
.call-bid .nt {{ font-size:{13*s}px; letter-spacing:{.5*s}px; }}
.call-pass {{ color:#8A7A63; font-style:italic; }}
.call-x {{ color:{p['suit_red']}; font-weight:800; }}

.notes {{
  margin-top:{8*s}px; background:{p['tea']};
  border:{1*s}px solid {p['hairline']}; border-left:{3*s}px solid {p['ember']};
  border-radius:{6*s}px; padding:{7*s}px {12*s}px;
}}
.notes-h {{ font-size:{15*s}px; font-weight:800; letter-spacing:{1.5*s}px;
  color:{p['ember']}; margin-bottom:{4*s}px; }}
.notes ul {{ margin:0; padding-left:{20*s}px; }}
.notes li {{ font-size:{18*s}px; line-height:1.6; color:{p['header_ink']}; }}

.ftr {{ text-align:center; padding-top:{6*s}px; }}
.ftr span {{ font-size:{13*s}px; letter-spacing:{4*s}px; color:{p['amber']}; }}
"""


# ---------------------------------------------------------------------------
# PNG 匯出
# ---------------------------------------------------------------------------
def _find_chromium() -> str | None:
    import shutil

    candidates = [
        "chromium", "chromium-browser", "chrome", "google-chrome",
        "google-chrome-stable",
        "/usr/bin/chromium", "/usr/bin/chromium-browser",
        "/usr/bin/google-chrome",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
    for c in candidates:
        found = shutil.which(c) if "/" not in c else (c if Path(c).exists() else None)
        if found:
            return found
    return None


def render_png(data: dict) -> bytes:
    from html2image import Html2Image
    from PIL import Image, ImageChops

    export_scale = 3
    html = build_diagram_html(data, scale=export_scale, for_export=True)

    chromium = _find_chromium()
    with tempfile.TemporaryDirectory() as tmp:
        opts = dict(
            output_path=tmp,
            custom_flags=[
                "--no-sandbox",
                "--headless=new",
                "--hide-scrollbars",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--default-background-color=EFE6D8",
                "--force-device-scale-factor=1",
            ],
        )
        if chromium:
            opts["browser_executable"] = chromium
        hti = Html2Image(**opts)
        out_name = "diagram.png"
        hti.screenshot(
            html_str=html,
            save_as=out_name,
            size=(620 * export_scale + 40, 4600),
        )
        raw = Path(tmp) / out_name
        img = Image.open(raw).convert("RGB")

    bg = Image.new("RGB", img.size, (239, 230, 216))
    diff = ImageChops.difference(img, bg)
    bbox = diff.getbbox()
    if bbox:
        pad = 6 * export_scale
        left = max(bbox[0] - pad, 0)
        top = max(bbox[1] - pad, 0)
        right = min(bbox[2] + pad, img.width)
        bottom = min(bbox[3] + pad, img.height)
        img = img.crop((left, top, right, bottom))

    buf = io.BytesIO()
    img.save(buf, format="PNG", dpi=(300, 300), optimize=True)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# 雲端硬碟收集（Google Apps Script Web App）
# ---------------------------------------------------------------------------
def _secret(name: str, default: str = "") -> str:
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:  # noqa: BLE001
        pass
    import os

    return os.environ.get(name.upper(), default)


def drive_enabled() -> bool:
    return bool(_secret("drive_webhook_url"))


def upload_to_drive(png: bytes, filename: str, description: str = "") -> tuple[bool, str]:
    url = _secret("drive_webhook_url")
    if not url:
        return False, "drive_webhook_url not set"
    import requests

    try:
        resp = requests.post(
            url,
            json={
                "filename": filename,
                "mimeType": "image/png",
                "data": base64.b64encode(png).decode("ascii"),
                "secret": _secret("drive_webhook_secret"),
                "description": description,
            },
            timeout=45,
        )
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
    if payload.get("ok"):
        return True, payload.get("url", "")
    return False, str(payload.get("error", "unknown error"))


# ---------------------------------------------------------------------------
# Streamlit 介面
# ---------------------------------------------------------------------------
DEFAULT_HANDS = {
    "N": {"S": "A K Q", "H": "K J 7 4", "D": "A 6 3", "C": "Q 8 2"},
    "E": {"S": "J 9 5", "H": "A Q 9", "D": "K T 9 8", "C": "K 7 5"},
    "S": {"S": "T 8 6 4 2", "H": "T 6 5", "D": "7 4", "C": "A J 3"},
    "W": {"S": "7 3", "H": "8 3 2", "D": "Q J 5 2", "C": "T 9 6 4"},
}


def _example(lang: str) -> dict:
    S = STR[lang]
    ex = {
        "f_title": S["ex_title"],
        "f_session": S["ex_session"],
        "f_board": "18",
        "f_dealer": "N",
        "f_vuln": "ns",
        "f_room": S["ex_room"],
        "f_first": "N",
        "nm_W": "", "nm_N": S["ex_n"], "nm_E": "", "nm_S": S["ex_s"],
        "f_bidding": "1NT  P  3NT  P\nP  P",
        "f_notes": S["ex_notes"],
    }
    for seat, holds in DEFAULT_HANDS.items():
        for k, v in holds.items():
            ex[f"h_{seat}_{k}"] = v
    return ex


def _ui_css() -> str:
    P = PALETTE
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@500;700;900&display=swap');

.stApp {{
  background:
    radial-gradient(1100px 520px at 12% -8%, #F6E4CE 0%, rgba(246,228,206,0) 60%),
    radial-gradient(900px 480px at 108% 4%, #F3D7C2 0%, rgba(243,215,194,0) 55%),
    linear-gradient(180deg, {P['parchment']} 0%, {P['outer']} 100%);
}}
.block-container {{ padding-top:1.4rem; max-width:1400px; }}

.autumn-banner {{
  position:relative; border-radius:18px; overflow:hidden;
  padding:26px 30px 24px;
  background:linear-gradient(120deg,{P['crimson_deep']} 0%,{P['crimson']} 42%,{P['ember']} 100%);
  box-shadow:0 12px 30px rgba(158,42,43,.28);
  color:#FFF4E8; margin-bottom:1.2rem;
}}
.autumn-banner::after {{
  content:"\U0001f341"; position:absolute; right:-8px; bottom:-18px;
  font-size:120px; opacity:.16; transform:rotate(-12deg);
}}
.autumn-banner h1 {{
  font-family:'Noto Serif TC',serif; font-weight:900;
  font-size:1.9rem; margin:0 0 .3rem; letter-spacing:1px;
}}
.autumn-banner p {{ margin:0; font-size:.95rem; opacity:.92; letter-spacing:.5px; }}

h2, h3 {{ font-family:'Noto Serif TC',serif; color:{P['crimson_deep']}; }}

.stButton > button, .stDownloadButton > button {{
  font-family:'Noto Serif TC',serif; font-weight:700; letter-spacing:1px;
  border:none; border-radius:12px; padding:.6rem 1.1rem;
  color:#FFF4E8;
  background:linear-gradient(120deg,{P['crimson_deep']},{P['ember']});
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
  border-color:{P['ember']} !important;
  box-shadow:0 0 0 2px rgba(231,111,81,.25) !important;
}}
div[data-testid="stExpander"] {{
  border:1px solid {P['hairline']}; border-radius:12px;
  background:{P['parchment_hi']};
}}
.preview-wrap {{
  position:sticky; top:1rem;
  background:{P['outer']};
  border:1px solid {P['hairline']};
  border-radius:16px; padding:10px;
  box-shadow:inset 0 2px 8px rgba(91,58,41,.10);
}}
hr {{ border-color:{P['hairline']}; }}
</style>
"""


def run_app(lang: str) -> None:
    """繪出整個 Streamlit 介面。lang = "zh" 或 "en"。"""
    S = STR[lang]

    st.set_page_config(page_title=S["page_title"], page_icon="\U0001f341", layout="wide")
    st.markdown(_ui_css(), unsafe_allow_html=True)
    st.markdown(
        f"""
<div class="autumn-banner">
  <h1>{S['banner_h1']}</h1>
  <p>{S['banner_p']}</p>
</div>
""",
        unsafe_allow_html=True,
    )

    example = _example(lang)
    st.session_state.setdefault("f_dealer", "N")
    st.session_state.setdefault("f_vuln", "ns")
    st.session_state.setdefault("f_first", "N")

    with st.expander(S["guide_title"], expanded=False):
        st.markdown(S["guide_md"])

    form_col, preview_col = st.columns([1, 1], gap="large")

    with form_col:
        eb1, eb2 = st.columns(2)
        if eb1.button(S["btn_sample"], use_container_width=True):
            for k, v in example.items():
                st.session_state[k] = v
            st.rerun()
        if eb2.button(S["btn_clear"], use_container_width=True):
            for k in example:
                if not k.startswith(("f_dealer", "f_vuln", "f_first")):
                    st.session_state[k] = ""
            st.rerun()
        st.caption(S["edit_hint"])

        st.markdown(S["h_basics"])
        title = st.text_input(S["f_title"], key="f_title", placeholder=S["ph_title"])
        session = st.text_input(S["f_session"], key="f_session", placeholder=S["ph_session"])
        b1, b2 = st.columns([1, 2])
        with b1:
            board = st.text_input(S["f_board"], key="f_board", placeholder=S["ph_board"])
        with b2:
            dealer = st.radio(
                S["f_dealer"], SEATS, key="f_dealer", horizontal=True,
                format_func=lambda x: SEAT_NAME[lang][x],
            )
        vuln_key = st.radio(
            S["f_vuln"], VULN_KEYS, key="f_vuln", horizontal=True,
            format_func=lambda k: S["vuln"][k],
        )

        st.markdown(S["h_hands"])
        hands: dict = {}
        for seat in ["W", "N", "E", "S"]:
            st.markdown(f"**{S['seat_form'][seat]}**")
            hands[seat] = {}
            scols = st.columns(4)
            for i, (key, sym) in enumerate(SUITS):
                with scols[i]:
                    hands[seat][key] = st.text_input(
                        sym, key=f"h_{seat}_{key}",
                        placeholder=DEFAULT_HANDS[seat][key].replace(" ", ""),
                    )

        st.markdown(S["h_auction"])
        room = st.text_input(S["f_room"], key="f_room", placeholder=S["ph_room"])
        first_seat = st.radio(
            S["f_first"], SEATS, key="f_first", horizontal=True,
            format_func=lambda x: SEAT_NAME[lang][x],
        )
        st.caption(S["cap_names"])
        n1, n2 = st.columns(2)
        names = {}
        with n1:
            names["W"] = st.text_input(S["f_name"]["W"], key="nm_W", placeholder=S["ph_name"])
            names["N"] = st.text_input(S["f_name"]["N"], key="nm_N", placeholder=S["ph_name"])
        with n2:
            names["E"] = st.text_input(S["f_name"]["E"], key="nm_E", placeholder=S["ph_name"])
            names["S"] = st.text_input(S["f_name"]["S"], key="nm_S", placeholder=S["ph_name"])
        bidding = st.text_area(
            S["f_bidding"], key="f_bidding", height=120, placeholder=S["ph_bidding"],
        )
        notes = st.text_area(
            S["f_notes"], key="f_notes", height=90, placeholder=S["ph_notes"],
        )

    data = {
        "lang": lang,
        "title": title,
        "session": session,
        "board": (board or "").strip(),
        "dealer": dealer,
        "vuln_key": vuln_key,
        "vuln_label": S["vuln"][vuln_key],
        "vuln_seats": VULN_SEATS[vuln_key],
        "hands": hands,
        "room": room,
        "first_seat": first_seat,
        "names": names,
        "bidding": bidding,
        "notes": notes,
    }

    with preview_col:
        st.markdown(S["h_preview"])
        preview_html = build_diagram_html(data, scale=1.0, for_export=False)
        n_rows = len(parse_bidding(data["bidding"], data["first_seat"]))
        n_notes = len([x for x in (notes or "").splitlines() if x.strip()])
        height = 470 + 34 * n_rows + 22 * n_notes + 90
        st.markdown('<div class="preview-wrap">', unsafe_allow_html=True)
        st.components.v1.html(preview_html, height=height, scrolling=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(S["h_export"])
        st.caption(S["cap_export"])
        if drive_enabled():
            st.caption(S["cap_cloud"])
        if st.button(S["btn_export"], use_container_width=True):
            with st.spinner(S["sp_render"]):
                try:
                    png = render_png(data)
                    st.session_state["png"] = png
                    st.session_state["png_name"] = (
                        f"Bridge_Diagram_{datetime.now():%Y%m%d_%H%M%S}.png"
                    )
                    st.session_state.pop("drive_msg", None)
                except Exception as exc:  # noqa: BLE001
                    st.error(S["err_export"].format(exc))
                    st.info(S["info_export"])

            if st.session_state.get("png") and drive_enabled():
                with st.spinner(S["sp_upload"]):
                    meta = " · ".join(
                        x for x in [
                            data.get("title", ""), data.get("session", ""),
                            (S["card_board"].format(data["board"]) if data.get("board") else ""),
                            (data.get("room") or ""),
                            f"[{lang}]",
                        ] if x
                    )
                    ok, info = upload_to_drive(png, st.session_state["png_name"], meta)
                st.session_state["drive_msg"] = ("ok" if ok else "err", info)

        if st.session_state.get("png"):
            st.download_button(
                S["dl_prefix"] + st.session_state["png_name"],
                data=st.session_state["png"],
                file_name=st.session_state["png_name"],
                mime="image/png",
                use_container_width=True,
            )
            dm = st.session_state.get("drive_msg")
            if dm and dm[0] == "ok":
                msg = S["ok_cloud"] + (S["ok_cloud_link"].format(dm[1]) if dm[1] else "")
                st.success(msg)
            elif dm and dm[0] == "err":
                st.warning(S["warn_cloud"].format(dm[1]))
            st.image(
                st.session_state["png"], caption=S["cap_final"], use_container_width=True,
            )

    st.divider()
    if S["footer"]:
        st.caption(S["footer"])
