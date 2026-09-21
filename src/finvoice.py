"""
「金融之声」看板数据层 —— 面向金融市场机构销售（公募 / 私募 / 理财子）。

输出：../evo-site/dash/data/dashboard.json
设计原则：
  1. 只放**能核实的公开事实**，不编造解读；
  2. 结构化：今日读数 / 变化 / 曲线 / 资金面 / 公开市场 / 来源；
  3. 面向机构销售：每条事实都标明「对谁有用、怎么用」，而不是堆指标。

用法： python src/finvoice.py
"""
from __future__ import annotations

import json
import sys
import urllib.parse
from datetime import datetime, timedelta

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from common import (ROOT, SOURCES, http_get, iso, load_state, log_line,  # noqa: E402
                    now_cst, save_json, save_state, today_cst)

OUT_DIR = ROOT / "data" / "dash"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TENORS = [("0.5", "6M"), ("1.0", "1Y"), ("2.0", "2Y"), ("3.0", "3Y"),
          ("5.0", "5Y"), ("7.0", "7Y"), ("10.0", "10Y"), ("30.0", "30Y")]
KEY = ["1.0", "2.0", "5.0", "10.0", "30.0"]


# ------------------------------------------------------------------ 取数
def curve_latest() -> dict:
    """中债国债收益率曲线（最近工作日）。"""
    url = "https://yield.chinabond.com.cn/cbweb-czb-web/czb/czbChartSearch"
    st, body, err = http_get(url, data=b"",
                             headers={"Referer": "https://yield.chinabond.com.cn/cbweb-czb-web/czb/moreInfo?locale=cn_ZH&qxId=ycqx",
                                      "X-Requested-With": "XMLHttpRequest"})
    if st != 200 or not body:
        return {}
    try:
        arr = json.loads(body.decode("utf-8", "ignore"))
    except Exception:                                 # noqa: BLE001
        return {}
    for it in arr:
        if "国债收益率曲线" in (it.get("ycDefName") or ""):
            return {"date": it.get("worktime"),
                    "series": {str(round(float(k), 4)): float(v)
                               for k, v in it["seriesData"] if float(v) > 0}}
    return {}


def curve_on(date: str) -> dict:
    """指定工作日的国债曲线。qxmc=1 才是国债（2 是地方政府债）。"""
    q = urllib.parse.urlencode({"zblx": "xy", "workTime": date, "qxmc": "1"})
    st, body, err = http_get(f"https://yield.chinabond.com.cn/cbweb-czb-web/czb/czbQueryXy?{q}",
                             headers={"Referer": "https://yield.chinabond.com.cn/"})
    if st != 200 or not body:
        return {}
    try:
        arr = json.loads(body.decode("utf-8", "ignore"))
    except Exception:                                 # noqa: BLE001
        return {}
    for it in arr:
        if "国债" in (it.get("ycDefName") or "") and "地方" not in (it.get("ycDefName") or ""):
            s = {str(round(float(k), 4)): float(v) for k, v in it["seriesData"] if float(v) > 0}
            if s:
                return {"date": it.get("worktime") or date, "series": s}
    return {}


def money_rates() -> dict:
    """DR001 / DR007 / FR007 / Shibor 1W —— 含近 40 日序列。"""
    today = today_cst()
    start = (now_cst() - timedelta(days=60)).strftime("%Y-%m-%d")
    out: dict[str, dict[str, float]] = {}

    q = urllib.parse.urlencode({"lang": "CN", "startDate": start, "endDate": today,
                                "pageNum": 1, "pageSize": 5})
    st, body, _ = http_get(
        f"https://www.chinamoney.com.cn/ags/ms/cm-u-bk-currency/FrrHis?{q}",
        headers={"Referer": "https://www.chinamoney.com.cn/chinese/bkfrr/"})
    if st == 200 and body:
        try:
            for r in json.loads(body.decode("utf-8", "ignore")).get("records") or []:
                d = r.get("lfiProducDate")
                m = r.get("frValueMap") or {}
                if not d or not isinstance(m, dict):
                    continue
                for code in ("FDR001", "FDR007", "FR007"):
                    try:
                        v = float(m.get(code))
                    except (TypeError, ValueError):
                        continue
                    if v > 0:
                        out.setdefault(code, {})[d] = v
        except Exception:                             # noqa: BLE001
            pass

    for ps in (5, 30):
        q = urllib.parse.urlencode({"lang": "CN", "startDate": start, "endDate": today,
                                    "pageNum": 1, "pageSize": ps})
        st, body, _ = http_get(
            f"https://www.chinamoney.com.cn/ags/ms/cm-u-bk-shibor/ShiborHis?{q}",
            headers={"Referer": "https://www.chinamoney.com.cn/chinese/bkshibor/"})
        if st == 200 and body:
            try:
                for r in json.loads(body.decode("utf-8", "ignore")).get("records") or []:
                    d = r.get("showDateCN")
                    try:
                        v = float(r.get("1W"))
                    except (TypeError, ValueError):
                        continue
                    if d and v > 0:
                        out.setdefault("SHIBOR_1W", {})[d] = v
            except Exception:                         # noqa: BLE001
                pass
        if out.get("SHIBOR_1W"):
            break
    return out


