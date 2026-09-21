"""
生成可编辑 PPTX（16:9，与用户现有作品集比例一致）与打印报告 HTML。

所有数值从 github-upload/data/market.json 读取 —— 与网站、看板图片同源，
不在本文件里手填任何研究数值。

用法： python src/make_ppt.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, log_line, now_cst, today_cst, iso            # noqa: E402

from pptx import Presentation                                          # noqa: E402
from pptx.dml.color import RGBColor                                    # noqa: E402
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR                        # noqa: E402
from pptx.util import Emu, Inches, Pt                                  # noqa: E402

SITE = ROOT / "github-upload"
CH = ROOT / "exports" / "charts"
SLIDES = ROOT / "slides"
PRINT = ROOT / "print"
SLIDES.mkdir(parents=True, exist_ok=True)
PRINT.mkdir(parents=True, exist_ok=True)

INK = RGBColor(0x1F, 0x29, 0x33)
ACCENT = RGBColor(0x1B, 0x3A, 0x6B)
TEAL = RGBColor(0x10, 0x75, 0x6A)
WARN = RGBColor(0x9A, 0x43, 0x18)
GREY = RGBColor(0x52, 0x60, 0x6D)
LINE = RGBColor(0xDC, 0xE1, 0xE8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
SOFT = RGBColor(0xF5, 0xF7, 0xFA)

CJK = "PingFang SC"           # 主力中文字体（macOS 自带）；Windows 会回退到系统默认
LAT = "Helvetica Neue"

M = json.loads((SITE / "data" / "market.json").read_text(encoding="utf-8"))
FX = M["finance"]["derived"]
GX = M["gtm"]["derived"]
CUR = FX["current"]
MM = FX["money_market"]
DUR = {r["shift_bp"]: r for r in FX["duration_scenario"]["rows"]}
BV = GX["byd"]["month"]
BY = GX["byd"]["ytd"]
DV = M["meta"]["data_version"]
GEN = M["meta"]["generated_at"]


def q(v):
    return f"{v:,}" if isinstance(v, (int, float)) else str(v)


# ------------------------------------------------------------------ 工具
def set_font(run, size, bold=False, color=INK, name=CJK):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = name
    # 同时设置东亚字形，避免 PowerPoint 用回退字体渲染中文
    from pptx.oxml.ns import qn
    rPr = run._r.get_or_add_rPr()
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = rPr.makeelement(qn("a:ea"), {})
        rPr.append(ea)
    ea.set("typeface", CJK)
    cs = rPr.find(qn("a:cs"))
    if cs is None:
        cs = rPr.makeelement(qn("a:cs"), {})
        rPr.append(cs)
    cs.set("typeface", CJK)


def textbox(slide, l, t, w, h, lines, *, size=14, color=INK, bold=False,
            align=PP_ALIGN.LEFT, spacing=1.25, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    first = True
    for ln in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        p.line_spacing = spacing
        if isinstance(ln, tuple):
            txt, sz, bd, col = ln
        else:
            txt, sz, bd, col = ln, size, bold, color
        r = p.add_run()
        r.text = txt
        set_font(r, sz, bd, col)
    return tb


def rect(slide, l, t, w, h, fill=None, line=None, lw=0.75):
    from pptx.enum.shapes import MSO_SHAPE
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(l), Inches(t),
                                Inches(w), Inches(h))
    if fill is None:
        sh.fill.background()
    else:
        sh.fill.solid()
        sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line
        sh.line.width = Pt(lw)
    sh.shadow.inherit = False
    sh.text_frame.text = ""
    return sh


def page(slide, title, kicker=None, num=None):
    """统一的页眉/页脚与底部来源条。"""
    rect(slide, 0.0, 0.0, 13.333, 0.055, fill=ACCENT)
    if kicker:
        textbox(slide, 0.62, 0.34, 11.0, 0.3, [kicker], size=10.5, color=TEAL, bold=True)
    textbox(slide, 0.62, 0.62, 11.6, 0.6, [title], size=24, color=ACCENT, bold=True)
    rect(slide, 0.62, 1.30, 12.1, 0.012, fill=LINE)
    foot = (f"数据版本 {DV}　导出 {GEN[:16]}　版本 {M['meta']['build_version']}　"
            f"｜ 本页与网站、打印 PDF 使用同一数据版本，未手工另填数字")
    textbox(slide, 0.62, 7.03, 12.1, 0.3, [foot], size=8.2, color=GREY)
    if num:
        textbox(slide, 12.3, 0.34, 0.7, 0.3, [num], size=10.5, color=GREY,
                align=PP_ALIGN.RIGHT)


def pic(slide, name, l, t, w):
    p = CH / f"{name}.png"
    if not p.exists():
        log_line(f"  ! 缺图 {name}")
        return
    slide.shapes.add_picture(str(p), Inches(l), Inches(t), width=Inches(w))


def bullets(slide, l, t, w, h, items, *, size=12.5, spacing=1.32):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    first = True
    for it in items:
        txt, sz, col, bold = (it if isinstance(it, tuple) else (it, size, INK, False))
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.line_spacing = spacing
        p.space_after = Pt(5)
        r = p.add_run()
        r.text = txt
        set_font(r, sz, bold, col)
    return tb


# ------------------------------------------------------------------ 建 PPT
def build_pptx() -> Path:
    prs = Presentation()
    prs.slide_width = Emu(12192000)      # 13.333 in
    prs.slide_height = Emu(6858000)      # 7.5 in
    blank = prs.slide_layouts[6]

    # ============ 封面 ============
    s = prs.slides.add_slide(blank)
    rect(s, 0, 0, 13.333, 7.5, fill=WHITE)
    rect(s, 0, 0, 13.333, 0.10, fill=ACCENT)
    textbox(s, 1.0, 1.55, 11.3, 0.5, ["AI 辅助个人研究 · 两项作品模块"],
            size=13, color=TEAL, bold=True)
    textbox(s, 1.0, 2.05, 11.3, 1.5,
            ["固收市场观察与机构客户沟通", "英国电动车市场情报与 GTM 执行工作台"],
            size=30, color=ACCENT, bold=True, spacing=1.18)
    textbox(s, 1.0, 3.95, 11.3, 0.5, ["刘柏廷　BoTing LIU　｜　澳门科技大学 商学院"],
            size=15, color=INK)
    rect(s, 1.0, 4.55, 3.2, 0.02, fill=LINE)
    textbox(s, 1.0, 4.75, 11.3, 1.4, [
        ("可插入现有作品集的两个模块，每个项目 4 页。", 12.5, False, GREY),
        (f"数据版本 {DV}　生成 {GEN[:16]}　构建 {M['meta']['build_version']}", 11, False, GREY),
        ("本模块所有数值由程序采集与计算，来源编号见附录；"
         "未获取的数据留空并注明，不推测。", 11, False, GREY),
    ], spacing=1.4)

    # ============ 项目 A（4 页）============
    # A1 背景 / 任务 / 贡献 / 成果
    s = prs.slides.add_slide(blank)
    page(s, "项目 A ｜ 固收市场观察与机构客户沟通研究", "第 1 页 / 背景 · 任务 · 我的贡献 · 当前成果", "A1")
    rect(s, 0.62, 1.52, 5.9, 2.55, fill=SOFT)
    bullets(s, 0.85, 1.72, 5.45, 2.2, [
        ("背景", 12.5, ACCENT, True),
        ("收益率中枢近年持续下移，久期提供的收益空间在收窄，但久期风险的绝对敞口并未同步下降；"
         "不同约束的机构客户在同一市场判断下受到的影响差别很大。", 11.5, INK, False),
        ("研究问题", 12.5, ACCENT, True),
        ("如何用公开数据把曲线与资金面的现状说清楚，并把「风险」翻译成"
         "不同久期上限与回撤容忍度的客户能听懂的语言？", 11.5, INK, False),
    ])
    rect(s, 6.82, 1.52, 5.9, 2.55, fill=WHITE, line=LINE)
    bullets(s, 7.05, 1.72, 5.45, 2.2, [
        ("我承担的任务", 12.5, ACCENT, True),
        ("· 确定有限核心指标集并逐一验证数据可得性", 11.5, INK, False),
        ("· 编写采集程序（官方公开接口）并落盘、校验、降级", 11.5, INK, False),
        ("· 完成期限利差、三阶段复盘与修正久期情景建模", 11.5, INK, False),
        ("· 输出 60 秒口述稿与一页机构客户沟通材料", 11.5, INK, False),
        ("· 列出反证与失效条件，而非只给结论", 11.5, INK, False),
    ])
    bullets(s, 0.62, 4.30, 12.1, 2.4, [
        ("当前成果（个人研究，非委托项目；无客户、无业绩数据）", 13, TEAL, True),
        (f"· 建成 5 个官方公开来源的日频采集管道：中债收益率曲线（S-CB-01/02）、"
         f"银行间质押式回购利率（S-CM-01）、Shibor（S-CM-02）、央行公开市场公告（S-PB-01）", 12, INK, False),
        (f"· 当前 10Y 国债 {CUR['y10']}%、30Y {CUR['y30']}%、"
         f"10Y-2Y 期限利差 {CUR['spread_10y2y']} 个百分点；DR007 {MM['DR007']}%"
         f"（曲线取数日 {CUR['date']}）", 12, INK, False),
        (f"· 完成三阶段曲线复盘：10Y 由 2024-09-30 的 {FX['stages'][0]['y10']}% "
         f"降至当前 {CUR['y10']}%", 12, INK, False),
        ("· 交付 13 条带来源编号、口径与验证状态的数据记录；明确列出未完成项（基金可比研究、"
         "公开市场净投放自动解析）", 12, INK, False),
    ], spacing=1.28)

    # A2 数据 / 方法 / 看板
    s = prs.slides.add_slide(blank)
    page(s, "项目 A ｜ 数据、方法及关键看板", "第 2 页 / 数据与证据", "A2")
    pic(s, "C02_收益率曲线_阶段对比", 0.62, 1.52, 6.6)
    bullets(s, 7.45, 1.52, 5.3, 5.3, [
        ("数据与口径", 12.5, ACCENT, True),
        ("· 来源：中债估值中心（财政部授权）、全国银行间同业拆借中心、中国人民银行", 11, INK, False),
        ("· 频率：按交易日与官方发布时间更新；增量更新、缓存去重", 11, INK, False),
        ("· 抓取失败时保留上次有效结果并标记过期，不写零", 11, INK, False),
        ("口径纪律（严格执行）", 12.5, ACCENT, True),
        ("· 国债曲线与地方政府债曲线不混用", 11, INK, False),
        ("· DR（存款类机构）与 FR（全市场）分列展示", 11, INK, False),
        ("· 到期收益率 ≠ 持有期回报；价格变化 ≠ 总回报", 11, INK, False),
        ("验证状态", 12.5, WARN, True),
        ("· 全部为单一权威来源，尚未独立交叉验证", 11, INK, False),
        ("· 纵轴自 0 起，未做截断", 11, INK, False),
    ], spacing=1.22)

    # A3 商业判断 / 情景工具
    s = prs.slides.add_slide(blank)
    page(s, "项目 A ｜ 关键判断与久期情景工具", "第 3 页 / 判断与工具", "A3")
    pic(s, "C03_久期情景分析", 0.62, 1.52, 6.9)
    bullets(s, 7.75, 1.52, 5.0, 5.3, [
        ("判断 1｜收益率中枢两年内持续下移", 12, ACCENT, True),
        (f"10Y 由 {FX['stages'][0]['y10']}%（2024-09-30）降至 {CUR['y10']}%（{CUR['date']}）。"
         f"失效条件：若回升并突破 {FX['stages'][2]['y10']}%（2026-06-30 水平），判断需修正。", 10.5, INK, False),
        ("判断 2｜下行行情里久期保护在减弱", 12, ACCENT, True),
        (f"教学情景（面值 1 亿元、修正久期 5.0、凸性 30）：+100bp → "
         f"{DUR[100]['approx_pct']:+.2f}%（约 {DUR[100]['value_change_cny']:+,.0f} 元）；"
         f"-100bp → {DUR[-100]['approx_pct']:+.2f}%。不对称来自凸性。", 10.5, INK, False),
        ("判断 3｜客户差异在约束，不在观点", 12, ACCENT, True),
        ("沟通重点从「我怎么看」改为「在你的久期上限与回撤容忍下，此情景意味着多少回撤」。", 10.5, INK, False),
        ("工具说明", 11.5, WARN, True),
        ("公式 ΔP/P ≈ -D_mod×Δy + ½C×Δy²；1bp = 0.0001；假设平行移位；"
         "凸性项在 ±25bp 内约占久期效应 6%，±100bp 内升至约 24%。"
         "参数为教学假设，不是任何真实产品。", 10, GREY, False),
    ], spacing=1.2)

    # A4 验证 / 局限 / 复盘
    s = prs.slides.add_slide(blank)
    page(s, "项目 A ｜ 验证结果、局限与复盘", "第 4 页 / 诚实边界", "A4")
    rect(s, 0.62, 1.55, 5.9, 5.2, fill=WHITE, line=LINE)
    bullets(s, 0.85, 1.75, 5.45, 4.9, [
        ("已验证（系统与研究）", 12.5, TEAL, True),
        ("· 5 个来源全部采集成功，程序可重复运行", 11, INK, False),
        ("· 34 项自动检查全部通过（数值非空、单位齐备、版本一致、图表存在）", 11, INK, False),
        ("· 三阶段曲线可重算，关键结论可追溯至来源编号", 11, INK, False),
        ("· 采集失败降级机制已实测（网络代理导致间歇 502 时保留历史结果）", 11, INK, False),
        ("效率实测", 12.5, TEAL, True),
        ("· 首轮建设（含接口勘察与调试）：约 2 小时内完成", 11, INK, False),
        ("· 单次增量更新：采集 + 校验 + 制图 + 导出全流程约 1–2 分钟", 11, INK, False),
        ("· 说明：这是程序流程耗时，不是「节省人力百分比」", 11, GREY, False),
    ], spacing=1.22)
    rect(s, 6.82, 1.55, 5.9, 5.2, fill=RGBColor(0xFB, 0xF0, 0xE9), line=RGBColor(0xEB, 0xD5, 0xC4))
    bullets(s, 7.05, 1.75, 5.45, 4.9, [
        ("未完成（不由 AI 代填）", 12.5, WARN, True),
        ("· 固收基金可比研究：份额、区间、分红、费用与披露滞后数据未取得",
         11, INK, False),
        ("· 公开市场净投放自动解析：需同时核对投放与到期两侧，未可靠解析金额",
         11, INK, False),
        ("· 人工抽查来源原文、手算久期情景比对：待我本人完成", 11, INK, False),
        ("· 真实读者查找任务测试：未测试", 11, INK, False),
        ("复盘：如果重做一次", 12.5, WARN, True),
        ("· 先验证「有没有接口」再决定研究范围，而不是先定范围再找数据"
         "（本轮中债与货币网的接口参数是实测出来的，不是文档给的）", 11, INK, False),
        ("· 基金比较应在一开始就确认数据可得性，避免中途降级", 11, INK, False),
        ("· 久期情景的凸性修正应更早与一阶线性对比，便于向非技术客户解释",
         11, INK, False),
    ], spacing=1.22)

    # ============ 项目 B（4 页）============
    s = prs.slides.add_slide(blank)
    page(s, "项目 B ｜ 英国电动车市场情报与 GTM 执行工作台", "第 1 页 / 背景 · 任务 · 贡献 · 成果", "B1")
    rect(s, 0.62, 1.52, 5.9, 2.5, fill=SOFT)
    bullets(s, 0.85, 1.70, 5.45, 2.2, [
        ("背景与范围锁定", 12.5, ACCENT, True),
        ("一个国家（英国）、一款车型（BYD DOLPHIN SURF，官方定位 The Compact Electric "
         "City Car，官网页续航 200 英里）、3 款直接竞品、一类优先用户、一个验证切口。", 11.5, INK, False),
        ("研究问题", 12.5, ACCENT, True),
        ("官方公开信息是否足以支撑同级别车型的可比判断？如果不能，缺口在哪里、"
         "作为独立研究者能实际补齐什么？", 11.5, INK, False),
    ])
    rect(s, 6.82, 1.52, 5.9, 2.5, fill=WHITE, line=LINE)
    bullets(s, 7.05, 1.70, 5.45, 2.2, [
        ("我承担的任务", 12.5, ACCENT, True),
        ("· 逐一实测各官方来源的可达性，并记录不可达的来源", 11.5, INK, False),
        ("· 搭建 SMMT 官方注册数据的增量采集与基线", 11.5, INK, False),
        ("· 建立竞品基线（仅用官网可核实的字段）", 11.5, INK, False),
        ("· 产出英文落地页、对比表、内容脚本、合作 brief、两周计划", 11.5, INK, False),
        ("· 在合规边界内主动放弃不可靠的做法（如达人数值评分）", 11.5, INK, False),
    ])
    bullets(s, 0.62, 4.25, 12.1, 2.5, [
        ("当前成果（个人研究，非委托项目；无品牌合作、无投放、无订单）", 13, TEAL, True),
        (f"· 市场基线：当月英国新乘用车注册 {q(GX['total_month'])} 辆，纯电 BEV "
         f"{q(GX['bev_month'])} 辆（份额 {GX['powertrain_mix'][0]['share']}%，"
         f"同比 {GX['powertrain_mix'][0]['yoy']:+.1f}%）；年初至今纯电 {q(GX['bev_ytd'])} 辆", 12, INK, False),
        (f"· BYD 品牌：当月 {q(BV['cur'])} 辆（同比 {BV['pct_change']:+.1f}%），"
         f"年初至今 {q(BY['cur'])} 辆（同比 {BY['pct_change']:+.1f}%）——品牌级，非车型级", 12, INK, False),
        (f"· 渠道结构：车队 {GX['channels'][0]['share']}%、私人 {GX['channels'][1]['share']}%、"
         f"公司自用 {GX['channels'][2]['share']}% → 据此提出切口优先级", 12, INK, False),
        ("· 竞品基线：4 款车型的官网续航/电池规格并列展示，并明确标注"
         "「口径未对齐前不得排名」", 12, INK, False),
    ], spacing=1.28)

    # B2 数据 / 方法 / 看板
    s = prs.slides.add_slide(blank)
    page(s, "项目 B ｜ 数据、方法及关键看板", "第 2 页 / 市场结构", "B2")
    pic(s, "C05_英国动力类型结构", 0.62, 1.50, 6.2)
    pic(s, "C06_英国渠道结构", 7.05, 1.50, 5.7)
    bullets(s, 0.62, 4.55, 12.1, 2.3, [
        ("数据与口径纪律", 12.5, ACCENT, True),
        ("· 来源：SMMT（英国汽车制造商与贸易商协会）免费公开页，来源编号 S-SM-01 / S-SM-02；"
         "品牌官网 S-BY-01 / S-RN-01 / S-MG-01 / S-DC-01", 11, INK, False),
        ("· 严格区分：注册量 ≠ 销量 ≠ 交付量；品牌级 ≠ 车型级；纯电 ≠ 插混；英国 ≠ 大不列颠", 11, INK, False),
        ("· 已知限制：SMMT 免费页仅公开车型 Top10（当月 BEV 榜中仅 Renault 5 出现，736 辆），"
         "另两款竞品无可公开核实的车型级注册量；BYD 官网价格与 PCP 月供为前端动态渲染，未获取", 11, INK, False),
        ("· 来源可达性实测记录：Vauxhall 与 Citroën 英国站点分别连接失败与返回 403，"
         "因此在竞品选择<b>之前</b>被排除，不是因为不利而排除", 11, GREY, False),
    ], spacing=1.2)

    # B3 商业判断 / 执行材料
    s = prs.slides.add_slide(blank)
    page(s, "项目 B ｜ 商业判断与执行材料", "第 3 页 / 判断与行动", "B3")
    pic(s, "C07_BYD品牌注册量", 0.62, 1.50, 6.2)
    bullets(s, 7.15, 1.50, 5.6, 5.3, [
        ("关键判断｜切口应优先放在车队/公司车决策链", 12, ACCENT, True),
        (f"当月英国新乘用车注册中车队占 {GX['channels'][0]['share']}%、"
         f"私人占 {GX['channels'][1]['share']}%。对一款低单价城市纯电而言，"
         f"「公司车与车队适配证据」比大规模消费者内容投放更接近可验证的切口。", 10.5, INK, False),
        ("失效条件（必须一起读）", 11.5, WARN, True),
        ("① 若该车型决策实际由私人零售主导，本判断需下调权重；"
         "② 渠道占比是全市场口径，不是纯电细分、更不是该车型自身结构，直接外推属于过度解读；"
         "③ 注册量 ≠ 销量 ≠ 交付量。", 10, GREY, False),
        ("已制作的执行材料", 12, TEAL, True),
        ("· 英文独立研究落地页（显著标注为独立研究，不冒充品牌官方）", 10.5, INK, False),
        ("· 同级别可比表 / 购买清单", 10.5, INK, False),
        ("· 内容脚本（面向车队决策链的沟通过程）", 10.5, INK, False),
        ("· 合作 brief（含必须声明与禁止事项）", 10.5, INK, False),
        ("· 两周执行计划：动作、负责人、依赖、成本假设、衡量方式、停止条件", 10.5, INK, False),
        ("状态：以上均为「提出 / 制作 / 准备验证」，尚未执行，无业务成效数据。", 10, WARN, True),
    ], spacing=1.18)

    # B4 验证 / 局限 / 复盘
    s = prs.slides.add_slide(blank)
    page(s, "项目 B ｜ 验证结果、局限与复盘", "第 4 页 / 诚实边界", "B4")
    rect(s, 0.62, 1.55, 5.9, 5.2, fill=WHITE, line=LINE)
    bullets(s, 0.85, 1.75, 5.45, 4.9, [
        ("已验证", 12.5, TEAL, True),
        ("· SMMT 官方数据采集成功，覆盖动力类型、销售渠道、59 个品牌、车型 Top10", 11, INK, False),
        ("· 4 款车型官网规格已核实并标注来源链接", 11, INK, False),
        ("· 官方来源可达性逐一实测并记录（含不可达来源）", 11, INK, False),
        ("· 站点交互已实测：竞品筛选可用、数据全部由同一份 JSON 注入、无控制台错误", 11, INK, False),
        ("明确未做（不假装做过）", 12.5, WARN, True),
        ("· 未做评论挖掘 → 无主题分布，更不会把提及占比说成消费者比例", 11, INK, False),
        ("· 未做人工标注留出集 → 不宣称任何 AI 分类准确率", 11, INK, False),
        ("· 未做达人数值评分：YouTube API 等平台条款限制衍生商业评估，未核实前不做",
         11, INK, False),
        ("· 未做真实用户测试 → 不引用任何「用户调研结果」", 11, INK, False),
    ], spacing=1.2)
    rect(s, 6.82, 1.55, 5.9, 5.2, fill=SOFT)
    bullets(s, 7.05, 1.75, 5.45, 4.9, [
        ("复盘：如果重做一次", 12.5, ACCENT, True),
        ("· 竞品选择应在采集前完成可达性实测，避免规则与结果互相污染"
         "（本轮已这么做，并保留了不可达记录作为证据）", 11, INK, False),
        ("· 价格是 GTM 对比的核心变量，应在研究设计阶段就决定"
         "「用浏览器渲染采集」还是「明确放弃」；本轮选择明确放弃并留空", 11, INK, False),
        ("· 用户痛点部分应先确认平台内容分析条款，再决定是否投入样本采集——"
         "本轮因未确认而主动放弃，是刻意的取舍", 11, INK, False),
        ("这个项目最能说明我的判断习惯", 12.5, TEAL, True),
        ("先确认「能不能拿到、能不能用、能不能公开」，再决定「做什么」；"
         "拿不到就写清楚拿不到，不用推测值把表格填满。", 11, INK, False),
        ("下一步（我自己做）", 12.5, ACCENT, True),
        ("① 人工复核达人候选的真实公开信息；② 邀请 2–3 位读者完成三项查找任务测试；"
         "③ 人工核对源页面与程序结果的一致性", 11, INK, False),
    ], spacing=1.2)

    # ============ 附录 ============
    s = prs.slides.add_slide(blank)
    page(s, "附录 ｜ 来源登记与口径对照", "可直接照抄进面试材料", "附")
    rows = [("S-CB-01", "中国债券信息网（中债估值中心）— 中债国债收益率曲线", "A", "CN"),
            ("S-CB-02", "中国债券信息网 — 指定工作日收益率曲线（历史复盘）", "A", "CN"),
            ("S-CM-01", "中国货币网 — 银行间质押式回购利率 FR / FDR(DR)", "A", "CN"),
            ("S-CM-02", "中国货币网 — Shibor", "A", "CN"),
            ("S-PB-01", "中国人民银行 — 公开市场业务交易公告", "A", "CN"),
            ("S-SM-01", "SMMT — 英国乘用车注册（动力类型/渠道/车型Top10）", "B", "UK"),
            ("S-SM-02", "SMMT — 品牌级注册量", "B", "UK"),
            ("S-BY-01", "BYD UK 官网 — DOLPHIN SURF 车型页", "A", "UK"),
            ("S-BY-02", "BYD UK 官网 — PCP 金融方案页（价格未获取）", "A", "UK"),
            ("S-RN-01", "Renault UK 官网 — 5 E-Tech electric", "A", "UK"),
            ("S-MG-01", "MG Motor UK 官网 — MG4 EV", "A", "UK"),
            ("S-DC-01", "Dacia UK 官网 — Spring Electric", "A", "UK")]
    t = s.shapes.add_table(len(rows) + 1, 4, Inches(0.62), Inches(1.5),
                           Inches(7.4), Inches(5.2)).table
    for i, w in enumerate((1.05, 4.75, 0.7, 0.9)):
        t.columns[i].width = Inches(w)
    hdr = ["编号", "来源", "权威性", "地区"]
    for j, htxt in enumerate(hdr):
        c = t.cell(0, j)
        c.text = htxt
        for p in c.text_frame.paragraphs:
            for r in p.runs:
                set_font(r, 10, True, WHITE)
        c.fill.solid()
        c.fill.fore_color.rgb = ACCENT
    for i, row in enumerate(rows, start=1):
        for j, v in enumerate(row):
            c = t.cell(i, j)
            c.text = v
            for p in c.text_frame.paragraphs:
                for r in p.runs:
                    set_font(r, 9.5, False, INK)
            c.fill.solid()
            c.fill.fore_color.rgb = WHITE if i % 2 else SOFT
    bullets(s, 8.25, 1.5, 4.5, 5.2, [
        ("口径对照（最常被追问）", 12, ACCENT, True),
        ("· 期限 ≠ 久期", 10.5, INK, False),
        ("· 到期收益率 ≠ 持有期回报", 10.5, INK, False),
        ("· 价格变化 ≠ 总回报", 10.5, INK, False),
        ("· 注册量 ≠ 销量 ≠ 交付量", 10.5, INK, False),
        ("· 品牌级 ≠ 车型级", 10.5, INK, False),
        ("· DR(存款类机构) ≠ FR(全市场)", 10.5, INK, False),
        ("· 国债曲线 ≠ 地方政府债曲线", 10.5, INK, False),
        ("· 英国(UK) ≠ 大不列颠", 10.5, INK, False),
        ("· 相关性 ≠ 因果", 10.5, INK, False),
        ("", 8, INK, False),
        ("全部来源均为 A 级原始披露或 B 级行业机构，"
         "无 C 级二手来源作为结论依据；均标注为「单一权威来源，尚未独立交叉验证」。",
         10, GREY, False),
    ], spacing=1.22)

    out = SLIDES / f"刘柏廷_作品集_两个项目模块_{DV}.pptx"
    prs.save(str(out))
    log_line(f"PPTX 已生成：{out.relative_to(ROOT)}（{len(prs.slides.__iter__.__self__._sldIdLst)} 页）")
    return out


if __name__ == "__main__":
    build_pptx()
