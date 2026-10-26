"""生成：英文独立研究落地页、简历 PDF、checks/ 验收文档，并复制证书与照片素材。"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, SOURCES, log_line, today_cst                 # noqa: E402

M = json.loads((ROOT / "github-upload" / "data" / "market.json")
               .read_text(encoding="utf-8"))
FX, GX = M["finance"]["derived"], M["gtm"]["derived"]
CUR, MM = FX["current"], FX["money_market"]
DUR = {r["shift_bp"]: r for r in FX["duration_scenario"]["rows"]}
ST = FX["stages"]
BV, BY = GX["byd"]["month"], GX["byd"]["ytd"]
CH, PM, CMP = GX["channels"], GX["powertrain_mix"], GX["competitors"]
DV, GEN, BVv = M["meta"]["data_version"], M["meta"]["generated_at"], M["meta"]["build_version"]
SITE = ROOT / "github-upload"
GTMDIR = SITE / "gtm"
GTMDIR.mkdir(parents=True, exist_ok=True)
RESEARCH = ROOT / "research"
if not RESEARCH.exists():
    RESEARCH.mkdir(parents=True)

# ============================================================ 英文落地页
LANDING = f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Comparing UK compact EVs — an independent facts sheet</title>
<meta name="description" content="Independent research: how to compare official UK information on compact electric cars without being misled by incomparable specs.">
<link rel="stylesheet" href="../styles.css">
<style>
  .disclosure {{ background:#FBF0E9; border:1px solid #EBD5C4; border-left:5px solid #9A4318;
    border-radius:4px; padding:14px 18px; margin:20px 0; }}
  .disclosure b {{ color:#9A4318; }}
  .en {{ max-width:760px; }}
  .en h1 {{ font-size:clamp(26px,4vw,36px); }}
  .en table {{ font-size:14.5px; }}
  .axes {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:14px; margin:18px 0; }}
  .axis {{ border:1px solid var(--line); border-radius:8px; padding:14px 16px; }}
  .axis h4 {{ margin:0 0 6px; color:var(--accent); }}
  .axis p {{ margin:0; font-size:14.5px; color:var(--ink-2); }}
</style>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site">
  <div class="wrap nav">
    <a class="brand" href="../index.html">BoTing LIU<span>Independent research</span></a>
    <nav aria-label="Main">
      <ul>
        <li><a href="../index.html">Home (中文)</a></li>
        <li><a href="../project-b.html">Project (中文)</a></li>
        <li><a href="./landing.html" aria-current="page">Facts sheet (EN)</a></li>
      </ul>
    </nav>
  </div>
</header>

<main id="main"><div class="wrap en">

  <div class="disclosure">
    <b>INDEPENDENT RESEARCH — NOT AFFILIATED WITH ANY BRAND.</b><br>
    This page is produced by an independent researcher. It is <b>not</b> a brand publication,
    <b>not</b> an advertisement, and <b>not</b> a recommendation or offer to purchase.
    No test drives can be booked here and no sales enquiries are collected on behalf of
    any manufacturer or dealer. Figures are reproduced from manufacturers' own UK websites
    on the date shown.
  </div>

  <h1>Comparing small EVs in the UK is harder than it should be</h1>
  <p class="lede">
    The information is public. It is just not <b>comparable</b>. Four things have to line up
    before any comparison means anything — and on several brand sites, one of them
    (price) cannot be read from the page at all.
  </p>

  <h2>The four things that must line up</h2>
  <div class="axes">
    <div class="axis"><h4>1. Range test cycle</h4>
      <p>Brands quote WLTP combined, WLTP urban, or their own headline figure.
      A 200-mile figure under one cycle is not comparable with a 200-mile figure under another.</p></div>
    <div class="axis"><h4>2. Battery convention</h4>
      <p>Usable versus gross capacity, and pack configuration differ between brands.
      Two "52 kWh" cars may not deliver the same usable energy.</p></div>
    <div class="axis"><h4>3. Price basis</h4>
      <p>On-the-road price, PCP monthly payment, and business/fleet pricing are three
      different numbers. Mixing them produces a comparison that fails in procurement review.</p></div>
    <div class="axis"><h4>4. Finance conditions</h4>
      <p>A monthly payment is meaningless without the deposit, the term, the balloon
      payment and the APR. All four must be quoted together.</p></div>
  </div>

  <h2>What I could verify</h2>
  <p>Only figures published on each brand's own UK website, on the retrieval date.
  Everything else is marked <b>not retrieved</b> — not estimated.</p>
  <div class="scroll-x">
  <table class="data">
    <caption>Official published figures. Test cycles may differ; figures are not ranked.</caption>
    <thead><tr><th>Model</th><th>Role</th><th>Official range</th><th>Battery</th><th>Source</th></tr></thead>
    <tbody>
    {''.join(
      "<tr><td>" + c['model'] + "</td><td>" + ("Subject of study" if c['is_subject'] else "Direct competitor") + "</td><td>"
      + (" / ".join(c['range_miles']) + " miles" if c['range_miles'] else "<b>not retrieved</b>") + "</td><td>"
      + (" / ".join(c['battery_kwh']) + " kWh" if c['battery_kwh'] else "<b>not retrieved</b>") + "</td><td>"
      + f"<a href='{c['source_url']}' target='_blank' rel='noopener noreferrer'>{c['source_url'].split('/')[2]} ↗</a></td></tr>"
      for c in CMP)}
    </tbody>
  </table>
  </div>

  <h2>What I deliberately did not do</h2>
  <div class="scroll-x">
  <table class="data">
    <thead><tr><th>Field</th><th>Status</th><th>Why</th></tr></thead>
    <tbody>
      <tr><td>On-the-road price / PCP monthly payment</td><td><b>Not retrieved</b></td>
          <td>Loaded client-side on the brand site; not obtainable from the static page</td></tr>
      <tr><td>Deposit, term, balloon payment, APR</td><td><b>Not retrieved</b></td>
          <td>Only meaningful together with the payment figure</td></tr>
      <tr><td>Model-level registration volume</td><td><b>Restricted</b></td>
          <td>SMMT's free public data covers only the top 10 models</td></tr>
      <tr><td>Test-cycle alignment</td><td><b>Not done</b></td>
          <td>Would require manufacturer documentation beyond the public pages</td></tr>
    </tbody>
  </table>
  </div>
  <p class="small muted">
    A figure without a source is worse than a blank cell, because it looks precise
    while being unverifiable. That is why the price column above is not filled in.
  </p>

  <h2>Market context (SMMT, official)</h2>
  <p>
    In the latest month, {GX['total_month']:,.0f} new cars were registered in the UK.
    Battery electric vehicles accounted for <b>{GX['bev_month']:,.0f} units ({PM[0]['share']}% share,
    {PM[0]['yoy']:+.1f}% year on year)</b>; year to date, BEVs total {GX['bev_ytd']:,.0f} units.
    <b>Registration is not a measure of sales or deliveries.</b>
  </p>
  <p>
    Channel split — the detail that matters most for fleet buyers:
    <b>fleet {CH[0]['share']}%</b>, private {CH[1]['share']}%,
    business {CH[2]['share']}%.
    Denominator: <b>all</b> new car registrations, not the BEV segment.
  </p>

  <h2>Sources</h2>
  <div class="scroll-x">
  <table class="data">
    <thead><tr><th>ID</th><th>Source</th><th>Type</th><th>Region</th></tr></thead>
    <tbody>
    {''.join(f"<tr><td><code>{k}</code></td><td>{v['name']}</td><td>{'Official / primary' if v['authority']=='A' else 'Industry body'}</td><td>{v['region']}</td></tr>" for k, v in SOURCES.items())}
    </tbody>
  </table>
  </div>
  <p class="small muted">
    All sources are single authoritative sources and have <b>not</b> been independently
    cross-validated. Same-origin republication does not count as independent verification.
  </p>

  <h2>How this is kept up to date</h2>
  <p class="small">
    Registration and market data update on release; competitor pages are checked daily.
    If a source is unreachable, the previous verified value is retained and flagged as stale —
    this page never writes a zero or silently substitutes an old value for a new one.
    Data version <b>{DV}</b>, generated <b>{GEN}</b>.
  </p>

  <div class="disclosure">
    <b>Limitations, stated plainly.</b>
    This is an independent research project, not a brand publication and not a commercial
    service. It has no sponsorship, no affiliate arrangement, and no brand relationship.
    No user research was conducted, so nothing here represents "what customers want".
    No creator has been contacted. No registrations, test drives or purchases are collected.
    Nothing on this page is financial or purchasing advice.
  </div>

</div></main>

<footer class="site"><div class="wrap">
  <div>Independent research facts sheet · BoTing LIU</div>
  <div class="tiny">Data version {DV}　Build {BVv}</div>
</div></footer>
</body>
</html>
"""
(GTMDIR / "landing.html").write_text(LANDING, encoding="utf-8")
(RESEARCH / "gtm" / "05_landing_page_en.html").write_text(LANDING, encoding="utf-8")
log_line(f"  写入 github-upload/gtm/landing.html 与 research/gtm/05_landing_page_en.html")

