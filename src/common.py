"""
共用基础设施：路径、来源登记表、带缓存的 HTTP、元数据记录、日志。

设计原则（对应交付要求）：
- 每条数据必须能追溯到来源编号 + 抓取时间 + 定义 + 单位 + 验证状态。
- 抓取失败不覆盖上次成功结果（保留 stale 状态）。
- 程序采集与模型解读分离：本文件不含任何模型调用。
"""
from __future__ import annotations

import hashlib
import json
import os
import ssl
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ---------------------------------------------------------------- 路径
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
STATE = ROOT / "data" / "state"
CACHE = ROOT / "data" / "cache"
MARKET = ROOT / "data" / "market"          # 网站消费的公开数据（同源版本）
for _p in (RAW, PROC, STATE, CACHE, MARKET):
    _p.mkdir(parents=True, exist_ok=True)

CST = timezone(timedelta(hours=8))          # 北京时间
BUILD_VERSION = "v1.0.0"
PIPELINE_VERSION = "pipeline-1.0.0"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

# ---------------------------------------------------------------- 来源登记表
# authority: A=原始披露/官方  B=官方衍生/行业机构  C=媒体/二手
# redistribution: 该来源内容可否再分发到公开目录
SOURCES: dict[str, dict] = {
    "S-CB-01": {
        "name": "中国债券信息网（中央国债登记结算公司）— 中债国债收益率曲线",
        "url": "https://yield.chinabond.com.cn/cbweb-czb-web/czb/moreInfo?locale=cn_ZH&qxId=ycqx",
        "endpoint": "POST https://yield.chinabond.com.cn/cbweb-czb-web/czb/czbChartSearch",
        "authority": "A",
        "region": "CN",
        "method": "官方页面 XHR 接口（公开、无需登录）",
        "redistribution": "仅再分发派生数值与自有图表，不镜像原始页面",
        "notes": "中债估值中心编制，财政部授权发布的关键期限国债收益率曲线。",
    },
    "S-CB-02": {
        "name": "中国债券信息网 — 指定工作日收益率曲线",
        "url": "https://yield.chinabond.com.cn/cbweb-czb-web/czb/czbQueryXy?zblx=xy&workTime={date}&qxmc=2",
        "endpoint": "GET https://yield.chinabond.com.cn/cbweb-czb-web/czb/czbQueryXy",
        "authority": "A",
        "region": "CN",
        "method": "官方页面 XHR 接口（公开、无需登录）",
        "redistribution": "仅再分发派生数值与自有图表",
        "notes": "用于补取历史工作日曲线，支撑期限利差与阶段复盘。",
    },
    "S-CM-01": {
        "name": "中国货币网（全国银行间同业拆借中心）— 银行间质押式回购利率",
        "url": "https://www.chinamoney.com.cn/chinese/bkfrr/",
        "endpoint": "GET https://www.chinamoney.com.cn/ags/ms/cm-u-bk-currency/FrrHis",
        "authority": "A",
        "region": "CN",
        "method": "官方站点公开 JSON 接口",
        "redistribution": "仅再分发派生数值",
        "notes": "含 FR001/FR007/FR014（全市场）与 FDR001/FDR007/FDR014（存款类机构，即 DR 系列）。",
    },
    "S-CM-02": {
        "name": "中国货币网 — Shibor",
        "url": "https://www.chinamoney.com.cn/chinese/bkshibor/",
        "endpoint": "GET https://www.chinamoney.com.cn/ags/ms/cm-u-bk-shibor/ShiborHis",
        "authority": "A",
        "region": "CN",
        "method": "官方站点公开 JSON 接口",
        "redistribution": "仅再分发派生数值",
        "notes": "作为货币市场基准利率的旁证，不与 DR 混用为同一口径。",
    },
    "S-PB-01": {
        "name": "中国人民银行 — 公开市场业务交易公告",
        "url": "https://www.pbc.gov.cn/zhengcehuobisi/125207/125213/125431/125475/index.html",
        "authority": "A",
        "region": "CN",
        "method": "官方公告页 HTML 解析（仅取标题与日期，正文另核）",
        "redistribution": "仅再分发标题/日期与派生净投放，不复制全文",
        "notes": "净投放须同时核对投放与到期两侧，单看一侧会误判。",
    },
    "S-SM-01": {
        "name": "SMMT — UK Car Registrations（月度 / 年累计，按动力类型与销售渠道）",
        "url": "https://www.smmt.co.uk/vehicle-data/car-registrations/",
        "authority": "B",
        "region": "UK",
        "method": "官方页面 HTML 表格解析",
        "redistribution": "SMMT 为英国汽车工业协会，免费公开部分可引用并注明来源；不批量镜像",
        "notes": "注册量 ≠ 销量 ≠ 交付量。免费页仅提供品牌级与 BEV Top10 车型级。",
    },
    "S-SM-02": {
        "name": "SMMT — 品牌注册量（月度 / 年累计）",
        "url": "https://www.smmt.co.uk/vehicle-data/car-registrations/",
        "authority": "B",
        "region": "UK",
        "method": "官方页面 HTML 表格解析",
        "redistribution": "引用并注明来源",
        "notes": "BYD 品牌级注册量，用于测算渗透与增速。",
    },
    "S-BY-01": {
        "name": "BYD UK 官网 — BYD DOLPHIN SURF 车型页",
        "url": "https://www.byd.com/uk/electric-cars/dolphin-surf",
        "authority": "A",
        "region": "UK",
        "method": "品牌官网 HTML 解析",
        "redistribution": "仅引用事实性规格数值，不复制品牌素材",
        "notes": "官方定位 'The Compact Electric City Car'，续航 'up to 200 miles'。",
    },
    "S-BY-02": {
        "name": "BYD UK 官网 — PCP 金融方案页",
        "url": "https://www.byd.com/uk/purchase/pcp-uk",
        "authority": "A",
        "region": "UK",
        "method": "品牌官网 HTML 解析",
        "redistribution": "仅引用事实与链接",
        "notes": "价格与月供由前端动态渲染，静态抓取不可得 → 状态记为 not_retrieved。",
    },
    "S-RN-01": {
        "name": "Renault UK 官网 — Renault 5 E-Tech electric",
        "url": "https://www.renault.co.uk/electric-vehicles/r5-e-tech-electric.html",
        "authority": "A",
        "region": "UK",
        "method": "品牌官网 HTML 解析",
        "redistribution": "仅引用链接与事实",
        "notes": "竞品基线之一。同级别最直接的对手；亦出现在 SMMT 当月 BEV 车型 Top10。",
    },
    "S-MG-01": {
        "name": "MG Motor UK 官网 — MG4 EV",
        "url": "https://www.mg.co.uk/new-cars/mg4-ev",
        "authority": "A",
        "region": "UK",
        "method": "品牌官网 HTML 解析（2026-09-11 实测可达 200）",
        "redistribution": "仅引用链接与事实",
        "notes": "竞品基线之一。英国在售纯电紧凑掀背，价格带贴近主车型上沿。",
    },
    "S-DC-01": {
        "name": "Dacia UK 官网 — Spring Electric",
        "url": "https://www.dacia.co.uk/hybrid-range/spring-electric.html",
        "authority": "A",
        "region": "UK",
        "method": "品牌官网 HTML 解析（2026-09-11 实测可达 200）",
        "redistribution": "仅引用链接与事实",
        "notes": "竞品基线之一。英国价格最低的纯电城市车之一，作为价格下限锚点。",
    },
    "S-VX-01": {
        "name": "Vauxhall UK 官网 — Corsa Electric",
        "url": "https://www.vauxhall.co.uk/cars/corsa-electric.html",
        "authority": "A",
        "region": "UK",
        "method": "品牌官网 HTML 解析",
        "redistribution": "仅引用链接",
        "notes": "NOT_REACHABLE 2026-09-11 实测连接失败（网络/反爬），未纳入竞品基线。",
    },
    "S-CT-01": {
        "name": "Citroën UK 官网 — ë-C3",
        "url": "https://www.citroen.co.uk/new-cars/citroen-c3.html",
        "authority": "A",
        "region": "UK",
        "method": "品牌官网 HTML 解析",
        "redistribution": "仅引用链接",
        "notes": "NOT_REACHABLE 2026-09-11 实测 HTTP 403（反爬拦截），未纳入竞品基线。",
    },
    "S-GV-01": {
        "name": "GOV.UK — 电动汽车相关官方政策与税率页",
        "url": "https://www.gov.uk/",
        "authority": "A",
        "region": "UK",
        "method": "官方站点 HTML 解析",
        "redistribution": "政府公开信息，可引用",
        "notes": "政策与税率时效性强，每次更新必须重新核对生效日期。",
    },
}

