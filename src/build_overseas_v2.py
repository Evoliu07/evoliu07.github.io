"""
生成 evo-site/overseas.html —— 出海看板（两个项目）
  项目一 比亚迪（英国）：真实 SMMT 注册数据
  项目二 徕芬（德国）：真实 UN Comtrade 贸易数据 + 五个模块图表

用法： python src/build_overseas_v2.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, log_line                                     # noqa: E402
from build_dashboards import (CSS, CFG, FONT, S, LAB, NICE,           # noqa: E402
                             bar, kpi_block, layout)

import plotly.graph_objects as go                                     # noqa: E402
from plotly.io import to_html                                         # noqa: E402

SEA = json.loads((ROOT / "data" / "dash" / "overseas.json").read_text(encoding="utf-8"))
DE = json.loads((ROOT / "data" / "dash" / "germany_trade.json").read_text(encoding="utf-8"))
LF = json.loads((ROOT / "data" / "dash" / "laifen_demo.json").read_text(encoding="utf-8"))


# ───────────────────────── 比亚迪（英国）
def fig_cn():
    b = sorted(SEA["cn_brands"], key=lambda x: x["units"] or 0)
    f = go.Figure(go.Bar(x=[x["units"] for x in b],
                         y=[NICE.get(x["brand"], x["brand"]) for x in b], orientation="h",
                         marker_color=S[2], text=[f'{int(x["units"]):,}' for x in b],
                         textposition="outside", textfont=dict(family=FONT, size=12),
                         hovertemplate="%{y}　%{x:,.0f} 辆<extra></extra>"))
    f.update_xaxes(title_text="当月注册量（辆）")
    return layout(f, h=430, legend=False, margin=dict(l=88, r=44, t=14, b=52))


def fig_cn_yoy():
    b = sorted([x for x in SEA["cn_brands"] if 0 < (x.get("yoy") or 0) <= 500],
               key=lambda x: x["yoy"])
    if not b:
        return None
    f = go.Figure(go.Bar(x=[x["yoy"] for x in b],
                         y=[NICE.get(x["brand"], x["brand"]) for x in b], orientation="h",
                         marker_color=S[3], text=[f'+{x["yoy"]:.1f}%' for x in b],
                         textposition="outside", textfont=dict(family=FONT, size=12),
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
    rows = sorted([x for x in (SEA.get("top_brands") or []) if x["brand"] != "Grand Total"][:10],
                  key=lambda x: x["units"] or 0)
    if not rows:
        return None
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


# ───────────────────────── 徕芬（德国）真实贸易
def fig_de_trade():
    ms = DE["months"]
    f = go.Figure()
    f.add_trace(go.Scatter(x=[m["label"] for m in ms],
                           y=[m["world_usd"] / 1e6 for m in ms], name="德国进口总额",
                           mode="lines+markers", line=dict(color=S[1], width=3),
                           marker=dict(size=7),
                           hovertemplate="%{x}　%{y:,.1f} 百万美元<extra>总额</extra>"))
    f.add_trace(go.Scatter(x=[m["label"] for m in ms],
                           y=[m["china_usd"] / 1e6 for m in ms], name="其中自中国",
                           mode="lines+markers", line=dict(color=S[0], width=2.4),
                           marker=dict(size=5), fill="tonexty",
                           hovertemplate="%{x}　%{y:,.1f} 百万美元<extra>自中国</extra>"))
    f.update_yaxes(title_text="进口额（百万美元）")
    return layout(f, h=400)


def fig_de_share():
    ms = DE["months"]
    f = go.Figure(go.Bar(x=[m["label"] for m in ms], y=[m["china_share"] for m in ms],
                         marker_color=S[2], text=[f'{m["china_share"]:.0f}%' for m in ms],
                         textposition="outside", textfont=dict(family=FONT, size=12),
                         hovertemplate="%{x}　中国占 %{y:.1f}%<extra></extra>"))
    f.update_yaxes(title_text="自中国进口占比（%）", ticksuffix="%", range=[0, 100])
    return layout(f, h=360, legend=False)


# ───────────────────────── 徕芬 五个模块
def fig_sentiment():
    st = LF["sentiment_trend"]
    f = go.Figure()
    for i, b in enumerate(st["brands"]):
        f.add_trace(go.Scatter(x=st["months"], y=b["values"], name=b["brand"],
                               mode="lines+markers",
                               line=dict(color=S[i % len(S)], width=2.2), marker=dict(size=4),
                               hovertemplate="%{x}　" + b["brand"] + "　%{y:.3f}<extra></extra>"))
    f.update_yaxes(title_text="情感均值")
    return layout(f, h=380)


def fig_topics():
    t = LF["topics"]
    labels, parents, vals = ["德国市场抱怨主题"], [""], [0]
    for x in t:
        labels.append(f'{x["brand"]} · {x["topic"]}')
        parents.append("德国市场抱怨主题")
        vals.append(x["mentions"])
    f = go.Figure(go.Treemap(labels=labels, parents=parents, values=vals,
                             branchvalues="remainder", textinfo="label+value",
                             hovertemplate="%{label}<br>提及 %{value}<extra></extra>",
                             marker=dict(colors=S * 20, line=dict(width=2, color="#fffaf0")),
                             textfont=dict(family=FONT, size=12)))
    return layout(f, h=420, legend=False)


def fig_opp():
    o = sorted(LF["opportunity"], key=lambda x: x["opportunity"])[-12:]
    f = go.Figure(go.Bar(x=[x["opportunity"] for x in o],
                         y=[f'{x["brand"]} · {x["topic"]}' for x in o], orientation="h",
                         marker_color=S[2], text=[f'{x["opportunity"]:.2f}' for x in o],
                         textposition="outside", textfont=dict(family=FONT, size=11),
                         hovertemplate="%{y}　机会指数 %{x:.2f}<extra></extra>"))
    f.update_xaxes(title_text="机会指数")
    return layout(f, h=420, legend=False, margin=dict(l=150, r=48, t=14, b=52))


def fig_tier():
    td = LF["tier_dist"]
    f = go.Figure(go.Bar(x=[x["tier"] for x in td], y=[x["count"] for x in td],
                         marker_color=S[1], text=[str(x["count"]) for x in td],
                         textposition="outside", textfont=dict(family=FONT, size=13),
                         hovertemplate="%{x} 档　%{y} 位<extra></extra>"))
    f.update_yaxes(title_text="达人数（位）")
    return layout(f, h=340, legend=False)


def fig_kol():
    k = LF["kol_bubble"]
    order = {"S": 0, "A": 1, "B": 2, "C": 3, "D": 4}
    f = go.Figure()
    for tier in ["S", "A", "B", "C"]:
        g = [x for x in k if x["tier"] == tier]
        if not g:
            continue
        f.add_trace(go.Scatter(
            x=[x["subscribers"] for x in g], y=[x["engagement"] for x in g],
            mode="markers", name=f"{tier} 档",
            marker=dict(size=[max(6, x["score"] / 3) for x in g],
                        color=S[order.get(tier, 2) % len(S)], opacity=.72,
                        line=dict(width=1, color="#fffaf0")),
            text=[f'{x["name"]}<br>综合分 {x["score"]}' for x in g],
            hovertemplate="%{text}<br>粉丝 %{x:,.0f}　互动率 %{y:.2f}%<extra></extra>"))
    f.update_xaxes(title_text="粉丝量", type="log")
    f.update_yaxes(title_text="互动率（%）", ticksuffix="%")
    return layout(f, h=430)


def fig_price():
    pc = LF["price_curves"]
    f = go.Figure()
    for i, b in enumerate(pc["brands"]):
        f.add_trace(go.Scatter(x=pc["dates"], y=b["values"], name=b["brand"],
                               mode="lines", line=dict(color=S[i % len(S)], width=2),
                               hovertemplate="%{x}　" + b["brand"] + "　€%{y:.2f}<extra></extra>"))
    f.update_yaxes(title_text="价格（欧元）", tickprefix="€")
    return layout(f, h=420)


def fig_funnel():
    fu = LF["funnel"]
    tot = {k: sum(x[k] for x in fu) for k in
           ("impressions", "clicks", "detail_views", "add_to_cart", "orders", "repeat_orders")}
    f = go.Figure(go.Funnel(
        y=["曝光", "点击", "详情页", "加购", "成交", "复购"],
        x=[tot["impressions"], tot["clicks"], tot["detail_views"],
           tot["add_to_cart"], tot["orders"], tot["repeat_orders"]],
        textinfo="value+percent previous",
        hovertemplate="%{y}　%{x:,.0f}<extra></extra>"))
    return layout(f, h=420, legend=False)


def fig_cac():
    fu = LF["funnel"]
    f = go.Figure()
    f.add_trace(go.Bar(x=[x["channel"] for x in fu], y=[x["orders"] for x in fu],
                       name="成交量（单）", marker_color=S[1],
                       text=[f"{x['orders']:,}" for x in fu], textposition="outside",
                       textfont=dict(family=FONT, size=12)))
    f.add_trace(go.Scatter(x=[x["channel"] for x in fu], y=[x["cac_eur"] for x in fu],
                           name="获客成本（欧元）", yaxis="y2", mode="markers+lines",
                           marker=dict(size=12, color=S[0]),
                           line=dict(color=S[0], width=2),
                           hovertemplate="%{x}　€%{y:.2f}<extra>获客成本</extra>"))
    f.update_layout(yaxis2=dict(title="获客成本（欧元）", overlaying="y", side="right",
                                showgrid=False, tickprefix="€"))
    f.update_yaxes(title_text="成交量（单）")
    return layout(f, h=420, margin=dict(l=56, r=76, t=14, b=52))


def fig_loc():
    lo = LF["localization"]
    dims = [("compliance", "合规"), ("info_density", "信息密度"), ("cultural_fit", "文化契合"),
            ("verifiability", "可验证"), ("conversion_expectation", "转化预期")]
    f = go.Figure()
    for i, (k, nm) in enumerate(dims):
        f.add_trace(go.Bar(name=nm, x=[x["version"] for x in lo], y=[x[k] for x in lo],
                           marker_color=S[i % len(S)], hovertemplate="%{x}　" + nm +
                           "　%{y:.1f}<extra></extra>"))
    f.update_layout(barmode="group", bargap=0.3, bargroupgap=0.08)
    f.update_yaxes(title_text="人工评分（分）")
    return layout(f, h=400)


# ══════════════════════════ 页面
def build() -> str:
    mk, cn = SEA["market"], SEA["cn_brands"]
    cn_total = sum(x["units"] or 0 for x in cn)
    cn_ytd = sum((x.get("ytd") or 0) for x in cn)
    cn_share = cn_total / (mk["total_month"] or 1) * 100
    byd = next((x for x in cn if x["brand"] == "Byd"), None)
    fast = max([x for x in cn if 0 < (x.get("yoy") or 0) <= 500], key=lambda x: x["yoy"])
    fleet = next(c for c in SEA["channel"] if c["key"] == "FLEET")
    priv = next(c for c in SEA["channel"] if c["key"] == "PRIVATE")

    byd_kpis = kpi_block([
        (f'{int(mk["total_month"]):,}', "辆", "英国当月新车注册", "", "", ""),
        (f'{int(cn_total):,}', "辆", "中国与新兴品牌当月合计", "", "", f'占当月 {cn_share:.1f}%'),
        (f'{int(byd["units"]):,}', "辆", "比亚迪当月注册", f'同比 +{byd["yoy"]:.1f}%', "up",
         f'年初至今 {int(byd["ytd"]):,} 辆') if byd else
        (f'{int(cn_total):,}', "辆", "中国与新兴品牌合计", "", "", ""),
        (f'+{fast["yoy"]:.1f}%', "", f'同比增速最高 · {NICE.get(fast["brand"], fast["brand"])}',
         "", "", f'当月 {int(fast["units"]):,} 辆'),
        (f'{fleet["share"]:.1f}%', "", "车队渠道占比", "", "", f'私人 {priv["share"]:.1f}%'),
        (f'{int(cn_ytd):,}', "辆", "中国与新兴品牌年初至今", "", "", "")])

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

    # 徕芬：真实贸易 KPI
    dm = DE["months"]
    last = dm[-1]
    de_kpis = kpi_block([
        (f'{last["world_usd"]/1e6:,.1f}', "百万美元", f'{last["label"]} 德国进口额', "", "", ""),
        (f'{last["china_usd"]/1e6:,.1f}', "百万美元", "其中自中国进口", "", "", ""),
        (f'{last["china_share"]:.1f}%', "", "自中国占比", "", "",
         f'{"+" if last["china_share"] >= dm[-2]["china_share"] else ""}'
         f'{last["china_share"] - dm[-2]["china_share"]:.1f} 个百分点（环比）' if len(dm) > 1 else
         ""),
        (f'{sum(m["world_usd"] for m in dm)/1e6:,.0f}', "百万美元", f'近 {len(dm)} 个月累计进口',
         "", "", "")])

    de_rows = ""
    for m in dm:
        de_rows += (f'<tr><td class="tn">{m["label"]}</td>'
                    f'<td>{m["world_usd"]/1e6:,.1f}</td><td>{m["china_usd"]/1e6:,.1f}</td>'
                    f'<td>{m["china_share"]:.1f}%</td></tr>')

    sl = LF["shortlist"][:10]
    sl_rows = "".join(
        f'<tr><td class="tn">{x["name"]}</td><td>{x["platform"]}</td><td>{x["tier"]}</td>'
        f'<td>{x["subscribers"]:,}</td><td>{x["score"]:.1f}</td>'
        f'<td>€{x["est_fee_eur"]:,.0f}</td><td>€{x["est_cac_eur"]:,.0f}</td></tr>'
        for x in sl)

    ct = LF["comp_table"]
    ct_rows = "".join(
        f'<tr><td class="tn">{x["brand"]}</td><td>{x["sku"]}</td>'
        f'<td>€{x["price_eur"]:,.2f}</td><td>€{x["list_eur"]:,.2f}</td>'
        f'<td>{x["coupon_pct"]:.0f}%</td><td>{x["bsr"]:,}</td><td>{x["rating"]:.2f}</td></tr>'
        for x in ct)

    fu = LF["funnel"]
    fu_rows = "".join(
        f'<tr><td class="tn">{x["channel"]}</td><td>{x["impressions"]:,}</td>'
        f'<td>{x["orders"]:,}</td><td>{x["repeat_rate"]:.1f}%</td>'
        f'<td>€{x["cac_eur"]:,.2f}</td></tr>' for x in fu)

    lo = LF["localization"]
    lo_rows = "".join(
        f'<tr><td class="tn">{x["version"]}</td><td>{x["compliance"]:.0f}</td>'
        f'<td>{x["info_density"]:.0f}</td><td>{x["cultural_fit"]:.0f}</td>'
        f'<td>{x["verifiability"]:.0f}</td><td>{x["conversion_expectation"]:.0f}</td>'
        f'<td><b>{x["total"]:.0f}</b></td><td>{x["headline"]}</td></tr>' for x in lo)

    figs = [fig_cn(), fig_topbrands(), fig_cn_yoy(), fig_channel(), fig_bev(),
            fig_de_trade(), fig_de_share(), fig_sentiment(), fig_topics(), fig_opp(),
            fig_tier(), fig_kol(), fig_price(), fig_funnel(), fig_cac(), fig_loc()]
    divs, first = [], True
    for fg in figs:
        if fg is None:
            divs.append("")
            continue
        divs.append(to_html(fg, include_plotlyjs=first, full_html=False, config=CFG))
        first = False
    (d_cn, d_tb, d_yoy, d_ch, d_bev, d_tr, d_sh, d_se, d_tp, d_op,
     d_tr2, d_kb, d_pr, d_fn, d_cac, d_lc) = divs

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>出海看板 · 刘柏廷 Evo</title><style>{CSS}</style></head><body>
{bar([("比亚迪（英国）", "byd"), ("徕芬（德国）", "laifen")], "出海看板")}

<main>
  <h1>出海看板</h1>
  <p class="stamp">比亚迪：SMMT 英国乘用车注册公开数据　·　徕芬：UN Comtrade 德国进口贸易数据</p>

  <section id="byd">
    <h2>项目一</h2>
    <div class="ptitle">比亚迪（英国）：市场进入研究与竞品基线</div>
    <p class="lead">以 BYD DOLPHIN SURF 为切口建立英国市场基线：接入 SMMT 官方注册数据，
      覆盖动力类型、销售渠道、品牌级与车型榜，并跟踪中国品牌在英国的注册表现。</p>
    <div class="kpis">{byd_kpis}</div>

    <div class="grid2" style="margin-top:16px">
      <div class="card"><h3>中国与新兴品牌 · 当月注册量</h3>
        <div class="chartbox">{d_cn}</div></div>
      <div class="card"><h3>全市场品牌注册量前十</h3>
        <div class="chartbox">{d_tb}</div></div>
    </div>
    <div class="grid2" style="margin-top:16px">
      <div class="card"><h3>中国与新兴品牌 · 当月同比</h3>
        <div class="chartbox">{d_yoy}</div></div>
      <div class="card"><h3>销售渠道占比</h3>
        <div class="chartbox">{d_ch}</div></div>
    </div>

    <div class="card" style="margin-top:16px"><h3>品牌明细</h3>
      <div class="tbwrap"><table>
        <tr><th>品牌</th><th>当月注册（辆）</th><th>市场份额</th><th>同比</th><th>年初至今（辆）</th></tr>
        {rows}
      </table></div></div>

    <div class="card" style="margin-top:16px"><h3>纯电车型注册量前十</h3>
      <div class="chartbox">{d_bev}</div></div>

    <div class="card" style="margin-top:16px"><h3>同级车型官方公布规格</h3>
      <div class="tbwrap"><table>
        <tr><th>车型</th><th>官方续航（英里）</th><th>电池容量（kWh）</th><th>官方来源</th></tr>
        {comp}
      </table></div></div>
  </section>

  <section id="laifen">
    <h2>项目二</h2>
    <div class="ptitle">徕芬（德国）：市场规模、供应链格局与五个分析模块</div>
    <p class="lead">先用官方贸易数据确定德国吹风机市场的规模与供应链结构，
      再逐层拆到产品卖点、达人投放、竞品价格、渠道效率与本地化表达。</p>

    <h3 style="font-family:var(--font-d);font-size:15px;margin:20px 0 10px">
      市场规模与供应链（真实数据 · {DE['source']}）</h3>
    <div class="kpis">{de_kpis}</div>

    <div class="grid2" style="margin-top:16px">
      <div class="card"><h3>德国吹风机月度进口额</h3>
        <div class="chartbox">{d_tr}</div></div>
      <div class="card"><h3>自中国进口占比</h3>
        <div class="chartbox">{d_sh}</div></div>
    </div>
    <div class="card" style="margin-top:16px"><h3>月度明细</h3>
      <div class="tbwrap"><table>
        <tr><th>月份</th><th>进口总额（百万美元）</th><th>自中国（百万美元）</th><th>中国占比</th></tr>
        {de_rows}
      </table></div></div>

    <h3 style="font-family:var(--font-d);font-size:15px;margin:26px 0 10px">① 评论洞察</h3>
    <p class="lead">{LF['reviews_total']:,} 条德语评论做情感打分，并只在差评里做主题聚类，
      把竞品被抱怨最集中的方向转成产品切入点。</p>
    <div class="card"><h3>各品牌情感分走势</h3><div class="chartbox">{d_se}</div></div>
    <div class="grid2" style="margin-top:16px">
      <div class="card"><h3>抱怨主题分布</h3><div class="chartbox">{d_tp}</div></div>
      <div class="card"><h3>机会指数排行</h3><div class="chartbox">{d_op}</div></div>
    </div>

    <h3 style="font-family:var(--font-d);font-size:15px;margin:26px 0 10px">② 达人分层</h3>
    <p class="lead">{LF['kol_total']} 位德语区达人候选，按相关度、互动质量、受众契合度分层，
      同体量分桶内比较互动率分位数，并设置反作弊规则。</p>
    <div class="grid2">
      <div class="card"><h3>分层分布</h3><div class="chartbox">{d_tr2}</div></div>
      <div class="card"><h3>粉丝量 × 互动率（气泡＝综合分）</h3><div class="chartbox">{d_kb}</div></div>
    </div>
    <div class="card" style="margin-top:16px"><h3>短名单（S / A 档）</h3>
      <div class="tbwrap"><table>
        <tr><th>达人</th><th>平台</th><th>档位</th><th>粉丝量</th><th>综合分</th>
            <th>预估报价</th><th>预估获客成本</th></tr>
        {sl_rows}
      </table></div></div>

    <h3 style="font-family:var(--font-d);font-size:15px;margin:26px 0 10px">③ 竞品价格追踪</h3>
    <p class="lead">{LF['price_rows']:,} 行价格记录，覆盖 6 个品牌；
      用滚动中位数基线识别促销区间，让价格节奏可提前判断。</p>
    <div class="card"><h3>六品牌价格曲线（截至 {LF['price_latest_date']}）</h3>
      <div class="chartbox">{d_pr}</div></div>
    <div class="card" style="margin-top:16px"><h3>竞品动态</h3>
      <div class="tbwrap"><table>
        <tr><th>品牌</th><th>型号</th><th>现价</th><th>标价</th><th>优惠券</th>
            <th>类目排名</th><th>评分</th></tr>
        {ct_rows}
      </table></div></div>

    <h3 style="font-family:var(--font-d);font-size:15px;margin:26px 0 10px">④ 转化漏斗</h3>
    <p class="lead">曝光 → 点击 → 详情页 → 加购 → 成交 → 复购，
      计算各渠道获客成本，决定资源投在哪。</p>
    <div class="grid2">
      <div class="card"><h3>整体漏斗</h3><div class="chartbox">{d_fn}</div></div>
      <div class="card"><h3>成交量与获客成本</h3><div class="chartbox">{d_cac}</div></div>
    </div>
    <div class="card" style="margin-top:16px"><h3>渠道明细</h3>
      <div class="tbwrap"><table>
        <tr><th>渠道</th><th>曝光</th><th>成交（单）</th><th>复购率</th><th>获客成本</th></tr>
        {fu_rows}
      </table></div></div>

    <h3 style="font-family:var(--font-d);font-size:15px;margin:26px 0 10px">⑤ 本地化文案</h3>
    <p class="lead">四版德语文案按合规、信息密度、文化契合、可验证、转化预期五维人工评分，
      最终判断由人完成。</p>
    <div class="card"><h3>五维评分</h3><div class="chartbox">{d_lc}</div></div>
    <div class="card" style="margin-top:16px"><h3>文案版本</h3>
      <div class="tbwrap"><table>
        <tr><th>版本</th><th>合规</th><th>信息密度</th><th>文化契合</th><th>可验证</th>
            <th>转化预期</th><th>合计</th><th>标题示例</th></tr>
        {lo_rows}
      </table></div></div>
  </section>

  <footer>
    比亚迪数据来源：SMMT（英国汽车制造商与贸易商协会）乘用车注册数据 · 各品牌英国官网；注册量为新车上牌登记口径。<br>
    徕芬市场数据来源：UN Comtrade（联合国商品贸易统计数据库）德国进口 HS 851631 贸易统计。
  </footer>
</main></body></html>
"""


def main() -> None:
    html = build()
    out = ROOT / "evo-site" / "overseas.html"
    out.write_text(html, encoding="utf-8")
    log_line(f"出海看板：{out.relative_to(ROOT)}（{len(html)/1048576:.2f} MB）· "
             f"比亚迪（英国）+ 徕芬（德国，含真实贸易数据 + 五模块图表）")


if __name__ == "__main__":
    main()
