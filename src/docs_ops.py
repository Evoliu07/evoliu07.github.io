"""生成 GTM 英文执行材料 + operations/ + START_HERE + checks/ 文档。"""
from __future__ import annotations

import json
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
DV, GEN = M["meta"]["data_version"], M["meta"]["generated_at"]
BVv = M["meta"]["build_version"]
F: dict[str, str] = {}

# ============================================================ GTM EN materials
F["research/gtm/06_comparison_table_en.md"] = f"""# UK Compact EV — Comparable Facts Sheet

Data version {DV}. Generated {GEN}.

> **INDEPENDENT RESEARCH — NOT AFFILIATED WITH ANY BRAND.**
> This sheet is produced by an independent researcher. It is not a brand publication,
> not an advertisement, and not an offer or recommendation to purchase.
> All figures are reproduced from the manufacturers' own UK websites on the retrieval date.
> **Testing cycles may differ between brands; figures must not be ranked against each other
> until the underlying test procedures are aligned.**

## What this sheet is for

Official UK information about compact EVs is published, but it is **not comparable**:
ranges are quoted under different test regimes, battery figures use different
pack/nominal conventions, and pricing is loaded dynamically on several brand sites.
This sheet records only what could be verified from each brand's own UK website,
and marks everything else as **not retrieved** rather than estimating it.

## Vehicle comparison (verified fields only)

| Model | Role | Official range (miles) | Battery (kWh) | Official source | Retrieval |
|---|---|---|---|---|---|
{chr(10).join(
    "| " + c['model'] + " | " + ("Subject of study" if c['is_subject'] else "Direct competitor") + " | "
    + (" / ".join(c['range_miles']) if c['range_miles'] else "**not retrieved**") + " | "
    + (" / ".join(c['battery_kwh']) if c['battery_kwh'] else "**not retrieved**") + " | "
    + f"[{c['source_url'].split('/')[2]}]({c['source_url']})" + " | "
    + ("verified" if c['retrieved_ok'] else "**failed**") + " |" for c in CMP)}

## Deliberately excluded

| Field | Status | Why |
|---|---|---|
| On-the-road price / PCP monthly payment | Not retrieved | Loaded client-side on the brand site; not obtainable from the static page |
| Deposit, term, balloon payment, APR | Not retrieved | Finance figures are only meaningful together with these conditions |
| Model-level registration volume | Restricted | SMMT's free public data covers only the top 10 models |
| Promotional validity dates | Not retrieved | Requires manual reading of campaign pages |

**We do not estimate these.** A figure without a source is worse than a blank cell,
because it looks precise while being unverifiable.

## UK market context (SMMT, official)

| Metric | Value | Unit | Period |
|---|---|---|---|
| New car registrations, all powertrains | {GX['total_month']:,.0f} | units | latest month |
| Battery electric (BEV) registrations | {GX['bev_month']:,.0f} | units | latest month |
| BEV share of market | {PM[0]['share']}% | % | latest month |
| BEV year-on-year change | {PM[0]['yoy']:+.1f}% | % | latest month |
| BEV registrations, year to date | {GX['bev_ytd']:,.0f} | units | year to date |

**Registration ≠ sale ≠ delivery.** SMMT counts new car *registrations*.

## Channel structure (the most informative cut for fleet buyers)

| Channel | Units | Share | Prior-year share | YoY |
|---|---|---|---|---|
{chr(10).join(f"| {c['label']} | {c['units']:,.0f} | {c['share']}% | {c['share_prev']}% | {c['yoy']:+.1f}% |" for c in CH)}

Denominator: **all** new car registrations in the UK in the latest month —
**not** the BEV segment, and **not** any single model.

## Source register

| ID | Source | Type | Region |
|---|---|---|---|
{chr(10).join(f"| `{k}` | {v['name']} | {'Official / primary' if v['authority']=='A' else 'Industry body'} | {v['region']} |" for k, v in SOURCES.items())}

All sources are single authoritative sources and have **not** been independently
cross-validated. Same-origin republication does not count as independent verification.

## Update policy

Financial and registration data update on release; competitor pages are checked daily.
If a source is unreachable, the previous verified value is retained and flagged as stale —
the sheet never writes a zero or silently substitutes an old value for a new one.
"""

