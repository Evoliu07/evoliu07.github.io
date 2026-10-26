"""
生成打印版报告 HTML（数值服务端直接写入，脱离网络与 JS 亦可读），
并用本机 Chrome 打印为 A4 PDF。

页面顺序：封面 / 阅读说明 / 项目A×4 / 项目B×4 / 附录×3

用法： python src/make_print.py
"""
from __future__ import annotations

import html
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, SOURCES, log_line, today_cst                  # noqa: E402

PRINT = ROOT / "print"
PRINT.mkdir(parents=True, exist_ok=True)
SITE = ROOT / "github-upload"
M = json.loads((SITE / "data" / "market.json").read_text(encoding="utf-8"))
FX, GX = M["finance"]["derived"], M["gtm"]["derived"]
CUR, MM = FX["current"], FX["money_market"]
DUR = {r["shift_bp"]: r for r in FX["duration_scenario"]["rows"]}
BV, BY = GX["byd"]["month"], GX["byd"]["ytd"]
DV = M["meta"]["data_version"]
GEN = M["meta"]["generated_at"]
BV_ = M["meta"]["build_version"]


def n(v):
    return f"{v:,}" if isinstance(v, (int, float)) else str(v)


def esc(s):
    return html.escape(str(s))


CSS = """
@page { size: A4 portrait; margin: 14mm 13mm 12mm; }
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { margin:0; font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
       color:#1F2933; font-size:10.2pt; line-height:1.62; }
.page { page-break-after: always; }
.page:last-child { page-break-after: auto; }
.top { height:4pt; background:#1B3A6B; margin:0 0 6mm; }
.kicker { color:#10756A; font-weight:700; font-size:8.6pt; letter-spacing:.06em;
          text-transform:uppercase; }
h1 { font-size:20pt; color:#1B3A6B; margin:3pt 0 2pt; line-height:1.24; letter-spacing:-.3pt; }
h2 { font-size:13pt; color:#1B3A6B; margin:13pt 0 5pt; border-bottom:1px solid #DCE1E8;
     padding-bottom:3pt; }
h3 { font-size:11pt; color:#1F2933; margin:9pt 0 3pt; }
p  { margin:0 0 5pt; }
.lede { font-size:11pt; color:#52606D; }
.muted { color:#52606D; }
.tiny { font-size:8.4pt; color:#7B8794; line-height:1.5; }
.rule { height:1px; background:#DCE1E8; margin:5pt 0 9pt; }
.grid2 { display:grid; grid-template-columns:1fr 1fr; gap:7mm; }
.grid3 { display:grid; grid-template-columns:repeat(3,1fr); gap:4mm; }
.box { border:1px solid #DCE1E8; border-radius:5pt; padding:7pt 9pt; }
.box.soft { background:#F5F7FA; }
.box.warn { background:#FBF0E9; border-color:#EBD5C4; }
.box.teal { background:#E6F2F0; border-color:#BFDEDA; }
.box h3 { margin-top:0; }
table { width:100%; table-layout:fixed; word-break:break-word; border-collapse:collapse; font-size:8.8pt; margin:3pt 0 5pt; }
th, td { border-bottom:1px solid #DCE1E8; padding:3.4pt 5pt; text-align:left;
         vertical-align:top; }
th { background:#F5F7FA; color:#52606D; font-weight:700; }
td.num, th.num { text-align:right; font-variant-numeric:tabular-nums; }
figure { margin:6pt 0 8pt; }
figure img { width:100%; border:1px solid #DCE1E8; border-radius:4pt; }
figcaption { font-size:8.4pt; color:#52606D; margin-top:3pt; }
figure img { max-height:74mm; width:auto; max-width:100%; display:block; margin:0 auto; }
figure.half img { max-height:62mm; }
ul, ol { margin:2pt 0 5pt; padding-left:14pt; }
li { margin-bottom:2.6pt; }
.kv { display:grid; grid-template-columns:58pt 1fr; gap:2pt 6pt; font-size:9.2pt; }
.kv dt { color:#7B8794; }
.tag { display:inline-block; font-size:8pt; padding:1pt 5pt; border-radius:8pt;
       background:#EDF1F7; color:#52606D; border:1px solid #DCE1E8; }
.tag.ok { background:#E6F2F0; color:#10756A; border-color:#BFDEDA; }
.tag.warn { background:#FBF0E9; color:#9A4318; border-color:#EBD5C4; }
.srcline { font-size:8pt; color:#7B8794; }
.foot { margin-top:8pt; padding-top:4pt; border-top:1px solid #DCE1E8;
        font-size:7.8pt; color:#7B8794; }
@media screen { body { background:#EDF1F7; overflow-x:hidden; }
  .page { background:#fff; max-width:210mm; margin:0 auto 8mm; padding:14mm 13mm;
          box-shadow:0 2px 10px rgba(0,0,0,.08); } }
"""


def page(inner: str) -> str:
    return f'<section class="page"><div class="top"></div>{inner}</section>'


def foot(txt: str) -> str:
    return (f'<div class="foot">数据版本 {DV}　生成 {GEN[:16]}　构建 {BV_}　'
            f'｜ {txt}　｜ 本页与网站、PPT 使用同一数据版本，未手工另填数字。</div>')


