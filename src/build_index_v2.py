"""
生成 evo-site/index.html —— 个人主页（多视图）

改动要点：
  导航五项「经历 / 项目 / 证书 / 数据 / 看板」置于第一行并水平居中；首页 = 点左上角姓名
  教育板块改称「教育经历」，澳门科技大学时间改 2021年9月 – 2025年6月
  荣誉只保留「商学院院长优秀毕业生」
  实习经历 6 段，按给定文案
  证书只显示 名称 / 颁发方 / 时间
用法： python src/build_index_v2.py
"""
from __future__ import annotations

import base64
import io
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, log_line                                    # noqa: E402
from PIL import Image                                                # noqa: E402

IMG = json.loads((ROOT / "build" / "images.json").read_text(encoding="utf-8"))
CUST = Path("/Users/evo/WorkBuddy/2026-09-11-23-22-58/_incoming/experiences/"
            "customer-prioritization.html")
LAIFEN = Path("/Users/evo/WorkBuddy/2026-09-11-23-22-58/_laifen/evoliu07-site/"
              "laifen-gtm/README.md")
AVATAR = ROOT / "build" / "avatar.jpg"

SKIP = {"photo", "photo_extra"}

CSS = """
:root{ --ink:#171411; --muted:#6d6258; --ink2:#3a332c; --paper:#f8f2e7; --paper-deep:#ece1cf;
  --line:#d8c8af; --red:#b9422f; --blue:#245f73; --green:#177A5C; --gold:#B8892F;
  --white:#fffaf0; --surface:rgba(255,250,240,.62); --surface-strong:rgba(255,250,240,.9);
  --bar-bg:rgba(248,242,231,.94);
  --font-b:"Songti SC","Noto Serif SC",Georgia,serif;
  --font-d:"PingFang SC","Microsoft YaHei",Helvetica,sans-serif;
  --bg:radial-gradient(circle at 20% 8%, rgba(184,137,47,.10), transparent 55%),
       radial-gradient(circle at 82% 0%, rgba(36,95,115,.08), transparent 45%), #f8f2e7;
  --shadow:0 2px 10px rgba(60,45,25,.07); --tint:rgba(184,137,47,.13);
  --tint-strong:rgba(184,137,47,.26);}
body[data-theme="ink-night"]{ --ink:#e8e4dc; --muted:#9c948a; --ink2:#cfc9bf; --paper:#14120f;
  --paper-deep:#1d1a16; --line:#332e27; --white:#0d0b09; --surface:rgba(34,30,25,.72);
  --surface-strong:rgba(40,35,29,.94); --bar-bg:rgba(20,18,15,.95);
  --bg:radial-gradient(circle at 20% 8%, rgba(217,171,82,.10), transparent 55%), #14120f;
  --shadow:0 2px 14px rgba(0,0,0,.5); --tint:rgba(217,171,82,.14);
  --tint-strong:rgba(217,171,82,.28); --red:#e07a63; --blue:#7fb6cc; --green:#6cc79f;}
body[data-theme="mist-blue"]{ --paper:#eef2f5; --paper-deep:#dde5ec; --line:#c2d0db; --ink:#16232c;
  --muted:#5c6b76; --ink2:#2c3d49; --white:#f8fbfd; --surface:rgba(248,251,253,.7);
  --surface-strong:rgba(248,251,253,.92); --bar-bg:rgba(238,242,245,.95);
  --bg:radial-gradient(circle at 20% 8%, rgba(36,95,115,.10), transparent 55%), #eef2f5;
  --tint:rgba(36,95,115,.11); --tint-strong:rgba(36,95,115,.22);}
body[data-theme="forest-moss"]{ --paper:#eef1ea; --paper-deep:#dde4d6; --line:#c2cfb8; --ink:#1b2419;
  --muted:#5d6a58; --ink2:#33422f; --white:#f8fbf6; --surface:rgba(248,251,246,.7);
  --surface-strong:rgba(248,251,246,.92); --bar-bg:rgba(238,241,234,.95);
  --bg:radial-gradient(circle at 20% 8%, rgba(23,122,92,.11), transparent 55%), #eef1ea;
  --tint:rgba(23,122,92,.12); --tint-strong:rgba(23,122,92,.24);}
body[data-theme="clay-rust"]{ --paper:#f6ece6; --paper-deep:#ecdcd2; --line:#dcc2b3; --ink:#251a16;
  --muted:#75635b; --ink2:#3f2d26; --white:#fdf7f3; --surface:rgba(253,247,243,.7);
  --surface-strong:rgba(253,247,243,.92); --bar-bg:rgba(246,236,230,.95);
  --bg:radial-gradient(circle at 20% 8%, rgba(185,66,47,.10), transparent 55%), #f6ece6;
  --tint:rgba(185,66,47,.11); --tint-strong:rgba(185,66,47,.22);}
body[data-theme="cloud-grey"]{ --paper:#f2f2f2; --paper-deep:#e4e4e4; --line:#cdcdcd; --ink:#1c1c1c;
  --muted:#6b6b6b; --ink2:#383838; --white:#fbfbfb; --surface:rgba(251,251,251,.72);
  --surface-strong:rgba(251,251,251,.94); --bar-bg:rgba(242,242,242,.95);
  --bg:radial-gradient(circle at 20% 8%, rgba(0,0,0,.04), transparent 55%), #f2f2f2;
  --shadow:0 2px 10px rgba(0,0,0,.06); --tint:rgba(0,0,0,.06); --tint-strong:rgba(0,0,0,.12);}
body[data-theme="gold-leaf"]{ --paper:#f7f1de; --paper-deep:#ebe0c4; --line:#d9c894; --ink:#241d10;
  --muted:#756646; --ink2:#3d331c; --white:#fdfaef; --surface:rgba(253,250,239,.7);
  --surface-strong:rgba(253,250,239,.92); --bar-bg:rgba(247,241,222,.95);
  --bg:radial-gradient(circle at 20% 8%, rgba(184,137,47,.16), transparent 55%), #f7f1de;
  --tint:rgba(184,137,47,.15); --tint-strong:rgba(184,137,47,.3);}

*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:var(--font-b);background:var(--bg);color:var(--ink);line-height:1.9;font-size:16.5px}
a{color:var(--blue);text-decoration:none} a:hover{text-decoration:underline}

/* ── 顶栏：三栏栅格，导航恒定居中于第一行 ── */
.bar{position:sticky;top:0;z-index:60;background:var(--bar-bg);backdrop-filter:blur(8px);
  border-bottom:1px solid var(--line);display:grid;grid-template-columns:1fr auto 1fr;
  align-items:center;gap:10px;padding:0 22px;height:62px;font-family:var(--font-d)}
.bar-l{justify-self:start}
.bar-r{justify-self:end;display:flex;align-items:center;gap:8px}
.brand{font-size:15.5px;font-weight:650;cursor:pointer;white-space:nowrap}
.b-mini{display:none}
.tabs{justify-self:center;display:flex;align-items:center;gap:6px;flex-wrap:nowrap}
.tabs button,.tabs a{border:0;background:none;color:var(--muted);font:inherit;
  font-family:var(--font-d);font-size:16px;letter-spacing:.08em;padding:8px 16px;border-radius:9px;
  cursor:pointer;white-space:nowrap;line-height:1.4}
.tabs button:hover,.tabs a:hover{background:var(--tint);color:var(--ink);text-decoration:none}
.tabs button[aria-selected="true"]{background:var(--tint-strong);color:var(--ink);font-weight:650}
.tp{position:relative}
.tp-trigger{border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:99px;
  padding:5px 12px;font:inherit;font-size:12.5px;cursor:pointer;font-family:var(--font-d);
  white-space:nowrap}
.t-mini{display:none}
.tp-menu{position:absolute;right:0;top:38px;background:var(--surface-strong);border:1px solid var(--line);
  border-radius:10px;box-shadow:var(--shadow);padding:6px;display:none;min-width:128px;z-index:70}
.tp[data-open="1"] .tp-menu{display:block}
.tp-menu button{display:block;width:100%;text-align:left;border:0;background:none;color:var(--ink);
  padding:7px 10px;border-radius:6px;font:inherit;font-size:13px;cursor:pointer;
  font-family:var(--font-d)}
.tp-menu button:hover{background:var(--tint)}
.tp-menu button[aria-pressed="true"]{font-weight:700;background:var(--tint-strong)}

main{max-width:900px;margin:0 auto;padding:0 24px 80px}
.view{display:none;animation:fd .28s ease}
.view.on{display:block}
@keyframes fd{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}

.hero{display:flex;flex-direction:column;align-items:center;text-align:center;padding:58px 0 26px}
.avatar{width:130px;height:130px;border-radius:50%;object-fit:cover;object-position:center;
  border:3px solid var(--paper-deep);box-shadow:var(--shadow);background:var(--white)}
.hero h1{font-family:var(--font-d);font-size:35px;font-weight:600;margin-top:18px}
.hero .sub{color:var(--muted);margin-top:6px;font-size:15.5px}
.hero .mail{margin-top:12px;font-size:14px;font-family:var(--font-d)}
.hero .bio{max-width:660px;margin-top:22px;font-size:16.5px;color:var(--ink2);text-align:left;
  line-height:2}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;
  margin:26px 0 6px;width:100%}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:15px;
  text-align:center}
.stat .v{font-size:22px;font-weight:650;font-family:var(--font-d);font-variant-numeric:tabular-nums}
.stat .l{font-size:12.5px;color:var(--muted);font-family:var(--font-d);margin-top:3px}
.jump{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin-top:22px;
  width:100%}
.jump button{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px;
  cursor:pointer;font:inherit;font-family:var(--font-d);text-align:left;color:var(--ink)}
.jump button:hover{background:var(--tint)}
.jump button b{display:block;font-size:15.5px;margin-bottom:3px}
.jump button span{font-size:12.5px;color:var(--muted)}

h2.sec{font-family:var(--font-d);font-size:12.5px;letter-spacing:.17em;text-transform:uppercase;
  color:var(--red);margin:30px 0 16px;font-weight:700}
h2.sec:first-child{margin-top:8px}
.entry{display:grid;grid-template-columns:60px 1fr;gap:15px;padding:19px 0;border-bottom:1px solid var(--line)}
.entry:last-child{border-bottom:0}
.logo{width:48px;height:48px;border-radius:11px;display:grid;place-items:center;color:#fff;
  font-size:12px;font-weight:700;background:var(--ink);font-family:var(--font-d)}
.org{font-family:var(--font-d);font-weight:650;font-size:16.5px}
.meta2{color:var(--muted);font-size:13.5px;margin-top:3px}
.when2{color:var(--muted);font-size:13px;white-space:nowrap;font-family:var(--font-d)}
.trow{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
.entry ul{margin:11px 0 0 18px}
.entry li{margin:8px 0;font-size:15.5px;line-height:1.85;color:var(--ink2)}

.card{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:19px 21px;
  margin-bottom:14px;box-shadow:var(--shadow)}
.card h3{font-family:var(--font-d);font-size:18px;font-weight:650;margin-bottom:6px}
.card .kick{color:var(--green);font-size:12.5px;font-family:var(--font-d);font-weight:600;
  margin-bottom:8px;letter-spacing:.02em}
.card p{color:var(--ink2);font-size:15.5px;margin-bottom:10px}
.card .more{display:none;margin-top:14px;padding-top:14px;border-top:1px dashed var(--line)}
.card.open .more{display:block}
.card .more h4{font-family:var(--font-d);font-size:14.5px;margin:15px 0 6px;color:var(--ink)}
.card .more p{font-size:14.8px;line-height:1.85}
.toggle{border:1px solid var(--line);background:var(--surface-strong);color:var(--ink);
  border-radius:99px;padding:7px 15px;font:inherit;font-size:13.5px;cursor:pointer;
  font-family:var(--font-d)}
.toggle:hover{background:var(--tint)}
.btnline{display:flex;gap:9px;flex-wrap:wrap;margin-top:11px}
.btnline a{border:1px solid var(--line);background:var(--surface-strong);color:var(--ink);
  border-radius:99px;padding:7px 15px;font-size:13.5px;font-family:var(--font-d)}
.btnline a:hover{background:var(--tint);text-decoration:none}
.tag{display:inline-block;font-size:12px;background:var(--tint);color:var(--muted);padding:2px 9px;
  border-radius:99px;margin:3px 4px 0 0;font-family:var(--font-d)}
.note{font-size:13px;color:var(--muted);line-height:1.75;margin-top:9px}

.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(176px,1fr));gap:14px;
  align-items:stretch}
.shot{background:var(--white);border:1px solid var(--line);border-radius:10px;overflow:hidden;
  cursor:zoom-in;box-shadow:var(--shadow);transition:transform .18s;display:flex;
  flex-direction:column}
.shot:hover{transform:translateY(-3px)}
.shot .ph{height:300px;display:grid;place-items:center;background:var(--paper-deep);padding:9px}
.shot img{max-height:282px;max-width:100%;width:auto;height:auto;object-fit:contain;display:block}
.shot .cap{padding:11px 12px;font-family:var(--font-d);flex:1;display:flex;flex-direction:column}
.shot .cap b{display:block;font-size:13px;color:var(--ink);font-weight:600;line-height:1.55}
.shot .cap .is{display:block;font-size:11.5px;color:var(--muted);line-height:1.6;margin-top:4px}
.shot .cap .dt{margin-top:auto;padding-top:9px;font-size:12.5px;color:var(--ink);font-weight:650;
  border-top:1px solid var(--line)}
.clabel{font-size:12px;color:var(--muted);font-family:var(--font-d);letter-spacing:.09em;
  margin:13px 0 7px}
.entry li b{font-weight:650;color:var(--ink)}
.lb{position:fixed;inset:0;background:rgba(15,12,9,.93);display:none;z-index:200;align-items:center;
  justify-content:center;padding:26px;cursor:zoom-out}
.lb.on{display:flex}
.lb img{max-width:100%;max-height:88vh;border-radius:8px}
footer{text-align:center;color:var(--muted);font-size:13px;padding:32px 0 0;margin-top:30px;
  border-top:1px solid var(--line);font-family:var(--font-d)}
@media(max-width:900px){
  .bar{height:56px;padding:0 12px;gap:6px}
  .brand{font-size:13px}
  .b-full{display:none} .b-mini{display:inline}
  .tabs{gap:1px}
  .tabs button,.tabs a{font-size:12.5px;padding:6px 8px;letter-spacing:.01em}
  .t-full{display:none} .t-mini{display:inline}
  .tp-trigger{padding:5px 9px}
}
@media(max-width:760px){
  main{padding:0 15px 60px}
  .hero{padding:34px 0 20px} .hero h1{font-size:26px}
  .entry{grid-template-columns:1fr} .logo{display:none}
}
@media print{ .bar{display:none} .view{display:block!important} .more{display:block!important} }
/* ── 经历 / 实习 / 教育 / 项目：回归左对齐原排版（仅导航与自我评价另设）── */
.tabs button,.tabs a{font-weight:700;font-size:17px}
h2.sec{font-size:12.5px;letter-spacing:.17em;margin:30px 0 16px}
.entry{display:grid;grid-template-columns:60px 1fr;gap:15px;padding:19px 0;text-align:left}
.trow{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;text-align:left}
.entry ul{margin:11px 0 0 18px;padding:0;list-style:disc}
.entry li{margin:8px 0;font-size:15.5px;line-height:1.85;color:var(--ink2);text-align:left}
.entry li b{font-weight:650;color:var(--ink)}
.clabel{font-size:12px;color:var(--muted);font-family:var(--font-d);letter-spacing:.09em;margin:13px 0 7px;text-align:left}
.card{text-align:left}
.card h3,.card p,.card .kick,.card .more,.card .more h4,.card .more p{text-align:left}
.card > div:not(.more){text-align:left}
.jump button{text-align:center}
.hero .biohead{font-family:var(--font-d);font-size:19px;font-weight:800;color:var(--ink);
  text-align:center;line-height:1.75;max-width:660px;margin:22px auto 18px}
.hero .bio{text-align:left;max-width:820px;margin:0 auto}
.bioitem{margin:0 0 11px;color:var(--muted);font-size:15px;line-height:1.95}
.bioitem:last-child{margin-bottom:0}
.bioitem b{font-weight:650;color:var(--ink)}

/* ══════════ 微信内置浏览器兜底 ══════════ */
html,body{overflow-x:hidden}          /* clip 在旧版 X5 内核不支持，用 hidden 兜底 */
#wxbar{position:fixed;left:0;right:0;bottom:0;z-index:400;background:#1B3A6B;color:#fff;
  padding:11px 14px;text-align:center;font-family:var(--font-d);font-size:13px;line-height:1.6}
#wxbar b{font-weight:700}
body.wx{padding-bottom:52px}
.nofallback{padding:24px 16px;text-align:left;font-family:var(--font-d);font-size:14.5px;color:var(--ink2);line-height:1.95;
  max-width:820px;margin:0 auto}
.nofallback h3{font-size:15px;margin:20px 0 8px;color:var(--ink)}
.nofallback ul{margin:0 0 0 18px;list-style:disc}
.nofallback li{margin:7px 0}
.nofallback p{margin:0 0 10px;color:var(--muted)}
.nofallback b{color:var(--ink);font-weight:650}
noscript .nofallback{display:block}


/* ══════════ 自适应（放在样式表最后，确保覆盖前面的规则）══════════ */
html{-webkit-text-size-adjust:100%;text-size-adjust:100%}
html,body{max-width:100%;overflow-x:clip}
img,svg,table,pre{max-width:100%}
*,*::before,*::after{box-sizing:border-box}

/* 平板 / 小笔电 */
@media(max-width:900px){
  .bar{height:auto;padding:9px 12px;flex-wrap:wrap;row-gap:6px}
  .bar b{font-size:14px}
  .bar nav{gap:10px;font-size:12.5px}
  main{padding:20px 14px 54px}
  h1{font-size:23px}
  .hero{padding:30px 0 16px}
  .hero h1{font-size:26px}
  .hero .sub{font-size:14px}
  .hero .biohead{font-size:17px;max-width:100%}
  .hero .bio{max-width:100%}
  .bioitem{font-size:14.5px}
  .entry{grid-template-columns:1fr;gap:0;padding:18px 0;text-align:left}
  .logo{display:none}
  .trow{display:block}
  .when2{display:block;margin-top:6px}
  .entry ul{margin-left:16px}
  .entry li{font-size:14.8px;line-height:1.85}
  .card{padding:16px 15px}
  .card h3{font-size:14.5px}
  .jump{grid-template-columns:1fr;gap:10px}
  .jump button{padding:14px 15px}
  .grid{grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:11px}
  .shot .ph{height:236px}
  .shot img{max-height:220px}
  .stats{grid-template-columns:repeat(2,1fr)}
}

/* 手机 */
@media(max-width:480px){
  .bar{padding:8px 10px}
  .bar b{font-size:13px}
  .bar nav{gap:8px}
  .bar{grid-template-columns:1fr auto;grid-template-areas:"brand theme" "nav nav";
    gap:8px 10px;align-items:center}
  .bar-l{grid-area:brand}
  .bar-r{grid-area:theme;justify-self:end}
  .tabs{grid-area:nav;width:100%;justify-content:center;flex-wrap:nowrap;gap:5px}
  .tabs button,.tabs a{font-size:12.5px;padding:6px 10px}
  .hero{padding:26px 0 14px}
  .avatar{width:112px;height:112px}
  .hero h1{font-size:24px}
  .hero .biohead{font-size:16.5px}
  .stats{grid-template-columns:1fr 1fr;gap:9px}
  .stat .v{font-size:19px}
  .grid{grid-template-columns:1fr 1fr;gap:10px}
  .shot .ph{height:212px}
  .shot img{max-height:198px}
  .shot .cap b{font-size:12.5px}
  .shot .cap .is{font-size:11px}
  .tbwrap{-webkit-overflow-scrolling:touch}
  .card{padding:15px 13px}
  .entry li{font-size:14.4px}
  .bioitem{font-size:14.2px}
  main{padding:18px 12px 48px}
}

/* 窄屏（iPhone SE 等） */
@media(max-width:380px){
  .tabs{gap:4px}
  .tabs button,.tabs a{font-size:12px;padding:6px 8px}
  .bar b{font-size:12.5px}
  .bar nav{gap:6px}
  .grid{grid-template-columns:1fr}
  .stat .v{font-size:18px}
  .hero h1{font-size:22px}
  .avatar{width:100px;height:100px}
}

/* 横屏手机 */
@media(max-height:480px) and (orientation:landscape){
  .hero{padding:18px 0 12px}
  .avatar{width:88px;height:88px}
  .hero h1{font-size:21px}
}

@media print{
  .bar,.sub2{display:none}
  .view{display:block!important}
  .more{display:block!important}
  .srcbox{text-align:left}
}



"""

