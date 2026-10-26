# 个人网站 · 每日自动更新版

## 先说清楚：什么是「自动更新」

GitHub Pages 是**静态托管**，没有服务器，所以不能像 App 那样秒级刷新。
这里做的自动更新是：**每天定时跑一次抓取脚本 → 重新生成 HTML → 自动提交**。
效果：你不用管，网站每天会自己变成当天的数据。

## 目录结构（全部上传到仓库根目录）

```
.github/workflows/daily-update.yml   ← 每日更新的定时任务
src/                                  ← 抓取与生成脚本
data/dash/                            ← 数据（每日被覆盖）
build/images.json                     ← 头像与证书图片（base64）
evo-site/                             ← 生成的三个页面
README-部署步骤.md
```

## 部署三步

1. 把上面这些文件**全部**放进你的 GitHub 仓库根目录（不是子文件夹）
2. 仓库 → Settings → Pages → Source 选 `Deploy from a branch`，分支 `main`，目录 `/ (root)`
3. 仓库 → Actions → 确认工作流已启用（默认开启）

之后每天**北京时间 12:00** 会自动跑一次。
想立刻看效果：Actions 页面 → 选「每日数据更新」→ Run workflow。

## 更新的是什么

| 页面 | 更新内容 | 频率 |
|---|---|---|
| news.html | 证券财经 / 出海新闻，每栏 15 条 | 每天 |
| dashboard.html | 国债收益率曲线、资金面（DR/FR）、两融、汇率、指数 | 每天（交易日） |
| index.html | 静态简历内容，不随数据变（但会重新生成） | 每天 |

## 关于失败

脚本有降级：**抓不到就保留上一次的结果**，页面不会变空、不会显示 0。
工作流里也加了 `|| echo 跳过`，单次接口失败不会让整条任务失败。

## 两个要留意的地方

1. **GitHub 免费版的定时任务可能延迟**几分钟到几十分钟（看当时负载），不会精确到秒。
2. **仓库连续 60 天没有任何提交，GitHub 会自动停用定时任务。** 停用后去 Actions 页面手动点一次即可恢复。

## 手动更新（本地）

```
pip install plotly pillow
python src/market_rt.py
python src/finvoice.py
python src/news_fetch.py
python src/build_unified.py
python src/build_index_v2.py
python src/build_news.py
```
