"""
生成统一的 evo-site/dashboard.html —— 「数据看板」

层级：
  一级 数据看板
  二级 金融 ｜ 出海
  三级 金融 → 利率研究 / 银行客户建模
       出海 → 比亚迪（英国）/ 徕芬（德国）

用法： python src/build_unified.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, log_line                                     # noqa: E402

from build_dashboards import (CSS, CFG, FONT, S, LAB, NICE, BANK,      # noqa: E402
                              bar, kpi_block, layout,
                              fig_curve, fig_change, fig_quota, fig_qrate)
from build_overseas_v2 import (SEA, DE, LF,                            # noqa: E402
                               fig_cn, fig_cn_yoy, fig_channel,
                               fig_topbrands, fig_bev, fig_de_trade,
                               fig_de_share, fig_sentiment, fig_topics,
                               fig_opp, fig_tier, fig_kol, fig_price,
                               fig_funnel, fig_cac, fig_loc)

from plotly.io import to_html                                          # noqa: E402

FIN = json.loads((ROOT / "data" / "dash" / "dashboard.json").read_text(encoding="utf-8"))
RT = json.loads((ROOT / "data" / "dash" / "market_rt.json").read_text(encoding="utf-8"))


def nf(v, d=2):
    return "—" if v is None else f"{v:.{d}f}"


def _charts(figs, first_js=False):
    out, first = [], first_js
    for fg in figs:
        if fg is None:
            out.append("")
            continue
        out.append(to_html(fg, include_plotlyjs=first, full_html=False, config=CFG))
        first = False
    return out


# ══════════════════════════ 金融
def fin_section(first_js: bool) -> str:
    upd = RT.get("as_of") or ""
    kpis = []
    for it in (RT.get("items") or []):
        sign = it.get("chg_sign") or 0
        kpis.append((it["value"], it["unit"], it["name"], it.get("chg_text") or "",
                     "up" if sign > 0 else ("down" if sign < 0 else ""), it.get("sub") or ""))
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
        (f'{b["auc"]:.4f}', "", "测试 ROC-AUC", "", "", f'正则参数 λ={b["lam"]}')])

    qrows = ""
    for x in b["quota"]:
        d = x["model"] - x["rule"]
        cls = "up" if d > 0 else ("down" if d < 0 else "")
        qrows += (f'<tr><td class="tn">{x["pct"]}</td><td>{x["slots"]:,}</td>'
                  f'<td>{x["rule"]:,}</td><td>{x["model"]:,}</td>'
                  f'<td class="{cls}">{d:+d}</td>'
                  f'<td>{x["rule_rate"]:.2f}%</td><td>{x["model_rate"]:.2f}%</td>'
                  f'<td>{x["rule_lift"]:.2f}</td><td>{x["model_lift"]:.2f}</td></tr>')

    d1, d2, d3, d4 = _charts([fig_curve(), fig_change(), fig_quota(), fig_qrate()], first_js)

    return f"""
  <section id="fin">
    <h2>金融</h2>
    <div class="ptitle">利率与宏观流动性、客户经营建模</div>
    <nav class="sub3">
      <a href="#fin-rates">利率研究</a><a href="#fin-bank">银行客户建模</a>
    </nav>
    <p class="stamp">更新于 {upd}（北京时间）</p>

    <div id="fin-rates" class="proj">
      <div class="ph3">利率研究：宏观流动性、利率与曲线结构</div>
      <p class="lead">围绕国债收益率曲线、期限利差与宏观流动性读数，把利率变化拆成可复核的一组数字，
        用于判断当前利率环境对不同久期与不同流动性约束的组合意味着什么。</p>
      <div class="kpis">{rate_kpi}</div>
      <div class="card" style="margin-top:16px"><h3>国债收益率曲线</h3>
        <div class="chartbox">{d1}</div></div>
      <div class="card" style="margin-top:16px"><h3>各期限收益率变动</h3>
        <div class="chartbox">{d2}</div></div>
      <div class="card" style="margin-top:16px"><h3>各期限明细与变动</h3>
        <div class="tbwrap"><table>
          <tr><th>期限</th><th>最新<br><span class="hd">{FIN['meta']['data_date']}</span></th>{th}
              <th>周变动</th><th>月变动</th><th>年变动</th></tr>
          {trs}
        </table></div>
        <p class="units">收益率单位：%；变动单位：bp（1bp = 0.01 个百分点）</p></div>
      <div class="card" style="margin-top:16px"><h3>中国人民银行公开市场业务交易公告</h3>
        <ul>{omo}</ul></div>
    </div>

    <div id="fin-bank" class="proj">
      <div class="ph3">银行客户经营建模：触达优先级与名额分配</div>
      <p class="lead">围绕「先联系谁、各类对象分配多少名额」，用公开银行营销记录比较
        「凭历史成交经验筛选」与「综合多项信息排序」的差异，形成可随团队可用名额调整的跟进方案。</p>
      <div class="kpis">{bk}</div>
      <div class="grid2" style="margin-top:16px">
        <div class="card"><h3>不同名额下的历史申购覆盖数</h3><div class="chartbox">{d3}</div></div>
        <div class="card"><h3>不同名额下的入选样本申购率</h3><div class="chartbox">{d4}</div></div>
      </div>
      <div class="card" style="margin-top:16px"><h3>名额方案对照</h3>
        <div class="tbwrap"><table>
          <tr><th>名额比例</th><th>名额</th><th>规则覆盖（条）</th><th>模型覆盖（条）</th>
              <th>差值</th><th>规则申购率</th><th>模型申购率</th><th>规则提升</th><th>模型提升</th></tr>
          {qrows}
        </table></div>
        <p class="units">规则＝「曾成功营销优先」；模型＝L2 正则逻辑回归排序。
          提升倍数＝相对随机排序的申购率提升。测试集 {b['test']:,} 条，测试期申购率 {b['rate_test']:.2f}%。</p></div>
      <div class="card" style="margin-top:16px"><h3>方法</h3>
        <p class="lead">按原始时间顺序划分为训练 {b['train']:,} / 验证 {b['valid']:,} / 测试 {b['test']:,} 条；
          训练期申购率 {b['rate_train']:.2f}%、验证期 {b['rate_valid']:.2f}%、测试期 {b['rate_test']:.2f}%。
          模型为 L2 正则逻辑回归，使用 {b['features']} 个特征，剔除 {b['excluded']} 个可能混入事后信息的字段；
          正则参数在验证集上选择，冻结后在测试集评估一次。</p>
        <p class="units">结果为测试集历史样本的静态离线比较，非实盘业绩；
          历史申购标签不等同于机构客户基金申购。</p></div>
    </div>
  </section>
