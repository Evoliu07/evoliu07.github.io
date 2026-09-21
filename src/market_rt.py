"""
实时市场指标采集 → data/dash/market_rt.json

七个口径（全部为公开可核验来源）：
  1 上证指数      东方财富 行情接口（secid 1.000001）
  2 沪深300       东方财富 行情接口（secid 1.000300）
  3 恒生指数      东方财富 行情接口（secid 100.HSI）
  4 10Y 国债      中国债券信息网 中债国债收益率曲线；当日变动按上一交易日曲线计算
  5 两融余额      东方财富 融资融券市场统计（RZYE + RQYE）
  6 美元兑人民币   中国货币网 人民币汇率中间价（USD/CNY）
  7 10Y-2Y 利差   同一条中债国债曲线上取点相减

每个字段独立采集、独立降级：抓不到就在输出里 absence，由渲染层整块不显示。
用法： python src/market_rt.py
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, http_get, iso, log_line, now_cst, save_json   # noqa: E402

OUT = ROOT / "data" / "dash" / "market_rt.json"
UA_HDR = {"Referer": "https://quote.eastmoney.com/"}


def num(v):
    try:
        f = float(v)
        return f
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- 1-3 指数
def _sina_indices() -> dict:
    """新浪行情：一次拿三个。字段：今开,昨收,最新,最高,最低,...；港股多一个名称列。"""
    st, body, _ = http_get(
        "https://hq.sinajs.cn/list=sh000001,sz399300,rt_hkHSI",
        headers={"Referer": "https://finance.sina.com.cn"}, timeout=20)
    if st != 200 or not body:
        return {}
    text = body.decode("gbk", "ignore")
    want = {"sh000001": "上证指数", "sz399300": "沪深300", "rt_hkHSI": "恒生指数"}
    out = {}
    for m in re.finditer(r'hq_str_(\w+)="([^"]*)"', text):
        code, payload = m.group(1), m.group(2)
        if code not in want or not payload:
            continue
        f = payload.split(",")
        try:
            if code == "rt_hkHSI":
                prev, last = num(f[3]), num(f[6])
            else:
                prev, last = num(f[2]), num(f[3])
        except IndexError:
            continue
        if not prev or last is None:
            continue
        chg = last - prev
        out[code] = {"name": want[code], "price": round(last, 2),
                     "pct": round(chg / prev * 100, 2), "chg": round(chg, 2)}
    return out


def _em_indices() -> dict:
    url = ("https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2"
           "&secids=1.000001,1.000300,100.HSI&fields=f2,f3,f4,f12,f14")
    st, body, _ = http_get(url, headers=UA_HDR, timeout=20)
    if st != 200 or not body:
        return {}
    try:
        diff = (json.loads(body.decode("utf-8", "ignore")).get("data") or {}).get("diff") or []
    except Exception:                                  # noqa: BLE001
        return {}
    m = {"000001": ("sh000001", "上证指数"), "000300": ("sz399300", "沪深300"),
         "HSI": ("rt_hkHSI", "恒生指数")}
    out = {}
    for d in diff:
        if d.get("f12") not in m:
            continue
        price, pct, chg = num(d.get("f2")), num(d.get("f3")), num(d.get("f4"))
        if price is None:
            continue
        key, nm = m[d["f12"]]
        out[key] = {"name": nm, "price": round(price, 2),
                    "pct": round(pct, 2) if pct is not None else None,
                    "chg": round(chg, 2) if chg is not None else None}
    return out


def fetch_indices() -> dict:
    """新浪优先（稳定），东财兜底；两源数据同口径，可交叉核对。"""
    return _sina_indices() or _em_indices()


# ---------------------------------------------------------------- 4/7 中债曲线
def _curve(worktime: str | None) -> dict:
    """worktime=None 取最新，否则取指定工作日。qxmc=1 才是国债曲线。"""
    if worktime is None:
        st, body, _ = http_get(
            "https://yield.chinabond.com.cn/cbweb-czb-web/czb/czbChartSearch",
            data=b"", timeout=20,
            headers={"Referer": "https://yield.chinabond.com.cn/cbweb-czb-web/czb/moreInfo?locale=cn_ZH&qxId=ycqx",
                     "X-Requested-With": "XMLHttpRequest"})
        if st != 200 or not body:
            return {}
        try:
            for it in json.loads(body.decode("utf-8", "ignore")):
                if "国债收益率曲线" in (it.get("ycDefName") or ""):
                    return {"date": it.get("worktime"),
                            "s": {float(k): float(v) for k, v in it["seriesData"] if float(v) > 0}}
        except Exception:                              # noqa: BLE001
            return {}
        return {}
    q = urllib.parse.urlencode({"zblx": "xy", "workTime": worktime, "qxmc": "1"})
    st, body, _ = http_get(
        f"https://yield.chinabond.com.cn/cbweb-czb-web/czb/czbQueryXy?{q}",
        headers={"Referer": "https://yield.chinabond.com.cn/"}, timeout=20)
    if st != 200 or not body:
        return {}
    try:
        for it in json.loads(body.decode("utf-8", "ignore")):
            nm = it.get("ycDefName") or ""
            if "国债" in nm and "地方" not in nm:
                s = {float(k): float(v) for k, v in it["seriesData"] if float(v) > 0}
                if s:
                    return {"date": it.get("worktime") or worktime, "s": s}
    except Exception:                                  # noqa: BLE001
        pass
    return {}


def fetch_cgb() -> dict:
    cur = _curve(None)
    if not cur:
        return {}
    d0 = datetime.strptime(cur["date"], "%Y-%m-%d")
    prev = {}
    for back in range(1, 8):                           # 向前找最近一个有数据的工作日
        d = (d0 - timedelta(days=back)).strftime("%Y-%m-%d")
        c = _curve(d)
        if c:
            prev = c
            break
    y10 = cur["s"].get(10.0)
    y2 = cur["s"].get(2.0)
    p10 = (prev.get("s") or {}).get(10.0)
    out = {"date": cur["date"]}
    if y10 is not None:
        out["y10"] = round(y10, 4)
    if y2 is not None:
        out["y2"] = round(y2, 4)
    if y10 is not None and p10 is not None:
        out["y10_chg_bp"] = round((y10 - p10) * 100, 2)
        out["y10_prev_date"] = prev.get("date")
    if y10 is not None and y2 is not None:
        out["spread_10y2y"] = round(y10 - y2, 4)
    return out


# ---------------------------------------------------------------- 5 两融
def fetch_margin() -> dict:
    url = ("https://datacenter-web.eastmoney.com/api/data/v1/get"
           "?reportName=RPTA_RZRQ_LSHJ&columns=DIM_DATE,RZYE,RQYE&source=WEB&client=WEB"
           "&sortColumns=DIM_DATE&sortTypes=-1&pageSize=1")
    st, body, _ = http_get(url, headers=UA_HDR, timeout=20)
    if st != 200 or not body:
        return {}
    try:
        d = (json.loads(body.decode("utf-8", "ignore")).get("result") or {}).get("data") or []
        if not d:
            return {}
        r = d[0]
        rzye, rqye = num(r.get("RZYE")), num(r.get("RQYE"))
        if rzye is None:
            return {}
        total = rzye + (rqye or 0)
        return {"date": (r.get("DIM_DATE") or "")[:10],
                "total": total, "rzye": rzye, "rqye": rqye}
    except Exception:                                  # noqa: BLE001
        return {}


# ---------------------------------------------------------------- 6 中间价
def fetch_usdcny() -> dict:
    today = now_cst().strftime("%Y-%m-%d")
    start = (now_cst() - timedelta(days=14)).strftime("%Y-%m-%d")
    q = urllib.parse.urlencode({"startDate": start, "endDate": today,
                                "currency": "USD/CNY", "pageNum": 1, "pageSize": 20})
    st, body, _ = http_get(
        f"https://www.chinamoney.com.cn/ags/ms/cm-u-bk-ccpr/CcprHisNew?{q}",
        headers={"Referer": "https://www.chinamoney.com.cn/chinese/bkccpr/"}, timeout=20)
    if st != 200 or not body:
        return {}
    try:
        recs = json.loads(body.decode("utf-8", "ignore")).get("records") or []
    except Exception:                                  # noqa: BLE001
        return {}
    rows = []
    for r in recs:
        v = (r.get("values") or [None])[0]
        f = num(v)
        if r.get("date") and f:
            rows.append((r["date"], f))
    rows.sort(reverse=True)
    if not rows:
        return {}
    d, v = rows[0]
    out = {"date": d, "value": round(v, 4)}
    if len(rows) > 1:
        out["prev"] = round(rows[1][1], 4)
        out["chg"] = round(v - rows[1][1], 4)
    return out


# ---------------------------------------------------------------- 组装
def build() -> dict:
    idx = fetch_indices()
    cgb = fetch_cgb()
    mg = fetch_margin()
    fx = fetch_usdcny()

    items = []
    for code, key in (("sh000001", "sh"), ("sz399300", "hs300"), ("rt_hkHSI", "hsi")):
        d = idx.get(code)
        if not d:
            continue
        items.append({
            "id": key, "name": d["name"], "value": f'{d["price"]:,.2f}',
            "unit": "点", "chg_text": (f'{d["pct"]:+.2f}%' if d["pct"] is not None else None),
            "chg_sign": (1 if (d["pct"] or 0) > 0 else (-1 if (d["pct"] or 0) < 0 else 0)),
            "sub": (f'{"+" if (d["chg"] or 0) > 0 else ""}{d["chg"]:,.2f}' if d["chg"] is not None else None),
            "kind": "index",
        })
    if cgb.get("y10") is not None:
        items.append({
            "id": "cgb10y", "name": "10 年期国债收益率",
            "value": f'{cgb["y10"]:.2f}', "unit": "%",
            "chg_text": (f'{cgb["y10_chg_bp"]:+.1f}bp' if cgb.get("y10_chg_bp") is not None else None),
            "chg_sign": (1 if (cgb.get("y10_chg_bp") or 0) > 0 else (-1 if (cgb.get("y10_chg_bp") or 0) < 0 else 0)),
            "sub": f'截至 {cgb["date"]}', "kind": "rate"})
    if mg:
        items.append({
            "id": "margin", "name": "两融余额",
            "value": f'{mg["total"] / 1e12:.2f}', "unit": "万亿元",
            "chg_text": None, "chg_sign": 0,
            "sub": f'截至 {mg["date"]}', "kind": "amount"})
    if fx:
        items.append({
            "id": "usdcny", "name": "美元兑人民币",
            "value": f'{fx["value"]:.4f}', "unit": "",
            "chg_text": (f'{fx["chg"]:+.4f}' if fx.get("chg") is not None else None),
            "chg_sign": (1 if (fx.get("chg") or 0) > 0 else (-1 if (fx.get("chg") or 0) < 0 else 0)),
            "sub": f'中间价 {fx["date"]}', "kind": "fx"})
    if cgb.get("spread_10y2y") is not None:
        items.append({
            "id": "spread", "name": "10Y − 2Y 期限利差",
            "value": f'{cgb["spread_10y2y"]:.2f}', "unit": "个百分点",
            "chg_text": None, "chg_sign": 0,
            "sub": f'截至 {cgb["date"]}', "kind": "spread"})

    payload = {
        "generated_at": iso(),
        "as_of": now_cst().strftime("%Y-%m-%d %H:%M"),
        "items": items,
        "cgb": cgb,
        "margin": mg,
        "fx": fx,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    log_line(f"实时指标 {len(items)} 项 → {OUT.relative_to(ROOT)}")
    for it in items:
        log_line(f"   {it['name']}：{it['value']}{it['unit']}  {it.get('chg_text') or ''}  {it.get('sub') or ''}")
    return payload


if __name__ == "__main__":
    build()
