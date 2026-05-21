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

## 使用规则

**不要重复看图。** 如果对话历史里已经有 `openvl` 的输出结果，直接从中提取信息即可，禁止再次调用 `openvl` 请求同一张图。除非用户明确说换了图或要求重新分析。

**复述内容时：**
- 不要只说概括，要列出关键数据（文字、数值、列表、选项等）
- 尤其是有大量数据的情况，不要省略，逐条列出
- 不加废话和评价，只说看到了什么

## 安装

```bash
npm install -g @scp3500/openvl
```

## 使用方式

```bash
openvl <路径/URL>      # 看图
openvl -c               # 读剪贴板截图
openvl <图片> -t 0.3    # 温度（0~1，越低越严谨）
openvl <图片> -T high   # 思考深度 (low|medium|high)
```

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
