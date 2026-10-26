# 个人网站（自动更新版）

每天北京时间 18:30 自动抓取数据并重新生成页面；GitHub Actions 手动也可触发。

## 目录（放仓库根目录）
  .github/workflows/daily-update.yml
  src/
  data/dash/
  build/images.json
  build/avatar.jpg
  evo-site/index.html
  evo-site/dashboard.html
  evo-site/news.html

## 上传 GitHub（从零开始）

1. 在 GitHub 网页新建一个 **Public** 仓库，仓库名建议 `personal-site`，先不要勾选初始化 README。
2. 在本目录打开终端，执行：

```bash
git init
git add .
git commit -m "feat: 个人网站初始版本"
git branch -M main
git remote add origin https://github.com/<你的用户名>/personal-site.git
git push -u origin main
```

把 `<你的用户名>` 换成你的 GitHub 用户名。若 GitHub 弹出登录，用浏览器授权即可。

3. 仓库页：Settings → Pages → Source 选 `Deploy from a branch`，Branch 选 `main` / `(root)`，保存。
4. 仓库页：Actions → 若提示启用工作流，点 `I understand my workflows, go ahead and enable them`。
5. 验证：Actions → `每日数据更新` → `Run workflow` 手动跑一次；成功后访问
   `https://<你的用户名>.github.io/personal-site/`。

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
