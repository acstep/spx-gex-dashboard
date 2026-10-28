# 每次給你希臘字母，我到底做了什麼（完整 SOP）

> 🚨 **【觸發卡｜看到這段就照做】**  
> 只要你（使用者）之後在任何話題中丟來 **選擇權鏈截圖 / CSV / Excel / 一句「跑下一筆」**，我**立刻切換回 GEX 模式**，不需要你重講：
> 1. 先建 `audit/raw_YYYYMMDD_NNN.py`（現價＋逐列原始數字，**唯一可信來源**）
> 2. 重算 `MULT_M = 100×S²×0.01/1e6`（**不可沿用上一筆**）
> 3. 算 6 個總量 ＋ 5 個關鍵點位 ＋ ⭐15 點叢集重心 ＋ Flip（**累積法**）
> 4. **增量分解**：新成交 vs IV 重估（>60% 重估＝不可交易）
> 5. 產 7 檔 → 推 GitHub → 驗 4 關（API／Pages 200／jsdom 0 error／manifest 一致）
> 6. 回覆格式：關鍵數字表 → 三個最重要變化 → 結構判讀 → 三劇本 A/B/C → **📎 更新連結**
>
> ⚠️ 鐵律：磁鐵＝15 點叢集重心（不是最大單檔）｜Flip 用累積法｜絕不把 token 寫進任何檔｜`[[數字]]` 只能放 `tldr_html` / `whyText`

---

## 0. 一句話版本

**你給資料 → 我存原始鏈 → 算 7 個數字 → 比對前一筆 → 寫三段敘事 → 產 7 個檔 → 推上 GitHub → 驗證 200 → 回你一張表＋劇本。**

---

## 1. 你給我什麼（三種都可以）

| 形式 | 我要的欄位 | 準確度 | 我的處理 |
|---|---|---|---|
| **① Excel 截圖** | 見下方欄位表 | 中（我要逐列讀） | 切成數段放大逐列判讀，**推論值會標註** |
| **② CSV**（`gex_from_excel.py` 產的 `gex_calc.csv`） | 見下方欄位表 | 高 | 直接讀，不做推論 |
| **③ 直接說「跑下一筆」** | 我會用上次的口徑 | — | 需要你補現價與時間 |

### 我需要的最小欄位集

| 欄位 | 用途 | 缺少會怎樣 |
|---|---|---|
| **Strike** | 橫軸 | 不能算 |
| **Call Volume / Put Volume** | 淨 GEX 主體 | 不能算（除非改用 OI） |
| **Gamma**（Call / Put 各一或共用） | 乘數 | 不能算 |
| Spot（現價） | 乘數 `S²`、地／天、Flip 相對位置 | 不能算 |
| Call OI / Put OI | OI 口徑參考 | 可缺，但少一層驗證 |
| IV | IV 升降、微笑、偏斜 | 可缺，但少「引擎」那一層 |
| 日期 / 時間 | 檔名、時序 | 我會推定並標註 |

> 你的表是：`Right|IV|Delta|Gamma|Vega|Theta | Strike | Right|IV|Delta|Gamma|Vega|Theta | CallVolume|PutVolume|CALL OI|PUT OI`
> （Call、Put 的 **Gamma 欄常常是同一組數字**，那就兩邊都用同一值，我會在回覆裡註明。）

---

## 2. 我做的第一步：把原始鏈釘死（**先存檔，再計算**）

```
audit/raw_YYYYMMDD_NNN.py
```

內容長這樣（**這是唯一可信來源，之後所有數字都從這裡重算**）：

```python
SPOT = 7723.49
DATE = "2026-10-27"
SEQ  = 9
# strike, iv, cdelta, gamma, vega, ctheta, pdelta, ptheta, cvol, pvol, coi, poi
RAW = [
(7600,0.38114846,0.99628471,0.00023893,0.01492131,-0.25273528,-0.00373061,-0.05355992,454,9124,259,3984),
...
]
```

