"""
德国吹风机市场真实贸易数据 → data/dash/germany_trade.json

来源：联合国商品贸易统计数据库（UN Comtrade）公开预览接口，免密钥、官方口径
  reporterCode=276（德国） cmdCode=851631（吹风机） flowCode=M（进口）
  月度 freq=M，可按 partnerCode 区分来源国（0=全球，156=中国）
失败降级：任一次抓取失败即保留上次成功结果，不写空值、不占位。

用法： python src/market_de.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, http_get, iso, log_line, now_cst, save_json   # noqa: E402

OUT = ROOT / "data" / "dash" / "germany_trade.json"
BASE = "https://comtradeapi.un.org/public/v1/preview/C/{freq}/HS?reporterCode=276&period={p}&cmdCode=851631&flowCode=M&partnerCode={pt}"
MONTHS = 12          # 取最近 12 个月（每国单独查询，避免预览接口 500 条截断）


def fetch(period: str, partner: int) -> dict:
    """返回 {'usd': 进口额(美元), 'kg': 净重(公斤)}；失败返回 None。"""
    url = BASE.format(freq="M", p=period, pt=partner)
    st, body, err = http_get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=45)
    if st != 200 or not body:
        return None
    try:
        data = json.loads(body.decode("utf-8", "ignore"))
    except Exception:                                   # noqa: BLE001
        return None
    recs = data.get("data") or []
    if not recs:
        return None
    usd = sum((r.get("primaryValue") or 0) for r in recs)
    kg = sum((r.get("netWkg") or 0) for r in recs)
    if usd <= 0:
        return None
    return {"usd": usd, "kg": kg}


def month_seq(n: int) -> list[str]:
    now = now_cst()
    out = []
    for i in range(n):
        d = (now.replace(day=1) - timedelta(days=31 * i))
        out.append(d.strftime("%Y%m"))
    return sorted(set(out), reverse=True)[:n]


def main() -> None:
    periods = month_seq(MONTHS)
    months, ok_n = [], 0
    for p in periods:
        w = fetch(p, 0)
        c = fetch(p, 156)
        if not w:
            continue
        ok_n += 1
        cu = (c or {}).get("usd", 0.0)
        share = (cu / w["usd"] * 100) if w["usd"] else 0.0
        months.append({
            "period": p,
            "label": f'{p[:4]}-{p[4:]}',
            "world_usd": round(w["usd"], 2),
            "china_usd": round(cu, 2),
            "china_share": round(share, 1),
            "unit_usd_per_kg": (round(w["usd"] / w["kg"], 2) if w.get("kg") else None),
        })
    months.sort(key=lambda x: x["period"])

    if not months:
        log_line("[STALE] 德国贸易数据本次未取到，保留上次结果")
        return

    latest = months[-1]
    payload = {
        "generated_at": iso(),
        "as_of": now_cst().strftime("%Y-%m-%d %H:%M"),
        "latest_month": latest["label"],
        "months": months,
        "source": "UN Comtrade（联合国商品贸易统计数据库）· 德国进口 HS 851631",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    log_line(f"德国贸易数据 {len(months)} 个月 → {OUT.relative_to(ROOT)}")
    log_line(f"   最新 {latest['label']}：全球 {latest['world_usd']/1e6:,.1f} 百万美元"
             f" / 自中国 {latest['china_usd']/1e6:,.1f} 百万美元"
             f" / 中国占比 {latest['china_share']}%")


if __name__ == "__main__":
    main()
