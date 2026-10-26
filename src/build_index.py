"""
生成主站 evo-site/index.html —— 多视图版：点哪个栏目只显示哪个。

视图：首页 / 经历 / 项目 / 证书（看板为独立页面 dashboard.html）
设计沿用参考站的暖纸质 + 衬线正文 + 7 主题。
用法： python src/build_index.py
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
FIN = json.loads((ROOT / "data" / "dash" / "dashboard.json").read_text(encoding="utf-8"))
SEA = json.loads((ROOT / "data" / "dash" / "overseas.json").read_text(encoding="utf-8"))
CUST = Path("/Users/evo/WorkBuddy/2026-09-11-23-22-58/_incoming/experiences/"
            "customer-prioritization.html")
LAIFEN = Path("/Users/evo/WorkBuddy/2026-09-11-23-22-58/_laifen/evoliu07-site/"
              "laifen-gtm/README.md")

SKIP_KEYS = {"photo", "photo_extra"}        # 头像与那张证件照，不作为证书展示

THEMES = Path(ROOT / "src" / "theme_tokens.css").read_text(encoding="utf-8") \
    if (ROOT / "src" / "theme_tokens.css").exists() else ""

CSS = (THEMES or """
:root{ --ink:#171411; --muted:#6d6258; --ink-soft:#3a332c; --ink-soft-2:#4a4239;
  --paper:#f8f2e7; --paper-deep:#ece1cf; --line:#d8c8af; --red:#b9422f; --blue:#245f73;
  --green:#177A5C; --gold:#B8892F; --white:#fffaf0; --surface:rgba(255,250,240,.62);
  --surface-strong:rgba(255,250,240,.9); --bar-bg:rgba(248,242,231,.94);
  --font-body:"Songti SC","Noto Serif SC",Georgia,serif;
  --font-display:"PingFang SC","Microsoft YaHei",Helvetica,sans-serif;
  --bg:radial-gradient(circle at 20% 8%, rgba(184,137,47,.10), transparent 55%),
       radial-gradient(circle at 82% 0%, rgba(36,95,115,.08), transparent 45%), #f8f2e7;
  --shadow:0 2px 10px rgba(60,45,25,.07); --tint:rgba(184,137,47,.13);
  --tint-strong:rgba(184,137,47,.26);}
""") + """
body[data-theme="ink-night"]{ --ink:#e8e4dc; --muted:#9c948a; --ink-soft:#cfc9bf; --ink-soft-2:#b9b2a7;
  --paper:#14120f; --paper-deep:#1d1a16; --line:#332e27; --red:#e07a63; --blue:#7fb6cc;
  --green:#6cc79f; --gold:#d9ab52; --white:#0d0b09; --surface:rgba(34,30,25,.7);
  --surface-strong:rgba(40,35,29,.94); --bar-bg:rgba(20,18,15,.95);
  --bg:radial-gradient(circle at 20% 8%, rgba(217,171,82,.10), transparent 55%), #14120f;
  --shadow:0 2px 14px rgba(0,0,0,.5); --tint:rgba(217,171,82,.14); --tint-strong:rgba(217,171,82,.28);}
body[data-theme="mist-blue"]{ --paper:#eef2f5; --paper-deep:#dde5ec; --line:#c2d0db;
  --ink:#16232c; --muted:#5c6b76; --ink-soft:#2c3d49; --ink-soft-2:#3d5061; --white:#f8fbfd;
  --surface:rgba(248,251,253,.7); --surface-strong:rgba(248,251,253,.92); --bar-bg:rgba(238,242,245,.95);
  --bg:radial-gradient(circle at 20% 8%, rgba(36,95,115,.10), transparent 55%), #eef2f5;
  --tint:rgba(36,95,115,.11); --tint-strong:rgba(36,95,115,.22);}