**為什麼一定要先存**：
- 截圖 OCR 一定有風險 → 存成數字後可以逐項核對、可以重算、可以回溯
- 之後每一筆的「Δ」都要拿前一筆的原始鏈來對
- 出錯時只改這一個檔，重跑就好

---

## 3. 計算：只有 7 個數字

### 3-1 乘數（**每次現價變就要重算**）

```
MULT_M = 100 × S² × 0.01 / 1e6        # 單位：百萬美元
```

| 現價 | MULT_M |
|---|---|
| 7,728.74（#008） | 59.7334 |
| 7,723.49（#009） | **59.6523** |

> 口語：「S² 是因為 Gamma 是對價格的二階導數，×0.01 是 1% 移動，×100 是乘數。」
> **絕對不要把上一個現價的 MULT 拿來用**，誤差會直接進到總量。

### 3-2 三個曝險（單位：$M，再 ÷1000 轉 $B）

```python
vol_vgex = (cvol - pvol) * gamma * MULT_M      # 成交量口徑 → 主圖用這個
pin_vgex = (cvol + pvol) * gamma * MULT_M      # 絕對曝險（磁吸強度）
oi_gex   = (coi  - poi ) * gamma * MULT_M      # 未平倉口徑 → 參考
```

> **符號約定**：交易商口徑 `long call / short put` → Put 取負，所以是 `cvol − pvol`。
> 若 Call / Put 的 gamma 不同，就寫成 `cvol*cgamma − pvol*pgamma`，結果等價。

**實例驗證（#009 的 7,730）**
```
(141,996 − 30,960) × 0.02959374 × 59.6523 = 196,000 $M = +$196.02B  ✅
```

### 3-3 總表（每一筆都要留這 6 個）

| 名稱 | 公式 | #009 值 |
|---|---|---|
| 淨 vGEX | `Σ vol_vgex / 1000` | **+$613.75B** |
| 正／負分區 | 分開加總 | +$688.58B / −$74.83B（9.20:1） |
| 絕對合計 | `Σ pin_vgex / 1000` | **$1,979.15B** |
| 現價以下 | `Σ vol_vgex where strike ≤ spot` | **+$19.61B** |
| 現價以上 | `Σ vol_vgex where strike > spot` | **+$594.14B** |
| 地／天比 | ⚠️ 見 3-5 | 0.60 |

---

## 4. 五個關鍵點位（+ 三個我額外加的）

| 代號 | 定義 | #009 |
|---|---|---|
| **Call Wall** | `max(vol_vgex)` | **7,730 +$196.02B** |
| **Put Trigger** | `min(vol_vgex)` | **7,700 −$15.05B** |
| **King Pin（王牌）** | `max(pin_vgex)` | **7,720 $406.60B（20.5%）** |
| **ATM** | 最接近現價的檔 | 7,725 |
| **Min IV** | `min(iv)` | 7,725 **9.41%** |
| **Put OI Wall** | `[S−60, S−5]` 內 `max(poi)` | 7,675（2,737 口） |
| ⭐ **15 點叢集重心** | `Σ(strike×pin)/Σpin`，`|strike−S|≤15` | **7,722.68（距 −0.81）** |
| ⭐ **最負單檔 / 最大 Put 量** | 分開看 | 7,700（92,257 口） |

> ⭐ 這兩個不在你的原始規格裡，是我從 #008 的錯誤中加的（見第 8 節鐵律一）。

---

## 5. Gamma Flip：一定要用「累積法」

```python
cum = 0
prev_cum = prev_k = None
for r in rows_sorted_by_strike:
    cum += r["vol_vgex"]
    if prev_cum is not None and prev_cum < 0 <= cum and flip is None:
        flip = prev_k + (r["strike"] - prev_k) * (-prev_cum) / (cum - prev_cum)
    prev_k, prev_cum = r["strike"], cum
```

- **累積法 = 主值**（寫進 `gamma_flip`）
- **單檔法**（第一個 `vol_vgex > 0` 的檔）只當對照，寫進 `gamma_flip_single`
- 兩者相差 <2 點 → 可交易；差很多 → 只當結構參考，停損改用「最近的厚 Gamma 檔」

