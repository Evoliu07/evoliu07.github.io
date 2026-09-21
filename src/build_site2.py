"""
生成「单文件个人主页」evo-site/index.html（v2）

v2 改动：
  1. 头像用证件照裁方图
  2. 去掉含本人照片的「院榜电子版」
  3. 经历排版：右侧索引列 + 左侧内容区（点哪条显示哪条）
  4. 新增统一数据看板：KPI / 曲线对比开关 / 自动轮播 / 时间口径切换 / 多图多表

用法： python src/build_site2.py
"""
from __future__ import annotations

import base64
import io
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, log_line                                   # noqa: E402
from PIL import Image                                               # noqa: E402

IMG = json.loads((ROOT / "build" / "images.json").read_text(encoding="utf-8"))
FIN = json.loads((ROOT / "data" / "dash" / "dashboard.json").read_text(encoding="utf-8"))
SEA = json.loads((ROOT / "data" / "dash" / "overseas.json").read_text(encoding="utf-8"))
CUST = Path("/Users/evo/WorkBuddy/2026-09-11-23-22-58/_incoming/experiences/"
            "customer-prioritization.html")
DROP_KEYS = {"cert_college_rank"}          # 含本人证件照，不展示

THEMES_CSS = """
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
"""

CSS = """
:root{
  --ink:#171411; --muted:#6d6258; --ink-soft:#3a332c; --ink-soft-2:#4a4239;
  --paper:#f8f2e7; --paper-deep:#ece1cf; --line:#d8c8af;
  --red:#b9422f; --blue:#245f73; --green:#177A5C; --gold:#B8892F;
  --white:#fffaf0; --surface:rgba(255,250,240,.62); --surface-strong:rgba(255,250,240,.9);
  --bar-bg:rgba(248,242,231,.94);
  --font-body:"Songti SC","Noto Serif SC","Noto Serif CJK SC",Georgia,serif;
  --font-display:"PingFang SC","Microsoft YaHei",Helvetica,sans-serif;
  --bg:radial-gradient(circle at 20% 8%, rgba(184,137,47,.10), transparent 55%),
       radial-gradient(circle at 82% 0%, rgba(36,95,115,.08), transparent 45%), #f8f2e7;
  --shadow:0 2px 10px rgba(60,45,25,.07);
  --tint:rgba(184,137,47,.13); --tint-strong:rgba(184,137,47,.26);
}
""" + THEMES_CSS + """
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:var(--font-body);background:var(--bg);color:var(--ink);line-height:1.9;font-size:16.5px}
a{color:var(--blue)}
.bar{position:sticky;top:0;z-index:50;background:var(--bar-bg);backdrop-filter:blur(8px);
  border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;
  gap:14px;padding:0 24px;height:58px;font-family:var(--font-display)}
.bar b{font-size:15px}
.bar nav{display:flex;gap:16px;font-size:13.5px;align-items:center;flex-wrap:wrap}
.bar nav a{color:var(--muted)} .bar nav a:hover{color:var(--ink);text-decoration:none}
.tp{position:relative}
.tp-trigger{border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:99px;
  padding:5px 12px;font:inherit;font-size:12.5px;cursor:pointer;font-family:var(--font-display)}
.tp-menu{position:absolute;right:0;top:38px;background:var(--surface-strong);border:1px solid var(--line);
  border-radius:10px;box-shadow:var(--shadow);padding:6px;display:none;min-width:130px;z-index:60}
.tp[data-open="1"] .tp-menu{display:block}
.tp-menu button{display:block;width:100%;text-align:left;border:0;background:none;color:var(--ink);
  padding:7px 10px;border-radius:6px;font:inherit;font-size:13px;cursor:pointer;font-family:var(--font-display)}
.tp-menu button:hover{background:var(--tint)}
.tp-menu button[aria-pressed="true"]{font-weight:700;background:var(--tint-strong)}
main{max-width:1080px;margin:0 auto;padding:0 24px 90px}
.hero{display:flex;flex-direction:column;align-items:center;text-align:center;padding:54px 0 30px}
.avatar{width:130px;height:130px;border-radius:50%;object-fit:cover;border:3px solid var(--paper-deep);
  box-shadow:var(--shadow);background:var(--white)}
.hero h1{font-family:var(--font-display);font-size:34px;font-weight:600;margin-top:18px}
.hero .sub{color:var(--muted);margin-top:6px;font-size:15px}
.hero .mail{margin-top:12px;font-size:14px;font-family:var(--font-display)}
.two{display:grid;grid-template-columns:1fr 296px;gap:32px;align-items:start;padding:22px 0 8px}
.side{position:sticky;top:74px;max-height:calc(100vh - 96px);overflow-y:auto;border:1px solid var(--line);
  border-radius:14px;background:var(--surface);padding:6px}
.side h3{font-family:var(--font-display);font-size:11.5px;letter-spacing:.14em;text-transform:uppercase;
  color:var(--muted);padding:13px 12px 5px;font-weight:700}
.side h3:first-child{padding-top:8px}
.side button{display:block;width:100%;text-align:left;border:0;background:none;color:var(--ink-soft);
  padding:8px 12px;border-radius:8px;font:inherit;font-size:14.5px;cursor:pointer;
  font-family:var(--font-display);line-height:1.5}
.side button small{display:block;color:var(--muted);font-size:12px;font-weight:400}
.side button:hover{background:var(--tint)}
.side button[aria-pressed="true"]{background:var(--tint-strong);color:var(--ink);font-weight:650}
.pane{min-height:400px;padding-right:6px}
.pane .kick{color:var(--green);font-size:13px;font-family:var(--font-display);font-weight:600;margin-bottom:8px}
.pane h2{font-family:var(--font-display);font-size:23px;font-weight:650;margin-bottom:6px}
.pane .when{color:var(--muted);font-size:13.5px;font-family:var(--font-display);margin-bottom:14px}
.pane .body{font-size:16px;line-height:1.95;color:var(--ink-soft)}
.pane .body p{margin-bottom:12px}
.pane .body h4{font-family:var(--font-display);font-size:15px;margin:20px 0 8px;color:var(--ink)}
.pane ul{margin:0 0 0 18px}
.pane li{margin:9px 0;font-size:15.8px;line-height:1.85;color:var(--ink-soft-2)}
section{padding:34px 0;border-top:1px solid var(--line)}
.shead{font-family:var(--font-display);font-size:13px;letter-spacing:.16em;text-transform:uppercase;
  color:var(--red);margin-bottom:14px;font-weight:700}
table{width:100%;border-collapse:collapse;font-size:13.5px;margin:10px 0;font-family:var(--font-display);
  font-variant-numeric:tabular-nums}
th,td{padding:7px 8px;text-align:right;border-bottom:1px solid var(--line)}
th:first-child,td:first-child{text-align:left}
th{color:var(--muted);font-weight:600;font-size:12.5px}
.up{color:var(--red)} .down{color:var(--green)}
.tscroll{overflow-x:auto}
.note{font-size:13px;color:var(--muted);line-height:1.75;margin-top:10px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:12px;margin-bottom:16px}
.kpi{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:14px 16px}
.kpi .lb{font-size:12px;color:var(--muted);font-family:var(--font-display)}
.kpi .vl{font-size:23px;font-weight:650;margin-top:3px;font-family:var(--font-display)}
.kpi .ch{font-size:12px;margin-top:2px;font-family:var(--font-display)}
.ctrl{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:12px 0;font-family:var(--font-display)}
.ctrl button{border:1px solid var(--line);background:var(--surface);color:var(--ink-soft);
  border-radius:99px;padding:6px 13px;font:inherit;font-size:13px;cursor:pointer}
.ctrl button:hover{background:var(--tint)}
.ctrl button[aria-pressed="true"]{background:var(--tint-strong);color:var(--ink);font-weight:650}
.ctrl .sp{flex:1}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:16px 18px;
  margin-bottom:15px;box-shadow:var(--shadow)}
.panel h4{font-family:var(--font-display);font-size:15px;margin-bottom:10px;font-weight:650}
.chart{width:100%;overflow-x:auto}
.barrow{display:grid;grid-template-columns:92px 1fr 118px;gap:10px;align-items:center;font-size:13.5px;
  margin:6px 0;font-family:var(--font-display)}
.barbg{height:19px;background:var(--tint);border-radius:5px;overflow:hidden}
.barbg i{display:block;height:100%;background:linear-gradient(90deg,var(--green),var(--blue));
  border-radius:5px;transition:width .5s}
.barnum{text-align:right;font-variant-numeric:tabular-nums;color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(158px,1fr));gap:14px}
.shot{background:var(--white);border:1px solid var(--line);border-radius:10px;overflow:hidden;
  cursor:zoom-in;box-shadow:var(--shadow);transition:transform .18s}
.shot:hover{transform:translateY(-3px)}
.shot img{width:100%;display:block;aspect-ratio:3/4;object-fit:cover;background:var(--paper-deep)}
.shot .cap{padding:9px 10px;font-size:12.5px;line-height:1.55;color:var(--ink-soft-2);
  font-family:var(--font-display)}
.shot .cap b{display:block;font-size:13px;color:var(--ink);font-weight:600;margin-bottom:2px}
.lb{position:fixed;inset:0;background:rgba(15,12,9,.93);display:none;z-index:200;align-items:center;
  justify-content:center;padding:26px;cursor:zoom-out}
.lb.on{display:flex}
.lb img{max-width:100%;max-height:88vh;border-radius:8px}
footer{text-align:center;color:var(--muted);font-size:13px;padding:34px 0 0;border-top:1px solid var(--line);
  font-family:var(--font-display)}
@media(max-width:900px){
  .two{grid-template-columns:1fr;gap:18px}
  .side{position:static;max-height:none}
  .bar{height:auto;padding:10px 14px;flex-wrap:wrap}
  .bar nav{gap:11px;font-size:12.5px}
  main{padding:0 15px 60px}
  .hero{padding:32px 0 20px} .hero h1{font-size:26px}
  .pane h2{font-size:20px} .pane{min-height:0}
}
@media print{ .bar,.tp,.side{display:none} .two{grid-template-columns:1fr} }
"""

