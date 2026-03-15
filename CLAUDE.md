# Claude Code 项目目录

这是一个多子项目工作区，每个子目录是一个独立的子项目。

## 项目结构

```
agent/
├── CLAUDE.md          # 本文件
├── .claude/           # Claude Code 配置
│   ├── settings.json
│   └── hooks/
│       └── session-start.sh
├── project-a/         # 子项目示例
├── project-b/
└── ...
```

## 子项目规范

每个子项目应包含：
- 自己的 `CLAUDE.md`（描述该子项目的用途、技术栈、常用命令）
- 自己的依赖管理文件（`package.json` / `pyproject.toml` / `go.mod` 等）
- 自己的 `README.md`

## 常用操作

- 进入子项目后，Claude Code 会自动读取该目录下的 `CLAUDE.md`
- Session start hook 会自动检测并安装各子项目的依赖

## 子项目列表

<!-- 在此维护子项目列表 -->
| 目录 | 描述 | 技术栈 |
|------|------|--------|
| `hn-daily` | HackerNews 每日摘要，Kimi K2.5 总结，部署到 GitHub Pages | Python / httpx / Jinja2 |