def omo_latest() -> list[dict]:
    st, body, _ = http_get(
        "https://www.pbc.gov.cn/zhengcehuobisi/125207/125213/125431/125475/index.html",
        headers={"Referer": "https://www.pbc.gov.cn/"})
    if st != 200 or not body:
        return []
    import re
    html = body.decode("utf-8", "ignore")
    items, seen = [], set()
    for m in re.finditer(r'href="([^"]+)"[^>]*>\s*([^<]{4,90}?)\s*</a>', html):
        href, text = m.group(1), " ".join(m.group(2).split())
        if "公开市场" not in text and "业务交易公告" not in text:
            continue
        if href.startswith("./"):
            href = href[2:]
        full = ("https://www.pbc.gov.cn" + href) if href.startswith("/") else \
            ("https://www.pbc.gov.cn/zhengcehuobisi/125207/125213/125431/125475/" + href)
        m2 = re.search(r"\[(\d{4})\]\s*第\s*(\d+)\s*号", text)
        if full in seen:
            continue
        seen.add(full)
        items.append({"title": text, "url": full,
                      "no": (f"[{m2.group(1)}]第{m2.group(2)}号" if m2 else "")})
    return items[:5]


# ------------------------------------------------------------------ 组装
def pick(series: dict, t: str):
    if not series:
        return None
    for k, v in series.items():
        if abs(float(k) - float(t)) < 1e-6:
            return round(v, 4)
    return None


def build() -> dict:
    cur = curve_latest()
    if not cur:
        prev = load_state("finvoice_curve")
        if prev and prev.get("data"):
            cur = prev["data"]
            log_line("[STALE] 曲线使用上次有效结果")
        else:
            log_line("[FAIL] 曲线无数据")
    else:
        save_state("finvoice_curve", {"data": cur, "updated": iso()})

    today = cur.get("date") or today_cst()
    dt = datetime.strptime(today, "%Y-%m-%d")
    hists = {}
    for label, days in (("1周前", 7), ("1个月前", 30), ("3个月前", 91), ("1年前", 365)):
        got = None
        for back in range(0, 5):          # 命中非交易日就往前找
            d = (dt - timedelta(days=days + back)).strftime("%Y-%m-%d")
            got = curve_on(d)
            if got:
                break
        if got:
            hists[label] = got
        log_line(f"[{'OK' if got else 'MISS'}] 历史曲线 {label} → {(got or {}).get('date') or d}")

    rates = money_rates() or (load_state("finvoice_rates") or {}).get("data") or {}
    if rates:
        save_state("finvoice_rates", {"data": rates, "updated": iso()})

    omo = omo_latest() or (load_state("finvoice_omo") or {}).get("data") or []
    if omo:
        save_state("finvoice_omo", {"data": omo, "updated": iso()})

    cs = cur.get("series") or {}
    rows = []
    for t, lab in TENORS:
        v = pick(cs, t)
        if v is None:
            continue
        row = {"tenor": lab, "key": t, "now": v}
        for label, h in hists.items():
            row[label] = pick(h.get("series") or {}, t)
        if row.get("1周前"):
            row["w1_bp"] = round((v - row["1周前"]) * 100, 2)
        if row.get("1个月前"):
            row["m1_bp"] = round((v - row["1个月前"]) * 100, 2)
        if row.get("1年前"):
            row["y1_bp"] = round((v - row["1年前"]) * 100, 2)
        rows.append(row)

    def latest(series: dict):
        if not series:
            return None, None, None
        ds = sorted(series)
        last, prev_d = ds[-1], (ds[-2] if len(ds) > 1 else None)
        return series[last], (series[prev_d] if prev_d else None), last

    money = {}
    for code, label, unit in (("FDR001", "DR001", "%"), ("FDR007", "DR007", "%"),
                              ("FR007", "FR007", "%"), ("SHIBOR_1W", "Shibor 1W", "%")):
        v, pv, d = latest(rates.get(code) or {})
        if v is not None:
            money[code] = {"label": label, "value": round(v, 4),
                           "prev": (round(pv, 4) if pv is not None else None),
                           "date": d, "unit": unit,
                           "chg_bp": (round((v - pv) * 100, 2) if pv is not None else None)}

    # 曲线形态：10Y-1Y 与 10Y-2Y
    y10, y1, y2 = pick(cs, "10.0"), pick(cs, "1.0"), pick(cs, "2.0")
    shape = {}
    if y10 is not None and y1 is not None:
        shape["10Y-1Y"] = round(y10 - y1, 4)
    if y10 is not None and y2 is not None:
        shape["10Y-2Y"] = round(y10 - y2, 4)
    for label, h in hists.items():
        hs = h.get("series") or {}
        hy10, hy1 = pick(hs, "10.0"), pick(hs, "1.0")
        if y10 is not None and hy10 is not None and hy1 is not None and y1 is not None:
            shape[f"10Y-1Y_{label}"] = round(hy10 - hy1, 4)

    # DR007 近 30 日序列（给资金面图用）
    dr = rates.get("FDR007") or {}
    dr_series = [{"date": d, "value": round(dr[d], 4)}
                 for d in sorted(dr)[-30:]]

    payload = {
        "meta": {
            "title": "金融之声",
            "data_date": today,
            "generated_at": iso(),
            "timezone": "Asia/Shanghai (UTC+8)",
            "audience": "金融机构销售：公募 / 私募 / 理财子",
            "note": "全部数字来自官方公开来源，可点来源链接复核。"
                    "单一权威来源，尚未独立交叉验证。",
        },
        "curve": {
            "date": today,
            "rows": rows,
            "history_labels": [{"label": k, "date": v.get("date")}
                               for k, v in hists.items()],
        },
        "shape": shape,
        "money": money,
        "dr_series": dr_series,
        "omo": omo,
        "sources": {k: {"name": v["name"], "url": v["url"], "authority": v["authority"]}
                    for k, v in SOURCES.items() if v["region"] == "CN"},
    }
    save_json(OUT_DIR / "dashboard.json", payload)
    log_line(f"金融之声数据已写入（曲线 {today}，{len(rows)} 个期限）")
    return payload


if __name__ == "__main__":
    build()