| #008 | #009 |
|---|---|
| 累積 7,715.4／單檔 7,701.3（差 14.1） | 累積 **7,719.0**／單檔 7,720（差 1.0） |

---

## 6. 增量分解（**這一節是整份 SOP 最重要的，也最容易被跳過**）

拿到新一筆後，把「淨 GEX 多了多少」拆成兩塊：

```python
for r in rows:
    p = prev_by[r["strike"]]
    vol_effect  += ((r.cvol - r.pvol) - (p.cvol - p.pvol)) * r.gamma          * MULT
    reprice     +=  (p.cvol - p.pvol) * (r.gamma - p.gamma)                  * MULT
# ΔvGEX = vol_effect + reprice
```

| #009 | 金額 | 佔比 |
|---|---|---|
| 新成交（真錢） | +$42.13B | 35.9% |
| **重估（IV 變動）** | **+$75.09B** | **64.1%** |

**判讀規則**

| 重估佔比 | 意思 | 我怎麼用 |
|---|---|---|
| <40% | 真錢在動 | 增厚可信，可順勢 |
| 40–60% | 混合 | 減碼、等下一筆 |
| **>60%** | **IV 崩塌造成的「假厚」** | **不可交易**，壓低順勢權重 |

> #009 就是 64.1%：7,725 的 IV 11.43→9.41，gamma 被動放大 58%，淨 GEX 才「多」了 $116B。

**同時要算的三件事**

```python
ΔC = Σ(r.cvol - p.cvol)      # 本段新增 Call 口數
ΔP = Σ(r.pvol - p.pvol)      # 本段新增 Put 口數
C/P = Σcvol / Σpvol          # 當日累計
```
→ 並看「新增的錢堆在哪幾個檔」（#009：Put 55% 落在 7,700–7,720；Call 51% 落在 7,720–7,730）。

---

## 7. IV 三件事（價格不告訴你的「引擎」）

| 指標 | 怎麼算 | #009 |
|---|---|---|
| 升降比 | `iv > prev_iv` 的檔數 / `<` 的檔數 | **29 升 / 13 跌** |
| **偏斜 Skew** | `iv(最低檔) − iv(最高檔)` | 38.11 − 27.39 = **10.72**（#008 是 9.91） |
| 最低 IV 位置 | `min(iv)` | 7,725 **9.41%** |
| 微笑偏離 | `iv − (iv[i−1]+iv[i+1])/2` → `div` 欄 | 寫進 calc.json |
| **「微笑變深」判別** | ATM 跌 ＋ 兩翼漲 | ✅ #009 就是（中間崩、兩頭升） |

> **29 升 / 13 跌 ≠ 全面上升**。#009 是「ATM 崩、兩翼漲」，這叫**微笑變深**，意思是「大家一致認為明天波動會變大」，不是「一致看多」。

---

## 8. 三大鐵律（每次都要主動拿出來對一遍）

### 鐵律一：磁鐵＝「15 點叢集重心」，不是最大單檔
- 重心距現價 **<5 點** → 貼著磨
- **5–12 點** → 來回但往重心靠
- **>12 點** → 重心失效，改用 Flip ＋ 下方正 Gamma 厚度

> 來源：#008 我用「7,730 單檔 $157B」判「被吸住」，結果價格走了 6.5 點。#009 重心 7,722.68（距 −0.81）才對得上。

### 鐵律二：IV 崩塌造成的增厚不可交易
- 三個特徵：① 集中在 ATM ② 下方同步被重估變薄 ③ IV 回彈就全部還回去

### 鐵律三：同一個價位可以同時是「磁鐵」與「懸崖」
- #009 的 7,720＝ Pin 20.5% ＋ 下方最後一塊正 Gamma ＋ Flip 在它下面 1 點
- 站上＝吸住；跌破＝推下去 → **停損直接放 Flip，不凹**

---

## 9. 我要產出的 7 個檔案

