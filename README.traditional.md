# 從一個想法，到一個工作助理

[簡體中文](README.md) | [繁體中文](README.traditional.md)

本文件使用繁體中文；課程程式、介面與教學截圖沿用原版，畫面文字可能為簡體中文，請對照實際介面操作。

## GitHub Copilot App 動手實驗 · Python 版

歡迎加入虛構的「晨光創意工作室」。你不是程式設計師，而是負責團隊活動、產品傳播和每週安排的業務同事。接下來的四次委託，會帶你從“把需求說清楚”走到“讓多個 Agent 分工協作”。

**這裡的 Copilot 是 GitHub Copilot App，不是 Microsoft 365 Copilot。** 不要求資訊相關科系背景，但需要按步驟開啟終端、複製命令，並核對執行結果。

**課程總時長：3 小時（180 分鐘）**，四個 Lab 按 35 + 45 + 45 + 55 分鐘安排。

| Lab | 建議時間 | 你的委託 | 新學到的 App 能力 | 交付作品 |
|---|---:|---|---|---|
| [Lab 1](Lab1/README.traditional.md) | 35 分鐘 | 為團隊做一個中國象棋小遊戲 | 本地資料夾、會話、模型、Autopilot、反饋與驗證 | HTML 遊戲 + Python 規則引擎 |
| [Lab 2](Lab2/README.traditional.md) | 45 分鐘 | 為 Surface 做一段產品短片 | 提供資料、Plan 審閱、切換 Autopilot、約束輸出 | edge-tts 中文女聲 + HyperFrames CLI 2 分鐘 9:16 MP4；**不構建播放介面** |
| [Lab 3](Lab3/README.traditional.md) | 45 分鐘 | 向同事講清微軟財報 | SDK、單 Agent、來源約束、分析檢視 | Power BI 風格財報頁面 + Python 單 Agent |
| [Lab 4](Lab4/README.traditional.md) | 55 分鐘 | 把郵件和會議整理成本週待辦 | 多 Agent 分工、Canvas 擴充功能、權限與持久化 | Python 工作助理 + Canvas 薄轉接器 |
| **合計** | **180 分鐘（3 小時）** |  |  |  |

四個 Lab 的目標模型都是 **GPT-6 Luna**，SDK 中的準確 ID 是 `gpt-6-luna`。不能用頁面上寫著模型名稱，來代替實際模型呼叫證明。本課程的真實呼叫記錄儲存在各 Lab 的 `Code/` 中。

## 課程演示範圍

每個 Lab 都配有可執行的 Python 程式碼和明確的驗收步驟；公開頁面使用虛構練習資料和經過篩選的作品截圖。

| 範圍 | 課程內容 |
|---|---|
| Lab 1 | Python 象棋規則引擎與瀏覽器小遊戲；按步驟檢查走棋、悔棋和重開 |
| Lab 2 | edge-tts 中文女聲與 HyperFrames CLI；目標為 1080×1920、30fps、120 秒成片 |
| Lab 3 | 基於 Microsoft FY2025 年報資料的 Python 分析和互動式經營觀察室 |
| Lab 4 | 用明確標註的虛構郵件與日曆資料練習多 Agent、排程和 Canvas 工作流 |
| 個人帳戶資料 | 真實郵箱、日曆和帳戶登入只屬於學員本地授權實操；不包含在公開演示中 |
| Canvas | SDK 協議、擴充功能註冊和 App 原生側欄是不同驗收面；請按當前 App 能力分別檢查 |

公開頁面只發布課程說明、原始碼和篩選後的教學截圖。本機執行日誌、個人帳戶資料和私人截圖不屬於課程公開材料。

## 開始前：只準備一次

### 1. 準備工具

在自己的電腦上安裝 GitHub Copilot App，並用有 Copilot 權限的帳號登入。確認模型選擇器中有 **GPT-6 Luna**。如果沒有，請先解決帳號或組織的模型權限，**不要悄悄換成另一個模型繼續當作本實驗通過**。

還需要 Python 3.11+、Copilot CLI，以及 Lab 2 專用的 Node.js 22+ 和 FFmpeg。不同系統與工具版本可能有差異，開始前請執行版本預檢命令。

開啟系統終端，進入本課程資料夾。後文出現的命令，除明確寫出 `cd` 的片段外，**都在包含本 README 的課程根目錄執行**。

