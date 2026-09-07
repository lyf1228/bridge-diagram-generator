# 🍁 牌局與叫牌排版工作台 · Bridge Deal & Auction Studio

開放給大眾使用、免登入、即時預覽、一鍵下載出版級 PNG 的橋牌牌局與叫牌自動生成系統。
介面與產出卡片以秋楓、羊皮紙為視覺語彙，追求出版級編排質感。

**兩個語系版本，共用同一份程式碼（`core.py`）與同一個雲端硬碟收藏：**

| 版本 | 進入點 | 線上版 |
| --- | --- | --- |
| 繁體中文 | `app.py` → `run_app("zh")` | <https://bridge-diagram-generator.streamlit.app/> |
| English | `app_en.py` → `run_app("en")` | *(另外部署一個 app，main file 選 `app_en.py`)* |

![preview](docs/preview.png)

## 功能

- **① 基本資訊**：賽事名稱、副數與發牌、發牌編號、發牌者、身價（雙無 / 南北 / 東西 / 雙方）。
- **② 四家手牌**：每家 ♠ ♥ ♦ ♣ 逐門輸入，`10` 自動轉 `T`，`--` 代表缺門，自動由大到小排序。
- **③ 叫牌區**：室別標題、開叫席位、四席選手姓名、多行叫牌序列
  （每行一輪、空白分隔、`P`=Pass、`X`=Dbl、`XX`=Rdbl）、叫牌註解。
- **好上手**：欄位預設留空並顯示淺灰範例提示；「🎴 載入範例牌局」一鍵帶入示範資料，
  「🧹 全部清空」一鍵清除。
- **即時預覽**：右側同步呈現卡片，改任一欄位立即更新。
- **一鍵匯出**：`html2image` 產生寬 620px、300DPI 級（3×）高解析度 PNG，
  自動裁切留白，檔名 `Bridge_Diagram_{timestamp}.png`。
- **選用雲端收集**：設定後每張匯出圖也會自動存進指定 Google 雲端硬碟（見下方）。

## 版面與字體

- 卡片寬 620px；除賽事名稱維持大字外，其餘文字統一約 18pt。
- ♠ ♥ ♦ ♣ 為內嵌 SVG 花色圖案（大、銳利、顏色精準、Mac / Linux 一致）。
- 中央方位羅盤：發牌者深褐描邊＋橘點徽記，有身價的一方以楓紅牌匾標示。

## 色彩計畫

| 角色 | 色票 |
| --- | --- |
| 楓葉赤紅（主標題 / ♥♦ / 裝飾） | `#9E2A2B` `#BA181B` `#C1121F` |
| 琥珀落葉金（邊框流線 / 高光） | `#D4A373` `#E76F51` |
| 羊皮紙米白（卡片背景） | `#FAF8F5` `#FDFBF7` |
| 楓木金黃（叫牌表頭） | `#FDE68A` + 深褐字 `#5B3A29` |
| 深胡桃炭黑（♠♣） | `#2B231F` |

## 本機執行

```bash
pip install -r requirements.txt
streamlit run app.py      # 中文版
streamlit run app_en.py   # 英文版
```

匯出 PNG 需要本機安裝 Chrome / Chromium（`html2image` 依賴）。

## 部署到 Streamlit Community Cloud（免費）

中文版與英文版各部署成**一個獨立的 app**（同倉庫、同分支，只差 main file）：

1. 將本倉庫推送到 GitHub。
2. <https://share.streamlit.io> → **New app** → 選此倉庫、分支，
   **main file** 中文版填 `app.py`、英文版填 `app_en.py`。
3. `requirements.txt` 安裝 Python 套件；`packages.txt` 安裝 `chromium` 供 `html2image` 匯出。
4. Deploy，取得公開、免登入的網址。
5. 兩個 app 都到 **Settings → Secrets** 貼上**相同的**
   `drive_webhook_url` / `drive_webhook_secret`（見下方），兩版匯出的圖就會存進同一個雲端硬碟資料夾。

## 選用：把每張匯出圖收集到雲端硬碟

啟用後，使用者匯出的每張 PNG 除了可自行下載，也會自動存進
`lyf1228@gmail.com` 的 Google 雲端硬碟（用 Google Apps Script，
不需要 Google Cloud 專案或服務帳戶）。

1. 依 [`drive_collector.gs`](drive_collector.gs) 內的步驟，用 `lyf1228@gmail.com`
   在 <https://script.google.com> 部署一個「網頁應用程式」（執行身分：我；存取權：任何人），
   複製結尾 `/exec` 的網址。
2. 把該網址與自訂密鑰填入 Streamlit Cloud → **Settings → Secrets**
   （格式見 [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example)）：

   ```toml
   drive_webhook_url = "https://script.google.com/macros/s/AKfyc.../exec"
   drive_webhook_secret = "與 drive_collector.gs 的 SHARED_SECRET 相同"
   ```

3. 存檔後 App 自動重啟，匯出區會顯示「☁️ …也會自動存入…雲端硬碟收藏」，
   匯出成功後顯示連結。未設定 secrets 時此功能自動隱藏、不影響下載。

## 檔案

| 檔案 | 用途 |
| --- | --- |
| `core.py` | 共用引擎：語系字串、卡片 HTML/CSS、PNG 匯出、雲端上傳、整個 Streamlit 介面 |
| `app.py` | 中文版進入點（`run_app("zh")`） |
| `app_en.py` | 英文版進入點（`run_app("en")`） |
| `requirements.txt` / `packages.txt` | Python 套件 / 系統套件（chromium） |
| `drive_collector.gs` | Google Apps Script：接收 PNG 並寫入雲端硬碟 |
| `.streamlit/config.toml` | 主題設定 |
| `.streamlit/secrets.toml.example` | 雲端硬碟密鑰範本 |

新增語系：在 `core.py` 的 `STR` 加一組字典、`SEAT_NAME` 加一列，再建一個
`app_xx.py` 呼叫 `run_app("xx")` 即可。
