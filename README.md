# OpenVL

[中文](README.md) | [English](README.en.md)

让没有视觉能力的 AI 模型也能看懂图片。

```
用户发图片 → OpenVL 调用多模态 API → 返回文字描述 → AI 根据描述回复
```

## 快速开始

```bash
# 1. 安装
npm install -g @scp3500/openvl

# 2. 配置 API
openvl -key sk-你的密钥
openvl -api https://你的中转站/v1/chat/completions

# 3. 用起来
openvl D:\截图.png              # 直接看文件
openvl -c "这张图里有什么"       # 或截图到剪贴板提问
```

AI IDE（Pi / Claude Code）用户额外复制 skills：

```bash
git clone https://github.com/scp3500/openvl.git ~/.agents/skills/openvl
```

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

## 工具集成

OpenVL 支持多种接入方式，按需求选择：

| 工具 | 方式 | 体验 | 适用场景 |
|------|------|------|----------|
| **OpenCode** | 插件 + AGENTS.md | 🤖 全自动 | 粘贴图片 → 自动分析，无需任何操作 |
| **Claude Code** | skills | 👆 半自动 | 图片路径出现时 AI 自动调 openvl |
| **Pi** | skills | 👆 半自动 | 同上 |
| **Cherry Studio** | MCP | 🖱️ 手动 | 告诉 AI "用 describe_image 工具" |

### OpenCode（推荐，全自动体验最佳）

粘贴图片到聊天框 → 插件自动拦截 → 存到临时文件 → 消息中替换为 `[Image: 路径]` 标记 → AI 自动调 `openvl` 读取。用户只管贴图，剩下的全自动。

配置：
```bash
# 1. 复制插件
cp integrations/opencode/openvl-image.mjs ~/.config/opencode/plugin/

# 2. opencode.json 添加插件
# "plugin": ["./plugin/openvl-image.mjs"]

# 3. AGENTS.md 加上图片规则（见 integrations/README.md）
```

### Claude Code / Pi（skills 方式）

AI 在上下文中看到图片路径或用户提及图片时，按 skills 规则自动调 `openvl`。无需插件，配置简单。

```bash
git clone https://github.com/scp3500/openvl.git ~/.claude/skills/openvl
```

### Cherry Studio（MCP 方式）

通过 MCP 协议连接，用户手动让 AI 调用 `describe_image` 或 `describe_clipboard` 工具。适合已有 MCP 工作流的用户。

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
