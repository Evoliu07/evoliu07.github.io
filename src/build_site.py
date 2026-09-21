"""
生成「单文件个人主页」：evo-site/index.html

形式参照 sanshengai/sansheng-distill 的产物规范：
  - 一个自包含的 HTML 文件（图片以 data URI 内嵌，无外部依赖）
  - 暖纸质 / 衬线正文 / 多主题切换 / 吸顶导航
  - 内容只用真实材料：教育、实习、项目、证书

数据来源：
  - build/images.json（压缩后的证书与证件照）
  - evo-site/dash/data/dashboard.json（金融之声）
  - evo-site/dash/data/overseas.json（出海情报）
  - _incoming/experiences/customer-prioritization.html（银行客户筛选项目，原文抽取）

用法： python src/build_site.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, log_line                                   # noqa: E402

IMG = json.loads((ROOT / "build" / "images.json").read_text(encoding="utf-8"))
FIN = json.loads((ROOT / "data" / "dash" / "dashboard.json")
                 .read_text(encoding="utf-8"))
SEA = json.loads((ROOT / "data" / "dash" / "overseas.json")
                 .read_text(encoding="utf-8"))
CUST_HTML = Path("/Users/evo/WorkBuddy/2026-09-11-23-22-58/_incoming/experiences/"
                 "customer-prioritization.html")


def strip_tags(s: str) -> str:
    s = re.sub(r"<(script|style)[\s\S]*?</\1>", "", s)
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"</(p|li|h[1-6]|div)>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return "\n".join(l.strip() for l in s.split("\n") if l.strip())


def cust_blocks() -> list[dict]:
    """从增补包页面里抽取真实正文，按小节组织。"""
    if not CUST_HTML.exists():
        return []
    t = CUST_HTML.read_text(encoding="utf-8")
    body = t[t.find("<body"):] if "<body" in t else t
    parts = re.split(r"<h2[^>]*>(.*?)</h2>", body, flags=re.S)
    out = []
    if len(parts) < 3:
        return [{"h": "项目说明", "p": strip_tags(body)[:1200]}]
    for i in range(1, len(parts) - 1, 2):
        h = strip_tags(parts[i])
        p = strip_tags(parts[i + 1])
        p = re.sub(r"（\s*）", "", p)
        if len(p) > 1400:
            p = p[:1400] + "…"
        out.append({"h": h, "p": p})
    return [b for b in out if b["h"] and b["p"]][:8]


CSS = """
:root{
  --ink:#171411; --muted:#6d6258; --ink-soft:#3a332c; --ink-soft-2:#4a4239;
  --paper:#f8f2e7; --paper-deep:#ece1cf; --line:#d8c8af;
  --red:#b9422f; --blue:#245f73; --green:#177A5C; --gold:#B8892F;
  --white:#fffaf0; --surface:rgba(255,250,240,.62); --surface-strong:rgba(255,250,240,.88);
  --bar-bg:rgba(248,242,231,.94);
  --font-body:"Songti SC","Noto Serif SC","Noto Serif CJK SC",Georgia,serif;
  --font-display:"PingFang SC","Microsoft YaHei",Helvetica,sans-serif;
  --bg:radial-gradient(circle at 20% 8%, rgba(184,137,47,.10), transparent 55%),
       radial-gradient(circle at 82% 0%, rgba(36,95,115,.08), transparent 45%), #f8f2e7;
  --shadow:0 2px 10px rgba(60,45,25,.07); --tint:rgba(184,137,47,.13);
  --tint-strong:rgba(184,137,47,.26);
}
body[data-theme="ink-night"]{ --ink:#e8e4dc; --muted:#9c948a; --ink-soft:#cfc9bf; --ink-soft-2:#b9b2a7;
  --paper:#14120f; --paper-deep:#1d1a16; --line:#332e27; --red:#e07a63; --blue:#7fb6cc;
  --green:#6cc79f; --gold:#d9ab52; --white:#0d0b09; --surface:rgba(34,30,25,.7);
  --surface-strong:rgba(40,35,29,.92); --bar-bg:rgba(20,18,15,.94);
  --bg:radial-gradient(circle at 20% 8%, rgba(217,171,82,.10), transparent 55%), #14120f;
  --shadow:0 2px 14px rgba(0,0,0,.5); --tint:rgba(217,171,82,.14); --tint-strong:rgba(217,171,82,.28); }