```bash
python3 --version
copilot --version
node --version
ffmpeg -version
ffprobe -version
```

如 Copilot CLI 尚未登入，執行 `copilot login` 並在它開啟的官方頁面完成登入。不要把密碼或令牌貼上到提示詞、程式碼或截圖中。App 和 SDK 的登入狀態需要分別確認，不能假設一個成功就代表另一個也成功。

### 2. 建立 Python 環境

macOS / Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt --index-url https://packagefeedproxy.microsoft.io/pypi/simple/
python -m playwright install chromium
python tools/probe.py
```

Windows PowerShell 的前兩條改為：

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

如果 PowerShell 組織策略禁止啟用，不要修改組織策略；可直接使用 `.\.venv\Scripts\python.exe` 替代後文的 `python`。

**通過條件：** `verification/capabilities.json` 中有 `gpt-6-luna`，命令沒有認證錯誤。若提示權限或登入錯誤，先處理錯誤再繼續。

### 3. 在 App 開啟課程

在 App 的 **Sessions** 旁點 **+**，選擇 **Open local folder**，開啟整個課程根目錄。四個 Lab 按順序做，每個 Lab 新建一個會話，並在提示詞中約束只修改相應 Lab 的 `Code/`。

這是本地資料夾實驗，**沒有自動建立 Git 分支或隔離 worktree**。不要讓多個會話同時修改同一檔案。App 標籤和按鈕隨版本變化時，以 [官方會話文件](https://docs.github.com/en/copilot/how-tos/github-copilot-app/agent-sessions) 和當前 `/` 命令列表為準。

## 四個詞，先弄明白

| 名詞 | 用日常工作理解 |
|---|---|
| Plan | 先交方案；你看清楚做什麼、用什麼資料、如何驗收，再批准 |
| Autopilot | 方案明確後，讓助理連續執行；不代表可以忽略帳號權限、資料保護或組織政策 |
| Agent / SDK | Agent 是帶職責的助理；SDK 是讓 Python 程式呼叫它的工具箱，不是另一個聊天視窗 |
| Canvas | App 旁邊的互動工作面；它的網頁渲染內容和 Canvas 註冊協議不是同一回事 |

**Python 統一約定：** 後端、計算、Agent、採集、排程、測試與執行入口使用 Python。瀏覽器互動仍需要少量 HTML/CSS/JavaScript。HyperFrames 官方引擎依賴 Node.js；App 擴充功能的官方入口必須是 `extension.mjs`。Lab 4 的該入口僅做註冊和轉發，不在 JavaScript 中實現業務邏輯。

## 目錄與證據

```text
Lab1/README.traditional.md    Lab1/Code/    Lab1/screenshots/
Lab2/README.traditional.md    Lab2/Code/    Lab2/screenshots/
Lab3/README.traditional.md    Lab3/Code/    Lab3/screenshots/
Lab4/README.traditional.md    Lab4/Code/    Lab4/screenshots/
tools/           共享 Python 工具
tests/           業務規則測試
```

`01-execution-record.png` 是 **真實 JSON 記錄渲染後的瀏覽器截圖**，不是偽造的 App 模式選擇截圖。各 README 每步都會註明圖片的性質；需要學員補拍的 App 原生圖片單獨列出，不能用執行記錄替換。

公開 Pages 構建只複製各 Lab 的虛構演示截圖；本機驗收報告及個人帳戶截圖不會發布。

## 講師複核

核心依賴安裝完成後，可以重複執行：

```bash
python -m pytest -q tests/test_labs.py
python Lab4/Code/canvas_smoke.py
python tools/verify.py
```

第三條會啟動短期本地服務、驗證四個作品、儲存截圖，然後關閉自己啟動的服務；**不是啟動後就永久線上**。學員體驗時請按各 Lab 的 `app.py` 命令啟動，並保持終端開啟。

真實擴充功能的驗證見 Lab 4，需要先從當前 `extensions_manage guide` 獲取 SDK 路徑。`tools/verify.py` 不讀取真實 Outlook，不自動重跑收費模型呼叫，也不把私人資料寫進截圖。

模型呼叫、網路下載與影片渲染會消耗時間和額度。已有 `generation.json`、`story.json`、`analysis.json`、`plan.json` 是此次執行結果；重新呼叫時措辭可能不同，驗收應看約束與功能，不要求逐字相同。