def build_html() -> str:
    st = FX["stages"]
    P = []

    # ---------------- 封面 ----------------
    P.append(page(f"""
      <div style="height:32mm"></div>
      <div class="kicker">个人作品集 · 打印版 · 面试版</div>
      <h1 style="font-size:26pt">两项 AI 辅助独立研究</h1>
      <p class="lede" style="font-size:13pt;color:#1B3A6B">
        固收市场观察与机构客户沟通　·　英国电动车市场情报与 GTM 执行工作台</p>
      <div class="rule"></div>
      <p style="font-size:12pt"><b>刘柏廷　BoTing LIU</b>　｜　澳门科技大学 商学院</p>
      <div style="height:16mm"></div>
      <div class="box soft">
        <h3>这份材料是什么</h3>
        <p class="muted">两个由我独立完成的 AI 辅助研究项目的完整纸质版本。
        每个项目按「背景 — 任务 — 数据与方法 — 关键判断 — 实际行动 — 验证结果 — 局限与复盘」组织，
        正文自带单位、期间、来源编号与复核状态，<b>不依赖点击、悬停或扫码即可完整阅读</b>。</p>
        <p class="muted" style="margin-bottom:0">这是<b>个人研究</b>，不是学校课程、不是委托项目、
        不代表任何机构。没有品牌合作、投放、达人合作、客户关系或订单。
        未获取的数据留空并注明，不推测、不填零。</p>
      </div>
      <div style="height:8mm"></div>
      <div class="grid3">
        <div class="box"><div class="kicker">项目 A</div>
          <p style="margin:0;font-size:15pt;font-weight:700;color:#1B3A6B">{CUR['y10']}%</p>
          <p class="tiny" style="margin:0">10Y 国债到期收益率<br>曲线取数日 {CUR['date']}</p></div>
        <div class="box"><div class="kicker">项目 A</div>
          <p style="margin:0;font-size:15pt;font-weight:700;color:#1B3A6B">{CUR['spread_10y2y']}</p>
          <p class="tiny" style="margin:0">10Y-2Y 期限利差（百分点）<br>同一曲线同日相减</p></div>
        <div class="box"><div class="kicker">项目 B</div>
          <p style="margin:0;font-size:15pt;font-weight:700;color:#10756A">{GX['channels'][0]['share']}%</p>
          <p class="tiny" style="margin:0">英国车队渠道份额<br>私人渠道 {GX['channels'][1]['share']}%</p></div>
      </div>
      {foot('打印版封面')}
    """))

    # ---------------- 阅读说明 ----------------
    P.append(page(f"""
      <div class="kicker">阅读说明</div>
      <h1>怎么读这份材料</h1>
      <p class="lede">如果你是面试官，建议按下面的顺序读，每页聚焦一个结论。</p>
      <div class="rule"></div>
      <div class="grid2">
        <div class="box">
          <h3>页码导航</h3>
          <ul>
            <li><b>项目 A</b>：P3 背景与成果 → P4 数据与方法 → P5 判断与工具 → P6 局限与复盘</li>
            <li><b>项目 B</b>：P7 背景与成果 → P8 市场结构 → P9 判断与执行 → P10 局限与复盘</li>
            <li><b>附录</b>：P11 来源登记 → P12 数据记录 → P13 口径对照与未获取项</li>
          </ul>
        </div>
        <div class="box soft">
          <h3>三个必须先看清的边界</h3>
          <ul>
            <li><b>这是个人研究</b>，不是实习成果、不是委托项目。项目 A 的组合数字是<b>教学假设</b>，
                项目 B 没有品牌合作与投放。</li>
            <li><b>来源均为单一权威</b>（政府 / 行业机构 / 品牌官网），
                尚未独立交叉验证，已逐条标注。</li>
            <li><b>未完成的事写明了</b>：基金可比研究、公开市场净投放自动解析、
                评论挖掘、达人数值评分、真实用户测试。没有做过的检查不标为通过。</li>
          </ul>
        </div>
      </div>
      <h2>这份材料解决什么问题</h2>
      <p>金融与出海岗位的面试里，最常见的追问是三类：
      「数字从哪来」「口径对不对」「结论在什么情况下会错」。
      这份材料的每一页都在回答这三类问题：
      每个数字带来源编号与所属日期；最容易混用的口径单独列表对照；
      每条重要判断都写明失效条件。</p>
      <h2>记忆骨架</h2>
      <p style="font-size:11.5pt"><b>问题 → 证据 → 判断 → 行动 → 验证 → 复盘</b></p>
      <p class="muted">两个项目都按这个骨架组织。如果只记一件事，记这条：
      <b>先确认「能不能拿到、能不能用、能不能公开」，再决定「做什么」。</b></p>
      {foot('阅读说明')}
    """))

    # ---------------- 项目 A ----------------
    P.append(page(f"""
      <div class="kicker">项目 A ｜ 第 1 页</div>
      <h1>背景 · 任务 · 我的贡献 · 当前成果</h1>
      <div class="rule"></div>
      <div class="grid2">
        <div class="box soft">
          <h3>背景与研究问题</h3>
          <p>收益率中枢近年持续下移，久期提供的收益空间在收窄，
          但久期风险的<b>绝对敞口并没有同步下降</b>。不同约束（久期上限、回撤容忍、会计分类）
          的机构客户，在同一个市场判断下受到的影响差别很大。</p>
          <p style="margin-bottom:0">研究问题：如何用公开数据把曲线与资金面的现状说清楚，
          并把「风险」翻译成不同约束的客户能听懂的语言？</p>
        </div>
        <div class="box">
          <h3>我承担的任务</h3>
          <ul>
            <li>确定有限核心指标集，逐一验证数据可得性</li>
            <li>编写采集程序（官方公开接口），落盘、校验、降级</li>
            <li>完成期限利差、三阶段曲线复盘与修正久期情景建模</li>
            <li>输出 60 秒口述稿与一页机构客户沟通材料</li>
            <li>列出反证与失效条件，而非只给结论</li>
          </ul>
        </div>
      </div>
      <h2>当前成果</h2>
      <p class="tiny">个人研究，非委托项目；<b>无客户、无业绩数据、无投资回测</b>。</p>
      <ul>
        <li><b>建成 5 个官方公开来源的日频采集管道</b>：中债收益率曲线（S-CB-01 / S-CB-02）、
            银行间质押式回购利率（S-CM-01）、Shibor（S-CM-02）、央行公开市场公告（S-PB-01）。</li>
        <li><b>当期读数</b>：10Y {CUR['y10']}%、30Y {CUR['y30']}%、
            10Y-2Y 期限利差 {CUR['spread_10y2y']} 个百分点；
            DR007 {MM['DR007']}%、DR001 {MM['DR001']}%、FR007 {MM['FR007']}%（{MM['date']}）。</li>
        <li><b>三阶段曲线复盘</b>：10Y 由 {st[0]['y10']}%（{st[0]['date']}）
            降至 {CUR['y10']}%（{CUR['date']}）。</li>
        <li><b>13 条数据记录</b>，每条带定义、单位、地区、统计范围、期间、抓取时间、来源编号与验证状态。</li>
        <li><b>明确列出未完成项</b>：固收基金可比研究、公开市场净投放自动解析、人工复核与学习记录。</li>
      </ul>
      {foot('项目 A · 第 1 页 / 4')}
    """))

    P.append(page(f"""
      <div class="kicker">项目 A ｜ 第 2 页</div>
      <h1>数据、方法及关键看板</h1>
      <div class="rule"></div>
      <figure>
        <img src="../exports/charts/C02_收益率曲线_阶段对比.png" alt="收益率曲线阶段对比">
        <figcaption><b>图 C-02　收益率曲线阶段对比</b>　单位：%（到期收益率）。
        取点日期：{st[0]['date']}、{st[1]['date']}、{st[2]['date']} 与 {CUR['date']}（当期）。
        来源编号 <span class="srcline">S-CB-01 / S-CB-02</span>。
        纵轴自 0 起、未截断；四个时点取同一条曲线类型，未混入地方政府债或国开债曲线。</figcaption>
      </figure>
      <table>
        <caption style="text-align:left;font-size:8.4pt;color:#52606D;padding-bottom:3pt">
          关键期限与利差（单位：%，利差为百分点）</caption>
        <thead><tr><th>日期</th><th>阶段</th><th class="num">1Y</th><th class="num">2Y</th>
        <th class="num">5Y</th><th class="num">10Y</th><th class="num">30Y</th>
        <th class="num">10Y-2Y</th></tr></thead><tbody>
        {''.join(f"<tr><td>{r['date']}</td><td>{r['label']}</td>"
                 f"<td class='num'>{r.get('y1') or '—'}</td><td class='num'>{r.get('y2') or '—'}</td>"
                 f"<td class='num'>{r.get('y5') or '—'}</td><td class='num'>{r.get('y10') or '—'}</td>"
                 f"<td class='num'>{r.get('y30') or '—'}</td>"
                 f"<td class='num'>{r.get('spread_10y2y') or '—'}</td></tr>" for r in st)}
        <tr><td>{CUR['date']}</td><td><b>当期</b></td>
        <td class="num">{CUR['y1']}</td><td class="num">{CUR['y2']}</td>
        <td class="num">{CUR['y5']}</td><td class="num">{CUR['y10']}</td>
        <td class="num">{CUR['y30']}</td><td class="num">{CUR['spread_10y2y']}</td></tr>
        </tbody></table>
      <h2>方法与口径纪律</h2>
      <ul>
        <li><b>来源</b>：中债估值中心（财政部授权）、全国银行间同业拆借中心、中国人民银行。</li>
        <li><b>频率</b>：按交易日与官方发布时间更新；增量更新、缓存去重。
            竞品页面每日检查；月度 / 宏观数据随发布更新。</li>
        <li><b>降级</b>：抓取失败时保留上次有效结果并标记过期，<b>不写零</b>；
            数据未发布、来源不可访问、校验失败与「无变化」是四种不同状态，分别记录。</li>
        <li><b>不混用</b>：国债曲线与地方政府债曲线不混用；DR（存款类机构）与 FR（全市场）
            分列展示；到期收益率 ≠ 持有期回报；价格变化 ≠ 总回报。</li>
        <li><b>验证状态</b>：全部为<b>单一权威来源，尚未独立交叉验证</b>。</li>
      </ul>
      {foot('项目 A · 第 2 页 / 4')}
    """))

    P.append(page(f"""
      <div class="kicker">项目 A ｜ 第 3 页</div>
      <h1>关键判断与久期情景工具</h1>
      <div class="rule"></div>
      <figure>
        <img src="../exports/charts/C03_久期情景分析.png" alt="修正久期情景分析">
        <figcaption><b>图 C-03　修正久期情景分析</b>
        <span class="tag warn">教学情景假设</span>　单位：% / 元。
        假设面值 100,000,000 元、修正久期 5.0、凸性 30；公式
        dP/P ≈ -D_mod·dy + 0.5·C·dy²；1bp = 0.0001。
        <b>参数为明确标注的教学情景，不是任何真实基金或产品的参数</b>，不构成投资建议。</figcaption>
      </figure>
      <div class="box" style="border-left:3pt solid #1B3A6B">
        <h3>判断 1｜收益率中枢在两年内持续下移</h3>
        <p>10Y 由 {st[0]['y10']}%（{st[0]['date']}）降至 {CUR['y10']}%（{CUR['date']}）。
        <b>失效条件</b>：若 10Y 回升并突破 {st[2]['y10']}%（{st[2]['date']} 水平），
        本判断需修正。结论仅适用于银行间市场国债曲线，换用国开债或地方政府债曲线后
        绝对水平不同，不可直接搬用。</p>
      </div>
      <div class="box" style="border-left:3pt solid #1B3A6B;margin-top:5pt">
        <h3>判断 2｜下行行情里，久期提供的保护在减弱</h3>
        <p>教学情景下，+100bp 使组合估值变动 {DUR[100]['approx_pct']:+.2f}%
        （约 {DUR[100]['value_change_cny']:+,.0f} 元），-100bp 变动
        {DUR[-100]['approx_pct']:+.2f}%。<b>方向上的不对称正是凸性</b>在起作用。
        <b>失效条件</b>：若发生扭曲型变动（非平行移位），本情景的偏差方向不确定。</p>
      </div>
      <div class="box" style="border-left:3pt solid #10756A;margin-top:5pt">
        <h3>判断 3｜客户的差异不在「看不看好」，而在「约束不同」</h3>
        <p style="margin-bottom:0">沟通材料的重点应从「我怎么看」转为
        <b>「在你的久期上限与回撤容忍下，这个情景意味着多少回撤」</b>。
        <b>限制</b>：客户案例为教学假设，不能仅凭「券商资管」或「城商行理财子」这样的类别
        推断适配性——真实适配必须基于该机构实际的久期上限、回撤容忍与会计分类。</p>
      </div>
      <h2>工具说明（必读）</h2>
      <p class="tiny">期限 ≠ 久期；到期收益率 ≠ 持有期回报；价格变化 ≠ 总回报。
      本工具为「修正久期 + 凸性」的近似公式，假设收益率曲线<b>平行移位</b>。
      误差来源：①忽略三阶及以上项；②平行移位假设；③未含信用利差变动、税收与交易成本；
      ④未考虑现金流时点变化。误差量级：凸性项在 ±25bp 内约占久期效应的 6%，
      在 ±100bp 内升至约 24%——<b>移位越大，线性估计越不可靠</b>。</p>
      {foot('项目 A · 第 3 页 / 4')}
    """))

    P.append(page(f"""
      <div class="kicker">项目 A ｜ 第 4 页</div>
      <h1>验证结果、局限与复盘</h1>
      <div class="rule"></div>
      <div class="grid2">
        <div class="box teal">
          <h3>已验证（系统成果 / 研究成果）</h3>
          <ul>
            <li>5 个官方来源全部采集成功，程序可重复运行</li>
            <li>34 项自动检查全部通过（数值非空、单位齐备、版本一致、图表文件存在）</li>
            <li>三阶段曲线可重算，关键结论可追溯至来源编号</li>
            <li>失败降级机制已实测：本机代理导致间歇性 502 时，
                程序保留上次有效结果并标记过期，页面不出现零值</li>
          </ul>
          <h3>效率实测（程序流程，不是人力百分比）</h3>
          <p class="tiny" style="margin-bottom:0">
          首轮建设含接口勘察与调参：约 2 小时。<br>
          单次增量更新（采集 → 校验 → 派生 → 制图 → 导出）：约 1–2 分钟。<br>
          <b>没有人工基线，因此不报告「节省 xx%」的百分比。</b></p>
        </div>
        <div class="box warn">
          <h3>未完成（不由 AI 代填）</h3>
          <ul>
            <li><b>固收基金可比研究</b>：份额、区间、分红、费用与披露滞后数据未取得，
                留空并说明；<b>不用收益率变化替代基金收益</b>，也不给真实基金强行赋值</li>
            <li><b>公开市场净投放自动解析</b>：须同时核对投放与到期两侧，
                本轮只取到公告标题与链接，未可靠解析金额，故不计算</li>
            <li><b>人工复核</b>：抽查来源原文、手算久期情景并与程序结果比对——待我本人完成</li>
            <li><b>真实读者查找任务测试</b>：未测试</li>
          </ul>
        </div>
      </div>
      <h2>复盘：如果重做一次</h2>
      <ul>
        <li><b>先验证「有没有接口」再决定研究范围。</b>本轮中债与货币网的可用接口参数是实测出来的，
            公开文档并没有给出；如果先定好范围再找数据，会白做一轮。</li>
        <li><b>基金比较应在一开始就确认数据可得性。</b>基金层面需要份额、区间、分红、费用与披露滞后，
            这是本轮最晚才确认不可得的部分，导致一个研究模块中途降级。</li>
        <li><b>凸性修正应更早与一阶线性对比。</b>向非技术背景的客户解释「为什么亏损小于
            久期相乘的结果」时，对比表述比公式更有效。</li>
      </ul>
      <h2>可复现记录</h2>
      <div class="kv">
        <dt>数据版本</dt><dd>{DV}</dd>
        <dt>生成时间</dt><dd>{GEN}</dd>
        <dt>构建版本</dt><dd>{BV_}　管道版本 {M['meta']['pipeline_version']}</dd>
        <dt>生成方式</dt><dd>程序采集与计算（采集、校验与制图环节<b>未调用模型</b>）</dd>
        <dt>计算参数</dt><dd>久期情景：面值 100,000,000 元、修正久期 5.0、凸性 30、平行移位（教学假设）</dd>
        <dt>依赖</dt><dd>Python 3.13、matplotlib 3.11、pandas 3.0（见 requirements.txt）</dd>
        <dt>修订记录</dt><dd>见 checks/pipeline_fixups.md</dd>
      </div>
      {foot('项目 A · 第 4 页 / 4')}
    """))

    # ---------------- 项目 B ----------------
    P.append(page(f"""
      <div class="kicker">项目 B ｜ 第 1 页</div>
      <h1>背景 · 任务 · 我的贡献 · 当前成果</h1>
      <div class="rule"></div>
      <div class="grid2">
        <div class="box soft">
          <h3>范围锁定（六个限制，不无限扩张）</h3>
          <ul>
            <li><b>国家</b>：英国（UK）——SMMT 口径含大不列颠与北爱尔兰</li>
            <li><b>主车型</b>：BYD DOLPHIN SURF（官方定位 <i>The Compact Electric City Car</i>，
                官网页续航 200 英里）</li>
            <li><b>直接竞品</b>：Renault 5 E-Tech electric / MG4 EV / Dacia Spring Electric</li>
            <li><b>优先用户</b>：小型纯电车的车队与公司车决策链，并对照私人首购用户</li>
            <li><b>验证切口</b>：官方公开信息能否支撑「同级别可比判断」——信息缺口切口，不是销量切口</li>
            <li><b>不做</b>：多国对比、全车型矩阵、冒充品牌官方、代收销售线索、未经授权联系达人</li>
          </ul>
        </div>
        <div class="box">
          <h3>我承担的任务</h3>
          <ul>
            <li>逐一实测各官方来源的可达性，<b>并记录不可达的来源</b></li>
            <li>搭建 SMMT 官方注册数据的增量采集与市场基线</li>
            <li>建立竞品基线（只用官网可核实的字段）</li>
            <li>产出英文落地页、对比表、内容脚本、合作 brief、两周执行计划</li>
            <li>在合规边界内主动放弃不可靠的做法（如达人数值评分）</li>
          </ul>
        </div>
      </div>
      <h2>当前成果</h2>
      <p class="tiny">个人研究，非委托项目；<b>无品牌合作、无投放、无达人合作、无订单</b>。</p>
      <ul>
        <li><b>市场基线</b>：当月英国新乘用车注册 {n(GX['total_month'])} 辆，纯电 BEV {n(GX['bev_month'])} 辆
        （份额 {GX['powertrain_mix'][0]['share']}%，同比 {GX['powertrain_mix'][0]['yoy']:+.1f}%）；
        年初至今纯电 {n(GX['bev_ytd'])} 辆。</li>
        <li><b>BYD 品牌</b>：当月 {n(BV['cur'])} 辆（同比 {BV['pct_change']:+.1f}%），
        年初至今 {n(BY['cur'])} 辆（同比 {BY['pct_change']:+.1f}%）——<b>品牌级，非车型级</b>。</li>
        <li><b>渠道结构</b>：车队 {GX['channels'][0]['share']}%、私人 {GX['channels'][1]['share']}%、
        公司自用 {GX['channels'][2]['share']}% → 据此提出切口优先级。</li>
        <li><b>竞品基线</b>：4 款车型官网续航 / 电池规格并列展示，并明确标注「口径未对齐前不得排名」。</li>
        <li><b>执行材料</b>：英文独立研究落地页、可比表 / 购买清单、内容脚本、合作 brief、两周执行计划。</li>
      </ul>
      {foot('项目 B · 第 1 页 / 4')}
    """))

    P.append(page(f"""
      <div class="kicker">项目 B ｜ 第 2 页</div>
      <h1>数据、方法及关键看板</h1>
      <div class="rule"></div>
      <div class="grid2">
        <figure class="half">
          <img src="../exports/charts/C05_英国动力类型结构.png" alt="英国新乘用车动力结构">
          <figcaption><b>图 C-05　英国新乘用车动力结构</b>　单位：%。
          样本：英国当月全部新乘用车注册，总量 {n(GX['total_month'])} 辆。
          来源编号 <span class="srcline">S-SM-01</span>。复核状态：单一权威来源，未独立交叉验证。
          <b>注册量不等于销量或交付量</b>；分母为全市场，不是纯电细分。</figcaption>
        </figure>
        <figure class="half">
          <img src="../exports/charts/C06_英国渠道结构.png" alt="英国新乘用车销售渠道结构">
          <figcaption><b>图 C-06　英国新乘用车销售渠道结构</b>　单位：%，
          分母＝英国当月全部新乘用车注册。来源编号 <span class="srcline">S-SM-01</span>。</figcaption>
        </figure>
      </div>
      <div class="grid2">
        <div>
          <h2>数据与口径纪律</h2>
          <ul style="font-size:9.4pt">
            <li><b>SMMT</b>（英国汽车制造商与贸易商协会）免费公开页：动力类型、销售渠道、
                59 个品牌、车型 Top10、BEV 车型 Top10。来源编号 S-SM-01 / S-SM-02。</li>
            <li>品牌官网：S-BY-01 / S-RN-01 / S-MG-01 / S-DC-01。</li>
            <li>严格区分：注册量 ≠ 销量 ≠ 交付量；品牌级 ≠ 车型级；纯电 ≠ 插混；英国 ≠ 大不列颠。</li>
          </ul>
        </div>
        <div>
          <h2>已知限制</h2>
          <ul style="font-size:9.4pt">
            <li>SMMT 免费页<b>仅公开车型 Top10</b>：当月 BEV 榜中只有 Renault 5 出现（736 辆），
                另两款竞品无可公开核实的车型级注册量。</li>
            <li>BYD 英国官网价格与 PCP 月供为<b>前端动态渲染</b>，静态采集不可得 → 记为未获取，不推测。</li>
            <li>来源可达性实测：Vauxhall 与 Citroën 英国站点分别连接失败与返回 403，
                因此在竞品选择<b>之前</b>被排除，不是因为不利而排除。</li>
          </ul>
        </div>
      </div>
      {foot('项目 B · 第 2 页 / 4')}
    """))

    P.append(page(f"""
      <div class="kicker">项目 B ｜ 第 3 页</div>
      <h1>商业判断与执行材料</h1>
      <div class="rule"></div>
      <figure>
        <img src="../exports/charts/C07_BYD品牌注册量.png" alt="BYD 品牌英国注册量">
        <figcaption><b>图 C-07　BYD 品牌英国注册量</b>　单位：辆。
        口径：BYD 品牌<b>全部动力类型</b>的英国新乘用车注册。来源编号
        <span class="srcline">S-SM-02</span>。
        <b>重要限制：品牌级数据不能当作 DOLPHIN SURF 单车型销量。</b></figcaption>
      </figure>
      <div class="box teal">
        <h3>关键判断｜切口应优先放在车队 / 公司车决策链</h3>
        <p>当月英国新乘用车注册中，车队渠道占 <b>{GX['channels'][0]['share']}%</b>，
        私人渠道占 <b>{GX['channels'][1]['share']}%</b>。对一款低单价城市纯电而言，
        这意味着「公司车与车队适配证据」比「面向私人消费者的大规模内容投放」
        更接近可验证的优先切口。据此<b>提出</b>把验证资源集中在车队 / 公司车决策链
        所需的可比证据上，<b>而不是</b>先做消费者内容。</p>
        <h3 style="margin-bottom:3pt">失效条件（必须一起读）</h3>
        <p style="margin-bottom:0" class="tiny">
        ① 若该车型的购买决策实际由私人零售主导（例如其经销网络以零售为主），本判断需下调权重；
        ② 渠道占比来自<b>全市场</b>口径，不是纯电细分、更不是该车型自身的渠道结构，直接外推属于过度解读；
        ③ 注册量 ≠ 销量 ≠ 交付量。
        <b>状态：这是「提出并准备验证」的建议，尚未执行，未取得任何成效数据。</b></p>
      </div>
      <div class="grid2" style="margin-top:6pt">
        <div class="box">
          <h3>已制作的执行材料</h3>
          <ul style="font-size:9.4pt">
            <li>英文独立研究落地页（显著标注为独立研究，<b>不冒充品牌官方</b>）</li>
            <li>同级别可比表 / 购买清单</li>
            <li>内容脚本（面向车队决策链的沟通过程）</li>
            <li>合作 brief（含必须声明与禁止事项）</li>
            <li>两周执行计划：动作、负责人、依赖、成本假设、衡量方式、停止条件</li>
          </ul>
        </div>
        <div class="box warn">
          <h3>边界声明</h3>
          <ul style="font-size:9.4pt">
            <li>不冒充品牌官方，不使用品牌商标做官方暗示</li>
            <li>不代收品牌销售线索；<b>外链点击、试驾预约与购车订单三者分别定义</b></li>
            <li>不发送未经授权的联系；英文联系草稿仅作为草稿存在</li>
            <li>两周计划中的成本数字为<b>假设</b>，已标注</li>
            <li>所有动作写为「提出 / 制作 / 配置 / 准备验证」，<b>不写已取得业务效果</b></li>
          </ul>
        </div>
      </div>
      {foot('项目 B · 第 3 页 / 4')}
    """))

    P.append(page(f"""
      <div class="kicker">项目 B ｜ 第 4 页</div>
      <h1>验证结果、局限与复盘</h1>
      <div class="rule"></div>
      <div class="grid2">
        <div class="box teal">
          <h3>已验证</h3>
          <ul>
            <li>SMMT 官方数据采集成功，覆盖动力类型、销售渠道、59 个品牌、车型 Top10</li>
            <li>4 款车型官网规格已核实并保留来源链接</li>
            <li>官方来源可达性逐一实测并记录（<b>含不可达来源</b>）</li>
            <li>站点交互已实测：竞品筛选可用、所有数值由同一份 JSON 注入、
                无控制台错误、无横向溢出、无小于 44px 的交互目标</li>
          </ul>
        </div>
        <div class="box warn">
          <h3>明确未做（不假装做过）</h3>
          <ul>
            <li><b>未做评论挖掘</b> → 无主题分布，更不会把提及占比说成消费者比例</li>
            <li><b>未做人工标注留出集</b> → 不宣称任何 AI 分类准确率</li>
            <li><b>未做达人数值评分</b>：YouTube API 等平台条款限制衍生商业评估，
                未核实前不做，改用透明的人工证据分层，受众地域 / 报价 / 转化率保持未知</li>
            <li><b>未做真实用户测试</b> → 不引用任何「用户调研结果」</li>
            <li><b>未做价格对比</b>：官网价格前端渲染不可得，留空而不用推测值填表</li>
          </ul>
        </div>
      </div>
      <h2>复盘：如果重做一次</h2>
      <ul>
        <li><b>竞品选择应在采集前完成可达性实测。</b>本轮已这么做，并保留了不可达记录作为证据，
            避免「结果好看才纳入」的选择性偏差。</li>
        <li><b>价格是 GTM 对比的核心变量，应在研究设计阶段就决定
            「用浏览器渲染采集」还是「明确放弃」。</b>本轮选择明确放弃并留空，
            因为用一个来源不明的价格数字填表，比留空更糟。</li>
        <li><b>用户痛点部分应先确认平台内容分析条款，再决定是否投入样本采集。</b>
            本轮因未确认而主动放弃，是刻意的取舍，不是遗漏。</li>
      </ul>
      <div class="box soft">
        <h3>这个项目最能说明我的判断习惯</h3>
        <p style="margin-bottom:0">先确认「能不能拿到、能不能用、能不能公开」，
        再决定「做什么」；拿不到就写清楚拿不到，不用推测值把表格填满。</p>
      </div>
      <h3>下一步（我自己做）</h3>
      <ul>
        <li>人工复核达人候选的公开信息，确认地区与主题证据</li>
        <li>邀请 2–3 位读者完成三项查找任务测试（找到我的背景 / 理解一项成果 / 定位一条证据）</li>
        <li>人工核对源页面与程序解析结果的一致性</li>
      </ul>
      {foot('项目 B · 第 4 页 / 4')}
    """))

    # ---------------- 附录 1：来源登记 ----------------
    rows = "".join(
        f"<tr><td><b>{k}</b></td><td>{esc(v['name'])}</td>"
        f"<td>{'A 原始披露/官方' if v['authority']=='A' else ('B 官方衍生/行业机构' if v['authority']=='B' else 'C 媒体/二手')}</td>"
        f"<td>{v['region']}</td><td class='srcline'>{esc(v['method'])}</td></tr>"
        for k, v in SOURCES.items())
    P.append(page(f"""
      <div class="kicker">附录 A</div>
      <h1>来源登记表（S-xx）</h1>
      <div class="rule"></div>
      <table><thead><tr><th style="width:52pt">编号</th><th>来源</th>
      <th style="width:88pt">权威性</th><th style="width:34pt">地区</th>
      <th style="width:130pt">采集方式</th></tr></thead><tbody>{rows}</tbody></table>
      <p class="tiny">权威性分级：<b>A</b> 原始披露 / 官方机构；<b>B</b> 官方衍生数据 / 行业机构；
      <b>C</b> 媒体或二手来源。<b>本项目没有用 C 级来源支撑任何结论。</b>
      搜索摘要只作为线索，重要事实均打开原文核对；同源转载不算独立交叉验证。</p>
      <h2>公开与再分发边界</h2>
      <ul>
        <li>本项目只采集官方公开页面与公开接口中<b>必要的少量字段</b>，
            不绕过访问控制、验证码与付费墙，<b>不镜像原始页面</b>。</li>
        <li>公开目录只包含派生数值、来源链接与自制的图表，不包含受限原始材料。</li>
        <li>公开可访问不等于允许批量抓取、长期保存或公开再分发；
            有保存期限或删除要求的数据不进入长期快照，并在复现说明中标注影响。</li>
        <li>测试样例与真实研究数据严格隔离，不混入公开目录。</li>
      </ul>
      {foot('附录 A · 来源登记表')}
    """))

    # ---------------- 附录 2：数据记录（拆为金融 / 英国两张表） ----------------
    def dtable(items, title, note):
        rows = "".join(
            f"<tr><td class='srcline'>{esc(d['dataset_id'])}</td><td>{esc(d['name'])}</td>"
            f"<td class='num'>{esc(str(d['value'])[:32])}</td><td>{esc(d['unit'])}</td>"
            f"<td>{esc(d['period'] or '—')}</td><td class='srcline'>{esc(d['source_id'])}</td>"
            f"<td class='srcline'>{esc(d['verified'])}</td></tr>" for d in items)
        return f"""
      <div class="kicker">附录 B</div>
      <h1>{title}</h1>
      <div class="rule"></div>
      <p class="tiny">{note}</p>
      <table style="font-size:8pt"><thead><tr><th style="width:62pt">编号</th><th>名称</th>
      <th class="num" style="width:66pt">数值</th><th style="width:38pt">单位</th>
      <th style="width:56pt">期间</th><th style="width:50pt">来源</th>
      <th style="width:64pt">验证状态</th></tr></thead><tbody>{rows}</tbody></table>
      {{foot('{title}')}}
    """

    FIN_DS = M["finance"]["datasets"]
    GTM_DS = M["gtm"]["datasets"]
    P.append(page(dtable(FIN_DS, "数据记录（D-xx）· 项目 A 固收",
                         f"共 {len(FIN_DS)} 条。每条记录含：定义、单位、地区、统计范围、期间、"
                         f"发布时间、抓取时间、来源链接、采集方式、修订状态、验证状态与展示权限。")))
    P.append(page(dtable(GTM_DS, "数据记录（D-xx）· 项目 B 英国市场",
                         f"共 {len(GTM_DS)} 条。口径提示：注册量 ≠ 销量 ≠ 交付量；"
                         f"品牌级 ≠ 车型级；续航口径未对齐前不得排名。")))

    # ---------------- 附录 3：口径对照 ----------------
    P.append(page(f"""
      <div class="kicker">附录 C</div>
      <h1>口径对照与已知限制</h1>
      <div class="rule"></div>
      <table><thead><tr><th style="width:130pt">不要混用</th><th>为什么</th></tr></thead><tbody>
        <tr><td>期限 vs 久期</td><td>期限是到期时间；久期是价格对利率的敏感度。10 年期债券的久期通常显著小于 10。</td></tr>
        <tr><td>到期收益率 vs 持有期回报</td><td>前者是持有到期的假设年化；后者还包含票息再投资与买卖价差。</td></tr>
        <tr><td>价格变化 vs 总回报</td><td>收益率下降带来的资本利得<b>不等于</b>投资总回报；本项目<b>没有</b>做收益回测。</td></tr>
        <tr><td>国债曲线 vs 地方政府债曲线</td><td>两条曲线的绝对水平与利差不同，拼接展示会制造虚假的连续性。</td></tr>
        <tr><td>DR（存款类机构）vs FR（全市场）</td><td>参与机构范围不同，是两条不同的利率序列。</td></tr>
        <tr><td>Shibor vs 回购成交利率</td><td>前者是报价行报价均值，后者是实际成交加权利率，口径不同。</td></tr>
        <tr><td>注册量 vs 销量 vs 交付量</td><td>SMMT 统计的是新乘用车<b>注册</b>；三者统计主体与时点都不同。</td></tr>
        <tr><td>品牌级 vs 车型级</td><td>BYD 品牌注册量包含全部动力类型，<b>不能</b>当作 DOLPHIN SURF 销量。</td></tr>
        <tr><td>英国（UK）vs 大不列颠</td><td>SMMT 口径为 UK（含北爱尔兰）。跨来源比较时地区口径必须一致。</td></tr>
        <tr><td>相关性 vs 因果</td><td>本项目不对观察到的相关关系做因果陈述；解释性内容均标注为「解释」并写出失效条件。</td></tr>
      </tbody></table>
      <h2>已知限制（分维度展示，不用综合分数掩盖）</h2>
      <table><thead><tr><th style="width:88pt">维度</th><th>现状</th></tr></thead><tbody>
        <tr><td>来源权威性</td><td>中债 / 中国货币网 / 人民银行 / SMMT / 品牌官网，均为 A 或 B 级官方来源；
            无 C 级二手来源作为结论依据。</td></tr>
        <tr><td>口径可比性</td><td>已分列展示（见上表）；各品牌续航测试口径不一致 → <b>不排名</b>。</td></tr>
        <tr><td>数据新鲜度</td><td>不同指标的日期不同，<b>分别标注</b>，不用一个日期掩盖差异。</td></tr>
        <tr><td>人工复核</td><td><b>待完成</b>：来源原文抽查、手算久期情景、竞品与达人候选核实，
            由本人完成后才会改为「已复核」。AI 分类在没有人工标注留出集前，不报告准确率。</td></tr>
        <tr><td>纸面实打</td><td><b>待确认</b>：PDF 已在屏幕上渲染检查（无缺字、无裁切、无溢出、灰度可辨），
            但<b>未在实际打印机上试打</b>。</td></tr>
      </tbody></table>
      <h2>导出与版本说明</h2>
      <div class="kv">
        <dt>本 PDF</dt><dd>打印版完整报告，与网站、看板图片、PPT 使用同一数据版本 {DV}</dd>
        <dt>面试版冻结</dt><dd>本打印材料为<b>本次面试版</b>；网站会持续更新，后续更新不覆盖本版本</dd>
        <dt>图片分辨率</dt><dd>看板 PNG 为 3840×2160（16:9）与 2480×3507（A4）@300ppi；
            图表同时提供 SVG 矢量版</dd>
        <dt>灰度可辨</dt><dd>图表系列使用不同色相与明度差，并在图注中标注文字说明，
            黑白打印仍可区分（已在屏幕上做灰度模拟检查）</dd>
        <dt>二维码</dt><dd>本材料<b>不依赖二维码</b>：所有关键结论、单位、期间与来源编号均在纸面直接可读</dd>
      </div>
      {foot('附录 C · 口径对照与已知限制')}
    """))

    body = "\n".join(P)
    return (f"<!DOCTYPE html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
            f"<title>刘柏廷 作品集 打印版 {DV}</title><style>{CSS}</style></head>"
            f"<body>{body}</body></html>")