body[data-theme="mist-blue"]{ --paper:#eef2f5; --paper-deep:#dde5ec; --line:#c2d0db;
  --ink:#16232c; --muted:#5c6b76; --ink-soft:#2c3d49; --ink-soft-2:#3d5061; --white:#f8fbfd;
  --surface:rgba(248,251,253,.7); --surface-strong:rgba(248,251,253,.9); --bar-bg:rgba(238,242,245,.94);
  --bg:radial-gradient(circle at 20% 8%, rgba(36,95,115,.10), transparent 55%), #eef2f5;
  --tint:rgba(36,95,115,.11); --tint-strong:rgba(36,95,115,.22); }
body[data-theme="forest-moss"]{ --paper:#eef1ea; --paper-deep:#dde4d6; --line:#c2cfb8;
  --ink:#1b2419; --muted:#5d6a58; --ink-soft:#33422f; --ink-soft-2:#44543f; --white:#f8fbf6;
  --surface:rgba(248,251,246,.7); --surface-strong:rgba(248,251,246,.9); --bar-bg:rgba(238,241,234,.94);
  --bg:radial-gradient(circle at 20% 8%, rgba(23,122,92,.11), transparent 55%), #eef1ea;
  --tint:rgba(23,122,92,.12); --tint-strong:rgba(23,122,92,.24); }
body[data-theme="clay-rust"]{ --paper:#f6ece6; --paper-deep:#ecdcd2; --line:#dcc2b3;
  --ink:#251a16; --muted:#75635b; --ink-soft:#3f2d26; --ink-soft-2:#503a31; --white:#fdf7f3;
  --surface:rgba(253,247,243,.7); --surface-strong:rgba(253,247,243,.9); --bar-bg:rgba(246,236,230,.94);
  --bg:radial-gradient(circle at 20% 8%, rgba(185,66,47,.10), transparent 55%), #f6ece6;
  --tint:rgba(185,66,47,.11); --tint-strong:rgba(185,66,47,.22); }
body[data-theme="cloud-grey"]{ --paper:#f2f2f2; --paper-deep:#e4e4e4; --line:#cdcdcd;
  --ink:#1c1c1c; --muted:#6b6b6b; --ink-soft:#383838; --ink-soft-2:#4a4a4a; --white:#fbfbfb;
  --surface:rgba(251,251,251,.72); --surface-strong:rgba(251,251,251,.92); --bar-bg:rgba(242,242,242,.94);
  --bg:radial-gradient(circle at 20% 8%, rgba(0,0,0,.04), transparent 55%), #f2f2f2;
  --shadow:0 2px 10px rgba(0,0,0,.06); --tint:rgba(0,0,0,.06); --tint-strong:rgba(0,0,0,.12); }
body[data-theme="gold-leaf"]{ --paper:#f7f1de; --paper-deep:#ebe0c4; --line:#d9c894;
  --ink:#241d10; --muted:#756646; --ink-soft:#3d331c; --ink-soft-2:#4f4326; --white:#fdfaef;
  --surface:rgba(253,250,239,.7); --surface-strong:rgba(253,250,239,.9); --bar-bg:rgba(247,241,222,.94);
  --bg:radial-gradient(circle at 20% 8%, rgba(184,137,47,.16), transparent 55%), #f7f1de;
  --tint:rgba(184,137,47,.15); --tint-strong:rgba(184,137,47,.3); }

*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{font-family:var(--font-body);background:var(--bg);color:var(--ink);line-height:1.9;
     font-size:16.5px;-webkit-font-smoothing:antialiased}
a{color:var(--blue);text-decoration:none}
a:hover{text-decoration:underline}
.bar{position:sticky;top:0;z-index:50;background:var(--bar-bg);backdrop-filter:blur(8px);
     border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;
     gap:16px;padding:0 26px;height:58px;font-family:var(--font-display)}
.bar b{font-size:15px;letter-spacing:.02em}
.bar nav{display:flex;gap:18px;font-size:13.5px;align-items:center;flex-wrap:wrap}
.bar nav a{color:var(--muted)}
.bar nav a:hover{color:var(--ink)}
.tp{position:relative}
.tp-trigger{border:1px solid var(--line);background:var(--surface);color:var(--ink);
  border-radius:99px;padding:5px 12px;font:inherit;font-size:12.5px;cursor:pointer;
  font-family:var(--font-display)}
