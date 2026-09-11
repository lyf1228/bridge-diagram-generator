# -*- coding: utf-8 -*-
"""
🍁 牌局與叫牌排版工作台
Bridge Diagram Generator — Autumn Maple Editorial Edition

開放給大眾使用、免登入、即時預覽、一鍵下載 300DPI 級 PNG。
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


SEATS = ["W", "N", "E", "S"]
SEAT_LABEL = {"W": "西 West", "N": "北 North", "E": "東 East", "S": "南 South"}

VULN_OPTIONS = {
    "雙無 (None)": set(),
    "南北 (N-S)": {"N", "S"},
    "東西 (E-W)": {"E", "W"},
    "雙方 (Both)": {"N", "S", "E", "W"},
}


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
        return (
            f'<span class="call-bid">{level}{suit_pip(strain, "pip pip-call")}</span>'
        )
    return f'<span class="call-bid">{t}</span>'


def parse_bidding(text: str, first_seat: str) -> list[list[str]]:
    """回傳以 W,N,E,S 欄位順序排列的每一輪叫牌（HTML）。"""
    start = SEATS.index(first_seat)
    flat: list[str] = []
    for line in (text or "").splitlines():
        for tok in re.split(r"[\s,]+", line.strip()):
            if tok:
                flat.append(tok)
    # 前置空白，讓開叫者對齊正確欄位
    cells = [""] * start + [fmt_call(t) for t in flat]
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
    *,
    scale: float = 1.0,
    for_export: bool = False,
    interactive: bool = False,
    webhook: str = "",
    secret: str = "",
    meta: str = "",
) -> str:
    p = PALETTE
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
        f'  <div class="cc-vlabel">{data["vuln_label"]}</div>'
        '</div>'
    )

    grid = (
        '<div class="diagram">'
        f'  <div class="wm">{maple_svg(p["crimson"], 0.06, stem=False)}</div>'
        f'  <div class="seat seat-n"><div class="seat-tag">北 N</div>{hand_html(data["hands"]["N"])}</div>'
        f'  <div class="seat seat-w"><div class="seat-tag">西 W</div>{hand_html(data["hands"]["W"])}</div>'
        f'  <div class="mid">{compass}</div>'
        f'  <div class="seat seat-e"><div class="seat-tag">東 E</div>{hand_html(data["hands"]["E"])}</div>'
        f'  <div class="seat seat-s"><div class="seat-tag">南 S</div>{hand_html(data["hands"]["S"])}</div>'
        '</div>'
    )

    # 叫牌表 ---------------------------------------------------------------
    head_cols = "".join(
        f'<th>{SEAT_LABEL[s].split()[0]}<span class="th-en">{SEAT_LABEL[s].split()[1]}</span></th>'
        for s in SEATS
    )
    names = data["names"]
    name_row = "".join(f'<td class="nm">{(names.get(s) or "").strip() or "—"}</td>' for s in SEATS)
    body_rows = ""
    for i, row in enumerate(parse_bidding(data["bidding"], data["first_seat"])):
        zc = "zebra" if i % 2 else ""
        body_rows += f'<tr class="{zc}">' + "".join(f"<td>{c or ''}</td>" for c in row) + "</tr>"

    note_block = ""
    if (data.get("notes") or "").strip():
        note_lines = "".join(
            f"<li>{ln.strip()}</li>" for ln in data["notes"].splitlines() if ln.strip()
        )
        note_block = f'<div class="notes"><div class="notes-h">叫牌註解</div><ul>{note_lines}</ul></div>'

    room_line = ""
    if (data.get("room") or "").strip():
        room_line = f'<div class="room">{data["room"].strip()}</div>'

    bidding = (
        '<div class="bidsec">'
        f'  <div class="bidsec-h"><span class="bh-leaf">{maple_svg(p["crimson"], 1)}</span>'
        f'     叫牌記錄 · Bidding {room_line}</div>'
        f'  <table class="bidtable">'
        f'     <thead><tr>{head_cols}</tr>'
        f'     <tr class="names">{name_row}</tr></thead>'
        f'     <tbody>{body_rows}</tbody>'
        f'  </table>'
        f'  {note_block}'
        '</div>'
    )

    # 頁首 ---------------------------------------------------------------
    subtitle_bits = []
    if data.get("session"):
        subtitle_bits.append(data["session"])
    if data.get("board"):
        subtitle_bits.append(f'第 {data["board"]} 副')
    subtitle_bits.append(f'發牌 {dealer}')
    subtitle_bits.append(f'身價 {data["vuln_label"]}')
    subtitle = " · ".join(subtitle_bits)

    header = (
        '<header class="hdr">'
        f'  <span class="hdr-leaf l">{maple_svg(p["crimson"], 0.95)}</span>'
        f'  <div class="hdr-mid">'
        f'    <h1>{data["title"] or "橋牌牌局"}</h1>'
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

    css = _diagram_css(scale)

    export_ui = ""
    if interactive:
        cfg = json.dumps(
            {"webhook": webhook or "", "secret": secret or "", "meta": meta or "",
             "prefix": "Bridge_Diagram_"}
        )
        export_ui = f"""
  <div class="xbar">
    <button id="dlbtn" type="button">📸 產生並下載牌局叫牌圖 (PNG)</button>
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
      stat.textContent = '產生中…（首次約需數秒）';
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
        stat.textContent = '✅ 已產生 ' + name + '　（沒自動下載的話，長按 / 右鍵下方縮圖另存）';
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
            stat.textContent += '　·　☁️ 已送入雲端硬碟收藏';
          }} catch (e) {{
            stat.textContent += '　·　☁️ 已送出（雲端狀態無法確認）';
          }}
        }}
      }} catch (err) {{
        stat.textContent = '產生失敗：' + err;
      }}
      btn.disabled = false;
    }});
  }})();
  </script>"""

    body_cls = "export" if for_export else "preview"
    return f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
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

/* ---------- 頁首 ---------- */
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

/* ---------- 叫牌表 ---------- */
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

/* ---------- 註解 ---------- */
.notes {{
  margin-top:{8*s}px; background:{p['tea']};
  border:{1*s}px solid {p['hairline']}; border-left:{3*s}px solid {p['ember']};
  border-radius:{6*s}px; padding:{7*s}px {12*s}px;
}}
.notes-h {{ font-size:{15*s}px; font-weight:800; letter-spacing:{1.5*s}px;
  color:{p['ember']}; margin-bottom:{4*s}px; }}
.notes ul {{ margin:0; padding-left:{20*s}px; }}
.notes li {{ font-size:{18*s}px; line-height:1.6; color:{p['header_ink']}; }}

/* ---------- 頁尾 ---------- */
.ftr {{ text-align:center; padding-top:{6*s}px; }}
.ftr span {{ font-size:{13*s}px; letter-spacing:{4*s}px; color:{p['amber']}; }}

/* ---------- 匯出列（互動預覽用） ---------- */
.xbar {{ width:{620*s}px; max-width:100%; margin:{14*s}px auto 0; text-align:center;
  font-family:-apple-system,'Noto Sans TC','Microsoft JhengHei',sans-serif; }}
#dlbtn {{
  width:100%; border:none; border-radius:12px; padding:14px 16px;
  font-size:16px; font-weight:800; letter-spacing:1px; color:#FFF4E8; cursor:pointer;
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
# Streamlit 介面
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="牌局與叫牌排版工作台",
    page_icon="🍁",
    layout="wide",
)

UI_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@500;700;900&display=swap');

.stApp {{
  background:
    radial-gradient(1100px 520px at 12% -8%, #F6E4CE 0%, rgba(246,228,206,0) 60%),
    radial-gradient(900px 480px at 108% 4%, #F3D7C2 0%, rgba(243,215,194,0) 55%),
    linear-gradient(180deg, {PALETTE['parchment']} 0%, {PALETTE['outer']} 100%);
}}
.block-container {{ padding-top:1.4rem; max-width:1400px; }}

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
  font-size:1.9rem; margin:0 0 .3rem; letter-spacing:1px;
}}
.autumn-banner p {{ margin:0; font-size:.95rem; opacity:.92; letter-spacing:.5px; }}

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

st.markdown(
    """