| # | 檔案 | 內容 |
|---|---|---|
| 1 | `audit/raw_YYYYMMDD_NNN.py` | 原始鏈（**唯一可信來源**） |
| 2 | `data/YYYY-MM-DD/YYYYMMDD_NNN_spotXXXX.XX_raw.csv` | 18 欄標準 CSV |
| 3 | `data/YYYY-MM-DD/YYYYMMDD_NNN_spotXXXX.XX_calc.json` | 全部計算＋敘事（下面第 10 節的結構） |
| 4 | `latest.json` | = calc.json（頁面自動抓這支） |
| 5 | `data/manifest.json` | 快照索引，`total_snapshots` ＋1 |
| 6 | `index.html` | 換掉內嵌 `let SNAPSHOT = {...};` |
| 7 | 兩份 MD | `…Ledger.md`（對帳）＋ `…Workflow.md`（附錄案例） |

### calc.json 的結構（前端靠這些 key）

```jsonc
{
  "date": "2026-10-27", "seq": 9, "seq_str": "009",
  "spot": 7723.49, "mult_m": 59.6523,
  "totals": { "tot_vgex_b": 613.75, "tot_oigex_b": 3.84, "tot_pin_b": 1979.15,
              "loc15_vgex_b": 537.53, "below20_vgex_b": 237.30, "above20_vgex_b": 393.22 },
  "key_levels": { "call_wall": {...}, "put_trigger": {...}, "put_oi_wall": {...},
                  "king_pin": {...}, "atm_row": {...}, "min_iv_row": {...},
                  "gamma_flip": 7719.0, "gamma_flip_single": 7720 },
  "quick_guide": { "tldr_html": "...", "cards": [ 5 張 ] },
  "delta_summary": { "has_prev": true, "prev_seq": "008", "prev_spot": 7728.74, "html_summary": "..." },
  "playbook_html": "...",        // 環境＋劇本對帳＋📌4️⃣ 四大真相/三大鐵律
  "extra_notes_html": "...",     // ⚠️ 當下需要注意什麼 ＋ 📈 接下來劇本推演與關鍵點位
  "rows": [ 21 個 key 的陣列 ],
  "updated_at": "2026-10-27T21:30:00Z"
}
```

**rows 每列的 21 個 key**：
`strike, iv, div, gamma, cdelta, pdelta, cvega, ctheta, ptheta, cvol, pvol, dcvol, dpvol, dnet_vol, coi, poi, vol_vgex, d_vgex, pin_vgex, oi_gex, role`

---

## 10. 我要寫的三段敘事（固定格式，不可省）

### ① `quick_guide.tldr_html`（一句話看懂）
```
💡 一句話看懂（#009 現價 [[7723.49]]｜#008 [[7728.74]] ➔ −5.25）
🚨 三個警訊 / 👑 一個極端結構 / 🎭 最關鍵的微觀訊號
👉 口訣：① 門檻 ② 黑洞 ③ 天花板
```
> `[[數字]]` 是給前端自動轉成「SPX→ES 對照」的語法，**只允許出現在 `tldr_html` / `whyText`**。

### ② `quick_guide.cards`（5 張白話卡）
每張 4 個欄位：`badge`（標題）、`actionText`（數字）、`whyText`（為什麼）、`strike`（`[[價位]]`）

#009 的五張：IV 微笑變深／地板被抽乾／7,715 翻負／7,720 新王牌 Pin／Put 增量首度反超

### ③ `delta_summary.html_summary`（跟前一筆的 12 條 Δ）
固定 12 條：現價、淨 GEX、負 Gamma 區、翻負檔位、最負檔位上移、地／天、Flip、正負加厚對比、Pin 集中度、量能、新錢位置、IV 升跌＋偏斜、重估佔比。

### ④ `playbook_html`
```
🌍 環境（FOMC / 利率 / 財報 / 地緣 / 油價）
✅ 上一筆三劇本對帳（A/B/C 各自命中或失準，附「誠實檢討」）
📌 4️⃣ 當日全序列追蹤（#001 → #NNN）：四大真相 ＋ 三大實戰鐵律
```

