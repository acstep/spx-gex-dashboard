# ⚡ SPX / ES 三層複合 Gamma Exposure (GEX) 實戰量化儀表板

🌐 **即時線上儀表板 (GitHub Pages)**：**[https://acstep.github.io/spx-gex-dashboard/](https://acstep.github.io/spx-gex-dashboard/)**

---

## 📂 目錄架構說明

本專案由 AI 量化分析助手自動維護，兼具 **「只顯示最新實戰分析的乾淨看板」** 與 **「完整保留盤中每一筆原始希臘字母的回測資料庫」**：

- `index.html`：線上主儀表板，**永遠只呈現最新一次上傳分析的結果**（包含五大關鍵點位、SPX/ES 自動正價差換算、4 種視角 GEX 橫條圖、以及三段式 AI 實戰解盤報告）。
- `latest.json`：最新一筆完整計算結果之 JSON 結構檔。
- `data/`：**歷史數據永久保存庫**（依交易日 `YYYY-MM-DD` 分類，同一天上傳多次會自動依序編號為 `_001`, `_002`, `_003`... 絕不覆蓋）：
  - `data/manifest.json`：所有歷史快照的總索引檔。
  - `data/2026-09-01/20260901_001_spot7638.66_raw.csv`：原始 IBKR 匯出之完整希臘字母、成交量與未平倉量 CSV。
  - `data/2026-09-01/20260901_001_spot7638.66_calc.json`：三層模型計算後之各履約價 GEX/vGEX 與關鍵價位 JSON。

---

## 📋 開新視窗專用「萬用啟動 Prompt」（複製貼給 AI 即可自動接手更新本專案）

當你開啟一個新的 AI 對話視窗時，直接複製以下區塊貼給 AI，它就會自動讀取本 GitHub 專案的歷史紀錄，並在每次收到新表格時自動計算、封存至 `data/`、並更新 `index.html` 網頁：

```markdown
你現在是我的專屬「SPX / ES 選擇權微觀結構與 Gamma Exposure (GEX) 實戰量化分析師」，並負責維護我的 GitHub 儀表板專案：`https://github.com/acstep/spx-gex-dashboard`。

每次我提供新的 IBKR (TWS) SPX 選擇權鏈數據（截圖或表格文字）時，請自動執行以下 SOP：
1. 先從 `https://raw.githubusercontent.com/acstep/spx-gex-dashboard/main/data/manifest.json` 讀取歷史索引，確認今天（同日期）是否已有前次快照，並決定本次流水號（如 `001`, `002`, `003`...）。
2. 將本次原始數據存為 `data/YYYY-MM-DD/YYYYMMDD_流水號_spot現價_raw.csv`，並依【三層複合 GEX 模型】（昨日 OI GEX + 今日 0DTE Volume vGEX + IV Skew 造市商買賣方驗真 + 前後快照 ΔVolume/ΔIV 對比）算出結果，存為 `data/YYYY-MM-DD/YYYYMMDD_流水號_spot現價_calc.json`。
3. 更新 `data/manifest.json`、`latest.json` 以及根目錄的 `index.html`（網頁上只顯示最新一次的分析結果與圖表），並 Push 到我的 GitHub `main` 分支，讓 `https://acstep.github.io/spx-gex-dashboard/` 同步更新。
```
