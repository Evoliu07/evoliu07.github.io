# 个人网站（自动更新版）

每天北京时间 18:30 自动抓取数据并重新生成页面；GitHub Actions 手动也可触发。

## 目录（放仓库根目录）
  .github/workflows/daily-update.yml
  src/
  data/dash/
  build/images.json
  build/avatar.jpg
  index.html
  dashboard.html
  news.html

> 注意：GitHub Pages 从仓库根目录读取 `index.html`。构建脚本会同时写入根目录和 `evo-site/`，
> 线上站点以根目录为准。

## 上传 GitHub（更新原网站）

原网站地址是 `https://evoliu07.github.io/`，对应仓库：`Evoliu07/evoliu07.github.io`。
不要再新建 `personal-site`；如果已经新建了空的 `personal-site`，可以删除或忽略。

在本目录终端执行：

```bash
git remote add origin https://github.com/Evoliu07/evoliu07.github.io.git
git fetch origin
git merge origin/main --allow-unrelated-histories -X ours -m "chore: 同步自动更新版个人网站"
git push -u origin main
```

如果提示登录，用浏览器授权 GitHub 即可。推送成功后等待 1–2 分钟，访问：

```text
https://evoliu07.github.io/
```

## 开启自动更新

1. 仓库页：Settings → Pages → Source 选 `Deploy from a branch`，Branch 选 `main` / `(root)`。
2. 仓库页：Actions → 若提示启用工作流，点 `I understand my workflows, go ahead and enable them`。
3. 验证：Actions → `每日数据更新` → `Run workflow` 手动跑一次。

## 自动更新说明

- 定时：每天北京时间 18:30（UTC 10:30）自动运行一次。
- 内容：抓取行情、新闻、英国 SMMT、德国贸易数据，并重建三个页面。
- 失败降级：单个接口失败不中断，保留上次有效数据；不会把缺失数据填成 0。
- 数据期 vs 更新时间：月度数据（如 SMMT 2026-09）按官方发布周期展示，页面同时标注抓取时间。

## 本地手动更新

```bash
.venv/bin/python src/market_rt.py
.venv/bin/python src/finvoice.py
.venv/bin/python src/news_fetch.py
.venv/bin/python src/gtm_fetch.py
.venv/bin/python src/overseas_dash.py
.venv/bin/python src/market_de.py
.venv/bin/python src/build_unified.py
.venv/bin/python src/build_index_v2.py
.venv/bin/python src/build_news.py
```

## 头像

网站头像使用 `build/avatar.jpg`。如需更换，直接替换该文件后重新运行：

```bash
.venv/bin/python src/build_index_v2.py
```
