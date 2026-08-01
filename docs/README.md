# OpenVL 文档索引

本目录按主题拆分详细文档；`README.md`（仓库根）只讲快速上手。
**遇到问题先看这里对应主题的文件，找不到再查仓库根 README。**

```
docs/
├── README.md            ← 本文件：索引
├── cli.md               ← CLI 完整参考：全部参数、多图、stdin/base64、思考档
├── mcp.md               ← MCP 详细：工具、stdio/http、Cherry Studio 配置、超时
├── troubleshooting.md   ← 排障：doctor、常见错误、中转站、配置丢失、依赖
├── DEVELOPMENT.md      ← 维护者：目录结构、副本、测试、发版、AI 安装指引
├── index.html          ← 产品介绍落地页（GitHub Pages）
└── ../integrations/README.md  ← 各工具（OpenCode/Claude Code/Pi）集成细节
```

## 怎么找

| 你的问题 | 看 |
|----------|-----|
| 命令行怎么用、有哪些参数 | [cli.md](cli.md) |
| 在 Cherry Studio / 其他 MCP 客户端用 | [mcp.md](mcp.md) |
| 装不上 / 报错 / 连不上 / 配置丢了 | [troubleshooting.md](troubleshooting.md) |
| OpenCode / Claude Code / Pi 集成 | [integrations/README.md](../integrations/README.md) |
| 想改代码 / 发版 / 多副本同步 | [DEVELOPMENT.md](DEVELOPMENT.md) |
| 只想快速用起来 | 仓库根 [README.md](../README.md) |

## 给 AI 助手

被要求"安装 openvl"时：读仓库根 README 的「AI 助手自动安装」区，执行 `install.sh`，
然后按 [DEVELOPMENT.md 第 9 节](DEVELOPMENT.md#9-ai-助手安装指引给-agent-读) 完成配置与验证。
