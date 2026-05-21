# OpenVL

[中文](README.md) | [English](README.en.md)

让没有视觉能力的 AI 模型也能看懂图片。

```
用户发图片 → OpenVL 调用多模态 API → 返回文字描述 → AI 根据描述回复
```

## 快速开始

### 1. 安装

```bash
npm install -g @scp3500/openvl
```

### 2. 配置 API

```bash
openvl -key sk-你的密钥
openvl -api https://你的中转站/v1/chat/completions
```

### 3. 看图

直接看文件：

```bash
openvl D:\截图.png
```

或截图到剪贴板后提问：

```bash
openvl -c "这张图里有什么"
```

### 4. 给 AI IDE 装 skills（可选）

```bash
git clone https://github.com/scp3500/openvl.git ~/.agents/skills/openvl
```

这样 AI（Pi / Claude Code 等）遇到图片会自动调 openvl。

## 使用方式

### CLI

| 命令 | 说明 |
|------|------|
| `openvl <路径/URL>` | 看图 |
| `openvl -c` | 读剪贴板截图 |
| `openvl -c 你的问题` | 截屏 + 提问 |
| `openvl --stdin` | 从管道读 data URI |
| `openvl --base64 iVBOR...` | 传 raw base64 |
| `openvl <图片> -t 0.3` | 温度（0~1） |
| `openvl <图片> -T high` | 思考深度 |
| `openvl <图片> -s 512` | 最大边长（默认1024） |
| `openvl -cfg` | 查看当前配置 |

多个图片一起传：`openvl a.png b.png 描述这些图`

### MCP（Cherry Studio）

| 字段 | 值 |
|------|-----|
| 命令 | `openvl` |
| 参数 | `--mcp` |
| 超时 | `90` |

AI 会使用 `describe_image` / `describe_clipboard` 工具。

## 配置

优先级：环境变量 > npm 包目录 > skills 目录

```ini
VISION_API_KEY=你的密钥
VISION_API_BASE=https://你的中转站/v1/chat/completions
VISION_MODEL=模型ID
```

## 各工具集成

| 工具 | 集成方式 | 说明 |
|------|----------|------|
| **OpenCode** | 插件 + AGENTS.md | 粘贴图片后自动分析，无需额外操作 |
| **Claude Code** | skills | AI 识别图片路径后自动调用 openvl |
| **Pi** | skills | 同上 |
| **Cherry Studio** | MCP 服务器 | 通过 describe_image 工具手动调用 |

### OpenCode

安装插件后，粘贴图片到聊天框即可自动触发 openvl 分析。

```bash
mkdir -p ~/.config/opencode/plugin
cp integrations/opencode/openvl-image.mjs ~/.config/opencode/plugin/
```

在 `opencode.json` 中添加插件声明，并在 `AGENTS.md` 中配置图片处理规则（详见 `integrations/README.md`）。

### Claude Code / Pi

将仓库克隆到 skills 目录即可生效：

```bash
git clone https://github.com/scp3500/openvl.git ~/.claude/skills/openvl
```

### Cherry Studio

配置为 MCP 服务器，AI 通过 `describe_image` 或 `describe_clipboard` 工具调用：

| 字段 | 值 |
|------|-----|
| 命令 | `openvl` |
| 参数 | `--mcp` |
| 超时 | `90` |

详见 `integrations/README.md`。

## 请求流程

```
prompts/describe.md(固定提示词) → 用户问题 → 图片数据
```

文本在前、图片在后，便于 API 前缀缓存命中。

## 项目文件

| 文件 | 作用 |
|------|------|
| `scripts/vision.py` | 核心：读图 → 调 API → 输出描述 |
| `scripts/mcp_server.js` | MCP 服务器 |
| `prompts/describe.md` | 描述提示词模板 |
| `SKILL.md` | AI 技能定义 |

## 许可证

MIT