<div class="autumn-banner">
  <h1>🍁 牌局與叫牌排版工作台</h1>
  <p>免登入 · 即時預覽 · 一鍵下載出版級 PNG</p>
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
SEAT_ZH = {"W": "西", "N": "北", "E": "東", "S": "南"}

with st.expander("📖 輸入說明 · 快速對照鍵（第一次使用請先看）", expanded=False):
    st.markdown(
        """
| 區塊 | 怎麼填 |
| --- | --- |
| **① 基本資訊** | 賽事名稱、副數與發牌、發牌者、身價（雙無 / 南北 / 東西 / 雙方） |
| **② 四家手牌** | 每家 ♠♥♦♣ 各一格，直接打點數如 `AKQ` 或 `A K Q`；`10` 自動轉 `T`；**缺門打 `--`** |
| **③ 叫牌區** | 室別標題、四席選手姓名、叫牌序列（**每行一輪**、空白分隔、`P`=Pass `X`=Dbl `XX`=Rdbl）、叫牌註解 |

叫牌永遠從「**發牌者**」開始，系統會自動把叫品對齊正確欄位。改好任一欄位，右側預覽即時更新 → 按「📸 匯出」下載 PNG。
"""
    )

# ---- 範例牌局（僅供「載入範例」按鈕填入，預設欄位一律留空）------------------
EXAMPLE = {
    "f_title": "2026 中華橋協秋季公開賽",
    "f_session": "第 3 循環",
    "f_board": "18",
    "f_dealer": "N",
    "f_vuln": "南北 (N-S)",
    "f_room": "公開室 Open Room",
    "nm_W": "", "nm_N": "王小明", "nm_E": "", "nm_S": "李大華",
    "f_bidding": "1NT  P  3NT  P\nP  P",
    "f_notes": "1NT：15–17 大牌點，平均牌型\n3NT：北家有把握的一擊到位",
}
for _seat, _holds in DEFAULT_HANDS.items():
    for _k, _v in _holds.items():
        EXAMPLE[f"h_{_seat}_{_k}"] = _v