F["research/gtm/07_content_script_en.md"] = f"""# Content Script — Fleet Decision-Maker Track

Data version {DV}. **Draft only — nothing has been published or filmed.**

> **INDEPENDENT RESEARCH — NOT AFFILIATED WITH ANY BRAND.**
> Any published version must carry this disclosure, visibly, above the fold.

## Audience and job-to-be-done

- **Primary audience:** UK fleet managers and company-car scheme administrators
  evaluating a small, low-cost EV for urban and pool-car duty.
- **Job to be done:** build a defensible shortlist comparison that can be taken
  into an internal procurement review.
- **The blocker we address:** official specs exist but are not directly comparable,
  so comparing options costs more time than a fleet manager has.

## Format

Two short pieces (60–90 seconds each). No vehicle footage is required —
both are screen-led, so they can be produced without brand assets or permissions.

---

## Piece 1 — "The comparison problem" (75 seconds)

| Time | Visual | Voiceover |
|---|---|---|
| 0:00–0:08 | Title card: "Comparing small EVs in the UK — why it's harder than it should be" | "Comparing small electric cars in the UK looks straightforward. It isn't." |
| 0:08–0:25 | Screen recording of two official brand pages, range figures highlighted | "This is the official range figure for one car. And here is another brand's official figure. Both are 'official'. Neither is measured the same way." |
| 0:25–0:45 | Custom graphic: the four comparison axes (range testing cycle, battery convention, price basis, finance conditions) | "There are four things you have to align before any comparison means anything: the range test cycle, the battery convention, the price basis — on-the-road or not — and the finance conditions." |
| 0:45–1:05 | Comparable facts sheet on screen, with the "not retrieved" column visible | "So instead of ranking them, I built a sheet that only records what each brand actually publishes — and leaves a blank where nothing could be verified. Including the price, which several brands load dynamically." |
| 1:05–1:15 | End card with source register | "Every figure links to its source. Where there's no source, there's no figure. Independent research — not affiliated with any brand." |

## Piece 2 — "The fleet cost angle" (60 seconds)

| Time | Visual | Voiceover |
|---|---|---|
| 0:00–0:10 | UK channel-split chart (fleet {CH[0]['share']}% vs private {CH[1]['share']}%) | "Most new car registrations in the UK are fleet, not private: {CH[0]['share']} percent versus {CH[1]['share']} percent." |
| 0:10–0:30 | Highlight on the fleet bar | "That matters because a fleet decision is a cost-per-month decision, and the levers are different: benefit-in-kind treatment, salary sacrifice structuring, and whole-life cost — not sticker price." |
| 0:30–0:50 | Screen recording of the finance-conditions checklist | "Which is exactly why finance figures should never be quoted alone. A monthly payment without the deposit, the term and the balloon payment tells you almost nothing." |
| 0:50–1:00 | End card | "Registration data: SMMT. Independent research — not affiliated with any brand. Nothing here is a recommendation to buy." |

---

## Mandatory disclosures (every published version)

- "Independent research — not affiliated with, endorsed by, or acting for any brand."
- "Figures are reproduced from manufacturers' official UK websites on the stated date."
- "Test cycles may differ between brands; figures are not ranked."
- "Registration data © SMMT. Registration is not a measure of sales or deliveries."
- Campaign disclosure if any commercial arrangement ever exists:
  "This content was produced independently. [Sponsor relationship, if any, disclosed here.]"

## Hard limits

- No brand logos presented as official endorsement.
- No vehicle footage or photography without a clear licence.
- No implied test-drive booking or purchase facility.
- No statement about sales impact, conversion, or cost-per-lead — none has been measured.
"""

