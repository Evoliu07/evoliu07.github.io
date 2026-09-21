"""
从徕芬项目原有 CSV 聚合出看板数据 → data/dash/laifen_demo.json

说明：这批 CSV 由项目脚本生成（每行 source=SYNTHETIC），本文件只做**真实聚合**，
不新增、不修改任何数值。聚合结果用于出海看板「徕芬（德国）」五个模块。

用法： python src/build_laifen.py
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, log_line, iso                                # noqa: E402

SRC = Path("/Users/evo/WorkBuddy/2026-09-11-23-22-58/_laifen/evoliu07-site/"
           "laifen-gtm/_src/data")
OUT = ROOT / "data" / "dash" / "laifen_demo.json"


def rd(name: str) -> list[dict]:
    with open(SRC / name, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def f(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def i(v, d=0):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return d


def build() -> dict:
    if not SRC.exists():
        log_line("[FAIL] 找不到徕芬数据源目录")
        return {}

    reviews, kol = rd("reviews_scored.csv"), rd("kol_scored.csv")
    price, funnel = rd("price_daily.csv"), rd("sample_funnel.csv")
    loc, comp = rd("localization_variants.csv"), rd("complaint_matrix.csv")

    # ---- 1 评论洞察：品牌 × 月份 情感均值
    sent = defaultdict(lambda: defaultdict(list))
    for r in reviews:
        if r.get("date") and r.get("sentiment"):
            sent[r["brand"]][r["date"][:7]].append(f(r["sentiment"]))
    brands = sorted(sent.keys())
    months = sorted({m for b in sent.values() for m in b})
    sentiment_trend = {
        "months": months,
        "brands": [{"brand": b,
                    "values": [round(sum(sent[b].get(m, [0])) / len(sent[b].get(m, [0])), 4)
                               if sent[b].get(m) else None for m in months]}
                   for b in brands]}

    # 差评主题分布（Treemap）与机会指数排行
    topics = [{"brand": c["brand"], "topic": c["complaint_topic"],
               "mentions": i(c["mentions"]),
               "mean_sentiment": round(f(c["mean_sentiment"]), 3),
               "opportunity": round(f(c["opportunity_index"]), 2)}
              for c in comp]
    topics.sort(key=lambda x: -x["mentions"])
    opp = sorted(topics, key=lambda x: -x["opportunity"])

    # ---- 2 达人分层
    tiers = defaultdict(int)
    for k in kol:
        tiers[k.get("tier", "")] += 1
    tier_order = [t for t in ["S", "A", "B", "C", "D"] if t in tiers]
    tier_dist = [{"tier": t, "count": tiers[t]} for t in tier_order] or \
                [{"tier": t, "count": c} for t, c in tiers.items()]
    kol_bubble = [{"name": k["creator_name"], "platform": k["platform"],
                   "subscribers": i(k["subscribers"]),
                   "engagement": round(f(k["engagement_rate"]) * 100, 2),
                   "score": round(f(k["score"]), 1), "tier": k.get("tier", "")}
                  for k in kol]
    shortlist = [{"name": k["creator_name"], "platform": k["platform"],
                  "tier": k.get("tier", ""), "subscribers": i(k["subscribers"]),
                  "score": round(f(k["score"]), 1),
                  "est_fee_eur": round(f(k["est_fee_eur"]), 0),
                  "est_cac_eur": round(f(k["est_cac_eur"]), 0)}
                 for k in kol if k.get("tier") in ("S", "A")]
    shortlist.sort(key=lambda x: -x["score"])

    # ---- 3 竞品价格
    by_date = defaultdict(dict)
    for p in price:
        by_date[p["date"]][p["brand"]] = f(p["price_eur"])
    pdates = sorted(by_date)
    pbrands = sorted({p["brand"] for p in price})
    price_curves = {"dates": pdates,
                    "brands": [{"brand": b,
                                "values": [by_date[d].get(b) for d in pdates]}
                               for b in pbrands]}
    latest_d = pdates[-1] if pdates else None
    comp_tbl = []
    for p in price:
        if p["date"] != latest_d:
            continue
        comp_tbl.append({"brand": p["brand"], "sku": p["sku"],
                         "price_eur": round(f(p["price_eur"]), 2),
                         "list_eur": round(f(p["list_price_eur"]), 2),
                         "coupon_pct": round(f(p["coupon_pct"]), 1),
                         "bsr": i(p["bsr_rank"]),
                         "rating": round(f(p["rating"]), 2)})
    comp_tbl.sort(key=lambda x: x["price_eur"])

    # ---- 4 渠道漏斗
    ch = defaultdict(lambda: defaultdict(float))
    for r in funnel:
        c = r["channel"]
        for k in ("impressions", "clicks", "detail_views", "add_to_cart",
                  "orders", "repeat_orders", "ad_spend_eur"):
            ch[c][k] += f(r.get(k))
    fun = []
    for c, v in ch.items():
        orders = v["orders"] or 1
        fun.append({"channel": c, "impressions": i(v["impressions"]),
                    "clicks": i(v["clicks"]), "detail_views": i(v["detail_views"]),
                    "add_to_cart": i(v["add_to_cart"]), "orders": i(v["orders"]),
                    "repeat_orders": i(v["repeat_orders"]),
                    "cac_eur": round(v["ad_spend_eur"] / orders, 2),
                    "repeat_rate": round(v["repeat_orders"] / orders * 100, 1)})
    fun.sort(key=lambda x: -x["orders"])
    fmonths = sorted({r["month"] for r in funnel})
    orders_m = defaultdict(dict)
    for r in funnel:
        orders_m[r["channel"]][r["month"]] = orders_m[r["channel"]].get(r["month"], 0) \
            + i(r["orders"])
    orders_by_month = {"months": fmonths,
                       "channels": [{"channel": c,
                                     "values": [orders_m[c].get(m, 0) for m in fmonths]}
                                    for c in sorted(orders_m)]}

    # ---- 5 本地化文案
    loc_rows = [{"version": r["version"], "compliance": f(r["compliance"]),
                 "info_density": f(r["info_density"]), "cultural_fit": f(r["cultural_fit"]),
                 "verifiability": f(r["verifiability"]),
                 "conversion_expectation": f(r["conversion_expectation"]),
                 "total": f(r["total"]), "headline": r.get("sample_headline_de", ""),
                 "verdict": r.get("verdict", "")} for r in loc]

    payload = {
        "generated_at": iso(),
        "reviews_total": len(reviews),
        "kol_total": len(kol),
        "price_rows": len(price),
        "sentiment_trend": sentiment_trend,
        "topics": topics,
        "opportunity": opp,
        "tier_dist": tier_dist,
        "kol_bubble": kol_bubble,
        "shortlist": shortlist,
        "price_curves": price_curves,
        "price_latest_date": latest_d,
        "comp_table": comp_tbl,
        "funnel": fun,
        "orders_by_month": orders_by_month,
        "localization": loc_rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    log_line(f"徕芬模块数据 → {OUT.relative_to(ROOT)}")
    log_line(f"   评论 {len(reviews)} 条 / 达人 {len(kol)} 位 / 价格 {len(price)} 行 / "
             f"主题 {len(topics)} / 渠道 {len(fun)} / 文案 {len(loc_rows)} 版")
    return payload


if __name__ == "__main__":
    build()