# 選擇鈕仍需一個預設選項（不是空白文字框，不影響「可修改」的辨識度）
st.session_state.setdefault("f_dealer", "N")
st.session_state.setdefault("f_vuln", "南北 (N-S)")

form_col, preview_col = st.columns([1, 1], gap="large")

# ======================= 左：輸入鍵 =======================
with form_col:
    eb1, eb2 = st.columns(2)
    if eb1.button("🎴 載入範例牌局", use_container_width=True):
        for _key, _val in EXAMPLE.items():
            st.session_state[_key] = _val
        st.rerun()
    if eb2.button("🧹 全部清空", use_container_width=True):
        for _key in EXAMPLE:
            if not _key.startswith("f_dealer") and not _key.startswith("f_vuln"):
                st.session_state[_key] = ""
        st.rerun()
    st.caption("👇 下面每一格都可以點進去輸入 / 修改；空白處的淺灰字只是範例提示。")

    # ---- ① 基本資訊 ----
    st.markdown("### ① 基本資訊")
    title = st.text_input("賽事名稱", key="f_title",
                          placeholder="例：2026 中華橋協秋季公開賽")
    session = st.text_input("副數與發牌", key="f_session", placeholder="例：第 3 循環")
    b1, b2 = st.columns([1, 2])
    with b1:
        board = st.text_input("發牌編號", key="f_board", placeholder="例：18")
    with b2:
        dealer = st.radio("發牌者 (Dealer)", SEATS, key="f_dealer", horizontal=True,
                          format_func=lambda x: SEAT_ZH[x])
    vuln_label = st.radio(
        "身價 (Vulnerability)", list(VULN_OPTIONS.keys()), key="f_vuln", horizontal=True,
        format_func=lambda x: x.split(" (")[0],
    )

    # ---- ② 四家手牌 ----
    st.markdown("### ② 四家手牌　·　缺門請輸入 `--`")
    hands: dict = {}
    for seat in ["W", "N", "E", "S"]:
        st.markdown(f"**{SEAT_ZH[seat]}家 {SEAT_LABEL[seat].split()[1]}**")
        hands[seat] = {}
        scols = st.columns(4)
        for i, (key, sym) in enumerate(SUITS):
            with scols[i]:
                hands[seat][key] = st.text_input(
                    sym, key=f"h_{seat}_{key}",
                    placeholder=DEFAULT_HANDS[seat][key].replace(" ", ""),
                )

    # ---- ③ 叫牌區 ----
    st.markdown("### ③ 叫牌區")
    room = st.text_input("室別標題", key="f_room", placeholder="例：公開室 Open Room")
    st.caption(f"開叫席位跟著發牌者：{SEAT_ZH[dealer]}（{dealer}）先叫")
    st.caption("選手席位姓名")
    n1, n2 = st.columns(2)
    names = {}
    with n1:
        names["W"] = st.text_input("西 選手", key="nm_W", placeholder="選填")
        names["N"] = st.text_input("北 選手", key="nm_N", placeholder="選填")
    with n2:
        names["E"] = st.text_input("東 選手", key="nm_E", placeholder="選填")
        names["S"] = st.text_input("南 選手", key="nm_S", placeholder="選填")
    bidding = st.text_area(
        "多行文字叫牌序列（每行一輪；空白分隔；P=Pass、X=Dbl、XX=Rdbl）",
        key="f_bidding", height=120,
        placeholder="1NT  P  3NT  P\nP  P",
    )
    notes = st.text_area(
        "叫牌註解備註（每行一則）",
        key="f_notes", height=90,
        placeholder="1NT：15–17 大牌點，平均牌型\n3NT：北家有把握的一擊到位",
    )