F["research/gtm/08_partnership_brief_en.md"] = f"""# Creator Collaboration Brief (Template)

Data version {DV}. **Template only. No creator has been contacted. No agreement exists.**

> **INDEPENDENT RESEARCH — NOT AFFILIATED WITH ANY BRAND.**

## Purpose

Help a UK-facing creator produce an accurate, useful video for people comparing
small electric cars, without overstating what the available information supports.

## About the project

An independent research project comparing official, publicly available UK information
on compact electric cars. The output is a comparable facts sheet and a one-page
explainer. **It is not a brand campaign.**

## What we are asking for

- **Format:** one long-form video (8–15 minutes) or one short-form series (3–5 pieces).
- **Angle:** "how to compare small EVs in the UK without being misled by the spec sheet".
- **Must include:** the four comparison axes (test cycle, battery convention,
  price basis, finance conditions), and at least one worked example.
- **Must not include:** any claim about sales, market share shifts, or cost-per-lead;
  any implication that the project is brand-affiliated; unpublished price figures.

## What the creator must disclose

- Any commercial relationship, clearly and in the first 30 seconds
  (e.g. "paid partnership", "gifted", "sponsored" as applicable).
- Any previously published partnership with the brands discussed, where platform
  rules or local advertising rules require it.

## What we provide

- The comparable facts sheet, with source links for every figure.
- A source register so claims can be checked.
- Key framing notes (in plain language) on what the data does and does not support.

## What we do **not** provide

- Brand assets, logos for official use, footage, or press materials we do not hold rights to.
- Any "brand-approved" script or talking points.
- Any statement that has not been sourced.

## Commercial terms

**Not applicable in this document.** No rates, budgets, or terms are set here,
because no creator has been contacted and no quotes have been obtained.
Any future terms must be agreed explicitly and in writing.

## Audience and geo notes

Audience geography, prior performance, and conversion data are **unknown** to us and
are therefore not used for selection or for predicting outcomes.
Selection is based on publicly visible content themes and UK region signals only.

## Compliance boundaries

- No impersonation of any brand's official channel.
- No collection of sales leads on behalf of any brand.
- No claim of "official partner" status.
- No purchased engagement of any kind.
"""