HTML = """<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>刘柏廷 · Evo</title>
<meta name="description" content="刘柏廷 BoTing LIU：香港中文大学（深圳）计算社会科学（统计学）硕士在读，澳门科技大学工商管理（国际贸易）学士。项目覆盖德国 GTM 出海研究、金融市场数据看板与银行客户经营分析。">
<style>__CSS__</style></head>
<body data-theme="warm-paper">

<div class="bar">
  <div class="bar-l"><span class="brand" onclick="go('home')"><span class="b-full">刘柏廷 · Evo</span><span class="b-mini">Evo</span></span></div>
  <nav class="tabs" aria-label="主导航">
    <button data-v="exp" onclick="go('exp')">经历</button>
    <button data-v="proj" onclick="go('proj')">项目</button>
    <button data-v="cert" onclick="go('cert')">证书</button>
    <a href="dashboard.html">数据看板</a>
    <a href="news.html">实时新闻</a>
  </nav>
  <div class="bar-r">
    <span class="tp" id="tp" data-open="0">
      <button class="tp-trigger" id="tp-btn" aria-haspopup="true" aria-expanded="false"><span class="t-full">主题</span><span class="t-mini">◐</span></button>
      <span class="tp-menu" id="tp-menu" role="menu"></span>
    </span>
  </div>
</div>

<main>
  <section class="view" id="v-home"></section>
  <section class="view" id="v-exp"></section>
  <section class="view" id="v-proj"></section>
  <section class="view" id="v-cert"></section>
  <noscript><div id="static-fallback">__STATIC__</div></noscript>
</main>
<div class="lb" id="lb"><img id="lb-img" alt="证书"></div>

__WXJS__
<script>
const AV=__AVATAR__, D=__DATA__;
const THEMES=[["warm-paper","暖纸"],["ink-night","夜墨"],["mist-blue","雾蓝"],
  ["forest-moss","苔绿"],["clay-rust","陶土"],["cloud-grey","云灰"],["gold-leaf","金叶"]];
const TK="evo:theme", VK="evo:view";
function setTheme(t){document.body.dataset.theme=t;
  document.querySelectorAll("[data-pick]").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.pick===t)));
  try{localStorage.setItem(TK,t)}catch(e){}}
(function(){const m=document.getElementById("tp-menu");
  m.innerHTML=THEMES.map(([k,n])=>`<button data-pick="${k}" role="menuitem" aria-pressed="false">${n}</button>`).join("");
  let t="warm-paper";try{t=localStorage.getItem(TK)||"warm-paper"}catch(e){}setTheme(t);
  const close=()=>{const tp=document.getElementById("tp");tp.dataset.open="0";
    document.getElementById("tp-btn").setAttribute("aria-expanded","false")};
  m.addEventListener("click",e=>{const b=e.target.closest("[data-pick]");if(b){setTheme(b.dataset.pick);close();}});
  const tp=document.getElementById("tp"),btn=document.getElementById("tp-btn");
  btn.addEventListener("click",e=>{e.stopPropagation();const o=tp.dataset.open==="1";
    tp.dataset.open=o?"0":"1";btn.setAttribute("aria-expanded",String(!o));});
  document.addEventListener("click",e=>{if(!tp.contains(e.target))close();});})();

document.getElementById("v-home").innerHTML=`
  <div class="hero">
    <img class="avatar" src="${AV}" alt="刘柏廷">
    <h1>刘柏廷 · Evo</h1>
    <p class="sub">${D.subtitle}</p>
    <p class="mail"><a href="mailto:${D.email}">${D.email}</a></p>
    <p class="biohead">${D.about.head.join('<br>')}</p>
    <div class="bio">${D.about.items.map((a)=>`<p class="bioitem"><b>${a.k}：</b>${a.v}</p>`).join("")}</div>
  </div>
  <div class="stats">${D.stats.map(s=>`<div class="stat"><div class="v">${s.v}</div><div class="l">${s.l}</div></div>`).join("")}</div>
  <div class="jump">
    <button onclick="go('exp')"><b>经历 →</b><span>教育背景与六段实习</span></button>
    <button onclick="go('proj')"><b>项目 →</b><span>四项独立研究</span></button>
    <button onclick="location.href='news.html'"><b>实时新闻 →</b><span>证券财经 · 出海大事</span></button>
    <button onclick="location.href='dashboard.html'"><b>数据看板 →</b><span>金融 · 出海</span></button>
  </div>`;

document.getElementById("v-exp").innerHTML=`
  <h2 class="sec">教育经历</h2>
  ${D.edu.map(e=>`<div class="entry">
    <div class="logo" style="background:${e.c}">${e.tag}</div>
    <div><div class="trow"><div>
      <div class="org">${e.org}</div><div class="meta2">${e.deg}</div>
      ${e.honor?`<div class="meta2" style="margin-top:5px">${e.honor}</div>`:""}
    </div><div class="when2">${e.when}</div></div></div></div>`).join("")}
  <h2 class="sec">实习经历</h2>
  ${D.career.map(c=>`<div class="entry">
    <div class="logo" style="background:${c.c}">${c.tag}</div>
    <div><div class="trow"><div>
      <div class="org">${c.org}</div><div class="meta2">${c.role}</div>
    </div><div class="when2">${c.when}</div></div>
    <div class="clabel">主要贡献</div>
    <ul>${c.pts.map(p=>`<li><b>${p.k}</b> — ${p.v}</li>`).join("")}</ul></div></div>`).join("")}`;

document.getElementById("v-proj").innerHTML=`
  <h2 class="sec">项目经历</h2>
  ${D.projects.map((p,i)=>`<div class="card" id="pc${i}">
    <div class="kick">${p.kick}</div><h3>${p.title}</h3>
    <p>${p.sum}</p>
    <div>${p.tags.map(t=>`<span class="tag">${t}</span>`).join("")}</div>
    <div style="margin-top:11px"><button class="toggle" data-p="${i}">展开看做法与数据</button></div>
    ${p.links.length?`<div class="btnline">${p.links.map(l=>`<a href="${l.href}">${l.label}</a>`).join("")}</div>`:""}
    <div class="more">${p.body}</div>
  </div>`).join("")}`;

document.getElementById("v-cert").innerHTML=`
  <h2 class="sec">证书与荣誉</h2>
  <div class="grid" id="cg"></div>`;

const cg=document.getElementById("cg");
cg.innerHTML=D.certs.map((c,i)=>`<div class="shot" data-i="${i}" role="button" tabindex="0" aria-label="${c.name}">
  <div class="ph"><img src="${c.uri}" alt="${c.name}" loading="lazy"></div>
  <div class="cap"><b>${c.name}</b>${(c.issuer||[]).map(x=>`<span class="is">${x}</span>`).join("")}<span class="dt">${c.date}</span></div>
</div>`).join("");
const lb=document.getElementById("lb"),lbI=document.getElementById("lb-img");
function op(i){lbI.src=D.certs[i].uri;lb.classList.add("on");}
cg.addEventListener("click",e=>{const s=e.target.closest(".shot");if(s)op(+s.dataset.i);});
cg.addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" "){const s=e.target.closest(".shot");
  if(s){e.preventDefault();op(+s.dataset.i);}}});
lb.addEventListener("click",()=>lb.classList.remove("on"));
document.addEventListener("keydown",e=>{if(e.key==="Escape")lb.classList.remove("on");});

document.addEventListener("click",e=>{const t=e.target.closest("[data-p]");
  if(t){const c=document.getElementById("pc"+t.dataset.p);const on=c.classList.toggle("open");
    t.textContent=on?"收起":"展开看做法与数据";}});

function go(v){
  document.querySelectorAll(".view").forEach(s=>s.classList.toggle("on",s.id==="v-"+v));
  document.querySelectorAll(".tabs button[data-v]").forEach(b=>b.setAttribute("aria-selected",String(b.dataset.v===v)));
  try{localStorage.setItem(VK,v)}catch(e){}
  window.scrollTo(0,0);
}
let v0="home";try{v0=localStorage.getItem(VK)||"home"}catch(e){}
go(["home","exp","proj","cert"].includes(v0)?v0:"home");
</script></body></html>
"""


