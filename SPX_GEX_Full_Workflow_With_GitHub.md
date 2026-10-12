# 📊 SPX / ES 0DTE 三層 GEX 量化分析、Barchart 雙圖儀表板與 GitHub 自動歸檔完整 SOP

> **文件用途**：本文件為「完整版工作流指令（含量化分析邏輯 + 網頁儀表板規格 + GitHub 歷史數據庫歸檔與自動部署 SOP）」。當你在新的 AI 對話視窗啟動專案時，直接上傳本 `.md` 檔（或貼上內容），AI 即可100% 還原所有計算邏輯、雙圖表 UI 與 GitHub 自動化流程。
> *(🔒 隱私安全聲明：本文件已完全移除任何個人 API Token 與私密金鑰，請於執行部署時透過環境變數或對話提供 `$GITHUB_TOKEN`。)*

---

## 一、 核心目標與系統架構

本系統結合 **IBKR TWS 即時選擇權鏈（0DTE Volume + Greeks + IV）** 與 **Barchart 雙圖表視覺化架構**，解決傳統免費 GEX 網站（僅看隔夜 OI、忽略 0DTE 當日巨量、盲目假設造市商買賣方向）的三大盲點，並將每一次盤中上傳的數據永久歸檔至 GitHub 資料庫供日後回測。

### 系統四大核心產出：
1. **三層 GEX 量化推演**：同時計算「第一層：昨日留倉 OI GEX」、「第二層：今日 0DTE 即時成交量 vGEX」、「第三層：全場總磁吸強度 Pin Strength (`Call + |Put|`)」。
2. **IV 曲率（IV Smile/Skew）造市商底牌驗真**：利用各履約價 `IV` 的局部凹陷（最低谷 `❄️`）或凸起，100% 驗明造市商在關鍵大牆是「真買方（Long Gamma 壓制）」還是「被動賣方（Short Gamma 助漲助跌）」。
3. **Barchart 風格雙圖並排互動儀表板 (`index.html`)**：
   - 支援 **☀️ 白底模式 (Barchart 經典)** 與 **🌙 黑底模式 (夜盤護眼)** 一鍵切換。
   - 支援 **🔥 今日 0DTE 即時成交量 (vGEX)** 與 **🏛️ 昨日留倉未平倉量 (OI GEX)** 數據源切換。
   - 支援 **🖥️ 左右雙圖並排** 與 **📐 上下大圖排列** 切換。
   - 內建 **ES 期貨價差 (`Basis = ES - SPX`)** 即時換算器。
4. **GitHub 自動化歷史數據庫與 Pages 部署 (`acstep/spx-gex-dashboard`)**：
   - 每次上傳的盤中數據自動編號存入 `data/YYYY-MM-DD/`（絕不覆蓋舊檔）。
   - 網頁 `index.html` 永遠保持乾淨，僅呈現「最新一期」分析結果與前後期增量對比（$\Delta\text{Volume}$ & $\Delta\text{IV}$）。

---

## 二、 必備輸入資料格式（IBKR TWS / Excel 匯出欄位）

每次分析時，使用者會提供截圖、CSV 或貼上包含以下欄位的 SPX 選擇權鏈表格：

### 1. 頂部基準資訊（Header Metadata）
- **到期日 (`Date / Expiration`)**：例如 `2026-09-01`（判斷是否為 0DTE）
- **SPX 現價 (`Spot Price`)**：例如 `7638.66`
- **ES 期貨價差 (`ES Basis`，選填)**：例如 `+12.50`（若未提供，預設以 `0` 或當期基差推算）