body[data-theme="forest-moss"]{ --paper:#eef1ea; --paper-deep:#dde4d6; --line:#c2cfb8;
  --ink:#1b2419; --muted:#5d6a58; --ink-soft:#33422f; --ink-soft-2:#44543f; --white:#f8fbf6;
  --surface:rgba(248,251,246,.7); --surface-strong:rgba(248,251,246,.92); --bar-bg:rgba(238,241,234,.95);
  --bg:radial-gradient(circle at 20% 8%, rgba(23,122,92,.11), transparent 55%), #eef1ea;
  --tint:rgba(23,122,92,.12); --tint-strong:rgba(23,122,92,.24);}
body[data-theme="clay-rust"]{ --paper:#f6ece6; --paper-deep:#ecdcd2; --line:#dcc2b3;
  --ink:#251a16; --muted:#75635b; --ink-soft:#3f2d26; --ink-soft-2:#503a31; --white:#fdf7f3;
  --surface:rgba(253,247,243,.7); --surface-strong:rgba(253,247,243,.92); --bar-bg:rgba(246,236,230,.95);
  --bg:radial-gradient(circle at 20% 8%, rgba(185,66,47,.10), transparent 55%), #f6ece6;
  --tint:rgba(185,66,47,.11); --tint-strong:rgba(185,66,47,.22);}
body[data-theme="cloud-grey"]{ --paper:#f2f2f2; --paper-deep:#e4e4e4; --line:#cdcdcd;
  --ink:#1c1c1c; --muted:#6b6b6b; --ink-soft:#383838; --ink-soft-2:#4a4a4a; --white:#fbfbfb;
  --surface:rgba(251,251,251,.72); --surface-strong:rgba(251,251,251,.94); --bar-bg:rgba(242,242,242,.95);
  --bg:radial-gradient(circle at 20% 8%, rgba(0,0,0,.04), transparent 55%), #f2f2f2;
  --shadow:0 2px 10px rgba(0,0,0,.06); --tint:rgba(0,0,0,.06); --tint-strong:rgba(0,0,0,.12);}
body[data-theme="gold-leaf"]{ --paper:#f7f1de; --paper-deep:#ebe0c4; --line:#d9c894;
  --ink:#241d10; --muted:#756646; --ink-soft:#3d331c; --ink-soft-2:#4f4326; --white:#fdfaef;
  --surface:rgba(253,250,239,.7); --surface-strong:rgba(253,250,239,.92); --bar-bg:rgba(247,241,222,.95);
  --bg:radial-gradient(circle at 20% 8%, rgba(184,137,47,.16), transparent 55%), #f7f1de;
  --tint:rgba(184,137,47,.15); --tint-strong:rgba(184,137,47,.3);}

*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:var(--font-body);background:var(--bg);color:var(--ink);line-height:1.9;font-size:16.5px}
a{color:var(--blue)}
.bar{position:sticky;top:0;z-index:60;background:var(--bar-bg);backdrop-filter:blur(8px);
  border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;
  gap:14px;padding:0 24px;height:60px;font-family:var(--font-display)}
.bar b{font-size:15px;cursor:pointer}
.tabs{display:flex;gap:4px;align-items:center;flex-wrap:wrap}
.tabs button,.tabs a{border:0;background:none;color:var(--muted);font:inherit;font-size:14px;
  padding:7px 13px;border-radius:8px;cursor:pointer;font-family:var(--font-display);text-decoration:none}
.tabs button:hover,.tabs a:hover{background:var(--tint);color:var(--ink)}
.tabs button[aria-selected="true"]{background:var(--tint-strong);color:var(--ink);font-weight:650}
.tp{position:relative}
.tp-trigger{border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:99px;
  padding:5px 12px;font:inherit;font-size:12.5px;cursor:pointer;font-family:var(--font-display)}
.tp-menu{position:absolute;right:0;top:38px;background:var(--surface-strong);border:1px solid var(--line);
  border-radius:10px;box-shadow:var(--shadow);padding:6px;display:none;min-width:128px;z-index:70}
.tp[data-open="1"] .tp-menu{display:block}
.tp-menu button{display:block;width:100%;text-align:left;border:0;background:none;color:var(--ink);
  padding:7px 10px;border-radius:6px;font:inherit;font-size:13px;cursor:pointer;font-family:var(--font-display)}
