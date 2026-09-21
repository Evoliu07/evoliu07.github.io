"""
生成 evo-site/news.html —— 实时新闻板块（静态内嵌）

设计要点：
- 新闻内容**直接写进 HTML**，页面不 fetch 任何 JSON —— 微信内置浏览器即使 JS 不执行也能看到
- 两栏：证券财经大事 / 出海大事（同一条快讯流按关键词分流）
- 某栏为空则整栏不渲染，不留占位

用法： python src/build_news.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, log_line                                    # noqa: E402
from build_dashboards import CSS                                     # noqa: E402

NEWS = json.loads((ROOT / "data" / "dash" / "news.json").read_text(encoding="utf-8"))
WX_JS = (Path(__file__).resolve().parent / "_wx_snippet.js").read_text(encoding="utf-8")

EXTRA = """
main{max-width:1060px;margin:0 auto;padding:26px 20px 60px}
h1{text-align:center;font-size:27px}
.stamp{text-align:center;color:var(--muted);font-size:13.5px;font-family:var(--font-d);
  margin:6px 0 26px}
.nsec{margin-top:34px}
.nsec + .nsec{margin-top:44px;border-top:1px solid var(--line);padding-top:30px}
.nh{display:flex;align-items:baseline;gap:12px;justify-content:center;margin-bottom:16px}
.nh b{font-family:var(--font-d);font-size:23px;font-weight:800;letter-spacing:.14em}
.nh span{font-size:12.5px;color:var(--muted);font-family:var(--font-d)}
.card{background:var(--surface);border:1px solid var(--line);border-radius:13px;
  padding:15px 18px;box-shadow:var(--shadow)}
.nlist{list-style:none;padding:0;margin:0}
.nlist li{padding:11px 0;border-bottom:1px solid var(--line);display:grid;
  grid-template-columns:92px 1fr;gap:12px;align-items:start}
.nlist li:last-child{border-bottom:0}
.nlist .t{font-family:var(--font-d);font-size:12.5px;color:var(--muted);
  font-variant-numeric:tabular-nums;padding-top:2px}
.nlist .x{font-size:15.2px;line-height:1.75;color:var(--ink2)}
.nlist .x a{color:var(--ink2);text-decoration:none}
.nlist .x a:hover{color:var(--blue);text-decoration:underline}
.srcbox{margin-top:38px;padding-top:20px;border-top:1px solid var(--line);text-align:center;
  font-size:12.5px;color:var(--muted);font-family:var(--font-d);line-height:1.9}
@media(max-width:900px){
  main{padding:20px 14px 52px}
  h1{font-size:23px}
  .nh b{font-size:19px;letter-spacing:.1em}
  .nlist li{grid-template-columns:1fr;gap:4px}
  .nlist .t{font-size:11.5px}
  .nlist .x{font-size:14.5px}
}
"""


def items_html(rows: list[dict]) -> str:
    out = []
    for r in rows:
        t = (r.get("time") or "")[-8:-3]
        txt = r.get("text", "")
        url = r.get("url") or ""
        body = f'<a href="{url}" target="_blank" rel="noopener">{txt}</a>' if url else txt
        out.append(f'<li><span class="t">{t}</span><span class="x">{body}</span></li>')
    return "\n".join(out)


def section(title: str, sub: str, rows: list[dict]) -> str:
    if not rows:
        return ""                      # 空则整栏不渲染
    return f"""
  <div class="nsec">
    <div class="nh"><b>{title}</b><span>{sub}</span></div>
    <div class="card"><ul class="nlist">{items_html(rows)}</ul></div>
  </div>
"""


def build() -> str:
    fin, sea = NEWS.get("finance") or [], NEWS.get("overseas") or []
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>实时新闻 · 刘柏廷 Evo</title>
<style>{CSS}{EXTRA}</style></head><body>

<div class="bar">
  <b><a href="index.html" style="color:inherit">刘柏廷 · Evo</a>　<span style="color:var(--muted);font-weight:400">实时新闻</span></b>
  <nav>
    <a href="dashboard.html">数据看板</a>
    <a href="index.html">回主页</a>
    <button class="tg" onclick="document.body.classList.toggle('dark')">深/浅色</button>
  </nav>
</div>

<main>
  <h1>实时新闻</h1>
  <p class="stamp">证券财经与出海大事　·　更新于 {NEWS.get('as_of','')}　·　当日已筛 {NEWS.get('total',0)} 条快讯</p>
  {section("证券财经大事", "宏观 · 市场 · 监管", fin)}
  {section("出海大事", "外贸 · 跨境 · 反倾销 · 出海", sea)}

  <div class="srcbox">
    数据来源：{NEWS.get('source','')}<br>
    覆盖范围：{NEWS.get('span','')}　·　按关键词自动分流，每日更新
  </div>
</main>
{WX_JS}
</body></html>
"""


def main() -> None:
    html = build()
    out = ROOT / "evo-site" / "news.html"
    out.write_text(html, encoding="utf-8")
    log_line(f"实时新闻页：{out.relative_to(ROOT)}（{len(html)/1024:.0f} KB）· "
             f"财经 {len(fin := NEWS.get('finance') or [])} 条 / "
             f"出海 {len(NEWS.get('overseas') or [])} 条")


if __name__ == "__main__":
    main()