### 2. 各履約價欄位（Strike Row Columns）
| 欄位名稱 | 物理意義 | 計算用途 |
| :--- | :--- | :--- |
| **`履約價 (Strike)`** | 選擇權履約價（通常每 5 點一格） | X 軸座標與關鍵牆點位 |
| **`IV`** | 該履約價隱含波動率 | **驗明造市商真實買賣方向（IV 曲率驗真）** |
| **`GAMMA`** | 價格每變動 1 點之 Delta 變化量 | 計算 GEX / vGEX / Pin Strength 核心乘數 |
| **`CALL DELTA` / `PUT DELTA`** | 買權 / 賣權 Delta | 推算造市商當前已對沖之期貨部位與 Charm 流向 |
| **`VEGA`** | 波動率每變動 1% 之價值變化 | 評估 Vanna 效應（IV 升降對 Delta 之二階影響） |
| **`CALL THETA` / `PUT THETA`** | 時間價值衰減速度 | 評估尾盤（14:30 ET 後）0DTE 時間價值蒸發與釘住效應 |
| **`Call Volume` / `Put Volume`** | **當日截至目前累積成交量** | **計算日內最準的「0DTE Volume vGEX」與「增量資金流 $\Delta\text{Vol}$」** |
| **`CALL OI` / `PUT OI`** | **昨日收盤留倉未平倉量** | **計算傳統「隔夜 OI GEX」與「極端破位之老空頭平倉支撐牆」** |

---

## 三、 核心數學公式與三層量化推演步驟

收到數據後，必須依序執行以下 **6 大定量計算步驟**：

### Step 1：計算每個履約價的三種 Gamma 曝險值（單位：$ Millions / $ Billions）
採用與 Barchart / SpotGamma 相同的 **1% 標的變動美元 Gamma 標準公式**（合約乘數 $100 \times 1\% = 1$）：

1. **單邊 Call / Put 0DTE 當日成交量 Gamma 曝險 (`Call vGEX` / `Put vGEX`)**：
   $$\text{Call vGEX}_K = +\text{Call\_Volume}_K \times \Gamma_K \times \text{Spot}^2$$
   $$\text{Put vGEX}_K = -\text{Put\_Volume}_K \times \Gamma_K \times \text{Spot}^2$$

2. **① 0DTE 淨成交量 Gamma 曝險 (`Net Volume vGEX`，對應左圖 ① 柱狀圖)**：
   $$\text{Net vGEX}_K = \left(\text{Call\_Volume}_K - \text{Put\_Volume}_K\right) \times \Gamma_K \times \text{Spot}^2$$
   - **正值（藍色向上柱）**：Call 主導，造市商預設偏正 Gamma（逢高賣出壓制、抑制波動）。
   - **負值（橘色向下柱）**：Put 主導，造市商預設偏負 Gamma（逢低追空加速、放大波動）。

3. **② 全場總磁吸強度 (`Absolute Exposure / Pin Strength`，對應右圖 ② 紫色虛線)**：
   $$\text{Pin vGEX}_K = \left(\text{Call\_Volume}_K + \text{Put\_Volume}_K\right) \times \Gamma_K \times \text{Spot}^2 = \text{Call vGEX}_K + \left|\text{Put vGEX}_K\right|$$
   - **核心意義**：解決 `Call Volume ≈ Put Volume` 時相減抵銷為 0 的假象（例如雙邊各 7 萬口巨量對鎖）。`Pin vGEX` 越高的履約價，代表多空雙邊總籌碼越厚重，是盤中反彈與尾盤收斂最強的**「價格黑洞（Straddle Pin Zone）」**。

4. **③ 昨日留倉未平倉量 Gamma 曝險 (`Overnight OI GEX`，傳統 Barchart 算法)**：
   $$\text{Call OI GEX}_K = +\text{Call\_OI}_K \times \Gamma_K \times \text{Spot}^2, \quad \text{Put OI GEX}_K = -\text{Put\_OI}_K \times \Gamma_K \times \text{Spot}^2$$
   $$\text{Net OI GEX}_K = \left(\text{Call\_OI}_K - \text{Put\_OI}_K\right) \times \Gamma_K \times \text{Spot}^2$$

---

### Step 2：自動定位「五大關鍵實戰點位（5 Key Levels）」