# ---------------------------------------------------------------- 通用工具


def now_cst() -> datetime:
    return datetime.now(CST)


def iso(dt: datetime | None = None) -> str:
    return (dt or now_cst()).isoformat(timespec="seconds")


def today_cst() -> str:
    return now_cst().strftime("%Y-%m-%d")


def _curl_fallback(url: str, headers: dict | None, timeout: int,
                   data: bytes | None) -> tuple[int, bytes, str]:
    """urllib 在部分代理环境下会 502（Tunnel connection failed），curl 可正常通过。
    这是本机实测行为，故保留 curl 作为第二通道。"""
    import subprocess
    import tempfile
    cmd = ["curl", "-sL", "--max-time", str(timeout), "--noproxy", "*", "-o", "-",
           "-w", "\n__STATUS__%{http_code}", "-A", UA]
    for k, v in (headers or {}).items():
        cmd += ["-H", f"{k}: {v}"]
    if data is not None:
        cmd += ["--data", ""]
        cmd += ["-X", "POST"]
    cmd.append(url)
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=timeout + 10)
    except Exception as e:                            # noqa: BLE001
        return 0, b"", f"curl: {e}"
    out = p.stdout
    status = 0
    marker = b"\n__STATUS__"
    if marker in out:
        out, _, tail = out.rpartition(marker)
        try:
            status = int(tail.strip() or 0)
        except ValueError:
            status = 0
    if status == 0 and p.returncode != 0:
        return 0, out, f"curl exit={p.returncode}"
    return status, out, ""