.tp-menu button:hover{background:var(--tint)}
.tp-menu button[aria-pressed="true"]{font-weight:700;background:var(--tint-strong)}

main{max-width:900px;margin:0 auto;padding:0 24px 80px}
.view{display:none;animation:fade .3s ease}
.view.on{display:block}
@keyframes fade{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}

.hero{display:flex;flex-direction:column;align-items:center;text-align:center;padding:60px 0 30px}
.avatar{width:130px;height:130px;border-radius:50%;object-fit:cover;border:3px solid var(--paper-deep);
  box-shadow:var(--shadow);background:var(--white)}
.hero h1{font-family:var(--font-display);font-size:35px;font-weight:600;margin-top:18px}
.hero .sub{color:var(--muted);margin-top:6px;font-size:15.5px}
.hero .mail{margin-top:12px;font-size:14px;font-family:var(--font-display)}
.hero .bio{max-width:660px;margin-top:20px;font-size:16.5px;color:var(--ink-soft);text-align:left;line-height:2}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;margin:26px 0 8px;width:100%}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px;text-align:center}
.stat .v{font-size:22px;font-weight:650;font-family:var(--font-display)}
.stat .l{font-size:12px;color:var(--muted);font-family:var(--font-display);margin-top:2px}
.jump{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin-top:22px;width:100%}
.jump button{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px;
  cursor:pointer;font:inherit;font-family:var(--font-display);text-align:left;color:var(--ink)}
.jump button:hover{background:var(--tint);transform:translateY(-2px)}
.jump button b{display:block;font-size:15.5px;margin-bottom:3px}
.jump button span{font-size:12.5px;color:var(--muted)}

h2.sec{font-family:var(--font-display);font-size:12.5px;letter-spacing:.16em;text-transform:uppercase;
  color:var(--red);margin:30px 0 16px;font-weight:700}
h2.sec:first-child{margin-top:8px}
.entry{display:grid;grid-template-columns:60px 1fr;gap:15px;padding:18px 0;border-bottom:1px solid var(--line)}
.entry:last-child{border-bottom:0}
.logo{width:48px;height:48px;border-radius:11px;display:grid;place-items:center;color:#fff;font-size:12px;
  font-weight:700;background:var(--ink);font-family:var(--font-display)}
.org{font-family:var(--font-display);font-weight:650;font-size:16.5px}
.meta2{color:var(--muted);font-size:13.5px;margin-top:2px}
.when2{color:var(--muted);font-size:13px;white-space:nowrap;font-family:var(--font-display)}
.trow{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
.entry ul{margin:10px 0 0 18px}
.entry li{margin:7px 0;font-size:15.5px;line-height:1.8;color:var(--ink-soft-2)}

.card{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:19px 21px;
  margin-bottom:14px;box-shadow:var(--shadow)}
.card h3{font-family:var(--font-display);font-size:18px;font-weight:650;margin-bottom:6px}
.card .kick{color:var(--green);font-size:12.5px;font-family:var(--font-display);font-weight:600;margin-bottom:8px}
.card p{color:var(--ink-soft-2);font-size:15.5px;margin-bottom:10px}
.card .more{display:none;margin-top:14px;padding-top:14px;border-top:1px dashed var(--line)}
.card.open .more{display:block}
.card .more h4{font-family:var(--font-display);font-size:14.5px;margin:15px 0 6px;color:var(--ink)}
.card .more p{font-size:14.8px;line-height:1.85}
.toggle{border:1px solid var(--line);background:var(--surface-strong);color:var(--ink);border-radius:99px;
  padding:7px 15px;font:inherit;font-size:13.5px;cursor:pointer;font-family:var(--font-display)}
.toggle:hover{background:var(--tint)}
.btnline{display:flex;gap:9px;flex-wrap:wrap;margin-top:6px}
.btnline a{border:1px solid var(--line);background:var(--surface-strong);color:var(--ink);
  border-radius:99px;padding:7px 15px;font-size:13.5px;font-family:var(--font-display);text-decoration:none}
.btnline a:hover{background:var(--tint);text-decoration:none}
.tag{display:inline-block;font-size:12px;background:var(--tint);color:var(--muted);padding:2px 9px;
  border-radius:99px;margin:3px 4px 0 0;font-family:var(--font-display)}
.note{font-size:13px;color:var(--muted);line-height:1.75;margin-top:9px}
table{width:100%;border-collapse:collapse;font-size:13.5px;margin:10px 0;font-family:var(--font-display);
  font-variant-numeric:tabular-nums}
th,td{padding:7px 8px;text-align:right;border-bottom:1px solid var(--line)}
th:first-child,td:first-child{text-align:left}
th{color:var(--muted);font-weight:600;font-size:12.5px}
.tscroll{overflow-x:auto}
.up{color:var(--red)} .down{color:var(--green)}

.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:14px}
.shot{background:var(--white);border:1px solid var(--line);border-radius:10px;overflow:hidden;cursor:zoom-in;
  box-shadow:var(--shadow);transition:transform .18s}