| 點位代號 | 點位名稱 | 精確定義與搜尋演算法 | 實戰物理意義 |
| :--- | :--- | :--- | :--- |
| **1. `GAMMA FLIP`** | **⚖️ 多空波動分水嶺** | `Net vGEX` 由負值（橘柱）正式翻轉為正值（藍柱）之交界履約價（即累積曲線 `Aggregate GEX` 的谷底轉折點 / 零軸穿越點）。 | **現價 > Flip**：正 Gamma 減速區（低買高賣，均值回歸）。<br>**現價 < Flip**：負 Gamma 加速區（追漲殺跌，順勢放大波動）。 |
| **2. `CALL WALL`** | **🟢 上方最大正 Gamma 鐵板** | 現價上方 `Net vGEX` 最大（最高藍柱）之履約價。 | 當日上方最強天花板阻力；若通過 IV 驗真為 Dealer Long Gamma，價格衝進此區必遭造市商機械式期貨賣壓擊落。 |
| **3. `PUT TRIGGER`** | **🔴 下方最大負 Gamma 扳機** | 現價下方 `Net vGEX` 負值最深（最長橘柱）之履約價。 | 初次觸及時有短線平倉支撐；但**一旦實質跌破，造市商被迫不計價追空期貨（Trapdoor 瀑布急殺）**，並成為尾盤收斂磁鐵。 |
| **4. `PUT OI WALL`** | **🛡️ 隔夜 Put OI 支撐牆** | 現價下方 `Put Trigger` 之下，`PUT OI`（昨日留倉量）最大的履約價。 | 當日內 `Put Trigger` 被跌破引發瀑布下殺時，**昨晚留倉的老空頭會在此處大量獲利平倉（賣回 Put）**，迫使造市商買回期貨空單，形成全天最低點的終極止跌區。 |
| **5. `KING PIN`** | **🧲 全場最大磁吸釘住點** | 全場 `Pin vGEX`（`Call + |Put|` 絕對總量）最高之履約價。 | 盤中無重大新聞時的反彈吸引中心與雙向泥沼區。 |

---

### Step 3：IV 曲率（IV Smile Curvature）驗明造市商真實買賣方向（核心獨家武器）
絕對不可盲目假設「Call 永遠是正 Gamma、Put 永遠是負 Gamma」！必須檢驗每個履約價的隱含波動率二階差分：
$$\text{IV\_Curvature}_K = \text{IV}_K - \frac{\text{IV}_{K-5} + \text{IV}_{K+5}}{2}$$
- **情境 A（真鐵板 `❄️`：巨量 Call + IV 局部最低谷 / 負曲率）**：
  - 若上方 `Call Wall`（如 `7660~7670`）累積數萬口 Call Volume，且其 `IV` 被砸到全場最低谷（$\text{IV\_Curvature} < 0$），代表**市場大戶（Overwrite 基金）在主動拋售 Call 給造市商**。
  - **結論**：造市商 **100% 是真買方（Long Gamma）**！指數拉升至該區時，造市商必拋售 ES 期貨壓制，為極高勝率之放空鐵板。
- **情境 B（假鐵板 / 軋空警報 🔥：巨量 Call + IV 異常飆高 / 正曲率）**：
  - 若上方某履約價 Call Volume 暴增，且其 `IV` 較鄰近履約價明顯凸起（$\text{IV\_Curvature} > 0$），代表**市場在主動搶買 Call（Sweeps）**，造市商被迫當賣方（Short Gamma）。
  - **結論**：此處**不是阻力而是軋空燃料**，突破將引發造市商被迫追買期貨！
- **情境 C（下方恐慌搶買 Put：巨量 Put + Put Skew 陡峭飆升）**：
  - 若現價下方 Put Volume 暴增且 IV 往低履約價一路陡峭拉升，代表市場主動搶買 Put 避險，造市商實錘處於 **Short Put（負 Gamma）**，跌破必觸發順勢追空。

---

### Step 4：盤中前後快照增量對比（$\Delta\text{Volume}$ & $\Delta\text{IV}$ Flow Tracking）
當同一交易日上傳第 2 筆以上快照（如 `#002` 對比 `#001`）時，自動計算每個履約價的增量：
$$\Delta\text{CallVol}_K = \text{CallVol}_{K, t} - \text{CallVol}_{K, t-1}, \quad \Delta\text{PutVol}_K = \text{PutVol}_{K, t} - \text{PutVol}_{K, t-1}$$
$$\Delta\text{IV}_K = \text{IV}_{K, t} - \text{IV}_{K, t-1}$$
- **$\Delta\text{Vol}$ 暴增 + $\Delta\text{IV} > 0$** $\rightarrow$ 主力資金正在**主動敲進（買方開倉）**，造市商被迫站賣方（Short Gamma 增加）。
- **$\Delta\text{Vol}$ 暴增 + $\Delta\text{IV} < 0$** $\rightarrow$ 主力資金正在**主動拋售（賣方開倉或買方止盈平倉）**，造市商站在買方（Long Gamma 增加）。
- **假突破 / 假跌破驗真**：若指數短線跌破某關卡（如 `7805`），但下方更深價外 Put（如 `7800`、`7795`）出現 **$\Delta\text{PutVol} = 0$（零新增追空）且 $\Delta\text{IV} < 0$（全場縮波）**，即實錘為「假跌破誘空陷阱（Bear Trap）」，應逢低承接看回中心磁王。