.tp-menu{position:absolute;right:0;top:38px;background:var(--surface-strong);border:1px solid var(--line);
  border-radius:10px;box-shadow:var(--shadow);padding:6px;display:none;min-width:132px;z-index:60}
.tp[data-open="1"] .tp-menu{display:block}
.tp-menu button{display:block;width:100%;text-align:left;border:0;background:none;color:var(--ink);
  padding:7px 10px;border-radius:6px;font:inherit;font-size:13px;cursor:pointer;
  font-family:var(--font-display)}
.tp-menu button:hover{background:var(--tint)}
.tp-menu button[aria-pressed="true"]{font-weight:700;background:var(--tint-strong)}

main{max-width:820px;margin:0 auto;padding:0 26px 90px}
.hero{display:flex;flex-direction:column;align-items:center;text-align:center;padding:64px 0 40px}
.avatar{width:132px;height:132px;border-radius:50%;object-fit:cover;object-position:center 22%;
  border:3px solid var(--paper-deep);box-shadow:var(--shadow);background:var(--white)}
.hero h1{font-family:var(--font-display);font-size:35px;font-weight:600;margin-top:20px;
  letter-spacing:.01em;line-height:1.25}
.hero .sub{color:var(--muted);margin-top:8px;font-size:15px}
.hero .mail{margin-top:14px;font-size:14px;font-family:var(--font-display)}
section{padding:38px 0;border-top:1px solid var(--line)}
section:first-of-type{border-top:0}
h2{font-family:var(--font-display);font-size:13px;letter-spacing:.16em;text-transform:uppercase;
   color:var(--red);margin-bottom:20px;font-weight:700}
.lede{font-size:17px;color:var(--ink-soft);line-height:1.95}
.entry{display:grid;grid-template-columns:62px 1fr;gap:16px;padding:20px 0;border-bottom:1px solid var(--line)}
.entry:last-child{border-bottom:0}
.logo{width:50px;height:50px;border-radius:11px;display:grid;place-items:center;color:#fff;
  font-size:12.5px;font-weight:700;background:var(--ink);font-family:var(--font-display)}
.org{font-family:var(--font-display);font-weight:650;font-size:16.5px}
.meta{color:var(--muted);font-size:13.5px;margin-top:2px}
.when{color:var(--muted);font-size:13px;white-space:nowrap;font-family:var(--font-display)}
.trow{display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap}
.entry ul{margin:10px 0 0 18px}
.entry li{margin:7px 0;font-size:15.5px;line-height:1.8;color:var(--ink-soft-2)}
.card{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:20px 22px;
  margin-bottom:14px;box-shadow:var(--shadow)}
.card h3{font-family:var(--font-display);font-size:18px;margin-bottom:6px;font-weight:650}
.card .kick{color:var(--green);font-size:13px;font-family:var(--font-display);font-weight:600;
  margin-bottom:8px;letter-spacing:.02em}
.card p{color:var(--ink-soft-2);font-size:15.5px;margin-bottom:10px}
.more{display:none;margin-top:14px;padding-top:14px;border-top:1px dashed var(--line)}
.card.open .more{display:block}
.toggle{border:1px solid var(--line);background:var(--surface-strong);color:var(--ink);
  border-radius:99px;padding:7px 16px;font:inherit;font-size:13.5px;cursor:pointer;
  font-family:var(--font-display)}
.toggle:hover{background:var(--tint)}
.more h4{font-family:var(--font-display);font-size:14.5px;margin:16px 0 6px;color:var(--ink)}
.more p{font-size:14.5px;line-height:1.85;color:var(--ink-soft-2);margin-bottom:8px}
table{width:100%;border-collapse:collapse;font-size:13.5px;margin:10px 0;
  font-family:var(--font-display);font-variant-numeric:tabular-nums}
th,td{padding:7px 8px;text-align:right;border-bottom:1px solid var(--line)}
th:first-child,td:first-child{text-align:left}
th{color:var(--muted);font-weight:600;font-size:12.5px}
.up{color:var(--red)} .down{color:var(--green)}
.tscroll{overflow-x:auto}
.tag{display:inline-block;font-size:12px;background:var(--tint);color:var(--muted);
  padding:2px 9px;border-radius:99px;margin:3px 4px 0 0;font-family:var(--font-display)}
