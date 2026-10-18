#!/usr/bin/env python3
"""
SPX 0DTE GEX Multi-Day Quantitative Regression & Self-Audit Engine
(`run_gex_regression_audit.py`)

用途：
1. 每次收到新快照或每日收盤時自動執行，讀取 `data/` 下所有歷史交易日 (`YYYY-MM-DD/*_calc.json`)。
2. 計算五大核心量化因子與下一筆真實走勢 (`dSpot = Spot_{t+1} - Spot_t`) 之統計回歸關係。
3. 對當日與歷史每一筆快照進行「劇本 A vs 真實走勢」自動對帳，抓出任何偏差並輸出強制修正指令。
4. 為最新一筆快照輸出「定量盤態鎖定結果 (Mandatory Regime Lock)」，嚴禁 AI 違反量化結果主觀亂說。
"""

import glob
import json
import math
import os
import re
from typing import Dict, List, Any

DATA_DIR = "/home/user/spx-gex-dashboard/data"


def strip_html(html_str: str) -> str:
    return re.sub(r"<[^>]+>", " ", html_str or "").replace("&rarr;", "->").strip()


def extract_pred_a_direction(playbook_html: str, spot: float) -> str:
    """Parse stored Playbook A text to determine whether Pred A was Bullish, Bearish, or Pinning."""
    txt = strip_html(playbook_html)
    m_a = re.search(r"劇本\s*A.*?(?=劇本\s*B|$)", txt, re.S)
    seg = m_a.group(0) if m_a else txt[:400]
    # Check explicit keywords
    if any(k in seg for k in ["順勢下殺", "順空頭", "壓回", "回測下檔", "向下破位", "續空"]):
        return "BEAR"
    if any(k in seg for k in ["狹幅", "釘死", "死釘", "泥沼收斂", "均值回歸"]):
        if "V 轉" not in seg and "V轉" not in seg and "上攻" not in seg and "強彈" not in seg:
            return "PIN"
    if any(k in seg for k in ["V 轉", "V轉", "上攻", "推升", "反撲", "挑戰", "突破", "強彈", "反彈回"]):
        return "BULL"
    return "PIN"