def make_avatar() -> str:
    if AVATAR.exists():
        src = AVATAR
    else:
        src = Path("/Users/evo/Desktop/校招/照片/简历版.png")
    if not src.exists():
        return next((c["uri"] for c in IMG if c["key"] == "photo"), "")
    im = Image.open(src).convert("RGB")
    if im.size != (520, 520):
        w, h = im.size
        s = min(w, h)
        top = int((h - s) * 0.10)
        im = im.crop((0, top, s, top + s)).resize((520, 520), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "JPEG", quality=88, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def strip_tags(s: str) -> str:
    s = re.sub(r"<(script|style)[\s\S]*?</\1>", "", s)
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"</(p|li|h[1-6]|div|tr)>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return "\n".join(l.strip() for l in s.split("\n") if l.strip())


def cust_body() -> str:
    if not CUST.exists():
        return ""
    t = CUST.read_text(encoding="utf-8")
    body = t[t.find("<body"):] if "<body" in t else t
    parts = re.split(r"<h2[^>]*>(.*?)</h2>", body, flags=re.S)
    if len(parts) < 3:
        return f"<p>{strip_tags(body)[:1200]}</p>"
    o = ""
    for i in range(1, len(parts) - 1, 2):
        h = strip_tags(parts[i])
        p = re.sub(r"（\s*）", "", strip_tags(parts[i + 1]))
        if len(p) > 1300:
            p = p[:1300] + "…"
        if h and p:
            o += f"<h4>{h}</h4>"
            for para in p.split("\n"):
                if len(para.strip()) > 12:
                    o += f"<p>{para.strip()}</p>"
    return o


def laifen_body() -> str:
    """只描述方法与模块结构，不引用任何样本量或演示数据。"""
    return (
        "<h4>评论挖掘</h4><p>对德语用户评论做情感打分与主题聚类，"
        "把竞品被抱怨最集中的方向转成产品切入点，而不是沿用国内话术。</p>"
        "<h4>达人分层</h4><p>按受众地域、内容契合度与互动质量分层，并设置反作弊规则，"
        "避免只看粉丝量导致的投放浪费。</p>"
        "<h4>竞品价格追踪</h4><p>每日入库竞品价格，用滚动中位数基线识别促销区间，"
        "让价格节奏可提前判断。</p>"
        "<h4>渠道漏斗</h4><p>曝光 → 点击 → 详情页 → 加购 → 成交 → 复购，"
        "计算各渠道获客成本并与单台贡献毛利对比，决定资源投在哪。</p>"
        "<h4>本地化文案</h4><p>生成多版德语文案并做人工评分，最终判断由人完成。</p>"
        "<h4>工程与更新</h4><p>抓取、清洗与看板代码可复现，支持按日定时自动更新。</p>")


WX_JS = (Path(__file__).resolve().parent / "_wx_snippet.js").read_text(encoding="utf-8")


def static_fallback(d: dict) -> str:
    """无 JS 环境（含微信内核异常）时的静态内容，保证信息不丢。"""
    out = ['<div class="nofallback">']
    out.append(f'<h3>自我评价</h3>')
    if isinstance(d.get("about"), dict):
        out.append('<p><b>' + d["about"].get("head", [])[0] + ' ' + (d["about"].get("head", ["", ""])[1] if len(d["about"].get("head", [])) > 1 else "") + '</b></p>')
        for it in d["about"].get("items", []):
            out.append(f'<p><b>{it["k"]}：</b>{it["v"]}</p>')
    out.append('<h3>教育经历</h3>')
    for e in d.get("edu", []):
        out.append(f'<p><b>{e["org"]}</b>　{e["deg"]}　{e["when"]}'
                   + (f'　{e["honor"]}' if e.get("honor") else '') + '</p>')
    out.append('<h3>实习经历</h3>')
    for c in d.get("career", []):
        out.append(f'<p><b>{c["org"]}</b>　{c["role"]}　{c["when"]}</p>')
        out.append('<ul>')
        for pt in c.get("pts", []):
            k = pt.get("k", "") if isinstance(pt, dict) else ""
            v = pt.get("v", pt) if isinstance(pt, dict) else pt
            out.append(f'<li><b>{k}：</b>{v}</li>')
        out.append('</ul>')
    out.append('<h3>项目经历</h3>')
    for pr in d.get("projects", []):
        out.append(f'<p><b>{pr["title"]}</b></p>')
        out.append(f'<p>{pr["sum"]}</p>')
    out.append('<h3>证书与荣誉</h3>')
    out.append('<ul>')
    for c in d.get("certs", []):
        iss = "　".join(c.get("issuer") or [])
        out.append(f'<li><b>{c["name"]}</b>　{iss}　{c["date"]}</li>')
    out.append('</ul>')
    out.append('<p style="margin-top:18px">完整交互（图表与实时数据）请访问数据看板：<b>dashboard.html</b></p>')
    out.append('</div>')
    return "\n".join(out)



def main() -> None:
    # 证书：只保留 名称 / 颁发方 / 时间
    # key -> (证书名称, 颁发方[按行], 获奖时间)
    cert_meta = {
        "cert_olympiad_math": ("全国大学生奥林匹克数学竞赛（夏季赛）· 非数学类铜奖",
                               ["国际（澳门）学术研究院数学科学研究所"], "2023年4月"),
        "cert_immche": ("国际高校数学建模竞赛 · Honorable Mention",
                        ["国际（澳门）学术研究院数学科学研究所",
                         "香港数学研究与应用学会"], "2023年7月"),
        "cert_ieera": ("「IEERA 杯」国际高校英语阅读挑战赛 · 中国区一等奖",
                       ["国际英语教育研究协会（IEERA）"], "2023年6月"),
        "cert_trade": ("全国大学生国际贸易挑战赛 · 三等奖",
                       ["中国欧洲经济技术合作协会", "一带一路经济文化委员会"], "2023年7月"),
        "cert_ietccs": ("国际大学生英语翻译挑战赛（IETCCS）· C 组三等奖",
                        ["国际（澳门）学术研究院外语教育研究所",
                         "香港语言研究会"], "2023年4月"),
        "cert_ibtac": ("全国大学生国际中英双语对外翻译能力大赛 · 三等奖",
                       ["中国国际经济合作促进会教育工作委员会"], "2023年7月"),
        "cert_college_rank": ("商学院院长优秀毕业生",
                              ["澳门科技大学商学院"], "2024年12月"),
        "cert_volunteer": ("杜克大学 B-LAB 红外相机科研实验",
                           ["昆山杜克大学 生物多样性与可持续发展实验室"], "2023年"),
    }
    certs = []
    for c in IMG:
        if c["key"] in SKIP or c["key"] not in cert_meta:
            continue
        name, issuers, when = cert_meta[c["key"]]
        certs.append({"name": name, "issuer": issuers,
                      "date": when, "uri": c["uri"], "ratio": round(c["w"] / c["h"], 3)})

    data = {
        "email": "lbt2238516944@163.com",
        "subtitle": "香港中文大学（深圳）计算社会科学（统计学）硕士在读",
        "about": "国际贸易本科，统计学硕士在读。实习覆盖银行、券商资管、基金渠道、"
                 "电商商务与卖方研究，涉及销售漏斗分析、渠道经营与数据看板搭建。",
        "stats": [
            {"v": "41,188", "l": "客户经营建模样本量"},
            {"v": "94,236", "l": "英国当月新车注册（SMMT）"},
            {"v": "6", "l": "段金融与商业实习"},
            {"v": "8", "l": "项竞赛与荣誉"},
        ],
        "edu": [
            {"tag": "CUHK", "c": "#6b1020", "org": "香港中文大学（深圳）",
             "deg": "计算社会科学（统计学）理学硕士 · 深圳", "when": "2025.09-2027.06",
             "honor": ""},
            {"tag": "MUST", "c": "#1a3c6e", "org": "澳门科技大学",
             "deg": "工商管理（国际贸易）学士 · 澳门", "when": "2021.09-2025.06",
             "honor": "商学院院长优秀毕业生"},
        ],
        "about": {
            "head": ["金融 × 统计复合背景", "机构客户经营、投研转译与数据驱动提效"],
            "items": [
                {"k": "市场跟踪与政策研判", "v": "华福证券研究所策略组维护 A 股／港股日度跟踪体系，AI 自动化监测 PMI、社融、两融余额等关键指标；累计输出 10+ 份政策解读／专题材料，支持策略路演与机构客户日常沟通。"},
                {"k": "机构客户开发与准入推进", "v": "鹏扬基金机构业务部建立 22 家机构需求台账（券商资管、城商行理财子、地方产业平台），开展 12 场线上交流，推动 3 家机构完成产品准入，意向规模合计约 8000 万元。"},
                {"k": "渠道经营与投研转译", "v": "诺安基金深度对接华中四省渠道，培训覆盖 200+ 人次；把赛道投资逻辑转译为客户适配要点，推进差异化营销与竞品分析，区域销售效能环比提升 15%。"},
                {"k": "数据驱动的业务拆解与提效", "v": "京东零售拆解线索至上线全周期转化数据，搭建城市预警与监控看板，交付周期缩短 30%，团队执行力提升 20%。"},
            ],
        },
        "career": [
            {"tag": "华福", "c": "#8a5a2b", "org": "华福证券股份有限公司",
             "role": "研究所-策略组-首席分析师助理", "when": "2026.07 – 2026.09", "pts": [
                 {"k": "日频跟踪研究支持", "v": "维护 A 股、港股及宏观流动性日度跟踪体系，AI 自动化监测 PMI、社融、两融余额等关键指标；更新市场数据及晨会／日报点评，支持策略组市场研判与日常研究服务。"},
                 {"k": "政策解读专题输出", "v": "梳理重要政策及宏观事件，提炼政策目标、受益方向与市场影响路径；累计输出 10+ 份政策解读／专题材料，撰写行业简评报告，传递策略观点并与机构客户日常沟通。"},
                 {"k": "客户需求对接及路演服务", "v": "筹备策略路演、电话会议与调研活动，精准捕捉客户关注的市场问题及反馈，并完善后续观点与服务内容，提升客户粘性。"}]},
            {"tag": "京东", "c": "#e21a1a", "org": "京东集团股份有限公司-京东零售",
             "role": "商务拓展岗", "when": "2026.03 – 2026.07", "pts": [
                 {"k": "链路拆解预警促活", "v": "围绕线索至上线全周期拆解转化数据，识别流失卡点，搭建城市预警机制，对滞后客户前置干预，交付周期缩短 30%，聚焦高价值客户开拓、转化率提升及存量裂变，完成意向到上线业务闭环。"},
                 {"k": "分层拓客赋能裂变", "v": "对高价值客户分层运营，挖掘竞对翻牌客户并定制攻坚方案，为存量商家输出裂变赋能体系，提高 KA 及老商新店占比，聚焦客户开拓转化与存量裂变，深度绑定高净值客户实现业务增长。"},
                 {"k": "中台协同迭代人效", "v": "统筹电销、工程、供应链中台，支撑 90+ 招商经理开展业务，AI 搭建数据收集与结果转化助力人效督导，使团队执行力提升 20%，统筹招商会落地，保障线索流转，实现政策精准触达与业务高效推进。"}]},
            {"tag": "诺安", "c": "#0b3d91", "org": "诺安基金管理有限公司",
             "role": "华中业务部-渠道经理助理", "when": "2025.09 – 2026.03", "pts": [
                 {"k": "渠道维护与精准营销", "v": "深度对接华中四省市渠道，与一线理财经理持续沟通，跟踪渠道客户结构、产品销售进度及市场反馈；梳理交易数据研判高净值客户偏好，落地差异化营销与竞品分析，推进区域渗透。"},
                 {"k": "投研观点转译与渠道赋能", "v": "围绕科技和半导体主题基金，结合产品持仓、行业景气、历史净值及回撤特征，拆解赛道投资逻辑与客户适配要点；参与制作路演材料与开展渠道培训，累计覆盖 200+ 人次。"},
                 {"k": "效能建模渠道优化", "v": "参与多场线上线下沙龙路演，搭建渠道效能评估模型，围绕覆盖率和转化率复盘渠道客户对市场、产品及风险问题的反馈，支持后续沟通材料与推广节奏优化；引导资源倾斜优质渠道，区域销售效环比提升 15%。"}]},
            {"tag": "鹏扬", "c": "#7a5c1e", "org": "鹏扬基金管理有限公司",
             "role": "机构业务部-机构经理助理", "when": "2024.12 – 2025.03", "pts": [
                 {"k": "机构客户开发与需求研判", "v": "负责券商资管、城商行理财子、地方产业平台等资金方的前期业务拜访与需求访谈；建立 22 家机构客户需求台账，精准匹配机构风险偏好、久期约束及配置诉求，形成投研反馈机制。"},
                 {"k": "定制化产品方案与拜访沟通", "v": "结合 Wind 与内部组合数据，针对固收+、权益赛道定制机构尽调材料与投资建议书，拆解产品收益、回撤、最大风险敞口；开展 12 场线上机构交流，输出观点摘要，大幅降低机构内部评审沟通成本。"},
                 {"k": "准入跟踪转化推进", "v": "搭建机构准入及意向跟踪台账，对客户准入进度、谈判卡点做量化复盘；协同产品、投研部门解决机构关切问题，推动 3 家机构完成产品准入，实现机构意向规模合计约 8000 万元。"}]},
            {"tag": "银河", "c": "#c4a35a", "org": "中国银河证券-银河金汇资产管理",
             "role": "固收二部-多资产投资助理岗", "when": "2024.06 – 2024.09", "pts": [
                 {"k": "产品研究募集落地", "v": "协助梳理「辰星FOF增利 1 号」等固收及多资产产品的定期报告、持仓与估值数据，提炼核心策略、收益来源及风险特征；撰写 20+ 份产品材料并支持 4 场路演，协助完成约 1000 万元产品募集落地。"},
                 {"k": "净值跟踪业绩归因与客户响应", "v": "基于 Wind 开展产品净值跟踪及业绩归因，拆解债券、权益等资产对净值波动的影响，覆盖 10+ 份产品／组合，高效支持前台回应机构客户对产品表现的问询。"},
                 {"k": "投研支持与投后管理", "v": "跟踪组合及投研讨论，关注锂矿、光伏等产业链价格变动与市场信息；整理信息底稿为投资经理研判资产配置提供参考；协助 FOF 投后管理，维护投资台账及产品估值表，支持投资复盘与绩效评估。"}]},
            {"tag": "贵阳", "c": "#0a6b4c", "org": "贵阳银行",
             "role": "成都分行-财富经理助理岗", "when": "2023.06 – 2023.09", "pts": [
                 {"k": "产品推介与募集落地", "v": "协助梳理「爽银财富」固收理财、大额存单及代销保险等在售产品要素、起购门槛与风险等级匹配规则，提炼适合稳健／平衡型客户的卖点与注意事项；撰写 15+ 份产品介绍及话术材料并支持 3 场网点沙龙，协助完成约 600 万元理财及存款类产品落地。"},
                 {"k": "客户经营与需求响应", "v": "协助维护高净值及潜力客户档案，整理持仓、到期日与风险测评结果，按客户需求准备产品对比与配置建议；覆盖 30+ 位重点客户的日常跟进，高效支持财富经理回应收益、赎回、到期承接等问询，推动到期资金留存与二次配置。"},
                 {"k": "厅堂服务与活动支持", "v": "协助厅堂识别有理财需求的客户并完成风险测评、双录及资料初审；整理沙龙物料、签到与会后跟进清单，配合开展客户答谢及产品宣讲；维护客户台账与活动反馈，支持财富团队日常营销与合规留痕。"}]},
        ],
        "projects": [
            {"kick": "数据看板 › 金融",
             "title": "利率研究：宏观流动性、利率与曲线结构",
             "sum": "围绕国债收益率曲线、期限利差与宏观流动性读数，把利率变化拆成可复核的一组数字，"
                    "用于判断当前利率环境对不同久期与不同流动性约束的组合意味着什么。",
             "tags": ["国债收益率曲线", "期限利差", "两融余额", "美元兑人民币"],
             "links": [{"href": "dashboard.html#fin-rates", "label": "在数据看板中查看 →"}],
             "body": "<p>数据来自交易所与官方公开渠道，按交易日更新；"
                     "债市曲线取中债国债收益率曲线，同一曲线取点计算期限利差。</p>"},
            {"kick": "数据看板 › 金融 · 国际高校数学建模竞赛",
             "title": "银行客户经营建模：触达优先级与名额分配",
             "sum": "围绕「先联系谁、各类对象分配多少名额」，用 41,188 条公开银行营销记录，"
                    "比较凭历史成交经验筛选与综合多项信息排序的差异，"
                    "形成可随团队可用名额调整的跟进方案。",
             "tags": ["逻辑回归", "名额分配", "样本外检验", "UCI 公开数据"],
             "links": [{"href": "dashboard.html#fin-bank", "label": "在数据看板中查看 →"}],
             "body": cust_body()},
            {"kick": "数据看板 › 出海",
             "title": "比亚迪（英国）：市场进入研究与竞品基线",
             "sum": "以 BYD DOLPHIN SURF 为切口建立英国市场基线：接入 SMMT 官方注册数据，"
                    "覆盖动力类型、销售渠道、品牌级与车型榜；并跟踪中国品牌在英国的注册表现。",
             "tags": ["SMMT", "市场基线", "竞品基线", "渠道结构"],
             "links": [{"href": "dashboard.html#sea-byd", "label": "在数据看板中查看 →"}],
             "body": "<p>市场基线：英国单月新乘用车注册 94,236 辆，纯电 28,063 辆，同比 +27.7%；"
                     "年初至今纯电 355,746 辆。</p>"
                     "<p>渠道结构：车队 57.2% / 私人 40.8% / 公司自用 2.0%。</p>"
                     "<p>中国与新兴品牌注册表现：MG 4,960 辆（同比 +93.5%）、Jaecoo 4,022 辆（+194.2%）、"
                     "BYD 3,867 辆（+119.8%）、Chery 2,380 辆、Omoda 2,216 辆、"
                     "Leapmotor 965 辆（+274%）。</p>"
                     "<p>竞品基线覆盖 BYD DOLPHIN SURF、Renault 5 E-Tech、MG4 EV 与 Dacia Spring "
                     "的官方公布规格。</p>"},
            {"kick": "数据看板 › 出海",
             "title": "徕芬（德国）：市场进入决策框架",
             "sum": "把「评论挖掘 → 达人分层 → 竞品价格追踪 → 渠道漏斗 → 本地化文案」五个模块"
                    "串成一条上市决策链，每个模块对应一个具体决策问题：切什么卖点、投给谁、"
                    "什么时候调价、钱花在哪、话怎么说。",
             "tags": ["出海 GTM", "评论挖掘", "达人分层", "价格追踪", "渠道漏斗"],
             "links": [{"href": "dashboard.html#sea-laifen", "label": "在数据看板中查看 →"}],
             "body": laifen_body()},
        ],
        "certs": certs,
    }

    html = (HTML.replace("__CSS__", CSS)
                .replace("__STATIC__", static_fallback(data))
                .replace("__WXJS__", WX_JS)
                .replace("__AVATAR__", json.dumps(make_avatar(), ensure_ascii=False))
                .replace("__DATA__", json.dumps(data, ensure_ascii=False)))
    evo = ROOT / "evo-site"
    if not evo.exists():
        evo.mkdir(parents=True)
    out = evo / "index.html"
    out.write_text(html, encoding="utf-8")
    log_line(f"主页已生成：{out.relative_to(ROOT)}（{len(html)/1048576:.2f} MB）")
    log_line(f"  导航 5 项 · 实习 {len(data['career'])} 段 · 项目 {len(data['projects'])} 个"
             f" · 证书 {len(certs)} 项")


if __name__ == "__main__":
    main()
