"""
项目 A：固收市场观察 — 采集层。

输出的每一条数值都带 dataset_id / 来源编号 / 抓取时间 / 定义 / 单位 / 验证状态。
抓取失败的来源保留上次成功结果，并写 stale 状态，不写 0。

用法：
    python src/finance_fetch.py            # 增量更新
    python src/finance_fetch.py --full     # 全量重建
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
from datetime import datetime, timedelta

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from common import (PROC, ROOT, SOURCES, http_get, iso, load_state, log_line,  # noqa: E402
                    now_cst, rec, save_json, save_raw, save_state, today_cst)

KEY_TENORS = ["1.0", "2.0", "3.0", "5.0", "7.0", "10.0", "30.0"]


# --------------------------------------------------------------------- A1 收益率曲线
def fetch_yield_curve_latest() -> dict:
    """中债国债收益率曲线 — 最近一个工作日（官方 XHR）。"""
    url = "https://yield.chinabond.com.cn/cbweb-czb-web/czb/czbChartSearch"
    st, body, err = http_get(
        url, data=b"",
        headers={"Referer": "https://yield.chinabond.com.cn/cbweb-czb-web/czb/moreInfo?locale=cn_ZH&qxId=ycqx",
                 "X-Requested-With": "XMLHttpRequest",
                 "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
    if st != 200 or not body:
        return {"ok": False, "error": err or f"status={st}"}
    try:
        arr = json.loads(body.decode("utf-8", "ignore"))
    except Exception as e:                            # noqa: BLE001
        return {"ok": False, "error": f"json: {e}"}
    target = None
    for item in arr:
        if "国债收益率曲线" in (item.get("ycDefName") or ""):
            target = item
            break
    if not target:
        return {"ok": False, "error": "未找到国债收益率曲线"}
    series = {str(round(float(k), 4)): float(v) for k, v in target["seriesData"] if float(v) > 0}
    return {"ok": True, "worktime": target["worktime"],
            "curve_name": target["ycDefName"], "series": series,
            "bytes": len(body), "raw_name": "chinabond_curve_latest.json"}


def fetch_yield_curve_date(date: str, qxmc: str = "1") -> dict | None:
    """指定工作日曲线（用于历史阶段复盘）。

    实测结论（2026-09-11 验证）：
      qxmc=1 → 仅返回「中债国债收益率曲线」（111 个标准期限点，含 10Y）
      qxmc=2 → 仅返回「财政部-中国地方政府债券收益率曲线」（81 点）
      qxmc>=3 → 同时返回两条
    本项目统一使用 qxmc=1，避免把两条不同曲线拼接到一起。
    """
    q = urllib.parse.urlencode({"zblx": "xy", "workTime": date, "qxmc": qxmc})
    url = f"https://yield.chinabond.com.cn/cbweb-czb-web/czb/czbQueryXy?{q}"
    st, body, err = http_get(url, headers={"Referer": "https://yield.chinabond.com.cn/"})
    if st != 200 or not body:
        return None
    try:
        arr = json.loads(body.decode("utf-8", "ignore"))
    except Exception:                                 # noqa: BLE001
        return None
    for item in arr:
        nm = item.get("ycDefName") or ""
        if "国债" in nm and "地方" not in nm:
            series = {str(round(float(k), 4)): float(v)
                      for k, v in item["seriesData"] if float(v) > 0}
            if series:
                return {"worktime": item.get("worktime") or date,
                        "curve_name": nm, "series": series}
    return None


# --------------------------------------------------------------------- A2 回购利率
def fetch_frr() -> dict:
    """中国货币网 银行间质押式回购利率（FR / FDR 系列）。"""
    today = today_cst()
    start = (now_cst() - timedelta(days=45)).strftime("%Y-%m-%d")
    q = urllib.parse.urlencode({"lang": "CN", "startDate": start,
                                "endDate": today, "pageNum": 1, "pageSize": 60})
    url = f"https://www.chinamoney.com.cn/ags/ms/cm-u-bk-currency/FrrHis?{q}"
    st, body, err = http_get(url, headers={"Referer": "https://www.chinamoney.com.cn/chinese/bkfrr/"})
    if st != 200 or not body:
        return {"ok": False, "error": err or f"status={st}"}
    try:
        j = json.loads(body.decode("utf-8", "ignore"))
    except Exception as e:                            # noqa: BLE001
        return {"ok": False, "error": f"json: {e}"}
    records = j.get("records") or []
    series: dict[str, dict[str, float]] = {}
    # 实测字段结构（2026-09-11）：数值在 record["frValueMap"]，键为 FR001/FR007/
    # FR014/FDR001/FDR007/FDR014，值为字符串百分数（如 "1.4200"）。
    for r in records:
        vm = r.get("frValueMap") or {}
        d = vm.get("date") or r.get("lfiProducDate")
        if not d:
            continue
        for code in ("FR001", "FR007", "FDR001", "FDR007"):
            raw = vm.get(code)
            if raw is None:
                continue
            try:
                v = float(raw)
            except (TypeError, ValueError):
                continue
            if v > 0:
                series.setdefault(code, {})[d] = v
    if not series:
        return {"ok": False, "error": "frValueMap 无有效利率字段"}
    return {"ok": True, "series": series, "n_records": len(records),
            "codes": sorted(series.keys()), "raw_name": "chinamoney_frr.json"}


# --------------------------------------------------------------------- A3 Shibor
def fetch_shibor() -> dict:
    """中国货币网 Shibor。实测：只在较小 pageSize 下返回带期限键的记录。"""
    today, start = today_cst(), (now_cst() - timedelta(days=40)).strftime("%Y-%m-%d")
    series: dict[str, dict[str, float]] = {}
    last_err = "unknown"
    attempts = [{"lang": "CN", "startDate": start, "endDate": today,
                 "pageNum": 1, "pageSize": 5},
                {"lang": "CN", "startDate": today, "endDate": today,
                 "pageNum": 1, "pageSize": 5},
                {"lang": "CN", "startDate": start, "endDate": today,
                 "pageNum": 1, "pageSize": 30}]
    for params in attempts:
        q = urllib.parse.urlencode(params)
        url = f"https://www.chinamoney.com.cn/ags/ms/cm-u-bk-shibor/ShiborHis?{q}"
        st, body, err = http_get(url, headers={"Referer": "https://www.chinamoney.com.cn/chinese/bkshibor/"})
        if st != 200 or not body:
            last_err = err or f"status={st}"
            continue
        try:
            j = json.loads(body.decode("utf-8", "ignore"))
        except Exception as e:                        # noqa: BLE001
            last_err = f"json: {e}"
            continue
        recs = j.get("records") or []
        for r in recs:
            if not isinstance(r, dict):
                continue
            d = r.get("showDateCN") or r.get("lfiProducDate")
            if not d:
                continue
            raw = None
            for k, v in r.items():
                if str(k).strip().lower() in ("1w", "shibor1w", "shibor_1w"):
                    raw = v
                    break
            try:
                v = float(raw)
            except (TypeError, ValueError):
                continue
            if v > 0:
                series.setdefault("SHIBOR_1W", {})[d] = v
        if series:
            return {"ok": True, "series": series, "raw_name": "chinamoney_shibor.json"}
        last_err = f"pageSize={params['pageSize']} 返回 {len(recs)} 条但无 1W 字段"
    return {"ok": False, "error": last_err}


# --------------------------------------------------------------------- A4 央行 OMO
def fetch_pbc_omo() -> dict:
    """央行公开市场业务公告列表 — 只取标题与日期，正文强口径需人工/二次核对。"""
    url = ("https://www.pbc.gov.cn/zhengcehuobisi/125207/125213/125431/125475/index.html")
    st, body, err = http_get(url, headers={"Referer": "https://www.pbc.gov.cn/"})
    if st != 200 or not body:
        return {"ok": False, "error": err or f"status={st}"}
    html = body.decode("utf-8", "ignore")
    items = []
    for m in re.finditer(r'href="([^"]+)"[^>]*>\s*([^<]{4,80}?)\s*</a>', html):
        href, text = m.group(1), re.sub(r"\s+", " ", m.group(2)).strip()
        if "公开市场" in text or "业务交易公告" in text:
            if href.startswith("./"):
                href = href[2:]
            if href.startswith("/"):
                full = "https://www.pbc.gov.cn" + href
            else:
                full = "https://www.pbc.gov.cn/zhengcehuobisi/125207/125213/125431/125475/" + href
            items.append({"title": text, "url": full})
    seen, uniq = set(), []
    for it in items:
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        uniq.append(it)
    return {"ok": True, "count": len(uniq), "items": uniq[:12],
            "raw_name": "pbc_omo_list.html"}


# --------------------------------------------------------------------- 主流程
def get_or_keep(name: str, fetcher, *, full: bool, cache_name: str) -> dict:
    """带增量与降级的统一入口：失败时保留上次成功结果并标 stale。"""
    prev = load_state(cache_name)
    if full:
        prev = None
    res = fetcher()
    if res.get("ok"):
        if res.get("raw_name"):
            pass  # 原始体已在 http 层落盘（此处仅记录名称）
        merged = {"ok": True, "stale": False, "updated": iso(), "data": res}
        if prev and prev.get("ok") and prev.get("data"):
            merged["previous_updated"] = prev.get("updated")
        save_state(cache_name, merged)
        log_line(f"[OK]   {name}")
        return merged
    if prev and prev.get("ok"):
        prev["stale"] = True
        prev["last_error"] = res.get("error")
        prev["last_attempt"] = iso()
        save_state(cache_name, prev)
        log_line(f"[STALE] {name} 失败({res.get('error')})，保留 {prev.get('updated')} 的有效结果")
        return prev
    log_line(f"[FAIL] {name} 失败且无历史：{res.get('error')}")
    return {"ok": False, "stale": False, "updated": iso(), "error": res.get("error"), "data": None}


def main() -> None:
    full = "--full" in sys.argv
    log_line(f"=== 项目A 采集开始 full={full} build={__import__('common').BUILD_VERSION} ===")

    curve = get_or_keep("中债国债收益率曲线(最新)", fetch_yield_curve_latest,
                        full=full, cache_name="fin_curve_latest")
    frr = get_or_keep("银行间质押式回购利率 FR/FDR", fetch_frr,
                      full=full, cache_name="fin_frr")
    shib = get_or_keep("Shibor 1W", fetch_shibor, full=full, cache_name="fin_shibor")
    omo = get_or_keep("央行公开市场公告列表", fetch_pbc_omo,
                      full=full, cache_name="fin_omo")

    # --- 历史阶段复盘取点（仅在缓存缺失时补取，避免每次全量请求官方接口）---
    stages = load_state("fin_stage_curves") or {"ok": True, "points": {}}
    need = {"2024-09-30": "阶段1", "2025-09-30": "阶段2", "2026-06-30": "阶段3"}
    for d, label in need.items():
        if d in (stages.get("points") or {}):
            continue
        got = fetch_yield_curve_date(d)
        if got:
            stages["points"][d] = {"label": label, "series": got["series"]}
            log_line(f"[OK]   历史曲线 {d}({label})")
        else:
            log_line(f"[MISS] 历史曲线 {d}({label}) 未取到")
    stages["updated"] = iso()
    save_state("fin_stage_curves", stages)

    # ---------------- 组装数据集 ----------------
    datasets: list[dict] = []
    curve_series = (curve.get("data") or {}).get("series") or {}
    worktime = (curve.get("data") or {}).get("worktime")

    def pick(series: dict, tenor: str):
        for k, v in series.items():
            if abs(float(k) - float(tenor)) < 1e-6:
                return v
        return None

    for t in KEY_TENORS:
        v = pick(curve_series, t)
        if v is not None:
            datasets.append(rec(
                dataset_id=f"D-FIN-YC-{t}Y", name=f"中债国债收益率 {t}年",
                value=round(v, 4), unit="%", region="CN",
                scope="中债国债收益率曲线（银行间市场，到期收益率，日频）",
                period=worktime, published=None, source_id="S-CB-01",
                method="官方 XHR 接口解析", verified="single_authoritative",
                revision="final",
                note="单一权威来源，尚未独立交叉验证；到期收益率非持有期回报。"))

    # 期限利差（计算值，非来源直接给出）
    y10, y2 = pick(curve_series, "10.0"), pick(curve_series, "2.0")
    if y10 and y2:
        datasets.append(rec(
            dataset_id="D-FIN-SPREAD-10Y2Y", name="10年-2年国债期限利差",
            value=round(y10 - y2, 4), unit="百分点(pp)", region="CN",
            scope="同一条中债国债收益率曲线上 10Y 与 2Y 之差",
            period=worktime, published=None, source_id="S-CB-01",
            method="本项目计算（10Y - 2Y，同源同日）", verified="computed",
            revision="final",
            note="CAREFUL 曲线类型必须一致；不得与国开债曲线利差混用。"))

    for code, label, uname in (("FDR001", "DR001", "存款类机构质押式回购加权利率 1天"),
                               ("FDR007", "DR007", "存款类机构质押式回购加权利率 7天"),
                               ("FR007", "FR007", "全市场质押式回购加权利率 7天")):
        s = ((frr.get("data") or {}).get("series") or {}).get(code) or {}
        if s:
            d = max(s)
            datasets.append(rec(
                dataset_id=f"D-FIN-{label}", name=uname, value=round(s[d], 4),
                unit="%", region="CN",
                scope="银行间市场质押式回购加权利率（日频，加权利率口径）",
                period=d, published=None, source_id="S-CM-01",
                method="官方 JSON 接口解析", verified="single_authoritative",
                revision="final",
                note=("FDR 系列为存款类机构口径，即市场通称 DR 系列；"
                      "与 FR（全市场）不可混用为同一序列。")))

    ss = ((shib.get("data") or {}).get("series") or {}).get("SHIBOR_1W") or {}
    if ss:
        d = max(ss)
        datasets.append(rec(
            dataset_id="D-FIN-SHIBOR-1W", name="Shibor 1周", value=round(ss[d], 4),
            unit="%", region="CN", scope="上海银行间同业拆放利率 1周（报价行报价均值）",
            period=d, published=None, source_id="S-CM-02",
            method="官方 JSON 接口解析", verified="single_authoritative",
            revision="final", note="报价利率口径，与回购成交利率口径不同。"))

    omo_items = (omo.get("data") or {}).get("items") or []
    if omo_items:
        datasets.append(rec(
            dataset_id="D-FIN-OMO-LATEST", name="央行公开市场业务交易公告（最新标题）",
            value=omo_items[0]["title"], unit="文本", region="CN",
            scope="中国人民银行公开市场业务交易公告列表首条",
            period=None, published=None, source_id="S-PB-01",
            method="官方公告页 HTML 解析", verified="unverified",
            revision="preliminary",
            note="LIMIT 仅标题与链接；净投放须同时核对投放与到期两侧，本期未自动计算。",
            display="public"))

    out = {
        "project": "A",
        "build_version": __import__("common").BUILD_VERSION,
        "pipeline_version": __import__("common").PIPELINE_VERSION,
        "generated_at": iso(),
        "data_version": today_cst(),
        "currency_curve_worktime": worktime,
        "stage_curves": stages.get("points", {}),
        "datasets": datasets,
        "source_status": {
            "S-CB-01": {"ok": curve.get("ok"), "stale": curve.get("stale"),
                        "updated": curve.get("updated"), "error": curve.get("error")},
            "S-CB-02": {"ok": bool(stages.get("points")), "stale": False,
                        "updated": stages.get("updated")},
            "S-CM-01": {"ok": frr.get("ok"), "stale": frr.get("stale"),
                        "updated": frr.get("updated"), "error": frr.get("error")},
            "S-CM-02": {"ok": shib.get("ok"), "stale": shib.get("stale"),
                        "updated": shib.get("updated"), "error": shib.get("error")},
            "S-PB-01": {"ok": omo.get("ok"), "stale": omo.get("stale"),
                        "updated": omo.get("updated"), "error": omo.get("error")},
        },
    }
    save_json(PROC / "finance_datasets.json", out)
    log_line(f"=== 项目A 采集结束：{len(datasets)} 条数据集 ===")


if __name__ == "__main__":
    main()
