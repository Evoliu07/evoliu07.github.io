"""
实时新闻抓取 → data/dash/news.json

来源（均已实测可达，国内财经媒体公开频道）：
  1 新浪财经 7x24      zhibo.sina.com.cn
  2 东方财富 快讯      np-listapi.eastmoney.com
  3 华尔街见闻 国际     api-one-wscn.awtmt.com

只取「标题 + 时间 + 来源 + 原文链接」，不抓取全文，避免侵权。
分两栏：finance（证券财经）/ overseas（出海·国际）。
任一源失败即跳过，不影响其它源；全部失败则保留上次结果。

用法： python src/market_news.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, http_get, iso, log_line, now_cst        # noqa: E402

OUT = ROOT / "data" / "dash" / "news.json"
UA = {"User-Agent": ("Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
                     "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148")}

# 证券财经（市场 / 机构 / 宏观 / 监管）
FINANCE_KW = [
    "A股", "港股", "美股", "沪指", "深成", "创业板", "科创板", "北交所", "指数",
    "收盘", "开盘", "涨停", "跌停", "涨超", "跌超", "大涨", "大跌", "两市",
    "央行", "降息", "加息", "降准", "利率", "国债", "债券", "收益率", "资金面",
    "基金", "券商", "银行", "保险", "信托", "理财", "资管", "两融", "北向", "主力",
    "社融", "PMI", "GDP", "CPI", "PPI", "财报", "业绩", "营收", "净利",
    "IPO", "上市", "退市", "回购", "分红", "增持", "减持", "定增", "并购",
    "证监会", "交易所", "金融监管", "货币政策", "财政政策", "公开市场",
    "期货", "大宗", "黄金", "原油", "大宗商品", "楼市", "地产",
]

# 出海 / 跨境（不做「国际/全球」这类泛词命中，否则会混进军事政治新闻）
OVERSEAS_KW = [
    "出海", "跨境", "外贸", "关税", "出口", "进口", "海外市场", "海外业务", "海外营收", "全球化",
    "人民币", "美元", "汇率", "中间价", "美联储", "欧央行", "欧洲", "东南亚", "东盟", "中东",
    "比亚迪", "新能源车", "电动车", "车企", "供应链", "航运", "集装箱", "跨境电商",
    "WTO", "反倾销", "自贸", "RCEP", "一带一路", "境外", "离岸", "结汇", "外汇",
]

# 明显与两栏都无关的噪音（军事冲突 / 社会 / 娱乐 / 体育），直接丢弃
NOISE_KW = [
    "伊朗", "以色列", "胡塞", "也门", "俄乌", "乌克兰", "俄罗斯", "北约", "导弹",
    "击落", "空袭", "军事", "部队", "战争", "士兵", "坦克", "无人机袭击",
    "地震", "台风", "暴雨", "事故", "车祸", "火灾", "逮捕", "判刑", "涉嫌",
    "演唱会", "电影", "综艺", "球星", "世界杯", "奥运会", "比赛", "夺冠",
    "会见", "外长", "外交部", "大使", "会谈", "国事访问", "联合声明", "谴责", "抗议",
]


def _j(url: str, referer: str, timeout: int = 20):
    st, body, err = http_get(url, headers={**UA, "Referer": referer}, timeout=timeout)
    if st != 200 or not body:
        return None
    try:
        return json.loads(body.decode("utf-8", "ignore"))
    except Exception:                                            # noqa: BLE001
        return None


def _tidy(s: str) -> str:
    s = re.sub(r"<[^>]+>", "", s or "")
    s = s.replace("\u200b", "").replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _is_overseas(text: str) -> bool:
    return any(k in text for k in OVERSEAS_KW)


def _is_finance(text: str) -> bool:
    return any(k in text for k in FINANCE_KW)


def _is_noise(text: str) -> bool:
    return any(k in text for k in NOISE_KW)


# ───────────────────────── 新浪财经 7x24
def fetch_sina(n=60) -> list[dict]:
    d = _j("https://zhibo.sina.com.cn/api/zhibo/feed?page=1&page_size=%d&zhibo_id=152"
           "&tag_id=0&dire=f&dpc=1" % n, "https://finance.sina.com.cn/7x24/")
    if not d:
        return []
    out = []
    for it in (d.get("result", {}).get("data", {}).get("feed", {}).get("list") or []):
        txt = _tidy(it.get("rich_text") or "")
        if not txt:
            continue
        out.append({"title": txt[:160], "time": (it.get("create_time") or "")[:16],
                    "source": "新浪财经 7x24", "url": "https://finance.sina.com.cn/7x24/"})
    return out


# ───────────────────────── 东方财富快讯
def fetch_em(n=60) -> list[dict]:
    d = _j("https://np-listapi.eastmoney.com/comm/web/getFastNewsList"
           "?client=web&biz=web_724&fastColumn=102&sortEnd=&pageSize=%d&req_trace=1" % n,
           "https://kuaixun.eastmoney.com/")
    if not d:
        return []
    out = []
    for it in (d.get("data", {}) or {}).get("fastNewsList", []) or []:
        title = _tidy(it.get("title") or it.get("summary") or "")
        if not title:
            continue
        out.append({"title": title[:160], "time": (it.get("showTime") or "")[:16],
                    "source": "东方财富 快讯", "url": "https://kuaixun.eastmoney.com/"})
    return out


# ───────────────────────── 华尔街见闻 国际频道
def fetch_wscn(n=40) -> list[dict]:
    d = _j("https://api-one-wscn.awtmt.com/apiv1/content/lives?channel=global-channel"
           "&client=pc&limit=%d" % n, "https://wallstreetcn.com/live/global")
    if not d:
        return []
    out = []
    for it in (d.get("data", {}) or {}).get("items", []) or []:
        txt = _tidy(it.get("content_text") or it.get("content") or it.get("title") or "")
        if not txt:
            continue
        ts = it.get("display_time") or it.get("create_time") or 0
        try:
            tm = datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M")
        except Exception:                                        # noqa: BLE001
            tm = ""
        out.append({"title": txt[:160], "time": tm,
                    "source": "华尔街见闻 国际", "url": "https://wallstreetcn.com/live/global"})
    return out


def _grams(t: str) -> set:
    t = re.sub(r"[^一-龥A-Za-z0-9]", "", t)
    return {t[i:i + 2] for i in range(len(t) - 1)} or {t}


def _dedup(items: list[dict], limit: int) -> list[dict]:
    """先精确去重，再按字符二元组重合度去掉同一事件的不同措辞版本。"""
    seen, out = set(), []
    for it in sorted(items, key=lambda x: x.get("time") or "", reverse=True):
        key = re.sub(r"[^一-龥A-Za-z0-9]", "", it["title"])[:18]
        if len(key) < 8 or key in seen:
            continue
        g = _grams(it["title"])
        dup = False
        for kept in out:
            kg = _grams(kept["title"])
            inter = len(g & kg)
            union = len(g | kg) or 1
            if inter / union > 0.45:          # 同一件事的不同写法
                dup = True
                break
        if dup:
            continue
        seen.add(key)
        out.append(it)
        if len(out) >= limit:
            break
    return out


def main() -> None:
    sina, em, wscn = fetch_sina(), fetch_em(), fetch_wscn()
    log_line(f"新闻抓取：新浪 {len(sina)} 条 / 东财 {len(em)} 条 / 见闻 {len(wscn)} 条")
    if not (sina or em or wscn):
        log_line("[STALE] 本次未取到任何新闻，保留上次结果")
        return

    raw = sina + em + wscn
    # 先按标题去重，再去噪，最后分栏（出海优先，避免同一条两边都出现）
    seen = set()
    pool = []
    for it in sorted(raw, key=lambda x: x.get("time") or "", reverse=True):
        key = re.sub(r"[^一-龥A-Za-z0-9]", "", it["title"])[:18]
        if len(key) < 8 or key in seen:
            continue
        seen.add(key)
        pool.append(it)

    overseas, finance, rest = [], [], []
    for it in pool:
        t = it["title"]
        if _is_noise(t):
            continue
        if _is_overseas(t):
            overseas.append(it)
        elif _is_finance(t):
            finance.append(it)
        else:
            rest.append(it)

    payload = {
        "generated_at": iso(),
        "as_of": now_cst().strftime("%Y-%m-%d %H:%M"),
        "finance": _dedup(finance, 24),
        "overseas": _dedup(overseas, 24),
        "sources": ["新浪财经 7x24", "东方财富 快讯", "华尔街见闻 国际"],
    }
    log_line(f"分栏结果：证券财经 {len(payload['finance'])} 条 / 出海·国际 {len(payload['overseas'])} 条"
             f"（其余 {len(rest)} 条与两栏无关，已剔除）")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    log_line(f"新闻已写入 {OUT.relative_to(ROOT)}：财经 {len(payload['finance'])} 条 / "
             f"出海 {len(payload['overseas'])} 条")


if __name__ == "__main__":
    main()