.shot:hover{transform:translateY(-3px)}
.shot img{width:100%;display:block;aspect-ratio:3/4;object-fit:cover;background:var(--paper-deep)}
.shot .cap{padding:9px 10px;font-size:12.5px;line-height:1.55;color:var(--ink-soft-2);font-family:var(--font-display)}
.shot .cap b{display:block;font-size:13px;color:var(--ink);font-weight:600;margin-bottom:2px}
.lb{position:fixed;inset:0;background:rgba(15,12,9,.93);display:none;z-index:200;align-items:center;
  justify-content:center;padding:26px;cursor:zoom-out}
.lb.on{display:flex}
.lb img{max-width:100%;max-height:88vh;border-radius:8px}
footer{text-align:center;color:var(--muted);font-size:13px;padding:32px 0 0;border-top:1px solid var(--line);
  font-family:var(--font-display);margin-top:30px}
@media(max-width:760px){
  .bar{height:auto;padding:10px 14px;flex-wrap:wrap;gap:8px}
  .tabs{gap:2px} .tabs button,.tabs a{padding:6px 10px;font-size:13px}
  main{padding:0 15px 60px}
  .hero{padding:34px 0 20px} .hero h1{font-size:26px}
  .entry{grid-template-columns:1fr} .logo{display:none}
}
@media print{ .bar{display:none} .view{display:block!important} .more{display:block!important} }
"""

HTML = """<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>刘柏廷 · Evo｜个人主页</title>
<meta name="description" content="刘柏廷 BoTing LIU：香港中文大学（深圳）统计学硕士在读，澳门科技大学工商管理（国际贸易）学士。项目含徕芬德国 GTM、债市与出海数据看板。">
<style>__CSS__</style></head>
<body data-theme="warm-paper">

<div class="bar">
  <b onclick="go('home')">刘柏廷 · Evo</b>
  <nav class="tabs">
    <button data-v="home" onclick="go('home')">首页</button>
    <button data-v="exp" onclick="go('exp')">经历</button>
    <button data-v="proj" onclick="go('proj')">项目</button>
    <button data-v="cert" onclick="go('cert')">证书</button>
    <a href="dashboard.html">数据看板</a>
    <span class="tp" id="tp" data-open="0">
      <button class="tp-trigger" id="tp-btn" aria-haspopup="true" aria-expanded="false">主题</button>
      <span class="tp-menu" id="tp-menu" role="menu"></span></span>
  </nav>
</div>

<main>
  <section class="view" id="v-home"></section>
  <section class="view" id="v-exp"></section>
  <section class="view" id="v-proj"></section>
  <section class="view" id="v-cert"></section>
</main>
<div class="lb" id="lb"><img id="lb-img" alt="证书放大"></div>

<script>
const IMG=__IMG__, D=__DATA__;
const THEMES=[["warm-paper","暖纸"],["ink-night","夜墨"],["mist-blue","雾蓝"],
  ["forest-moss","苔绿"],["clay-rust","陶土"],["cloud-grey","云灰"],["gold-leaf","金叶"]];
