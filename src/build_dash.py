"""
生成统一数据看板 evo-site/dashboard.html

按徕芬看板的标准：Plotly 交互图（可缩放 /  hover / 图例开关 / 下载），
分模块组织，数据来自官方公开来源。plotly.js 内嵌，页面自包含无外部依赖。

模块：一 债市 ｜ 二 英国出海 ｜ 三 数据质量
用法： python src/build_dash.py
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
SEA = json.loads((ROOT / "data" / "dash" / "overseas.json").read_text(encoding="utf-8"))

PAL = ["#b9422f", "#245f73", "#177A5C", "#B8892F", "#6d6258"]
FONT = "PingFang SC, Microsoft YaHei, Helvetica, sans-serif"


def base_layout(fig, title="", h=380, legend=True):
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, family=FONT), x=0.01),
        height=h,
        font=dict(family=FONT, size=12.5),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=52, r=22, t=42, b=44),
        hovermode="x unified",
        legend=dict(orientation="h", y=1.12, x=0) if legend else None,
        modebar=dict(orientation="v"),
        xaxis=dict(gridcolor="rgba(140,120,90,.16)", zeroline=False),
        yaxis=dict(gridcolor="rgba(140,120,90,.16)", zeroline=False),
    )
    return fig


# ---------------------------------------------------------------- 图 1 曲线
def fig_curve():
    rows = FIN["curve"]["rows"]
    hist = FIN["curve"].get("history_labels", [])
    ten = [r["tenor"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ten, y=[r["now"] for r in rows], name=f"当前 {FIN['meta']['data_date']}",
                             mode="lines+markers", line=dict(color=PAL[0], width=3),
                             marker=dict(size=7),
                             hovertemplate="%{x}：%{y:.4f}%<extra>当前</extra>"))
    for i, h in enumerate(hist):
        lab = h["label"]
        fig.add_trace(go.Scatter(
            x=ten, y=[r.get(lab) for r in rows], name=f"{lab}（{h['date']}）",
            mode="lines+markers", line=dict(color=PAL[(i + 1) % len(PAL)], width=2, dash="dot"),
            marker=dict(size=5),
            hovertemplate="%{x}：%{y:.4f}%<extra>" + lab + "</extra>"))
    fig.update_yaxes(title_text="到期收益率（%）", ticksuffix="%")
    base_layout(fig, "国债收益率曲线（中债 · 银行间市场）　点击图例可开关任意对比基准", 440)
    fig.update_layout(hovermode="x unified")
    return fig


# ---------------------------------------------------------------- 图 2 变动
def fig_change():
    rows = FIN["curve"]["rows"]
    ten = [r["tenor"] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=ten, y=[r.get("w1_bp") for r in rows], name="周变动",
                         marker_color=PAL[2], hovertemplate="%{x}：%{y:+.1f}bp<extra>周变动</extra>"))
    fig.add_trace(go.Bar(x=ten, y=[r.get("m1_bp") for r in rows], name="月变动",
                         marker_color=PAL[1], hovertemplate="%{x}：%{y:+.1f}bp<extra>月变动</extra>"))
    fig.add_trace(go.Bar(x=ten, y=[r.get("y1_bp") for r in rows], name="年变动",
                         marker_color=PAL[0], hovertemplate="%{x}：%{y:+.1f}bp<extra>年变动</extra>"))
    fig.update_yaxes(title_text="变动（bp）", ticksuffix="bp")
    base_layout(fig, "各期限收益率变动（1bp = 0.01 个百分点）", 360)
    fig.update_layout(barmode="group", hovermode="x")
    return fig


# ---------------------------------------------------------------- 图 3 DR007
def fig_dr():
    s = FIN.get("dr_series") or []
    if not s:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[p["date"] for p in s], y=[p["value"] for p in s],
                             name="DR007", mode="lines+markers",
                             line=dict(color=PAL[0], width=2.6), marker=dict(size=5),
                             hovertemplate="%{x}：%{y:.4f}%<extra>DR007</extra>"))
    fig.update_yaxes(title_text="利率（%）", ticksuffix="%")
    base_layout(fig, "资金面：DR007 近期走势（存款类机构质押式回购加权利率 · 7 天）", 320, legend=False)
    return fig


# ---------------------------------------------------------------- 图 4 英国结构
def fig_uk_mix():
    pt = SEA.get("powertrain") or []
    ch = SEA.get("channel") or []
    LAB = {"BEV": "纯电", "PHEV": "插混", "HEV": "混动", "PETROL": "汽油", "DIESEL": "柴油",
           "FLEET": "车队", "PRIVATE": "私人", "BUSINESS": "公司自用"}
    if not pt and not ch:
        return None
    labels, parents, values = ["英国新乘用车注册"], [""], [0]
    if ch:
        labels += [f"渠道 · {LAB.get(c['key'], c['key'])}" for c in ch]
        parents += ["英国新乘用车注册"] * len(ch)
        values += [c["share"] or 0 for c in ch]
    if pt:
        labels += [f"动力 · {LAB.get(c['key'], c['key'])}" for c in pt]
        parents += ["英国新乘用车注册"] * len(pt)
        values += [c["share"] or 0 for c in pt]
    fig = go.Figure(go.Treemap(
        labels=labels, parents=parents, values=values, branchvalues="remainder",
        textinfo="label+value", hovertemplate="%{label}<br>占比 %{value:.1f}%<extra></extra>",
        marker=dict(colors=PAL * 4, line=dict(width=2, color="#fffaf0")),
        textfont=dict(family=FONT, size=13)))
    base_layout(fig, "英国市场结构（SMMT · 当月占比 %）　点击色块可下钻", 400, legend=False)
    return fig


# ---------------------------------------------------------------- 图 5 中国品牌
def fig_brands():
    b = (SEA.get("cn_brands") or [])[:10]
    if not b:
        return None
    b = sorted(b, key=lambda x: x["units"] or 0)
    fig = go.Figure(go.Bar(
        x=[x["units"] for x in b], y=[x["brand"] for x in b], orientation="h",
        marker=dict(color=[PAL[2] if (x.get("yoy") or 0) > 0 else PAL[4] for x in b]),
        text=[f'{int(x["units"]):,} 辆　{(x.get("yoy") or 0):+.1f}%' for x in b],
        textposition="outside", textfont=dict(family=FONT, size=12),
        hovertemplate="%{y}<br>%{x:,.0f} 辆<extra></extra>"))
    fig.update_xaxes(title_text="当月注册量（辆）")
    base_layout(fig, "中国与新兴品牌 · 英国注册表现（当月，品牌级含全部动力类型）", 400, legend=False)
    return fig


# ---------------------------------------------------------------- 图 6 BEV
def fig_bev():
    t = SEA.get("bev_top10") or []
    if not t:
        return None
    t = sorted(t, key=lambda x: x["units"])
    fig = go.Figure(go.Bar(
        x=[x["units"] for x in t], y=[f'{x["rank"]}. {x["model"]}' for x in t], orientation="h",
        marker_color=PAL[1],
        text=[f'{int(x["units"]):,}' for x in t], textposition="outside",
        textfont=dict(family=FONT, size=12),
        hovertemplate="%{y}<br>%{x:,.0f} 辆<extra></extra>"))
    fig.update_xaxes(title_text="当月注册量（辆）")
    base_layout(fig, "英国纯电车型 Top10（SMMT 免费公开部分）", 420, legend=False)
    return fig


def nf(v, d=2):
    return "—" if v is None else f"{v:.{d}f}"


def n0(v):
    return "—" if v is None else f"{round(v):,}"


def bp(v):
    return "—" if v is None else f"{'+' if v > 0 else ''}{v:.1f}bp"


def ccls(v):
    return "" if v is None else ("up" if v > 0.05 else ("down" if v < -0.05 else ""))


def kpi(v, l, ch=""):
    return f'<div class="kpi"><div class="lb">{l}</div><div class="vl">{v}</div>' \
           + (f'<div class="ch {ch}">{ch and ""}</div>' if False else "") + "</div>"


def build_html() -> str:
    mk = SEA.get("market") or {}
    y10 = next((r for r in FIN["curve"]["rows"] if r["key"] == "10.0"), {})
    dr = (FIN.get("money") or {}).get("FDR007") or {}
    sh = FIN.get("shape") or {}
    cn = (SEA.get("cn_brands") or [{}])[0]

    figs = [("curve", fig_curve()), ("change", fig_change()), ("dr", fig_dr()),
            ("uk", fig_uk_mix()), ("brands", fig_brands()), ("bev", fig_bev())]
    divs, first = {}, True
    for key, f in figs:
        if f is None:
            divs[key] = ""
            continue
        divs[key] = to_html(f, include_plotlyjs=first, full_html=False,
                            config={"displaylogo": False, "responsive": True,
                                    "toImageButtonOptions": {"scale": 2}})
        first = False

    # KPI
    kpis = [
        (nf(y10.get("now")) + "%", "10 年期国债", f"月 {bp(y10.get('m1_bp'))} · 年 {bp(y10.get('y1_bp'))}"),
        (nf(sh.get("10Y-1Y"), 3), "10Y − 1Y 利差", f"3 个月前 {nf(sh.get('10Y-1Y_3个月前'), 3)}"),
        (nf(dr.get("value")) + "%", "DR007", f"较前值 {bp(dr.get('chg_bp'))}"),
        (nf(mk.get("bev_share"), 1) + "%", "英国纯电份额", f"同比 {bp(mk.get('bev_yoy'))}"),
        (n0(mk.get("total_month")), "英国当月注册（辆）", f"纯电 {n0(mk.get('bev_month'))}"),
        (cn.get("brand", "—"), "中国品牌首位", f"{n0(cn.get('units'))} 辆 · {bp(cn.get('yoy'))}"),
    ]
    kpi_html = "".join(f'<div class="kpi"><div class="lb">{l}</div><div class="vl">{v}</div>'
                       f'<div class="ch">{c}</div></div>' for v, l, c in kpis)

    # 期限表
    hist = FIN["curve"].get("history_labels", [])
    th = "".join(f"<th>{h['label']}</th>" for h in hist)
    trs = ""
    for r in FIN["curve"]["rows"]:
        tds = "".join(f"<td>{nf(r.get(h['label']))}</td>" for h in hist)
        trs += (f"<tr><td><b>{r['tenor']}</b></td><td>{nf(r['now'])}</td>{tds}"
                f"<td class='{ccls(r.get('w1_bp'))}'>{bp(r.get('w1_bp'))}</td>"
                f"<td class='{ccls(r.get('m1_bp'))}'>{bp(r.get('m1_bp'))}</td>"
                f"<td class='{ccls(r.get('y1_bp'))}'>{bp(r.get('y1_bp'))}</td></tr>")

    omo = "".join(
        f'<li><a href="{o["url"]}" target="_blank" rel="noopener">{o["title"]}</a></li>'
        for o in (FIN.get("omo") or []))

    srcs = "".join(
        f'<tr><td><code>{k}</code></td><td>{v["name"]}</td>'
        f'<td><a href="{v["url"]}" target="_blank" rel="noopener">原文</a></td></tr>'
        for k, v in (FIN.get("sources") or {}).items())

    nr = "".join(f'<li><b>{x["item"]}</b> —— {x["reason"]}</li>'
                 for x in (SEA.get("not_retrieved") or []))

    html = TEMPLATE
    for k, v in {
        "kpis": kpi_html, "th": th, "trs": trs, "omo": omo, "srcs": srcs, "nr": nr,
        "c_curve": divs["curve"], "c_change": divs["change"], "c_dr": divs["dr"] or "",
        "c_uk": divs["uk"] or "", "c_brands": divs["brands"] or "", "c_bev": divs["bev"] or "",
        "date": FIN["meta"]["data_date"],
        "gen": FIN["meta"]["generated_at"][:16].replace("T", " "),
        "aud": FIN["meta"]["audience"],
    }.items():
        html = html.replace("@@" + k + "@@", v)
    return html


TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>数据看板 · 刘柏廷 Evo</title>
<style>
:root{ --ink:#171411; --muted:#6d6258; --ink-soft-2:#4a4239; --paper:#f8f2e7;
  --paper-deep:#ece1cf; --line:#d8c8af; --red:#b9422f; --blue:#245f73; --green:#177A5C;
  --white:#fffaf0; --surface:rgba(255,250,240,.66); --bar-bg:rgba(248,242,231,.95);
  --font-body:"Songti SC","Noto Serif SC",Georgia,serif;
  --font-display:"PingFang SC","Microsoft YaHei",Helvetica,sans-serif;
  --bg:radial-gradient(circle at 18% 6%, rgba(184,137,47,.10), transparent 55%), #f8f2e7;
  --shadow:0 2px 10px rgba(60,45,25,.07); --tint:rgba(184,137,47,.13); --tint-strong:rgba(184,137,47,.26);}
body.dark{ --ink:#e8e4dc; --muted:#9c948a; --ink-soft-2:#b9b2a7; --paper:#14120f; --paper-deep:#1d1a16;
  --line:#332e27; --white:#0d0b09; --surface:rgba(34,30,25,.72); --bar-bg:rgba(20,18,15,.95);
  --bg:radial-gradient(circle at 18% 6%, rgba(217,171,82,.10), transparent 55%), #14120f;
  --red:#e07a63; --blue:#7fb6cc; --green:#6cc79f;
  --shadow:0 2px 14px rgba(0,0,0,.5); --tint:rgba(217,171,82,.14); --tint-strong:rgba(217,171,82,.28);}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:var(--font-body);background:var(--bg);color:var(--ink);line-height:1.85;font-size:16px}
a{color:var(--blue)}
.bar{position:sticky;top:0;z-index:60;background:var(--bar-bg);backdrop-filter:blur(8px);
  border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;
  gap:14px;padding:0 26px;height:58px;font-family:var(--font-display)}
.bar b{font-size:15px}
.bar nav{display:flex;gap:16px;font-size:13.5px;align-items:center;flex-wrap:wrap}
.bar nav a{color:var(--muted)} .bar nav a:hover{color:var(--ink);text-decoration:none}
.tg{border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:99px;
  padding:5px 12px;font:inherit;font-size:12.5px;cursor:pointer;font-family:var(--font-display)}
main{max-width:1120px;margin:0 auto;padding:26px 26px 80px}
h1{font-family:var(--font-display);font-size:26px;font-weight:600;margin-bottom:6px}
.sub{color:var(--muted);font-size:14px;font-family:var(--font-display);margin-bottom:22px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:22px}
.kpi{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.kpi .lb{font-size:12px;color:var(--muted);font-family:var(--font-display)}
.kpi .vl{font-size:23px;font-weight:650;margin-top:3px;font-family:var(--font-display)}
.kpi .ch{font-size:12px;color:var(--muted);font-family:var(--font-display)}
section{margin-top:34px}
h2{font-family:var(--font-display);font-size:13px;letter-spacing:.16em;text-transform:uppercase;
  color:var(--red);margin-bottom:6px;font-weight:700}
.secl{font-family:var(--font-display);font-size:17px;font-weight:650;margin-bottom:14px}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px 18px;
  margin-bottom:16px;box-shadow:var(--shadow)}
.panel h4{font-family:var(--font-display);font-size:14.5px;margin-bottom:8px;font-weight:650}
table{width:100%;border-collapse:collapse;font-size:13.5px;font-family:var(--font-display);
  font-variant-numeric:tabular-nums}
th,td{padding:7px 8px;text-align:right;border-bottom:1px solid var(--line)}
th:first-child,td:first-child{text-align:left}
th{color:var(--muted);font-weight:600;font-size:12.5px}
.up{color:var(--red)} .down{color:var(--green)}
.tscroll{overflow-x:auto}
ul{margin:8px 0 0 18px} li{margin:6px 0;font-size:14.5px}
.note{font-size:13px;color:var(--muted);line-height:1.75;margin-top:9px}
.btnrow{display:flex;gap:10px;flex-wrap:wrap;margin:10px 0 0}
.btnrow a{border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:99px;
  padding:8px 16px;font-size:13.5px;font-family:var(--font-display);text-decoration:none}
.btnrow a:hover{background:var(--tint);text-decoration:none}
footer{text-align:center;color:var(--muted);font-size:13px;padding:30px 0 0;
  border-top:1px solid var(--line);font-family:var(--font-display);margin-top:36px}
@media(max-width:760px){ .bar{height:auto;padding:10px 14px;flex-wrap:wrap}
  .bar nav{gap:11px;font-size:12.5px} main{padding:0 14px 60px} h1{font-size:21px} }
</style></head>
<body>
<div class="bar">
  <b onclick="location.href='index.html'" style="cursor:pointer">刘柏廷 · Evo｜数据看板</b>
  <nav>
    <a href="#m1">债市</a><a href="#m2">英国出海</a><a href="#m3">数据质量</a>
    <a href="laifen-gtm/dashboard.html">徕芬德国 GTM 看板</a>
    <a href="index.html">回主页</a>
    <button class="tg" onclick="document.body.classList.toggle('dark')">深/浅色</button>
  </nav>
</div>
<main>
  <h1>统一数据看板</h1>
  <p class="sub">数据日期 @@date@@　生成于 @@gen@@　·　面向：@@aud@@　·　图表可缩放、hover 查看、点图例开关、右上角可下载 PNG</p>

  <div class="kpis">@@kpis@@</div>

  <section id="m1">
    <h2>模块一</h2><div class="secl">债市读数（中债 / 中国货币网 / 中国人民银行）</div>
    <div class="panel">@@c_curve@@</div>
    <div class="panel">@@c_change@@</div>
    <div class="panel">@@c_dr@@</div>
    <div class="panel">
      <h4>各期限明细与变动</h4>
      <div class="tscroll"><table>
        <tr><th>期限</th><th>当前（%）</th>@@th@@<th>周变动</th><th>月变动</th><th>年变动</th></tr>
        @@trs@@
      </table></div>
      <p class="note">1bp = 0.01 个百分点。红色为上行、绿色为下行。
      所有对比点取自同一条国债曲线（qxmc=1），未混入地方政府债或国开债曲线。</p>
    </div>
    <div class="panel">
      <h4>央行公开市场业务交易公告</h4>
      <ul>@@omo@@</ul>
      <p class="note">只列标题与原文链接。<b>净投放需同时核对投放与到期两侧</b>，本页不自动计算。</p>
    </div>
  </section>

  <section id="m2">
    <h2>模块二</h2><div class="secl">英国电动车市场（SMMT 官方注册数据）</div>
    <div class="panel">@@c_uk@@</div>
    <div class="panel">@@c_brands@@</div>
    <div class="panel">@@c_bev@@</div>
    <div class="note" style="margin-bottom:18px">
      口径提醒：<b>注册量 ≠ 销量 ≠ 交付量</b>；<b>品牌级 ≠ 车型级</b>；
      渠道占比是<b>全市场</b>口径，不是纯电细分、也不是单一车型的结构。
      BYD DOLPHIN SURF 未进入当月纯电前十，因此本页<b>不给它的车型级数字</b>。
    </div>
  </section>

  <section id="m3">
    <h2>模块三</h2><div class="secl">数据质量：来源、缺失与口径纪律</div>
    <div class="panel">
      <h4>来源登记（CN 侧）</h4>
      <div class="tscroll"><table><tr><th>编号</th><th>来源</th><th>原文</th></tr>@@srcs@@</table></div>
      <p class="note">全部为<b>单一权威来源，尚未独立交叉验证</b>。</p>
    </div>
    <div class="panel">
      <h4>明确没拿到的数据（留空，不推测）</h4>
      <ul>@@nr@@</ul>
      <p class="note">拿不到就写拿不到。用推测值把表格填满，比留空更糟。</p>
    </div>
    <div class="panel">
      <h4>口径红钱</h4>
      <ul>
        <li>国债曲线与地方政府债曲线<b>不混用</b></li>
        <li>DR（存款类机构）与 FR（全市场）<b>不混用</b></li>
        <li>期限 ≠ 久期；到期收益率 ≠ 持有期回报；价格变化 ≠ 总回报</li>
        <li><b>收益率变化不等于投资收益</b>，本页不做任何收益预测或回测</li>
        <li>各品牌续航测试口径不同，<b>不对齐前不排名</b></li>
      </ul>
    </div>
    <div class="btnrow">
      <a href="laifen-gtm/dashboard.html">打开徕芬德国 GTM 完整看板（5 模块）→</a>
      <a href="index.html">回个人主页</a>
    </div>
  </section>

  <footer>© Liu Boting · Evo　｜　本页由程序从官方公开来源生成，每日 12:00 自动刷新</footer>
</main>
</body></html>
"""


def main() -> None:
    html = build_html()
    evo = ROOT / "evo-site"
    if not evo.exists():
        evo.mkdir(parents=True)
    out = evo / "dashboard.html"
    out.write_text(html, encoding="utf-8")
    log_line(f"统一看板已生成：{out.relative_to(ROOT)}（{len(html)/1048576:.2f} MB）")


if __name__ == "__main__":
    main()