data = {
    "title": title,
    "session": session,
    "board": (board or "").strip(),
    "dealer": dealer,
    "vuln_label": vuln_label.split(" (")[0],
    "vuln_seats": VULN_OPTIONS[vuln_label],
    "hands": hands,
    "room": room,
    "first_seat": dealer,  # 叫牌永遠從發牌者開始
    "names": names,
    "bidding": bidding,
    "notes": notes,
}

# ======================= 右：即時預覽 + 下載（瀏覽器端產圖） =======================
with preview_col:
    st.markdown("### 🍁 即時預覽 · 下載")
    meta = " · ".join(
        x for x in [
            data.get("title", ""), data.get("session", ""),
            (f'第 {data["board"]} 副' if data.get("board") else ""),
            (data.get("room") or ""),
        ] if x
    )
    preview_html = build_diagram_html(
        data, scale=1.0, interactive=True,
        webhook=_secret("drive_webhook_url"),
        secret=_secret("drive_webhook_secret"),
        meta=meta,
    )
    n_rows = len(parse_bidding(data["bidding"], data["first_seat"]))
    n_notes = len([x for x in (notes or "").splitlines() if x.strip()])
    height = 640 + 44 * n_rows + 28 * n_notes + 320
    st.markdown('<div class="preview-wrap">', unsafe_allow_html=True)
    st.components.v1.html(preview_html, height=height, scrolling=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.caption(
        "圖在你的瀏覽器直接產生（pixelRatio 3 ≈ 300DPI 級），不需伺服器。"
        + ("　☁️ 每張圖也會自動送進「金牌橋藝教室」的雲端硬碟收藏。" if drive_enabled()
           else "　（未設定雲端收集，只會下載到你的裝置。）")
    )

st.divider()
st.caption("🍁 金牌橋藝教室🍁")