.note{font-size:13px;color:var(--muted);line-height:1.75;margin-top:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:14px}
.shot{background:var(--white);border:1px solid var(--line);border-radius:10px;overflow:hidden;
  cursor:zoom-in;box-shadow:var(--shadow);transition:transform .18s}
.shot:hover{transform:translateY(-3px)}
.shot img{width:100%;display:block;aspect-ratio:3/4;object-fit:cover;background:var(--paper-deep)}
.shot .cap{padding:9px 10px;font-size:12.5px;line-height:1.55;color:var(--ink-soft-2);
  font-family:var(--font-display)}
.shot .cap b{display:block;font-size:13px;color:var(--ink);font-weight:600;margin-bottom:2px}
.lb{position:fixed;inset:0;background:rgba(15,12,9,.92);display:none;z-index:200;
  align-items:center;justify-content:center;padding:26px;cursor:zoom-out}
.lb.on{display:flex}
.lb img{max-width:100%;max-height:88vh;border-radius:8px;box-shadow:0 10px 50px rgba(0,0,0,.6)}
footer{text-align:center;color:var(--muted);font-size:13px;padding:36px 0 0;
  border-top:1px solid var(--line);font-family:var(--font-display)}
@media(max-width:720px){
  .bar{height:auto;padding:10px 16px;flex-wrap:wrap;gap:8px}
  .bar nav{gap:12px;font-size:12.5px}
  main{padding:0 16px 70px}
  .hero{padding:38px 0 26px}
  .hero h1{font-size:27px}
  .entry{grid-template-columns:1fr}
  .logo{display:none}
}
@media print{ .bar,.tp{display:none} .more{display:block!important} }
"""

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>刘柏廷 · Evo｜个人主页</title>
<meta name="description" content="刘柏廷 BoTing LIU：香港中文大学（深圳）统计学硕士在读，澳门科技大学工商管理（国际贸易）学士。实习覆盖卖方研究、公募渠道、券商资管、银行与电商商务拓展。">
<style>__CSS__</style>
</head>
<body data-theme="warm-paper">

<div class="bar">
  <b>刘柏廷 · Evo</b>
  <nav>
    <a href="#about">关于</a>
    <a href="#edu">教育</a>
    <a href="#career">实习</a>
    <a href="#projects">项目</a>
    <a href="#certs">证书</a>
    <span class="tp" id="tp" data-open="0">
      <button class="tp-trigger" id="tp-btn" aria-haspopup="true" aria-expanded="false">主题</button>
      <span class="tp-menu" id="tp-menu" role="menu"></span>
    </span>
  </nav>
</div>

<main>
  <div class="hero">
    <img class="avatar" id="avatar" alt="刘柏廷">
    <h1>刘柏廷 · Evo</h1>
    <p class="sub" id="sub">香港中文大学（深圳）统计学硕士在读</p>
    <p class="mail"><a href="mailto:lbt2238516944@163.com">lbt2238516944@163.com</a></p>
  </div>

  <section id="about">
    <h2>关于</h2>
    <p class="lede" id="about-p">__ABOUT__</p>
  </section>

  <section id="edu">
    <h2>教育</h2>
    <div id="edu-list"></div>
  </section>

  <section id="career">
    <h2>实习经历</h2>
    <div id="career-list"></div>
    <p class="note">__CAREER_NOTE__</p>
  </section>

  <section id="projects">
    <h2>项目经历</h2>
    <div id="proj-list"></div>
  </section>

  <section id="certs">
    <h2>证书与荣誉</h2>
    <p class="lede" style="font-size:15.5px;margin-bottom:18px">
      以下为证书原件扫描件，名称、等级、日期与编号均未修改。点击可放大查看。
    </p>
    <div class="grid" id="cert-grid"></div>
    <p class="note">证书图片已压缩至网页可用尺寸（最长边 900px）；原件保存在本地。
      竞赛与项目的完整研究过程，见各项目卡片的展开内容。</p>
  </section>

  <footer>© Liu Boting · Evo　｜　本页为单文件静态页面，无外部依赖、无追踪脚本</footer>
</main>

<div class="lb" id="lb"><img id="lb-img" alt="证书放大图"></div>

<script>
const IMG = __IMG__;
const DATA = __DATA__;
const THEMES = [["warm-paper","暖纸"],["ink-night","夜墨"],["mist-blue","雾蓝"],
                ["forest-moss","苔绿"],["clay-rust","陶土"],["cloud-grey","云灰"],["gold-leaf","金叶"]];

/* ---------- 主题 ---------- */
const KEY="evo:theme";
function setTheme(t){
  document.body.dataset.theme=t;
  document.querySelectorAll("[data-pick]").forEach(b=>
    b.setAttribute("aria-pressed", String(b.dataset.pick===t)));
  try{localStorage.setItem(KEY,t)}catch(e){}
}
(function initTheme(){
  const menu=document.getElementById("tp-menu");
  menu.innerHTML=THEMES.map(([k,n])=>
    `<button data-pick="${k}" role="menuitem" aria-pressed="false">${n}</button>`).join("");
  let t="warm-paper"; try{t=localStorage.getItem(KEY)||"warm-paper"}catch(e){}
  setTheme(t);
  menu.addEventListener("click",e=>{
    const b=e.target.closest("[data-pick]"); if(!b)return;
    setTheme(b.dataset.pick); closeTp();
  });
  const tp=document.getElementById("tp"), btn=document.getElementById("tp-btn");
  function closeTp(){tp.dataset.open="0";btn.setAttribute("aria-expanded","false")}
  window.closeTp=closeTp;
  btn.addEventListener("click",e=>{e.stopPropagation();
    const open=tp.dataset.open==="1"; tp.dataset.open=open?"0":"1";
    btn.setAttribute("aria-expanded",String(!open));});
  document.addEventListener("click",e=>{ if(!tp.contains(e.target)) closeTp(); });
})();

/* ---------- 渲染 ---------- */
document.getElementById("avatar").src = IMG.photo;

document.getElementById("edu-list").innerHTML = DATA.edu.map(e=>`
  <div class="entry">
    <div class="logo" style="background:${e.c}">${e.tag}</div>
    <div>
      <div class="trow">
        <div><div class="org">${e.org}</div><div class="meta">${e.deg}</div></div>
        <div class="when">${e.when}</div>
      </div>
      ${e.note?`<div class="meta" style="margin-top:6px">${e.note}</div>`:""}
    </div>
  </div>`).join("");

document.getElementById("career-list").innerHTML = DATA.career.map(c=>`
  <div class="entry">
    <div class="logo" style="background:${c.c}">${c.tag}</div>
    <div>
      <div class="trow">
        <div><div class="org">${c.org}</div><div class="meta">${c.role}</div></div>
        <div class="when">${c.when}</div>
      </div>
      <ul>${c.pts.map(p=>`<li>${p}</li>`).join("")}</ul>
    </div>
  </div>`).join("");

document.getElementById("proj-list").innerHTML = DATA.projects.map((p,i)=>`
  <div class="card" id="card-${i}">
    <div class="kick">${p.kick}</div>
    <h3>${p.title}</h3>
    <p>${p.sum}</p>
    <div>${p.tags.map(t=>`<span class="tag">${t}</span>`).join("")}</div>
    <button class="toggle" style="margin-top:12px" data-t="${i}">展开看数据与做法</button>
    <div class="more">${p.body}</div>
  </div>`).join("");

document.addEventListener("click",e=>{
  const b=e.target.closest("[data-t]");
  if(b){
    const card=document.getElementById("card-"+b.dataset.t);
    const on=card.classList.toggle("open");
    b.textContent = on?"收起":"展开看数据与做法";
    return;
  }
});

/* 证书网格 + 灯箱 */
const lb=document.getElementById("lb"), lbImg=document.getElementById("lb-img");
document.getElementById("cert-grid").innerHTML = DATA.certs.map((c,i)=>`
  <div class="shot" data-i="${i}" role="button" tabindex="0" aria-label="放大查看：${c.title}">
    <img src="${c.uri}" alt="${c.title}" loading="lazy">
    <div class="cap"><b>${c.title}</b>${c.date}　${c.no?("编号 "+c.no):""}</div>
  </div>`).join("");
function openLb(i){ lbImg.src=DATA.certs[i].uri; lb.classList.add("on"); }
document.getElementById("cert-grid").addEventListener("click",e=>{
  const s=e.target.closest(".shot"); if(s) openLb(+s.dataset.i);
});
document.getElementById("cert-grid").addEventListener("keydown",e=>{
  if(e.key==="Enter"||e.key===" "){ const s=e.target.closest(".shot");
    if(s){e.preventDefault(); openLb(+s.dataset.i);} }
});
lb.addEventListener("click",()=>lb.classList.remove("on"));
document.addEventListener("keydown",e=>{ if(e.key==="Escape") lb.classList.remove("on"); });
</script>
</body>
</html>
"""


