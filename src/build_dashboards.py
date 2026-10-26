"""
生成两个看板（每块两个项目）：

  dashboard.html —— 金融看板
    项目一 利率研究（实时市场与利率读数 + 国债收益率曲线 + 期限变动 + 公开市场公告）
    项目二 银行客户经营建模（名额方案对照 + 模型 vs 规则 + 方法说明）

  overseas.html —— 出海看板
    项目一 比亚迪（英国）：SMMT 注册数据 + 中国品牌表现 + 竞品官方规格
    项目二 徕芬（德国）：市场进入决策框架与五个模块

用法： python src/build_dashboards.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, log_line                                    # noqa: E402

import plotly.graph_objects as go                                    # noqa: E402
from plotly.io import to_html                                        # noqa: E402

FIN = json.loads((ROOT / "data" / "dash" / "dashboard.json").read_text(encoding="utf-8"))
RT = json.loads((ROOT / "data" / "dash" / "market_rt.json").read_text(encoding="utf-8"))
SEA = json.loads((ROOT / "data" / "dash" / "overseas.json").read_text(encoding="utf-8"))

# 银行客户经营建模：数值取自 research-note.md / results.json
# （UCI Bank Marketing 公开数据集，固定种子 20260911，可复现）
BANK = {
    "records": 41188, "train": 24712, "valid": 8238, "test": 8238,
    "rate_train": 4.81, "rate_valid": 11.07, "rate_test": 30.83,
    "auc": 0.6581, "mean_pred": 6.84, "lam": 0.01,
    "features": 10, "excluded": 15,
    "quota": [
        {"pct": "10%", "slots": 823, "rule": 572, "model": 550,
         "rule_rate": 69.50, "model_rate": 66.83, "rule_lift": 2.25, "model_lift": 2.17},
        {"pct": "20%", "slots": 1647, "rule": 934, "model": 980,
         "rule_rate": 56.71, "model_rate": 59.50, "rule_lift": 1.84, "model_lift": 1.93},
        {"pct": "40%", "slots": 3295, "rule": 1344, "model": 1411,
         "rule_rate": 40.79, "model_rate": 42.82, "rule_lift": 1.32, "model_lift": 1.39},
    ],
    "coverage": {"slots": 1647, "reserved": 659, "hit": 825},
}

FONT = "PingFang SC, Microsoft YaHei, Helvetica, sans-serif"
S = ["#b9422f", "#245f73", "#0a6b4c", "#B8892F", "#6d6258"]
CFG = {"displaylogo": False, "responsive": True,
       "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"]}
LAB = {"BEV": "纯电", "PHEV": "插混", "HEV": "混动", "PETROL": "汽油", "DIESEL": "柴油",
       "FLEET": "车队", "PRIVATE": "私人", "BUSINESS": "公司自用"}
NICE = {"Mg": "MG", "Byd": "BYD", "Bmw": "BMW", "Gwm": "GWM", "Ds": "DS",
        "Jaecoo": "JAECOO", "Omoda": "OMODA"}


def layout(fig, h=380, legend=True, margin=None):
    fig.update_layout(
        height=h, font=dict(family=FONT, size=12.5),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=margin or dict(l=56, r=26, t=14, b=52),
        legend=(dict(orientation="h", yanchor="top", y=-0.14, x=0, font=dict(size=12))
                if legend else None),
        xaxis=dict(gridcolor="rgba(140,120,90,.15)", zeroline=False,
                   linecolor="rgba(140,120,90,.35)"),
        yaxis=dict(gridcolor="rgba(140,120,90,.15)", zeroline=False,
                   linecolor="rgba(140,120,90,.35)"))
    return fig


# ══════════════════════════ 利率研究图
def fig_curve():
    rows, hist = FIN["curve"]["rows"], FIN["curve"].get("history_labels", [])
    ten = [r["tenor"] for r in rows]
    f = go.Figure()
    f.add_trace(go.Scatter(x=ten, y=[r["now"] for r in rows], name="最新",
                           mode="lines+markers", line=dict(color=S[0], width=3),
                           marker=dict(size=8),
                           hovertemplate="%{x}　%{y:.4f}%<extra>最新</extra>"))
    for i, h in enumerate(hist):
        f.add_trace(go.Scatter(
            x=ten, y=[r.get(h["label"]) for r in rows], name=f'{h["label"]}（{h["date"]}）',
            mode="lines+markers", line=dict(color=S[(i + 1) % len(S)], width=2, dash="dot"),
            marker=dict(size=5),
            hovertemplate="%{x}　%{y:.4f}%<extra>" + h["label"] + "</extra>"))
    f.update_yaxes(title_text="到期收益率（%）", ticksuffix="%")
    f.update_xaxes(title_text="期限")
    return layout(f, h=400)


def fig_change():
    rows = FIN["curve"]["rows"]
    ten = [r["tenor"] for r in rows]
    f = go.Figure()
    for key, nm, col in (("w1_bp", "周变动", S[2]), ("m1_bp", "月变动", S[1]),
                         ("y1_bp", "年变动", S[0])):
        f.add_trace(go.Bar(x=ten, y=[r.get(key) for r in rows], name=nm,
                           marker_color=col,
                           hovertemplate="%{x}　%{y:+.1f} bp<extra>" + nm + "</extra>"))
    f.update_yaxes(title_text="变动（bp）", ticksuffix="bp")
    f.update_xaxes(title_text="期限")
    f.update_layout(barmode="group", bargap=0.28, bargroupgap=0.08)
    return layout(f, h=360)


# ══════════════════════════ 银行建模图
def fig_quota():
    q = BANK["quota"]
    f = go.Figure()
    f.add_trace(go.Bar(x=[x["pct"] for x in q], y=[x["rule"] for x in q],
                       name="曾成功营销优先", marker_color=S[1],
                       text=[f'{x["rule"]:,}' for x in q], textposition="outside",
                       textfont=dict(family=FONT, size=12),
                       hovertemplate="%{x} 名额　规则 %{y:,.0f} 条<extra></extra>"))
    f.add_trace(go.Bar(x=[x["pct"] for x in q], y=[x["model"] for x in q],
                       name="逻辑回归排序", marker_color=S[0],
                       text=[f'{x["model"]:,}' for x in q], textposition="outside",
                       textfont=dict(family=FONT, size=12),
                       hovertemplate="%{x} 名额　模型 %{y:,.0f} 条<extra></extra>"))
    f.update_yaxes(title_text="入选样本的历史申购数（条）")
    f.update_xaxes(title_text="可跟进名额占测试集比例")
    f.update_layout(barmode="group", bargap=0.34, bargroupgap=0.1)
    return layout(f, h=380)


def fig_qrate():
    q = BANK["quota"]
    f = go.Figure()
    f.add_trace(go.Bar(x=[x["pct"] for x in q], y=[x["rule_rate"] for x in q],
                       name="曾成功营销优先", marker_color=S[1],
                       text=[f'{x["rule_rate"]:.2f}%' for x in q], textposition="outside",
                       textfont=dict(family=FONT, size=12),
                       hovertemplate="%{x} 名额　%{y:.2f}%<extra>规则</extra>"))
    f.add_trace(go.Bar(x=[x["pct"] for x in q], y=[x["model_rate"] for x in q],
                       name="逻辑回归排序", marker_color=S[0],
                       text=[f'{x["model_rate"]:.2f}%' for x in q], textposition="outside",
                       textfont=dict(family=FONT, size=12),
                       hovertemplate="%{x} 名额　%{y:.2f}%<extra>模型</extra>"))
    f.update_yaxes(title_text="入选样本申购率（%）", ticksuffix="%")
    f.update_xaxes(title_text="可跟进名额占测试集比例")
    f.update_layout(barmode="group", bargap=0.34, bargroupgap=0.1)
    return layout(f, h=380)


# ══════════════════════════ 出海图
def fig_cn():
    b = sorted(SEA["cn_brands"], key=lambda x: x["units"] or 0)
    f = go.Figure(go.Bar(x=[x["units"] for x in b], y=[NICE.get(x["brand"], x["brand"]) for x in b],
                         orientation="h", marker_color=S[2],
                         text=[f'{int(x["units"]):,}' for x in b], textposition="outside",
                         textfont=dict(family=FONT, size=12),
                         hovertemplate="%{y}　%{x:,.0f} 辆<extra></extra>"))
    f.update_xaxes(title_text="当月注册量（辆）")
    return layout(f, h=430, legend=False, margin=dict(l=88, r=44, t=14, b=52))


def fig_cn_yoy():
    b = sorted([x for x in SEA["cn_brands"] if 0 < (x.get("yoy") or 0) <= 500],
               key=lambda x: x["yoy"])
    if not b:
        return None
    f = go.Figure(go.Bar(x=[x["yoy"] for x in b], y=[NICE.get(x["brand"], x["brand"]) for x in b],
                         orientation="h", marker_color=S[3],
                         text=[f'+{x["yoy"]:.1f}%' for x in b], textposition="outside",
                         textfont=dict(family=FONT, size=12),
                         hovertemplate="%{y}　%{x:.1f}%<extra></extra>"))
    f.update_xaxes(title_text="当月注册量同比（%）", ticksuffix="%",
                   range=[0, max(x["yoy"] for x in b) * 1.22])
    return layout(f, h=430, legend=False, margin=dict(l=88, r=52, t=14, b=52))


def fig_channel():
    ch = SEA["channel"]
    f = go.Figure(go.Bar(x=[c["share"] for c in ch],
                         y=[LAB.get(c["key"], c["key"]) for c in ch], orientation="h",
                         marker_color=S[1], text=[f'{c["share"]:.1f}%' for c in ch],
                         textposition="outside", textfont=dict(family=FONT, size=12),
                         hovertemplate="%{y}　占当月注册 %{x:.1f}%<extra></extra>"))
    f.update_xaxes(title_text="占当月新车注册比重（%）", ticksuffix="%",
                   range=[0, max(c["share"] for c in ch) * 1.28])
    return layout(f, h=430, legend=False, margin=dict(l=78, r=44, t=14, b=52))


def fig_topbrands():
    rows = [x for x in (SEA.get("top_brands") or []) if x["brand"] != "Grand Total"][:10]
    if not rows:
        return None
    rows = sorted(rows, key=lambda x: x["units"] or 0)
    f = go.Figure(go.Bar(x=[x["units"] for x in rows],
                         y=[NICE.get(x["brand"], x["brand"]) for x in rows], orientation="h",
                         marker_color=S[1], text=[f'{int(x["units"]):,}' for x in rows],
                         textposition="outside", textfont=dict(family=FONT, size=12),
                         hovertemplate="%{y}　%{x:,.0f} 辆<extra></extra>"))
    f.update_xaxes(title_text="当月注册量（辆）")
    return layout(f, h=430, legend=False, margin=dict(l=100, r=48, t=14, b=52))


def fig_bev():
    t = sorted(SEA["bev_top10"], key=lambda x: x["units"])
    f = go.Figure(go.Bar(x=[x["units"] for x in t],
                         y=[f'{x["rank"]}. {x["model"]}' for x in t], orientation="h",
                         marker_color=S[0], text=[f'{int(x["units"]):,}' for x in t],
                         textposition="outside", textfont=dict(family=FONT, size=12),
                         hovertemplate="%{y}　%{x:,.0f} 辆<extra></extra>"))
    f.update_xaxes(title_text="当月注册量（辆）")
    return layout(f, h=430, legend=False, margin=dict(l=132, r=44, t=14, b=52))


CSS = """
:root{ --ink:#171411; --muted:#6d6258; --ink2:#3a332c; --paper:#f8f2e7; --line:#d8c8af;
  --red:#b9422f; --blue:#245f73; --green:#0a6b4c; --white:#fffaf0;
  --surface:rgba(255,250,240,.66); --bar-bg:rgba(248,242,231,.95);
  --font-b:"Songti SC","Noto Serif SC",Georgia,serif;
  --font-d:"PingFang SC","Microsoft YaHei",Helvetica,sans-serif;
  --bg:radial-gradient(circle at 18% 6%, rgba(184,137,47,.09), transparent 55%), #f8f2e7;
  --shadow:0 2px 10px rgba(60,45,25,.07); --tint:rgba(184,137,47,.12); }