const TK="evo:theme", VK="evo:view";
function setTheme(t){document.body.dataset.theme=t;
  document.querySelectorAll("[data-pick]").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.pick===t)));
  try{localStorage.setItem(TK,t)}catch(e){}}
(function(){const m=document.getElementById("tp-menu");
  m.innerHTML=THEMES.map(([k,n])=>`<button data-pick="${k}" role="menuitem" aria-pressed="false">${n}</button>`).join("");
  let t="warm-paper";try{t=localStorage.getItem(TK)||"warm-paper"}catch(e){}setTheme(t);
  m.addEventListener("click",e=>{const b=e.target.closest("[data-pick]");if(b){setTheme(b.dataset.pick);ct();}});
  const tp=document.getElementById("tp"),btn=document.getElementById("tp-btn");
  function ct(){tp.dataset.open="0";btn.setAttribute("aria-expanded","false")}window.ct=ct;
  btn.addEventListener("click",e=>{e.stopPropagation();const o=tp.dataset.open==="1";
    tp.dataset.open=o?"0":"1";btn.setAttribute("aria-expanded",String(!o));});
  document.addEventListener("click",e=>{if(!tp.contains(e.target))ct();});})();

document.getElementById("v-home").innerHTML=`
  <div class="hero">
    <img class="avatar" src="${IMG.photo}" alt="刘柏廷">
    <h1>刘柏廷 · Evo</h1>
    <p class="sub">香港中文大学（深圳）统计学硕士在读 · 澳门科技大学工商管理（国际贸易）学士</p>
    <p class="mail"><a href="mailto:lbt2238516944@163.com">lbt2238516944@163.com</a></p>
    <p class="bio">${D.about}</p>
  </div>
  <div class="stats">${D.stats.map(s=>`<div class="stat"><div class="v">${s.v}</div><div class="l">${s.l}</div></div>`).join("")}</div>
  <div class="jump">
    <button onclick="go('exp')"><b>经历 →</b><span>教育背景与 5 段实习</span></button>
    <button onclick="go('proj')"><b>项目 →</b><span>4 个自己做过的研究项目</span></button>
    <button onclick="go('cert')"><b>证书 →</b><span>8 张证书原件</span></button>
    <button onclick="location.href='dashboard.html'"><b>数据看板 →</b><span>每日 12:00 自动更新</span></button>
  </div>`;

document.getElementById("v-exp").innerHTML=`
  <h2 class="sec">教育</h2>
  ${D.edu.map(e=>`<div class="entry">
    <div class="logo" style="background:${e.c}">${e.tag}</div>
    <div><div class="trow"><div>
      <div class="org">${e.org}</div><div class="meta2">${e.deg}</div>
      ${e.note?`<div class="meta2" style="margin-top:5px">${e.note}</div>`:""}
    </div><div class="when2">${e.when}</div></div></div></div>`).join("")}
  <h2 class="sec">实习经历</h2>
  ${D.career.map(c=>`<div class="entry">
    <div class="logo" style="background:${c.c}">${c.tag}</div>
    <div><div class="trow"><div>
      <div class="org">${c.org}</div><div class="meta2">${c.role}</div>
    </div><div class="when2">${c.when}</div></div>
    <ul>${c.pts.map(p=>`<li>${p}</li>`).join("")}</ul></div></div>`).join("")}
  <p class="note">${D.careerNote}</p>`;

document.getElementById("v-proj").innerHTML=`
  <h2 class="sec">项目经历</h2>
  ${D.projects.map((p,i)=>`<div class="card" id="pc${i}">
    <div class="kick">${p.kick}</div><h3>${p.title}</h3>
    <p>${p.sum}</p>
    <div>${p.tags.map(t=>`<span class="tag">${t}</span>`).join("")}</div>
    <div style="margin-top:11px"><button class="toggle" data-p="${i}">展开看做法与数据</button></div>
    ${p.links&&p.links.length?`<div class="btnline">${p.links.map(l=>`<a href="${l.href}" ${l.ext?'target="_blank" rel="noopener"':''}>${l.label}</a>`).join("")}</div>`:""}
    <div class="more">${p.body}</div>
  </div>`).join("")}`;