# ------------------------------------------------------------------ 数据
def fmt(v, d=2):
    return "—" if v is None else f"{v:.{d}f}"


def bp(v):
    return "—" if v is None else f"{'+' if v > 0 else ''}{v:.1f}bp"


def build_fin_body() -> str:
    rows = FIN["curve"]["rows"]
    mk = FIN["market"] if "market" in FIN else {}
    money = FIN.get("money") or {}
    hist = {h["label"]: h["date"] for h in FIN["curve"].get("history_labels", [])}
    sh = FIN.get("shape") or {}
    dr = money.get("FDR007")

    t = '<h4>国债收益率曲线（中债，银行间市场，到期收益率 %）</h4><div class="tscroll"><table>'
    t += '<tr><th>期限</th><th>当前</th><th>1 周前</th><th>1 个月前</th><th>1 年前</th>'\
         '<th>周变动</th><th>月变动</th><th>年变动</th></tr>'
    for r in rows:
        c = lambda v: ' class="up"' if (v or 0) > 0 else (' class="down"' if (v or 0) < 0 else '')
        t += (f'<tr><td><b>{r["tenor"]}</b></td><td>{fmt(r["now"])}</td>'
              f'<td>{fmt(r.get("1周前"))}</td><td>{fmt(r.get("1个月前"))}</td>'
              f'<td>{fmt(r.get("1年前"))}</td>'
              f'<td{c(r.get("w1_bp"))}>{bp(r.get("w1_bp"))}</td>'
              f'<td{c(r.get("m1_bp"))}>{bp(r.get("m1_bp"))}</td>'
              f'<td{c(r.get("y1_bp"))}>{bp(r.get("y1_bp"))}</td></tr>')
    t += "</table></div>"
    t += f'<p class="note">曲线取数日 {FIN["meta"]["data_date"]}；'
    t += "；".join(f"{k} {v}" for k, v in hist.items()) + "。1bp = 0.01 个百分点。</p>"

    t += '<h4>曲线形态与资金面</h4><div class="tscroll"><table><tr><th>指标</th><th>数值</th><th>说明</th></tr>'
    if sh.get("10Y-1Y") is not None:
        t += (f'<tr><td>10Y − 1Y 利差</td><td>{fmt(sh["10Y-1Y"],3)}</td>'
              f'<td>3 个月前 {fmt(sh.get("10Y-1Y_3个月前"),3)}，1 个月前 '
              f'{fmt(sh.get("10Y-1Y_1个月前"),3)}</td></tr>')
    for k in ("FDR001", "FDR007", "FR007", "SHIBOR_1W"):
        m = money.get(k)
        if m:
            t += (f'<tr><td>{m["label"]}</td><td>{fmt(m["value"])}%</td>'
                  f'<td>较前值 {bp(m["chg_bp"])}　{m["date"]}</td></tr>')
    t += "</table></div>"
    t += ('<p class="note">DR（存款类机构）与 FR（全市场）不是同一口径，分列展示不混用。'
          '收益率变化不等于投资收益，本页不做任何收益预测或回测。</p>')
    return t