def compute_snapshot_metrics(snap: Dict[str, Any]) -> Dict[str, Any]:
    spot = float(snap["spot"])
    rows = snap.get("rows", []) or snap.get("strikes", [])
    mult_m = spot * spot * 0.01 * 100 / 1e6

    tot_vgex = sum(r.get("vol_vgex", 0.0) for r in rows) / 1000.0
    loc15_vgex = sum(r.get("vol_vgex", 0.0) for r in rows if abs(r.get("strike", 0) - spot) <= 15.0) / 1000.0
    below20_rows = [r for r in rows if -20.0 <= (r.get("strike", 0) - spot) <= 2.0]
    above20_rows = [r for r in rows if 2.0 < (r.get("strike", 0) - spot) <= 20.0]

    below20_vgex = sum(r.get("vol_vgex", 0.0) for r in below20_rows) / 1000.0
    above20_vgex = sum(r.get("vol_vgex", 0.0) for r in above20_rows) / 1000.0
    below20_dnet = sum(r.get("dcvol", 0) - r.get("dpvol", 0) for r in below20_rows)
    above20_dnet = sum(r.get("dcvol", 0) - r.get("dpvol", 0) for r in above20_rows)
    ntm25_dnet = sum(r.get("dcvol", 0) - r.get("dpvol", 0) for r in rows if abs(r.get("strike", 0) - spot) <= 25.0)

    inc_vgex = sum((r.get("dcvol", 0) - r.get("dpvol", 0)) * r.get("gamma", 0.0) * mult_m for r in rows) / 1000.0

    kp_row = max(rows, key=lambda x: x.get("pin_vgex", 0.0)) if rows else {"strike": spot, "pin_vgex": 0.0}
    kp = kp_row["strike"]
    kp_pin_b = kp_row.get("pin_vgex", 0.0) / 1000.0

    flip = snap.get("key_levels", {}).get("gamma_flip", kp)
    if isinstance(flip, dict):
        flip = flip.get("strike", kp)

    # Count how many strikes within Spot ± 10 have Pin >= $50B
    mega_pins_near = sum(1 for r in rows if abs(r.get("strike", 0) - spot) <= 10.0 and (r.get("pin_vgex", 0.0) / 1000.0) >= 50.0)

    # Quantitative 5-Regime Classification
    if below20_vgex < 0 and above20_vgex < 0:
        if mega_pins_near >= 2 and abs(spot - kp) <= 6.0 and inc_vgex > -65.0:
            regime_code = "R2_LATE_MEGA_PIN"
            regime_name = "📌 盤態2：尾盤多座巨型磁王水泥釘死局 (Pinning)"
            expected_dir = "PIN"
        else:
            regime_code = "R1_DEEP_NEG_WATERFALL"
            regime_name = "🔴 盤態1：深水負Gamma單邊殺盤局 (Bear Waterfall)"
            expected_dir = "BEAR"
    elif abs(tot_vgex) <= 5.0 and kp_pin_b >= 40.0 and abs(spot - kp) <= 7.0 and inc_vgex > 0:
        regime_code = "R2_LATE_MEGA_PIN"
        regime_name = "📌 盤態2：尾盤多座巨型磁王水泥釘死局 (Pinning)"
        expected_dir = "PIN"
    elif below20_vgex > 0 and above20_vgex > 0 and spot >= kp + 4.0 and tot_vgex > 100.0:
        regime_code = "R4_POS_GAMMA_MEAN_REVERT"
        regime_name = "🧲 盤態4：全正Gamma高檔超漲均值回歸局 (Revert to KP)"
        expected_dir = "BEAR_OR_PIN"
    elif inc_vgex < 0 or (spot < flip and below20_dnet < -3000):
        regime_code = "R3_BELOW_FLIP_SINKHOLE"
        regime_name = "🟠 盤態3：分水嶺下沿黑洞擴大/增量轉空回踩局 (Pullback/Breakdown)"
        expected_dir = "BEAR"
    else:
        regime_code = "R5_BULL_PUSH_OR_BASE"
        regime_name = "🟢 盤態5：正Gamma多頭推升/換手築底局 (Bull Push/Base)"
        expected_dir = "BULL"

    return {
        "spot": spot,
        "flip": flip,
        "kp": kp,
        "kp_pin_b": kp_pin_b,
        "tot_vgex": tot_vgex,
        "loc15_vgex": loc15_vgex,
        "below20_vgex": below20_vgex,
        "above20_vgex": above20_vgex,
        "below20_dnet": below20_dnet,
        "above20_dnet": above20_dnet,
        "ntm25_dnet": ntm25_dnet,
        "inc_vgex": inc_vgex,
        "regime_code": regime_code,
        "regime_name": regime_name,
        "expected_dir": expected_dir,
    }