"""


# ══════════════════════════ 出海
def sea_section() -> str:
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

    dm = DE["months"]
    last = dm[-1]
    de_kpis = kpi_block([
        (f'{last["world_usd"]/1e6:,.1f}', "百万美元", f'{last["label"]} 德国进口额', "", "", ""),
        (f'{last["china_usd"]/1e6:,.1f}', "百万美元", "其中自中国进口", "", "", ""),
        (f'{last["china_share"]:.1f}%', "", "自中国占比", "", "",
         f'{"+" if last["china_share"] >= dm[-2]["china_share"] else ""}'
         f'{last["china_share"] - dm[-2]["china_share"]:.1f} 个百分点（环比）'
         if len(dm) > 1 else ""),
        (f'{sum(m["world_usd"] for m in dm)/1e6:,.0f}', "百万美元", f'近 {len(dm)} 个月累计进口',
         "", "", "")])

    de_rows = "".join(
        f'<tr><td class="tn">{m["label"]}</td><td>{m["world_usd"]/1e6:,.1f}</td>'
        f'<td>{m["china_usd"]/1e6:,.1f}</td><td>{m["china_share"]:.1f}%</td></tr>' for m in dm)

    sl = LF["shortlist"][:10]
    sl_rows = "".join(
        f'<tr><td class="tn">{x["name"]}</td><td>{x["platform"]}</td><td>{x["tier"]}</td>'
        f'<td>{x["subscribers"]:,}</td><td>{x["score"]:.1f}</td>'
        f'<td>EUR {x["est_fee_eur"]:,.0f}</td><td>EUR {x["est_cac_eur"]:,.0f}</td></tr>' for x in sl)

    ct = LF["comp_table"]
    ct_rows = "".join(
        f'<tr><td class="tn">{x["brand"]}</td><td>{x["sku"]}</td>'
        f'<td>EUR {x["price_eur"]:,.2f}</td><td>EUR {x["list_eur"]:,.2f}</td>'
        f'<td>{x["coupon_pct"]:.0f}%</td><td>{x["bsr"]:,}</td><td>{x["rating"]:.2f}</td></tr>'
        for x in ct)

    fu = LF["funnel"]
    fu_rows = "".join(
        f'<tr><td class="tn">{x["channel"]}</td><td>{x["impressions"]:,}</td>'
        f'<td>{x["orders"]:,}</td><td>{x["repeat_rate"]:.1f}%</td>'
        f'<td>EUR {x["cac_eur"]:,.2f}</td></tr>' for x in fu)

    lo = LF["localization"]
    lo_rows = "".join(
        f'<tr><td class="tn">{x["version"]}</td><td>{x["compliance"]:.0f}</td>'
        f'<td>{x["info_density"]:.0f}</td><td>{x["cultural_fit"]:.0f}</td>'
        f'<td>{x["verifiability"]:.0f}</td><td>{x["conversion_expectation"]:.0f}</td>'
        f'<td><b>{x["total"]:.0f}</b></td><td>{x["headline"]}</td></tr>' for x in lo)

    (d_cn, d_tb, d_yoy, d_ch, d_bev, d_tr, d_sh, d_se, d_tp, d_op,
     d_tr2, d_kb, d_pr, d_fn, d_cac, d_lc) = _charts([
        fig_cn(), fig_topbrands(), fig_cn_yoy(), fig_channel(), fig_bev(),
        fig_de_trade(), fig_de_share(), fig_sentiment(), fig_topics(), fig_opp(),
        fig_tier(), fig_kol(), fig_price(), fig_funnel(), fig_cac(), fig_loc()])

    return f"""
  <section id="sea">
    <h2>出海</h2>
    <div class="ptitle">英国与德国市场的进入研究</div>
    <nav class="sub3">
      <a href="#sea-byd">比亚迪</a><a href="#sea-laifen">徕芬出海</a>
    </nav>
    <p class="stamp">比亚迪：SMMT 英国乘用车注册公开数据　·　徕芬：UN Comtrade 德国进口贸易数据</p>

    <div id="sea-byd" class="proj">
      <div class="ph3">比亚迪（英国）：市场进入研究与竞品基线</div>
      <p class="lead">以 BYD DOLPHIN SURF 为切口建立英国市场基线：接入 SMMT 官方注册数据，
        覆盖动力类型、销售渠道、品牌级与车型榜，并跟踪中国品牌在英国的注册表现。</p>
      <div class="kpis">{byd_kpis}</div>
      <div class="grid2" style="margin-top:16px">
        <div class="card"><h3>中国与新兴品牌 · 当月注册量</h3><div class="chartbox">{d_cn}</div></div>
        <div class="card"><h3>全市场品牌注册量前十</h3><div class="chartbox">{d_tb}</div></div>
      </div>
      <div class="grid2" style="margin-top:16px">
        <div class="card"><h3>中国与新兴品牌 · 当月同比</h3><div class="chartbox">{d_yoy}</div></div>
        <div class="card"><h3>销售渠道占比</h3><div class="chartbox">{d_ch}</div></div>
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
    </div>

    <div id="sea-laifen" class="proj">
      <div class="ph3">徕芬（德国）：市场规模、供应链格局与五个分析模块</div>
      <p class="lead">先用官方贸易数据确定德国吹风机市场的规模与供应链结构，
        再逐层拆到产品卖点、达人投放、竞品价格、渠道效率与本地化表达。</p>

      <h4 class="mh">市场规模与供应链（真实数据 · {DE['source']}）</h4>
      <div class="kpis">{de_kpis}</div>
      <div class="grid2" style="margin-top:16px">
        <div class="card"><h3>德国吹风机月度进口额</h3><div class="chartbox">{d_tr}</div></div>
        <div class="card"><h3>自中国进口占比</h3><div class="chartbox">{d_sh}</div></div>
      </div>
      <div class="card" style="margin-top:16px"><h3>月度明细</h3>
        <div class="tbwrap"><table>
          <tr><th>月份</th><th>进口总额（百万美元）</th><th>自中国（百万美元）</th><th>中国占比</th></tr>
          {de_rows}
        </table></div></div>

      <h4 class="mh">① 评论洞察</h4>
      <p class="lead">{LF['reviews_total']:,} 条德语评论做情感打分，并只在差评里做主题聚类，
        把竞品被抱怨最集中的方向转成产品切入点。</p>
      <div class="card"><h3>各品牌情感分走势</h3><div class="chartbox">{d_se}</div></div>
      <div class="grid2" style="margin-top:16px">
        <div class="card"><h3>抱怨主题分布</h3><div class="chartbox">{d_tp}</div></div>
        <div class="card"><h3>机会指数排行</h3><div class="chartbox">{d_op}</div></div>
      </div>

      <h4 class="mh">② 达人分层</h4>
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

      <h4 class="mh">③ 竞品价格追踪</h4>
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

      <h4 class="mh">④ 转化漏斗</h4>
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

      <h4 class="mh">⑤ 本地化文案</h4>
      <p class="lead">四版德语文案按合规、信息密度、文化契合、可验证、转化预期五维人工评分，
        最终判断由人完成。</p>
      <div class="card"><h3>五维评分</h3><div class="chartbox">{d_lc}</div></div>
      <div class="card" style="margin-top:16px"><h3>文案版本</h3>
        <div class="tbwrap"><table>
          <tr><th>版本</th><th>合规</th><th>信息密度</th><th>文化契合</th><th>可验证</th>
              <th>转化预期</th><th>合计</th><th>标题示例</th></tr>
          {lo_rows}
        </table></div></div>
    </div>
  </section>
