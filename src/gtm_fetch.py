"""
项目 B：英国电动车市场情报与 GTM 执行工作台 — 采集层。

锁定范围（经 2026-09-11 真实可达性验证后确定，不无限扩张）：
  国家     ：英国（UK = Great Britain + Northern Ireland；SMMT 口径为 UK）
  主车型   ：BYD DOLPHIN SURF（紧凑型纯电城市车）
  直接竞品 ：Renault 5 E-Tech electric / Vauxhall Corsa Electric / Citroën ë-C3
  优先用户 ：英国小型纯电车的私人首购与公司车（fleet / salary sacrifice）决策链
  验证切口 ：官方公开信息是否足以支撑「同级别可比判断」

数据边界（诚实记录，不猜）：
  - SMMT 免费公开页提供：总量按动力类型（月/年累计）、按销售渠道（月/年累计）、
    品牌级注册量、车型 Top10、BEV 车型 Top10。**不提供**完整车型级注册量。
  - BYD 英国官网的价格与月供为前端动态渲染，静态抓取不可得 → 记为 not_retrieved。

用法：
    python src/gtm_fetch.py [--full]
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (PROC, SOURCES, http_get, iso, load_state, log_line,  # noqa: E402
                    now_cst, rec, save_json, save_raw, save_state, today_cst)

UA_HDR = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}


# ------------------------------------------------------------------ 工具
def strip_tables(raw: str) -> list[str]:
    """把 HTML 里所有 <table> 转成用 | 分隔的纯文本行。"""
    out = []
    for t in re.findall(r"<table[\s\S]*?</table>", raw, re.I):
        txt = re.sub(r"<[^>]+>", "|", t)
        txt = html.unescape(txt)
        txt = re.sub(r"\|{2,}", "|", txt)
        txt = re.sub(r"[ \t\u00a0]+", " ", txt)
        txt = re.sub(r"\n+", "\n", txt)
        out.append(txt.strip())
    return out


def cells(row: str) -> list[str]:
    return [c.strip() for c in row.strip().strip("|").split("|") if c.strip() != ""]


def chunk(seq: list, n: int, start: int = 0) -> list[list]:
    s = seq[start:]
    return [s[i:i + n] for i in range(0, len(s) - n + 1, n)]


def num(s: str):
    """'28,063' -> 28063 ; '27.7%' -> 27.7 ; '-' -> None"""
    if s is None:
        return None
    s = str(s).replace(",", "").replace("%", "").strip()
    if s in ("", "-", "n/a", "N/A", "—"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _nums(row: list[str], n: int = 5) -> list:
    vals = [num(x) for x in row[:n]]
    while len(vals) < n:
        vals.append(None)
    return vals


# ------------------------------------------------------------------ SMMT
SMMT_URL = "https://www.smmt.co.uk/vehicle-data/car-registrations/"


def fetch_smmt() -> dict:
    """SMMT 官方页抓取。网络经代理时存在间歇性 502，故重试 3 轮。"""
    last_err = "unknown"
    for attempt in range(3):
        st, body, err = http_get(SMMT_URL, headers=UA_HDR, timeout=45)
        if st == 200 and body:
            break
        last_err = err or f"status={st}"
        log_line(f"[RETRY] SMMT 第 {attempt + 1} 轮失败：{last_err}")
        time.sleep(3)
    else:
        return {"ok": False, "error": last_err}
    raw = body.decode("utf-8", "ignore")
    name = save_raw(f"smmt_car_registrations_{today_cst()}.html", body)
    tabs = strip_tables(raw)
    if len(tabs) < 5:
        return {"ok": False, "error": f"仅解析到 {len(tabs)} 张表"}

    # SMMT 的 HTML 表是「整张表挤在一行」的结构：表头标签与数据在同一 <tr> 内，
    # 因此不能用「按行取值」，必须把一行拆成扁平单元格后按标签/固定宽度重新分组。
    out: dict = {"tables_found": len(tabs), "raw": name,
                 "powertrain": {}, "channel": {}, "brand": {},
                 "top_models": {}, "top_bev_models": {}}

    POW = {"BEV", "HEV", "PHEV", "PETROL", "DIESEL", "TOTAL"}
    CHN = {"PRIVATE", "FLEET", "BUSINESS", "TOTAL"}

    def flat(idx: int) -> list[str]:
        f: list[str] = []
        for row in tabs[idx].split("\n"):
            f += cells(row)
        return f

    # --- 表0/1：动力类型 当月 / 年累计（宽度 5）---
    for idx, key in ((0, "month"), (1, "ytd")):
        f = flat(idx)
        bucket = out["powertrain"].setdefault(key, {})
        for i, c in enumerate(f):
            k = c.upper().replace("ALL ", "").strip()
            if k in POW and k not in bucket:
                v = _nums(f[i + 1:i + 6])
                bucket[k] = {"cur": v[0], "prev": v[1], "pct_change": v[2],
                             "share_cur": v[3], "share_prev": v[4]}

    # --- 表2/3：销售渠道 当月 / 年累计 ---
    for idx, key in ((2, "month"), (3, "ytd")):
        f = flat(idx)
        bucket = out["channel"].setdefault(key, {})
        for i, c in enumerate(f):
            k = c.upper().replace("ALL ", "").strip()
            if k in CHN and k not in bucket:
                v = _nums(f[i + 1:i + 6])
                bucket[k] = {"cur": v[0], "prev": v[1], "pct_change": v[2],
                             "share_cur": v[3], "share_prev": v[4]}

    # --- 表4/5：品牌级 当月 / 年累计（表头占前 7 格，之后每 6 格一个品牌）---
    for idx, key in ((4, "month"), (5, "ytd")):
        f = flat(idx)
        bucket = out["brand"].setdefault(key, {})
        body = f[7:] if len(f) > 7 else []
        for g in chunk(body, 6):
            brand = g[0].strip()
            if not brand or num(g[1]) is None and num(g[3]) is None:
                continue
            bucket[brand] = {"cur": num(g[1]), "share_cur": num(g[2]),
                             "prev": num(g[3]), "share_prev": num(g[4]),
                             "pct_change": num(g[5])}

    # --- 表6/7/8：车型 / BEV 车型 Top10（表头占 1 格，之后每 3 格一条）---
    for idx, key in ((6, "month_all"), (7, "ytd_all"), (8, "month_bev")):
        f = flat(idx)
        ranked = []
        for g in chunk(f, 3, start=1):
            rk, mdl, un = num(g[0]), g[1], num(g[2])
            if rk is not None and un is not None:
                ranked.append({"rank": int(rk), "model": mdl, "units": int(un)})
        tgt = "top_models" if "all" in key else "top_bev_models"
        out[tgt][key] = ranked

    return {"ok": True, "data": out, "raw_name": name}


# ------------------------------------------------------------------ 车型官方事实
def fetch_model_facts(url: str, sid: str, patterns: dict) -> dict:
    st, body, err = http_get(url, headers=UA_HDR, timeout=35)
    if st != 200 or not body:
        return {"ok": False, "error": err or f"status={st}", "url": url}
    txt = html.unescape(body.decode("utf-8", "ignore"))
    facts = {}
    for key, pat in patterns.items():
        hits = re.findall(pat, txt, re.I)
        facts[key] = sorted(set(h if isinstance(h, str) else h[0] for h in hits))[:8]
    return {"ok": True, "url": url, "facts": facts, "bytes": len(body),
            "source_id": sid}


# ------------------------------------------------------------------ 主流程
def main() -> None:
    full = "--full" in sys.argv
    log_line(f"=== 项目B 采集开始 full={full} ===")

    # 1) SMMT 市场统计
    prev = None if full else load_state("gtm_smmt")
    smmt = fetch_smmt()
    if smmt.get("ok"):
        smmt_state = {"ok": True, "stale": False, "updated": iso(), "data": smmt["data"]}
        save_state("gtm_smmt", smmt_state)
        log_line("[OK]   SMMT 月度/年累计注册数据")
    elif prev and prev.get("ok"):
        prev["stale"] = True
        prev["last_error"] = smmt.get("error")
        prev["last_attempt"] = iso()
        save_state("gtm_smmt", prev)
        smmt_state = prev
        log_line(f"[STALE] SMMT 失败({smmt.get('error')})，保留 {prev.get('updated')}")
    else:
        smmt_state = {"ok": False, "data": None, "error": smmt.get("error")}
        log_line(f"[FAIL] SMMT：{smmt.get('error')}")

    # 2) 车型官方事实（主车型 + 直接竞品）。
    # 竞品选择规则（2026-09-11 实测可达性后锁定，不事后调整）：
    #   (a) 英国在售的紧凑/小型纯电乘用车；
    #   (b) 品牌英国官网可公开访问并核实规格；
    #   (c) 覆盖价格阶梯：入门(Dacia Spring) — 主流(BYD DOLPHIN SURF) — 主流偏上(Renault 5 / MG4 EV)。
    # 已知限制：SMMT 免费 BEV Top10 中只出现 Renault 5，另两款无可公开核实的车型级注册量。
    targets = [
        ("S-BY-01", "https://www.byd.com/uk/electric-cars/dolphin-surf", "BYD DOLPHIN SURF",
         {"range_miles": r'"?val"?\s*:\s*"?(\d{2,3})"?\s*,\s*"?suffix"?\s*:\s*"miles"',
          "charge_kw": r'Fast charge in\s*"?[^0-9]{0,12}(\d{1,3})"?',
          "model_name": r'BYD DOLPHIN SURF'}),
        ("S-RN-01", "https://www.renault.co.uk/electric-vehicles/r5-e-tech-electric.html",
         "Renault 5 E-Tech electric",
         {"range_miles": r'(\d{3})\s*miles', "battery_kwh": r'(\d{2}(?:\.\d)?)\s*kWh'}),
        ("S-MG-01", "https://www.mg.co.uk/new-cars/mg4-ev", "MG4 EV",
         {"range_miles": r'(\d{3})\s*miles', "battery_kwh": r'(\d{2}(?:\.\d)?)\s*kWh'}),
        ("S-DC-01", "https://www.dacia.co.uk/hybrid-range/spring-electric.html",
         "Dacia Spring Electric",
         {"range_miles": r'(\d{2,3})\s*(?:miles|mi\b)',
          "battery_kwh": r'(\d{2}(?:\.\d)?)\s*kWh',
          "wltp": r'WLTP[^<]{0,60}'}),
    ]
    model_state = load_state("gtm_models") or {"ok": True, "models": {}}
    for sid, url, label, pats in targets:
        if not full and label in (model_state.get("models") or {}) \
                and model_state["models"][label].get("ok"):
            continue
        r = fetch_model_facts(url, sid, pats)
        r["label"] = label
        model_state["models"][label] = r
        log_line(f"[{'OK' if r.get('ok') else 'MISS'}]   {label} "
                 f"{'' if r.get('ok') else '(' + str(r.get('error')) + ')'}")
    model_state["updated"] = iso()
    save_state("gtm_models", model_state)

    # ---------------- 组装数据集 ----------------
    datasets: list[dict] = []
    d = smmt_state.get("data") or {}
    pt, ch, br = d.get("powertrain", {}), d.get("channel", {}), d.get("brand", {})

    def add(dsid, name, value, unit, scope, period, sid, method,
            verified="single_authoritative", note="", revision="preliminary"):
        datasets.append(rec(dataset_id=dsid, name=name, value=value, unit=unit,
                            region="UK", scope=scope, period=period,
                            published=None, source_id=sid, method=method,
                            verified=verified, revision=revision, note=note))

    m_bev = (pt.get("month") or {}).get("BEV") or {}
    y_bev = (pt.get("ytd") or {}).get("BEV") or {}
    m_tot = (pt.get("month") or {}).get("TOTAL") or {}
    y_tot = (pt.get("ytd") or {}).get("TOTAL") or {}
    m_total_units = m_tot.get("cur")

    if m_bev.get("cur") is not None:
        add("D-GTM-BEV-M", "英国纯电乘用车月度注册量（当月）", int(m_bev["cur"]),
            "辆", "SMMT 口径：英国新乘用车注册，纯电（BEV），当月",
            "最新月度", "S-SM-01", "SMMT 官方页面表格解析",
            note="注册量 ≠ 销量 ≠ 交付量。SMMT 为英国汽车制造商与贸易商协会。")
        add("D-GTM-BEV-SHARE-M", "英国纯电乘用车市场份额（当月）", m_bev.get("share_cur"),
            "%", "SMMT 口径：BEV 占当月新乘用车注册比重", "最新月度",
            "S-SM-01", "SMMT 官方页面表格解析")
        add("D-GTM-BEV-YOY-M", "英国纯电乘用车注册同比（当月）", m_bev.get("pct_change"),
            "%", "SMMT 口径：BEV 当月注册量同比", "最新月度",
            "S-SM-01", "SMMT 官方页面表格解析")

    if y_bev.get("cur") is not None:
        add("D-GTM-BEV-YTD", "英国纯电乘用车注册量（年初至今）", int(y_bev["cur"]),
            "辆", "SMMT 口径：英国新乘用车注册，纯电（BEV），年初至今累计",
            "年初至今累计", "S-SM-01", "SMMT 官方页面表格解析")
        add("D-GTM-BEV-SHARE-YTD", "英国纯电乘用车市场份额（年初至今）", y_bev.get("share_cur"),
            "%", "SMMT 口径：BEV 占年初至今新乘用车注册比重", "年初至今累计",
            "S-SM-01", "SMMT 官方页面表格解析")
    if y_tot.get("cur") is not None:
        add("D-GTM-TOTAL-YTD", "英国新乘用车注册总量（年初至今）", int(y_tot["cur"]),
            "辆", "SMMT 口径：英国新乘用车注册全动力类型，年初至今累计",
            "年初至今累计", "S-SM-01", "SMMT 官方页面表格解析")

    # 渠道结构（这是本项目最关键的 GTM 判断依据之一）
    mc = ch.get("month") or {}
    for k in ("Private", "Fleet", "Business"):
        v = mc.get(k) or {}
        if v.get("share_cur") is not None:
            add(f"D-GTM-CH-{k.upper()}-SHARE", f"英国新乘用车销售渠道占比 — {k}（当月）",
                v["share_cur"], "%",
                "SMMT 口径：当月新乘用车注册按销售渠道拆分（Private/Fleet/Business）",
                "最新月度", "S-SM-01", "SMMT 官方页面表格解析",
                note="渠道占比是 GTM 判断公司车/私人渠道优先级的直接依据。")

    # BYD 品牌级
    b_m = (br.get("month") or {}).get("Byd") or {}
    b_y = (br.get("ytd") or {}).get("Byd") or {}
    if b_m.get("cur") is not None:
        add("D-GTM-BYD-M", "BYD 品牌英国月度注册量", int(b_m["cur"]), "辆",
            "SMMT 口径：BYD 品牌新乘用车注册，当月（含全部动力类型）", "最新月度",
            "S-SM-02", "SMMT 官方页面表格解析",
            note="品牌级，非 DOLPHIN SURF 车型级；不可直接当作该车型销量。")
        add("D-GTM-BYD-SHARE-M", "BYD 品牌英国月度市场份额", b_m.get("share_cur"), "%",
            "SMMT 口径：BYD 占当月新乘用车注册比重", "最新月度",
            "S-SM-02", "SMMT 官方页面表格解析")
        add("D-GTM-BYD-YOY-M", "BYD 品牌英国月度注册同比", b_m.get("pct_change"), "%",
            "SMMT 口径：BYD 当月注册量同比", "最新月度",
            "S-SM-02", "SMMT 官方页面表格解析")
    if b_y.get("cur") is not None:
        add("D-GTM-BYD-YTD", "BYD 品牌英国注册量（年初至今）", int(b_y["cur"]), "辆",
            "SMMT 口径：BYD 品牌新乘用车注册，年初至今累计", "年初至今累计",
            "S-SM-02", "SMMT 官方页面表格解析")
        add("D-GTM-BYD-SHARE-YTD", "BYD 品牌英国市场份额（年初至今）", b_y.get("share_cur"), "%",
            "SMMT 口径：BYD 占年初至今新乘用车注册比重", "年初至今累计",
            "S-SM-02", "SMMT 官方页面表格解析")

    # 车型级 Top10（免费页仅提供 Top10，作为竞品选择的证据而非完整车型销量）
    bev_models = (d.get("top_bev_models") or {}).get("month_bev") or []
    if bev_models:
        add("D-GTM-BEV-TOP10-M", "英国 BEV 车型注册量 Top10（当月）",
            " ; ".join(f"{x['rank']}.{x['model']} {x['units']}" for x in bev_models[:10]),
            "辆", "SMMT 口径：当月 BEV 车型注册量前 10 名", "最新月度",
            "S-SM-01", "SMMT 官方页面表格解析", verified="single_authoritative",
            note="LIMIT SMMT 免费页仅公开 Top10，无完整车型级注册量，"
                 "因此竞品选择以品牌级可核实数据 + 官方车型页为双重依据。")

    # 车型官方规格事实
    models_out = {}
    for label, m in (model_state.get("models") or {}).items():
        models_out[label] = {"ok": bool(m.get("ok")), "url": m.get("url"),
                             "facts": m.get("facts") or {},
                             "error": m.get("error")}
        if m.get("ok") and m.get("facts", {}).get("range_miles"):
            add(f"D-GTM-SPEC-{label.split()[0].upper()}", f"{label} 官方续航（WLTP/官网页）",
                " / ".join(m["facts"]["range_miles"][:3]), "英里",
                "品牌官方网站公布的续航数值（口径以各品牌页面标注为准）",
                None, m.get("source_id") or "S-BY-01", "品牌官网 HTML 解析",
                note="CAREFUL 各品牌续航测试口径可能不同（WLTP combined / urban / 等），"
                     "未逐一口径对齐前不得直接排名。")

    out = {
        "project": "B",
        "build_version": __import__("common").BUILD_VERSION,
        "generated_at": iso(),
        "data_version": today_cst(),
        "smmt_status": {"ok": smmt_state.get("ok"), "stale": smmt_state.get("stale"),
                        "updated": smmt_state.get("updated"),
                        "error": smmt_state.get("error")},
        "smmt_raw": d,
        "model_facts": models_out,
        "datasets": datasets,
        "not_retrieved": [
            {"item": "BYD DOLPHIN SURF 英国官方售价 / PCP 月供",
             "reason": "官网价格与月供由前端动态渲染，静态请求无法取得",
             "source_id": "S-BY-02",
             "url": "https://www.byd.com/uk/purchase/pcp-uk",
             "status": "not_retrieved",
             "action": "需人工打开页面读取，或后续引入浏览器渲染采集"},
            {"item": "完整车型级注册量（非 Top10）",
             "reason": "SMMT 免费公开页只提供 Top10 车型",
             "source_id": "S-SM-01", "status": "restricted",
             "action": "不购买付费数据；在结论中明确车型级不可得"},
        ],
    }
    save_json(PROC / "gtm_datasets.json", out)

    # 同步给网站消费的公开数据
    save_json(PROC / "gtm_public.json", {
        "data_version": today_cst(), "generated_at": iso(), "datasets": datasets})
    log_line(f"=== 项目B 采集结束：{len(datasets)} 条数据集 ===")


if __name__ == "__main__":
    main()