# ============================================================ START_HERE
F["START_HERE.md"] = f"""# 从这份压缩包开始读什么

**这个包里有 8 个目录。你只需要按下面的顺序看，5 分钟就能把这个项目讲清楚。**

数据版本 **{DV}**　生成时间 {GEN}　构建版本 {BVv}

---

## 一、先看这 4 个文件（按顺序）

| 顺序 | 文件 | 你需要从中知道什么 |
|---|---|---|
| 1 | `slides/刘柏廷_作品集_两个项目模块_{DV}.pptx` | 两个项目各 4 页，可直接插进你现有作品集 |
| 2 | `print/刘柏廷_作品集_打印版_{DV}.pdf` | 14 页完整纸质版，面试时打印带去 |
| 3 | `exports/dashboards/DASHBOARD_16x9.png` | 一张图看懂两个项目（可直接放进 PPT 封面） |
| 4 | `interview/00_START_HERE_interview.md` | 面试怎么讲、哪些话不能说 |

---

## 二、两个项目一句话是什么

**项目 A｜AI 固收市场观察与机构客户沟通研究**
用中债、中国货币网、央行的官方公开数据搭日频管道，把收益率曲线和资金面做成可复核的基线，
再用修正久期情景把「风险」翻译成客户能看懂的流失金额（当前 10Y = {CUR['y10']}%，
教学情景 +100bp ≈ {DUR[100]['approx_pct']:+.2f}%）。

**项目 B｜英国电动车市场情报与 GTM 执行工作台**
锁定一个国家（英国）、一款车（BYD DOLPHIN SURF）、三款竞品、一类用户、一个切口。
用 SMMT 官方数据建基线（当月纯电 {GX['bev_month']:,.0f} 辆、份额 {PM[0]['share']}%），
发现车队渠道占 {CH[0]['share']}%、私人占 {CH[1]['share']}%，据此提出优先做车队/公司车切口，
并完成英文落地页、对比表、内容脚本、合作 brief 与两周计划。

---

## 三、每个目录里是什么

| 目录 | 里面有什么 | 适合公开吗 |
|---|---|---|
| `github-upload/` | **给 GitHub Pages 用的网站**（含必要代码、公开数据、部署配置） | ✅ **只把这个目录公开** |
| `slides/` | 两个项目的可编辑 PPTX（16:9，与你的现有作品集比例一致） | ⚠️ 可公开，但建议先看一遍 |
| `print/` | 14 页打印版 PDF + 生成它的 HTML | ⚠️ 可公开 |
| `exports/` | `dashboards/` 看板整图、`charts/` 单图 PNG+SVG、`photos/` 证书与证件照素材 | ⚠️ photos 内含证书和个人照片，**公开前先确认** |
| `research/` | 研究方法、来源、口径、客户沟通材料、GTM 执行材料（含英文） | ⚠️ 含方法与来源，可公开；不含受限原始材料 |
| `interview/` | 简历表述、口述稿、STAR、20 道追问、贡献表、自检清单 | ❌ **仅自己使用** |
| `operations/` | 运行、额度、日期、监测、暂停、补跑、导出说明 | ❌ **仅自己使用** |
| `checks/` | 实际验收结果、版本清单、已知限制、截图 | ❌ **仅自己使用** |

> **不要把这整个压缩包无差别公开。** 只公开 `github-upload/`。
> 其余目录含有面谈材料、运行配置和你的个人素材。

---

## 四、网站怎么部署（3 步）

1. 解压后，把 **`github-upload/` 目录里的全部内容**（不是这个目录本身）
   上传到你的 GitHub 仓库根目录。
   - 注意：`site/` 里的文件要保持目录结构；`.nojekyll` 这类隐藏文件要一起上传。
2. 仓库 Settings → Pages → Source 选 `Deploy from a branch`，
   Branch 选 `main`、目录选 `/ (root)`，保存。
3. 等 1–2 分钟，访问 `https://<你的用户名>.github.io/<仓库名>/`
   - 检查首页两张项目卡片上的数字是否正常显示（不是「…」）。
   - 点开「固收研究」和「英国出海 GTM」，检查图表是否加载。
   - 用手机打开一次，确认布局正常。

**如果数字显示成「…」**：说明 `data/market.json` 没上传成功，
或你是用 `file://` 双击打开的（浏览器会拦截 `fetch`）。必须通过 HTTP 访问。

### 自动更新（可选）

`operations/RUN_CONFIG.md` 里有定时任务的配置。
定时任务只更新 `github-upload/data/market.json` 与 `exports/`，
更新后重新提交到仓库即可（网站会随后更新；已冻结的面试版不会被覆盖）。

---

## 五、你必须自己做的事（我没有代做）

清单在 `interview/07_self_check_list.md`。最关键的四件：

1. **抽查数据来源原文**（打开中债、SMMT 页面核对数字）
2. **手算一次久期情景**，和程序结果比对
3. **在 PowerPoint / WPS 里打开 PPTX 逐页看一遍**
   —— 本机没有 PowerPoint/LibreOffice，PPTX 只做了结构检查（18 项通过，含文字溢出测算），
   **没有原生渲染成图片逐页目检**
4. **在真实打印机上试打一次 PDF** —— 屏幕检查通过，纸面实打未确认

---

## 六、需要你补的信息（我会填进去）

以下字段目前标为「待确认」，网站公开版会自动隐藏。你确认后我补入，**不编造**：

- [ ] 邮箱 / 手机号（是否放进公开网页？建议**不放**，只放在投递版简历）
- [ ] 学位与专业全称、预计毕业时间
- [ ] GitHub 用户名 / 仓库名（部署网站要用）
- [ ] 证件照是否允许公开（当前 `exports/photos/` 里只有素材，未嵌入网站）
- [ ] 实习描述里那几个百分比的口径：
      京东「30% / 20%」、诺安「15%」、国学社「35%」、志愿者「40%」
- [ ] 是否保留「意向规模约 8,000 万元」这类意向口径表述

---

## 七、一句话说明这份材料的边界

这是**个人研究项目**，不是实习成果、不是委托项目。
没有品牌合作、没有投放、没有达人合作、没有客户、没有订单。
所有来源都是单一权威来源（政府 / 行业机构 / 品牌官网），**尚未独立交叉验证**。
未获取的数据一律留空并注明，**不推测、不填零**。
"""