body.dark{ --ink:#e8e4dc; --muted:#9c948a; --ink2:#cfc9bf; --paper:#14120f; --line:#332e27;
  --white:#0d0b09; --surface:rgba(34,30,25,.72); --bar-bg:rgba(20,18,15,.95);
  --bg:radial-gradient(circle at 18% 6%, rgba(217,171,82,.09), transparent 55%), #14120f;
  --red:#e07a63; --blue:#7fb6cc; --green:#4fbe86; --shadow:0 2px 14px rgba(0,0,0,.5);
  --tint:rgba(217,171,82,.13); }
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--font-b);background:var(--bg);color:var(--ink);line-height:1.8;font-size:16px}
a{color:var(--blue);text-decoration:none} a:hover{text-decoration:underline}
.bar{position:sticky;top:0;z-index:60;background:var(--bar-bg);backdrop-filter:blur(8px);
  border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;
  gap:14px;padding:0 24px;height:58px;font-family:var(--font-d)}
.bar b{font-size:15px;font-weight:600}
.bar nav{display:flex;gap:18px;font-size:13.5px;align-items:center;flex-wrap:wrap}
.bar nav a{color:var(--muted)} .bar nav a:hover{color:var(--ink)}
.tg{border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:99px;
  padding:5px 13px;font:inherit;font-size:12.5px;cursor:pointer;font-family:var(--font-d)}
