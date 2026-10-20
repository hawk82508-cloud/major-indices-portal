# 各大指數高低控統整系統 v2.0 (九大指數整合版) — GitHub Pages 直接部署與每日自動更新套件

本套件將 **台股及美股指數（TAIEX、DJI、S&P 500 (SPX)、NASDAQ、SOX）** 與 **台幣美元及避險工具四大指數（美元指數 DXY、美元兌台幣 USDTWD、比特幣 BTC、黃金國際現貨 GOLD / XAUUSD）** 共九套多週期（日/周/月）與跨週期前瞻雙軌通道分析系統完整整合於單一入口網頁 (`index.html` / `各大指數高低控統整_多週期與跨週期前瞻雙軌通道分析系統_v2.0.html`)：

- **頂部雙排導覽列設計（v2.0 升級版）**：
  - **第一排**：`🏠 台股及美股四大指數`、`🇹🇼 TAIEX (加權指數)`、`🇺🇸 DJI (道瓊工業)`、`🇺🇸 S&P 500 (SPX)`、`🇺🇸 NASDAQ (那斯達克)`、`🇺🇸 SOX (費城半導體)`。
  - **第二排（緊接於「台股及美股四大指數」按鍵正下方）**：`🌐 台幣美元及避險工具四大指數`、`💵 美元指數 (DXY)`、`💱 美元兌台幣 (USDTWD)`、`₿ 比特幣 (BTC)`、`🥇 黃金 (GOLD)`。
- **雙總覽頁面架構**：
  - **台股及美股四大指數總覽頁**：依序呈現 **集中市場加權指數 (TAIEX)**、**道瓊工業平均指數 (DJI)**、**S&P 500 指數 (SPX)**（位於道瓊工業之下、那斯達克之上）、**那斯達克綜合指數 (NASDAQ)**、**費城半導體指數 (SOX)** 摘要卡與跨週期融合走勢圖。
  - **台幣美元及避險工具四大指數總覽頁**：依序呈現 **美元指數 (DXY)**、**美元兌台幣 (USDTWD)**、**比特幣 (BTC)**、**黃金 (GOLD)** 四種跨週期融合走勢圖與摘要卡。
- **九大指數獨立完整頁面**：
  - 點選任一指數按鍵（包含新增之 `S&P 500` 與 `黃金 (GOLD)` 按鍵），即進入該指數專屬之多週期與跨週期前瞻雙軌通道分析系統（含 `🌐 跨週期融合`、`📅 日 K 線`、`📊 周 K 線`、`🗓️ 月 K 線`、Y 軸右側 30% 半透明標註、KPI 指標卡、次期前瞻預測卡、CSV 匯出與歷史明細表）。

---

## 📁 套件檔案結構

- `index.html`：GitHub Pages 預設首頁（部署後開啟您的 GitHub 網址即可直接瀏覽）。
- `各大指數高低控統整_多週期與跨週期前瞻雙軌通道分析系統_v2.0.html`：與 `index.html` 完全相同之中文版本編號檔案，方便下載至電腦直接以 Google Chrome 開啟。
- `.nojekyll`：告知 GitHub Pages 直接以純靜態網頁高速發佈。
- `data/TAIEX/`、`data/DJI/`、`data/SPX/`、`data/NASDAQ/`、`data/SOX/`、`data/DXY/`、`data/USDTWD/`、`data/BTC/`、`data/GOLD/`：九大指數各自的 `raw_daily.csv`、`raw_weekly.csv`、`raw_monthly.csv` 歷史與最新收盤資料庫（含基準備份與回溯檔）。
- `update_all_indices.py`：每日自動抓取九大指數最新盤後收盤數據、更新日/周/月 CSV、重算 12 期通道與 11 期次期前瞻雙軌，並同步寫回 `index.html` 與 `各大指數高低控統整_多週期與跨週期前瞻雙軌通道分析系統_v2.0.html` 的核心引擎。
- `.github/workflows/daily_update.yml`：GitHub Actions 自動排程設定檔（涵蓋每日 08:05 BTC 收盤、14:35 台股收盤、16:30 台北外匯收盤、05:30 美股/美元指數/黃金收盤四個時段自動更新並推播至 GitHub Pages）。
- `send_email_report.py`：每日自動寄送九大指數 HTML 報告附件至指定雙信箱之腳本。
- `requirements.txt`：Python 依賴套件清單（`requests`、`pandas`、`numpy`）。

---

## 🚀 手把手教學：直接部署在 GitHub Pages（使用 GitHub 網址 + 每日自動更新）

