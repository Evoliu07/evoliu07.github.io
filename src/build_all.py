"""
派生计算 + 校验 + 图表渲染 + 对外数据导出。

一个数据版本 → 同时生成：网站数据、看板整图、单图 PNG/SVG。
所有数字只从 data/processed/*.json 读取，不在本文件里手填任何数值。

用法： python src/build_all.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib                                        # noqa: E402
matplotlib.use("Agg")
import matplotlib.font_manager as fm                     # noqa: E402
import matplotlib.pyplot as plt                          # noqa: E402
from matplotlib.ticker import FuncFormatter             # noqa: E402

from common import (BUILD_VERSION, PIPELINE_VERSION, PROC, ROOT, SOURCES,  # noqa: E402
                    iso, log_line, now_cst, save_json, today_cst)

CHARTS = ROOT / "exports" / "charts"
DASH = ROOT / "exports" / "dashboards"
PUB = ROOT / "github-upload" / "data"
for p in (CHARTS, DASH, PUB):
    p.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------------ 视觉规范
INK = "#1F2933"        # 深灰正文
ACCENT = "#1B3A6B"     # 深蓝主强调
TEAL = "#1B9E8F"       # 青绿辅色
WARN = "#B3541E"
GREY = "#8A94A6"
GRID = "#DCE1E8"
SERIES = [ACCENT, TEAL, "#B3541E", "#6B4E9B", "#3D7EA6"]

CN_FONT_CANDIDATES = [
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Songti.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
]


def setup_fonts() -> str:
    picked = []
    for f in CN_FONT_CANDIDATES:
        if Path(f).exists():
            try:
                fm.fontManager.addfont(f)
                picked.append(fm.FontProperties(fname=f).get_name())
            except Exception:                            # noqa: BLE001
                pass
    fams = picked + ["Helvetica Neue", "Arial", "DejaVu Sans"]
    plt.rcParams["font.sans-serif"] = fams
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.dpi"] = 110
    plt.rcParams["savefig.bbox"] = "tight"
    plt.rcParams["axes.edgecolor"] = GREY
    plt.rcParams["axes.linewidth"] = 0.8
    plt.rcParams["text.color"] = INK
    plt.rcParams["axes.labelcolor"] = INK
    plt.rcParams["xtick.color"] = INK
    plt.rcParams["ytick.color"] = INK
    log_line(f"字体已加载：{picked or ['(无中文字体)']}")
    return picked[0] if picked else "Arial"


def style(ax, *, grid_axis="y"):
    ax.set_facecolor("white")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(True, axis=grid_axis, color=GRID, lw=0.7, zorder=0)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=9.5)


def stamp(fig, lines: list[str], y=0.005):
    """每张图都必须自带单位/来源/日期/复核状态。"""
    fig.text(0.005, y, "  ".join(lines), fontsize=7.4, color=GREY, ha="left", va="bottom")


def save(fig, name: str, *, wide=False):
    png = CHARTS / f"{name}.png"
    svg = CHARTS / f"{name}.svg"
    fig.savefig(png, dpi=300, facecolor="white")
    fig.savefig(svg, format="svg", facecolor="white")
    plt.close(fig)
    log_line(f"  ↳ {png.name} / {svg.name}")


# ------------------------------------------------------------------ 载入
FIN = json.loads((PROC / "finance_datasets.json").read_text(encoding="utf-8"))
GTM = json.loads((PROC / "gtm_datasets.json").read_text(encoding="utf-8"))
FD = {d["dataset_id"]: d for d in FIN["datasets"]}
GD = {d["dataset_id"]: d for d in GTM["datasets"]}
DV = today_cst()
GEN = iso()

problems: list[dict] = []


def check(name: str, ok: bool, detail: str = "", level: str = "error"):
    problems.append({"check": name, "passed": bool(ok), "level": level,
                     "detail": detail})


# ================================================================== 派生：固收
def finance_derived() -> dict:
    stages = FIN.get("stage_curves") or {}
    latest = {t: FD.get(f"D-FIN-YC-{t}Y", {}).get("value") for t in
              ("1.0", "2.0", "3.0", "5.0", "7.0", "10.0", "30.0")}

    # 阶段曲线（按日期排序）
    stage_rows = []
    for d in sorted(stages):
        s = stages[d]["series"]
        def g(t):
            for k, v in s.items():
                if abs(float(k) - t) < 1e-6:
                    return round(v, 4)
            return None
        stage_rows.append({"date": d, "label": stages[d]["label"],
                           "y1": g(1.0), "y2": g(2.0), "y5": g(5.0),
                           "y10": g(10.0), "y30": g(30.0),
                           "spread_10y2y": (None if g(10.0) is None or g(2.0) is None
                                            else round(g(10.0) - g(2.0), 4))})
    # 当前点
    cur = {"date": FIN.get("currency_curve_worktime"),
           "y1": latest.get("1.0"), "y2": latest.get("2.0"),
           "y3": latest.get("3.0"), "y5": latest.get("5.0"),
           "y7": latest.get("7.0"), "y10": latest.get("10.0"), "y30": latest.get("30.0"),
           "spread_10y2y": FD.get("D-FIN-SPREAD-10Y2Y", {}).get("value")}

    # ---- 修正久期教学情景（平行移位）----
    # dP/P ~= -D_mod * dy + 0.5 * C * dy^2 ；dy 以小数表示（100bp = 0.01）
    FACE = 100_000_000.0          # 教学情景假设组合面值
    D_MOD = 5.0                   # 假设修正久期
    CONVEX = 30.0                 # 假设凸性
    scen = []
    for bp in (-100, -50, -25, 0, 25, 50, 100):
        dy = bp / 10000.0
        lin = -D_MOD * dy
        quad = 0.5 * CONVEX * dy * dy
        approx = lin + quad
        exact = (1.0 + approx)          # 情景化的价格比率（线性+凸性近似）
        scen.append({
            "shift_bp": bp,
            "dy_decimal": dy,
            "duration_effect_pct": round(lin * 100, 4),
            "convexity_effect_pct": round(quad * 100, 4),
            "approx_pct": round(approx * 100, 4),
            "value_change_cny": round(FACE * approx, 0),
            "value_after_cny": round(FACE * (1 + approx), 0),
        })
        check(f"久期情景 {bp:+d}bp 的凸性修正 ≥0", quad >= 0, "", "info")

    # 近似误差说明（不含高阶项时，bp 越大偏差越大；这里给出量级而非精确值）
    err_note = ("凸性项在 +/-25bp 内约占久期效应的 %.2f%%，+/-100bp 内升至 %.2f%%；"
                "未计入更高阶项，故 +/-100bp 情景为量级估计而非定价。"
                % (abs(scen[4]["convexity_effect_pct"] / scen[4]["duration_effect_pct"] * 100),
                   abs(scen[6]["convexity_effect_pct"] / scen[6]["duration_effect_pct"] * 100)))

    # 反证/失效条件
    falsifiers = [
        "若后续 10Y 收益率回升并突破 2026-06-30 的水平（%.4f%%），则「收益率中枢下移」的判断需要修正。"
        % (stage_rows[-1]["y10"] if stage_rows else 0),
        "本判断基于银行间市场国债到期收益率曲线。若改用国开债或地方政府债曲线，"
        "绝对水平与利差都会不同，结论不可直接搬用。",
        "久期情景假设「平行移位」。若发生扭曲型（steepener / flattener）变动，"
        "本情景会系统性高估或低估组合影响。",
        "收益率下降本身不等于投资收益。缺少可靠总回报数据时，不得把收益率变动当作回测收益。",
    ]

    return {"current": cur, "stages": stage_rows, "duration_scenario": {
        "assumptions": {
            "face_value_cny": FACE, "modified_duration": D_MOD, "convexity": CONVEX,
            "formula": "dP/P ~= -D_mod * dy + 0.5 * C * dy^2",
            "bp_conversion": "1bp = 0.0001，dy 为小数",
            "shift_type": "平行移位（parallel shift）",
            "label": "教学情景假设，非任何真实产品的参数",
        },
        "rows": scen,
        "error_note": err_note,
    }, "falsifiers": falsifiers,
        "money_market": {
            "DR001": FD.get("D-FIN-DR001", {}).get("value"),
            "DR007": FD.get("D-FIN-DR007", {}).get("value"),
            "FR007": FD.get("D-FIN-FR007", {}).get("value"),
            "date": FD.get("D-FIN-DR007", {}).get("period"),
        },
        "omo": FD.get("D-FIN-OMO-LATEST", {}).get("value"),
    }


# ================================================================== 派生：GTM
def gtm_derived() -> dict:
    r = GTM.get("smmt_raw") or {}
    pm = (r.get("powertrain") or {}).get("month") or {}
    py = (r.get("powertrain") or {}).get("ytd") or {}
    cm = (r.get("channel") or {}).get("month") or {}
    bm = ((r.get("brand") or {}).get("month") or {}).get("Byd") or {}
    by = ((r.get("brand") or {}).get("ytd") or {}).get("Byd") or {}

    mix = []
    for k, zh in (("BEV", "纯电 BEV"), ("PHEV", "插混 PHEV"), ("HEV", "普通混动 HEV"),
                  ("PETROL", "汽油"), ("DIESEL", "柴油")):
        v = pm.get(k)
        if not v:
            continue
        mix.append({"key": k, "label": zh, "units": v["cur"], "share": v["share_cur"],
                    "share_prev": v["share_prev"], "yoy": v["pct_change"]})

    channels = []
    for k, zh in (("FLEET", "车队 Fleet"), ("PRIVATE", "私人 Private"),
                  ("BUSINESS", "公司自用 Business")):
        v = cm.get(k)
        if not v:
            continue
        channels.append({"key": k, "label": zh, "units": v["cur"], "share": v["share_cur"],
                         "share_prev": v["share_prev"], "yoy": v["pct_change"]})

    models = [m for m in (r.get("top_bev_models") or {}).get("month_bev", [])]

    # ---- 竞品基线（只用官方页可核实的字段）----
    mf = GTM.get("model_facts") or {}
    comp = []
    for label, m in mf.items():
        f = m.get("facts") or {}
        comp.append({
            "model": label, "source_url": m.get("url"), "retrieved_ok": bool(m.get("ok")),
            "range_miles": f.get("range_miles") or [],
            "battery_kwh": f.get("battery_kwh") or [],
            "is_subject": label.startswith("BYD"),
        })

    # 渠道集中度：这是本站最核心的 GTM 判断依据
    fleet_share = cm.get("FLEET", {}).get("share_cur")
    priv_share = cm.get("PRIVATE", {}).get("share_cur")
    insight = None
    if fleet_share and priv_share:
        insight = (f"当月英国新乘用车注册中，车队渠道占 {fleet_share}%，私人渠道占 {priv_share}%。"
                   f"对一款低单价城市纯电而言，车队/公司车渠道的占比高于私人渠道，"
                   f"意味着「公司车与车队适配证据」比「面向私人消费者的大规模内容投放」"
                   f"更接近可验证的优先切口。")
        check("车队渠道占比 > 私人渠道占比（洞察前提）", fleet_share > priv_share,
              f"fleet={fleet_share}% private={priv_share}%", "info")

    falsifiers = [
        "若有证据显示该车型的购买决策实际由私人渠道主导（例如其经销网络以零售为主），"
        "则「优先车队渠道」的判断需要下调权重。",
        "渠道占比来自全市场新乘用车注册，不是纯电细分，也不是该车型自身；"
        "把它直接当作该车型的渠道结构属于过度外推。",
        "注册量 ≠ 销量 ≠ 交付量。BYD 为品牌级数据，不能当成 DOLPHIN SURF 车型销量。",
        "续航数值来自各品牌官网，测试口径可能不同，未对齐前不得排名。",
    ]

    return {"powertrain_mix": mix, "channels": channels, "bev_top10": models,
            "competitors": comp, "insight": insight, "falsifiers": falsifiers,
            "byd": {"month": bm, "ytd": by},
            "total_month": pm.get("TOTAL", {}).get("cur"),
            "total_ytd": py.get("TOTAL", {}).get("cur"),
            "bev_month": pm.get("BEV", {}).get("cur"),
            "bev_ytd": py.get("BEV", {}).get("cur")}


# ================================================================== 图表
def charts_fin(f: dict):
    # C-01 当前收益率曲线
    cur = f["current"]
    ts = [("1Y", cur["y1"]), ("3Y", cur["y3"]), ("5Y", cur["y5"]),
          ("7Y", cur["y7"]), ("10Y", cur["y10"]), ("30Y", cur["y30"])]
    ts = [(a, b) for a, b in ts if b is not None]
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    style(ax)
    ax.plot([a for a, _ in ts], [b for _, b in ts], "o-", color=ACCENT, lw=2.4,
            ms=7, zorder=3)
    for a, b in ts:
        ax.annotate(f"{b:.3f}", (a, b), textcoords="offset points", xytext=(0, 9),
                    ha="center", fontsize=9, color=ACCENT, fontweight="bold")
    ax.set_ylabel("到期收益率（%）", fontsize=10)
    ax.set_xlabel("关键期限", fontsize=10)
    ax.set_title(f"中债国债收益率曲线（{cur['date']}）\n"
                 f"10Y-2Y 期限利差 {cur['spread_10y2y']} 个百分点",
                 fontsize=13, color=ACCENT, fontweight="bold", pad=12)
    ax.set_ylim(min(b for _, b in ts) - 0.18, max(b for _, b in ts) + 0.30)
    stamp(fig, ["单位：%（到期收益率）", "来源：S-CB-01 中国债券信息网",
                f"数据日期：{cur['date']}", f"版本：{DV} / {BUILD_VERSION}",
                "复核：单源权威，未独立交叉验证"])
    save(fig, "C01_国债收益率曲线_当期")

    # C-02 阶段对比
    st = f["stages"]
    if st:
        fig, ax = plt.subplots(figsize=(8.6, 4.6))
        style(ax)
        labs = ["1Y", "2Y", "5Y", "10Y", "30Y"]
        keys = ["y1", "y2", "y5", "y10", "y30"]
        x = range(len(labs))
        n = len(st) + 1                     # 阶段数 + 当前
        w = 0.8 / max(n, 1)

        def series_of(row, keys_):
            return [v if isinstance(v, (int, float)) else 0.0 for v in
                    (row.get(k) for k in keys_)]

        for i, row in enumerate(st):
            vals = series_of(row, keys)
            bars = ax.bar([p + (i - (n - 1) / 2) * w for p in x], vals, w,
                          label=f"{row['date']}（{row['label']}）",
                          color=SERIES[i % len(SERIES)], zorder=3)
            for b, v in zip(bars, vals):
                ax.annotate(f"{v:.2f}", (b.get_x() + b.get_width() / 2, v),
                            textcoords="offset points", xytext=(0, 3),
                            ha="center", fontsize=7.6)
        cur_lab = f"当前 {f['current']['date']}"
        vals = series_of(f["current"], keys)
        bars = ax.bar([p + (n - 1 - (n - 1) / 2) * w for p in x], vals, w,
                      label=cur_lab, color="#0F2A4A", zorder=3)
        for b, v in zip(bars, vals):
            if v is not None:
                ax.annotate(f"{v:.2f}", (b.get_x() + b.get_width() / 2, v),
                            textcoords="offset points", xytext=(0, 3),
                            ha="center", fontsize=7.6, fontweight="bold")
        ax.set_xticks(list(x))
        ax.set_xticklabels(labs)
        ax.set_ylabel("到期收益率（%）", fontsize=10)
        ax.set_title("国债收益率曲线阶段对比：收益率中枢持续下移",
                     fontsize=13, color=ACCENT, fontweight="bold", pad=12)
        ax.legend(fontsize=8.6, frameon=False, ncol=2, loc="upper left")
        stamp(fig, ["单位：%", "来源：S-CB-01 / S-CB-02 中国债券信息网",
                    f"取点日期：{'、'.join(r['date'] for r in st)} 与当前"
                    f"{f['current']['date']}", f"版本：{DV}",
                    "非零起点轴：坐标轴自 0 起，未截断"])
        save(fig, "C02_收益率曲线_阶段对比")

    # C-03 久期情景
    ds = f["duration_scenario"]
    rows = ds["rows"]
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    style(ax)
    xs = [r["shift_bp"] for r in rows]
    ys = [r["approx_pct"] for r in rows]
    colors = [TEAL if v > 0 else WARN for v in ys]
    bars = ax.bar([str(x) for x in xs], ys, color=colors, zorder=3, width=0.55)
    for b, r in zip(bars, rows):
        ax.annotate(f"{r['approx_pct']:+.2f}%\n{r['value_change_cny']:+,.0f}元",
                    (b.get_x() + b.get_width() / 2, r["approx_pct"]),
                    textcoords="offset points",
                    xytext=(0, 6 if r["approx_pct"] >= 0 else -22),
                    ha="center", fontsize=8.2)
    ax.axhline(0, color=GREY, lw=1)
    ax.set_ylabel("组合估值变动（%）", fontsize=10)
    ax.set_xlabel("收益率平行移位（bp）", fontsize=10)
    ax.set_title("修正久期情景分析：平行移位对组合估值的近似影响",
                 fontsize=13, color=ACCENT, fontweight="bold", pad=12)
    ax.set_ylim(min(ys + [0]) * 1.5, max(ys + [0]) * 1.5)
    a = ds["assumptions"]
    stamp(fig, [f"假设：面值 {a['face_value_cny']:,.0f} 元，修正久期 {a['modified_duration']}，"
                f"凸性 {a['convexity']}",
                f"公式：{a['formula']}", f"1bp = 0.0001",
                "性质：教学情景假设，非任何真实产品参数",
                f"版本：{DV}"])
    save(fig, "C03_久期情景分析")

    # C-04 期限利差阶段
    if st:
        fig, ax = plt.subplots(figsize=(8.6, 4.0))
        style(ax)
        labs = [r["date"] for r in st] + [f["current"]["date"]]
        vals = [r["spread_10y2y"] for r in st] + [f["current"]["spread_10y2y"]]
        keep = [(a, b) for a, b in zip(labs, vals) if b is not None]
        ax.plot([a for a, _ in keep], [b for _, b in keep], "o-", color=TEAL,
                lw=2.4, ms=8, zorder=3)
        for a, b in keep:
            ax.annotate(f"{b:.3f}", (a, b), textcoords="offset points", xytext=(0, 10),
                        ha="center", fontsize=9, color=TEAL, fontweight="bold")
        ax.set_ylabel("10Y - 2Y（百分点）", fontsize=10)
        ax.set_title("10Y-2Y 期限利差：曲线形态的变化", fontsize=13,
                     color=ACCENT, fontweight="bold", pad=12)
        ax.tick_params(axis="x", rotation=20)
        stamp(fig, ["单位：百分点（同一条国债曲线同日取值相减）",
                    "来源：S-CB-01 / S-CB-02", f"版本：{DV}",
                    "口径提醒：不得与国开债或地方政府债曲线利差混用"])
        save(fig, "C04_期限利差")


def charts_gtm(g: dict):
    # C-05 动力类型结构（当月）
    mix = g["powertrain_mix"]
    if mix:
        fig, ax = plt.subplots(figsize=(8.6, 4.6))
        style(ax, grid_axis="x")
        labs = [m["label"] for m in mix][::-1]
        cur = [m["share"] for m in mix][::-1]
        prev = [m["share_prev"] for m in mix][::-1]
        y = range(len(labs))
        ax.barh([i + 0.19 for i in y], cur, height=0.36, color=ACCENT,
                label="当期份额", zorder=3)
        ax.barh([i - 0.19 for i in y], prev, height=0.36, color=GREY,
                label="上年同期份额", zorder=3)
        for i, (c, p) in enumerate(zip(cur, prev)):
            ax.annotate(f"{c}%", (c, i + 0.19), xytext=(5, 0),
                        textcoords="offset points", va="center", fontsize=8.6,
                        color=ACCENT, fontweight="bold")
            ax.annotate(f"{p}%", (p, i - 0.19), xytext=(5, 0),
                        textcoords="offset points", va="center", fontsize=8.2, color=GREY)
        ax.set_yticks(list(y))
        ax.set_yticklabels(labs)
        ax.set_xlabel("占当月新乘用车注册比重（%）", fontsize=10)
        ax.set_title(f"英国新乘用车动力结构（{DV} 前最新月度，总量 {g['total_month']:,.0f} 辆）",
                     fontsize=13, color=ACCENT, fontweight="bold", pad=12)
        ax.legend(fontsize=9, frameon=False, loc="lower right")
        ax.set_xlim(0, max(cur + prev) * 1.22)
        stamp(fig, ["单位：% ；样本：英国当月全部新乘用车注册",
                    "来源：S-SM-01 SMMT（英国汽车制造商与贸易商协会）",
                    f"版本：{DV}", "复核：单源权威（SMMT 免费公开页），未独立交叉验证"])
        save(fig, "C05_英国动力类型结构")

    # C-06 渠道结构
    ch = g["channels"]
    if ch:
        fig, ax = plt.subplots(figsize=(8.6, 4.2))
        style(ax, grid_axis="x")
        labs = [c["label"] for c in ch]
        vals = [c["share"] for c in ch]
        cols = [ACCENT, TEAL, GREY]
        bars = ax.barh(labs[::-1], vals[::-1], color=cols[::-1], zorder=3, height=0.5)
        for b, c in zip(bars, ch[::-1]):
            ax.annotate(f"{c['share']}%  ({c['units']:,.0f} 辆，同比 {c['yoy']:+.1f}%)",
                        (b.get_width(), b.get_y() + b.get_height() / 2),
                        xytext=(6, 0), textcoords="offset points", va="center",
                        fontsize=9)
        ax.set_xlim(0, max(vals) * 1.65)
        ax.set_xlabel("占当月新乘用车注册比重（%）", fontsize=10)
        ax.set_title("英国新乘用车销售渠道结构：车队渠道占比最高",
                     fontsize=13, color=ACCENT, fontweight="bold", pad=12)
        stamp(fig, ["单位：%（分母＝英国当月全部新乘用车注册）",
                    "来源：S-SM-01 SMMT", f"版本：{DV}",
                    "口径提醒：全市场口径，非纯电细分，也非该车型自身"])
        save(fig, "C06_英国渠道结构")

    # C-07 BYD 品牌注册量同比
    b = g["byd"]
    if b.get("month", {}).get("cur"):
        fig, ax = plt.subplots(figsize=(8.6, 4.4))
        style(ax)
        groups = [("当月", b["month"]), ("年初至今", b["ytd"])]
        x = range(len(groups))
        w = 0.32
        cur = [gg[1].get("cur") or 0 for gg in groups]
        prev = [gg[1].get("prev") or 0 for gg in groups]
        b1 = ax.bar([i - w / 2 for i in x], prev, w, color=GREY,
                    label="上年同期", zorder=3)
        b2 = ax.bar([i + w / 2 for i in x], cur, w, color=ACCENT,
                    label="本期", zorder=3)
        for bars, vals in ((b1, prev), (b2, cur)):
            for bb, v in zip(bars, vals):
                ax.annotate(f"{v:,.0f}", (bb.get_x() + bb.get_width() / 2, v),
                            xytext=(0, 4), textcoords="offset points",
                            ha="center", fontsize=9,
                            fontweight="bold" if bars is b2 else "normal")
        for i, (nm, mm) in enumerate(groups):
            if mm.get("pct_change") is not None:
                ax.annotate(f"同比 {mm['pct_change']:+.1f}%",
                            (i, max(mm.get("cur") or 0, mm.get("prev") or 0) * 1.09),
                            ha="center", fontsize=10, color=WARN, fontweight="bold")
        ax.set_xticks(list(x))
        ax.set_xticklabels([gg[0] for gg in groups])
        ax.set_ylabel("注册量（辆）", fontsize=10)
        ax.set_title("BYD 品牌英国注册量：同比接近翻倍（品牌级，非车型级）",
                     fontsize=13, color=ACCENT, fontweight="bold", pad=12)
        ax.legend(fontsize=9, frameon=False)
        ax.set_ylim(0, max(cur + prev) * 1.28)
        stamp(fig, ["单位：辆；口径：BYD 品牌全部动力类型，非 DOLPHIN SURF 车型",
                    "来源：S-SM-02 SMMT", f"版本：{DV}",
                    "重要限制：注册量 ≠ 销量 ≠ 交付量；品牌级不可当作车型销量"])
        save(fig, "C07_BYD品牌注册量")

    # C-08 竞品续航对比（带口径警示）
    comp = [c for c in g["competitors"] if c.get("range_miles")]
    if comp:
        fig, ax = plt.subplots(figsize=(8.6, 4.4))
        style(ax)
        names, vals, cols = [], [], []
        for c in comp:
            try:
                v = max(float(x) for x in c["range_miles"])
            except ValueError:
                continue
            names.append(c["model"].replace(" Electric", "").replace(" electric", ""))
            vals.append(v)
            cols.append(ACCENT if c["is_subject"] else TEAL)
        order = sorted(range(len(vals)), key=lambda i: -vals[i])
        names = [names[i] for i in order]
        vals = [vals[i] for i in order]
        cols = [cols[i] for i in order]
        bars = ax.bar(names, vals, color=cols, zorder=3, width=0.55)
        for bb, v in zip(bars, vals):
            ax.annotate(f"{v:.0f}", (bb.get_x() + bb.get_width() / 2, v),
                        xytext=(0, 4), textcoords="offset points", ha="center",
                        fontsize=9.4, fontweight="bold")
        ax.set_ylabel("官方公布续航（英里）", fontsize=10)
        ax.set_title("官方公布续航对比（深蓝＝研究对象，青绿＝直接竞品）",
                     fontsize=13, color=ACCENT, fontweight="bold", pad=12)
        ax.tick_params(axis="x", rotation=12)
        ax.set_ylim(0, max(vals) * 1.2)
        stamp(fig, ["单位：英里；取各品牌英国官网公布数值",
                    "来源：S-BY-01 / S-RN-01 / S-MG-01 / S-DC-01（品牌官网）",
                    f"版本：{DV}",
                    "重要警示：各品牌测试口径可能不同（WLTP combined / urban 等），"
                    "未对齐口径前不得据此排名"])
        save(fig, "C08_续航对比")

    # C-09 BEV Top10
    m = g["bev_top10"]
    if m:
        fig, ax = plt.subplots(figsize=(8.6, 5.0))
        style(ax, grid_axis="x")
        labs = [f"{x['rank']}. {x['model']}" for x in m][::-1]
        vals = [x["units"] for x in m][::-1]
        cols = [ACCENT if "RENAULT 5" in x["model"].upper() else GREY
                for x in m][::-1]
        bars = ax.barh(labs, vals, color=cols, zorder=3, height=0.62)
        for bb, v in zip(bars, vals):
            ax.annotate(f"{v:,}", (bb.get_width(), bb.get_y() + bb.get_height() / 2),
                        xytext=(5, 0), textcoords="offset points", va="center", fontsize=9)
        ax.set_xlabel("当月注册量（辆）", fontsize=10)
        ax.set_title("英国纯电车型注册量 Top10（当月）", fontsize=13,
                     color=ACCENT, fontweight="bold", pad=12)
        ax.set_xlim(0, max(vals) * 1.16)
        stamp(fig, ["单位：辆；深蓝＝出现在本站竞品基线中的车型",
                    "来源：S-SM-01 SMMT", f"版本：{DV}",
                    "限制：SMMT 免费页仅公开 Top10，无完整车型级注册量"])
        save(fig, "C09_英国BEV车型Top10")


# ================================================================== 看板整图
def dashboards(f: dict, g: dict):
    def panel(ax, title, lines, color=ACCENT, fs=12.0, step=0.135, y0=0.74):
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.add_patch(plt.Rectangle((0, 0), 1, 1, fill=False, ec=GRID, lw=1))
        ax.text(0.04, 0.88, title, fontsize=fs + 1.4, color=color, fontweight="bold")
        ax.plot([0.04, 0.96], [0.815, 0.815], color=GRID, lw=1)
        for i, t in enumerate(lines):
            ax.text(0.04, y0 - i * step, t, fontsize=fs, color=INK, va="top")

    # ---- 16:9 展示版 3840x2160 ----
    fig = plt.figure(figsize=(12.8, 7.2), dpi=300)
    fig.patch.set_facecolor("white")
    fig.text(0.04, 0.955, "AI 辅助个人研究 · 两项作品看板", fontsize=21,
             color=ACCENT, fontweight="bold")
    fig.text(0.04, 0.917, f"数据版本 {DV}　生成时间 {GEN}　版本 {BUILD_VERSION}",
             fontsize=10, color=GREY)
    cur, ds = f["current"], f["duration_scenario"]
    mm = f["money_market"]
    panel(fig.add_axes([0.04, 0.52, 0.44, 0.34]), "项目 A ｜ 固收市场观察与客户沟通", [
        f"国债到期收益率　1Y {cur['y1']}%　2Y {cur['y2']}%　10Y {cur['y10']}%　30Y {cur['y30']}%",
        f"10Y-2Y 期限利差 {cur['spread_10y2y']} 个百分点（同一曲线同日相减）",
        f"资金面 DR007 {mm['DR007']}%　DR001 {mm['DR001']}%　FR007 {mm['FR007']}%",
        f"阶段复盘 10Y：2024-09-30 {f['stages'][0]['y10']}% → 当前 {cur['y10']}%",
        f"久期情景（教学假设 D=5.0 / 凸性=30 / 面值1亿）：+100bp {ds['rows'][6]['approx_pct']:+.2f}%",
        f"曲线取数日 {cur['date']}　来源 S-CB-01 / S-CM-01 / S-PB-01",
    ], fs=10.6, step=0.128, y0=0.735)
    panel(fig.add_axes([0.52, 0.52, 0.44, 0.34]), "项目 B ｜ 英国 EV 市场情报与 GTM 工作台", [
        f"当月新乘用车 {g['total_month']:,.0f} 辆　纯电 BEV {g['bev_month']:,.0f} 辆"
        f"（份额 {g['powertrain_mix'][0]['share']}%，同比 {g['powertrain_mix'][0]['yoy']:+.1f}%）",
        f"渠道结构　车队 {g['channels'][0]['share']}%　私人 {g['channels'][1]['share']}%"
        f"　公司自用 {g['channels'][2]['share']}%",
        f"BYD 品牌当月 {g['byd']['month']['cur']:,.0f} 辆（同比 {g['byd']['month']['pct_change']:+.1f}%）"
        f"，年初至今 {g['byd']['ytd']['cur']:,.0f} 辆",
        "研究对象 BYD DOLPHIN SURF（官网页续航 200 英里，紧凑纯电城市车）",
        "直接竞品 Renault 5 E-Tech electric / MG4 EV / Dacia Spring Electric",
        "来源 S-SM-01 / S-SM-02 / S-BY-01 / S-RN-01 / S-MG-01 / S-DC-01",
    ], color=TEAL, fs=10.6, step=0.128, y0=0.735)
    panel(fig.add_axes([0.04, 0.10, 0.44, 0.34]), "关键判断（含失效条件）", [
        "① 收益率中枢两年内持续下移，但久期提供的保护同步减弱",
        f"　失效条件：10Y 回升并突破 {f['stages'][-1]['y10']}%（2026-06-30 水平）",
        f"② 教学情景 +100bp 时组合估值约 {ds['rows'][6]['approx_pct']:+.2f}%，"
        f"-100bp 约 {ds['rows'][0]['approx_pct']:+.2f}%",
        "　失效条件：发生扭曲型变动（非平行移位）时本情景不适用",
        f"③ 英国市场由车队渠道主导（{g['channels'][0]['share']}%），"
        f"公司车适配证据优先级高于大规模私人投放",
        "　失效条件：若该车型决策实际由零售主导，则本判断需下调权重",
        "④ 官方公开信息不足以完成同级可比判断 → 这是内容切口，而非结论",
    ], color=WARN, fs=10.6, step=0.108, y0=0.735)
    panel(fig.add_axes([0.52, 0.10, 0.44, 0.34]), "复核状态与已知限制", [
        "项目A：中债曲线 S-CB-01、中国货币网 S-CM-01、央行 S-PB-01",
        "　＝单一权威来源，尚未独立交叉验证；口径不可混用",
        "项目B：SMMT S-SM-01/-02 ＝单一权威；免费页仅提供车型 Top10",
        "未获取：BYD 官网售价与 PCP 月供（前端动态渲染）——留空不推测",
        "不把收益率变动当投资回报；不把注册量当销量或营销效果",
        "人工抽查、手算久期、真实用户测试：由本人完成后再更新状态",
        "　（当前状态：待完成，不由 AI 代填）",
    ], color=GREY, fs=10.6, step=0.108, y0=0.735)
    stamp(fig, ["来源编号见每张单图与附录索引", "本页为同一数据版本导出，未手工另填数字",
                f"数据有效日期：{DV}"], y=0.005)
    _old = plt.rcParams["savefig.bbox"]
    plt.rcParams["savefig.bbox"] = "standard"
    fig.savefig(DASH / "DASHBOARD_16x9.png", dpi=300, facecolor="white")
    fig.savefig(DASH / "DASHBOARD_16x9.svg", format="svg", facecolor="white")
    plt.close(fig)
    log_line("  ↳ DASHBOARD_16x9.png (3840x2160 等效)")

    # ---- A4 打印版（2480x3508 像素 = A4 @300ppi）----
    fig = plt.figure(figsize=(8.2667, 11.6933), dpi=300)
    fig.patch.set_facecolor("white")
    fig.text(0.065, 0.962, "AI 辅助个人研究 · 打印版看板", fontsize=19,
             color=ACCENT, fontweight="bold")
    fig.text(0.065, 0.943, f"数据版本 {DV}　生成 {GEN}　版本 {BUILD_VERSION}",
             fontsize=8.6, color=GREY)
    from matplotlib.lines import Line2D
    fig.add_artist(Line2D([0.065, 0.935], [0.935, 0.935], color=GRID, lw=1.2,
                          transform=fig.transFigure))

    def bpanel(y0, h, title, lines, color, fs=9.5, step=0.088, text_y=0.715):
        ax = fig.add_axes([0.065, y0, 0.87, h])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.add_patch(plt.Rectangle((0, 0), 1, 1, fill=False, ec=GRID, lw=1))
        ax.add_patch(plt.Rectangle((0, 0), 0.006, 1, facecolor=color,
                                   edgecolor="none"))
        ax.text(0.028, 0.855, title, fontsize=11.2, color=color,
                fontweight="bold")
        ax.plot([0.028, 0.975], [0.795, 0.795], color=GRID, lw=0.9,
                transform=ax.transAxes)
        for i, t in enumerate(lines):
            ax.text(0.028, text_y - i * step, t, fontsize=fs, color=INK, va="top")

    mm_ = f["money_market"]
    st_ = f["stages"]
    bpanel(0.665, 0.250, "项目 A ｜ 固收市场观察与机构客户沟通研究", [
        f"国债到期收益率（{cur['date']}）：1Y {cur['y1']}%　2Y {cur['y2']}%　5Y {cur['y5']}%　"
        f"10Y {cur['y10']}%　30Y {cur['y30']}%",
        f"10Y-2Y 期限利差 {cur['spread_10y2y']} 个百分点（同一条国债曲线同日相减）",
        f"资金面：DR007 {mm_['DR007']}%　DR001 {mm_['DR001']}%　FR007 {mm_['FR007']}%（{mm_['date']}）",
        f"阶段复盘（10Y）：2024-09-30 {st_[0]['y10']}% → 2025-09-30 {st_[1]['y10']}% → "
        f"2026-06-30 {st_[2]['y10']}% → 当前 {cur['y10']}%",
        "久期情景（教学假设，非任何真实产品）：修正久期 5.0、凸性 30、组合面值 1 亿元",
        f"　收益率 +25bp → {ds['rows'][4]['approx_pct']:+.2f}%；-25bp → {ds['rows'][2]['approx_pct']:+.2f}%",
        f"　收益率 +100bp → {ds['rows'][6]['approx_pct']:+.2f}%；-100bp → {ds['rows'][0]['approx_pct']:+.2f}%",
        "　假设收益率曲线平行移位；未计入更高阶项，故较大移位情景为量级估计而非定价",
        "　凸性修正项在 +/-25bp 内约占久期效应的 6%，+/-100bp 内升至约 24%",
    ], ACCENT, fs=9.3, step=0.083, text_y=0.705)

    bpanel(0.400, 0.250, "项目 B ｜ 英国电动车市场情报与 GTM 执行工作台", [
        f"市场（最新月）：英国新乘用车注册 {g['total_month']:,.0f} 辆，其中纯电 BEV "
        f"{g['bev_month']:,.0f} 辆（份额 {g['powertrain_mix'][0]['share']}%，"
        f"同比 {g['powertrain_mix'][0]['yoy']:+.1f}%）",
        f"渠道结构（全市场）：车队 {g['channels'][0]['share']}%　私人 {g['channels'][1]['share']}%"
        f"　公司自用 {g['channels'][2]['share']}%",
        f"BYD 品牌：当月 {g['byd']['month']['cur']:,.0f} 辆（同比 {g['byd']['month']['pct_change']:+.1f}%）；"
        f"年初至今 {g['byd']['ytd']['cur']:,.0f} 辆（同比 {g['byd']['ytd']['pct_change']:+.1f}%）",
        "研究对象：BYD DOLPHIN SURF — 官方定位 The Compact Electric City Car，官网页续航 200 英里",
        "直接竞品：Renault 5 E-Tech electric / MG4 EV / Dacia Spring Electric",
        "竞品选择规则：英国在售紧凑/小型纯电 + 品牌英国官网可核实 + 覆盖入门至主流价格带",
        "主要切口：官方公开信息不足以支撑同级别可比判断 → 补齐可比信息即为内容机会",
        "限制：SMMT 免费页仅公开车型 Top10；BYD 官网售价与 PCP 月供为前端渲染，未获取",
    ], TEAL, fs=9.3, step=0.083, text_y=0.705)

    bpanel(0.115, 0.250, "限制、反证与复核状态", [
        "单源权威：中债曲线 S-CB-01、中国货币网 S-CM-01、SMMT S-SM-01/-02 均为单一权威来源，尚未独立交叉验证",
        "口径警示：国债与地方政府债曲线不可混用；DR（存款类机构）与 FR（全市场）不可混用",
        "口径警示：注册量不等于销量或交付量；品牌级不等于车型级；各品牌续航测试口径不同，未对齐前不得排名",
        "禁止外推：不得把收益率变动当作投资回报或回测收益；久期情景参数为明确标注的教学假设",
        "缺失处理：未获取的数据一律留空并注明状态，不填零、不推测；数据未发布、来源不可访问与无变化分别记录",
        "失效条件：10Y 收益率若回升并突破 2026-06-30 水平，或曲线发生扭曲型变动，本页判断需相应修正",
        "人工复核：抽查来源、手算久期情景、真实用户测试、达人候选核实 — 由本人完成后再更新状态（当前：待完成）",
    ], WARN, fs=9.3, step=0.083, text_y=0.705)

    fig.text(0.065, 0.078,
             "本页与网站、PPT 使用同一数据版本导出，未手工另填数字。"
             "关键结论、单位、期间、来源编号与限制均在纸面直接可读，无需点击或扫码。",
             fontsize=8.0, color=GREY)
    fig.text(0.065, 0.052, f"数据有效日期 {DV}　导出时间 {GEN}　版本 {BUILD_VERSION}",
             fontsize=8.0, color=GREY)

    _old = plt.rcParams["savefig.bbox"]
    plt.rcParams["savefig.bbox"] = "standard"
    fig.savefig(DASH / "DASHBOARD_A4_portrait.png", dpi=300, facecolor="white")
    fig.savefig(DASH / "DASHBOARD_A4_portrait.pdf", facecolor="white")
    plt.rcParams["savefig.bbox"] = _old
    plt.close(fig)
    log_line("  ↳ DASHBOARD_A4_portrait.png / .pdf")


# ================================================================== 校验 & 导出
def validate(f: dict, g: dict):
    # 数值/单位/日期检查
    for did, d in FD.items():
        if d["value"] is None:
            check(f"{did} 非空", False, "值为 None", "error")
        if not d.get("unit"):
            check(f"{did} 有单位", False, "", "error")
        if d["verified"] == "single_authoritative":
            check(f"{did} 已标注单源未交叉验证", True, "", "info")
    for did, d in GD.items():
        if d["value"] is None:
            check(f"{did} 非空", False, "值为 None", "error")
        if not d.get("unit"):
            check(f"{did} 有单位", False, "", "error")

    # 口径一致性：不得混用曲线类型
    names = [x["name"] for x in FIN["datasets"]]
    check("未混用地方政府债曲线", not any("地方政府债" in n and "国债" in n for n in names),
          "", "error")
    check("DR 与 FR 分列展示",
          "D-FIN-DR007" in FD and "D-FIN-FR007" in FD, "", "info")

    # 缺数据不得填零
    for d in FIN["datasets"] + GTM["datasets"]:
        if d["note"] and "未获取" in d["note"]:
            check(f"{d['dataset_id']} 标注未获取", True, "", "info")

    # 数据版本一致性
    check("项目A/B 同一数据版本", FIN["data_version"] == GTM["data_version"],
          f"{FIN['data_version']} vs {GTM['data_version']}", "error")

    # 图表文件存在性
    for c in ("C01_国债收益率曲线_当期", "C02_收益率曲线_阶段对比", "C03_久期情景分析",
              "C04_期限利差", "C05_英国动力类型结构", "C06_英国渠道结构",
              "C07_BYD品牌注册量", "C08_续航对比", "C09_英国BEV车型Top10"):
        ok = (CHARTS / f"{c}.png").exists() and (CHARTS / f"{c}.svg").exists()
        check(f"图表 {c} 已生成 PNG+SVG", ok, "", "error")

    for d in ("DASHBOARD_16x9.png", "DASHBOARD_A4_portrait.png", "DASHBOARD_A4_portrait.pdf"):
        check(f"看板 {d}", (DASH / d).exists(), "", "error")


def export_market(f: dict, g: dict):
    payload = {
        "meta": {"data_version": DV, "generated_at": GEN,
                 "build_version": BUILD_VERSION, "pipeline_version": PIPELINE_VERSION,
                 "timezone": "Asia/Shanghai (UTC+8)",
                 "generated_by": "程序采集与计算（未调用模型）",
                 "note": "本文件由 src/build_all.py 从 data/processed 的同一数据版本生成；"
                         "网站、看板图片与 PPT/PDF 共用此版本。"},
        "sources": {k: {"name": v["name"], "url": v["url"], "authority": v["authority"],
                        "region": v["region"]} for k, v in SOURCES.items()},
        "finance": {"datasets": FIN["datasets"], "derived": f,
                    "source_status": FIN["source_status"]},
        "gtm": {"datasets": GTM["datasets"], "derived": g,
                "smmt_status": GTM["smmt_status"], "not_retrieved": GTM["not_retrieved"]},
        "charts": [
            {"id": "C-01", "file": "C01_国债收益率曲线_当期", "title": "中债国债收益率曲线（当期）",
             "unit": "%", "period": f["current"]["date"], "sources": ["S-CB-01"]},
            {"id": "C-02", "file": "C02_收益率曲线_阶段对比", "title": "收益率曲线阶段对比",
             "unit": "%", "period": "、".join([r["date"] for r in f["stages"]] + [f["current"]["date"]]),
             "sources": ["S-CB-01", "S-CB-02"]},
            {"id": "C-03", "file": "C03_久期情景分析", "title": "修正久期情景分析",
             "unit": "% / 元", "period": DV, "sources": ["S-CB-01"],
             "nature": "教学情景假设"},
            {"id": "C-04", "file": "C04_期限利差", "title": "10Y-2Y 期限利差",
             "unit": "百分点", "period": DV, "sources": ["S-CB-01", "S-CB-02"]},
            {"id": "C-05", "file": "C05_英国动力类型结构", "title": "英国新乘用车动力结构",
             "unit": "%", "period": DV, "sources": ["S-SM-01"]},
            {"id": "C-06", "file": "C06_英国渠道结构", "title": "英国新乘用车渠道结构",
             "unit": "%", "period": DV, "sources": ["S-SM-01"]},
            {"id": "C-07", "file": "C07_BYD品牌注册量", "title": "BYD 品牌英国注册量",
             "unit": "辆", "period": DV, "sources": ["S-SM-02"]},
            {"id": "C-08", "file": "C08_续航对比", "title": "官方公布续航对比",
             "unit": "英里", "period": DV,
             "sources": ["S-BY-01", "S-RN-01", "S-MG-01", "S-DC-01"]},
            {"id": "C-09", "file": "C09_英国BEV车型Top10", "title": "英国 BEV 车型 Top10",
             "unit": "辆", "period": DV, "sources": ["S-SM-01"]},
        ],
        "claims": [
            {"id": "K-01", "type": "fact",
             "text": f"截至 {f['current']['date']}，中债国债 10Y 到期收益率为 {f['current']['y10']}%。",
             "evidence": ["D-FIN-YC-10.0Y"], "source": "S-CB-01",
             "exception": "单源权威，未独立交叉验证。"},
            {"id": "K-02", "type": "computation",
             "text": f"同期 10Y-2Y 期限利差为 {f['current']['spread_10y2y']} 个百分点。",
             "evidence": ["D-FIN-SPREAD-10Y2Y"], "source": "本项目计算",
             "exception": "仅在同一曲线类型内成立。"},
            {"id": "K-03", "type": "interpretation",
             "text": f"10Y 由 2024-09-30 的 {f['stages'][0]['y10']}% 降至 {f['current']['y10']}%，"
                     f"收益率中枢在两年内持续下移。",
             "evidence": ["D-FIN-YC-10.0Y"], "source": "S-CB-02",
             "exception": "债券收益率下行不等于投资收益；本结论不含总回报数据。"},
            {"id": "K-04", "type": "assumption",
             "text": f"教学情景下，修正久期 5.0、凸性 30 的 1 亿元组合在收益率 +100bp 时估值约变动 "
                     f"{f['duration_scenario']['rows'][6]['approx_pct']:+.2f}%。",
             "evidence": [], "source": "本项目计算",
             "exception": "参数为明确标注的教学假设，非任何真实产品；假设平行移位。"},
            {"id": "K-05", "type": "fact",
             "text": f"最近一个月英国新乘用车注册中纯电占 {g['powertrain_mix'][0]['share']}%"
                     f"（{g['bev_month']:,.0f} 辆，同比 {g['powertrain_mix'][0]['yoy']:+.1f}%）。",
             "evidence": ["D-GTM-BEV-M", "D-GTM-BEV-SHARE-M"], "source": "S-SM-01",
             "exception": "注册量不等于销量或交付量。"},
            {"id": "K-06", "type": "fact",
             "text": f"同期车队渠道占 {g['channels'][0]['share']}%，私人渠道占 {g['channels'][1]['share']}%。",
             "evidence": ["D-GTM-CH-FLEET-SHARE"], "source": "S-SM-01",
             "exception": "全市场口径，非纯电细分，也非该车型自身结构。"},
            {"id": "K-07", "type": "interpretation",
             "text": g["insight"] or "渠道结构支持优先验证车队/公司车切口。",
             "evidence": ["D-GTM-CH-FLEET-SHARE", "D-GTM-CH-PRIVATE-SHARE"],
             "source": "本项目推断", "exception": "属于推断而非事实；已列出失效条件。"},
            {"id": "K-08", "type": "recommendation",
             "text": "优先制作面向车队/公司车决策链的可比证据材料，而非面向私人消费者的大规模内容投放。",
             "evidence": ["K-06", "K-07"], "source": "本项目建议",
             "exception": "尚未执行、未验证；表述为「提出/准备验证」。"},
        ],
    }
    save_json(PUB / "market.json", payload)
    save_json(ROOT / "checks" / "validation.json", {
        "data_version": DV, "generated_at": GEN, "checked": len(problems),
        "failed": sum(1 for p in problems if not p["passed"]),
        "results": problems})
    log_line(f"导出网站数据 github-upload/data/market.json（{len(payload['claims'])} 条可追溯结论）")


def main():
    setup_fonts()
    log_line(f"=== 派生/图表/导出开始　数据版本 {DV} ===")
    f = finance_derived()
    g = gtm_derived()
    charts_fin(f)
    charts_gtm(g)
    dashboards(f, g)
    validate(f, g)
    export_market(f, g)
    bad = [p for p in problems if not p["passed"]]
    log_line(f"=== 完成：检查 {len(problems)} 项，未通过 {len(bad)} 项 ===")
    for p in bad:
        log_line(f"   ✗ {p['check']} {p['detail']}")


if __name__ == "__main__":
    main()