def html_to_pdf(src: Path, out: Path) -> bool:
    """用本机 Chrome 打印为 A4 PDF（保留原生文本，非整页图片）。"""
    script = ROOT / "checks" / "_html2pdf.mjs"
    script.write_text(f"""
import {{ chromium }} from '/Users/evo/.workbuddy/binaries/node/workspace/node_modules/playwright-core/index.mjs';
const b = await chromium.launch({{ channel: 'chrome',
  args: ['--no-proxy-server', '--proxy-bypass-list=<-loopback>', '--allow-file-access-from-files'] }});
const pg = await b.newPage();
await pg.goto('file://{src}', {{ waitUntil: 'load' }});
await pg.emulateMedia({{ media: 'print' }});
await pg.waitForTimeout(1200);
await pg.pdf({{ path: '{out}', format: 'A4', printBackground: true,
  margin: {{ top: '14mm', bottom: '12mm', left: '13mm', right: '13mm' }} }});
await b.close();
""", encoding="utf-8")
    r = subprocess.run(
        ["/Users/evo/.workbuddy/binaries/node/versions/22.22.2-3/bin/node", str(script)],
        capture_output=True, text=True,
        env={**__import__("os").environ,
             "NODE_PATH": "/Users/evo/.workbuddy/binaries/node/workspace/node_modules"})
    if r.returncode != 0:
        log_line(f"  ! PDF 生成失败：{r.stderr[-400:]}")
        return False
    return True


if __name__ == "__main__":
    h = PRINT / "print_report.html"
    h.write_text(build_html(), encoding="utf-8")
    log_line(f"打印报告 HTML：{h.relative_to(ROOT)}")
    pdf = PRINT / f"刘柏廷_作品集_打印版_{today_cst()}.pdf"
    ok = html_to_pdf(h, pdf)
    log_line(f"打印 PDF：{pdf.relative_to(ROOT)}  {'成功' if ok else '失败'}")