def build_sea_body() -> str:
    mk = SEA.get("market") or {}
    t = '<h4>英国市场（SMMT 官方注册数据）</h4><div class="tscroll"><table>'
    t += '<tr><th>指标</th><th>数值</th></tr>'
    t += f'<tr><td>当月新乘用车注册</td><td>{int(mk.get("total_month") or 0):,} 辆</td></tr>'
    t += f'<tr><td>纯电 BEV 注册</td><td>{int(mk.get("bev_month") or 0):,} 辆</td></tr>'
    t += f'<tr><td>纯电份额</td><td>{fmt(mk.get("bev_share"),1)}%（上年同期 {fmt(mk.get("bev_share_prev"),1)}%）</td></tr>'
    t += f'<tr><td>纯电同比</td><td>{bp(mk.get("bev_yoy"))}</td></tr>'
    t += f'<tr><td>年初至今纯电</td><td>{int(mk.get("bev_ytd") or 0):,} 辆</td></tr>'
    t += "</table></div>"

    ch = SEA.get("channel") or []
    if ch:
        LAB = {"FLEET": "车队", "PRIVATE": "私人", "BUSINESS": "公司自用"}
        t += '<h4>渠道结构</h4><div class="tscroll"><table><tr><th>渠道</th><th>当月</th>'\
             '<th>份额</th><th>上年同期</th></tr>'
        for c in ch:
            t += (f'<tr><td>{LAB.get(c["key"], c["key"])}</td>'
                  f'<td>{int(c["units"] or 0):,} 辆</td>'
                  f'<td>{fmt(c.get("share"),1)}%</td>'
                  f'<td>{fmt(c.get("share_prev"),1)}%</td></tr>')
        t += "</table></div>"
        t += ('<p class="note">车队占比高于私人，说明「公司车 / 车队适配」更值得优先验证。'
              '但这是<b>全市场</b>口径，不是纯电细分，也不是单一车型的结构。</p>')

    cn = SEA.get("cn_brands") or []
    if cn:
        t += '<h4>中国与新兴品牌在英国的注册表现（当月）</h4><div class="tscroll"><table>'\
             '<tr><th>品牌</th><th>当月</th><th>份额</th><th>同比</th></tr>'
        for b in cn[:8]:
            t += (f'<tr><td>{b["brand"]}</td><td>{int(b["units"] or 0):,} 辆</td>'
                  f'<td>{fmt(b.get("share"),1)}%</td><td>{bp(b.get("yoy"))}</td></tr>')
        t += "</table></div>"
        t += ('<p class="note">品牌级、含全部动力类型，<b>不能当作单一车型销量</b>；'
              '同比超过 1000% 的条目通常来自极小的上年基数。</p>')

    nr = SEA.get("not_retrieved") or []
    if nr:
        t += "<h4>明确没拿到的数据</h4><ul style='margin-left:18px'>"
        for x in nr:
            t += f'<li style="font-size:14.5px;margin:6px 0"><b>{x["item"]}</b>——{x["reason"]}</li>'
        t += "</ul><p class='note'>拿不到就写拿不到，不用推测值把表格填满。</p>"
    return t


