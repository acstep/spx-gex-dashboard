# 📊 SPX / ES 0DTE 3-Layer GEX & Dealer Flow Quantitative Dashboard

🔗 **Live Interactive Dashboard (GitHub Pages)**: [https://acstep.github.io/spx-gex-dashboard/](https://acstep.github.io/spx-gex-dashboard/)

## 🚨 每次收到「希臘字母 / 選擇權鏈」時要做什麼（先讀這份）

> **觸發句**：只要使用者丟來**截圖 / CSV / Excel / 一句「跑下一筆」**，就照這份 SOP 跑完，不用重新確認。
>
> 📄 **[`SPX_GEX_SOP_Each_Snapshot.md`](./SPX_GEX_SOP_Each_Snapshot.md)** — 逐筆作業 SOP（15 節，含公式、增量分解判讀門檻、三大鐵律、7 個產出檔、上傳驗證 4 關、回覆固定格式、我犯過的 8 個錯）

**一頁版流程**
```
原始鏈 → MULT_M=100×S²×0.01/1e6 → 6 總量＋5 點位＋15 點重心＋Flip(累積法)
      → 增量分解（新成交 vs IV 重估，>60% 重估＝不可交易）
      → 7 個檔案 → 推 GitHub → 驗 4 關 → 回覆（附更新連結）
```

---

## 📚 系統指令與量化分析 SOP 文件 (Markdown Prompts)

1. 📄 **[`SPX_GEX_Full_Workflow_With_GitHub.md`](./SPX_GEX_Full_Workflow_With_GitHub.md)**  
   - **完整版工作流 SOP（含分析算法 + 七大防誤判量化鐵律 + 雙圖表規格 + GitHub 自動歸檔與部署流程）**：供你在新對話視窗一鍵還原整套自動化歸檔與儀表板更新流程（已完全移除任何 Token 隱私資訊）。
2. 📄 **[`SPX_GEX_AI_Analysis_Prompt_Only.md`](./SPX_GEX_AI_Analysis_Prompt_Only.md)**  
   - **純 AI 量化解盤專用 Prompt（不含 GitHub 流程）**：可直接複製貼給任何 AI（ChatGPT / Claude / Gemini 等），貼上 IBKR 選擇權鏈即可產出「五大關鍵點位 + 造市商 IV 底牌驗真 + ES/SPX 實戰劇本 + 盤中增量資金流對比」。
3. 📓 **[`SPX_GEX_Prediction_Error_Log_and_Correction_Ledger.md`](./SPX_GEX_Prediction_Error_Log_and_Correction_Ledger.md)**  
   - **歷史預測錯題本與持續修正總帳**：完整記錄過去 6 個交易日（37 筆快照 / 31 次盤中推進）中所有曾經預測失誤的 16 筆快照、AI 大數據模型五大先天缺陷與「五不亂說戒律」、跨日皮爾森統計回歸基準表，以及「盤中逐筆對帳、連錯即斬」的持續修正規範。
4. 🧮 **[`run_gex_regression_audit.py`](./run_gex_regression_audit.py)**  
   - **每日/每筆自動量化回歸檢驗與自我對帳引擎**：自動掃描 `data/` 下全部歷史快照，計算 7 大微觀因子與下一筆漲跌 (`dSpot`) 之相關係數 ($r$)，檢驗五大定量盤態分類器命中率，並為最新一筆快照輸出「強制盤態鎖定 (Mandatory Regime Lock)」。

---

## 🗂️ 歷史數據永久歸檔目錄 (`/data`)

每一次盤中上傳的 IBKR 選擇權鏈數據皆會自動編號並永久保存在 [`/data`](./data) 目錄下，絕不覆蓋歷史紀錄：
- `data/manifest.json`：全歷史快照總索引
- `data/YYYY-MM-DD/YYYYMMDD_SEQ_spotXXXX.XX_raw.csv`：原始 IBKR 選擇權鏈與 Greeks 數據
- `data/YYYY-MM-DD/YYYYMMDD_SEQ_spotXXXX.XX_calc.json`：三層 GEX / vGEX / Pin Strength 與 IV 曲率計算結果