# ============================================================ operations
ROWS = [
    ("任务名称", "portfolio-daily-refresh", "网站与看板的数据刷新"),
    ("运行位置", "本机 macOS（用户名 evo）", "本机文件系统可直接读写项目目录"),
    ("工作目录", str(ROOT), "所有相对路径的基准"),
    ("执行程序", "src/finance_fetch.py → src/gtm_fetch.py → src/build_all.py", "纯程序，不调用模型"),
    ("模型", "无（采集、校验、计算、制图环节均不调用模型）", "AI 仅用于协调与必要解读"),
    ("频率", "每天 1 次，北京时间 24:00（即次日 00:00）", "非交易日只更新检查状态，不写伪新数据"),
    ("时区", "Asia/Shanghai（UTC+8）", "所有时间戳以此为基准"),
    ("生效时间", "2026-09-11（首次建立）", "—"),
    ("停止条件", "我手动暂停；或连续 7 天全部来源失败；或平台额度耗尽", "任务无计划结束日"),
    ("下一次运行", "由自动化任务调度（见下方任务标识）", "—"),
    ("最近成功运行", "见 data/run.log 末次记录", "—"),
    ("失败原因", "见 data/run.log 的 [STALE]/[FAIL] 行", "失败不影响已发布内容"),
]

F["operations/RUN_CONFIG.md"] = f"""# 运行配置（Run Configuration）

数据版本 {DV}　最后更新 {GEN}

## 1. 任务配置

| 字段 | 取值 | 说明 |
|---|---|---|
{chr(10).join(f"| {a} | {b} | {c} |" for a, b, c in ROWS)}

## 2. 额度与日期管理（**分别管理，不能混为一谈**）

| 项 | 内容 | 状态 |
|---|---|---|
| 1. 免费权益到期日 | WorkBuddy 免费权益 / 试用额度到期日 | **未确认** |
| 2. 账户额度重置日 | 账户 token 额度的重置周期与日期 | **未确认** |
| 3. 任务计划结束日 | 本任务**无计划结束日**，按持续更新设计 | 持续 |
| 4. 各数据指标的有效日期 | 见 `market.json` 每条记录的 `period` 字段 | 已记录 |
| 5. 获取及验证时间 | 见每条记录的 `retrieved` 与 `verified` 字段 | 已记录 |
| 6. 分析报告信息截止时间 | 见 `checks/VERSION_MANIFEST.md` | 已记录 |
| 7. 网站构建与发布版本 | `{BVv}` / 数据版本 {DV} | 已记录 |
| 8. PPT / PDF 快照版本 | `slides/` 与 `print/` 中的文件名为快照版本 | 已冻结 |

> **不确定的日期一律标记「未确认」，不猜测。**
> **「任务没有计划结束日」不等于「服务保证永久可用」** ——
> 平台策略、免费额度或接口可用性变化都可能导致停止。
>
> **关于费用估计**：如果只能看到账户总量，那么账户用量差值可能混入其他任务的消耗，
> **不能当作本任务的单次精确成本**。任何费用数字都须标注为估计。

## 3. 更新频率（按数据发布节奏，而不是统一每日）

| 数据 | 频率 | 理由 |
|---|---|---|
| 国债收益率曲线、回购利率、Shibor | 按交易日 | 跟随官方发布节奏 |
| 央行公开市场公告 | 按公告 | 有公告才更新 |
| SMMT 注册数据 | 随发布（通常月度） | 月度发布，不是日频 |
| 竞品官网页面 | 每日检查 | 价格/规格可能随时改 |
| 用户材料、达人名单 | 按周或有新证据时 | 变化慢，避免无意义抓取 |

## 4. 自动化状态（诚实说明）

| 项 | 状态 |
|---|---|
| 手动跑通 | ✅ 已完成（`src/finance_fetch.py`、`src/gtm_fetch.py`、`src/build_all.py` 均已实跑） |
| 真实定时触发验证 | ✅ 已配置自动化任务；**以实际触发一次并拿到执行证据为准** |
| 任务标识 | 见 WorkBuddy 自动化列表中的 `portfolio-daily-refresh` |
| 运行状态监控 | `data/run.log`（追加写入）；状态文件在 `data/state/*.json` |

> **口径纪律**：只有拿到任务标识、运行状态与执行证据后，才能对外宣称「自动化已生效」。
> 仅「配置了任务」不等于「验证过能跑」。
> 另外：**AI 自动任务启动程序本身也会消耗额度**，不能宣称绝对零 token。

## 5. 只在这些情况提醒

- 有**重要变化**（例如某指标出现结构性变化、曲线形态切换）
- **运行失败**（来源不可达、解析失败）
- **额度不足**
- **需要我处理**（例如需要人工核实某项数据）

**不重复推送无变化状态。** 无变化时只写一行检查记录，不发通知。

## 6. 状态文件说明

| 文件 | 内容 |
|---|---|
| `data/state/fin_*.json` | 固收各来源最近成功结果 + stale 标记 + 上次错误 |
| `data/state/gtm_*.json` | SMMT 与车型事实的最近成功结果 |
| `data/run.log` | 追加式运行日志（含 `[OK]` / `[STALE]` / `[FAIL]` / `[MISS]` / `[RETRY]`） |
| `data/processed/*.json` | 当前数据版本的结构化输出 |
"""