---

### Step 5：當下需要注意什麼 & 接下來劇本推演與關鍵點位（結合當日全序列變化推導 Scenario Playbooks A / B / C）
每一筆快照分析（無論在對話文字回覆或網頁 `index.html` 的 `SNAPSHOT.playbook_html` 中）都**必須根據「當日先前所有快照 (`#001 ～ #N`) 的連續變化軌跡」加上「與前一筆 (`#N-1`) 的增量對比」來推導以下兩大實戰區塊**（網頁 `index.html` 版面則保持乾淨，僅呈現最新一筆之圖表、報價梯與最新劇本）：

- **四大核心推導法則（Multi-Snapshot Trajectory Deduction）**：
  1. **連續變化抓「真假破底 / 真假突破」**：當指數回測或突破某關卡時，檢查正下方/正上方 1～2 格履約價在過去數筆快照是否出現 **「$\Delta\text{Put}$ 或 $\Delta\text{Call}$ 連續零新增」＋「近端 IV 持續縮波破底 (`❄️`)」**（例如跌到 `7805` 時下方 `7800 Put` 連續零新增且翻正 Gamma $\rightarrow$ 實錘為假跌破誘空陷阱，應逢低接多）。
  2. **Call / Put 增速黃金交叉抓「多空翻轉點」**：追蹤核心磁吸王履約價（如 `7810`、`7815`）在連續數筆快照中的 $\Delta\text{Call}$ 與 $\Delta\text{Put}$ 增速差；當 Call 總量正式追平並反超 Put 總量（使該格由負 Gamma 翻轉為正 Gamma）時，該點位即從「頭頂蓋子」切換為「腳下護盤彈簧墊」。
  3. **雙磁王幾何中心與大牆提前量（`±0.5 ～ 1.5 點` Buffer）**：當場上形成雙磁王（如 `7810` 與 `7815`）時，以雙磁王之幾何中點（如 `7812.50`）或磁吸加權重心作為收斂目標；並在巨型正 Gamma 牆前預留 `0.5 ～ 1.5 點` 作為實戰止盈與逆勢短空提前量。
  4. **依上方賣方鐵蓋（Call 暴增 + IV 破底）與剩餘時間動態分配機率 `%`**：依正負 Gamma 牆厚度與 IV 曲率動態給出劇本 A / B / C 之發生機率。

1. **⚠️ 一、當下最需要注意的實戰關鍵（Points of Caution）**：
   - 點出當前最容易誤判的結構陷阱（例如：表面負 vGEX 但實為高磁吸減速泥沼、多單已達雙磁王幾何中心必須止盈不可追高、或某履約價由負翻正形成腳下鐵墊等）。
2. **📈 二、接下來劇本推演與關鍵點位（劇本 A / 劇本 B / 劇本 C）**：
   - **🎯 劇本 A（主劇本，標註機率 %）**：給出最高機率的走勢路徑、上檔壓制區、下檔支撐墊、收斂中心點，以及具體進出場 / 止盈 / 高拋低吸點位。
   - **🚀 劇本 B（次劇本，標註機率 %）**：給出向上突破或向下延伸時的觸發條件、造市商對沖行為變化，以及下一道極限封頂 / 止跌目標位。
   - **🛡️ 劇本 C（極端風控劇本，標註機率 %）**：給出結構反轉的破位扳機點（Trigger）與嚴格停損退守位置。

---

## 四、 互動網頁儀表板 (`index.html`) 視覺與功能規格

網頁必須為單一獨立 HTML 檔（使用原生 SVG 繪圖，無外部 CDN 依賴，確保在本地端、沙盒預覽與 GitHub Pages 皆能 100% 正常渲染）：