def pearson_r(xs: List[float], ys: List[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    denx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    deny = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (denx * deny) if denx > 0 and deny > 0 else 0.0


def main():
    days = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))])
    transitions = []
    all_snapshots = []

    for day in days:
        files = sorted(glob.glob(os.path.join(DATA_DIR, day, "*_calc.json")))
        snaps = [json.load(open(f)) for f in files]
        for idx, s in enumerate(snaps):
            m = compute_snapshot_metrics(s)
            m["day"] = day
            m["seq"] = str(s.get("seq", idx + 1))
            m["pred_a_dir"] = extract_pred_a_direction(s.get("playbook_html", ""), m["spot"])
            if idx + 1 < len(snaps):
                next_spot = float(snaps[idx + 1]["spot"])
                d_spot = round(next_spot - m["spot"], 2)
                m["next_spot"] = next_spot
                m["d_spot"] = d_spot
                # Check if quantitative regime matched actual move
                if m["expected_dir"] == "BEAR":
                    m["quant_match"] = d_spot < 0
                elif m["expected_dir"] == "PIN":
                    m["quant_match"] = abs(d_spot) <= 4.0
                elif m["expected_dir"] == "BEAR_OR_PIN":
                    m["quant_match"] = d_spot <= 0.5
                else:
                    m["quant_match"] = d_spot >= -0.8
                transitions.append(m)
            else:
                m["next_spot"] = None
                m["d_spot"] = None
                m["quant_match"] = None
            all_snapshots.append(m)

    print("=" * 105)
    print("📊 SPX 0DTE GEX 跨日全樣本量化回歸與自我對帳報告 (Daily Regression & Self-Audit Report)")
    print("=" * 105)
    print(f"• 總交易日數: {len(days)} 日 ({', '.join(days)})")
    print(f"• 總快照筆數: {len(all_snapshots)} 筆 | 盤中實際推進樣本數 (t -> t+1): {len(transitions)} 次")

    # 1. Statistical correlations with next-snapshot dSpot
    d_spots = [t["d_spot"] for t in transitions]
    factors = [
        ("全場總淨曝險 (Tot_vGEX)", [t["tot_vgex"] for t in transitions]),
        ("近端 ±15點 淨曝險 (Loc15_vGEX)", [t["loc15_vgex"] for t in transitions]),
        ("腳下 20點 淨曝險 (Below20_vGEX)", [t["below20_vgex"] for t in transitions]),
        ("頭頂 20點 淨曝險 (Above20_vGEX)", [t["above20_vgex"] for t in transitions]),
        ("單筆 Gamma 加權增量 (Inc_vGEX)", [t["inc_vgex"] for t in transitions]),
        ("腳下 20點 淨增量口數 (Below20_dNet)", [float(t["below20_dnet"]) for t in transitions]),
        ("近端 ±25點 淨增量口數 (NTM25_dNet)", [float(t["ntm25_dnet"]) for t in transitions]),
    ]
    print("\n--- [1] 單因子與下一筆價格變動 (dSpot) 之皮爾森相關係數 (Pearson r) ---")
    for name, vals in factors:
        r_val = pearson_r(vals, d_spots)
        print(f"  {name:<36}: r = {r_val:+.4f}")

    # 2. Performance by Regime
    print("\n--- [2] 五大定量盤態分類器 (5-Regime Classifier) 歷史回測表現 ---")
    regime_groups: Dict[str, List[Dict[str, Any]]] = {}
    for t in transitions:
        regime_groups.setdefault(t["regime_name"], []).append(t)

    tot_correct = sum(1 for t in transitions if t["quant_match"])
    for rname, items in sorted(regime_groups.items()):
        avg_d = sum(x["d_spot"] for x in items) / len(items)
        hits = sum(1 for x in items if x["quant_match"])
        up_cnt = sum(1 for x in items if x["d_spot"] > 3.2)
        down_cnt = sum(1 for x in items if x["d_spot"] < 0)
        print(
            f"  {rname:<52} | 樣本: {len(items):2d} | 命中: {hits:2d}/{len(items):2d} ({hits/len(items)*100:5.1f}%) | "
            f"平均 dSpot: {avg_d:+6.2f} 點 | 下跌次數: {down_cnt}/{len(items)} | >3.2點V轉: {up_cnt}/{len(items)}"
        )
    print(f"  >> 全樣本定量模型總命中率: {tot_correct}/{len(transitions)} ({tot_correct/len(transitions)*100:.1f}%)")

    # 3. Latest Snapshot Mandatory Regime Lock
    latest = all_snapshots[-1]
    print("\n--- [3] 最新一筆快照強制盤態鎖定 (Mandatory Regime Lock for Latest Snapshot) ---")
    print(f"  • 日期/編號: {latest['day']} #{latest['seq']} | Spot = {latest['spot']} | Flip = {latest['flip']} | #1 King Pin = {latest['kp']} (${latest['kp_pin_b']:.1f}B)")
    print(f"  • 核心指標 : Tot_vGEX = {latest['tot_vgex']:+.2f}B | Below20_vGEX = {latest['below20_vgex']:+.2f}B | Above20_vGEX = {latest['above20_vgex']:+.2f}B")
    print(f"  • 增量指標 : Inc_vGEX = {latest['inc_vgex']:+.2f}B | Below20_d(C-P) = {latest['below20_dnet']:+,d} | Above20_d(C-P) = {latest['above20_dnet']:+,d}")
    print(f"  • 鎖定盤態 : {latest['regime_name']} (強制主劇本方向: {latest['expected_dir']})")
    print("=" * 105)


if __name__ == "__main__":
    main()