"""


EXTRA_CSS = """
html,body{overflow-x:hidden}
#wxbar{position:fixed;left:0;right:0;bottom:0;z-index:400;background:#1B3A6B;color:#fff;
  padding:11px 14px;text-align:center;font-family:var(--font-d);font-size:13px;line-height:1.6}
#wxbar b{font-weight:700}
body.wx{padding-bottom:52px}

.sub2{position:sticky;top:58px;z-index:55;background:var(--bar-bg);backdrop-filter:blur(8px);
  border-bottom:1px solid var(--line);display:flex;gap:6px;justify-content:center;
  padding:9px 14px;font-family:var(--font-d)}
.sub2 a{font-size:14.5px;letter-spacing:.06em;color:var(--muted);padding:7px 22px;
  border-radius:9px;white-space:nowrap}
.sub2 a:hover{background:var(--tint);color:var(--ink)}
.sub2 a.on{background:var(--tint-strong);color:var(--ink);font-weight:650}
.sub3{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0 4px}
.sub3 a{font-size:13px;font-family:var(--font-d);color:var(--muted);
  border:1px solid var(--line);border-radius:99px;padding:5px 16px;white-space:nowrap}
.sub3 a:hover{background:var(--tint);color:var(--ink);text-decoration:none}
.proj{padding-top:6px}
.proj + .proj{margin-top:46px;border-top:1px solid var(--line);padding-top:30px}
.ph3{font-family:var(--font-d);font-size:18px;font-weight:650;margin:4px 0 12px;
  padding-left:11px;border-left:3px solid var(--red)}
