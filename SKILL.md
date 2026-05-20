---
name: openvl
description: 让无视觉能力的 AI 模型看懂图片。支持从文件、URL、剪贴板读取图片，调用外部多模态 API 描述内容并返回结构化 Markdown 结果。
version: 1.0.0
credentials:
  - name: VISION_API_KEY
    required: true
    description: "API Key"
    storage: "config.env 文件"
read_when:
  - 用户提供了图片路径或 URL（如 D:\xxx.png, https://...）→ 运行 openvl <路径>
  - 用户说"好了""截好了""截图了"，表示已截图到剪贴板 → 运行 openvl --clip
  - 用户问图片内容、文字、场景等
  - 需要 OCR 提取图中的文字
---

## 安装

```bash
npm install -g @scp3500/openvl
```

## 使用方式

### CLI（Pi / Claude Code / OpenCode 等）

```bash
openvl <图片路径或URL>     # 看图
openvl --clip              # 读剪贴板截图
```

### Cherry Studio（通过 MCP）

| 字段 | 值 |
|------|-----|
| 命令 | `openvl` |
| 参数 | `--mcp` |
| 超时 | `90` |

告诉 AI 使用 `describe_image` 或 `describe_clipboard` 工具。

## 配置

编辑 `config.env`：

```ini
VISION_API_KEY=你的密钥
VISION_API_BASE=https://你的中转站地址/v1
VISION_MODEL=模型ID
```

## 项目结构

```
openvl/
├── SKILL.md
├── config.env
├── prompts/
│   └── describe.md
└── scripts/
    ├── vision.py
    └── mcp_server.js
```