main{max-width:1120px;margin:0 auto;padding:30px 26px 70px}
h1{font-family:var(--font-d);font-size:27px;font-weight:600}
.stamp{color:var(--muted);font-size:13.5px;font-family:var(--font-d);margin:6px 0 26px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:13px}
.kpi{background:var(--surface);border:1px solid var(--line);border-radius:13px;padding:15px 17px;
  box-shadow:var(--shadow)}
.kpi .lb{font-size:12.5px;color:var(--muted);font-family:var(--font-d);letter-spacing:.02em}
.kpi .vl{font-size:23px;font-weight:650;font-family:var(--font-d);margin-top:2px;
  font-variant-numeric:tabular-nums;line-height:1.35}
.kpi .vl .u{font-size:12.5px;font-weight:400;color:var(--muted);margin-left:3px}
.kpi .ch{font-size:13px;font-family:var(--font-d);font-variant-numeric:tabular-nums;
  min-height:20px;margin-top:3px}
.kpi .sub{font-size:11.5px;color:var(--muted);font-family:var(--font-d);margin-top:3px}
.up{color:var(--red)} .down{color:#1e8449}
section{margin-top:40px}
h2{font-family:var(--font-d);font-size:12.5px;letter-spacing:.17em;text-transform:uppercase;
  color:var(--red);font-weight:700;margin-bottom:6px}
.ptitle{font-family:var(--font-d);font-size:19px;font-weight:650;margin-bottom:14px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start}
.card{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:17px 19px;
  box-shadow:var(--shadow);min-width:0}
.card h3{font-family:var(--font-d);font-size:15px;font-weight:650;margin-bottom:12px;
  padding-bottom:9px;border-bottom:1px solid var(--line)}
.chartbox{width:100%;overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:13.5px;font-family:var(--font-d);
  font-variant-numeric:tabular-nums}
th,td{padding:8px 9px;text-align:right;border-bottom:1px solid var(--line);white-space:nowrap}
th:first-child,td:first-child{text-align:left}
th{color:var(--muted);font-weight:600;font-size:12px}
th .hd{font-weight:400;font-size:11px;opacity:.8}
td.tn{font-weight:650}
tr:last-child td{border-bottom:0}
.tbwrap{overflow-x:auto}
.units{font-size:12.5px;color:var(--muted);font-family:var(--font-d);margin-top:10px;
  line-height:1.7}
p.lead{font-size:15.5px;color:var(--ink2);margin-bottom:14px;line-height:1.9}
/* 方法模块卡片 */
.mgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:13px}
.mcard{background:var(--surface);border:1px solid var(--line);border-left:3px solid var(--green);
  border-radius:11px;padding:15px 16px;box-shadow:var(--shadow)}