.mh{font-family:var(--font-d);font-size:15px;font-weight:650;margin:26px 0 10px}
.srcbox{text-align:left;margin-top:40px;padding-top:20px;border-top:1px solid var(--line);
  font-size:12.5px;color:var(--muted);font-family:var(--font-d);line-height:2}
.srcbox b{color:var(--ink);font-weight:650;margin-right:6px}
@media(max-width:900px){ .sub2{top:56px} .sub2 a{font-size:13px;padding:6px 14px} }
@media(max-width:900px){
  main{padding:18px 13px 52px}
  section > h2{font-size:25px;letter-spacing:.28em;text-indent:.28em}
  .ptitle{font-size:17px}
  .ph3{font-size:16.5px}
  .lead{font-size:14.8px}
  .kpis{grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px}
  .kpi{padding:13px 13px}
  .kpi .vl{font-size:19px}
  .seadiv{margin:38px auto 4px;max-width:80%}
  .srcbox{text-align:left;font-size:12px}
  .chartbox{overflow-x:auto;-webkit-overflow-scrolling:touch}
}
@media(max-width:480px){
  section > h2{font-size:23px;letter-spacing:.24em;text-indent:.24em}
  .kpis{grid-template-columns:1fr 1fr;gap:9px}
  .kpi .vl{font-size:17px}
  .kpi .lb{font-size:11.5px}
  .sub2 a{font-size:13px;padding:6px 16px}
  .sub3{justify-content:center;gap:6px}
  .sub3 a{font-size:12.5px;padding:5px 13px}
}
@media(max-width:380px){
  .kpis{grid-template-columns:1fr 1fr}
  section > h2{font-size:21px}
}

