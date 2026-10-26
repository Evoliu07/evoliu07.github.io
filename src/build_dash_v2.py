"""
生成 evo-site/dashboard.html —— 金融市场数据看板

结构：市场速览（7 个实时指标）→ 债市（曲线图 / 变动图 / 期限明细表）→ 公开市场公告
排版：每个板块独立分区，图表标题用 HTML 而非 Plotly title（彻底避免标题与图例重叠），
      图例固定在图下方；移动端全部上下排列。
用法： python src/build_dash_v2.py
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

FONT = "PingFang SC, Microsoft YaHei, Helvetica, sans-serif"
C_UP, C_DOWN, C_NEU = "#c0392b", "#1e8449", "#6d6258"
SERIES = ["#b9422f", "#245f73", "#177A5C", "#B8892F", "#7b6a58"]

PLOT_CFG = {"displaylogo": False, "responsive": True,
            "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d"]}


def layout(fig, h=380, legend=True):
    fig.update_layout(
        height=h,
        font=dict(family=FONT, size=12.5),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=56, r=24, t=14, b=52),
        legend=(dict(orientation="h", yanchor="top", y=-0.14, x=0,
                     font=dict(size=12)) if legend else None),
        xaxis=dict(gridcolor="rgba(140,120,90,.15)", zeroline=False,
                   linecolor="rgba(140,120,90,.35)"),
        yaxis=dict(gridcolor="rgba(140,120,90,.15)", zeroline=False,
                   linecolor="rgba(140,120,90,.35)"),
    )
    return fig


def fig_curve():
    rows = FIN["curve"]["rows"]
    ten = [r["tenor"] for r in rows]
    hist = FIN["curve"].get("history_labels", [])
    f = go.Figure()
    f.add_trace(go.Scatter(
        x=ten, y=[r["now"] for r in rows], name="最新", mode="lines+markers",
        line=dict(color=SERIES[0], width=3), marker=dict(size=8),
        hovertemplate="%{x}　%{y:.4f}%<extra>最新</extra>"))
    for i, h in enumerate(hist):
        f.add_trace(go.Scatter(
            x=ten, y=[r.get(h["label"]) for r in rows],
            name=f'{h["label"]}（{h["date"]}）', mode="lines+markers",
            line=dict(color=SERIES[(i + 1) % len(SERIES)], width=2, dash="dot"),
            marker=dict(size=5),
            hovertemplate="%{x}　%{y:.4f}%<extra>" + h["label"] + "</extra>"))
    f.update_yaxes(title_text="到期收益率（%）", ticksuffix="%")
    f.update_xaxes(title_text="期限")
    return layout(f, h=400)


def fig_change():
    rows = FIN["curve"]["rows"]
    ten = [r["tenor"] for r in rows]
    f = go.Figure()
    for key, nm, col in (("w1_bp", "近一周", SERIES[2]),
                         ("m1_bp", "近一月", SERIES[1]),
                         ("y1_bp", "近一年", SERIES[0])):
        f.add_trace(go.Bar(x=ten, y=[r.get(key) for r in rows], name=nm,
                           marker_color=col,
                           hovertemplate="%{x}　%{y:+.1f} bp<extra>" + nm + "</extra>"))
    f.update_yaxes(title_text="变动（bp）", ticksuffix="bp")
    f.update_xaxes(title_text="期限")
    f.update_layout(barmode="group", bargap=0.28, bargroupgap=0.08)
    return layout(f, h=360)


def nf(v, d=2, dash=True):
    return ("—" if v is None else f"{v:.{d}f}") if dash else ("" if v is None else f"{v:.{d}f}")


def build_html() -> str:
    items = RT.get("items") or []
    cgb = RT.get("cgb") or {}
    upd = RT.get("as_of") or ""

    # ---------- KPI ----------
    kpis = []
    for it in items:
        sign = it.get("chg_sign") or 0
        cls = "up" if sign > 0 else ("down" if sign < 0 else "")
        chg = it.get("chg_text") or ""
        sub = it.get("sub") or ""
        kpis.append(
            f'<div class="kpi"><div class="lb">{it["name"]}</div>'
            f'<div class="vl">{it["value"]}<span class="u">{it["unit"]}</span></div>'
            f'<div class="ch {cls}">{chg}</div>'
            f'<div class="sub">{sub}</div></div>')
    kpi_html = "".join(kpis)

    # ---------- 期限明细表 ----------
    hist = FIN["curve"].get("history_labels", [])
    th = "".join(f"<th>{h['label']}<br><span class='hd'>{h['date']}</span></th>" for h in hist)
    trs = ""
    for r in FIN["curve"]["rows"]:
        tds = "".join(f"<td>{nf(r.get(h['label']))}</td>" for h in hist)

        def cell(v):
            s = "up" if (v or 0) > 0.05 else ("down" if (v or 0) < -0.05 else "")
            t = "—" if v is None else f"{v:+.1f}"
            return f'<td class="{s}">{t}</td>'

        trs += (f"<tr><td class='tn'>{r['tenor']}</td><td>{nf(r['now'])}</td>{tds}"
                f"{cell(r.get('w1_bp'))}{cell(r.get('m1_bp'))}{cell(r.get('y1_bp'))}</tr>")

    omo = "".join(
        f'<li><a href="{o["url"]}" target="_blank" rel="noopener">{o["title"]}</a></li>'
        for o in (FIN.get("omo") or []))

    d_curve = to_html(fig_curve(), include_plotlyjs=True, full_html=False,
                      config=PLOT_CFG)
    d_change = to_html(fig_change(), include_plotlyjs=False, full_html=False,
                       config=PLOT_CFG)

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>金融数据看板 · 刘柏廷 Evo</title>
<style>
:root{{ --ink:#171411; --muted:#6d6258; --ink2:#3a332c; --paper:#f8f2e7; --line:#d8c8af;
  --red:#b9422f; --blue:#245f73; --white:#fffaf0; --surface:rgba(255,250,240,.66);
  --bar-bg:rgba(248,242,231,.95); --tint:rgba(184,137,47,.13);
  --font-b:"Songti SC","Noto Serif SC",Georgia,serif;
  --font-d:"PingFang SC","Microsoft YaHei",Helvetica,sans-serif;
  --bg:radial-gradient(circle at 18% 6%, rgba(184,137,47,.10), transparent 55%), #f8f2e7;
  --shadow:0 2px 10px rgba(60,45,25,.07); }}
body.dark{{ --ink:#e8e4dc; --muted:#9c948a; --ink2:#cfc9bf; --paper:#14120f; --line:#332e27;
  --white:#0d0b09; --surface:rgba(34,30,25,.72); --bar-bg:rgba(20,18,15,.95);
  --bg:radial-gradient(circle at 18% 6%, rgba(217,171,82,.10), transparent 55%), #14120f;
  --red:#e07a63; --blue:#7fb6cc; --tint:rgba(217,171,82,.14);
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
h1{{font-family:var(--font-d);font-size:27px;font-weight:600;letter-spacing:.01em}}
.stamp{{color:var(--muted);font-size:13.5px;font-family:var(--font-d);margin:6px 0 26px}}

.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:13px}}
.kpi{{background:var(--surface);border:1px solid var(--line);border-radius:13px;
  padding:15px 17px;box-shadow:var(--shadow)}}
.kpi .lb{{font-size:12.5px;color:var(--muted);font-family:var(--font-d);letter-spacing:.02em}}
.kpi .vl{{font-size:24px;font-weight:650;font-family:var(--font-d);line-height:1.35;
  font-variant-numeric:tabular-nums;margin-top:2px}}
.kpi .vl .u{{font-size:12.5px;font-weight:400;color:var(--muted);margin-left:3px}}
.kpi .ch{{font-size:13px;font-family:var(--font-d);font-variant-numeric:tabular-nums;
  min-height:20px;margin-top:3px}}
.kpi .sub{{font-size:11.5px;color:var(--muted);font-family:var(--font-d);margin-top:3px}}
.up{{color:var(--red)}} .down{{color:#1e8449}}

section{{margin-top:38px}}
h2{{font-family:var(--font-d);font-size:12.5px;letter-spacing:.17em;text-transform:uppercase;
  color:var(--red);font-weight:700;margin-bottom:14px}}
.grid2{{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start}}
.card{{background:var(--surface);border:1px solid var(--line);border-radius:14px;
  padding:17px 19px;box-shadow:var(--shadow);min-width:0}}
.card h3{{font-family:var(--font-d);font-size:15px;font-weight:650;margin-bottom:12px;
  padding-bottom:9px;border-bottom:1px solid var(--line)}}
.card + .card{{margin-top:16px}}
.chartbox{{width:100%;overflow-x:auto}}
table{{width:100%;border-collapse:collapse;font-size:13.5px;font-family:var(--font-d);
  font-variant-numeric:tabular-nums}}
th,td{{padding:8px 9px;text-align:right;border-bottom:1px solid var(--line);white-space:nowrap}}
th:first-child,td:first-child{{text-align:left}}
th{{color:var(--muted);font-weight:600;font-size:12px}}
th .hd{{font-weight:400;font-size:11px;opacity:.8}}
td.tn{{font-weight:650}}
tr:last-child td{{border-bottom:0}}
.tbwrap{{overflow-x:auto;margin:0 -4px}}
ul{{margin:4px 0 0 18px}} li{{margin:7px 0;font-size:14.5px}}
.units{{font-size:12.5px;color:var(--muted);font-family:var(--font-d);margin-top:10px}}
footer{{margin-top:44px;padding-top:22px;border-top:1px solid var(--line);text-align:center;
  color:var(--muted);font-size:12.5px;font-family:var(--font-d);line-height:1.9}}
@media(max-width:900px){{
  .grid2{{grid-template-columns:1fr}}
  .bar{{height:auto;padding:10px 14px;flex-wrap:wrap}}
  .bar nav{{gap:12px;font-size:12.5px}}
  main{{padding:22px 15px 56px}}
  h1{{font-size:22px}}
  .kpis{{grid-template-columns:repeat(auto-fit,minmax(146px,1fr));gap:10px}}
  .kpi .vl{{font-size:21px}}
}}
</style></head>
<body>
<div class="bar">
  <b><a href="index.html" style="color:inherit">刘柏廷 · Evo</a>　<span style="color:var(--muted);font-weight:400">金融数据看板</span></b>
  <nav>
    <a href="#mkt">市场速览</a><a href="#bond">债市</a><a href="#omo">公开市场</a>
    <a href="laifen-gtm/dashboard.html">出海看板</a>
    <a href="index.html">回主页</a>
    <button class="tg" onclick="document.body.classList.toggle('dark')">深/浅色</button>
  </nav>
</div>

<main>
  <h1>金融市场数据看板</h1>
  <p class="stamp">更新于 {upd}（北京时间）</p>

  <section id="mkt">
    <h2>市场速览</h2>
    <div class="kpis">{kpi_html}</div>
  </section>

  <section id="bond">
    <h2>债市</h2>
    <div class="card">
      <h3>国债收益率曲线</h3>
      <div class="chartbox">{d_curve}</div>
    </div>
    <div class="card" style="margin-top:16px">
      <h3>各期限收益率变动</h3>
      <div class="chartbox">{d_change}</div>
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
  </section>

  <section id="omo">
    <h2>公开市场</h2>
    <div class="card">
      <h3>中国人民银行公开市场业务交易公告</h3>
      <ul>{omo}</ul>
    </div>
  </section>

  <footer>
    数据来源：上海证券交易所 · 深圳证券交易所 · 香港交易所 · 中央国债登记结算有限责任公司 · 中国外汇交易中心<br>
    历史数据仅用于本页展示
  </footer>
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
    log_line(f"金融看板已生成：{out.relative_to(ROOT)}（{len(html)/1048576:.2f} MB）")
    log_line(f"  实时指标 {len(RT.get('items') or [])} 项 · 曲线日期 {FIN['meta']['data_date']} "
             f"· 对比点 {len(FIN['curve'].get('history_labels', []))} 个")


if __name__ == "__main__":
    main()
