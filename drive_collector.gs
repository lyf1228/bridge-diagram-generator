/**
 * 金牌橋藝教室 · 牌局叫牌圖雲端收集
 * ------------------------------------------------------------------
 * 用途：接收 Streamlit App 傳來的 PNG，存入 lyf1228@gmail.com 的雲端硬碟。
 * 檔案擁有者＝部署這支腳本的帳號（請用 lyf1228@gmail.com 登入部署），
 * 佔用的是該帳號自己的 15GB 空間，不需要 Google Cloud 專案或服務帳戶。
 *
 * ===== 安裝步驟 =====
 * 1. 用 lyf1228@gmail.com 登入 https://script.google.com → 新增專案。
 * 2. 把本檔案內容整段貼上，覆蓋預設的 Code.gs。
 * 3. 在雲端硬碟建立一個資料夾（例如「牌局叫牌圖收藏」），打開它，
 *    網址 https://drive.google.com/drive/folders/XXXXXXXX 中的 XXXXXXXX 就是 FOLDER_ID。
 * 4. 填入下方兩個常數：FOLDER_ID、SHARED_SECRET（SHARED_SECRET 自訂一串亂碼即可）。
 * 5. 右上「部署」→「新增部署作業」→ 類型選「網頁應用程式」：
 *      - 執行身分：我 (lyf1228@gmail.com)
 *      - 具存取權的使用者：任何人
 *    按「部署」，第一次會要求授權 → 允許。複製「網頁應用程式」網址（結尾是 /exec）。
 * 6. 到 Streamlit Cloud → 你的 App → Settings → Secrets，貼上：
 *      drive_webhook_url = "https://script.google.com/macros/s/AKfyc.../exec"
 *      drive_webhook_secret = "與下方 SHARED_SECRET 完全相同的字串"
 *    存檔，App 會自動重啟並啟用雲端同步。
 * ------------------------------------------------------------------
 */

const FOLDER_ID = "";        // ← 貼上資料夾 ID；留空則存到雲端硬碟根目錄
const SHARED_SECRET = "";    // ← 自訂一串亂碼，需與 Streamlit secrets 的 drive_webhook_secret 相同

function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);

    if (SHARED_SECRET && body.secret !== SHARED_SECRET) {
      return _json({ ok: false, error: "unauthorized" });
    }

    const bytes = Utilities.base64Decode(body.data);
    const blob = Utilities.newBlob(
      bytes,
      body.mimeType || "image/png",
      body.filename || ("bridge_" + Date.now() + ".png")
    );

    const folder = FOLDER_ID ? DriveApp.getFolderById(FOLDER_ID) : DriveApp.getRootFolder();
    const file = folder.createFile(blob);
    if (body.description) file.setDescription(body.description);

    return _json({ ok: true, id: file.getId(), url: file.getUrl() });
  } catch (err) {
    return _json({ ok: false, error: String(err) });
  }
}

function doGet() {
  return _json({ ok: true, service: "bridge diagram collector" });
}

function _json(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