document.getElementById("v-cert").innerHTML=`
  <h2 class="sec">证书与荣誉</h2>
  <p class="note" style="font-size:14px;margin-bottom:16px">
    以下为证书原件扫描件，名称、等级、日期与编号均未修改，点击可放大。
  </p>
  <div class="grid" id="cg"></div>
  <p class="note">图片已压缩至网页尺寸（最长边 900px），原件保存在本地。</p>`;
const cg=document.getElementById("cg");
cg.innerHTML=D.certs.map((c,i)=>`<div class="shot" data-i="${i}" role="button" tabindex="0" aria-label="放大：${c.title}">
  <img src="${c.uri}" alt="${c.title}" loading="lazy">
  <div class="cap"><b>${c.title}</b>${c.date}　${c.no?("编号 "+c.no):""}</div></div>`).join("");
const lb=document.getElementById("lb"),lbI=document.getElementById("lb-img");
function op(i){lbI.src=D.certs[i].uri;lb.classList.add("on");}
cg.addEventListener("click",e=>{const s=e.target.closest(".shot");if(s)op(+s.dataset.i);});
cg.addEventListener("keydown",e=>{if(e.key==="Enter"||e.key===" "){const s=e.target.closest(".shot");
  if(s){e.preventDefault();op(+s.dataset.i);}}});
lb.addEventListener("click",()=>lb.classList.remove("on"));
document.addEventListener("keydown",e=>{if(e.key==="Escape")lb.classList.remove("on");});

document.addEventListener("click",e=>{
  const t=e.target.closest("[data-p]");
  if(t){const c=document.getElementById("pc"+t.dataset.p);const on=c.classList.toggle("open");
    t.textContent=on?"收起":"展开看做法与数据";}
});
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
    src = Path("/Users/evo/Desktop/校招/作品集/证件照.jpg")
    if not src.exists():
        return next(c["uri"] for c in IMG if c["key"] == "photo")
    im = Image.open(src).convert("RGB")
    w, h = im.size
    s = min(w, h)
    top = int((h - s) * 0.16)
    im = im.crop((0, top, s, top + s)).resize((520, 520), Image.LANCZOS)
    b = io.BytesIO()
    im.save(b, "JPEG", quality=84, optimize=True)
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
        return "<p class='note'>详情见增补包 customer-prioritization.html。</p>"
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
    """从徕芬 README 抽真实要点（不编造）。"""
    if not LAIFEN.exists():
        return "<p class='note'>徕芬项目详情见 laifen-gtm/dashboard.html。</p>"
    t = LAIFEN.read_text(encoding="utf-8", errors="ignore")
    # 抽取「项目背景与目标」「市场与品牌选择」「AI 应用部分」几节的要点
    out = []
    for kw in ["## 2. 项目背景与目标", "## 3. 市场与品牌选择", "## 4. AI 应用部分"]:
        i = t.find(kw)
        if i < 0:
            continue
        seg = t[i:i + 2600]
        seg = re.sub(r"^#+ .*$", "", seg, flags=re.M)
        seg = re.sub(r"\|[-: |]+\|", "", seg)
        seg = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", seg)
        seg = re.sub(r"[`*>　]", "", seg)
        lines = [l.strip() for l in seg.split("\n") if len(l.strip()) > 24]
        if lines:
            title = kw.replace("## ", "").split(".")[-1].strip()
            out.append(f"<h4>{title}</h4><p>{'　'.join(lines[:5])[:900]}</p>")
    return "".join(out) or "<p class='note'>徕芬项目详情见 laifen-gtm/dashboard.html。</p>"