1. **頂部控制列與「🎯 對應 ES 期貨點位」一鍵切換**：
   - 顯示當前快照日期、編號（如 `Snapshot #010`）、SPX 現價、Gamma Regime 狀態燈（🟢 正 Gamma 穩定區 / 🔴 負 Gamma 加速區）。
   - **ES 期貨價差換算器 (`ES Basis`)**：輸入框即時連動全網頁所有點位顯示 `ES 目標價`。
   - **🎯 對應 ES 期貨點位切換按鈕 (`toggleESMode`)**：點擊後，將全網頁五大卡片、雙圖表 X 軸與標記線、左側報價梯，以及**右側 AI 實戰報告內所有 `<code>7XXX</code>` 點位自動加上 `[ES XXXX]` 期貨點位換算**（並記憶於 `localStorage`）。
   - **主題切換按鈕**：`☀️ 白底模式 (Barchart)` vs. `🌙 黑底模式 (夜盤)`（自動記憶至 `localStorage`）。
2. **五大關鍵點位卡片列**：並排顯示 `GAMMA FLIP`、`CALL WALL`、`PUT TRIGGER`、`PUT OI WALL`、`KING PIN`（含 SPX 點位、ES 換算點位、GEX 規模與操作提示）。
3. **Barchart 風格雙圖表區（支援左右並排 / 上下大圖切換，及 Volume vGEX / OI GEX 切換）**：
   - **左圖 `① $SPX - Net Gamma Exposure by Strike`**：
     - 垂直柱狀圖（左軸）：`Call - Put` 相減淨值（正值寶藍色 `#1d4ed8` 向上，負值橘黃色 `#ea580c` 向下）。
     - 平滑曲線（右軸）：`Aggregate Gamma Exposure` 累積曲線（水藍色 `#38bdf8`）。
     - 垂直標記線：`Last Price`（深綠實線）、`Put Wall`（紅虛線，可點擊圖例開關）、`Call Wall`（綠虛線，可點擊圖例開關）。
   - **右圖 `② $SPX - Call vs. Put Gamma Exposure`**：
     - 對稱拆解垂直柱狀圖（左軸）：同一履約價上方畫 `Call Gamma Exposure`（寶藍向上），下方畫 `Put Gamma Exposure`（橘黃向下）。
     - 磁吸曲線（左軸）：`Absolute Exposure`（`Call + |Put|` 總磁吸強度紫色虛線 `#8b5cf6`，可點擊圖例開關）。
     - 垂直標記線：`Last Price`（深綠實線）。
4. **左下角：報價梯明細表 (`Strike Ladder`)**：由高到低排列，內含水平雙向能量條、增量欄位與 `IV (%)` 最低谷 `❄️` 驗真標記。
5. **右下角：AI 實戰量化分析報告（必須完整包含四大核心區塊）**：
   - **1️⃣ 造市商底牌驗真（IV Skew 照妖鏡）**
   - **2️⃣ 當下需要注意什麼 & 接下來劇本推演與關鍵點位（劇本 A / B / C）**：直接渲染 `SNAPSHOT.playbook_html`，完整呈現「⚠️ 一、當下最需要注意的實戰關鍵」與「📈 二、接下來劇本推演與關鍵點位（劇本 A 主劇本 / 劇本 B 次劇本 / 劇本 C 下檔風控劇本，含機率 %、走勢路徑、關鍵點位與具體操作策略）」，並支援點擊「對應 ES」自動換算全文點位。
   - **3️⃣ 盤中前後快照增量對比 ($\Delta\text{Volume}$ & $\Delta\text{IV}$)**：渲染 `SNAPSHOT.delta_summary.html_summary`。
   - **📌 當期重點觀察與行情複盤**：渲染 `SNAPSHOT.extra_notes_html`。

---

## 五、 GitHub 自動歸檔與部署標準作業程序 (GitHub SOP)