# ============================================================ 简历 PDF
RESUME = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>刘柏廷 BoTing LIU · 简历（面试版 {DV}）</title><style>
@page {{ size:A4 portrait; margin:12mm 12mm 10mm; }}
* {{ box-sizing:border-box; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
body {{ margin:0; font-family:"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
        color:#1F2933; font-size:9.6pt; line-height:1.55; }}
.name {{ font-size:19pt; font-weight:700; color:#1B3A6B; margin:0; letter-spacing:.5pt; }}
.role {{ font-size:10pt; color:#52606D; margin:2pt 0 0; }}
.contact {{ font-size:9pt; color:#52606D; margin:6pt 0 0; }}
.bar {{ height:3pt; background:#1B3A6B; margin:8pt 0 10pt; }}
h2 {{ font-size:11pt; color:#1B3A6B; margin:11pt 0 4pt; padding-bottom:2pt;
      border-bottom:1px solid #DCE1E8; }}
h3 {{ font-size:9.9pt; margin:7pt 0 1pt; color:#1F2933; }}
h3 .when {{ float:right; font-weight:400; font-size:8.8pt; color:#7B8794; }}
ul {{ margin:2pt 0 0; padding-left:13pt; }}
li {{ margin-bottom:1.8pt; }}
.tag {{ display:inline-block; font-size:7.6pt; padding:0.5pt 4pt; border-radius:7pt;
        background:#FBF0E9; color:#9A4318; border:1px solid #EBD5C4; margin-left:3pt; }}
.pend {{ background:#FFF6E5; color:#7A5310; border:1px dashed #E0BE7A; border-radius:3px;
         padding:0 4px; }}
.grid {{ display:grid; grid-template-columns:1fr 1fr; gap:0 10mm; }}
.foot {{ margin-top:10pt; padding-top:4pt; border-top:1px solid #DCE1E8; font-size:7.6pt;
         color:#7B8794; }}
</style></head><body>

<p class="name">刘柏廷　BoTing LIU</p>
<p class="role">澳门科技大学 商学院　|　固收研究 · 机构与渠道销售 · 出海 GTM</p>
<p class="contact">
邮箱 lbt2238516944@163.com　手机 <span class="pend">待确认</span>　
GitHub <span class="pend">待确认</span>　作品集 <span class="pend">待确认（部署后填入）</span>
</p>
<div class="bar"></div>

<h2>个人定位</h2>
<p style="margin:0">商科背景，五段金融与零售实习横跨卖方研究、机构与渠道销售、商务拓展。
核心能力是把公开数据变成可被追问的判断，并把它翻译成不同约束的对象能听懂的语言。
另有两项独立完成的 AI 辅助研究项目（固收市场观察、英国电动车 GTM），
全部数据可追溯至来源编号。</p>

<h2>实习经历</h2>

<h3>华福证券股份有限公司 · 研究所策略组 · 首席分析师助理<span class="when">2026.07 – 2026.09</span></h3>
<ul>
<li><b>日频跟踪研究支持</b>：维护 A 股、港股及宏观流动性日度跟踪体系，监测 PMI、社融、两融余额等关键指标；更新市场数据及晨会/日报点评。</li>
<li><b>政策解读专题输出</b>：梳理重要政策及宏观事件，提炼政策目标、受益方向与市场影响路径；累计输出 10+ 份政策解读/专题材料。</li>
<li><b>客户需求对接及路演服务</b>：筹备策略路演、电话会议与调研活动，捕捉客户关注的市场问题及反馈。</li>
</ul>

<h3>京东集团 · 京东零售 · 商务拓展岗<span class="when">2026.03 – 2026.07</span></h3>
<ul>
<li><b>链路拆解预警促活</b>：围绕线索至上线全周期拆解转化数据，识别流失卡点，搭建城市预警机制，对滞后客户前置干预。</li>
<li><b>分层拓客赋能裂变</b>：对高价值客户分层运营，挖掘竞对翻牌客户并定制攻坚方案，为存量商家输出裂变赋能体系。</li>
<li><b>中台协同迭代人效</b>：统筹电销、工程、供应链中台，支撑 90+ 招商经理开展业务，搭建监控看板落地人效督导。</li>
</ul>

<h3>诺安基金管理有限公司 · 华中业务部 · 渠道经理助理<span class="when">2025.09 – 2026.03</span></h3>
<ul>
<li><b>渠道维护与精准营销</b>：深度对接华中四省市渠道，跟踪渠道客户结构、产品销售进度及市场反馈；落地差异化营销与竞品分析。</li>
<li><b>投研观点转译与渠道赋能</b>：围绕科技与半导体主题基金，结合持仓、行业景气、历史净值与回撤特征，拆解赛道逻辑与客户适配要点；参与路演材料并开展渠道培训，累计覆盖 200+ 人次。</li>
<li><b>效能建模渠道优化</b>：参与多场线上线下沙龙路演，搭建渠道效能评估模型，围绕覆盖率与转化率复盘渠道反馈。</li>
</ul>

<h3>鹏扬基金管理有限公司 · 机构业务部 · 机构经理助理<span class="when">2024.12 – 2025.03</span></h3>
<ul>
<li><b>机构客户开发与需求研判</b>：面向券商资管、城商行理财子、地方产业平台开展前期拜访与需求访谈；建立 22 家机构客户需求台账，匹配风险偏好、久期约束及配置诉求。</li>
<li><b>定制化产品方案与拜访沟通</b>：结合 Wind 与内部组合数据，针对固收+、权益赛道定制尽调材料与投资建议书，拆解收益、回撤与最大风险敞口；开展 12 场线上机构交流。</li>
<li><b>准入跟踪转化推进</b>：搭建机构准入及意向跟踪台账，协同产品与投研解决机构关切，推动 3 家机构完成产品准入。<b>「意向规模约 8,000 万元」为意向口径，非已到账收入。</b></li>
</ul>

<h3>中国银河证券 · 银河金汇资产管理 · 固收二部 · 多资产投资助理岗<span class="when">2024.06 – 2024.09</span></h3>
<ul>
<li><b>产品研究募集落地</b>：协助梳理「辰星 FOF 增利 1 号」等固收及多资产产品的定期报告、持仓与估值数据；撰写 20+ 份产品材料并支持 4 场路演，协助完成约 1,000 万元产品募集落地。</li>
<li><b>净值跟踪与业绩归因</b>：基于 Wind 开展净值跟踪及业绩归因，拆解债券、权益等资产对净值波动的影响，覆盖 10+ 份产品/组合。</li>
<li><b>投研支持与投后管理</b>：跟踪锂矿、光伏等产业链价格与市场信息；协助 FOF 投后管理，维护投资台账及产品估值表。</li>
</ul>

<h3>贵阳银行 · 成都分行 · 财富经理助理岗<span class="when">2023.06 – 2023.09</span></h3>
<ul>
<li><b>产品推介与募集落地</b>：梳理「爽银财富」固收理财、大额存单及代销保险等产品要素与风险等级匹配规则；撰写 15+ 份产品介绍及话术材料并支持 3 场网点沙龙，协助完成约 600 万元理财及存款类产品落地。</li>
<li><b>客户经营与需求响应</b>：维护高净值及潜力客户档案，整理持仓、到期日与风险测评结果；覆盖 30+ 位重点客户日常跟进。</li>
<li><b>厅堂服务与活动支持</b>：协助识别有理财需求的客户并完成风险测评、双录及资料初审；维护客户台账与活动反馈。</li>
</ul>

<h2>项目经历（独立完成 · AI 辅助）</h2>

<h3>A｜AI 固收市场观察与机构客户沟通研究</h3>
<ul>
<li>从中国债券信息网、中国货币网、人民银行公告等官方公开来源自建日频数据管道（Python），
覆盖国债收益率曲线关键期限、银行间质押式回购利率与公开市场操作；产出 13 条带来源编号、
统计口径与验证状态的数据记录。</li>
<li>搭建修正久期情景工具，按 <code>dP/P ≈ -D_mod·dy + 0.5·C·dy²</code> 量化
±25/±50/±100bp 平行移位对组合估值的近似影响，并说明凸性修正量级
（±25bp 内约 6%、±100bp 内约 24%）；参数全部标注为教学假设。</li>
<li>将观点转译为不同约束客户的沟通材料：由「观点陈述」改为「在你的久期上限与回撤容忍下，
此情景意味着多少回撤」，配套 60 秒口述稿与一页纸材料。</li>
</ul>

<h3>B｜英国电动车市场情报与 GTM 执行工作台（BYD DOLPHIN SURF）</h3>
<ul>
<li>搭建英国市场监测管道，接入 SMMT 官方注册数据（动力类型、销售渠道、品牌级、车型 Top10），
建立可增量更新、失败可降级的数据基线；严格区分注册量/销量/交付量与品牌级/车型级口径。</li>
<li>基于真实渠道结构（车队 {CH[0]['share']}% vs 私人 {CH[1]['share']}%）提出内容切口优先级建议：
优先准备车队/公司车决策链所需可比证据；同时给出三条明确失效条件。</li>
<li>在明确合规边界下产出英文独立研究落地页、同级别可比表、内容脚本、合作 brief 与两周执行计划；
对达人筛选主动放弃数值化评分，改为透明的人工证据分层。</li>
</ul>

<h2>教育</h2>
<h3>澳门科技大学 商学院<span class="when">2022 年入学</span></h3>
<p style="margin:0">学位与专业 <span class="pend">待确认</span>　|　
<b>院长优秀生榜</b>（2023/2024 学年，证书编号 D230B0182）</p>

<h2>荣誉（真实证书）</h2>
<div class="grid">
<ul>
<li>「IEERA 杯」国际高校英语阅读挑战赛 中国区<b>一等奖</b>（2023-06-18）</li>
<li>全国大学生奥林匹克数学竞赛（夏季赛）非数学类<b>铜奖</b>（2023-04-09）</li>
<li>国际高校数学建模竞赛 <b>Honorable Mention</b>（2023-07-27）</li>
<li>澳门科技大学商学院「院长优秀生榜」（2024-12）</li>
</ul>
<ul>
<li>全国大学生国际贸易挑战赛 <b>三等奖</b>（2023-07-22）</li>
<li>国际大学生英语翻译挑战赛（IETCCS）C 组 <b>三等奖</b>（2023-07-22）</li>
<li>全国大学生国际中英双语对外翻译能力大赛 <b>三等奖</b>（2023-07）</li>
</ul>
</div>

<h2>技能与特长</h2>
<div class="grid">
<ul>
<li><b>研究分析</b>：SPSS、定量问卷设计、深度访谈、结构化报告撰写</li>
<li><b>技术</b>：Python（requests / pandas / matplotlib 数据采集与可视化）、
Excel 建模、Wind 基础、AI 辅助全栈开发</li>
<li><b>业务</b>：销售漏斗分析、渠道开拓与维护、高净值客户触达、路演呈现、跨部门协调</li>
</ul>
<ul>
<li><b>语言</b>：中文（母语）、英语 CET-6</li>
<li><b>长跑</b>：系统训练 5 年，完成 4 场半程马拉松</li>
<li><b>公众表达</b>：校级辩论赛最佳辩手；结构化阅读与个人知识库 500+ 篇笔记</li>
</ul>
</div>

<div class="foot">
本简历为面试版（数据版本 {DV}）。标注为「待确认」的字段尚未核实，正式公开版将隐藏。
实习经历中的百分比口径正在核实，未核实前不放入对外版本。
所有经历真实，未经第三方独立核验，可提供实习证明与证书原件。
</div>
</body></html>
"""
C = ROOT / "checks"
(C / "_resume.html").write_text(RESUME, encoding="utf-8")
log_line("  写入 checks/_resume.html")


def chrome_pdf(src: Path, out: Path) -> bool:
    js = ROOT / "checks" / "_pdf.mjs"
    js.write_text(f"""
import {{ chromium }} from '/Users/evo/.workbuddy/binaries/node/workspace/node_modules/playwright-core/index.mjs';
const b = await chromium.launch({{ channel: 'chrome',
  args: ['--no-proxy-server','--proxy-bypass-list=<-loopback>','--allow-file-access-from-files'] }});
const p = await b.newPage();
await p.goto('file://{src}', {{ waitUntil: 'load' }});
await p.emulateMedia({{ media: 'print' }});
await p.waitForTimeout(900);
await p.pdf({{ path: '{out}', format: 'A4', printBackground: true,
  margin: {{ top:'12mm', bottom:'10mm', left:'12mm', right:'12mm' }} }});
await b.close();
""", encoding="utf-8")
    r = subprocess.run(
        ["/Users/evo/.workbuddy/binaries/node/versions/22.22.2-3/bin/node", str(js)],
        capture_output=True, text=True,
        env={**__import__("os").environ,
             "NODE_PATH": "/Users/evo/.workbuddy/binaries/node/workspace/node_modules"})
    if r.returncode:
        log_line(f"  ! 简历 PDF 失败：{r.stderr[-300:]}")
    return r.returncode == 0


resume_pdf = ROOT / "interview" / f"刘柏廷_简历_面试版_{DV}.pdf"
ok = chrome_pdf(C / "_resume.html", resume_pdf)
log_line(f"  简历 PDF：{'成功' if ok else '失败'}")
if ok:
    shutil.copy(resume_pdf, SITE / "exports" / resume_pdf.name)

# ============================================================ 素材复制
PH = ROOT / "exports" / "photos"
PH.mkdir(parents=True, exist_ok=True)
CERT_SRC = Path("/Users/evo/Desktop/校招/作品集/获奖证书")
PHOTO_SRC = [
    Path("/Users/evo/Desktop/校招/作品集/证件照.jpg"),
    Path("/Users/evo/Desktop/校招/高清照.jpg"),
]
copied = []
if CERT_SRC.exists():
    for f in sorted(CERT_SRC.iterdir()):
        if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".pdf") and not f.name.startswith("."):
            shutil.copy2(f, PH / f.name)
            copied.append(f.name)
for f in PHOTO_SRC:
    if f.exists():
        shutil.copy2(f, PH / f"证件照_{f.name}")
        copied.append(f"证件照_{f.name}")
log_line(f"  复制素材 {len(copied)} 个到 exports/photos/")

(RESEARCH / "MATERIAL_INDEX.md").write_text(f"""# 素材索引（找图用）

数据版本 {DV}。

## 一、高清看板（整图，适合 PPT 封面 / 一页总结）

| 文件 | 尺寸 | 用途 |
|---|---|---|
| `exports/dashboards/DASHBOARD_16x9.png` | 3840×2160 @300ppi | 16:9 展示页，直接插 PPT |
| `exports/dashboards/DASHBOARD_16x9.svg` | 矢量 | 需要缩放时用 |
| `exports/dashboards/DASHBOARD_A4_portrait.png` | 2480×3507 @300ppi | A4 打印 |
| `exports/dashboards/DASHBOARD_A4_portrait.pdf` | 矢量 A4 | 打印 |

## 二、单张图表（自由插入现有 PPT）

| 编号 | 文件（`exports/charts/`，同时有 PNG 与 SVG） | 建议插在哪 |
|---|---|---|
| C-01 | `C01_国债收益率曲线_当期` | 项目 A 数据页 |
| C-02 | `C02_收益率曲线_阶段对比` | 项目 A 数据页（推荐主图） |
| C-03 | `C03_久期情景分析` | 项目 A 工具页 |
| C-04 | `C04_期限利差` | 项目 A 备用 |
| C-05 | `C05_英国动力类型结构` | 项目 B 市场页 |
| C-06 | `C06_英国渠道结构` | 项目 B 判断页（推荐主图） |
| C-07 | `C07_BYD品牌注册量` | 项目 B 品牌页 |
| C-08 | `C08_续航对比` | 项目 B 竞品页（带口径警示） |
| C-09 | `C09_英国BEV车型Top10` | 项目 B 备用 |

每张图的来源编号、单位、期间见 `github-upload/data/market.json` → `charts[]`，
或网站「证据与限制」页的图表索引。

## 三、照片与证书（`exports/photos/`）

- 获奖证书原件：{len([x for x in copied if not x.startswith("证件照")])} 个文件
- 证件照素材：{[x for x in copied if x.startswith("证件照")] or "未找到"}

> ⚠️ **公开提醒**：`exports/photos/` 内含证书原件与个人照片。
> 证书保持真实内容（名称、等级、日期、编号、印章均未修改）。
> **是否公开由你决定**；当前网站**没有**嵌入这些照片。

## 四、PPT 与打印版

- `slides/刘柏廷_作品集_两个项目模块_{DV}.pptx` —— 10 页，16:9，可编辑
- `print/刘柏廷_作品集_打印版_{DV}.pdf` —— 14 页 A4
- `interview/刘柏廷_简历_面试版_{DV}.pdf` —— 简历

## 五、命名与版本规则

`<项目>_<内容>_<版本日期>.<扩展名>`
所有素材同属数据版本 **{DV}**，构建版本 **{BVv}**，生成于 {GEN}。
""", encoding="utf-8")
log_line("  写入 research/MATERIAL_INDEX.md")

# ============================================================ checks 文档
(C / "VERSION_MANIFEST.md").write_text(f"""# 版本清单

## 本次导出

| 项 | 取值 |
|---|---|
| 数据版本 | **{DV}** |
| 构建版本 | **{BVv}** |
| 管道版本 | {M['meta']['pipeline_version']} |
| 生成时间 | {GEN} |
| 时区 | Asia/Shanghai (UTC+8) |
| 分析报告信息截止时间 | {DV}（各指标期间见下） |

## 各数据指标的期间（**不同指标日期不同，分别标注**）

| 数据集 | 期间 | 来源 | 验证状态 |
|---|---|---|---|
{chr(10).join(f"| `{d['dataset_id']}` | {d['period'] or '—'} | {d['source_id']} | {d['verified']} |" for d in M['finance']['datasets'] + M['gtm']['datasets'])}

## 版本一致性

- 网站：`github-upload/data/market.json` → meta.data_version = {DV}
- 看板图：`exports/dashboards/*` → 由同一版本 `src/build_all.py` 生成
- 单图：`exports/charts/*` → 同上
- PPT：`slides/*{DV}.pptx` → 读取同一 market.json
- 打印 PDF：`print/*{DV}.pdf` → 读取同一 market.json

**四个出口使用同一数据版本，未手工另填数字。** 校验脚本见 `checks/validation.json`。
""", encoding="utf-8")

(C / "KNOWN_LIMITATIONS.md").write_text(f"""# 已知限制（不隐瞒、不用一分数掩盖）

数据版本 {DV}。

## 一、来源与验证

| 限制 | 说明 |
|---|---|
| 全部单源权威 | 中债 / 中国货币网 / 人民银行 / SMMT / 品牌官网，均为单一权威来源，**尚未独立交叉验证**。同源转载不算独立验证。 |
| 无第三方业务数据 | 没有品牌侧销量、流量、线索或订单数据。**不声称提升销量或降低获客成本。** |
| 无用户研究 | 未做访谈、问卷或评论挖掘。因此**没有**任何「用户想要什么」的结论。 |
| 无人工基准 | 未测人工做同一任务所需时间，所以**不报「节省 xx%」**；只给程序流程耗时。 |

## 二、数据可得性

| 项 | 状态 |
|---|---|
| BYD 官网价格 / PCP 月供 | 未获取（前端动态渲染） |
| 完整车型级注册量 | 受限（SMMT 免费页仅 Top10） |
| 固收基金份额/区间/分红/费用/披露滞后 | 未取得 → 基金可比研究**未完成** |
| 公开市场净投放金额 | 未可靠解析（须同时核对投放与到期两侧） |
| Vauxhall / Citroën / Fiat / Kia / Peugeot / Hyundai 英国站点 | 实测不可达或 403 → 未纳入竞品基线 |

## 三、口径限制

- 各品牌续航测试口径不一致 → **不排名**
- 渠道结构为**全市场**口径，非纯电细分，也非该车型自身 → 已标注外推限制
- 注册量 ≠ 销量 ≠ 交付量；品牌级 ≠ 车型级
- 久期情景为**平行移位**假设；扭曲型变动下偏差方向不确定
- 教学情景参数（D=5.0、C=30、面值 1 亿）**不是任何真实产品参数**

## 四、未做过的检查（**不得标记为通过**）

| 检查 | 状态 | 说明 |
|---|---|---|
| 网站渲染与交互 | ✅ 已通过 | 5 页、0 未绑定数值、0 破图、0 控制台错误、无 44px 以下控件 |
| 打印版逐页溢出 | ✅ 已通过 | 14 页、0 溢出、无缺字（屏幕渲染） |
| 图片分辨率 | ✅ 已通过 | 读取 PNG 头部像素：3840×2160 / 2480×3507 @300ppi |
| PPTX 结构检查 | ✅ 已通过 | 18 项（素材、文字溢出测算、可编辑性、数值一致性） |
| **PPTX 原生渲染目检** | ❌ **未完成** | 本机无 LibreOffice / PowerPoint / Keynote，无法把 pptx 渲染为页面图片。**需你在 PowerPoint / WPS 中逐页看一遍。** |
| **纸面实打** | ❌ **未确认** | 屏幕检查通过，但**未在真实打印机上试打** |
| **真实用户测试** | ❌ **未测试** | 未邀请他人完成三项查找任务。AI 模拟用户不能替代真实用户。 |
| **人工复核** | ❌ **待完成** | 抽查来源原文、手算久期情景、复核竞品与达人候选 —— 见 `interview/07_self_check_list.md` |
| **定时任务真实触发** | ⏳ 已配置 | 以实际触发一次并拿到证据为准 |
| **压缩包独立解压验证** | ✅ 已通过 | 见 `checks/archive_verify.txt` |

## 五、数据保存与再分发

- `data/raw/` 保存原始响应，仅用于复现与排错；**不进入公开目录**。
- 公开目录（`github-upload/`）只含派生数值、来源链接与自制图表，**不镜像原始页面**。
- 若某来源条款要求限期删除，执行删除并在本文件记录对复现的影响。
- 本项目**未绕过**任何访问控制、验证码或付费墙。
""", encoding="utf-8")

(C / "SOURCE_CATALOG.md").write_text(f"""# 来源目录（含不可达来源记录）

数据版本 {DV}。**包含不可达来源——这本身就是研究纪律的证据。**

| 编号 | 来源 | 权威性 | 地区 | 采集方式 | 本次结果 |
|---|---|---|---|---|---|
{chr(10).join(
  f"| `{k}` | {v['name']} | {v['authority']} | {v['region']} | {v['method']} | "
  + ("成功" if k not in ('S-VX-01', 'S-CT-01') else "**不可达（已排除）**") + " |"
  for k, v in SOURCES.items())}

## 说明

- **A 级**：原始披露 / 官方机构（政府、央行、法定披露平台、品牌官网）
- **B 级**：官方衍生数据 / 行业机构（SMMT 等）
- **C 级**：媒体或二手来源 —— **本项目没有用 C 级来源支撑任何结论**

## 搜索摘要的使用纪律

搜索摘要**只作为线索**，重要事实一律打开原文核对。
同源转载**不算**独立交叉验证。

## 采集边界

只采集官方公开页面与公开接口中**必要的少量字段**；
不绕过访问控制、验证码与付费墙；不镜像原始页面；
不批量抓取超出研究必要范围的字段。
""", encoding="utf-8")

(C / "pipeline_fixups.md").write_text("""# 管道调参与错误修订记录

按时间顺序记录建设期实际遇到的问题与修正方式。**这份记录是可复现性的一部分。**

## 1. 中债收益率曲线：`qxmc` 参数选错

- **现象**：`czbQueryXy` 返回的曲线 `ycDefName` 是「财政部-中国地方政府债券收益率曲线」，
  不是国债曲线。
- **错误做法**（差点采用）：用 `qxmc=2` 取历史曲线，与最新国债曲线混拼 →
  会造成两条不同曲线被拼在一起，期限利差全错。
- **实测结论**：
  - `qxmc=1` → 仅「中债国债收益率曲线」（111 个标准期限点）
  - `qxmc=2` → 仅「财政部-中国地方政府债券收益率曲线」（81 点）
  - `qxmc>=3` → 同时返回两条
- **修正**：统一使用 `qxmc=1`；并在校验中加了一条「未混用地方政府债曲线」的断言。

## 2. 中国货币网 FRR：字段名与预期不符

- **现象**：`records[].lfiFrValue` 为 `null`，解析得到 0 条有效数据。
- **实测结构**：数值实际在 `records[].frValueMap`，键为
  `FR001 / FR007 / FR014 / FDR001 / FDR007 / FDR014`，**值为字符串**（如 `"1.4200"`）。
- **修正**：改读 `frValueMap`，并做 `float()` 转换与异常捕获。

## 3. 中国货币网 Shibor：`pageSize` 影响返回结构

- **现象**：大 `pageSize` 请求返回的记录里没有期限键。
- **修正**：改为按 `pageSize=5` 请求并做三次回退尝试；
  解析时忽略大小写扫描键名（兼容 `1W` / `shibor1W` / `shibor_1W`）。

## 4. 本机代理导致间歇性 502

- **现象**：`urllib` 请求 SMMT 与回环地址返回
  `Tunnel connection failed: 502 Bad Gateway`；同一 URL 用 `curl` 有时正常。
- **根因**：本机存在 HTTP 代理 `127.0.0.1:64265`，对回环与部分外网请求拦截。
- **修正**：
  1. `http_get()` 增加 **curl 回退通道**（urllib 失败后自动改用 curl）；
  2. SMMT 抓取增加 3 轮重试；
  3. 所有抓取失败走「保留上次有效结果 + 标记 stale」路径，不写零。

## 5. SMMT 表格是「整表一行」结构

- **现象**：按 `<tr>` 分行解析得到 0 条数据。
- **实际结构**：表头标签与数据在**同一个 `<tr>`** 内，需要把整表拆成扁平单元格后
  按标签位置（动力类型/渠道）或固定宽度（品牌 6 格、车型 3 格）重新分组。
- **修正**：改用扁平单元格 + 标签定位 + 固定宽度分块；
  并加断言「品牌数 > 0」防止静默失败。

## 6. 字体字形缺失

- **现象**：matplotlib 报 `Glyph 8722 (MINUS SIGN) missing`、
  `Glyph 189 (½) missing`、`Glyph 178 (²) missing`。
- **修正**：把数学符号改为字体安全写法（`-`、`0.5`、`^2`）；
  注册 `Hiragino Sans GB` 作为中文主字体。

## 7. 看板导出尺寸不含精确像素

- **现象**：`savefig` 的 `bbox_inches="tight"` 覆盖了 `bbox_inches` 参数，
  导致 16:9 输出为 3727×2189 而非 3840×2160。
- **修正**：导出看板时临时把 `rcParams["savefig.bbox"]` 设为 `"standard"`，
  导出后恢复。现输出精确为 **3840×2160** 与 **2480×3507**。

## 8. 打印版分页溢出

- **现象**：首版项目 B 第 2 页超出 A4 可用高度 342px，附录 B 超出 885px。
- **修正**：限制图高（`max-height`）、项目 B 第 2 页改为双栏并排、
  附录 B 拆为「金融数据记录」与「英国市场数据记录」两页。
- **复检**：`checks/verify_print.mjs` 显示 14 页、**0 溢出**。
""", encoding="utf-8")
log_line("  写入 checks/ 下 4 份验收文档")

# 汇总 validation.json 中的检查项
val = json.loads((C / "validation.json").read_text(encoding="utf-8"))
log_line(f"  validation.json：{val['checked']} 项检查，未通过 {val['failed']} 项")