### ⑤ `extra_notes_html`
```
⚠️ 當下需要注意什麼（5–6 條，含事件時鐘與資料可信度）
📈 接下來劇本推演與關鍵點位（A/B/C 機率＋觸發＋路徑 ＋ 關鍵點位表）
```

---

## 11. 上傳與驗證（**沒驗證不算完成**）

```
_push.py  FILES = [ raw.csv, calc.json, manifest.json, latest.json, index.html ]
         （有寫 MD 時再加那兩份）
```

**驗證四關**

| 關 | 怎麼驗 | 通過標準 |
|---|---|---|
| 1 | GitHub API `contents/latest.json` | `seq` / `spot` / `rows` 對得上 |
| 2 | `acstep.github.io/…?cb=<ts>` | HTTP 200，內文含新 `"seq": N` 與 `spot` |
| 3 | jsdom 渲染 index.html | **0 errors**、`[[ ]]` 無殘留、`disp-spot` 正確 |
| 4 | manifest | `total_snapshots == len(snapshots)` |

> ⚠️ **Pages 有 CDN 延遲**（實測 40–60 秒）。看到舊版不是失敗，加 `?cb=` 輪詢。
> ⚠️ **raw.githubusercontent 也會落後**，一律優先打 `api.github.com`。

---

## 12. 我回你什麼（固定格式）

```
# 標題（一句話結論）
1. 這次推了哪些檔（commit hash ＋ HTTP 200 證據）
2. 關鍵數字表（#N−1 vs #N vs 變化）
3. 三個最重要的變化（附「翻譯」）
4. 我怎麼讀這個結構（懸崖圖／示意）
5. 三劇本 A/B/C ＋ 機率 ＋ 路徑
6. 檔案版本／啟動指令（若動到工具）
7. 📎 本次更新連結（必附，先驗 200）
```

---

## 13. 我自己常犯、你已經抓過的 8 個錯（別再犯）

| # | 錯 | 修正 |
|---|---|---|
| 1 | 用舊現價的 `MULT` | 每筆重算 `S²` |
| 2 | `updated_at` 硬編碼 | 填**實際** UTC |
| 3 | 負 Gamma 用 totals 反推 | 一律逐檔重算 |
| 4 | Flip 用單檔法 | **累積法為主**，單檔只當對照 |
| 5 | 「磁鐵＝最大單檔」 | 改 **15 點叢集重心** |
| 6 | 把「淨 Gamma 增厚」直接當買盤 | 先做**重估分解** |
| 7 | 交付多檔工具 → 版本不同步 | 工具一律**單檔自足** |
| 8 | `[[ ]]` 寫到不該寫的地方 | 只放 `tldr_html` / `whyText` |

---

## 14. 你要貼給我時，最省事的模板

```
10/28 #010
SPX 7723.49（14:05 ET）
[截圖 / CSV / Excel 路徑]
```

我就會：建 raw → 算 → 比對 #009 → 三段敘事 → 推 7 檔 → 驗 4 關 → 回你表格＋劇本。

---

## 15. 快速對照：口徑差異（很重要，別搞混）

| 口徑 | 公式 | 出現在哪 |
|---|---|---|
| **成交量口徑（主）** | `(Cvol − Pvol) × Γ × MULT` | 儀表板主圖、`vol_vgex` |
| **OI 口徑（參考）** | `(Coi − Poi) × Γ × MULT` | `oi_gex`，看「留倉」不看「今日」 |
| **絕對曝險** | `(Cvol + Pvol) × Γ × MULT` | `pin_vgex`、紫線「磁吸強度」 |
| **Python UI 工具** | `(Cvol×Γc − Pvol×Γp) × S²×0.01×100/1e9` | `gex_live_ui.py`（Call/Put gamma 分開時才不同） |

> 兩種寫法在「Call / Put gamma 相同」時**數值完全相同**，只是單位寫法不同（÷1e6 再 ÷1000 vs ÷1e9）。