.mcard .n{font-size:11.5px;color:var(--green);font-family:var(--font-d);font-weight:700;
  letter-spacing:.1em}
.mcard b{display:block;font-family:var(--font-d);font-size:15px;margin:4px 0 6px}
.mcard span{font-size:13.5px;color:var(--ink2);line-height:1.75}
footer{margin-top:44px;padding-top:22px;border-top:1px solid var(--line);text-align:center;
  color:var(--muted);font-size:12.5px;font-family:var(--font-d);line-height:1.9}
@media(max-width:900px){
  .grid2{grid-template-columns:1fr;gap:0}
  .grid2 > .card + .card{margin-top:16px}
  .bar{height:auto;padding:10px 14px;flex-wrap:wrap}
  .bar nav{gap:12px;font-size:12.5px}
  main{padding:22px 15px 56px} h1{font-size:22px}
  .kpis{grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:10px}
  .kpi .vl{font-size:20px}
}
"""


def bar(tabs: list[tuple[str, str]], title: str) -> str:
    links = "".join(f'<a href="#{h}">{t}</a>' for t, h in tabs)
    return f"""<div class="bar"><b><a href="index.html" style="color:inherit">刘柏廷 · Evo</a>　<span style="color:var(--muted);font-weight:400">{title}</span></b>
