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

## 各工具怎么用

| 工具 | 贴图方式 | 操作步骤 |
|------|----------|----------|
| **OpenCode** | 直接粘贴到聊天框 | 装插件 → 配 AGENTS.md → 贴图自动读 |
| **Claude Code / Pi** | 传文件路径或截图 | 装 skills → AI 自动识别图片 |
| **Cherry Studio** | 发图片给 AI | 配 MCP → 让 AI 调工具 |

### OpenCode（推荐）

装好插件后，粘贴图片到聊天框，AI 自动看图回答。

```bash
# 1. 装插件
mkdir -p ~/.config/opencode/plugin
cp integrations/opencode/openvl-image.mjs ~/.config/opencode/plugin/

# 2. opencode.json 加上这行
# "plugin": ["./plugin/openvl-image.mjs"]

# 3. AGENTS.md 加规则（参考 integrations/README.md）
```

### Claude Code / Pi

只要把仓库克隆到 skills 目录，AI 遇到图片就会自动调 openvl。

```bash
git clone https://github.com/scp3500/openvl.git ~/.claude/skills/openvl
```

### Cherry Studio

配成 MCP 服务器，让 AI 调 `describe_image` 工具：

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
