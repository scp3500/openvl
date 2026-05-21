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

# 3. 截图到剪贴板，直接读
openvl -c "这张图里有什么"
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

| 工具 | 方式 | 说明 |
|------|------|------|
| **OpenCode** | 插件 | 粘贴图片 → 自动存临时文件 → AI 调 openvl |
| **Claude Code** | skills | 自动识别图片路径 → 调 openvl |
| **Cherry Studio** | MCP | `openvl --mcp` |
| **Pi** | skills | 自动识别图片路径 → 调 openvl |

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