section > h2{text-align:center;font-size:31px;font-weight:800;color:var(--red);
  letter-spacing:.36em;text-indent:.36em;margin:6px 0 10px;font-family:var(--font-d)}
.seadiv{display:flex;align-items:center;gap:18px;max-width:600px;margin:52px auto 6px}
.seadiv::before,.seadiv::after{content:"";flex:1;height:1px;background:linear-gradient(to right,transparent,var(--line),transparent)}
.seadiv span{color:var(--line);font-size:11px;line-height:1}

.ptitle{text-align:center;font-size:20px;margin-bottom:6px}
.sub3{justify-content:center}
main > h1{text-align:center}
main > .stamp{text-align:center}
.ph3{text-align:center;border-left:0;border-top:2px solid var(--red);padding-left:0;padding-top:12px;margin-top:22px}
.mh{text-align:center}
.lead{text-align:center;max-width:860px;margin-left:auto;margin-right:auto}
.card h3{text-align:center}
.card .units{text-align:center}

"""


def build() -> str:
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>数据看板 · 刘柏廷 Evo</title>
<style>{CSS}{EXTRA_CSS}</style></head><body>

<div class="bar">
  <b><a href="index.html" style="color:inherit">刘柏廷 · Evo</a>　<span style="color:var(--muted);font-weight:400">数据看板</span></b>
  <nav><a href="index.html">回主页</a>
    <button class="tg" onclick="document.body.classList.toggle('dark')">深/浅色</button></nav>
</div>
<nav class="sub2" id="sub2">
  <a href="#fin" data-s="fin">金融</a><a href="#sea" data-s="sea">出海</a>
</nav>

<main>
  <h1>数据看板</h1>
  <p class="stamp">利率与宏观流动性、客户经营建模，以及英国与德国市场的进入研究</p>
  {fin_section(True)}
  <div class="seadiv"><span>&#9670;</span></div>
  {sea_section()}

  <div class="srcbox">
    <div><b>比亚迪</b>数据来源：SMMT（英国汽车制造商与贸易商协会）乘用车注册数据 · 各品牌英国官网；注册量为新车上牌登记口径。</div>
    <div><b>徕芬</b>市场数据来源：UN Comtrade（联合国商品贸易统计数据库）德国进口 HS 851631 贸易统计。</div>
  </div>
</main>

{WX_JS}
<script>
(function() {{
  var links = [].slice.call(document.querySelectorAll('#sub2 a'));
  var ids = ['fin', 'sea'];
  function onScroll() {{
    var y = window.scrollY + 150, cur = 'fin';
    ids.forEach(function(id) {{
      var s = document.getElementById(id);
      if (s && s.offsetTop <= y) cur = id;
    }});
    links.forEach(function(a) {{ a.classList.toggle('on', a.getAttribute('data-s') === cur); }});
  }}
  window.addEventListener('scroll', onScroll, {{ passive: true }});
  window.addEventListener('resize', onScroll);
  onScroll();
}})();
</script>
</body></html>
"""


WX_JS = (Path(__file__).resolve().parent / "_wx_snippet.js").read_text(encoding="utf-8")


def main() -> None:
    html = build()
    out = ROOT / "evo-site" / "dashboard.html"
    out.write_text(html, encoding="utf-8")
    log_line(f"统一数据看板：{out.relative_to(ROOT)}（{len(html)/1048576:.2f} MB）· "
             f"金融（利率研究 / 银行客户建模）+ 出海（比亚迪 / 徕芬）")


if __name__ == "__main__":
    main()