### 步驟一：在 GitHub 建立新的儲存庫 (Repository) — 或使用既有儲存庫
1. 登入您的 [GitHub](https://github.com/) 帳號，點擊右上角的 **`+`** 號 ➔ 選擇 **`New repository`**。
2. **Repository name（儲存庫名稱）**：輸入您喜歡的英文名稱，例如 `major-indices-portal`（這會成為您之後 GitHub 網址的一部分）。
3. **Public / Private**：請務必選擇 **`Public`（公開）**（GitHub 免費版帳號設為 Public 即可免費使用 GitHub Pages 網址與無限次 GitHub Actions 每日自動更新）。
4. 勾選 **`Add a README file`**，然後點擊最下方的綠色按鈕 **`Create repository`**。

### 步驟二：上傳本套件所有檔案至 GitHub
1. 將下載的 `各大指數高低控統整_GitHub_Pages每日自動更新部署套件_v2.0.zip` 在電腦上**解壓縮**。
2. 進入剛剛建立好的 GitHub 儲存庫頁面，點擊上方的 **`Add file`** ➔ **`Upload files`**。
3. 將解壓縮出來的所有檔案與資料夾（包含 `index.html`、`各大指數高低控統整_多週期與跨週期前瞻雙軌通道分析系統_v2.0.html`、`data` 資料夾、`update_all_indices.py`、`send_email_report.py`、`requirements.txt`、`.nojekyll`、`.github` 資料夾）**全部拖曳到上傳框中**。
   > 💡 **注意隱藏資料夾 `.github`**：Windows 或 Mac 若預設隱藏 `.` 開頭的資料夾，導致拖曳時沒上傳到 `.github/workflows/daily_update.yml`，您可以在上傳完成後，點選儲存庫上方的 **`Actions`** 頁籤 ➔ 點擊 **`set up a workflow yourself`**（或 **`New workflow`**），將檔名命名為 `daily_update.yml`，並把套件內 `.github/workflows/daily_update.yml` 的文字內容完整貼上，點擊右上角綠色 **`Commit changes...`** 即可！
4. 在頁面下方點擊綠色按鈕 **`Commit changes`** 完成檔案上傳。

### 步驟三：開啟 GitHub Actions 自動寫入權限（讓系統能每日自動更新網頁）
1. 在您的 GitHub 儲存庫頁面，點擊最上方的 **`Settings`（設定）**。
2. 在左側選單展開 **`Actions`** ➔ 點擊 **`General`**。
3. 往下滑動到最底部找到 **`Workflow permissions`（工作流程權限）**：
   - 改勾選 **`Read and write permissions`（讀取與寫入權限）**。
   - 點擊下方的 **`Save`** 按鈕儲存。

### 步驟四：啟用 GitHub Pages（取得您的專屬 GitHub 網址）
1. 同樣在 **`Settings`（設定）** 頁面，點擊左側選單的 **`Pages`**。
2. 在 **`Build and deployment`** 區塊下的 **`Source`**：
   - 維持選擇 **`Deploy from a branch`**。
3. 在 **`Branch`（分支）** 下拉選單：
   - 第一個選單將 `None` 改選為 **`main`**。
   - 第二個選單維持 **`/ (root)`**。
   - 點擊旁邊的 **`Save`** 按鈕。
4. 等待約 **30 秒至 1 分鐘** 後，重新整理該 `Pages` 設定頁面，畫面上方就會出現您的專屬網址：
   > **Your site is live at `https://<您的GitHub帳號>.github.io/major-indices-portal/`**
5. 點擊該網址即可直接開啟您的「各大指數高低控統整系統 v2.0」！將此網址加入瀏覽器書籤或手機主畫面即可隨時查看。

### 步驟五：手動測試一次自動更新（確認每日排程運作正常）
1. 點擊儲存庫最上方的 **`Actions`** 頁籤。
2. 點擊左側的 **`Daily 9 Major Indices Auto Update & GitHub Pages Deploy`**。
3. 點擊右側的 **`Run workflow`** 下拉按鈕 ➔ 點擊綠色的 **`Run workflow`** 按鈕。
4. 等待約 30~45 秒出現綠色勾勾 `✅`，即代表系統已成功自動連線抓取九大指數最新數據、重算雙軌通道並更新至您的 GitHub Pages 網址！

### （選配）步驟六：設定每日自動寄信通知 (GitHub Secrets)
若您希望每日收盤更新後自動寄送 HTML 報告至信箱，請至 **`Settings`** ➔ 左側 **`Secrets and variables`** ➔ **`Actions`** ➔ 點擊 **`New repository secret`** 新增兩組變數：
- `GMAIL_USER`：您的 Gmail 信箱帳號
- `GMAIL_APP_PASSWORD`：您的 16 位數 Google 應用程式密碼（若未設定也不影響網頁每日自動更新！）