<nav>{links}<a href="index.html">回主页</a><button class="tg" onclick="document.body.classList.toggle('dark')">深/浅色</button></nav></div>"""


def kpi_block(items) -> str:
    return "".join(
        f'<div class="kpi"><div class="lb">{l}</div>'
        f'<div class="vl">{v}<span class="u">{u}</span></div>'
        f'<div class="ch {c}">{ct}</div>'
        f'<div class="sub">{s}</div></div>' for v, u, l, ct, c, s in items)


def nf(v, d=2):
    return "—" if v is None else f"{v:.{d}f}"


# ══════════════════════════════ 金融看板
def build_fin() -> str:
    items = RT.get("items") or []
    upd = RT.get("as_of") or ""
    kpis = []
    for it in items:
        sign = it.get("chg_sign") or 0
        cls = "up" if sign > 0 else ("down" if sign < 0 else "")
        kpis.append((it["value"], it["unit"], it["name"], it.get("chg_text") or "",
                     cls, it.get("sub") or ""))
    rate_kpi = kpi_block(kpis)

    hist = FIN["curve"].get("history_labels", [])
    th = "".join(f"<th>{h['label']}<br><span class='hd'>{h['date']}</span></th>" for h in hist)
    trs = ""
    for r in FIN["curve"]["rows"]:
        tds = "".join(f"<td>{nf(r.get(h['label']))}</td>" for h in hist)

        def cell(v):
            s = "up" if (v or 0) > 0.05 else ("down" if (v or 0) < -0.05 else "")
            return f'<td class="{s}">{"—" if v is None else f"{v:+.1f}"}</td>'

        trs += (f"<tr><td class='tn'>{r['tenor']}</td><td>{nf(r['now'])}</td>{tds}"
                f"{cell(r.get('w1_bp'))}{cell(r.get('m1_bp'))}{cell(r.get('y1_bp'))}</tr>")

    omo = "".join(f'<li><a href="{o["url"]}" target="_blank" rel="noopener">{o["title"]}</a></li>'
                  for o in (FIN.get("omo") or []))

    b = BANK
    bk = kpi_block([
        (f'{b["records"]:,}', "条", "公开营销记录", "", "", "UCI Bank Marketing"),
        (f'{b["test"]:,}', "条", "测试集样本", "", "", f'测试期申购率 {b["rate_test"]:.2f}%'),
        (f'{b["quota"][1]["model"]:,}', "条", "20% 名额 · 模型覆盖历史申购",
         f'比规则多 {b["quota"][1]["model"] - b["quota"][1]["rule"]} 条', "up", ""),
        (f'{b["auc"]:.4f}', "", "测试 ROC-AUC", "", "", f'正则参数 λ={b["lam"]}'),
    ])

    qrows = ""
    for x in b["quota"]:
        d = x["model"] - x["rule"]
        cls = "up" if d > 0 else ("down" if d < 0 else "")
        qrows += (f'<tr><td class="tn">{x["pct"]}</td><td>{x["slots"]:,}</td>'
                  f'<td>{x["rule"]:,}</td><td>{x["model"]:,}</td>'
                  f'<td class="{cls}">{d:+d}</td>'
                  f'<td>{x["rule_rate"]:.2f}%</td><td>{x["model_rate"]:.2f}%</td>'
                  f'<td>{x["rule_lift"]:.2f}</td><td>{x["model_lift"]:.2f}</td></tr>')

    d1 = to_html(fig_curve(), include_plotlyjs=True, full_html=False, config=CFG)
    d2 = to_html(fig_change(), include_plotlyjs=False, full_html=False, config=CFG)
    d3 = to_html(fig_quota(), include_plotlyjs=False, full_html=False, config=CFG)
    d4 = to_html(fig_qrate(), include_plotlyjs=False, full_html=False, config=CFG)

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>金融看板 · 刘柏廷 Evo</title><style>{CSS}</style></head><body>
{bar([("利率研究", "rates"), ("银行客户经营建模", "bank")], "金融看板")}

<main>
  <h1>金融看板</h1>
  <p class="stamp">更新于 {upd}（北京时间）</p>

  <section id="rates">
    <h2>项目一</h2>
    <div class="ptitle">利率研究：宏观流动性、利率与曲线结构</div>
    <p class="lead">围绕国债收益率曲线、期限利差与宏观流动性读数，把利率变化拆成可复核的一组数字，
      用于判断当前利率环境对不同久期与不同流动性约束的组合意味着什么。</p>
    <div class="kpis">{rate_kpi}</div>

    <div class="card" style="margin-top:16px">
      <h3>国债收益率曲线</h3>
      <div class="chartbox">{d1}</div>
    </div>
    <div class="card" style="margin-top:16px">
      <h3>各期限收益率变动</h3>
      <div class="chartbox">{d2}</div>
    </div>
    <div class="card" style="margin-top:16px">
      <h3>各期限明细与变动</h3>
      <div class="tbwrap"><table>
        <tr><th>期限</th><th>最新<br><span class="hd">{FIN['meta']['data_date']}</span></th>{th}
            <th>周变动</th><th>月变动</th><th>年变动</th></tr>
        {trs}
      </table></div>
      <p class="units">收益率单位：%；变动单位：bp（1bp = 0.01 个百分点）</p>
    </div>
    <div class="card" style="margin-top:16px">
      <h3>中国人民银行公开市场业务交易公告</h3>
      <ul>{omo}</ul>
    </div>
  </section>

  <section id="bank">
    <h2>项目二</h2>
    <div class="ptitle">银行客户经营建模：触达优先级与名额分配</div>
    <p class="lead">围绕「先联系谁、各类对象分配多少名额」，用公开银行营销记录比较
      「凭历史成交经验筛选」与「综合多项信息排序」的差异，形成可随团队可用名额调整的跟进方案。</p>
    <div class="kpis">{bk}</div>

    <div class="grid2" style="margin-top:16px">
      <div class="card">
        <h3>不同名额下的历史申购覆盖数</h3>
        <div class="chartbox">{d3}</div>
      </div>
      <div class="card">
        <h3>不同名额下的入选样本申购率</h3>
        <div class="chartbox">{d4}</div>
      </div>
    </div>

    <div class="card" style="margin-top:16px">
      <h3>名额方案对照</h3>
      <div class="tbwrap"><table>
        <tr><th>名额比例</th><th>名额</th><th>规则覆盖（条）</th><th>模型覆盖（条）</th>
            <th>差值</th><th>规则申购率</th><th>模型申购率</th><th>规则提升</th><th>模型提升</th></tr>
        {qrows}
      </table></div>
      <p class="units">规则＝「曾成功营销优先」；模型＝L2 正则逻辑回归排序。
        提升倍数＝相对随机排序的申购率提升。测试集 {b['test']:,} 条，测试期申购率 {b['rate_test']:.2f}%。</p>
    </div>

    <div class="card" style="margin-top:16px">
      <h3>方法</h3>
      <p class="lead">按原始时间顺序划分为训练 {b['train']:,} / 验证 {b['valid']:,} / 测试 {b['test']:,} 条；
        训练期申购率 {b['rate_train']:.2f}%、验证期 {b['rate_valid']:.2f}%、测试期 {b['rate_test']:.2f}%。
        模型为 L2 正则逻辑回归，使用 {b['features']} 个特征，剔除 {b['excluded']} 个可能混入事后信息的字段；
        正则参数在验证集上选择，冻结后在测试集评估一次。</p>
      <p class="units">结果为测试集历史样本的静态离线比较，非实盘业绩；历史申购标签不等同于机构客户基金申购。</p>
    </div>
  </section>

  <footer>
    数据来源：上海证券交易所 · 深圳证券交易所 · 香港交易所 · 中央国债登记结算有限责任公司 ·
    中国外汇交易中心 · 中国人民银行；银行建模数据来自 UCI Bank Marketing 公开数据集（CC BY 4.0）
  </footer>
</main></body></html>
"""