def build_cust_body() -> str:
    blocks = cust_blocks()
    if not blocks:
        return "<p class='note'>项目详情页见增补包中的 customer-prioritization.html。</p>"
    t = ""
    for b in blocks:
        t += f'<h4>{b["h"]}</h4>'
        for para in b["p"].split("\n"):
            para = para.strip()
            if len(para) > 12:
                t += f"<p>{para}</p>"
    return t


DATA = {
    "edu": [
        {"tag": "CUHK", "c": "#6b1020", "org": "香港中文大学（深圳）",
         "deg": "计算社会科学（统计学）理学硕士 · 深圳", "when": "2025.09 – 2027.06", "note": ""},
        {"tag": "MUST", "c": "#1a3c6e", "org": "澳门科技大学",
         "deg": "工商管理（国际贸易）学士 · 澳门", "when": "2022.09 – 2026.06",
         "note": "商学院院长优秀毕业生（2023/2024 学年）"},
    ],
    "career": [
        {"tag": "华福", "c": "#8a5a2b", "org": "华福证券 · 研究所",
         "role": "首席策略分析组", "when": "2026.07 – 至今",
         "pts": ["维护 A 股、港股及宏观流动性日度跟踪体系，监测 PMI、社融、两融余额等指标。",
                 "梳理重要政策与宏观事件，提炼政策目标、受益方向与市场影响路径。",
                 "筹备策略路演与电话会议，捕捉客户关注的市场问题并反馈。"]},
        {"tag": "京东", "c": "#e21a1a", "org": "京东零售",
         "role": "商务拓展", "when": "2026.03 – 2026.07",
         "pts": ["拆解线索到上线的转化数据、识别流失卡点，搭建城市预警机制，交付周期缩短约 30%。",
                 "高价值客户分层运营，挖掘竞对翻牌客户，提升 KA 与老商新店占比。",
                 "协同电销、工程、供应链中台，支撑 90+ 招商经理，团队执行力提升约 20%。"]},
        {"tag": "诺安", "c": "#0b3d91", "org": "诺安基金",
         "role": "华中业务部 · 渠道经理助理", "when": "2025.09 – 2026.03",
         "pts": ["覆盖湖北、湖南、厦门、福建银行与券商渠道，输出周度销售报表和竞品分析。",
                 "用 Wind 做科技 AI / 半导体主题基金课件，路演培训超 200 人次。",
                 "搭建渠道效能评估模型，区域销售效率环比提升约 15%。"]},
        {"tag": "银河", "c": "#c4a35a", "org": "中国银河证券 · 银河金汇",
         "role": "固定收益 · 多资产运营", "when": "2024.06 – 2024.09",
         "pts": ["为 200+ 企业财务数据建校验规则，处理效率提升约 30%，差错率压到 0.5% 以内。",
                 "参与多资产组合流动性压力测试与归因，完成 2 只产品季度调参回测。",
                 "协助亿元级固收 FOF 投后管理，路演材料支撑约 1000 万元募集。"]},
        {"tag": "成都", "c": "#0a6b4c", "org": "成都银行总行",
         "role": "财富经理助理", "when": "2023.06 – 2023.09",
         "pts": ["对筹资企业做盈利、回报、营运、成长、资本结构与偿债分析，出具财务分析报告。",
                 "参与贷后监控流程优化，跟踪核心财务指标并提示风险。"]},
    ],
    "projects": [
        {"kick": "客户经营项目 · 有完整过程与结果",
         "title": "银行营销客户筛选与跟进资源分配",
         "sum": "名单很长、销售精力有限。先给客户排出跟进优先级，再用实际做决定的条件检验，"
                "最后把排序转成可选名单与名额方案，并说明扩大覆盖要付出什么代价。",
         "tags": ["客户分层", "跟进优先级", "名额分配", "可复现"],
         "body": None},
        {"kick": "金融数据看板 · 每日 12:00 自动更新",
         "title": "金融之声：债市读数看板",
         "sum": "把国债收益率曲线、资金利率和央行公告做成一张每天自动刷新的表，"
                "面向公募、私募、理财子的机构销售。数据来自官方公开来源，每条都能点回原文。",
         "tags": ["中债", "资金面", "自动更新", "可追溯"],
         "body": None},
        {"kick": "出海数据看板 · 官方注册数据",
         "title": "出海情报：英国电动车市场",
         "sum": "以 BYD DOLPHIN SURF 为对象，用 SMMT 官方注册数据建立市场基线，"
                "并跟踪中国品牌在英国的注册表现。",
         "tags": ["SMMT", "英国", "中国品牌", "口径纪律"],
         "body": None},
    ],
    "certs": [{"title": c["title"], "date": c["date"], "no": c["no"], "uri": c["uri"]}
              for c in IMG if c["key"] != "photo"],
}

