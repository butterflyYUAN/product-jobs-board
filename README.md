# 大厂产品岗招聘聚合（GitHub 自动定时版）

聚合 **腾讯 / 字节跳动 / 淘天集团 / 饿了么 / 百度** 官方招聘站点的「产品类」职位，
自动生成静态看板并通过 **GitHub Pages** 公开访问。**不依赖本地电脑开关机**，
由 GitHub Actions 每 6 小时自动爬取、更新并部署。

## 站点功能
- 按公司分 Tab 展示（全部 / 各家 + 数量），点 Tab 立即筛选
- 关键词搜索（职位 / 职责 / 要求 / 城市）、时间筛选（🔥今日新发 / 7天 / 30天）
- 分页、JD 全文展开/收起、跳转官网详情页
- 数据来源：各公司官方招聘公开页，仅作聚合展示

## 工作原理
```
crawl_*.py  →  jobs_*.json / *_raw.json   （各站爬虫，尽力而为，单站失败不影响整体）
normalize.py →  jobs_data.json             （统一字段、去重、标记今日新发）
build_html.py→  site/index.html           （自包含静态站点，内嵌全部数据）
```
GitHub Actions（`cron: 0 */6 * * *`，每 6 小时）自动执行 `run_all.py`，
把新数据提交回仓库，并部署 `site/` 到 GitHub Pages。

## 本地运行
```bash
pip install -r requirements.txt
playwright install chromium      # 仅 ByteDance/淘天/饿了么 三家需要
python run_all.py
# 产物: jobs_data.json 与 site/index.html
```

## 部署到 GitHub Pages（一次性）
1. 把这个仓库推到你自己的 GitHub（公开仓库，Pages 免费）。
2. 仓库 **Settings → Pages → Source** 选择 **GitHub Actions**。
3. 之后无需任何操作：每 6 小时自动爬取更新；也可在 Actions 页手动 **Run workflow** 立即触发。
4. 公开网址：`https://<你的用户名>.github.io/<仓库名>/`

> 首次推送后，Actions 会自动跑一次并完成 Pages 部署；若 Pages 未自动启用，
> 按第 2 步手动开启即可（仅需一次）。

## 目录
| 文件 | 作用 |
|---|---|
| `crawl_tencent.py` | 腾讯（HTTP API，无需浏览器） |
| `crawl_bytedance.py` | 字节（Playwright 拦截搜索接口） |
| `crawl_taotian.py` / `crawl_eleme.py` | 阿里系（Playwright 翻页 + 接口拦截） |
| `crawl_baidu.py` | 百度（表单编码 POST 接口） |
| `normalize.py` / `build_html.py` | 归一化与建站 |
| `run_all.py` | 一键编排 |
| `.github/workflows/crawl.yml` | 定时爬取 + 部署 |

## 说明
- 各爬虫为「尽力而为」：某站临时不可达/反爬时跳过，不影响其它站与整体看板。
- 仓库内已包含一份基线 `jobs_data.json` 与 `site/`，确保首次部署即有内容；
  后续由 Actions 覆盖更新。
- GitHub 公开仓库 Actions 分钟数免费、无上限；定时任务在长期无 commit 的仓库可能被
  GitHub 自动暂停，重新 push 一次即可恢复。
