---
name: openvl
description: 让无视觉能力的 AI 模型看懂图片。支持本地图片、URL、剪贴板截图、base64 数据、stdin 管道。用户提问会传给视觉模型直接回答。也支持 MCP 服务器供 Cherry Studio 等工具调用。
version: 1.1.5
credentials:
  - name: VISION_API_KEY
    required: true
    description: "API Key"
    storage: "config.env 文件"
read_when:
  - 用户提供了图片路径、URL 或 data URI → 运行 openvl <路径/URI>
  - 用户粘贴了图片（AI IDE 会传临时文件路径）→ 运行 openvl <路径>
  - 用户说"好了""截好了""截图了"，表示已截图到剪贴板 → 运行 openvl -c
  - 用户问图片内容、文字、场景、出处等 → 把问题带上：openvl <路径> 用户的问题
  - 需要 OCR 提取图中的文字
  - 用户问"这张图是谁画的/什么出处" → 先用 openvl 读图，再用联网工具查
---

## 使用规则

**调用 openvl 时，把用户问题带上。** `openvl -c 用户的问题` 或 `openvl <路径> 用户的问题`，问题会自动拼到视觉模型的提示词里，直接回答。

**不要重复看图。** 对话历史已有 `openvl` 输出则直接复用，除非用户明确说换了图。

**根据用户需求回答，不是固定描述图片。**
- 用户问出处 → 联网查
- 用户问文字 → 提取文字
- 用户问内容 → 描述图片
- 用户没提具体要求 → 直接说关键信息，大量数据逐条列出

## 安装

```bash
npm install -g @scp3500/openvl
```

## 使用方式

```bash
openvl <路径/URL>                  # 看图
openvl -c                           # 读剪贴板截图
openvl --stdin                      # 从 stdin 读 data URI
openvl --base64 iVBOR...            # 直接传 base64
openvl <路径> 用户的问题            # 带问题看图
openvl -c 用户的问题                # 带问题读剪贴板
openvl <图片> -t 0.3                # 温度（0~1，越低越严谨）
openvl <图片> -T high               # 思考深度 (low|medium|high)
openvl <图片> -s 512                # 图片最大边长（默认1024，越小越省）
```

## 配置

编辑 `config.env`：

```ini
VISION_API_KEY=你的密钥
VISION_API_BASE=https://你的中转站地址/v1/chat/completions
VISION_MODEL=模型ID
```