F["operations/DAILY_UPDATE.md"] = f"""# 日常更新指令（简短版）

> **用途**：这是给「每日自动任务」用的**短指令**。
> 它只读取必要规则、新增数据和相关上下文，**不重新读整份建设提示词与全部历史材料**。

---

## 指令正文（复制这段给自动任务）

```
你负责刷新 portfolio-delivery 项目的数据。

工作目录：{ROOT}

按顺序执行：
1. python src/finance_fetch.py
2. python src/gtm_fetch.py
3. python src/build_all.py

然后判断：
- 如果三步都成功，且关键指标与上一版本相比没有重要变化 →
  只在 data/run.log 追加一行「无变化」，不生成报告，不发通知，直接结束。
- 如果某一步失败 →
  不要覆盖已发布内容；确认 data/state/ 中是否保留了上次有效结果；
  在 data/run.log 记录失败原因；如果有来源失败，向我报告一条简短说明。
- 如果关键指标出现重要变化（例如收益率曲线形态切换、注册量份额显著变动）→
  生成一段简短摘要（不超过 200 字），必须区分「事实」与「我的解释」，
  并引用数据集编号（D-xx）与来源编号（S-xx）。

禁止事项：
- 不得调用任何收费 API 或模型接口来完成采集与计算。
- 不得在没有人工复核的情况下生成新的研究结论。
- 不得为了让页面看起来更新而修改 data/version 或 generated_at。
- 不得把失败状态改写成成功状态。
```

---

## 三条纪律

1. **无变化保持安静。** 每天发一条「今天没变化」是噪音，不是勤奋。
2. **失败不降级成零。** 失败就保留旧值并标记过期；页面继续用旧值显示，同时标注状态。
3. **模型解读只在必要时触发。** 采集、清洗、校验、计算、制图**不调用模型**；
   只有出现重要变化需要写摘要时才用，且摘要必须标注为「AI 研究草稿，待人工复核」。

## 时间与顺序

- 触发时间：北京时间 24:00（次日 00:00）。
- 选择这个时间的原因：当日金融数据已发布完毕，避免抓到不全的当日数据。
- 若当日为非交易日，程序会记录「无新增数据」，不写入伪新值。
"""

