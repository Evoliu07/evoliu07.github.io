"""
生成 evo-site/overseas.html —— 出海市场看板（真实数据）

数据：SMMT 英国乘用车注册官方公开数据 + 各品牌英国官网公布规格
用法： python src/build_overseas.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, log_line                                    # noqa: E402

import plotly.graph_objects as go                                    # noqa: E402
from plotly.io import to_html                                        # noqa: E402

SEA = json.loads((ROOT / "data" / "dash" / "overseas.json").read_text(encoding="utf-8"))

FONT = "PingFang SC, Microsoft YaHei, Helvetica, sans-serif"
S = ["#0a6b4c", "#1a3c6e", "#b9422f", "#B8892F", "#245f73", "#7b6a58"]
CFG = {"displaylogo": False, "responsive": True,
       "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"]}
LAB = {"BEV": "纯电", "PHEV": "插混", "HEV": "混动", "PETROL": "汽油", "DIESEL": "柴油",
       "FLEET": "车队", "PRIVATE": "私人", "BUSINESS": "公司自用"}


def layout(fig, h=380, legend=True):
    fig.update_layout(
        height=h, font=dict(family=FONT, size=12.5),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=64, r=26, t=14, b=52),
        legend=(dict(orientation="h", yanchor="top", y=-0.14, x=0, font=dict(size=12))
                if legend else None),
        xaxis=dict(gridcolor="rgba(140,120,90,.15)", zeroline=False,
                   linecolor="rgba(140,120,90,.35)"),
        yaxis=dict(gridcolor="rgba(140,120,90,.15)", zeroline=False,
                   linecolor="rgba(140,120,90,.35)"))
    return fig


def fig_cn():
    b = sorted(SEA["cn_brands"], key=lambda x: x["units"] or 0)
    f = go.Figure(go.Bar(
        x=[x["units"] for x in b], y=[x["brand"] for x in b], orientation="h",
        marker=dict(color=S[0]), text=[f'{int(x["units"]):,}' for x in b],
        textposition="outside", textfont=dict(family=FONT, size=12),
        hovertemplate="%{y}　%{x:,.0f} 辆<extra></extra>"))
    f.update_xaxes(title_text="当月注册量（辆）")
    f.update_layout(margin=dict(l=88, r=44, t=14, b=52))
    return layout(f, h=430, legend=False)


NICE = {"Mg": "MG", "Byd": "BYD", "Bmw": "BMW", "Gwm": "GWM", "Ds": "DS",
        "Jaecoo": "JAECOO", "Omoda": "OMODA", "Kia": "Kia", "Skoda": "Skoda"}


def pretty(name):
    return NICE.get(name, name)


def fig_channel():
    ch = SEA["channel"]
    f = go.Figure(go.Bar(
        x=[c["share"] for c in ch], y=[LAB.get(c["key"], c["key"]) for c in ch],
        orientation="h", marker_color=S[1],
        text=[f'{c["share"]:.1f}%' for c in ch], textposition="outside",
        textfont=dict(family=FONT, size=12),
        hovertemplate="%{y}　占当月注册 %{x:.1f}%<extra></extra>"))
    f.update_xaxes(title_text="占当月新车注册比重（%）", ticksuffix="%",
                   range=[0, max(c["share"] for c in ch) * 1.28])
    f.update_layout(margin=dict(l=78, r=44, t=14, b=52))
    return layout(f, h=430, legend=False)


def fig_topbrands():
    rows = [x for x in (SEA.get("top_brands") or [])
            if x["brand"] != "Grand Total"][:10]
    if not rows:
        return None
    rows = sorted(rows, key=lambda x: x["units"] or 0)
    f = go.Figure(go.Bar(
        x=[x["units"] for x in rows], y=[pretty(x["brand"]) for x in rows],
        orientation="h", marker_color=S[4],
        text=[f'{int(x["units"]):,}' for x in rows], textposition="outside",
        textfont=dict(family=FONT, size=12),
        hovertemplate="%{y}　%{x:,.0f} 辆<extra></extra>"))
    f.update_xaxes(title_text="当月注册量（辆）")
    f.update_layout(margin=dict(l=100, r=48, t=14, b=52))
    return layout(f, h=430, legend=False)


def fig_bev():
    t = sorted(SEA["bev_top10"], key=lambda x: x["units"])
    f = go.Figure(go.Bar(
        x=[x["units"] for x in t], y=[f'{x["rank"]}. {x["model"]}' for x in t],
        orientation="h", marker_color=S[2],
        text=[f'{int(x["units"]):,}' for x in t], textposition="outside",
        textfont=dict(family=FONT, size=12),
        hovertemplate="%{y}　%{x:,.0f} 辆<extra></extra>"))
    f.update_xaxes(title_text="当月注册量（辆）")
    f.update_layout(margin=dict(l=132, r=44, t=14, b=52))
    return layout(f, h=430, legend=False)


def fig_brand_yoy():
    b = sorted([x for x in SEA["cn_brands"]
                if 0 < (x.get("yoy") or 0) <= 500],
               key=lambda x: x["yoy"])
    if not b:
        return None
    f = go.Figure(go.Bar(
        x=[x["yoy"] for x in b], y=[x["brand"] for x in b], orientation="h",
        marker=dict(color=S[3]), text=[f'+{x["yoy"]:.1f}%' for x in b],
        textposition="outside", textfont=dict(family=FONT, size=12),
        hovertemplate="%{y}　%{x:.1f}%<extra>同比</extra>"))
    f.update_xaxes(title_text="当月注册量同比（%）", ticksuffix="%",
                   range=[0, max(x["yoy"] for x in b) * 1.22])
    f.update_layout(margin=dict(l=88, r=52, t=14, b=52))
    return layout(f, h=430, legend=False)


def build_html() -> str:
    mk = SEA["market"]
    cn = SEA["cn_brands"]
    cn_total = sum(x["units"] or 0 for x in cn)
    cn_ytd = sum((x.get("ytd") or 0) for x in cn)
    cn_share = cn_total / (mk["total_month"] or 1) * 100
    top = max(cn, key=lambda x: x["units"] or 0)
    fast = max([x for x in cn if 0 < (x.get("yoy") or 0) <= 500],
               key=lambda x: x["yoy"])
    fast_units = int(fast["units"])
    fleet = next(c for c in SEA["channel"] if c["key"] == "FLEET")
    priv = next(c for c in SEA["channel"] if c["key"] == "PRIVATE")

    kpis = [
        (f'{int(mk["total_month"]):,}', "辆", "英国当月新车注册", ""),
        (f'{int(cn_total):,}', "辆", "中国与新兴品牌当月合计", f'占当月 {cn_share:.1f}%'),
        (f'{int(top["units"]):,}', "辆", f'当月最高 · {top["brand"]}', f'同比 +{top["yoy"]:.1f}%'),
        (f'+{fast["yoy"]:.1f}%', "", f'同比增速最高 · {fast["brand"]}',
         f'当月 {fast_units:,} 辆'),
        (f'{fleet["share"]:.1f}%', "", "车队渠道占比", f'私人 {priv["share"]:.1f}%'),
        (f'{int(cn_ytd):,}', "辆", "中国与新兴品牌年初至今", ""),
    ]
    kpi_html = "".join(
        f'<div class="kpi"><div class="lb">{l}</div>'
        f'<div class="vl">{v}<span class="u">{u}</span></div>'
        f'<div class="ch">{c}</div></div>' for v, u, l, c in kpis)

    rows = ""
    for x in cn:
        yoy = x.get("yoy")
        cls = "up" if (yoy or 0) > 0.05 else ("down" if (yoy or 0) < -0.05 else "")
        rows += (f'<tr><td class="tn">{x["brand"]}</td>'
                 f'<td>{int(x["units"]):,}</td><td>{x.get("share"):.2f}%</td>'
                 f'<td class="{cls}">{("%+.2f%%" % yoy) if yoy is not None else "—"}</td>'
                 f'<td>{int(x.get("ytd") or 0):,}</td></tr>')

    comp = ""
    for c in SEA["competitors"]:
        if not c.get("range_miles") and not c.get("battery_kwh"):
            continue                      # 官方页未公布规格的车型不展示，不留空列
        rng = " / ".join(c["range_miles"]) if c.get("range_miles") else "—"
        bat = " / ".join(c["battery_kwh"]) if c.get("battery_kwh") else "—"
        comp += (f'<tr><td class="tn">{c["model"]}</td><td>{rng}</td><td>{bat}</td>'
                 f'<td><a href="{c["url"]}" target="_blank" rel="noopener">'
                 f'{c["url"].split("/")[2]}</a></td></tr>')

    d1 = to_html(fig_cn(), include_plotlyjs=True, full_html=False, config=CFG)
    d2 = to_html(fig_channel(), include_plotlyjs=False, full_html=False, config=CFG)
    d3 = to_html(fig_bev(), include_plotlyjs=False, full_html=False, config=CFG)
    f4 = fig_brand_yoy()
    d4 = to_html(f4, include_plotlyjs=False, full_html=False, config=CFG) if f4 else ""
    f5 = fig_topbrands()
    d5 = to_html(f5, include_plotlyjs=False, full_html=False, config=CFG) if f5 else ""

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>出海市场看板 · 刘柏廷 Evo</title>
<style>
:root{{ --ink:#171411; --muted:#6d6258; --ink2:#3a332c; --paper:#f8f2e7; --paper-deep:#ece1cf;
  --line:#d8c8af; --red:#b9422f; --blue:#245f73; --green:#0a6b4c; --white:#fffaf0;
  --surface:rgba(255,250,240,.66); --bar-bg:rgba(248,242,231,.95);
  --font-b:"Songti SC","Noto Serif SC",Georgia,serif;
  --font-d:"PingFang SC","Microsoft YaHei",Helvetica,sans-serif;
  --bg:radial-gradient(circle at 80% 4%, rgba(10,107,76,.09), transparent 55%), #f8f2e7;
  --shadow:0 2px 10px rgba(60,45,25,.07); --tint:rgba(10,107,76,.10); }}
body.dark{{ --ink:#e8e4dc; --muted:#9c948a; --ink2:#cfc9bf; --paper:#14120f; --line:#332e27;
  --white:#0d0b09; --surface:rgba(34,30,25,.72); --bar-bg:rgba(20,18,15,.95);
  --bg:radial-gradient(circle at 80% 4%, rgba(79,190,134,.10), transparent 55%), #14120f;
  --red:#e07a63; --blue:#7fb6cc; --green:#4fbe86; --tint:rgba(79,190,134,.14);
  --shadow:0 2px 14px rgba(0,0,0,.5); }}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:var(--font-b);background:var(--bg);color:var(--ink);line-height:1.8;font-size:16px}}
a{{color:var(--blue);text-decoration:none}} a:hover{{text-decoration:underline}}
.bar{{position:sticky;top:0;z-index:60;background:var(--bar-bg);backdrop-filter:blur(8px);
  border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;
  gap:14px;padding:0 24px;height:58px;font-family:var(--font-d)}}
.bar b{{font-size:15px;font-weight:600}}
.bar nav{{display:flex;gap:18px;font-size:13.5px;align-items:center;flex-wrap:wrap}}
.bar nav a{{color:var(--muted)}} .bar nav a:hover{{color:var(--ink)}}
.tg{{border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:99px;
  padding:5px 13px;font:inherit;font-size:12.5px;cursor:pointer;font-family:var(--font-d)}}
main{{max-width:1120px;margin:0 auto;padding:30px 26px 70px}}
h1{{font-family:var(--font-d);font-size:27px;font-weight:600}}
.stamp{{color:var(--muted);font-size:13.5px;font-family:var(--font-d);margin:6px 0 26px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(172px,1fr));gap:13px}}
.kpi{{background:var(--surface);border:1px solid var(--line);border-radius:13px;padding:15px 17px;
  box-shadow:var(--shadow)}}
.kpi .lb{{font-size:12.5px;color:var(--muted);font-family:var(--font-d)}}
.kpi .vl{{font-size:23px;font-weight:650;font-family:var(--font-d);margin-top:2px;
  font-variant-numeric:tabular-nums;line-height:1.35}}
.kpi .vl .u{{font-size:12.5px;font-weight:400;color:var(--muted);margin-left:3px}}
.kpi .ch{{font-size:12.5px;color:var(--muted);font-family:var(--font-d);margin-top:3px}}
section{{margin-top:38px}}
h2{{font-family:var(--font-d);font-size:12.5px;letter-spacing:.17em;text-transform:uppercase;
  color:var(--red);font-weight:700;margin-bottom:14px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start}}
.card{{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:17px 19px;
  box-shadow:var(--shadow);min-width:0}}
.card h3{{font-family:var(--font-d);font-size:15px;font-weight:650;margin-bottom:12px;
  padding-bottom:9px;border-bottom:1px solid var(--line)}}
.chartbox{{width:100%;overflow-x:auto}}
table{{width:100%;border-collapse:collapse;font-size:13.5px;font-family:var(--font-d);
  font-variant-numeric:tabular-nums}}
th,td{{padding:8px 9px;text-align:right;border-bottom:1px solid var(--line);white-space:nowrap}}
th:first-child,td:first-child{{text-align:left}}
th{{color:var(--muted);font-weight:600;font-size:12px}}
td.tn{{font-weight:650}}
tr:last-child td{{border-bottom:0}}
.tbwrap{{overflow-x:auto}}
.up{{color:var(--red)}} .down{{color:#1e8449}}
footer{{margin-top:44px;padding-top:22px;border-top:1px solid var(--line);text-align:center;
  color:var(--muted);font-size:12.5px;font-family:var(--font-d);line-height:1.9}}
@media(max-width:900px){{
  .grid2{{grid-template-columns:1fr}}
  .bar{{height:auto;padding:10px 14px;flex-wrap:wrap}}
  .bar nav{{gap:12px;font-size:12.5px}}
  main{{padding:22px 15px 56px}} h1{{font-size:22px}}
  .kpis{{grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:10px}}
  .kpi .vl{{font-size:20px}}
}}
</style></head>
<body>
<div class="bar">
  <b><a href="index.html" style="color:inherit">刘柏廷 · Evo</a>　<span style="color:var(--muted);font-weight:400">出海市场看板</span></b>
  <nav>
    <a href="#cn">中国品牌</a><a href="#mix">市场结构</a><a href="#bev">纯电车型</a><a href="#comp">竞品规格</a>
    <a href="dashboard.html">金融数据看板</a>
    <a href="index.html">回主页</a>
    <button class="tg" onclick="document.body.classList.toggle('dark')">深/浅色</button>
  </nav>
</div>

<main>
  <h1>英国乘用车市场看板</h1>
  <p class="stamp">数据来源：SMMT 英国乘用车注册公开数据　·　数据日期 {SEA['meta']['data_date']}</p>

  <div class="kpis">{kpi_html}</div>

  <section id="cn">
    <h2>中国与新兴品牌</h2>
    <div class="grid2">
      <div class="card">
        <h3>当月注册量</h3>
        <div class="chartbox">{d1}</div>
      </div>
      <div class="card">
        <h3>当月注册量同比</h3>
        <div class="chartbox">{d4}</div>
      </div>
    </div>
    <div class="card" style="margin-top:16px">
      <h3>品牌明细</h3>
      <div class="tbwrap"><table>
        <tr><th>品牌</th><th>当月注册（辆）</th><th>市场份额</th><th>同比</th><th>年初至今（辆）</th></tr>
        {rows}
      </table></div>
    </div>
  </section>

  <section id="mix">
    <h2>市场结构</h2>
    <div class="grid2">
      <div class="card">
        <h3>销售渠道占比</h3>
        <div class="chartbox">{d2}</div>
      </div>
      <div class="card">
        <h3>全市场品牌注册量前十</h3>
        <div class="chartbox">{d5}</div>
      </div>
    </div>
  </section>

  <section id="bev">
    <h2>纯电车型</h2>
    <div class="card">
      <h3>纯电车型注册量前十</h3>
      <div class="chartbox">{d3}</div>
    </div>
  </section>

  <section id="comp">
    <h2>竞品规格</h2>
    <div class="card">
      <h3>同级车型官方公布规格</h3>
      <div class="tbwrap"><table>
        <tr><th>车型</th><th>官方续航（英里）</th><th>电池容量（kWh）</th><th>官方来源</th></tr>
        {comp}
      </table></div>
    </div>
  </section>

  <footer>
    数据来源：SMMT（英国汽车制造商与贸易商协会）乘用车注册数据 · 各品牌英国官网<br>
    注册量为新车上牌登记口径
  </footer>
</main>
</body></html>
"""


def main() -> None:
    html = build_html()
    evo = ROOT / "evo-site"
    if not evo.exists():
        evo.mkdir(parents=True)
    out = evo / "overseas.html"
    out.write_text(html, encoding="utf-8")
    log_line(f"出海看板已生成：{out.relative_to(ROOT)}（{len(html)/1048576:.2f} MB）")


if __name__ == "__main__":
    main()