def main() -> None:
    mk = SEA.get("market") or {}
    cn = (SEA.get("cn_brands") or [{}])[0]
    y10 = next((r for r in FIN["curve"]["rows"] if r["key"] == "10.0"), {})
    certs = [{"title": c["title"], "date": c["date"], "no": c["no"], "uri": c["uri"]}
             for c in IMG if c["key"] not in SKIP_KEYS]

    data = {
        "about": ("国际贸易本科，统计学硕士在读。实习覆盖银行、券商资管、公募渠道、"
                  "电商商务拓展与卖方研究，熟悉销售漏斗与渠道分析；"
                  "也习惯用程序把公开数据整理成每天自动刷新的看板。"
                  "做研究最较真的是口径：能核实的才写，拿不到的一律留空并注明。"),
        "stats": [
            {"v": f"{y10.get('now')}%" if y10.get("now") else "—", "l": "10 年期国债收益率"},
            {"v": f"{mk.get('bev_share')}%" if mk.get("bev_share") else "—", "l": "英国纯电份额"},
            {"v": "1,800+", "l": "德语评论样本（徕芬）"},
            {"v": "8", "l": "张证书原件"},
        ],
        "edu": [
            {"tag": "CUHK", "c": "#6b1020", "org": "香港中文大学（深圳）",
             "deg": "计算社会科学（统计学）理学硕士 · 深圳", "when": "2025.09 – 2027.06", "note": ""},
            {"tag": "MUST", "c": "#1a3c6e", "org": "澳门科技大学",
             "deg": "工商管理（国际贸易）学士 · 澳门", "when": "2022.09 – 2026.06",
             "note": "商学院院长优秀毕业生（2023/2024 学年，编号 D230B0182）"}],
        "career": [
            {"tag": "华福", "c": "#8a5a2b", "org": "华福证券 · 研究所", "role": "首席策略分析组",
             "when": "2026.07 – 至今", "pts": [
                 "维护 A 股、港股及宏观流动性日度跟踪体系，监测 PMI、社融、两融余额等指标。",
                 "梳理重要政策与宏观事件，提炼政策目标、受益方向与市场影响路径。",
                 "筹备策略路演与电话会议，捕捉客户关注的市场问题并反馈。"]},
            {"tag": "京东", "c": "#e21a1a", "org": "京东零售", "role": "商务拓展", "when": "2026.03 – 2026.07", "pts": [
                 "拆解线索到上线的转化数据、识别流失卡点，搭建城市预警机制，交付周期缩短约 30%。",
                 "高价值客户分层运营，挖掘竞对翻牌客户，提升 KA 与老商新店占比。",
                 "协同电销、工程、供应链中台，支撑 90+ 招商经理，团队执行力提升约 20%。"]},
            {"tag": "诺安", "c": "#0b3d91", "org": "诺安基金", "role": "华中业务部 · 渠道经理助理",
             "when": "2025.09 – 2026.03", "pts": [
                 "覆盖湖北、湖南、厦门、福建银行与券商渠道，输出周度销售报表和竞品分析。",
                 "用 Wind 做科技 AI / 半导体主题基金课件，路演培训超 200 人次。",
                 "搭建渠道效能评估模型，区域销售效率环比提升约 15%。"]},
            {"tag": "银河", "c": "#c4a35a", "org": "中国银河证券 · 银河金汇", "role": "固定收益 · 多资产运营",
             "when": "2024.06 – 2024.09", "pts": [
                 "为 200+ 企业财务数据建校验规则，处理效率提升约 30%，差错率压到 0.5% 以内。",
                 "参与多资产组合流动性压力测试与归因，完成 2 只产品季度调参回测。",
                 "协助亿元级固收 FOF 投后管理，路演材料支撑约 1000 万元募集。"]},
            {"tag": "成都", "c": "#0a6b4c", "org": "成都银行总行", "role": "财富经理助理",
             "when": "2023.06 – 2023.09", "pts": [
                 "对筹资企业做盈利、回报、营运、成长、资本结构与偿债分析，出具财务分析报告。",
                 "参与贷后监控流程优化，跟踪核心财务指标并提示风险。"]}],
        "careerNote": "以上百分比为实习期间的业务口径；若被追问分母与统计区间，我可以说明各自测算方式。",
        "projects": [
            {"kick": "出海 GTM · 标杆项目（含完整交互看板）",
             "title": "徕芬出海镜 · 德国高速吹风机市场进入监测",
             "sum": "AI 做数据处理层、人做决策层：处理 1,800+ 条德语用户评论、64 位 KOL 候选、"
                    "6 个竞品的 6 个月价格时序，输出市场测算 / 竞品格局 / 用户画像 / 渠道组合 / "
                    "上市节奏 / ROI 三情景，并用 Plotly 搭 5 模块自动更新看板。",
             "tags": ["出海", "GTM", "Python", "Plotly", "评论挖掘", "KOL 分层"],
             "links": [{"href": "laifen-gtm/dashboard.html", "label": "打开完整交互看板 →", "ext": False}],
             "body": laifen_body() + "<p class='note'>完整 5 模块看板（情感趋势 Treemap 下钻、"
                     "达人气泡分层、价格促销时间轴、渠道漏斗、文案五维评分）见上方按钮。</p>"},
            {"kick": "金融数据看板 · 每日 12:00 自动更新",
             "title": "金融之声 · 债市读数看板",
             "sum": "把国债收益率曲线、资金利率和央行公告做成每天自动刷新的看板，"
                    "面向公募、私募、理财子的机构销售。数据来自官方公开来源，每条都能点回原文。",
             "tags": ["中债", "资金面", "自动更新", "可追溯"],
             "links": [{"href": "dashboard.html#fin", "label": "在统一看板中查看 →", "ext": False}],
             "body": "<p>核心指标：国债收益率曲线（6M–30Y，含 1 周 / 1 月 / 3 月 / 1 年前对比）、"
                     "10Y−1Y 期限利差、DR001/DR007/FR007、Shibor、央行公开市场公告。</p>"
                     "<p class='note'>口径纪律：国债与地方政府债曲线不混用；DR 与 FR 不混用；"
                     "收益率变化不等于投资收益，不做任何收益预测或回测。</p>"},
            {"kick": "出海数据看板 · SMMT 官方注册数据",
             "title": "出海情报 · 英国电动车市场",
             "sum": "以 BYD DOLPHIN SURF 为对象，用 SMMT 官方注册数据建立市场基线，"
                    "并跟踪中国品牌在英国的注册表现。",
             "tags": ["SMMT", "英国", "中国品牌", "口径纪律"],
             "links": [{"href": "dashboard.html#sea", "label": "在统一看板中查看 →", "ext": False}],
             "body": "<p>核心指标：英国新乘用车注册量、纯电 BEV 份额与同比、车队 / 私人 / 公司自用渠道结构、"
                     "中国与新兴品牌注册排名、纯电车型 Top10、竞品官方规格。</p>"
                     "<p class='note'>注册量 ≠ 销量 ≠ 交付量；品牌级 ≠ 车型级。"
                     "BYD 官网价格与月供为前端动态渲染，拿不到，故留空不填。</p>"},
            {"kick": "客户经营项目 · 有完整过程与结果",
             "title": "银行营销客户筛选与跟进资源分配",
             "sum": "名单很长、销售精力有限。先排出跟进优先级，再用实际做决定的条件检验，"
                    "最后转成可选名单与名额方案，并说明扩大覆盖要付出什么代价。",
             "tags": ["客户分层", "跟进优先级", "名额分配", "可复现"],
             "links": [],
             "body": cust_body()},
        ],
        "certs": certs,
    }

    html = (HTML.replace("__CSS__", CSS)
                .replace("__IMG__", json.dumps({"photo": make_avatar()}, ensure_ascii=False))
                .replace("__DATA__", json.dumps(data, ensure_ascii=False)))
    evo = ROOT / "evo-site"
    if not evo.exists():
        evo.mkdir(parents=True)
    out = evo / "index.html"
    out.write_text(html, encoding="utf-8")
    log_line(f"主站已生成：{out.relative_to(ROOT)}（{len(html)/1048576:.2f} MB）")
    log_line(f"  视图 4 个（首页/经历/项目/证书）· 项目 {len(data['projects'])} 个"
             f" · 证书 {len(certs)} 张")


if __name__ == "__main__":
    main()