def http_get(url: str, *, headers: dict | None = None, timeout: int = 30,
             data: bytes | None = None, retries: int = 3) -> tuple[int, bytes, str]:
    """返回 (status, body, error)。不抛异常，失败由上层记录状态。
    先试 urllib，失败则回退 curl。"""
    h = {"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
         "Accept": "*/*"}
    if headers:
        h.update(headers)
    ctx = ssl.create_default_context()
    last = ""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=h, data=data,
                                         method="POST" if data else "GET")
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return r.status, r.read(), ""
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}"
            if e.code in (403, 404):
                break
        except Exception as e:                      # noqa: BLE001
            last = f"{type(e).__name__}: {e}"
        time.sleep(0.6 * (attempt + 1))
    st, body, cerr = _curl_fallback(url, h, timeout, data)
    if st == 200 and body:
        return st, body, ""
    return st, body, f"{last} | {cerr}".strip(" |")


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def save_raw(name: str, body: bytes) -> str:
    p = RAW / name
    p.write_bytes(body)
    return str(p.relative_to(ROOT))


def load_state(name: str, default=None):
    p = STATE / f"{name}.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:                            # noqa: BLE001
            return default
    return default


def save_state(name: str, obj) -> None:
    (STATE / f"{name}.json").write_text(
        json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def log_line(msg: str) -> None:
    line = f"[{iso()}] {msg}"
    print(line)
    with (ROOT / "data" / "run.log").open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def rec(*, dataset_id: str, name: str, value, unit: str, region: str,
        scope: str, period: str, published: str | None, source_id: str,
        method: str, verified: str = "unverified",
        revision: str = "preliminary", note: str = "",
        display: str = "public") -> dict:
    """构造一条符合编号体系的数据记录。"""
    return {
        "dataset_id": dataset_id,
        "name": name,
        "value": value,
        "unit": unit,
        "region": region,
        "scope": scope,
        "period": period,
        "published": published,          # None = 未确认
        "retrieved": iso(),
        "source_id": source_id,
        "source_url": SOURCES[source_id]["url"],
        "method": method,
        "verified": verified,            # verified | single_authoritative | unverified | failed
        "revision": revision,            # preliminary | final | n/a
        "note": note,
        "display_permission": display,   # public | private | restricted
    }