F["operations/WEEKLY_REVIEW.md"] = f"""# 周度复盘指令（简短版）

> 用途：每周一次，检查**数据质量、来源健康度与运行稳定性**，
> 而不是重复跑一遍日报。

## 指令正文

```
对 portfolio-delivery 项目做一次周度复盘，只输出以下五项，每项不超过 5 行：

1. 来源健康度
   读取 data/run.log，统计本周各来源的 [OK] / [STALE] / [FAIL] 次数。
   列出出现过 FAIL 的来源编号与原因。

2. 数据新鲜度
   检查 market.json 每条记录的 period，列出「期间早于 7 天前」的记录编号。
   不要修改它们，只列出。

3. 校验结果
   检查 checks/validation.json 的 failed 数量。若大于 0，列出未通过项。

4. 待人工事项
   检查 interview/07_self_check_list.md 中仍未勾选的项目，列出前 3 项。

5. 需要我决定的事
   如果有任何需要我做的判断（例如某来源连续失败是否要换源、
   某指标口径是否要调整），单独列出，不要替我决定。

禁止：
- 不要生成新的研究结论。
- 不要在未复核的情况下把 checks/ 里的「待完成」改成「已完成」。
```

## 月度额外动作

- 把超过 30 天的日志按主题摘要归档。
- 检查是否有来源页面结构变化导致解析失败（对照 `data/raw/` 的最近抓取）。
- 更新 `checks/VERSION_MANIFEST.md` 的版本清单。
"""

F["operations/EXPORT.md"] = f"""# 导出指令（面试版冻结）

数据版本 {DV}。

> **核心原则**：从一个**固定的数据快照**导出全部格式。
> 网站可以持续更新，**面试版必须可冻结**；冻结后不被日常更新覆盖。

## 三种导出

### 1. 完整看板截图（保留当前日期与筛选状态）

```
python src/build_all.py
```
产出：
- `exports/dashboards/DASHBOARD_16x9.png` —— 3840×2160（16:9 展示页 @300ppi）
- `exports/dashboards/DASHBOARD_16x9.svg` —— 矢量版
- `exports/dashboards/DASHBOARD_A4_portrait.png` —— 2480×3507（A4 @300ppi）
- `exports/dashboards/DASHBOARD_A4_portrait.pdf` —— 矢量打印版

### 2. 单图导出（自由插入现有 PPT）

产出在 `exports/charts/`：9 张图，每张同时给 **PNG（@300ppi）** 与 **SVG（矢量）**。
建议插入 PPT 时用 PNG（PowerPoint 对 SVG 的编辑支持有限，但缩放用 SVG 更清晰）。

### 3. 专门重排的项目展示页（适合纸质阅读）

```
python src/make_ppt.py      # 生成可编辑 PPTX（16:9）
python src/make_print.py    # 生成 A4 打印版 PDF（14 页）
```

**纸面自足要求**：打印版不依赖点击、悬停或扫码。
每张图与每个项目页都包含：标题、图表或证据、简短解读、单位、数据区间、
来源编号、版本日期、必要的局限与复核状态。

## 导出清单（每次导出必填）

| 字段 | 本次取值 |
|---|---|
| 版本编号 | {DV} / 构建 {BVv} |
| 数据快照 | `data/processed/*.json` + `github-upload/data/market.json` |
| 导出时间 | {GEN} |
| 每张图的来源编号 | 见 `market.json` → `charts[].sources` |
| 筛选参数 | 无（未使用筛选状态导出） |
| 图注 | 见各图 figcaption 与 `market.json` → `charts[]` |
| 对应报告 | `print/`、`slides/` |
| 使用限制 | 个人研究；非委托；不代表任何机构；教学情景非真实产品 |

## 命名规则

`<项目>_<内容>_<版本日期>.<扩展名>`
例：`刘柏廷_作品集_打印版_{DV}.pdf`

## 冻结规则

1. 面试版导出后，把 `slides/`、`print/`、`exports/` 复制到
   `archive/<版本日期>/` 作为冻结副本。
2. 后续日常更新**只更新** `github-upload/`，**不覆盖** `archive/`。
3. 网站展示「当前版本」；打印材料显示「本次面试版」。
4. 历史快照仅在来源允许保存的范围内保留；有保存期限或删除要求的数据按规则处理，
   并在 `checks/KNOWN_LIMITATIONS.md` 中说明对复现的影响。

## 导出前检查（必须逐项做）

- [ ] `python src/build_all.py` 无报错，`checks/validation.json` failed = 0
- [ ] 网站、图片、PPT、PDF 使用同一 `data_version`
- [ ] 图片分辨率检查（PNG 头部读取，不只看 DPI 标签）
- [ ] 打印版逐页溢出检查（`checks/verify_print.mjs`）
- [ ] PPTX 结构检查（`checks/verify_pptx.py`）
- [ ] 中文显示、缺字、裁切、溢出、灰度可辨性
- [ ] **未做过的检查不得标记为通过**
"""