# ══════════════════════════════ 出海看板
def build_sea() -> str:
    mk, cn = SEA["market"], SEA["cn_brands"]
    cn_total = sum(x["units"] or 0 for x in cn)
    cn_ytd = sum((x.get("ytd") or 0) for x in cn)
    cn_share = cn_total / (mk["total_month"] or 1) * 100
    top = max(cn, key=lambda x: x["units"] or 0)
    fast = max([x for x in cn if 0 < (x.get("yoy") or 0) <= 500], key=lambda x: x["yoy"])
    fleet = next(c for c in SEA["channel"] if c["key"] == "FLEET")
    priv = next(c for c in SEA["channel"] if c["key"] == "PRIVATE")
    byd = next((x for x in cn if x["brand"] == "Byd"), None)

    k = [ (f'{int(mk["total_month"]):,}', "辆", "英国当月新车注册", "", "", ""),
          (f'{int(cn_total):,}', "辆", "中国与新兴品牌当月合计", "", "", f'占当月 {cn_share:.1f}%'),
          (f'{int(byd["units"]):,}', "辆", "比亚迪当月注册", f'同比 +{byd["yoy"]:.1f}%', "up",
           f'年初至今 {int(byd["ytd"]):,} 辆') if byd else
          (f'{int(top["units"]):,}', "辆", f'当月最高 · {NICE.get(top["brand"], top["brand"])}',
           f'同比 +{top["yoy"]:.1f}%', "up", ""),
          (f'+{fast["yoy"]:.1f}%', "", f'同比增速最高 · {NICE.get(fast["brand"], fast["brand"])}',
           "", "", f'当月 {int(fast["units"]):,} 辆'),
          (f'{fleet["share"]:.1f}%', "", "车队渠道占比", "", "", f'私人 {priv["share"]:.1f}%'),
          (f'{int(cn_ytd):,}', "辆", "中国与新兴品牌年初至今", "", "", "") ]
    ok_html = kpi_block(k)

    rows = ""
    for x in cn:
        yoy = x.get("yoy")
        cls = "up" if (yoy or 0) > 0.05 else ("down" if (yoy or 0) < -0.05 else "")
        rows += (f'<tr><td class="tn">{NICE.get(x["brand"], x["brand"])}</td>'
                 f'<td>{int(x["units"]):,}</td><td>{x.get("share"):.2f}%</td>'
                 f'<td class="{cls}">{("%+.2f%%" % yoy) if yoy is not None else "—"}</td>'
                 f'<td>{int(x.get("ytd") or 0):,}</td></tr>')

    comp = ""
    for c in SEA["competitors"]:
        if not c.get("range_miles") and not c.get("battery_kwh"):
            continue
        rng = " / ".join(c["range_miles"]) if c.get("range_miles") else "—"
        bat = " / ".join(c["battery_kwh"]) if c.get("battery_kwh") else "—"
        comp += (f'<tr><td class="tn">{c["model"]}</td><td>{rng}</td><td>{bat}</td>'
                 f'<td><a href="{c["url"]}" target="_blank" rel="noopener">'
                 f'{c["url"].split("/")[2]}</a></td></tr>')

    mods = [("评论挖掘", "对德语用户评论做情感打分与主题聚类，把竞品被抱怨最集中的方向转成产品切入点。"),
            ("达人分层", "按受众地域、内容契合度与互动质量分层，并设置反作弊规则，避免只看粉丝量。"),
            ("竞品价格追踪", "每日入库竞品价格，用滚动中位数基线识别促销区间，让价格节奏可提前判断。"),
            ("渠道漏斗", "曝光 → 点击 → 详情页 → 加购 → 成交 → 复购，计算各渠道获客成本并与单台贡献毛利对比。"),
            ("本地化文案", "生成多版德语文案并做人工评分，最终判断由人完成。")]
    mcards = "".join(
        f'<div class="mcard"><div class="n">{i+1:02d}</div><b>{n}</b><span>{d}</span></div>'
        for i, (n, d) in enumerate(mods))

    d1 = to_html(fig_cn(), include_plotlyjs=True, full_html=False, config=CFG)
    f2, f3, f4, f5 = fig_topbrands(), fig_cn_yoy(), fig_bev(), fig_channel()
    d2 = to_html(f2, include_plotlyjs=False, full_html=False, config=CFG) if f2 else ""
    d3 = to_html(f3, include_plotlyjs=False, full_html=False, config=CFG) if f3 else ""
    d4 = to_html(f4, include_plotlyjs=False, full_html=False, config=CFG) if f4 else ""
    d5 = to_html(f5, include_plotlyjs=False, full_html=False, config=CFG) if f5 else ""

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>出海看板 · 刘柏廷 Evo</title><style>{CSS}</style></head><body>
{bar([("比亚迪（英国）", "byd"), ("徕芬（德国）", "laifen")], "出海看板")}

