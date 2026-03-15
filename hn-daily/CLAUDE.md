# hn-daily

每天定时抓取 HackerNews Top 30，用 Kimi K2.5 生成中文摘要，输出为静态 HTML，部署到 GitHub Pages。

## 技术栈

- Python 3.12
- httpx（异步 HTTP，调用 HN API 和 Kimi API）
- Jinja2（HTML 模板渲染）
- GitHub Actions（定时触发 + 自动部署）

## 本地运行

```bash
cd hn-daily
pip install -r requirements.txt
MOONSHOT_API_KEY=your_key python fetch.py
# 输出在 output/index.html
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `fetch.py` | 主脚本：抓取 HN → Kimi 总结 → 渲染 HTML |
| `requirements.txt` | 依赖：httpx, jinja2 |
| `templates/index.html` | Jinja2 模板 |
| `output/` | 生成产物（git ignored） |

## 环境变量

| 变量 | 说明 |
|------|------|
| `MOONSHOT_API_KEY` | Kimi API 密钥，从 platform.moonshot.cn 获取 |

## 部署

GitHub Actions 每天 UTC 01:00（北京时间 09:00）自动运行，结果推送到 `gh-pages` 分支。
手动触发：GitHub → Actions → hn-daily → Run workflow。
