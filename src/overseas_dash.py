"""
「出海情报」看板数据层 —— 从 SMMT 英国注册数据生成网站用 JSON。

输入：data/processed/gtm_datasets.json（由 src/gtm_fetch.py 产生）
输出：evo-site/dash/data/overseas.json

用法： python src/overseas_dash.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, iso, log_line                            # noqa: E402

SRC = ROOT / "data" / "processed" / "gtm_datasets.json"
OUT = ROOT / "data" / "dash" / "overseas.json"

# 在英国注册数据中出现的中国 / 新兴品牌（按 SMMT 表中的拼写）
CN_BRANDS = {"Byd", "Mg", "Chery", "Jaecoo", "Omoda", "Geely", "Changan",
             "Gwm", "Nio", "Xpeng", "Aion", "Leapmotor", "Skyworth", "Voyah",
             "Zeekr", "Jae", "Hongqi", "Lynk & Co", "Baidu"}


def main() -> None:
    if not SRC.exists():
        log_line(f"[FAIL] 找不到 {SRC}，请先运行 src/gtm_fetch.py")
        return
    G = json.loads(SRC.read_text(encoding="utf-8"))
    r = G.get("smmt_raw") or {}
    pm = (r.get("powertrain") or {}).get("month") or {}
    py = (r.get("powertrain") or {}).get("ytd") or {}
    cm = (r.get("channel") or {}).get("month") or {}
    cy = (r.get("channel") or {}).get("ytd") or {}
    bm = (r.get("brand") or {}).get("month") or {}
    by = (r.get("brand") or {}).get("ytd") or {}

    def g(d, k, f, dflt=None):
        return (d.get(k) or {}).get(f, dflt)

    cn_brands = [{"brand": name, "units": v["cur"], "share": v.get("share_cur"),
                  "yoy": v.get("pct_change"), "ytd": g(by, name, "cur")}
                 for name, v in sorted(bm.items(), key=lambda x: -(x[1].get("cur") or 0))
                 if name in CN_BRANDS and v.get("cur")]
    top_brands = [{"brand": k, "units": v["cur"], "share": v.get("share_cur"),
                   "yoy": v.get("pct_change")}
                  for k, v in sorted(bm.items(), key=lambda x: -(x[1].get("cur") or 0))[:15]]

    payload = {
        "meta": {
            "title": "出海情报 · 英国电动车市场",
            "data_date": G.get("data_version"),
            "generated_at": iso(),
            "scope": "英国（UK）乘用车注册 · 来源 SMMT 官方公开页",
            "subject": "BYD DOLPHIN SURF（紧凑型纯电城市车）",
            "note": "注册量 ≠ 销量 ≠ 交付量。品牌级 ≠ 车型级。"
                    "SMMT 免费公开页仅提供车型 Top10。单一权威来源，尚未独立交叉验证。",
        },
        "market": {
            "total_month": g(pm, "TOTAL", "cur"), "total_ytd": g(py, "TOTAL", "cur"),
            "bev_month": g(pm, "BEV", "cur"), "bev_share": g(pm, "BEV", "share_cur"),
            "bev_share_prev": g(pm, "BEV", "share_prev"), "bev_yoy": g(pm, "BEV", "pct_change"),
            "bev_ytd": g(py, "BEV", "cur"), "phev_share": g(pm, "PHEV", "share_cur"),
            "petrol_share": g(pm, "PETROL", "share_cur"),
        },
        "powertrain": [{"key": k, "units": v["cur"], "share": v.get("share_cur"),
                        "share_prev": v.get("share_prev"), "yoy": v.get("pct_change")}
                       for k, v in pm.items() if k != "TOTAL"],
        "powertrainYtd": [{"key": k, "units": v["cur"], "share": v.get("share_cur"),
                           "share_prev": v.get("share_prev"), "yoy": v.get("pct_change")}
                          for k, v in py.items() if k != "TOTAL"],
        "channel": [{"key": k, "units": v["cur"], "share": v.get("share_cur"),
                     "share_prev": v.get("share_prev"), "yoy": v.get("pct_change")}
                    for k, v in cm.items() if k != "TOTAL"],
        "channelYtd": [{"key": k, "units": v["cur"], "share": v.get("share_cur"),
                        "share_prev": v.get("share_prev"), "yoy": v.get("pct_change")}
                       for k, v in cy.items() if k != "TOTAL"],
        "cn_brands": cn_brands,
        "top_brands": top_brands,
        "bev_top10": (r.get("top_bev_models") or {}).get("month_bev") or [],
        "all_top10": (r.get("top_models") or {}).get("ytd_all") or [],
        "competitors": [{"model": k, "ok": v.get("ok"), "url": v.get("url"),
                         "range_miles": (v.get("facts") or {}).get("range_miles") or [],
                         "battery_kwh": (v.get("facts") or {}).get("battery_kwh") or []}
                        for k, v in (G.get("model_facts") or {}).items()],
        "not_retrieved": G.get("not_retrieved") or [],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    log_line(f"出海情报数据已写入（数据日期 {payload['meta']['data_date']}，"
             f"中国品牌 {len(cn_brands)} 个）")


if __name__ == "__main__":
    main()