F["operations/OPERATION_MANUAL.md"] = f"""# 运行手册：暂停、补跑、故障处理

数据版本 {DV}。

## 1. 暂停任务

- 在 WorkBuddy 自动化列表中把 `portfolio-daily-refresh` 状态改为 **PAUSED**。
- 暂停期间网站继续正常访问（用的是上一次成功的数据版本）。
- **不要删除** `.workbuddy/` 目录 —— 它保存任务配置与状态。

## 2. 恢复任务

把状态改回 ACTIVE。恢复后建议先手动跑一次：
```
cd {ROOT}
python src/finance_fetch.py
python src/gtm_fetch.py
python src/build_all.py
```

## 3. 补跑（错过计划时间）

直接手动执行上面的三步即可。程序是**增量**的：
- 只会请求自上次成功运行以来的新数据（缓存命中则不重复请求）
- 已有状态文件的情况下不会重复写盘
- 若想强制全量重建：`python src/finance_fetch.py --full`

## 4. 常见故障与处理

| 症状 | 原因 | 处理 |
|---|---|---|
| `[FAIL]` 且无历史结果 | 首次运行即失败，或状态文件被删 | 检查网络/代理；重跑一次 |
| `[STALE]` 出现 | 本次抓取失败，已保留上次有效结果 | 无需处理；连续 3 天出现再排查 |
| 502 Bad Gateway | 本机代理（127.0.0.1:64265）拦截 | 程序已有 curl 回退通道；也可临时 `unset HTTP_PROXY` |
| SMMT 解析到 0 张表 | 页面结构改版 | 检查 `data/raw/smmt_*.html`，更新 `src/gtm_fetch.py` 的解析逻辑 |
| 中债曲线为空 | 当日为非工作日，或接口参数变化 | 程序会自动使用最近工作日；参数变化需重新勘察页面请求 |
| 网站数字显示「…」 | `market.json` 未上传，或用 `file://` 打开 | 通过 HTTP 访问；确认 `site/data/market.json` 已上传 |
| PDF 缺字 / 方框 | 中文字体未嵌入 | 确认 `make_print.py` 用的是 Chrome 打印路径（会自动嵌入字体） |
| PPT 中文变方框 | 演示电脑缺少 `PingFang SC` | 在目标机器上把字体改为「微软雅黑」或把标题文字转换为图片 |

## 5. 想改研究范围时

研究范围是**刻意锁死**的（一国、一车、三竞品、一类用户、一个切口）。
如果确实要扩展：

1. 先做数据可得性验证（能不能拿到、能不能用、能不能公开）；
2. 把新范围写进 `research/` 下的方法文档，并说明**为什么**要扩；
3. 更新 `src/common.py` 的 SOURCES 登记表；
4. 重新跑一次全量：`python src/finance_fetch.py --full` 与 `python src/gtm_fetch.py --full`；
5. 更新 `checks/KNOWN_LIMITATIONS.md`。

**不要为了「看起来更完整」而加国家、车型或指标。**
每加一个都要能说明它解决了什么具体问题。

## 6. 数据保存期限

- 原始响应保存在 `data/raw/`，当前保留策略：不主动清理，但仅用于复现与排错。
- 若某来源条款要求限期删除，在 `checks/KNOWN_LIMITATIONS.md` 记录并执行删除，
  同时说明对复现的影响。
- 公开目录（`github-upload/`）**不包含**原始抓取页面，只包含派生数值与自制图表。
"""
for rel, content in F.items():
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    log_line(f"  写入 {rel}（{len(content)} 字符）")