HTML = """<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>刘柏廷 · Evo｜个人主页</title>
<meta name="description" content="刘柏廷 BoTing LIU：香港中文大学（深圳）统计学硕士在读，澳门科技大学工商管理（国际贸易）学士。">
<style>__CSS__</style></head>
<body data-theme="warm-paper">
<div class="bar">
  <b>刘柏廷 · Evo</b>
  <nav><a href="#top">首页</a><a href="#exp">经历</a><a href="#dash">数据看板</a>
    <a href="#certs">证书</a>
    <span class="tp" id="tp" data-open="0">
      <button class="tp-trigger" id="tp-btn" aria-haspopup="true" aria-expanded="false">主题</button>
      <span class="tp-menu" id="tp-menu" role="menu"></span></span></nav>
</div>
<main id="top">
  <div class="hero">
    <img class="avatar" id="avatar" alt="刘柏廷">
    <h1>刘柏廷 · Evo</h1>
    <p class="sub">香港中文大学（深圳）统计学硕士在读</p>
    <p class="mail"><a href="mailto:lbt2238516944@163.com">lbt2238516944@163.com</a></p>
  </div>
  <div class="two" id="exp">
    <div class="pane" id="pane"></div>
    <aside class="side" id="side"></aside>
  </div>
  <section id="dash">
    <div class="shead">数据看板</div>
    <p class="note" style="margin-bottom:14px;font-size:14px">
      三个项目的数据合在一处：债市（中债 / 中国货币网 / 央行）与英国车市（SMMT）。
      可切换曲线对比基准、开自动轮播、切换「当月 / 年初至今」。数据每日 12:00 自动刷新，全部可点回官方原文。
    </p>
    <div id="dashbox"></div>
  </section>
  <section id="certs">
    <div class="shead">证书与荣誉</div>
    <p class="note" style="margin-bottom:16px;font-size:14px">
      证书原件扫描件，名称、等级、日期与编号均未修改，点击可放大。
    </p>
    <div class="grid" id="cert-grid"></div>
    <p class="note">图片已压缩至网页尺寸（最长边 900px），原件保存在本地。
      「商学院院长优秀生榜」已在教育经历中列明；该榜单电子版含本人证件照，故不在此展示。</p>
  </section>
  <footer>© Liu Boting · Evo　｜　单文件静态页面，无外部依赖、无追踪脚本</footer>
</main>
<div class="lb" id="lb"><img id="lb-img" alt="证书放大图"></div>
<script>
const IMG=__IMG__, DATA=__DATA__;
const THEMES=[["warm-paper","暖纸"],["ink-night","夜墨"],["mist-blue","雾蓝"],
              ["forest-moss","苔绿"],["clay-rust","陶土"],["cloud-grey","云灰"],["gold-leaf","金叶"]];
const KEY="evo:theme";
function setTheme(t){document.body.dataset.theme=t;
  document.querySelectorAll("[data-pick]").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.pick===t)));
  try{localStorage.setItem(KEY,t)}catch(e){}}
(function(){const menu=document.getElementById("tp-menu");
  menu.innerHTML=THEMES.map(([k,n])=>`<button data-pick="${k}" role="menuitem" aria-pressed="false">${n}</button>`).join("");
  let t="warm-paper";try{t=localStorage.getItem(KEY)||"warm-paper"}catch(e){}setTheme(t);
  menu.addEventListener("click",e=>{const b=e.target.closest("[data-pick]");if(b){setTheme(b.dataset.pick);closeTp();}});
  const tp=document.getElementById("tp"),btn=document.getElementById("tp-btn");
  function closeTp(){tp.dataset.open="0";btn.setAttribute("aria-expanded","false")}window.closeTp=closeTp;
  btn.addEventListener("click",e=>{e.stopPropagation();const o=tp.dataset.open==="1";
    tp.dataset.open=o?"0":"1";btn.setAttribute("aria-expanded",String(!o));});
  document.addEventListener("click",e=>{if(!tp.contains(e.target))closeTp();});})();
document.getElementById("avatar").src=IMG.photo;

/* ---- 右侧索引 + 左侧内容 ---- */
const ITEMS=[];
DATA.edu.forEach(e=>ITEMS.push({g:"教育",t:e.org,s:e.deg,b:eduB(e)}));
DATA.career.forEach(c=>ITEMS.push({g:"实习",t:c.org,s:c.role,b:carB(c)}));
DATA.projects.forEach(p=>ITEMS.push({g:"项目",t:p.title,s:p.kick,b:proB(p)}));
function eduB(e){return `<div class="kick">教育</div><h2>${e.org}</h2>
  <div class="when">${e.deg}　|　${e.when}</div>
  <div class="body">${e.note?`<p>${e.note}</p>`:""}<p>${e.desc||""}</p></div>`}
function carB(c){return `<div class="kick">${c.tag}　${c.when}</div><h2>${c.org}</h2>
  <div class="when">${c.role}</div><div class="body"><ul>${c.pts.map(p=>`<li>${p}</li>`).join("")}</ul>
  <p class="note">${DATA.careerNote}</p></div>`}
function proB(p){return `<div class="kick">${p.kick}</div><h2>${p.title}</h2>
  <div class="body"><p>${p.sum}</p>${p.body}</div>`}
let cur=0;
function renderSide(){let h="",last="";
  ITEMS.forEach((it,i)=>{if(it.g!==last){h+=`<h3>${it.g}</h3>`;last=it.g;}
    h+=`<button data-i="${i}" aria-pressed="${i===cur}">${it.t}<small>${it.s}</small></button>`;});
  document.getElementById("side").innerHTML=h;}
function show(i){cur=i;document.getElementById("pane").innerHTML=ITEMS[i].b;renderSide();}
document.getElementById("side").addEventListener("click",e=>{
  const b=e.target.closest("[data-i]");if(b)show(+b.dataset.i);});
show(0);

/* ---- 数据看板 ---- */
const F=DATA.fin,S=DATA.sea;
const nf=(v,d=2)=>(v===null||v===undefined)?"—":Number(v).toFixed(d);
const n0=v=>(v===null||v===undefined)?"—":Math.round(v).toLocaleString("en-GB");
const bpv=v=>(v===null||v===undefined)?"—":((v>0?"+":"")+Number(v).toFixed(1)+"bp");
const cc=v=>(v===null||v===undefined)?"":(v>0.05?"up":(v<-0.05?"down":""));
const HIS=F.history; let showH=new Set(HIS.map(h=>h.label)); let timer=null,ai=0,seaV="month";
function line(series,opt={}){const W=opt.w||820,H=opt.h||250,P={t:14,r:14,b:28,l:42};
  const all=series.filter(s=>s.on).flatMap(s=>s.pts.map(p=>p.y)).filter(v=>v!=null);
  if(!all.length)return '<div class="note">（无可绘制数据）</div>';
  let mn=Math.min(...all),mx=Math.max(...all);const pad=(mx-mn)*0.14||0.05;mn-=pad;mx+=pad;
  const n=Math.max(...series.map(s=>s.pts.length));
  const X=i=>P.l+(W-P.l-P.r)*(i/(n-1||1)),Y=v=>P.t+(H-P.t-P.b)*(1-(v-mn)/(mx-mn||1));
  let g="";
  for(let k=0;k<=3;k++){const v=mn+(mx-mn)*k/3,y=Y(v);
    g+=`<line x1="${P.l}" y1="${y}" x2="${W-P.r}" y2="${y}" stroke="var(--line)"/>`
      +`<text x="${P.l-6}" y="${y+4}" text-anchor="end" font-size="10.5" fill="var(--muted)">${v.toFixed(2)}</text>`;}
  series.forEach(s=>{if(!s.on)return;
    const pts=s.pts.map((p,i)=>p.y==null?null:`${X(i)},${Y(p.y)}`).filter(Boolean);
    if(pts.length)g+=`<polyline fill="none" stroke="${s.color}" stroke-width="2.3" points="${pts.join(' ')}"/>`;
    s.pts.forEach((p,i)=>{if(p.y!=null)g+=`<circle cx="${X(i)}" cy="${Y(p.y)}" r="2.8" fill="${s.color}"/>`;});});
  const labs=series[0].pts.map((p,i)=>
    `<text x="${X(i)}" y="${H-8}" text-anchor="middle" font-size="10.5" fill="var(--muted)">${p.x}</text>`).join("");
  return `<svg viewBox="0 0 ${W} ${H}" width="100%" style="min-width:600px">${g}${labs}</svg>`;}
function kpis(){const y=F.rows.find(r=>r.key==="10.0")||{},dr=F.money.FDR007||{};
  const sh=F.shape["10Y-1Y"],sq=F.shape["10Y-1Y_3个月前"],mk=S.market||{},cn=(S.cn_brands||[])[0];
  return `<div class="kpis">
   <div class="kpi"><div class="lb">10 年期国债</div><div class="vl">${nf(y.now)}%</div>
     <div class="ch ${cc(y.m1_bp)}">月 ${bpv(y.m1_bp)}　年 ${bpv(y.y1_bp)}</div></div>
   <div class="kpi"><div class="lb">10Y − 1Y 利差</div><div class="vl">${nf(sh,3)}</div>
     <div class="ch">3 个月前 ${nf(sq,3)}</div></div>
   <div class="kpi"><div class="lb">DR007</div><div class="vl">${nf(dr.value)}%</div>
     <div class="ch ${cc(dr.chg_bp)}">较前值 ${bpv(dr.chg_bp)}</div></div>
   <div class="kpi"><div class="lb">英国纯电份额</div><div class="vl">${nf(mk.bev_share,1)}%</div>
     <div class="ch ${cc(mk.bev_yoy)}">同比 ${bpv(mk.bev_yoy)}</div></div>
   <div class="kpi"><div class="lb">英国当月注册</div><div class="vl">${n0(mk.total_month)}</div>
     <div class="ch">纯电 ${n0(mk.bev_month)} 辆</div></div>
   <div class="kpi"><div class="lb">中国品牌首位</div><div class="vl">${cn?cn.brand:"—"}</div>
     <div class="ch ${cc(cn&&cn.yoy)}">${cn?n0(cn.units)+" 辆 "+bpv(cn.yoy):""}</div></div></div>`;}
function ctrl(){return `<div class="ctrl"><b style="font-size:13px;color:var(--muted)">曲线对比</b>
   ${HIS.map(h=>`<button data-h="${h.label}" aria-pressed="${showH.has(h.label)}">${h.label}</button>`).join("")}
   <span class="sp"></span><button id="auto" aria-pressed="false">▶ 自动轮播</button>
   <button id="allh">全选</button></div>
   <div class="ctrl"><b style="font-size:13px;color:var(--muted)">英国口径</b>
   <button data-v="month" aria-pressed="${seaV==="month"}">当月</button>
   <button data-v="ytd" aria-pressed="${seaV==="ytd"}">年初至今</button>
   <span class="sp"></span><span style="font-size:12.5px;color:var(--muted)">数据日期 ${F.date}</span></div>`;}
function curP(){const base={name:"当前",color:"var(--red)",on:true,pts:F.rows.map(r=>({x:r.tenor,y:r.now}))};
  const o=HIS.map((h,i)=>({name:h.label,color:["var(--blue)","var(--green)","var(--gold)","var(--muted)"][i%4],
    on:showH.has(h.label),pts:F.rows.map(r=>({x:r.tenor,y:r[h.label]??null}))}));
  return `<div class="panel"><h4>国债收益率曲线（中债 · 银行间 · 到期收益率 %）</h4>
   <div class="chart">${line([base,...o],{h:262})}</div>
   <div class="note">点上方对比基准开关曲线，或按「自动轮播」自动依次高亮各时点。</div></div>`;}
function curT(){let h='<div class="panel"><h4>各期限明细与变动</h4><div class="tscroll"><table><tr><th>期限</th><th>当前</th>'
  +HIS.filter(x=>showH.has(x.label)).map(x=>`<th>${x.label}</th>`).join("")
  +'<th>周变动</th><th>月变动</th><th>年变动</th></tr>';
  F.rows.forEach(r=>{h+=`<tr><td><b>${r.tenor}</b></td><td>${nf(r.now)}</td>`
    +HIS.filter(x=>showH.has(x.label)).map(x=>`<td>${nf(r[x.label])}</td>`).join("")
    +`<td class="${cc(r.w1_bp)}">${bpv(r.w1_bp)}</td><td class="${cc(r.m1_bp)}">${bpv(r.m1_bp)}</td>`
    +`<td class="${cc(r.y1_bp)}">${bpv(r.y1_bp)}</td></tr>`;});
  return h+'</table></div><div class="note">1bp = 0.01 个百分点；红=上行，绿=下行。</div></div>';}
function monP(){if(!F.dr.length)return"";
  return `<div class="panel"><h4>资金面：DR007 近期走势</h4>
   <div class="chart">${line([{name:"DR007",color:"var(--red)",on:true,
     pts:F.dr.map(p=>({x:p.date.slice(5),y:p.value}))}],{h:196})}</div>
   <div class="note">DR007＝存款类机构质押式回购加权利率（7 天）；与 FR007（全市场）不混用。</div></div>`;}
const LB={FLEET:"车队",PRIVATE:"私人",BUSINESS:"公司自用",BEV:"纯电",PHEV:"插混",HEV:"混动",
          PETROL:"汽油",DIESEL:"柴油"};
function seaP(){const ch=(seaV==="ytd"&&S.channelYtd&&S.channelYtd.length)?S.channelYtd:S.channel;
  const pt=(seaV==="ytd"&&S.powertrainYtd&&S.powertrainYtd.length)?S.powertrainYtd:S.powertrain;
  const a=Math.max(...ch.map(x=>x.share||0),1),b=Math.max(...pt.map(x=>x.share||0),1);
  return `<div class="panel"><h4>英国市场结构（SMMT · ${seaV==="ytd"?"年初至今":"当月"}）</h4>
   <div style="font-size:13px;color:var(--muted);margin-bottom:4px">渠道</div>
   ${ch.map(c=>`<div class="barrow"><span>${LB[c.key]||c.key}</span>
     <span class="barbg"><i style="width:${((c.share||0)/a*100).toFixed(1)}%"></i></span>
     <span class="barnum">${nf(c.share,1)}%　${n0(c.units)} 辆</span></div>`).join("")}
   <div style="font-size:13px;color:var(--muted);margin:12px 0 4px">动力类型</div>
   ${pt.map(c=>`<div class="barrow"><span>${LB[c.key]||c.key}</span>
     <span class="barbg"><i style="width:${((c.share||0)/b*100).toFixed(1)}%"></i></span>
     <span class="barnum">${nf(c.share,1)}%　${n0(c.units)} 辆</span></div>`).join("")}
   <div class="note">分母＝英国新乘用车<b>注册</b>量。注册量 ≠ 销量 ≠ 交付量。</div></div>`;}
function brP(){const l=(S.cn_brands||[]).slice(0,10);if(!l.length)return"";
  const m=Math.max(...l.map(x=>x.units||0),1);
  return `<div class="panel"><h4>中国与新兴品牌 · 英国注册（当月）</h4>
   ${l.map(x=>`<div class="barrow"><span>${x.brand}</span>
     <span class="barbg"><i style="width:${((x.units||0)/m*100).toFixed(1)}%"></i></span>
     <span class="barnum ${cc(x.yoy)}">${n0(x.units)}　${bpv(x.yoy)}</span></div>`).join("")}
   <div class="note">品牌级、含全部动力类型，<b>不能当作单一车型销量</b>。</div></div>`;}
function bevP(){if(!(S.bev_top10||[]).length)return"";
  return `<div class="panel"><h4>纯电车型 Top10（当月）</h4><div class="tscroll"><table>
   <tr><th>#</th><th>车型</th><th>注册（辆）</th></tr>
   ${S.bev_top10.map(x=>`<tr><td>${x.rank}</td><td>${x.model}</td><td>${n0(x.units)}</td></tr>`).join("")}
   </table></div><div class="note">SMMT 免费页<b>只公开 Top10</b>；
   研究对象 BYD DOLPHIN SURF 未进前十，故本页<b>不给它的车型级数字</b>。</div></div>`;}
function omoP(){if(!(F.omo||[]).length)return"";
  return `<div class="panel"><h4>央行公开市场业务交易公告</h4><ul style="margin-left:18px">
   ${F.omo.map(o=>`<li style="font-size:14.5px;margin:6px 0">
     <a href="${o.url}" target="_blank" rel="noopener">${o.title}</a></li>`).join("")}</ul>
   <div class="note">只列标题与原文链接；<b>净投放需同时核对投放与到期两侧</b>，未自动计算。</div></div>`;}
function srcP(){let h='<div class="panel"><h4>数据来源与口径纪律</h4><ul style="margin-left:18px">';
  (F.sources||[]).forEach(s=>h+=`<li style="font-size:14px;margin:5px 0"><code>${s.id}</code> ${s.name} —
    <a href="${s.url}" target="_blank" rel="noopener">原文</a></li>`);
  return h+'</ul><div class="note">全部为<b>单一权威来源，尚未独立交叉验证</b>。'
    +'国债与地方政府债曲线不混用；DR 与 FR 不混用；<b>收益率变化不等于投资收益</b>，'
    +'本页不做任何收益预测或回测。</div></div>';}
function paint(){document.getElementById("dashbox").innerHTML=
  kpis()+ctrl()+curP()+curT()+monP()+seaP()+brP()+bevP()+omoP()+srcP();}
document.getElementById("dashbox").addEventListener("click",e=>{
  const h=e.target.closest("[data-h]");
  if(h){const k=h.dataset.h;showH.has(k)?showH.delete(k):showH.add(k);paint();return;}
  const v=e.target.closest("[data-v]");
  if(v){seaV=v.dataset.v;paint();return;}
  if(e.target.id==="allh"){showH=new Set(HIS.map(x=>x.label));paint();return;}
  if(e.target.id==="auto"){const b=document.getElementById("auto");
    if(timer){clearInterval(timer);timer=null;return;}
    timer=setInterval(()=>{ai=(ai+1)%(HIS.length+1);
      showH=ai===0?new Set(HIS.map(x=>x.label)):new Set([HIS[ai-1].label]);
      paint();const b2=document.getElementById("auto");
      if(b2){b2.setAttribute("aria-pressed","true");b2.textContent="⏸ 停止轮播";}},2200);
    b.setAttribute("aria-pressed","true");b.textContent="⏸ 停止轮播";}});
paint();

/* ---- 证书 ---- */
const lb=document.getElementById("lb"),lbI=document.getElementById("lb-img");
document.getElementById("cert-grid").innerHTML=DATA.certs.map((c,i)=>`
  <div class="shot" data-i="${i}" role="button" tabindex="0" aria-label="放大：${c.title}">
   <img src="${c.uri}" alt="${c.title}" loading="lazy">
   <div class="cap"><b>${c.title}</b>${c.date}　${c.no?("编号 "+c.no):""}</div></div>`).join("");
function openL(i){lbI.src=DATA.certs[i].uri;lb.classList.add("on");}
document.getElementById("cert-grid").addEventListener("click",e=>{
  const s=e.target.closest(".shot");if(s)openL(+s.dataset.i);});
document.getElementById("cert-grid").addEventListener("keydown",e=>{
  if(e.key==="Enter"||e.key===" "){const s=e.target.closest(".shot");
    if(s){e.preventDefault();openL(+s.dataset.i);}}});
lb.addEventListener("click",()=>lb.classList.remove("on"));
document.addEventListener("keydown",e=>{if(e.key==="Escape")lb.classList.remove("on");});
</script></body></html>
"""


