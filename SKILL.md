---
name: openvl
description: 让无视觉能力的 AI 模型看懂图片。支持从文件、URL、剪贴板读取图片，调用外部多模态 API 描述内容并返回结构化 Markdown 结果。
version: 1.0.0
credentials:
  - name: VISION_API_KEY
    required: true
    description: "API Key"
    storage: "config.env 文件"
---

## 安装

```bash
npm install -g @scp3500/openvl
```

## Cherry Studio MCP 配置

设置 → MCP 服务器 → 添加：

| 字段 | 值 |
|------|-----|
| 名称 | `openvl` |
| 命令 | `openvl` |
| 参数 | `--mcp` |
| 超时 | `90` |

### 使用非视觉模型看图

Cherry Studio 中使用 DeepSeek 等不支持原生视觉的模型时，上传图片会报错。此时告诉 AI：

> 请使用 describe_image 或 describe_clipboard 工具来分析图片

### 可用工具

| 工具 | 说明 |
|------|------|
| `describe_image` | 传入图片路径/URL/base64，返回结构化描述 |
| `describe_clipboard` | 从剪贴板读取截图并描述（仅 Windows） |

## 配置

编辑 `config.env`：

```ini
VISION_API_KEY=你的密钥
VISION_API_BASE=https://你的中转站地址/v1
VISION_MODEL=gpt-5.4-mini
```

> 详细教程请查看 README：
> 本地: `notepad <skill_dir>/README.md`
> GitHub: https://github.com/scp3500/openvl

> 配置文件路径：`notepad <skill_dir>/config.env`