ABOUT = ("国际贸易本科，统计学硕士在读。实习覆盖银行、券商资管、公募渠道、"
         "电商商务拓展和卖方研究，熟悉销售漏斗、渠道分析，"
         "也习惯用程序把公开数据整理成能每天刷新的看板。"
         "做研究时最较真的是口径：能核实的才写，拿不到的一律留空并注明。")

CAREER_NOTE = ("以上百分比为实习期间的业务口径。若对方追问分母与统计区间，"
               "我可以说明各自的测算方式；无法核实的数字我不会放进简历。")


def main() -> None:
    DATA["projects"][0]["body"] = build_cust_body()
    DATA["projects"][1]["body"] = build_fin_body()
    DATA["projects"][2]["body"] = build_sea_body()

    img_map = {c["key"]: c["uri"] for c in IMG}
    html = (HTML
            .replace("__CSS__", CSS)
            .replace("__IMG__", json.dumps(img_map, ensure_ascii=False))
            .replace("__DATA__", json.dumps(DATA, ensure_ascii=False))
            .replace("__ABOUT__", ABOUT)
            .replace("__CAREER_NOTE__", CAREER_NOTE))

    evo = ROOT / "evo-site"
    if not evo.exists():
        evo.mkdir(parents=True)
    out = evo / "index.html"
    out.write_text(html, encoding="utf-8")
    log_line(f"单文件主页已生成：{out.relative_to(ROOT)}（{len(html)/1048576:.2f} MB）")
    log_line(f"  证书 {len(DATA['certs'])} 张 · 教育 {len(DATA['edu'])} 条 · "
             f"实习 {len(DATA['career'])} 段 · 项目 {len(DATA['projects'])} 个")


if __name__ == "__main__":
    main()