def make_avatar() -> str:
    src = Path("/Users/evo/Desktop/校招/作品集/证件照.jpg")
    if not src.exists():
        return next(c["uri"] for c in IMG if c["key"] == "photo")
    im = Image.open(src).convert("RGB")
    w, h = im.size
    s = min(w, h)
    top = int((h - s) * 0.16)          # 证件照人脸偏上，方切略微上移
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
    o = ""
    if len(parts) < 3:
        return f"<p>{strip_tags(body)[:1200]}</p>"
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


def main() -> None:
    hist = [{"label": h["label"], "date": h["date"]}
            for h in FIN["curve"].get("history_labels", [])]
    fin = {"date": FIN["meta"]["data_date"], "rows": FIN["curve"]["rows"], "history": hist,
           "shape": FIN.get("shape") or {}, "money": FIN.get("money") or {},
           "dr": FIN.get("dr_series") or [], "omo": FIN.get("omo") or [],
           "sources": [{"id": k, "name": v["name"], "url": v["url"]}
                       for k, v in (FIN.get("sources") or {}).items()]}
    # 英国：当月 + 年初至今（年初至今用同一套占比口径，来源为 SMMT 年累计列）
    sea = {"market": SEA.get("market") or {},
           "powertrain": SEA.get("powertrain") or [],
           "powertrainYtd": SEA.get("powertrainYtd") or [],
           "channel": SEA.get("channel") or [],
           "channelYtd": SEA.get("channelYtd") or [],
           "cn_brands": SEA.get("cn_brands") or [],
           "bev_top10": SEA.get("bev_top10") or []}

    certs = [{"title": c["title"], "date": c["date"], "no": c["no"], "uri": c["uri"]}
             for c in IMG if c["key"] != "photo" and c["key"] not in DROP_KEYS]

    data = {
        "edu": [
            {"org": "香港中文大学（深圳）", "deg": "计算社会科学（统计学）理学硕士 · 深圳",
             "when": "2025.09 – 2027.06", "note": "", "desc": "统计学方向，目前在读。"},
            {"org": "澳门科技大学", "deg": "工商管理（国际贸易）学士 · 澳门",
             "when": "2022.09 – 2026.06",
             "note": "商学院院长优秀毕业生（2023/2024 学年，证书编号 D230B0182）",
             "desc": "国际贸易方向，入选商学院院长优秀生榜。"}],
        "career": [
            {"tag": "华福", "org": "华福证券 · 研究所", "role": "首席策略分析组", "when": "2026.07 – 至今",
             "pts": ["维护 A 股、港股及宏观流动性日度跟踪体系，监测 PMI、社融、两融余额等指标。",
                     "梳理重要政策与宏观事件，提炼政策目标、受益方向与市场影响路径。",
                     "筹备策略路演与电话会议，捕捉客户关注的市场问题并反馈。"]},
            {"tag": "京东", "org": "京东零售", "role": "商务拓展", "when": "2026.03 – 2026.07",
             "pts": ["拆解线索到上线的转化数据、识别流失卡点，搭建城市预警机制，交付周期缩短约 30%。",
                     "高价值客户分层运营，挖掘竞对翻牌客户，提升 KA 与老商新店占比。",
                     "协同电销、工程、供应链中台，支撑 90+ 招商经理，团队执行力提升约 20%。"]},
            {"tag": "诺安", "org": "诺安基金", "role": "华中业务部 · 渠道经理助理", "when": "2025.09 – 2026.03",
             "pts": ["覆盖湖北、湖南、厦门、福建银行与券商渠道，输出周度销售报表和竞品分析。",
                     "用 Wind 做科技 AI / 半导体主题基金课件，路演培训超 200 人次。",
                     "搭建渠道效能评估模型，区域销售效率环比提升约 15%。"]},
            {"tag": "银河", "org": "中国银河证券 · 银河金汇", "role": "固定收益 · 多资产运营",
             "when": "2024.06 – 2024.09",
             "pts": ["为 200+ 企业财务数据建校验规则，处理效率提升约 30%，差错率压到 0.5% 以内。",
                     "参与多资产组合流动性压力测试与归因，完成 2 只产品季度调参回测。",
                     "协助亿元级固收 FOF 投后管理，路演材料支撑约 1000 万元募集。"]},
            {"tag": "成都", "org": "成都银行总行", "role": "财富经理助理", "when": "2023.06 – 2023.09",
             "pts": ["对筹资企业做盈利、回报、营运、成长、资本结构与偿债分析，出具财务分析报告。",
                     "参与贷后监控流程优化，跟踪核心财务指标并提示风险。"]}],
        "careerNote": "以上百分比为实习期间的业务口径；若被追问分母与统计区间，我可以说明各自测算方式。",
        "projects": [
            {"kick": "客户经营项目 · 有完整过程与结果", "title": "银行营销客户筛选与跟进资源分配",
             "sum": "名单很长、销售精力有限。先排出跟进优先级，再用实际做决定的条件检验，最后转成可选名单与名额方案，并说明扩大覆盖要付出什么代价。",
             "body": cust_body()},
            {"kick": "金融数据看板 · 每日 12:00 自动更新", "title": "金融之声：债市读数看板",
             "sum": "把国债收益率曲线、资金利率和央行公告做成每天自动刷新的看板，面向公募、私募、理财子的机构销售。数据来自官方公开来源，每条都能点回原文。",
             "body": "<p class='note'>完整曲线表、资金面走势与央行公告，见页面下方「数据看板」。</p>"},
            {"kick": "出海数据看板 · SMMT 官方注册数据", "title": "出海情报：英国电动车市场",
             "sum": "以 BYD DOLPHIN SURF 为对象，用 SMMT 官方注册数据建立市场基线，并跟踪中国品牌在英国的注册表现。",
             "body": "<p class='note'>市场结构、中国品牌排名与纯电车型 Top10，见页面下方「数据看板」。</p>"}],
        "certs": certs, "fin": fin, "sea": sea,
    }

    html = (HTML.replace("__CSS__", CSS)
                .replace("__IMG__", json.dumps({"photo": make_avatar()}, ensure_ascii=False))
                .replace("__DATA__", json.dumps(data, ensure_ascii=False)))
    evo = ROOT / "evo-site"
    if not evo.exists():
        evo.mkdir(parents=True)
    out = evo / "index.html"
    out.write_text(html, encoding="utf-8")
    log_line(f"单文件主页 v2 已生成：{out.relative_to(ROOT)}（{len(html)/1048576:.2f} MB）")
    log_line(f"  证书 {len(certs)} 张（已排除含照片的院榜电子版）"
             f" · 索引 {len(data['edu'])+len(data['career'])+len(data['projects'])} 条"
             f" · 看板面板已内嵌")


if __name__ == "__main__":
    main()