<main>
  <h1>出海看板</h1>
  <p class="stamp">数据来源：SMMT 英国乘用车注册公开数据　·　数据日期 {SEA['meta']['data_date']}</p>

  <section id="byd">
    <h2>项目一</h2>
    <div class="ptitle">比亚迪（英国）：市场进入研究与竞品基线</div>
    <p class="lead">以 BYD DOLPHIN SURF 为切口建立英国市场基线：接入 SMMT 官方注册数据，
      覆盖动力类型、销售渠道、品牌级与车型榜，并跟踪中国品牌在英国的注册表现。</p>
    <div class="kpis">{ok_html}</div>

    <div class="grid2" style="margin-top:16px">
      <div class="card">
        <h3>中国与新兴品牌 · 当月注册量</h3>
        <div class="chartbox">{d1}</div>
      </div>
      <div class="card">
        <h3>中国与新兴品牌 · 当月同比</h3>
        <div class="chartbox">{d3}</div>
      </div>
    </div>

    <div class="card" style="margin-top:16px">
      <h3>品牌明细</h3>
      <div class="tbwrap"><table>
        <tr><th>品牌</th><th>当月注册（辆）</th><th>市场份额</th><th>同比</th><th>年初至今（辆）</th></tr>
        {rows}
      </table></div>
    </div>

    <div class="grid2" style="margin-top:16px">
      <div class="card">
        <h3>全市场品牌注册量前十</h3>
        <div class="chartbox">{d2}</div>
      </div>
      <div class="card">
        <h3>销售渠道占比</h3>
        <div class="chartbox">{d5}</div>
      </div>
    </div>

    <div class="card" style="margin-top:16px">
      <h3>纯电车型注册量前十</h3>
      <div class="chartbox">{d4}</div>
    </div>

    <div class="card" style="margin-top:16px">
      <h3>同级车型官方公布规格</h3>
      <div class="tbwrap"><table>
        <tr><th>车型</th><th>官方续航（英里）</th><th>电池容量（kWh）</th><th>官方来源</th></tr>
        {comp}
      </table></div>
    </div>
  </section>

  <section id="laifen">
    <h2>项目二</h2>
    <div class="ptitle">徕芬（德国）：市场进入决策框架</div>
    <p class="lead">把「评论挖掘 → 达人分层 → 竞品价格追踪 → 渠道漏斗 → 本地化文案」五个模块
      串成一条上市决策链，每个模块对应一个具体决策问题：切什么卖点、投给谁、什么时候调价、
      钱花在哪、话怎么说。</p>
    <div class="mgrid">{mcards}</div>
    <div class="card" style="margin-top:16px">
      <h3>工程与更新</h3>
      <p class="lead">抓取、清洗与看板代码可复现，支持按日定时自动更新；AI 承担数据处理层，
        上市判断与文案定稿由人完成。</p>
    </div>
  </section>

  <footer>
    数据来源：SMMT（英国汽车制造商与贸易商协会）乘用车注册数据 · 各品牌英国官网；注册量为新车上牌登记口径
  </footer>
</main></body></html>
"""


def main() -> None:
    evo = ROOT / "evo-site"
    if not evo.exists():
        evo.mkdir(parents=True)
    p1 = evo / "dashboard.html"
    h1 = build_fin()
    p1.write_text(h1, encoding="utf-8")
    log_line(f"金融看板：{p1.relative_to(ROOT)}（{len(h1)/1048576:.2f} MB）· 利率研究 + 银行客户经营建模")
    p2 = evo / "overseas.html"
    h2 = build_sea()
    p2.write_text(h2, encoding="utf-8")
    log_line(f"出海看板：{p2.relative_to(ROOT)}（{len(h2)/1048576:.2f} MB）· 比亚迪（英国）+ 徕芬（德国）")


if __name__ == "__main__":
    main()
