"""
实时新闻采集 → data/dash/news.json

来源：新浪财经 7×24 全球实时财经快讯（zhibo_id=152），官方公开 JSON 接口，免密钥。
分流：按关键词分为「证券财经大事」与「出海大事」两栏。
降级：任一页抓取失败即停止翻页，保留已取到的部分；某栏为空则该栏不渲染。

用法：
  python src/news_fetch.py            # 默认翻 20 页（约 20 小时）
  python src/news_fetch.py --pages 24
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, http_get, iso, log_line, now_cst      # noqa: E402

BASE = ("https://zhibo.sina.com.cn/api/zhibo/feed"
        "?page={p}&page_size=100&zhibo_id=152&tag_id=0&dire=f&dpc=1")
HDRS = {"User-Agent": "Mozilla/5.0",
        "Referer": "https://finance.sina.com.cn/7x24/"}
OUT = ROOT / "data" / "dash" / "news.json"

# 出海 / 跨境 / 外贸：只用「强信号词」，避免把普通国际财经（如"德国经济部长"）误判为出海
KW_SEA = [
    "出海", "品牌出海", "供应链出海", "走出去", "全球化", "国际业务",
    "跨境", "跨境电商", "外贸", "进出口", "出口", "进口", "关税", "加征关税",
    "贸易摩擦", "反倾销", "反补贴", "贸易壁垒", "RCEP", "广交会", "义乌",
    "中欧班列", "海外仓", "海运", "集装箱运价", "海外市场", "海外业务",
    "海外营收", "海外建厂", "海外门店", "海外投资",
    "SHEIN", "Temu", "TikTok Shop", "Shopee", "Lazada", "AliExpress", "亚马逊",
]
# 排除词：命中即不算出海（多为海外企业的本地 HR / 零售新闻，与出海无关）
KW_SEA_NOT = [
    "员工福利", "起薪", "每小时", "工会", "全食超市", "杂货", "终身银行福利",
]
# 证券 / 财经 / 宏观
KW_FIN = [
    "央行", "货币政策", "利率", "国债", "债券", "收益率", "资金面", "A股", "港股",
    "美股", "上证", "深证", "创业板", "科创板", "IPO", "再融资", "基金", "公募",
    "私募", "券商", "两融", "融资余额", "证监会", "金融监管总局", "财政", "税收",
    "监管", "LPR", "MLF", "降准", "逆回购", "社融", "PMI", "CPI", "PPI", "GDP",
    "经济数据", "上市公司", "财报", "业绩", "分红", "回购", "增持", "减持",
    "涨停", "跌停", "板块", "银行", "保险", "证券", "地产", "大宗", "黄金",
    "原油", "期货", "指数",
]


def clean(t: str) -> str:
    t = (t or "").replace("\u3000", " ").strip()
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def fetch_page(p: int):
    st, body, err = http_get(BASE.format(p=p), headers=HDRS, timeout=30)
    if st != 200 or not body:
        return None
    try:
        d = json.loads(body.decode("utf-8", "ignore"))
        return d["result"]["data"]["feed"]["list"]
    except Exception:                                    # noqa: BLE001
        return None


def classify(text: str):
    sea = [k for k in KW_SEA if k in text]
    if any(k in text for k in KW_SEA_NOT):
        sea = []          # 命中排除词即不算出海
    fin = [k for k in KW_FIN if k in text]
    return sea, fin


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=20)
    args = ap.parse_args()

    seen, items = set(), []
    for p in range(1, args.pages + 1):
        lst = fetch_page(p)
        if lst is None:
            log_line(f"[MISS] 新闻第 {p} 页未取到，停止翻页")
            break
        for it in lst:
            iid = it.get("id")
            if not iid or iid in seen:
                continue
            txt = clean(it.get("rich_text"))
            if len(txt) < 8:
                continue
            seen.add(iid)
            sea, fin = classify(txt)
            items.append({
                "id": iid,
                "time": it.get("create_time", ""),
                "text": txt,
                "url": it.get("docurl") or "",
                "sea": sea[:3], "fin": fin[:3],
            })

    if not items:
        log_line("[STALE] 本次未取到新闻，保留上次结果")
        return

    items.sort(key=lambda x: x["time"], reverse=True)
    finance = sorted([x for x in items if x["fin"]],
                     key=lambda x: (-len(x["fin"]), x["time"]), reverse=False)[:15]
    overseas = sorted([x for x in items if x["sea"]],
                      key=lambda x: (-len(x["sea"]), x["time"]))[:15]
    finance.sort(key=lambda x: x["time"], reverse=True)

    span = (items[-1]["time"], items[0]["time"]) if items else ("", "")
    payload = {
        "generated_at": iso(),
        "as_of": now_cst().strftime("%Y-%m-%d %H:%M"),
        "span": f"{span[0]} ~ {span[1]}",
        "total": len(items),
        "finance": finance,
        "overseas": overseas,
        "source": "新浪财经 7×24 全球实时财经快讯（公开接口）",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    log_line(f"新闻 {len(items)} 条 → {OUT.relative_to(ROOT)}")
    log_line(f"   证券财经 {len(finance)} 条 / 出海 {len(overseas)} 条 ｜ 覆盖 {payload['span']}")


if __name__ == "__main__":
    main()