### 1. 儲存庫資訊與目錄結構
- **GitHub Repository**：`https://github.com/acstep/spx-gex-dashboard`
- **GitHub Pages 線上網址**：`https://acstep.github.io/spx-gex-dashboard/`
- **檔案結構規範**：
  ```text
  spx-gex-dashboard/
  ├── index.html                                         # 永遠只顯示「最新一筆」完整互動儀表板
  ├── latest.json                                        # 最新一筆快照之完整計算結果 JSON
  ├── README.md                                          # 專案說明與歷史快照索引表
  ├── SPX_GEX_Full_Workflow_With_GitHub.md               # 本完整工作流 SOP 文件（不含任何 Token）
  ├── SPX_GEX_AI_Analysis_Prompt_Only.md                 # 純 AI 分析專用 Prompt 文件（不含 GitHub 與 Token）
  └── data/
      ├── manifest.json                                  # 所有歷史上傳快照的總索引清單
      └── YYYY-MM-DD/                                    # 依交易日期分資料夾保存
          ├── YYYYMMDD_001_spotXXXX.XX_raw.csv           # 第 1 筆原始 IBKR 選擇權鏈 CSV（永久保存）
          ├── YYYYMMDD_001_spotXXXX.XX_calc.json         # 第 1 筆三層 GEX 計算結果 JSON（永久保存）
          ├── YYYYMMDD_002_spotXXXX.XX_raw.csv           # 同日第 2 筆原始 CSV（自動遞增編號，絕不覆蓋）
          └── YYYYMMDD_002_spotXXXX.XX_calc.json         # 同日第 2 筆計算結果（自動帶入與 #001 的 ΔVolume/ΔIV 對比）
  ```

### 2. 每次收到新數據時的自動化執行步驟（Python / Git 腳本流程）
當使用者在對話中貼上新的選擇權鏈數據或截圖時，AI 必須自動執行以下動作：

1. **解析與驗證數據**：提取日期 `YYYY-MM-DD`、現價 `Spot` 與所有履約價之 Greeks / Volume / OI。
2. **檢查當日流水號 (`SEQ`)**：
   - 讀取 `data/manifest.json`（或查詢 GitHub API `contents/data/YYYY-MM-DD`），找出當日已有幾筆快照，將新快照編號設為 `SEQ = N + 1`（格式化為 3 位數，如 `001`、`002`、`003`）。
   - 若當日已有前一筆快照 `SEQ - 1`，自動讀取前一筆 `_calc.json`，計算每個履約價的 `dcvol` ($\Delta\text{CallVol}$)、`dpvol` ($\Delta\text{PutVol}$)、`dnet_vol` 與 `div` ($\Delta\text{IV}$)。
3. **寫入歸檔檔案（嚴禁覆蓋歷史檔案）**：
   - 產生 `data/YYYY-MM-DD/YYYYMMDD_SEQ_spotXXXX.XX_raw.csv`
   - 產生 `data/YYYY-MM-DD/YYYYMMDD_SEQ_spotXXXX.XX_calc.json`
   - 更新 `data/manifest.json` 與根目錄 `latest.json`
4. **重新編譯 `index.html`**：
   - 將最新一筆 `SNAPSHOT` JSON 內嵌至 `index.html` 中，確保打開網頁即直接呈現最新一期圖表與分析報告。
5. **推送至 GitHub（安全規範）**：
   - 使用環境變數 `$GITHUB_TOKEN` 透過 Git 或 GitHub REST API (`PUT /repos/acstep/spx-gex-dashboard/contents/...`) 上傳檔案。
   - ⚠️ **嚴格安全守則**：任何提交至 GitHub 的程式碼、Markdown 或 JSON 檔案中，**絕對不可包含任何真實 Personal Access Token 或私密金鑰字串**！

---

## 六、 在新對話視窗一鍵啟動之話術（Copy-Paste 啟動指令）

當你開啟一個全新的 AI 對話視窗時，只需把這份檔案丟給 AI，並說：

> **「請讀取這份 `SPX_GEX_Full_Workflow_With_GitHub.md` 作為你的系統規範。接下來我每次貼上或上傳 IBKR 的 SPX/ES 選擇權鏈數據，請自動幫我：1. 完成三層 GEX + IV 驗真分析與實戰劇本；2. 將 raw.csv 與 calc.json 按流水號歸檔至 `acstep/spx-gex-dashboard` 的 `/data/YYYY-MM-DD/` 目錄；3. 更新 `index.html` 只顯示最新一期雙圖表儀表板並推送到 GitHub Pages。」**
