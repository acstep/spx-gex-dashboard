# 📊 SPX / ES 0DTE 3-Layer GEX & Dealer Flow Quantitative Dashboard

🔗 **Live Interactive Dashboard (GitHub Pages)**: [https://acstep.github.io/spx-gex-dashboard/](https://acstep.github.io/spx-gex-dashboard/)

## 📚 系統指令與量化分析 SOP 文件 (Markdown Prompts)

1. 📄 **[`SPX_GEX_Full_Workflow_With_GitHub.md`](./SPX_GEX_Full_Workflow_With_GitHub.md)**  
   - **完整版工作流 SOP（含分析算法 + 雙圖表規格 + GitHub 自動歸檔與部署流程）**：供你在新對話視窗一鍵還原整套自動化歸檔與儀表板更新流程（已完全移除任何 Token 隱私資訊）。
2. 📄 **[`SPX_GEX_AI_Analysis_Prompt_Only.md`](./SPX_GEX_AI_Analysis_Prompt_Only.md)**  
   - **純 AI 量化解盤專用 Prompt（不含 GitHub 流程）**：可直接複製貼給任何 AI（ChatGPT / Claude / Gemini 等），貼上 IBKR 選擇權鏈即可產出「五大關鍵點位 + 造市商 IV 底牌驗真 + ES/SPX 實戰劇本 + 盤中增量資金流對比」。

---

## 🗂️ 歷史數據永久歸檔目錄 (`/data`)

每一次盤中上傳的 IBKR 選擇權鏈數據皆會自動編號並永久保存在 [`/data`](./data) 目錄下，絕不覆蓋歷史紀錄：
- `data/manifest.json`：全歷史快照總索引
- `data/YYYY-MM-DD/YYYYMMDD_SEQ_spotXXXX.XX_raw.csv`：原始 IBKR 選擇權鏈與 Greeks 數據
- `data/YYYY-MM-DD/YYYYMMDD_SEQ_spotXXXX.XX_calc.json`：三層 GEX / vGEX / Pin Strength 與 IV 曲率計算結果
